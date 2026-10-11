"""llms.txt structure, links and llms-full.txt; sameAs and review-platform
profiles; Core Web Vitals field data and static estimates; and full fixture
audits that exercise every new check together.

Third-party lookups run against a fake transport, so no test touches the network.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline
from transport import Response
from instrumentation import Instrumentation
from acquire_site import _extract_page, acquire_site
from html_features import Document
from llms_txt import parse_llms_txt
from check_llms_txt import check_llms_txt
import check_off_site_profiles as offsite
from check_off_site_profiles import check_off_site_profiles, evaluate_profile, static_problem
from field_vitals import parse_response, fetch_field_vitals, start_field_lookup, KEY_ENV, LOOKUP_ENV
from analyze_web_vitals import analyze_web_vitals, page_factors
from execution_summary import derive_limitations
from ingest_agent_findings import ingest_agent_findings
from platforms import review_platform, video_platform
from check_catalog import CATALOG, get_entry
from run_audit import run_audit
from fixtures_server import start_server

LIMITS = Limits()
SITE = "https://acme.example"
IDENTITY = {"status": "success", "data": {"canonical_name": "Acme Widgets", "confidence": 0.92}}


def page(body="", head="", url=SITE + "/", headers=None, duration=50):
    html = f'<html lang="en"><head>{head}</head><body>{body}</body></html>'
    response = Response(200, {"Content-Type": "text/html", **(headers or {})}, html.encode(), url)
    response.network_duration_ms = duration
    return _extract_page(url, response, duration, LIMITS)


def org(same_as, name="Acme Widgets", kind="Organization"):
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@type": kind, "name": name, "sameAs": same_as})
            + "</script>")


def snapshot(pages, llms=None):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value(llms or {"present": False, "status": "absent"}),
                          freeze_value({"status": "ok"}), freeze_value({"coverage": coverage}), ())


def by_id(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


# ------------------------------------------------------------------ llms.txt

def test_parse_valid_llms_txt():
    text = ("# Acme\n\n> Widgets for workshops.\n\n## Docs\n\n- [Guide](/docs/guide.md): how to\n"
            "- [API](https://acme.example/api#auth)\n\n## Optional\n\n- [Blog](https://blog.example.org/)\n"
            "- [Mail](mailto:hi@acme.example)\n")
    parsed = parse_llms_txt(text, "https://acme.example/llms.txt")
    assert parsed["title"] == "Acme" and parsed["has_summary"] is True
    assert parsed["sections"] == ["Docs", "Optional"]
    assert parsed["links"] == ["https://acme.example/docs/guide.md", "https://acme.example/api",
                               "https://blog.example.org/"]
    assert parsed["structure_issues"] == []


@pytest.mark.parametrize("text,issue", [
    ("Acme widgets\n- [Guide](/g)\n", "does not start with an H1 title"),
    ("# Acme\n# Again\n## S\n- [Guide](/g)\n", "has 2 H1 titles"),
    ("# Acme\n\n> Summary only.\n", "links to no pages"),
    ("# Acme\n\nhttps://acme.example/a\nhttps://acme.example/b\n", "bare URLs, not as Markdown links"),
    ("# Acme\n\n- [Guide](/g)\n", "not grouped under H2 sections"),
])
def test_parse_llms_txt_issues(text, issue):
    issues = parse_llms_txt(text, SITE + "/llms.txt")["structure_issues"]
    assert any(issue in i for i in issues), issues


def test_check_llms_txt_reports_broken_links_format_and_llms_full():
    llms = {"present": True, "status": "ok", "structure_issues": ["the file links to no pages"],
            "link_count": 3,
            "link_checks": [{"url": SITE + "/a", "status": "ok", "http_status": 200},
                            {"url": SITE + "/gone", "status": "broken", "http_status": 404},
                            {"url": "https://other.example/x", "status": "cross_origin_not_checked"}],
            "link_summary": {"ok": 1, "broken": 1, "cross_origin_not_checked": 1, "requests": 1},
            "full": {"present": False, "status": "malformed", "served_html": True}}
    result = check_llms_txt(snapshot([page()], llms), make_deadline(LIMITS))
    (broken,) = by_id(result, "llms-txt-broken-links")
    assert broken["severity"] == "medium" and "HTTP 404 for https://acme.example/gone" in broken["evidence_text"]
    (invalid,) = by_id(result, "llms-txt-invalid")
    assert "links to no pages" in invalid["evidence_text"]
    assert "/llms-full.txt answers with an HTML page" in invalid["evidence_text"]
    metrics = result["metrics"]
    assert metrics["llms_txt_links_checked"] == 2 and metrics["llms_full_txt_status"] == "malformed"
    assert metrics["llms_txt_link_outcomes"] == {"ok": 1, "broken": 1, "cross_origin_not_checked": 1}


def test_absent_llms_txt_mentions_existing_llms_full():
    llms = {"present": False, "status": "absent", "full": {"present": True, "status": "ok"}}
    (finding,) = by_id(check_llms_txt(snapshot([page()], llms), make_deadline(LIMITS)), "no-llms-txt")
    assert "/llms-full.txt exists" in finding["evidence_text"]


def test_valid_llms_txt_with_live_links_is_quiet():
    llms = {"present": True, "status": "ok", "structure_issues": [], "link_count": 1,
            "link_checks": [{"url": SITE + "/a", "status": "ok"}], "link_summary": {"ok": 1, "requests": 0},
            "full": {"present": True, "status": "ok"}}
    assert check_llms_txt(snapshot([page()], llms), make_deadline(LIMITS))["findings"] == []


def test_acquisition_checks_llms_links_within_cap_and_never_off_origin():
    seen = []
    base, stop = start_server(rich=True, requests_seen=seen)
    try:
        limits = Limits(TOTAL_AUDIT_TIMEOUT_S=60, REQUEST_DELAY_S=0)
        artifacts = acquire_site(base + "/", make_deadline(limits), limits, allow_private_targets=True)
        capped = acquire_site(base + "/", make_deadline(limits), Limits(TOTAL_AUDIT_TIMEOUT_S=60, REQUEST_DELAY_S=0,
                                                                         MAX_LLMS_LINK_CHECKS=0),
                              allow_private_targets=True)
    finally:
        stop()
    llms = artifacts.llms_txt_data
    assert llms["title"] == "Rich Brand" and llms["link_count"] == 3
    outcomes = {c["url"].rsplit("/", 1)[-1]: c for c in llms["link_checks"]}
    assert outcomes["gallery"]["status"] == "ok" and outcomes["gallery"]["source"] == "crawl"
    assert outcomes["old-catalogue"]["status"] == "broken" and outcomes["old-catalogue"]["http_status"] == 404
    assert outcomes["tools"]["status"] == "cross_origin_not_checked"
    assert llms["full"]["status"] == "malformed" and llms["full"]["served_html"] is True
    # The crawled page is not fetched again for the check; the dead one once per acquisition.
    assert seen.count("/gallery") == 2 and seen.count("/old-catalogue") == 1 and seen.count("/llms-full.txt") == 2
    assert capped.llms_txt_data["link_summary"]["check_cap_reached"] == 1


# ------------------------------------------------------- off-site profiles

@pytest.mark.parametrize("url,problem", [
    ("/about", "not an absolute http(s) web address"),
    ("ftp://files.example/acme", "not an absolute http(s) web address"),
    ("https://www.acme.example/about", "points back at the site itself"),
    ("https://shop.acme.example/", "points back at the site itself"),
    ("https://twitter.com/intent/tweet?text=x", "share or widget link"),
    ("https://www.facebook.com/sharer/sharer.php?u=x", "share or widget link"),
    ("https://www.linkedin.com/", "platform home page"),
    ("https://github.com/acme", None),
    ("https://www.youtube.com/@acme", None),
])
def test_static_problem(url, problem):
    found = static_problem(url, "acme.example")
    assert (found is None) if problem is None else problem in found


def resp(status=200, body="", url="https://github.com/acme", ctype="text/html"):
    return Response(status, {"Content-Type": ctype}, body.encode(), url)


def html(title, og_title=None, body=""):
    og = f'<meta property="og:title" content="{og_title}">' if og_title else ""
    return f"<html><head><title>{title}</title>{og}</head><body>{body}</body></html>"


@pytest.mark.parametrize("response,status,verdict,detail", [
    (None, "robots_disallowed", "unverified", "robots_disallowed"),
    (resp(404, "missing"), "ok", "broken", "HTTP 404"),
    (resp(410, "gone"), "ok", "broken", "HTTP 410"),
    (resp(403, "challenge"), "ok", "unverified", "http_403"),
    (resp(200, "{}", ctype="application/json"), "ok", "unverified", "not_html"),
    (resp(200, html("Sign in"), url="https://github.com/login?return_to=acme"), "ok", "unverified", "login_wall"),
    (resp(200, html("Page not found · GitHub")), "ok", "soft_broken", "not available"),
    (resp(200, html("GitHub"), url="https://github.com/"), "ok", "soft_broken", "platform home page"),
    (resp(200, html("Someone", body='<a href="https://acme.example/">site</a>')), "ok", "verified", "links to the site"),
    (resp(200, html("Acme Widgets · GitHub")), "ok", "verified", "names the brand"),
    (resp(200, html("GitHub", body="<p>repos</p>"), url="https://github.com/acmewidgets"), "ok", "verified",
     "handle matches"),
    (resp(200, html("zenith (Zenith Traders) · GitHub", "zenith"), url="https://github.com/zenith"), "ok",
     "mismatch", "names neither the brand nor the site"),
    (resp(200, html("YouTube"), url="https://www.youtube.com/@zenith"), "ok", "unverified", "no_profile_metadata"),
    (resp(200, html("404 Media · GitHub"), url="https://github.com/404media"), "ok", "mismatch", "404media"),
])
def test_evaluate_profile(response, status, verdict, detail):
    url = response.final_url if response is not None and "login" not in response.final_url else "https://github.com/acme"
    if response is not None and response.final_url.rstrip("/") == "https://github.com":
        url = "https://github.com/acme"
    got_verdict, got_detail = evaluate_profile(url, response, status, "acme.example", ["Acme Widgets"])
    assert got_verdict == verdict and detail in got_detail


class FakeTransport:
    """Transport.get for one origin: robots enforcement and canned responses.
    A route is a body, (status, body), (status, body, final_url) or a failure
    status string such as "timeout"."""

    def __init__(self, origin, routes, log):
        self.origin, self.routes, self.log = origin, routes, log
        self.robots = None
        self.delay = 0.0

    def get(self, url, *, robots_exempt=False, max_bytes=None, headers=None):
        if not robots_exempt and self.robots is not None and not self.robots.can_fetch("x", url):
            return None, "robots_disallowed"
        self.log.append(url)
        route = self.routes.get(url)
        if route is None:
            route = next((v for k, v in self.routes.items() if k.endswith("*") and url.startswith(k[:-1])), None)
        if route is None:
            return Response(404, {"Content-Type": "text/html"}, b"missing", url), "ok"
        if isinstance(route, str) and route in ("timeout", "deadline", "failed"):
            return None, route
        status, body, final = (200, route, url) if isinstance(route, str) else (
            route + (url,) if len(route) == 2 else route)
        ctype = "text/plain" if url.endswith("robots.txt") else (
            "application/json" if body.lstrip().startswith("{") else "text/html")
        body = body.encode()
        return Response(status, {"Content-Type": ctype}, body[:max_bytes], final,
                        max_bytes is not None and len(body) > max_bytes), "ok"


def offsite_check(pages, routes, identity=IDENTITY, monkeypatch=None):
    log, made = [], []

    def factory(origin, deadline, limits):
        made.append(origin)
        return FakeTransport(origin, routes, log)

    if monkeypatch is not None:
        monkeypatch.setenv("OFF_SITE_LOOKUP", "1")
    inst = Instrumentation()
    result = check_off_site_profiles(snapshot(pages), identity, make_deadline(LIMITS), LIMITS, inst,
                                     transport_factory=factory)
    return result, log, made, inst


GH, TW, YT = "https://github.com", "https://twitter.com", "https://www.youtube.com"
ALLOW = "User-agent: *\nDisallow: /search\n"


def test_profiles_verified_broken_and_robots_blocked(monkeypatch):
    same_as = [GH + "/acme", GH + "/acme-old", TW + "/acme", YT + "/@acmewidgets"]
    routes = {GH + "/robots.txt": ALLOW, GH + "/acme": html("Acme Widgets · GitHub"),
              GH + "/acme-old": (404, "not found"),
              TW + "/robots.txt": "User-agent: *\nDisallow: /\n",
              YT + "/robots.txt": ALLOW, YT + "/@acmewidgets": (200, html("Acme Widgets - YouTube"),
                                                                 YT + "/channel/UCabcdefghijklmnopqrstuv")}
    result, log, made, inst = offsite_check([page(head=org(same_as))], routes, monkeypatch=monkeypatch)
    (broken,) = by_id(result, "profile-link-broken")
    assert broken["status"] == "confirmed" and broken["severity"] == "medium"
    assert "https://github.com/acme-old answers HTTP 404" in broken["evidence_text"]
    verdicts = {p["url"]: p["verdict"] for p in result["metrics"]["profiles"]}
    assert verdicts == {GH + "/acme": "verified", GH + "/acme-old": "broken", TW + "/acme": "unverified",
                        YT + "/@acmewidgets": "verified"}
    assert TW + "/acme" not in log  # robots.txt forbids it, so it is never requested
    assert result["metrics"]["robots"][TW] == "ok" and result["metrics"]["profiles_unverified"] == 1
    assert any("could not be verified" in w for w in result["warnings"])
    # robots.txt for three hosts plus three profile pages; the blocked page is not counted.
    assert inst.external_fetches_attempted == 6


def test_mismatched_profile_is_suspected(monkeypatch):
    routes = {GH + "/robots.txt": ALLOW, GH + "/zenith": html("zenith (Zenith Traders)", "zenith")}
    result, _, _, _ = offsite_check([page(head=org([GH + "/zenith"]))], routes, monkeypatch=monkeypatch)
    (finding,) = by_id(result, "profile-identity-mismatch")
    assert finding["status"] == "suspected" and "about 'zenith'" in finding["evidence_text"]


def test_unreadable_robots_fails_closed(monkeypatch):
    routes = {GH + "/robots.txt": (500, "error")}
    result, log, _, _ = offsite_check([page(head=org([GH + "/acme"]))], routes, monkeypatch=monkeypatch)
    assert log == [GH + "/robots.txt"]
    assert result["metrics"]["profiles"][0]["detail"] == "robots_unavailable"
    assert by_id(result, "profile-link-broken") == []


def test_dns_pool_rejections_are_retried_then_reported(monkeypatch):
    """url_safety turns a lookup away when its small DNS pool is busy; parallel
    profile lookups must retry rather than mark the host's robots.txt unreadable."""
    from external_lookup import DNS_RETRIES, ExternalLookup

    class Flaky(FakeTransport):
        failures = {}

        def get(self, url, **kwargs):
            left = Flaky.failures.get(url, 0)
            if left:
                Flaky.failures[url] = left - 1
                return None, "dns_error"
            return super().get(url, **kwargs)

    routes = {GH + "/robots.txt": ALLOW, GH + "/acme": html("Acme Widgets")}
    Flaky.failures = {GH + "/robots.txt": 2, GH + "/acme": 1}
    lookup = ExternalLookup(10 ** 9, LIMITS, Instrumentation(), lambda o, d, l: Flaky(o, routes, []))
    resp, status = lookup.get(GH + "/acme", 10_000)
    assert status == "ok" and lookup.robots[GH] == "ok"
    Flaky.failures = {GH + "/robots.txt": DNS_RETRIES + 1}
    inst = Instrumentation()
    lookup = ExternalLookup(10 ** 9, LIMITS, inst, lambda o, d, l: Flaky(o, routes, []))
    assert lookup.get(GH + "/acme", 10_000) == (None, "robots_unavailable")
    assert inst.external_fetches_attempted == 0  # no request ever reached a server


