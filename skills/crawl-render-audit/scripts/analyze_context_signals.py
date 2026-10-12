"""analyze_context_signals.py -- signals assistants use to match a brand to who is asking.

Assistants tailor answers to the person asking: their location, stated role or
need, and earlier context (handout appendix E). A brand is surfaced for "near me"
or "for students" questions only if its pages state where it operates and whom it
serves in a form a machine can read. This check reads the acquisition snapshot
only (no requests):

  - location-markup-missing: the pages show a physical location (an address,
    a map embed, a directions link) but no page states a location in
    structured data (address, geo, areaServed, a Place). An address is an
    <address> block with a number in it, or a postal address written as plain
    text: after a label ("Address:", "Visit us at"), as a street line
    ("12 High Street, Springfield"), or as comma-separated parts ending in a
    postal code.
    Two or more kinds of location evidence make it a confirmed medium defect;
    one kind makes it a low suggestion.
  - local-business-incomplete: LocalBusiness (or a subtype) markup without an
    address, which Google requires (confirmed defect, medium), or with an
    address but neither geo nor areaServed (suggestion, low).
  - audience-segment-missing (suggestion, suspected): a commercial site whose
    titles, headings and internal links never name an audience ("for
    students", "/industries/", "/use-cases/"), so an assistant has no page to
    match a user's stated context to.
  - contact-markup-missing (suggestion, suspected): the pages show an email
    or phone number (mailto: and tel: links, emails written as text, phone
    numbers after a label such as "Phone:") but no page states an email,
    telephone or contactPoint in JSON-LD, microdata or RDFa.

Pages whose raw HTML carries too little text for their type are probably built
by JavaScript. They still count as evidence when they show a location or an
audience, but the audience check never concludes from them that one is missing,
and the report says how many were skipped.
"""
import re
from collections import Counter
from urllib.parse import urlsplit
from check_helpers import (eligible_pages, split_script_dependent, script_dependent_warning, contact_details,
                           page_share)
from check_catalog import calibrated_confidence
from models import make_finding, skill_result
from structured_data import iter_nodes, types_of, LOCAL_BUSINESS_TYPES, LOCATION_PROPERTIES, LOCATION_TYPES

_MAP_URL = re.compile(r"^(?:https?:)?//(?:[a-z0-9-]+\.)*(?:google\.[a-z.]{2,6}/maps|maps\.google\.[a-z.]{2,6}"
                      r"|maps\.app\.goo\.gl|goo\.gl/maps|maps\.apple\.com|(?:www\.)?openstreetmap\.org"
                      r"|bing\.com/maps|waze\.com)", re.I)
_SEGMENT_TEXT = re.compile(
    r"\bfor\s+(?:students?|teachers?|educators?|schools?|universit(?:y|ies)|enterprises?|business(?:es)?"
    r"|small businesses|smbs?|startups?|teams?|agencies|developers?|creators?|non-?profits?|government"
    r"|healthcare|hospitals?|retail(?:ers)?|individuals?|families|parents|professionals?|freelancers?"
    r"|beginners?|kids|seniors|marketers?|designers?|engineers?|educat(?:ion|ors)|manufacturers?"
    r"|restaurants?|clinics?|law firms?|accountants?|consultants?|enterprise)\b", re.I)
_SEGMENT_PATH = re.compile(r"/(?:solutions|industries|industry|use-cases?|usecases|who-we-serve|audiences?"
                           r"|segments?|customers|for-[a-z0-9-]+)(?:/|$)"
                           r"|/(?:mens?|womens?|men-s|women-s|kids|children|boys|girls|baby|toddlers?|teens?)(?:/|$|[-_])",
                           re.I)
# Consumer segments a shop names in its navigation: "Men", "Women's", "Shop Kids".
_SEGMENT_LABEL = re.compile(r"^(?:shop\s+)?(?:men|women|kids|children|boys|girls|baby|babies|toddlers?|teens?"
                            r"|juniors?|unisex)(?:'?s)?(?:\s+\S+){0,2}$", re.I)
_PRICING_PATH = re.compile(r"/(?:pricing|plans|buy|shop)(?:/|$)", re.I)


def _has_location_markup(page):
    for node in iter_nodes(page.jsonld_blocks):
        if types_of(node) & LOCATION_TYPES or any(node.get(k) for k in LOCATION_PROPERTIES):
            return True
    microdata = set((page.features or {}).get("microdata_types") or ())
    return bool(microdata & (LOCATION_TYPES | LOCAL_BUSINESS_TYPES))


# Pages where a shown address or map is the organization's own: the home,
# contact and about pages and location pages ("/locations", "/find-us").
_OWN_LOCATION_PATH = re.compile(r"/(?:contact|contact-us|about|about-us|locations?|stores?|store-locator|find-us"
                                r"|visit(?:-us)?|directions|offices?|campus|hours)(?:/|$|[-_.])", re.I)


def _key(text):
    return " ".join((text or "").lower().split())


