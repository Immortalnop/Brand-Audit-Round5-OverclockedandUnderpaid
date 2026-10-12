"""check_off_site_profiles.py -- do the brand's off-site profiles exist and match it?

Two related questions about the brand's presence on other platforms:

1. sameAs profiles. Organization sameAs tells assistants "these profiles are
   us". A link that is not a profile at all, that answers 404, or that leads to
   a profile naming a different organization breaks that identity chain.
     - Without network: a sameAs value that is not an absolute web address, that
       points at a platform home page or a share link, or that points back at
       the site itself is reported at once (profile-link-broken).
     - With network: each remaining profile (at most 8, at most 2 per host) is
       fetched by plain GET after reading that host's robots.txt, and failing
       closed when it cannot be read. A 404 or 410 is profile-link-broken
       (confirmed); a "not found" page or a redirect to the platform home page is
       profile-link-broken (suspected); a page that is clearly about this profile
       handle but names neither the brand nor the site is
       profile-identity-mismatch (suspected).
   Many social platforms disallow crawlers in robots.txt (X, LinkedIn,
   Facebook, Instagram) or answer bots with a challenge page. Those profiles are
   reported as unverified in metrics and limitations, never as a site defect.

2. Review and directory platforms (Trustpilot, G2, Capterra, Google Business
   Profile, Yelp and others). Profiles linked from the site or from sameAs are
   collected. When a search provider is configured, one "<brand> reviews" query
   adds platforms found by search. review-platform-missing is reported when the
   site links no review or directory profile; the reach of that conclusion is
   stated in the finding (link absence, not proof that no profile exists).
   Searching review platforms by name directly is the agent stage's job (AG-06),
   since those sites block automated clients.

The lookup can be switched off with OFF_SITE_LOOKUP=0; then only the checks that
need no network run.
"""
import os
import re
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import replace
from time import monotonic
from urllib.parse import urlsplit

from bot_challenge import challenge_signals
from check_helpers import site_kind
from external_lookup import ROBOTS_MAX_BYTES, ExternalLookup
from html_features import Document
from instrumentation import Instrumentation
from models import make_finding, skill_result
from platforms import google_maps_link, host_of, review_platform
from resolve_entity_identity import ORG_TYPES, _normalize_org_name
from search_provider import SearchProviderError, is_configured, search
from structured_data import iter_nodes, types_of
from transport import Transport

LOOKUP_ENV = "OFF_SITE_LOOKUP"
_LOOKUP_BUDGET_S = 18.0
_FETCH_TIMEOUT_MS = 5000
_PROFILE_MAX_BYTES = 400_000
_MAX_PROFILES = 8
_MAX_PER_HOST = 2
_WORKERS = 4
_KG_HOST = re.compile(r"(?:^|\.)(?:wikidata\.org|wikipedia\.org)$")
_SHARE_PATH = re.compile(r"/(?:sharer|share|intent|sharearticle|dialog|plugins)(?:[/.]|$)", re.I)
_LOGIN_PATH = re.compile(r"/(?:login|signin|sign-in|sign_in|accounts/login|auth|authwall|checkpoint|uas/login)"
                         r"(?:[/?.]|$)", re.I)
_NOT_FOUND = re.compile(r"page not found|not found|\b404\b(?=\s*(?:[-:|\u00b7]|error|not found|page|$))|doesn['\u2019]t exist|does not exist|"
                        r"isn['\u2019]t available|is not available|no longer available|account suspended|"
                        r"has been suspended|deactivated|this page (?:is|was) removed", re.I)
_GENERIC_SEGMENTS = frozenset({"company", "companies", "in", "user", "users", "c", "channel", "pages", "page",
                               "profile", "profiles", "people", "biz", "review", "reviews", "products",
                               "product", "organization", "org", "orgs", "p", "u", "school", "showcase",
                               "groups", "group", "home", "about", "en", "en-us", "us"})