def test_per_host_cap_and_disabled_lookup(monkeypatch):
    same_as = [GH + f"/acme{i}" for i in range(4)]
    routes = {GH + "/robots.txt": ALLOW, GH + "/acme*": html("Acme Widgets")}
    result, log, _, _ = offsite_check([page(head=org(same_as))], routes, monkeypatch=monkeypatch)
    details = [p["detail"] for p in result["metrics"]["profiles"]]
    assert details.count("check_cap_reached") == 2 and len(log) == 3
    monkeypatch.setenv("OFF_SITE_LOOKUP", "0")
    inst = Instrumentation()
    result = check_off_site_profiles(snapshot([page(head=org(same_as))]), IDENTITY, make_deadline(LIMITS),
                                     LIMITS, inst, transport_factory=lambda *a: pytest.fail("no transport"))
    assert result["metrics"]["lookup"] == "disabled" and inst.external_fetches_attempted == 0


def test_static_problems_need_no_network(monkeypatch):
    same_as = ["/about", "https://twitter.com/intent/tweet", "https://www.wikidata.org/wiki/Q1", SITE + "/x"]
    result, log, made, _ = offsite_check([page(head=org(same_as))], {}, monkeypatch=monkeypatch)
    (finding,) = by_id(result, "profile-link-broken")
    assert finding["status"] == "confirmed" and made == [] and log == []
    assert "wikidata" not in finding["evidence_text"]  # the knowledge-graph check owns those links
    assert finding["evidence_text"].count("sameAs link") == 3