def _plain_locations(page):
    """Postal addresses written as plain text, map embeds and map links on one page,
    as {kind: [values]}."""
    f = page.features or {}
    return {"address": [t for t in f.get("postal_address_text") or () if t],
            "map_embed": [(r.get("src") or "").strip() for r in f.get("media_records") or ()
                          if r.get("tag") == "iframe" and _MAP_URL.search((r.get("src") or "").strip())],
            "map_link": [(h or "").strip() for h, _ in f.get("anchors") or () if _MAP_URL.search((h or "").strip())]}


def _location_evidence(page, repeated=frozenset()):
    """Kinds of physical-location evidence on one page: {kind: example}.

    An <address> element always counts. A plain-text address, map embed or map
    link counts as the organization's own only on a home, contact, about or
    location page, or when the same value appears on two or more sampled pages
    (a site-wide header or footer): an address quoted in an article or a map of
    an event venue is about something else."""
    f = page.features or {}
    found = {}
    for text in f.get("address_text") or ():
        if re.search(r"\d", text) and len(text.split()) >= 3:
            found["address"] = text[:120]
            break
    try:
        own_page = page.page_type in ("home", "contact", "about") or bool(_OWN_LOCATION_PATH.search(urlsplit(page.url).path))
    except ValueError:
        own_page = page.page_type in ("home", "contact", "about")
    for kind, values in _plain_locations(page).items():
        if kind in found:
            continue
        value = next((v for v in values if own_page or _key(v) in repeated), None)
        if value:
            found[kind] = value[:120]
    return found


def _has_contact_markup(page):
    """True when the page states an email, telephone or contactPoint in
    JSON-LD, microdata or RDFa."""
    if (page.features or {}).get("contact_markup"):
        return True
    return any(node.get(k) for node in iter_nodes(page.jsonld_blocks) for k in ("email", "telephone", "contactPoint"))


def _contact_evidence(page):
    """'email: a@b.com; phone: +1 555 0100' for one page, or '' when none is shown."""
    emails, phones = contact_details(page)
    parts = []
    if emails:
        parts.append("email: " + ", ".join(sorted(emails)[:3]))
    if phones:
        parts.append("phone: " + ", ".join(sorted(phones)[:3]))
    return "; ".join(parts)


def _audience_signals(page):
    f = page.features or {}
    texts = [page.title or ""] + list(page.headings[:20]) + [t for _, t in (f.get("anchors") or ())]
    if any(_SEGMENT_TEXT.search(t or "") or _SEGMENT_LABEL.match(" ".join((t or "").split())) for t in texts):
        return True
    paths = [urlsplit(page.url).path] + [urlsplit(u).path for u in page.internal_links]
    if any(_SEGMENT_PATH.search(p or "") for p in paths):
        return True
    return any(node.get("audience") for node in iter_nodes(page.jsonld_blocks))