_LOCAL_TYPES = frozenset({"LocalBusiness", "Restaurant", "Store", "Hotel", "LodgingBusiness", "FoodEstablishment",
                          "MedicalBusiness", "Dentist", "AutoDealer", "HealthAndBeautyBusiness", "HomeAndConstructionBusiness",
                          "ProfessionalService", "LegalService", "RealEstateAgent", "SportsActivityLocation",
                          "TravelAgency", "FinancialService", "EntertainmentBusiness", "CafeOrCoffeeShop"})
_SOFTWARE_TYPES = frozenset({"SoftwareApplication", "WebApplication", "MobileApplication"})
# Public bodies are not reviewed on consumer review platforms, so the review
# check does not apply to them.
_PUBLIC_TYPES = frozenset({"GovernmentOrganization", "GovernmentOffice", "EducationalOrganization",
                           "CollegeOrUniversity", "School", "HighSchool", "MiddleSchool", "ElementarySchool",
                           "Preschool", "NGO", "ResearchOrganization", "Library", "Museum"})
_PUBLIC_HOST = re.compile(r"\.(?:gov|mil|edu|int)(?:\.[a-z]{2})?$|\.(?:gov|ac|edu)\.[a-z]{2}$")
_SUGGESTED = {
    "local": "Google Business Profile, Yelp, Tripadvisor or an industry directory",
    "software": "G2, Capterra, TrustRadius or Product Hunt",
    "general": "Trustpilot, the Better Business Bureau, Crunchbase or an industry directory",
}