def test_review_platform_links_and_missing_profiles():
    linked = page('<footer><a href="https://www.trustpilot.com/review/acme.example">Reviews</a></footer>')
    result = check_off_site_profiles(snapshot([linked]), IDENTITY, make_deadline(LIMITS), LIMITS)
    assert result["metrics"]["review_platforms_linked"] == ["Trustpilot"]
    assert by_id(result, "review-platform-missing") == []
    local = page(head=org([], kind="Restaurant"))
    result = check_off_site_profiles(snapshot([local]), IDENTITY, make_deadline(LIMITS), LIMITS)
    (finding,) = by_id(result, "review-platform-missing")
    assert finding["status"] == "suspected" and "was not searched" in finding["evidence_text"]
    assert "Google Business Profile" in finding["suggested_action"]["summary"]


@pytest.mark.parametrize("head,url", [
    (org([], kind="GovernmentOrganization"), SITE + "/"),
    (org([], kind="NGO"), SITE + "/"),
    ("", "https://www.agency.gov/"),
    ("", "https://www.dept.gov.uk/"),
    ("", "https://www.cs.uni.ac.uk/"),
])
def test_review_platform_check_skips_public_bodies(head, url):
    artifacts = snapshot([page(head=head, url=url)])
    artifacts = AuditArtifacts(url, url.rstrip("/"), artifacts.pages, artifacts.robots_data, artifacts.llms_txt_data,
                               artifacts.sitemap_data, artifacts.acquisition_metadata, ())
    result = check_off_site_profiles(artifacts, IDENTITY, make_deadline(LIMITS), LIMITS)
    assert by_id(result, "review-platform-missing") == []
    assert result["metrics"]["business_kind"] == "public"
    assert result["metrics"]["review_platform_check"] == "not_applicable_public_body"


