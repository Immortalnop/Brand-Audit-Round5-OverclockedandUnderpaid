"""test_recall_and_calibration.py -- recall and calibration guards (Plan phases 3 and 4).

Recall:
  - a start URL (or its robots.txt) that redirects to another origin is
    re-anchored once on that origin, under that origin's own robots.txt;
  - a sitemap larger than the read budget, or gzipped, still yields its entries
    and is never reported as malformed;
  - AI crawlers disallowed on some sections only are reported;
  - with no Organization markup, the brand name is read from site metadata at
    reduced confidence.
Calibration:
  - overall confidence counts analyzed pages, not attempted ones, and leaves
    brand identity beside the score;
  - a confirmed finding has at least 0.7 confidence, and each finding states
    how much of the site it covers.

Every server here is a local http.server on 127.0.0.1; nothing leaves the machine.
"""
import gzip
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import Limits
from models import make_deadline, apply_status_floor, CONFIRMED_MIN_CONFIDENCE, make_finding
from instrumentation import Instrumentation
from acquire_site import acquire_site, _parse_sitemap, _ai_crawler_section_blocks
from robots_policy import RobotsPolicy

LIMITS = Limits()
TEXT = "Plain words about the offer and what it does for the people who use it every day. " * 12


def _html(title, body, head=""):
    return (f'<!doctype html><html lang="en"><head><title>{title}</title>{head}</head>'
            f"<body><main><h1>{title}</h1>{body}</main></body></html>").encode()


def serve(routes):
    """Serve {path: (status, headers, body)} on 127.0.0.1. A callable value gets
    the base URL and returns that tuple. Returns (base_url, stop, requests)."""
    seen = []
    holder = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append((self.command, self.path))
            route = routes.get(self.path.split("?")[0])
            if callable(route):
                route = route(holder["base"])
            status, headers, body = route or (404, {"Content-Type": "text/html"}, b"<h1>Not found</h1>")
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    holder["base"] = f"http://127.0.0.1:{httpd.server_address[1]}"

    def stop():
        httpd.shutdown()
        httpd.server_close()
    return holder["base"], stop, seen


def _site(robots="User-agent: *\nAllow: /\n"):
    nav = '<nav><a href="/">Home</a> <a href="/about">About</a> <a href="/blog/post">Post</a></nav>'
    return {"/robots.txt": (200, {"Content-Type": "text/plain"}, robots.encode()),
            "/": (200, {"Content-Type": "text/html"}, _html("Acme home", nav + "<p>" + TEXT + "</p>")),
            "/about": (200, {"Content-Type": "text/html"}, _html("About Acme", nav + "<p>" + TEXT + "</p>")),
            "/blog/post": (200, {"Content-Type": "text/html"}, _html("A post", nav + "<p>" + TEXT + "</p>"))}


def _acquire(url):
    return acquire_site(url, make_deadline(LIMITS), LIMITS, Instrumentation(), allow_private_targets=True)


# ---------------------------------------------------------------------------
# 3.1 Start URL redirected to another origin
# ---------------------------------------------------------------------------