def analyze_context_signals(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Context-signal checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    judged, built = split_script_dependent(pages)
    findings = []

    markup_pages = [p for p in pages if _has_location_markup(p)]
    # Plain-text locations repeated across pages belong to the site chrome.
    seen = Counter(_key(v) for p in pages for values in _plain_locations(p).values() for v in set(values))
    repeated = frozenset(k for k, n in seen.items() if n >= 2)
    evidence = [(p, _location_evidence(p, repeated)) for p in pages]
    evidence = [(p, e) for p, e in evidence if e]
    kinds = {k for _, e in evidence for k in e}
    if evidence and not markup_pages:
        strong = len(kinds) >= 2
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect" if strong else "proactive_improvement",
            severity="medium" if strong else "low", status="confirmed" if strong else "suspected",
            confidence=0.85 if strong else 0.55,
            title="Physical location is shown on the page but stated in no structured data",
            root_cause="Assistants answer location-dependent questions from machine-readable addresses, "
                       "coordinates and service areas; a location shown only as text or a map is easy to miss",
            affected_pages=[p.url for p, _ in evidence],
            evidence=[{"type": "location_signal",
                       "description": "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in sorted(e.items()))
                                      + ". No address, geo or areaServed in any page's JSON-LD",
                       "urls": [p.url]} for p, e in evidence[:10]],
            suggested_action={
                "summary": "State the address, coordinates and service area in Organization or LocalBusiness JSON-LD",
                "steps": ["Add a PostalAddress (streetAddress, addressLocality, postalCode, addressCountry) to the "
                          "Organization or LocalBusiness markup",
                          "Add geo coordinates for each physical location, and areaServed for the regions served",
                          "Keep the visible address, the markup and the business profile identical"],
                "priority": "medium" if strong else "low", "effort": "low",
                "expected_benefit": "The brand can be matched to location-specific questions",
                "verification": "Validate the markup and confirm the address matches the visible text"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_context_signals.py",
                        "rule_id": "location-markup-missing"},
        ))

    incomplete = []
    for p in pages:
        for node in iter_nodes(p.jsonld_blocks):
            local = types_of(node) & LOCAL_BUSINESS_TYPES
            if not local:
                continue
            missing = [k for k in ("address",) if not node.get(k)]
            if not node.get("geo") and not node.get("areaServed"):
                missing.append("geo or areaServed")
            if missing:
                incomplete.append((p, sorted(local)[0], missing))
    if incomplete:
        no_address = any("address" in m for _, _, m in incomplete)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect" if no_address else "proactive_improvement",
            severity="medium" if no_address else "low", status="confirmed" if no_address else "suspected",
            confidence=0.9 if no_address else 0.6,
            title="LocalBusiness markup has no address" if no_address
            else "LocalBusiness markup has no coordinates or service area",
            root_cause="LocalBusiness markup without an address is not eligible for local results, and without "
                       "geo or areaServed it cannot be matched to where the asker is",
            affected_pages=sorted({p.url for p, _, _ in incomplete}),
            evidence=[{"type": "local_business_markup",
                       "description": f"{kind} omits: {', '.join(missing)}", "urls": [p.url]}
                      for p, kind, missing in incomplete[:10]],
            suggested_action={
                "summary": "Complete the LocalBusiness markup with address, geo and areaServed",
                "steps": ["Add address as a PostalAddress matching the visible address",
                          "Add geo with latitude and longitude, or areaServed for a service-area business"],
                "priority": "medium" if no_address else "low", "effort": "low",
                "expected_benefit": "The business qualifies for local answers and results",
                "verification": "Validate the LocalBusiness node with a structured-data validator"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_context_signals.py",
                        "rule_id": "local-business-incomplete"},
        ))

    contact_markup_pages = [p for p in pages if _has_contact_markup(p)]
    contacts = [(p, _contact_evidence(p)) for p in pages]
    contacts = [(p, e) for p, e in contacts if e]
    if contacts and not contact_markup_pages:
        # Home and contact pages first: they hold the organization's own details.
        contacts.sort(key=lambda item: item[0].page_type not in ("home", "contact"))
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=calibrated_confidence("contact-markup-missing", 0.7),
            title="Email or phone shown on " + page_share([p for p, _ in contacts], pages)
                  + " but stated in no structured data",
            root_cause="Assistants answer \"how do I contact them?\" from machine-readable email, telephone and "
                       "contactPoint properties; contact details shown only as text or links are easy to miss "
                       "or to attribute to the wrong organization",
            affected_pages=[p.url for p, _ in contacts],
            evidence=[{"type": "contact_signal",
                       "description": e + ". No email, telephone or contactPoint in any page's structured data",
                       "urls": [p.url]} for p, e in contacts[:10]],
            suggested_action={
                "summary": "State the main email and phone number in the Organization JSON-LD",
                "steps": ["Add email and telephone to the Organization or LocalBusiness markup on the home page",
                          "Add a contactPoint for each department visitors contact (sales, support, admissions), "
                          "with its contactType, telephone and email",
                          "Use the same details as the contact page, written in international format (+country code)"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Assistants can give the brand's own contact details when asked",
                "verification": "Validate the markup and confirm it matches the visible contact details"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_context_signals.py",
                        "rule_id": "contact-markup-missing"},
        ))

    commercial = any(p.page_type in ("product", "service", "software") or _PRICING_PATH.search(urlsplit(p.url).path)
                     or any(_PRICING_PATH.search(urlsplit(u).path) for u in p.internal_links) for p in pages)
    if commercial and len(judged) >= 3 and not any(_audience_signals(p) for p in pages):
        links = sum(len(p.internal_links) for p in judged)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.5,
            title=f"No page or link names an audience segment across {len(judged)} sampled pages",
            root_cause="Assistants weight answers toward the asker's stated role or need; a site with no page "
                       "for a named audience gives them nothing to match \"for small businesses\" or "
                       "\"for students\" to",
            affected_pages=[judged[0].url],
            evidence=[{"type": "audience_segments",
                       "description": f"Checked {len(judged)} page titles and headings and {links} internal links; "
                                      "none names an audience (\"for teams\", /industries/, /use-cases/)",
                       "urls": [judged[0].url]}],
            suggested_action={
                "summary": "Publish one page per main audience and link it from the navigation",
                "steps": ["List the two to four audiences the offer serves best",
                          "Give each a page that states the audience in its title and H1, with the use cases, "
                          "proof and pricing that matter to it",
                          "Link those pages from the main navigation and the home page"],
                "priority": "low", "effort": "medium",
                "expected_benefit": "Assistants can match the brand to questions that state who is asking",
                "verification": "Re-run the audit and confirm audience pages are detected"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_context_signals.py",
                        "rule_id": "audience-segment-missing"},
        ))

    warnings = [script_dependent_warning(built, pages, "location and audience signals")] if built else []
    return skill_result(
        "crawl-render-audit", findings=findings, warnings=warnings,
        metrics={"context_pages_analyzed": len(pages),
                 "context_script_dependent_pages": len(built),
                 "context_location_markup_pages": len(markup_pages),
                 "context_location_evidence_pages": len(evidence),
                 "context_location_evidence_kinds": sorted(kinds),
                 "context_commercial_site": commercial,
                 "context_audience_pages": sum(_audience_signals(p) for p in pages),
                 "context_contact_pages": len(contacts),
                 "context_contact_markup_pages": len(contact_markup_pages)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