@pytest.mark.parametrize("hits,status,text", [
    ([{"url": "https://www.g2.com/products/acme/reviews"}, {"url": "https://news.example/acme"}],
     "confirmed", "Search found the brand on G2"),
    ([{"url": "https://news.example/acme"}], "confirmed", "a search for the brand's reviews found none"),
])
def test_review_platform_search_when_provider_configured(monkeypatch, hits, status, text):
    queries = []
    monkeypatch.setattr(offsite, "is_configured", lambda: True)
    monkeypatch.setattr(offsite, "search", lambda q, max_results, timeout_s: queries.append(q) or hits)
    result = check_off_site_profiles(snapshot([page()]), IDENTITY, make_deadline(LIMITS), LIMITS, Instrumentation())
    (finding,) = by_id(result, "review-platform-missing")
    assert finding["status"] == status and text in finding["evidence_text"]
    assert queries == ['"Acme Widgets" reviews']


def test_profile_lookups_do_not_spend_the_search_query_budget(monkeypatch):
    """Robots-checked profile and entity lookups are counted as external fetches but
    never use up MAX_EXTERNAL_FETCHES, which budgets search-provider queries."""
    inst = Instrumentation()
    for _ in range(LIMITS.MAX_EXTERNAL_FETCHES + 5):
        inst.record_external_fetch(ok=True)
    assert inst.external_fetches_attempted == LIMITS.MAX_EXTERNAL_FETCHES + 5
    assert inst.search_queries_attempted == 0
    queries = []
    monkeypatch.setattr(offsite, "is_configured", lambda: True)
    monkeypatch.setattr(offsite, "search", lambda q, max_results, timeout_s: queries.append(q) or [])
    check_off_site_profiles(snapshot([page()]), IDENTITY, make_deadline(LIMITS), LIMITS, inst)
    assert queries and inst.search_queries_attempted == 1
    assert inst.as_dict(None)["search_queries_attempted"] == 1
    for _ in range(LIMITS.MAX_EXTERNAL_FETCHES):
        inst.record_external_fetch(ok=True, search=True)
    result = check_off_site_profiles(snapshot([page()]), IDENTITY, make_deadline(LIMITS), LIMITS, inst)
    assert len(queries) == 1 and any("search query budget reached" in w for w in result["warnings"])