def test_start_url_redirect_to_another_origin_is_audited_there():
    new, stop_new, seen_new = serve(_site())
    old, stop_old, seen_old = serve({
        "/robots.txt": (200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /\n"),
        "/": lambda base: (301, {"Location": new + "/"}, b""),
    })
    try:
        artifacts = _acquire(old + "/")
    finally:
        stop_new()
        stop_old()
    assert artifacts.site_url == new + "/" and artifacts.normalized_origin == new
    assert artifacts.acquisition_metadata["coverage"]["urls_analyzed"] >= 3
    moved = artifacts.acquisition_metadata["start_redirect"]
    assert moved["requested_url"] == old + "/" and moved["audited_url"] == new + "/" and moved["via"] == "start_url"
    assert any("redirects to another site" in w for w in artifacts.warnings)
    paths_new = [p for _, p in seen_new]
    # The new origin's robots.txt is read before any of its pages.
    assert paths_new[0] == "/robots.txt"
    assert {m for m, _ in seen_new + seen_old} == {"GET"}


def test_redirected_robots_txt_moves_the_audit_and_keeps_the_path():
    new, stop_new, seen_new = serve(_site())
    old, stop_old, _ = serve({"/robots.txt": lambda base: (301, {"Location": new + "/robots.txt"}, b"")})
    try:
        artifacts = _acquire(old + "/about")
    finally:
        stop_new()
        stop_old()
    assert artifacts.site_url == new + "/about"
    assert artifacts.acquisition_metadata["start_redirect"]["via"] == "robots_txt"
    assert artifacts.pages and artifacts.pages[0].url == new + "/about"


def test_new_origin_robots_rules_are_obeyed():
    new, stop_new, seen_new = serve(_site(robots="User-agent: *\nDisallow: /\n"))
    old, stop_old, _ = serve({"/robots.txt": (200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /\n"),
                              "/": lambda base: (302, {"Location": new + "/"}, b"")})
    try:
        artifacts = _acquire(old + "/")
    finally:
        stop_new()
        stop_old()
    assert artifacts.site_url == new + "/"
    assert [p for _, p in seen_new if p != "/robots.txt"] == []
    assert not artifacts.pages


def test_audited_origin_is_not_moved_by_a_later_redirect():
    # The start page itself is served; only an inner link redirects elsewhere.
    other, stop_other, seen_other = serve(_site())
    routes = _site()
    routes["/about"] = (lambda base: (301, {"Location": other + "/about"}, b""))
    base, stop, _ = serve(routes)
    try:
        artifacts = _acquire(base + "/")
    finally:
        stop()
        stop_other()
    assert artifacts.site_url == base + "/" and "start_redirect" not in artifacts.acquisition_metadata
    assert seen_other == []


def test_unresolvable_redirect_target_is_reported_not_followed():
    old, stop_old, _ = serve({"/robots.txt": (200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /\n"),
                              "/": (301, {"Location": "https://moved.invalid.test/"}, b"")})
    try:
        artifacts = _acquire(old + "/")
    finally:
        stop_old()
    assert artifacts.site_url == old + "/"
    assert any("could not be resolved, so it was not audited" in w for w in artifacts.warnings)


def test_redirect_is_named_in_the_report(monkeypatch):
    from run_audit import run_audit
    for key, value in {"OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0", "FIELD_VITALS_LOOKUP": "0",
                       "SEARCH_API_URL": "", "AGENT_FINDINGS_PATH": "", "ENABLE_RENDERING": "0",
                       "AUDIT_PROGRESS": "0"}.items():
        monkeypatch.setenv(key, value)
    new, stop_new, _ = serve(_site())
    old, stop_old, _ = serve({"/robots.txt": (200, {"Content-Type": "text/plain"}, b"User-agent: *\nAllow: /\n"),
                              "/": lambda base: (301, {"Location": new + "/"}, b"")})
    try:
        report = run_audit(old + "/", Limits(), allow_private_targets=True)
    finally:
        stop_new()
        stop_old()
    assert report["site"] == old + "/" and report["coverage"]["audited_url"] == new + "/"
    assert report["coverage"]["start_redirect"]["audited_url"] == new + "/"
    assert any("audited " + new + "/ instead" in line for line in report["limitations"])
    assert report["coverage"]["pages_analyzed"] >= 3 and report["confidence"]["score"] > 0


# ---------------------------------------------------------------------------
# 3.2 Large and gzipped sitemaps
# ---------------------------------------------------------------------------

def _urlset(base, count, pad=0):
    filler = "<!--" + "x" * pad + "-->" if pad else ""
    return ("<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            + "".join(f"<url><loc>{base}/p{i}</loc><lastmod>2026-01-0{1 + i % 9}</lastmod>{filler}</url>"
                      for i in range(count)) + "</urlset>").encode()


def test_sitemap_larger_than_the_read_budget_yields_its_entries():
    routes = _site(robots="User-agent: *\nAllow: /\n")
    routes["/sitemap.xml"] = lambda base: (200, {"Content-Type": "application/xml"}, _urlset(base, 3000, pad=300))
    base, stop, _ = serve(routes)
    try:
        artifacts = _acquire(base + "/")
    finally:
        stop()
    sitemap = artifacts.sitemap_data
    assert sitemap["status"] == "ok" and sitemap["discovered"]
    assert list(sitemap["partial"]) == [base + "/sitemap.xml"]
    assert len(sitemap["urls"]) == 200 and sitemap["checked"][0]["truncated"]


def test_gzipped_sitemap_is_read():
    routes = _site(robots="User-agent: *\nAllow: /\nSitemap: /sitemap.xml.gz\n")
    routes["/sitemap.xml.gz"] = lambda base: (200, {"Content-Type": "application/gzip"}, gzip.compress(_urlset(base, 5)))
    base, stop, _ = serve(routes)
    try:
        artifacts = _acquire(base + "/")
    finally:
        stop()
    assert artifacts.sitemap_data["status"] == "ok" and len(artifacts.sitemap_data["urls"]) == 5
    assert list(artifacts.sitemap_data["partial"]) == []


@pytest.mark.parametrize("content,truncated", [
    (b"<html><body>Not a sitemap</body></html>", False),
    (b"<?xml version='1.0'?><!DOCTYPE urlset [<!ENTITY a 'b'>]><urlset><url><loc>&a;</loc></url></urlset>", False),
    (b"<urlset><url><loc>https://a.test/</loc></url>", False),
    (b"<urlset><url><loc>https://a.test/x", True),
])
def test_invalid_sitemaps_are_still_malformed(content, truncated):
    with pytest.raises(ET.ParseError):
        _parse_sitemap(content, truncated)


def test_sitemap_parser_reads_index_and_empty_sets():
    kind, locs, entries = _parse_sitemap(b"<sitemapindex><sitemap><loc>https://a.test/s1.xml</loc></sitemap>"
                                         b"<sitemap><loc>https://a.test/s2.xml</loc></sitemap></sitemapindex>", False)
    assert kind == "sitemapindex" and locs == ["https://a.test/s1.xml", "https://a.test/s2.xml"] and entries == []
    assert _parse_sitemap(b"<urlset></urlset>", False) == ("urlset", [], [])
    kind, locs, entries = _parse_sitemap(b"<urlset><url><loc>https://a.test/1</loc></url><url><loc>https://a", True)
    assert locs == ["https://a.test/1"] and len(entries) == 1


# ---------------------------------------------------------------------------
# 3.3 AI crawlers blocked from some sections
# ---------------------------------------------------------------------------

_ROBOTS = ("User-agent: GPTBot\nDisallow: /blog/\n\nUser-agent: OAI-SearchBot\nDisallow: /docs/\n\n"
           "User-agent: *\nDisallow: /admin/\nAllow: /\n")
_URLS = ["https://a.test/", "https://a.test/blog/post", "https://a.test/docs/start", "https://a.test/admin/x",
         "https://a.test/about"]


def test_section_blocks_are_ai_specific():
    blocks = _ai_crawler_section_blocks(RobotsPolicy(_ROBOTS), _URLS, conservative=False)
    assert blocks["GPTBot"] == ["https://a.test/blog/post"]
    assert blocks["OAI-SearchBot"] == ["https://a.test/docs/start"]
    # /admin/ is closed to every crawler: a general choice, not reported.
    assert not any("admin" in u for urls in blocks.values() for u in urls)
    assert _ai_crawler_section_blocks(RobotsPolicy(_ROBOTS), _URLS, conservative=True) == {}


def _robots_artifacts(section_blocks, directives=None):
    return SimpleNamespace(robots_data={"status": "ok", "ai_crawler_directives": directives or {},
                                        "ai_crawler_section_blocks": section_blocks},
                           site_url="https://a.test/")


def test_section_block_findings():
    from check_ai_crawler_access import check_ai_crawler_access
    result = check_ai_crawler_access(_robots_artifacts({"OAI-SearchBot": ["https://a.test/docs/start"]}),
                                     make_deadline(LIMITS))
    (finding,) = [f for f in result["findings"] if f["check_id"] == "ai-crawler-section-blocked"]
    assert finding["severity"] == "medium" and finding["status"] == "confirmed"
    assert finding["affected_pages"] == ["https://a.test/docs/start"]
    training = check_ai_crawler_access(_robots_artifacts({"GPTBot": ["https://a.test/blog/post"]}),
                                       make_deadline(LIMITS))
    (finding,) = [f for f in training["findings"] if f["check_id"] == "ai-crawler-section-blocked"]
    assert finding["severity"] == "low" and finding["finding_type"] == "proactive_improvement"
    # A crawler already blocked from the whole site is not reported again per section.
    whole = check_ai_crawler_access(_robots_artifacts({"GPTBot": ["https://a.test/blog/post"]},
                                                      {"GPTBot": "disallow"}), make_deadline(LIMITS))
    assert not [f for f in whole["findings"] if f["check_id"] == "ai-crawler-section-blocked"]


# ---------------------------------------------------------------------------
# 3.4 Brand name from site metadata
# ---------------------------------------------------------------------------

def _page(url, title, text="", meta=None, jsonld=(), page_type="other"):
    return SimpleNamespace(url=url, status_code=200, title=title, visible_text=text, page_type=page_type,
                           jsonld_blocks=jsonld, features={"meta": meta or {}})


def _identity(*pages):
    from resolve_entity_identity import resolve_entity_identity
    artifacts = SimpleNamespace(pages=pages, normalized_origin="https://a.test")
    return resolve_entity_identity(artifacts, SimpleNamespace(expired=lambda: False))


def test_name_from_agreeing_site_metadata():
    pages = [_page("https://a.test/", "Acme Tools", meta={"og:site_name": ["Acme Tools"]}, page_type="home")] + [
        _page(f"https://a.test/p{i}", f"Page {i} | Acme Tools") for i in range(3)]
    result = _identity(*pages)
    data = result["data"]
    assert result["status"] == "partial" and data["canonical_name"] == "Acme Tools"
    assert data["confidence"] == 0.6 and data["ambiguity_type"] == "name_from_site_metadata"
    assert data["identity_sources"] == ["og_site_name", "title_suffix"]
    from execution_summary import identity_resolution
    assert identity_resolution(result) == "name_from_site_metadata"


def test_single_source_and_copyright_line():
    one = _identity(_page("https://a.test/", "Home", jsonld=({"@type": "WebSite", "name": "Fellwalk"},),
                          page_type="home"))
    assert one["data"]["canonical_name"] == "Fellwalk" and one["data"]["confidence"] == 0.5
    footer = "© 2026 Harbour Plumbing Ltd. All rights reserved."
    two = _identity(_page("https://a.test/", "Home", TEXT + footer), _page("https://a.test/b", "B", TEXT + footer))
    assert two["data"]["canonical_name"] == "Harbour Plumbing Ltd"
    # A copyright line on one page only is not enough.
    assert _identity(_page("https://a.test/", "Home", TEXT + footer))["status"] == "insufficient_evidence"


def test_titles_without_a_shared_site_name_resolve_nothing():
    pages = [_page(f"https://a.test/p{i}", f"Topic {i} | Section {i}") for i in range(5)]
    assert _identity(*pages)["status"] == "insufficient_evidence"


def test_organization_markup_still_wins():
    pages = [_page("https://a.test/", "Home | Other", meta={"og:site_name": ["Other"]},
                   jsonld=({"@type": "Organization", "name": "Acme"},), page_type="home")]
    data = _identity(*pages)["data"]
    assert data["canonical_name"] == "Acme" and data["confidence"] >= 0.85


# ---------------------------------------------------------------------------
# 3.5 Page text held only in script data is covered in test_precision_traps.py
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 4. Calibration
# ---------------------------------------------------------------------------

def test_overall_confidence_counts_analyzed_pages_only():
    from execution_summary import overall_confidence
    attempted = overall_confidence({"pages_discovered": 10, "pages_fetched_attempted": 10, "pages_analyzed": 2},
                                   "completed")
    assert attempted["components"]["crawl_completeness"] == 0.2 and attempted["score"] == 0.2
    nothing = overall_confidence({"pages_discovered": 1, "pages_fetched_attempted": 1, "pages_analyzed": 0,
                                  "sections_discovered": 1, "sections_analyzed": 0}, "completed")
    assert nothing["score"] == 0.0 and nothing["limiting_factor"] == "sample_representativeness"
    assert "identity_confidence" not in nothing["method"].split(" where ")[0]


def _finding(status, confidence, severity="low"):
    return make_finding(category="engagement", finding_type="defect", severity=severity, status=status,
                        confidence=confidence, title="T", root_cause="R",
                        evidence=[{"type": "x", "description": "d", "urls": []}],
                        suggested_action={"summary": "s", "steps": ["s"], "priority": severity, "effort": "low",
                                          "expected_benefit": "b", "verification": "v"},
                        provenance={"skill": "s", "script": "x.py", "rule_id": "r"})


def test_low_confidence_cannot_be_confirmed():
    f = apply_status_floor(_finding("confirmed", 0.33))
    assert f["status"] == "suspected" and "below the 0.7" in f["status_note"]
    assert apply_status_floor(_finding("confirmed", CONFIRMED_MIN_CONFIDENCE))["status"] == "confirmed"
    assert "status_note" not in apply_status_floor(_finding("suspected", 0.3))


def test_floor_then_gate_lowers_an_unearned_high():
    from prioritize_findings import prioritize_findings
    f = _finding("confirmed", 0.4, severity="high")
    f["id"] = "F-001"
    prioritize_findings([f])
    assert f["status"] == "suspected" and f["severity"] == "medium"


def test_report_findings_carry_coverage_and_honest_status(monkeypatch):
    from run_audit import run_audit
    from archetype_sites import ARCHETYPES, serve as serve_site
    for key, value in {"OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0", "FIELD_VITALS_LOOKUP": "0",
                       "SEARCH_API_URL": "", "AGENT_FINDINGS_PATH": "", "ENABLE_RENDERING": "0",
                       "AUDIT_PROGRESS": "0"}.items():
        monkeypatch.setenv(key, value)
    base, stop, _ = serve_site(ARCHETYPES["blog"])
    try:
        report = run_audit(base + "/", Limits(), allow_private_targets=True)
    finally:
        stop()
    assert report["findings"]
    for f in report["findings"]:
        assert f["coverage"]["pages_analyzed"] == report["coverage"]["pages_analyzed"]
        assert f["coverage"]["affected_pages"] == len(f["affected_pages"])
        assert f["status"] != "confirmed" or f["confidence"] >= CONFIRMED_MIN_CONFIDENCE
    # The blog has Organization markup on its home page only; identity sits beside the score.
    assert report["confidence"]["score"] == min(report["confidence"]["components"]["sample_representativeness"],
                                                report["confidence"]["components"]["execution_penalty"])


def test_markdown_states_reach_and_status_note():
    from report_markdown import render
    finding = {"id": "F-001", "title": "T", "severity": "low", "status": "suspected", "confidence": 0.33,
               "status_note": "Reported as suspected: its confidence (0.33) is below the 0.7 a confirmed finding needs.",
               "coverage": {"affected_pages": 3, "pages_analyzed": 40, "pages_discovered": 800},
               "affected_pages": [], "evidence": [], "suggested_action": {"summary": "s", "steps": []}}
    md = render({"site": "https://a.test/", "findings": [finding]})
    assert "Seen on 3 of 40 analyzed page(s)" in md and "below the 0.7 a confirmed finding needs" in md