def _compact(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _handle(url):
    """The profile name in a profile URL, such as 'acme' in /company/acme or /@acme."""
    try:
        segments = [s for s in urlsplit(url).path.split("/") if s]
    except ValueError:
        return ""
    candidates = [s.lstrip("@") for s in segments if s.lower() not in _GENERIC_SEGMENTS and not s.isdigit()]
    # Skip opaque channel IDs such as YouTube's 24-character "UC..." identifiers.
    candidates = [c for c in candidates if c and not (c.lower().startswith("uc") and len(c) >= 20)]
    return candidates[0] if candidates else ""


def _organization(artifacts):
    """(pages with Organization markup, brand names, sameAs URLs, business kind)."""
    pages, names, same_as, all_types = [], [], [], set()
    for page in artifacts.pages:
        found = False
        for node in iter_nodes(page.jsonld_blocks):
            if not isinstance(node, Mapping):
                continue
            types = types_of(node)
            all_types |= types
            if not types & ORG_TYPES and not types & _LOCAL_TYPES:
                continue
            found = True
            for key in ("name", "legalName", "alternateName"):
                value = node.get(key)
                names.extend(value if isinstance(value, (list, tuple)) else [value])
            value = node.get("sameAs")
            same_as.extend(value if isinstance(value, (list, tuple)) else [value])
        if found:
            pages.append(page.url)
    kind = "local" if all_types & _LOCAL_TYPES else "software" if (
        all_types & _SOFTWARE_TYPES or any(p.page_type == "software" for p in artifacts.pages)) else (
        "public" if all_types & _PUBLIC_TYPES or _PUBLIC_HOST.search(host_of(artifacts.site_url)) else "general")
    names = [n for n in dict.fromkeys(names) if isinstance(n, str) and n.strip()]
    same_as = [u.strip() for u in dict.fromkeys(same_as) if isinstance(u, str) and u.strip()]
    return pages, names, same_as, kind


def static_problem(url, site_host):
    """Why a sameAs value cannot be a profile, or None."""
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return "is not a valid web address"
    if parts.scheme not in ("http", "https") or not host:
        return "is not an absolute http(s) web address"
    host = host[4:] if host.startswith("www.") else host
    if site_host and (host == site_host or host.endswith("." + site_host)):
        return "points back at the site itself, not at a profile on another platform"
    if _SHARE_PATH.search(parts.path):
        return "is a share or widget link, not a profile"
    if google_maps_link(url) == "not_place":
        return "is a map position, route or search, not a business profile"
    if parts.path.strip("/") == "" and not parts.query:
        return "points at the platform home page, not at a profile"
    return None


def _profile_transport(origin, deadline_monotonic, limits):
    bounded = replace(limits, MAX_TOTAL_HTTP_REQUESTS=1 + 2 * _MAX_PER_HOST,
                      MAX_TOTAL_BYTES=ROBOTS_MAX_BYTES + _MAX_PER_HOST * _PROFILE_MAX_BYTES,
                      MAX_RESPONSE_BYTES=_PROFILE_MAX_BYTES,
                      PER_FETCH_TIMEOUT_MS=max(limits.PER_FETCH_TIMEOUT_MS, _FETCH_TIMEOUT_MS))
    # Never allow private targets here: these are public third-party hosts.
    return Transport(origin, deadline_monotonic, bounded, Instrumentation(), allow_private=False,
                     pool="external", stage="off_site_profiles")


def _page_summary(resp):
    doc = Document()
    try:
        doc.feed(resp.text)
        doc.close()
    except (ValueError, RecursionError):
        pass
    meta = doc.meta
    def first(key):
        return next((v for v in meta.get(key, ()) if v and v.strip()), "")
    title = " ".join("".join(doc.title_parts).split())
    labels = [title, first("og:title"), first("twitter:title"), first("og:site_name")]
    identity = " ".join(labels + [first("og:description"), first("description"), first("og:url")]
                        + doc.headings[:5] + [" ".join(doc.text)[:3000]])
    return {"title": title, "labels": " ".join(labels), "identity": identity}


def evaluate_profile(url, resp, status, site_host, brand_names):
    """(verdict, detail) for one fetched profile. Verdicts: verified, broken,
    soft_broken, mismatch, unverified."""
    if status != "ok":
        return "unverified", status
    # A bot challenge says nothing about the profile: unverified, never broken.
    if challenge_signals(resp.status_code, resp.headers, resp.text):
        return "unverified", "bot_challenge"
    if resp.status_code in (404, 410):
        return "broken", f"HTTP {resp.status_code}"
    if not resp.ok:
        return "unverified", f"http_{resp.status_code}"
    ctype = resp.headers.get("Content-Type", "").lower()
    if ctype and "html" not in ctype:
        return "unverified", "not_html"
    final = resp.final_url or url
    if _LOGIN_PATH.search(urlsplit(final).path):
        return "unverified", "login_wall"
    summary = _page_summary(resp)
    if _NOT_FOUND.search(summary["labels"]) or _NOT_FOUND.search(" ".join(summary["identity"].split()[:12])):
        return "soft_broken", f"the page says the profile is not available ('{summary['title'][:80]}')"
    if urlsplit(final).path.strip("/") == "" and urlsplit(url).path.strip("/") != "":
        return "soft_broken", "redirects to the platform home page"
    if site_host and site_host.encode() in resp.content.lower():
        return "verified", "links to the site"
    # A Google Maps place page draws the place's name with script; its HTML names
    # only the map application, so it can neither confirm nor contradict the brand.
    if google_maps_link(url) == "place" or google_maps_link(final) == "place":
        return "unverified", "map_place_not_readable"
    identity = " " + " ".join(re.findall(r"\w+", summary["identity"].lower())) + " "
    handle = _handle(final) or _handle(url)
    for name in brand_names:
        normalized = _normalize_org_name(name)
        if normalized and f" {normalized} " in identity:
            return "verified", "names the brand"
        compact = _compact(normalized)
        if len(compact) >= 4 and compact in _compact(handle):
            return "verified", "profile handle matches the brand name"
    if handle and _compact(handle) in _compact(summary["identity"]) and summary["labels"].strip():
        return "mismatch", (f"the profile page is about '{handle}' ('{summary['title'][:80]}') but names "
                            f"neither the brand nor the site")
    return "unverified", "no_profile_metadata"


def _lookup_profiles(targets, site_host, brand_names, deadline, limits, instrumentation, factory):
    end = monotonic() + _LOOKUP_BUDGET_S
    if deadline is not None:
        end = min(end, deadline.deadline_monotonic)
    lookup = ExternalLookup(end, limits, instrumentation, factory)
    by_origin = {}
    for target in targets:
        parts = urlsplit(target["url"])
        by_origin.setdefault(f"{parts.scheme}://{parts.netloc}".lower(), []).append(target)

    def run(group):
        for target in group:
            if monotonic() >= end:
                target.update(verdict="unverified", detail="deadline")
                continue
            resp, status = lookup.get(target["url"], _PROFILE_MAX_BYTES)
            verdict, detail = evaluate_profile(target["url"], resp, status, site_host, brand_names)
            target.update(verdict=verdict, detail=detail,
                          http_status=resp.status_code if resp is not None else None)

    pool = ThreadPoolExecutor(max_workers=_WORKERS)
    futures = [pool.submit(run, group) for group in by_origin.values()]
    wait(futures, timeout=max(0.0, end - monotonic()) + 2.0)
    pool.shutdown(wait=False, cancel_futures=True)
    for target in targets:
        target.setdefault("verdict", "unverified")
        target.setdefault("detail", "deadline")
    return lookup


def _search_review_platforms(name, limits, instrumentation, deadline):
    """Review platforms named in one '<brand> reviews' search, or None when the
    search did not run."""
    if not is_configured() or not name:
        return None, None
    if deadline is not None and deadline.expired():
        return None, "deadline"
    if instrumentation is not None and instrumentation.search_queries_attempted >= limits.MAX_EXTERNAL_FETCHES:
        return None, "search query budget reached"
    try:
        hits = search(f'"{name}" reviews', max_results=10, timeout_s=limits.PER_FETCH_TIMEOUT_MS / 1000)
    except SearchProviderError:
        if instrumentation is not None:
            instrumentation.record_external_fetch(ok=False, search=True)
        return None, "search provider failed"
    if instrumentation is not None:
        instrumentation.record_external_fetch(ok=True, search=True)
    found = {}
    for hit in hits:
        platform = review_platform(hit.get("url", ""))
        if platform and platform[0] not in found:
            found[platform[0]] = hit.get("url", "")
    return found, None


def _broken_text(target):
    where = "sameAs link" if target["source"] == "sameAs" else "Profile link"
    detail = target["detail"]
    if target["verdict"] == "soft_broken":
        return f"{where} {target['url']}: {detail}"
    if detail.startswith("HTTP"):
        return f"{where} {target['url']} answers {detail}"
    return f"{where} {target['url']} {detail}"


def _action(summary, steps, priority, benefit):
    return {"summary": summary, "steps": steps, "priority": priority, "effort": "low",
            "expected_benefit": benefit,
            "verification": "Re-run the audit after the links or profiles change"}


def check_off_site_profiles(artifacts, identity, deadline, limits, instrumentation=None, transport_factory=None):
    if deadline is not None and deadline.expired():
        return skill_result("freshness-corroboration", status="insufficient_evidence",
                            warnings=["Off-site profile checks skipped: deadline reached."])
    org_pages, names, same_as, kind = _organization(artifacts)
    identity_data = identity.get("data", {}) if isinstance(identity, Mapping) else {}
    if isinstance(identity_data.get("canonical_name"), str):
        names = [identity_data["canonical_name"]] + [n for n in names if n != identity_data["canonical_name"]]
    site_host = host_of(artifacts.site_url) or host_of(artifacts.normalized_origin)
    warnings, findings = [], []

    # --- sameAs profiles ---------------------------------------------------
    profiles, invalid = [], []
    for url in same_as:
        if _KG_HOST.search(host_of(url) or ""):
            continue  # knowledge-graph links belong to check_knowledge_graph
        problem = static_problem(url, site_host)
        if problem:
            invalid.append({"url": url, "verdict": "broken", "detail": problem, "source": "sameAs"})
        else:
            profiles.append({"url": url, "source": "sameAs"})

    # --- review and directory platforms -------------------------------------
    linked = {}
    for url in same_as:
        platform = review_platform(url)
        if platform and platform[0] not in linked:
            linked[platform[0]] = {"url": url, "kind": platform[1], "source": "sameAs"}
    for page in artifacts.pages:
        for url in page.external_links:
            platform = review_platform(url)
            if platform and platform[0] not in linked:
                linked[platform[0]] = {"url": url, "kind": platform[1], "source": page.url}
    profile_urls = {p["url"] for p in profiles}
    for name, item in linked.items():
        if item["source"] != "sameAs" and item["url"] not in profile_urls and not static_problem(item["url"], site_host):
            profiles.append({"url": item["url"], "source": item["source"], "platform": name})

    # Bounded selection: at most _MAX_PER_HOST per host and _MAX_PROFILES overall.
    selected, per_host = [], {}
    for target in profiles:
        host = host_of(target["url"])
        if per_host.get(host, 0) >= _MAX_PER_HOST or len(selected) >= _MAX_PROFILES:
            target.update(verdict="unverified", detail="check_cap_reached")
            continue
        per_host[host] = per_host.get(host, 0) + 1
        selected.append(target)

    metrics = {"organization_pages": len(org_pages), "same_as_links": len(same_as),
               "review_platforms_linked": sorted(linked), "business_kind": kind, "lookup": "not_needed"}
    lookup = None
    if selected:
        if os.environ.get(LOOKUP_ENV) == "0":
            metrics["lookup"] = "disabled"
            for target in selected:
                target.update(verdict="unverified", detail="lookup_disabled")
            warnings.append(f"Off-site profile lookup disabled ({LOOKUP_ENV}=0); linked profiles were not "
                            f"fetched or verified.")
        else:
            lookup = _lookup_profiles(selected, site_host, names, deadline, limits, instrumentation,
                                      transport_factory or _profile_transport)
            metrics["lookup"] = "completed"
            metrics["robots"] = dict(lookup.robots)
            metrics["requests"] = list(lookup.requests)[:40]
    checked = invalid + profiles
    metrics["profiles"] = [{k: t.get(k) for k in ("url", "source", "verdict", "detail", "http_status")}
                           for t in checked][:20]
    outcome = {}
    for target in checked:
        outcome[target.get("verdict", "unverified")] = outcome.get(target.get("verdict", "unverified"), 0) + 1
    metrics["profile_outcomes"] = outcome
    unverified = [t for t in profiles if t.get("verdict") == "unverified"]
    if unverified:
        metrics["profiles_unverified"] = len(unverified)

    broken = invalid + [t for t in profiles if t.get("verdict") in ("broken", "soft_broken")]
    if broken:
        confirmed = any(t["verdict"] == "broken" for t in broken)
        severity = "medium" if confirmed else "low"
        pages = org_pages[:10] or [artifacts.site_url]
        findings.append(make_finding(
            category="off_site_presence", finding_type="defect", severity=severity,
            status="confirmed" if confirmed else "suspected", confidence=0.9 if confirmed else 0.6,
            title="Linked off-site profiles are broken or are not profiles",
            root_cause="A sameAs or profile link that is invalid or leads to a missing page breaks the chain "
                       "assistants follow to confirm who the brand is",
            evidence=[{"type": "off_site_profile", "description": _broken_text(t),
                       "urls": pages if t["source"] == "sameAs" else [t["source"]]}
                      for t in broken[:10]],
            affected_pages=sorted({u for t in broken for u in (pages if t["source"] == "sameAs" else [t["source"]])}),
            suggested_action=_action(
                "Point every sameAs and profile link at a live profile the brand owns",
                ["Replace each listed link with the full address of the brand's profile page",
                 "Remove links to deleted or suspended profiles",
                 "Do not list share links, platform home pages or the site itself in sameAs"],
                severity, "Every profile link resolves to the brand's own profile"),
            provenance={"skill": "freshness-corroboration", "script": "check_off_site_profiles.py",
                        "rule_id": "profile-link-broken"},
        ))

    mismatched = [t for t in profiles if t.get("verdict") == "mismatch"]
    if mismatched:
        pages = org_pages[:10] or [artifacts.site_url]
        findings.append(make_finding(
            category="off_site_presence", finding_type="defect", severity="medium",
            status="suspected", confidence=0.6,
            title="A linked profile does not appear to belong to the brand",
            root_cause="A profile linked as the brand's names neither the brand nor the site, so assistants "
                       "may attribute another account's content to the brand",
            evidence=[{"type": "off_site_profile", "description": f"{t['url']}: {t['detail']}",
                       "urls": pages if t["source"] == "sameAs" else [t["source"]]}
                      for t in mismatched[:10]],
            affected_pages=sorted({u for t in mismatched for u in (pages if t["source"] == "sameAs" else [t["source"]])}),
            suggested_action=_action(
                "Check that each listed profile is the brand's own and link it back to the site",
                ["Open each listed profile and confirm the brand owns it",
                 "Replace links to other accounts with the brand's own profile",
                 "Add the site address and the brand name to the profile's bio or about section"],
                "medium", "Profiles and site confirm each other, so assistants attribute content correctly"),
            provenance={"skill": "freshness-corroboration", "script": "check_off_site_profiles.py",
                        "rule_id": "profile-identity-mismatch"},
        ))

    # --- review platform presence -----------------------------------------
    name = names[0] if names else ""
    searched, search_note = (None, None)
    # Public bodies, news publishers and nonprofits are not reviewed on consumer
    # review platforms, so the review check does not apply to them. Publishers and
    # nonprofits are recognized from positive evidence only (check_helpers.site_kind);
    # a site with no such evidence is still checked.
    html_pages = [p for p in artifacts.pages if p.status_code == 200 and "non_html_content" not in p.warnings]
    exempt = {"public": "public body"}.get(kind) or {"publisher": "news publisher",
                                                     "nonprofit": "nonprofit"}.get(site_kind(html_pages))
    if exempt:
        metrics["review_platform_check"] = "not_applicable_" + exempt.replace(" ", "_")
    if not linked and not exempt and identity_data.get("confidence", 0) >= 0.85:
        searched, search_note = _search_review_platforms(name, limits, instrumentation, deadline)
        if search_note:
            warnings.append(f"Review-platform search not completed ({search_note}).")
    metrics["review_platform_search"] = ("not_run" if searched is None else sorted(searched))
    if not linked and not exempt and html_pages:
        pages = [p.url for p in html_pages][:10]
        if searched:
            description = ("Search found the brand on " + ", ".join(sorted(searched)) +
                           ", but no crawled page or sameAs link points to those profiles")
            title = "Review profiles exist but the site does not link them"
            status, confidence = "confirmed", 0.7
        else:
            description = (f"None of the {len(html_pages)} crawled page(s) or the sameAs links point to a "
                           f"review or directory profile"
                           + (" and a search for the brand's reviews found none" if searched is not None else
                              "; whether profiles exist off-site was not searched"))
            title = "No review or directory profile is linked from the site"
            status, confidence = ("confirmed", 0.7) if searched is not None else ("suspected", 0.55)
        findings.append(make_finding(
            category="off_site_presence", finding_type="proactive_improvement", severity="low",
            status=status, confidence=confidence, title=title,
            root_cause="Assistants answer 'is this brand any good?' from review and directory platforms; "
                       "a brand with no linked review profile leaves them nothing to corroborate it with",
            evidence=[{"type": "review_platforms", "description": description, "urls": pages[:3]}],
            affected_pages=pages[:3],
            suggested_action=_action(
                f"Claim and link review profiles that fit the business, such as {_SUGGESTED[kind]}",
                [f"Claim or create profiles on review platforms that fit the business ({_SUGGESTED[kind]})",
                 "Link them from the site footer and list them in Organization sameAs",
                 "Ask real customers for reviews and answer them publicly"],
                "low", "Independent ratings and reviews corroborate the brand in assistant answers"),
            provenance={"skill": "freshness-corroboration", "script": "check_off_site_profiles.py",
                        "rule_id": "review-platform-missing"},
        ))

    if unverified and metrics["lookup"] == "completed":
        warnings.append(f"{len(unverified)} linked profile(s) could not be verified (robots rules, bot "
                        f"challenges, login walls or errors on the platform); not checked, not a site defect.")
    return skill_result("freshness-corroboration", findings=findings, metrics=metrics, warnings=warnings,
                        coverage={"pages_analyzed": len(artifacts.pages), "pages_skipped": 0,
                                  "queries_attempted": 1 if searched is not None or search_note == "search provider failed" else 0,
                                  "queries_completed": 1 if searched is not None else 0})