@pytest.mark.parametrize("url,expected", [
    ("https://www.trustpilot.com/review/acme.example", ("Trustpilot", "reviews")),
    ("https://uk.trustpilot.com/review/acme.example", ("Trustpilot", "reviews")),
    ("https://www.google.com/maps/place/Acme", ("Google Business Profile", "local")),
    ("https://maps.google.co.uk/?cid=1", ("Google Business Profile", "local")),
    ("https://g.page/acme", ("Google Business Profile", "local")),
    ("https://maps.app.goo.gl/abc", ("Google Business Profile", "local")),
    ("https://www.google.com/search?q=acme", None),
    ("https://www.g2.com/products/acme", ("G2", "software")),
    ("https://notg2.com/x", None),
    ("not a url", None),
])
def test_review_platform_registry(url, expected):
    assert review_platform(url) == expected


def test_video_platform_registry():
    assert video_platform("https://player.vimeo.com/video/1") == "Vimeo"
    assert video_platform("https://www.youtube-nocookie.com/embed/x") == "YouTube"
    assert video_platform("https://evilyoutube.com/embed/x") is None


def test_ag06_ingests_as_review_platform_missing(tmp_path, monkeypatch):
    path = tmp_path / "agent.json"
    path.write_text(json.dumps([{"check": "AG-06", "evidence": "No Trustpilot or G2 profile found for Acme"}]),
                    encoding="utf-8")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    (finding,) = ingest_agent_findings(SimpleNamespace(pages=()), {}, make_deadline(LIMITS))["findings"]
    assert finding["check_id"] == "review-platform-missing"
    assert finding["root_cause"] == get_entry("review-platform-missing")["mechanism"]


# ------------------------------------------------------------- web vitals

def test_document_loading_hints():
    doc = Document()
    doc.feed('<html><head><link rel="stylesheet" href="/a.css"><link rel="stylesheet" href="/p.css" media="print">'
             '<link rel="preload" as="image" href="/hero.jpg"><script src="https://cdn.other.example/x.js"></script>'
             '<script src="//tags.example.net/t.js" async></script><script src="/local.js"></script>'
             '<script>var a = 1;</script><script type="application/ld+json">{"@type":"Thing"}</script></head>'
             '<body><header><img src="/logo.png"></header><img src="/icon.png" width="32" height="32">'
             '<img src="/hero.jpg" loading="lazy" fetchpriority="low"><img src="/second.jpg"></body></html>')
    doc.close()
    f = doc.features()
    assert f["blocking_stylesheets"] == 1 and f["preload_images"] == 1
    assert f["script_hosts"] == ["cdn.other.example", "tags.example.net"] and f["external_scripts"] == 3
    assert f["inline_script_bytes"] == len("var a = 1;")
    assert f["lcp_image"]["src"] == "/hero.jpg" and f["lcp_image"]["loading"] == "lazy"


def test_page_factors_per_metric():
    heavy = page('<img src="/hero.jpg" loading="lazy">'
                 + "".join(f'<img src="/i{i}.jpg">' for i in range(6))
                 + '<iframe src="https://www.youtube.com/embed/x"></iframe>'
                 + "".join(f'<script src="https://t{i}.example.org/s.js"></script>' for i in range(31))
                 + "<script>" + "x" * 120_000 + "</script>",
                 head="".join(f'<link rel="stylesheet" href="/s{i}.css">' for i in range(8)), duration=2500)
    factors = page_factors(heavy, "acme.example")
    lcp_strong, lcp_moderate = factors["LCP"]
    assert lcp_strong == []
    assert "the first content image is lazy-loaded in the HTML" in lcp_moderate
    assert "the HTML took 2500 ms to arrive" in lcp_moderate
    assert "8 render-blocking scripts and stylesheets in the head" in lcp_moderate
    slow_strong, _ = page_factors(page("<p>x</p>", duration=3500), "acme.example")["LCP"]
    assert slow_strong == ["the HTML took 3500 ms to arrive"]
    _, cls = factors["CLS"]
    # The unsized first image is covered by "7 of 7 images", so it is not counted twice.
    assert cls == ["1 video or iframe embed(s) without reserved size", "7 of 7 images without width and height"]
    _, cls = page_factors(page('<img src="/hero.jpg"><iframe src="/map"></iframe>'), "acme.example")["CLS"]
    assert cls == ["1 video or iframe embed(s) without reserved size",
                   "the first content image has no width and height"]
    inp_strong, inp_moderate = factors["INP"]
    assert inp_strong == [] and len(inp_moderate) == 3


def test_static_estimates_need_one_strong_or_two_moderate_patterns():
    lazy_and_slow = page('<img src="/hero.jpg" loading="lazy" width="800" height="400">', url=SITE + "/a",
                         duration=2000)
    one_moderate = page('<iframe src="https://www.youtube.com/embed/x"></iframe>', url=SITE + "/b")
    lazy_only = page('<img src="/hero.jpg" loading="lazy" width="800" height="400">', url=SITE + "/c")
    result = analyze_web_vitals(snapshot([lazy_and_slow, one_moderate, lazy_only]), make_deadline(LIMITS))
    (finding,) = result["findings"]
    assert finding["check_id"] == "cwv-risk" and finding["status"] == "suspected"
    assert "Largest Contentful Paint" in finding["title"] and finding["affected_pages"] == [SITE + "/a"]
    assert result["metrics"]["web_vitals_mode"] == "static_estimate"
    assert result["metrics"]["web_vitals_field_lookup"] == "not_configured"


def psi(lcp=None, cls=None, inp=None, origin_fallback=False, key="INTERACTION_TO_NEXT_PAINT"):
    metrics = {}
    if lcp is not None:
        metrics["LARGEST_CONTENTFUL_PAINT_MS"] = {"percentile": lcp, "category": "X"}
    if cls is not None:
        metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"] = {"percentile": cls}
    if inp is not None:
        metrics[key] = {"percentile": inp}
    block = {"metrics": metrics}
    if origin_fallback:
        block["origin_fallback"] = True
    return block


def test_parse_field_data_scopes_scaling_and_ratings():
    parsed = parse_response({"loadingExperience": psi(2400, 12, 600)})
    assert parsed["scope"] == "url"
    assert parsed["metrics"] == {"LCP": {"p75": 2400.0, "rating": "good"},
                                 "CLS": {"p75": 0.12, "rating": "needs_improvement"},
                                 "INP": {"p75": 600.0, "rating": "poor"}}
    parsed = parse_response({"loadingExperience": psi(5000, origin_fallback=True),
                             "originLoadingExperience": psi(3000, inp=150, key="EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT")})
    assert parsed["scope"] == "origin" and parsed["metrics"]["INP"]["rating"] == "good"
    assert parse_response({"loadingExperience": {}})["status"] == "no_field_data"
    assert parse_response({"loadingExperience": psi(lcp="fast")})["status"] == "no_field_data"
    assert parse_response([])["status"] == "malformed_response"


class Handle:
    def __init__(self, result):
        self.value = result

    def result(self, timeout):
        return self.value


def test_field_data_drives_findings_and_suppresses_good_estimates():
    lazy = page('<img src="/hero.jpg" loading="lazy" width="800" height="400">', duration=3500)
    field = {"status": "ok", "scope": "origin",
             "metrics": {"LCP": {"p75": 1900.0, "rating": "good"}, "INP": {"p75": 650.0, "rating": "poor"}}}
    result = analyze_web_vitals(snapshot([lazy]), make_deadline(LIMITS), Handle(field))
    (finding,) = result["findings"]
    assert finding["check_id"] == "cwv-field-poor" and finding["severity"] == "medium"
    assert "Interaction to Next Paint (INP) 75th percentile is 650 ms, rated poor" in finding["evidence_text"]
    assert "for the whole origin" in finding["evidence_text"]
    assert result["metrics"]["web_vitals_estimates_suppressed_by_field_data"] == ["LCP"]
    assert result["metrics"]["web_vitals_field"]["LCP"] == {"p75": 1900.0, "unit": "ms", "rating": "good"}
    middling = {"status": "ok", "scope": "url", "metrics": {"CLS": {"p75": 0.2, "rating": "needs_improvement"}}}
    (finding,) = [f for f in analyze_web_vitals(snapshot([page()]), make_deadline(LIMITS), Handle(middling))["findings"]]
    assert finding["severity"] == "low" and "0.20" in finding["evidence_text"]
    failed = analyze_web_vitals(snapshot([page()]), make_deadline(LIMITS), Handle({"status": "http_429"}))
    assert failed["metrics"]["web_vitals_field_lookup"] == "http_429" and failed["findings"] == []


def test_fetch_field_vitals_reads_robots_and_keeps_key_out_of_result(monkeypatch):
    monkeypatch.setenv(KEY_ENV, "secret-key")
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?*"
    log = []
    routes = {"https://www.googleapis.com/robots.txt": (404, "missing"),
              api: json.dumps({"loadingExperience": psi(4500, 5, 100)})}
    inst = Instrumentation()
    result = fetch_field_vitals(SITE + "/", 10 ** 9, LIMITS, inst,
                                transport_factory=lambda o, d, l: FakeTransport(o, routes, log))
    assert result["metrics"]["LCP"]["rating"] == "poor" and result["scope"] == "url"
    assert log[0].endswith("/robots.txt") and "key=secret-key" in log[1] and "url=https%3A%2F%2Facme.example%2F" in log[1]
    assert "secret" not in json.dumps(result) and inst.external_fetches_attempted == 2
    routes[api] = (429, '{"error": "quota"}')
    assert fetch_field_vitals(SITE + "/", 10 ** 9, LIMITS, None,
                              transport_factory=lambda o, d, l: FakeTransport(o, routes, []))["status"] == "http_429"


def test_field_lookup_starts_only_with_a_key_and_a_public_target(monkeypatch):
    deadline = make_deadline(LIMITS)
    assert start_field_lookup(SITE, deadline, LIMITS) is None  # conftest removes the key
    monkeypatch.setenv(KEY_ENV, "k")
    monkeypatch.setenv(LOOKUP_ENV, "1")
    assert start_field_lookup(SITE, deadline, LIMITS, allow_private_targets=True) is None
    routes = {"https://www.googleapis.com/robots.txt": "User-agent: *\nDisallow: /\n"}
    handle = start_field_lookup(SITE, deadline, LIMITS,
                                transport_factory=lambda o, d, l: FakeTransport(o, routes, []))
    assert handle.result(timeout=5) == {"status": "robots_disallowed"}


# ---------------------------------------------------------------- reporting

def test_limitations_cover_new_unassessed_areas():
    artifacts = SimpleNamespace(robots_data={}, sitemap_data={"status": "ok"}, media_data=None)
    caps = {"headless_rendering": True, "external_search": True}
    coverage = {"off_site_profiles": {"lookup": "completed", "profiles_unverified": 2,
                                      "review_platform_search": "not_run", "review_platforms_linked": []},
                "web_vitals": {"web_vitals_mode": "static_estimate", "web_vitals_field_lookup": "http_429"},
                "llms_txt": {"llms_txt_link_outcomes": {"ok": 2, "check_cap_reached": 3}}}
    text = " ".join(derive_limitations(artifacts, caps, coverage, "completed"))
    assert "2 linked off-site profile(s) could not be verified" in text
    assert "(AG-06) was not supplied" in text
    assert "the field-data lookup did not complete (http_429)" in text
    assert "3 link(s) listed in llms.txt were not checked" in text
    coverage = {"off_site_profiles": {"lookup": "completed", "review_platforms_linked": ["G2"]},
                "web_vitals": {"web_vitals_mode": "field_data"}, "llms_txt": {"llms_txt_link_outcomes": {"ok": 1}}}
    assert derive_limitations(artifacts, caps, coverage, "completed") == []


def test_new_catalog_entries_are_complete():
    for check_id in ("llms-txt-invalid", "llms-txt-broken-links", "profile-link-broken",
                     "profile-identity-mismatch", "review-platform-missing", "cwv-field-poor", "cwv-risk"):
        assert check_id in CATALOG and get_entry(check_id)


def test_rich_fixture_audit_reports_every_new_check():
    base, stop = start_server(rich=True)
    try:
        report = run_audit(base + "/", Limits(TOTAL_AUDIT_TIMEOUT_S=60, REQUEST_DELAY_S=0),
                           allow_private_targets=True)
    finally:
        stop()
    found = {f["check_id"] for f in report["findings"]}
    assert {"alt-text-quality", "media-transcript-missing", "media-schema-missing", "citation-schema-invalid",
            "citation-schema-opportunity", "author-missing", "author-credentials-weak", "llms-txt-invalid",
            "llms-txt-broken-links", "profile-link-broken", "cwv-risk"} <= found
    assert "review-platform-missing" not in found  # the footer links a Trustpilot profile
    assert not any("Dropped" in w for w in report["warnings"])
    coverage = report["coverage"]
    assert coverage["llms_txt"]["llms_full_txt_status"] == "malformed"
    assert coverage["off_site_profiles"]["lookup"] == "disabled"
    assert coverage["web_vitals"]["web_vitals_mode"] == "static_estimate"
    assert coverage["capabilities"]["web_vitals_mode"] == "static_estimate"
    assert coverage["external_fetches"] == 0
    assert any("Core Web Vitals (LCP, CLS, INP) were not measured" in line for line in report["limitations"])
    json.dumps(report, allow_nan=False)


def test_clean_fixture_raises_no_new_defects():
    base, stop = start_server(clean=True)
    try:
        report = run_audit(base + "/", Limits(TOTAL_AUDIT_TIMEOUT_S=60, REQUEST_DELAY_S=0),
                           allow_private_targets=True)
    finally:
        stop()
    new_rules = {"alt-text-quality", "media-transcript-missing", "media-schema-missing", "citation-schema-invalid",
                 "citation-schema-opportunity", "author-missing", "author-credentials-weak", "llms-txt-invalid",
                 "llms-txt-broken-links", "profile-link-broken", "profile-identity-mismatch", "cwv-field-poor",
                 "cwv-risk"}
    assert not {f["check_id"] for f in report["findings"]} & new_rules
