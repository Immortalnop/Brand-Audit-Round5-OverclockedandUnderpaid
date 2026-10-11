"""The whats_working section: a check is listed as passed only when its skill
finished, no finding or recommendation carries its check IDs, and the stated
observation holds on the snapshot. Unit tests build pages from HTML strings and
never touch the network; the end-to-end tests use the local fixture server."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

import whats_working as ww
from constants import Limits
from models import AuditArtifacts, freeze_value
from transport import Response
from acquire_site import _extract_page
from check_catalog import CATALOG
from report_markdown import render
from run_audit import run_audit, SITE_LEVEL_CHECKS
from fixtures_server import start_server

LIMITS = Limits()
SITE = "https://fixture.example"
ALL_KEYS = [c[0] for c in ww.CHECKS]
SITE_LEVEL_KEYS = {c[0] for c in ww.CHECKS if c[5]}
HEAD = ('<title>Acme bicycles</title><meta name="description" content="Bicycles made in Leeds.">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="canonical" href="{url}">'
        '<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "Organization", '
        '"name": "Acme", "url": "https://fixture.example/"}}</script>')
BODY = ('<h1>Acme bicycles</h1><img src="/bike.jpg" alt="A red touring bicycle" width="400" height="300">'
        '<p>' + 'Acme builds touring bicycles by hand and ships them across the country every week. ' * 8
        + '</p><a href="/about">About us</a>')


def page(url=SITE + "/", head=None, body=BODY, headers=None, lang="en"):
    lang_attr = f' lang="{lang}"' if lang else ""
    html = f"<html{lang_attr}><head>{HEAD.format(url=url) if head is None else head}</head><body>{body}</body></html>"
    response = Response(200, dict({"Content-Type": "text/html"}, **(headers or {})), html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


ROBOTS = {"status": "ok", "conservative_fail_closed": False, "general_disallow": False,
          "ai_crawler_directives": {"GPTBot": "allow", "OAI-SearchBot": "allow", "PerplexityBot": "allow"},
          "ai_crawler_section_blocks": {}}
LLMS = {"present": True, "status": "ok", "links": [SITE + "/about"], "structure_issues": []}
SITEMAP = {"status": "ok", "urls": [SITE + "/", SITE + "/about"], "url_entries": 2, "partial": []}


def snapshot(*pages, robots=None, llms=None, sitemap=None):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value(robots or ROBOTS),
                          freeze_value(llms or LLMS), freeze_value(sitemap or SITEMAP),
                          freeze_value({"coverage": coverage}), ())


def results(**overrides):
    names = {name for check in ww.CHECKS for name in check[2]}
    out = {name: {"status": "success"} for name in names}
    out["offer_expiry"] = {"status": "success", "metrics": {"offer_deadlines_found": 2,
                                                            "offer_expiry_pages_scanned": 2}}
    out["fact_consistency"] = {"status": "success", "metrics": {"facts_compared_with_text": 3,
                                                                "fact_consistency_pages": 2}}
    out["site_graph"] = {"status": "success",
                         "data": {"nodes": {SITE + "/": {}, SITE + "/about": {}}, "dead_ends": []}}
    out.update(overrides)
    return out


def keys(items):
    return [w["check"] for w in items]


def good_site():
    return snapshot(page(), page(SITE + "/about"))


# ------------------------------------------------------------- what passes

def test_a_site_that_passes_every_check_lists_them_all_in_order():
    items = ww.whats_working(good_site(), results(), [], [], pages_analyzed=2)
    assert keys(items) == ALL_KEYS
    assert [w["id"] for w in items] == [f"W-{i:03d}" for i in range(1, len(ALL_KEYS) + 1)]
    for w in items:
        assert w["title"] and w["evidence"].endswith(".")
        assert set(w["check_ids"]) <= set(CATALOG), w["check"]
        assert w["evidence"].isascii() and chr(0x2014) not in w["evidence"]
    by_key = {w["check"]: w for w in items}
    assert by_key["titles"]["pages_checked"] == 2 and "All 2 pages checked" in by_key["titles"]["evidence"]
    assert by_key["robots-txt"]["pages_checked"] is None
    assert "(AI search: OAI-SearchBot, PerplexityBot; model training: GPTBot)" in by_key["ai-crawler-access"]["evidence"]
    assert "All 2 offer end dates" in by_key["offer-dates"]["evidence"]
    assert by_key["fact-consistency"]["evidence"].startswith("3 facts stated in structured data")
    assert "lists 2 URLs" in by_key["sitemap"]["evidence"]
    assert "All 2 images" in by_key["image-alt"]["evidence"]


def test_output_is_deterministic():
    art = good_site()
    assert ww.whats_working(art, results(), [], [], 2) == ww.whats_working(art, results(), [], [], 2)
    json.dumps(ww.whats_working(art, results(), [], [], 2), allow_nan=False)


# ------------------------------------------------------------- never contradicts a finding

def test_a_reported_check_id_removes_the_check():
    finding = {"id": "F-001", "check_id": "missing-description"}
    assert "meta-descriptions" not in keys(ww.whats_working(good_site(), results(), [finding], [], 2))


def test_merged_check_ids_and_recommendation_links_count_as_reported():
    merged = {"id": "F-001", "check_id": "missing-alt", "check_ids": ["image-context-missing", "missing-alt"]}
    link = {"id": "R-001", "finding_id": "F-009", "check_id": "missing-canonical", "check_ids": []}
    found = keys(ww.whats_working(good_site(), results(), [merged], [link], 2))
    assert "image-alt" not in found and "canonical" not in found
    assert "titles" in found


# ------------------------------------------------------------- never shows a skipped check

def test_a_skill_that_did_not_finish_removes_its_checks():
    found = keys(ww.whats_working(good_site(), results(metadata={"status": "insufficient_evidence"}), [], [], 2))
    for key in ("https", "titles", "meta-descriptions", "language", "canonical"):
        assert key not in found, key
    assert "h1" in found
    assert "llms-txt" not in keys(ww.whats_working(good_site(), results(llms_txt={"status": "failed"}), [], [], 2))
    assert "internal-links" not in keys(ww.whats_working(good_site(), results(site_graph={}), [], [], 2))


def test_no_page_analyzed_lists_only_site_level_checks():
    items = ww.whats_working(good_site(), results(), [], [], pages_analyzed=0)
    assert set(keys(items)) == SITE_LEVEL_KEYS
    assert set(c for w in items for c in w["check_ids"]) <= SITE_LEVEL_CHECKS


def test_a_check_that_cannot_be_evaluated_is_not_listed(monkeypatch):
    def broken(ctx):
        raise RuntimeError("boom")
    checks = tuple((k, t, s, ids, broken if k == "titles" else fn, lvl) for k, t, s, ids, fn, lvl in ww.CHECKS)
    monkeypatch.setattr(ww, "CHECKS", checks)
    found = keys(ww.whats_working(good_site(), results(), [], [], 2))
    assert "titles" not in found and "meta-descriptions" in found


# ------------------------------------------------------------- the observation must hold

def test_one_page_without_a_title_or_description_is_enough_to_withhold_the_claim():
    bare = page(SITE + "/about", head=HEAD.format(url=SITE + "/about").replace("<title>Acme bicycles</title>", "")
                .replace('<meta name="description" content="Bicycles made in Leeds.">', ""))
    found = keys(ww.whats_working(snapshot(page(), bare), results(), [], [], 2))
    assert "titles" not in found and "meta-descriptions" not in found and "h1" in found


def test_missing_language_canonical_viewport_and_h1_are_each_withheld():
    head = ('<title>Acme</title><meta name="description" content="d">'
            '<script type="application/ld+json">{"@type": "Organization", "name": "Acme"}</script>')
    body = BODY.replace("<h1>Acme bicycles</h1>", "<h2>Acme bicycles</h2>")
    found = keys(ww.whats_working(snapshot(page(head=head, body=body, lang=None)), results(), [], [], 1))
    for key in ("language", "canonical", "viewport", "h1"):
        assert key not in found, key
    assert "titles" in found


def test_any_index_or_snippet_block_withholds_the_indexable_claim():
    noindex = page(SITE + "/about", head=HEAD.format(url=SITE + "/about") + '<meta name="robots" content="noindex">')
    googlebot = page(SITE + "/about", head=HEAD.format(url=SITE + "/about")
                     + '<meta name="googlebot" content="nosnippet">')
    header = page(SITE + "/about", headers={"x-robots-tag": "max-snippet:0"})
    for other in (noindex, googlebot, header):
        assert "indexable" not in keys(ww.whats_working(snapshot(page(), other), results(), [], [], 2))
    allowed = page(SITE + "/about", head=HEAD.format(url=SITE + "/about")
                   + '<meta name="robots" content="index, follow, max-snippet:-1">')
    assert "indexable" in keys(ww.whats_working(snapshot(page(), allowed), results(), [], [], 2))


def test_http_pages_and_error_pages_withhold_their_claims():
    plain = page("http://fixture.example/about")
    assert "https" not in keys(ww.whats_working(snapshot(page(), plain), results(), [], [], 2))
    html = b"<html><body>Gone</body></html>"
    gone = _extract_page(SITE + "/old", Response(404, {"Content-Type": "text/html"}, html, SITE + "/old"), 50, LIMITS)
    assert "http-status" not in keys(ww.whats_working(snapshot(page(), gone), results(), [], [], 1))


def test_a_page_built_by_javascript_withholds_the_raw_html_claim():
    shell = page(SITE + "/app", body='<div id="root"></div><script src="/static/app.js"></script>')
    assert "raw-html" not in keys(ww.whats_working(snapshot(page(), shell), results(), [], [], 2))


def test_nothing_to_look_at_is_not_a_pass():
    none_found = results(offer_expiry={"status": "success", "metrics": {"offer_deadlines_found": 0}},
                         fact_consistency={"status": "success", "metrics": {"facts_compared_with_text": 0}})
    found = keys(ww.whats_working(good_site(), none_found, [], [], 2))
    assert "offer-dates" not in found and "fact-consistency" not in found
    expired = {"id": "F-001", "check_id": "expired-offer"}
    assert "offer-dates" not in keys(ww.whats_working(good_site(), results(), [expired], [], 2))
    no_images = snapshot(page(body=BODY.replace('<img src="/bike.jpg" alt="A red touring bicycle" '
                                                'width="400" height="300">', "")))
    assert "image-alt" not in keys(ww.whats_working(no_images, results(), [], [], 1))
    missing_alt = snapshot(page(body=BODY.replace(' alt="A red touring bicycle"', "")))
    assert "image-alt" not in keys(ww.whats_working(missing_alt, results(), [], [], 1))
    no_jsonld = snapshot(page(head="<title>Acme</title>"))
    assert "structured-data" not in keys(ww.whats_working(no_jsonld, results(), [], [], 1))
    one_node = results(site_graph={"status": "success", "data": {"nodes": {SITE + "/": {}}, "dead_ends": []}})
    assert "internal-links" not in keys(ww.whats_working(good_site(), one_node, [], [], 2))


def test_site_level_claims_need_a_readable_and_open_robots_txt_sitemap_and_llms_txt():
    unknown = dict(ROBOTS, status="timeout", conservative_fail_closed=True, general_disallow=None,
                   ai_crawler_directives={})
    found = keys(ww.whats_working(snapshot(page(), robots=unknown), results(), [], [], 1))
    assert "robots-txt" not in found and "ai-crawler-access" not in found
    one_blocked = dict(ROBOTS, ai_crawler_directives=dict(ROBOTS["ai_crawler_directives"], GPTBot="disallow"))
    assert "ai-crawler-access" not in keys(ww.whats_working(snapshot(page(), robots=one_blocked), results(), [], [], 1))
    section = dict(ROBOTS, ai_crawler_section_blocks={"GPTBot": [SITE + "/docs"]})
    assert "ai-crawler-access" not in keys(ww.whats_working(snapshot(page(), robots=section), results(), [], [], 1))
    absent = dict(ROBOTS, status="absent")
    by_key = {w["check"]: w for w in ww.whats_working(snapshot(page(), robots=absent), results(), [], [], 1)}
    assert "HTTP 404" in by_key["robots-txt"]["evidence"]
    for sitemap in ({"status": "absent", "urls": []}, {"status": "ok", "urls": []}):
        assert "sitemap" not in keys(ww.whats_working(snapshot(page(), sitemap=sitemap), results(), [], [], 1))
    partial = dict(SITEMAP, partial=[SITE + "/sitemap.xml"])
    assert "at least 2 URLs" in {w["check"]: w for w in ww.whats_working(
        snapshot(page(), sitemap=partial), results(), [], [], 1)}["sitemap"]["evidence"]
    for llms in ({"present": False, "status": "absent"}, dict(LLMS, structure_issues=["no H1 title"]),
                 dict(LLMS, links=[])):
        assert "llms-txt" not in keys(ww.whats_working(snapshot(page(), llms=llms), results(), [], [], 1))


def test_markdown_shows_whats_working_and_never_repeats_a_linked_finding():
    finding = {"id": "F-001", "check_id": "no-llms-txt", "title": "No llms.txt file found", "severity": "low",
               "finding_type": "proactive_improvement", "status": "confirmed",
               "suggested_action": {"summary": "Publish an llms.txt", "steps": ["Create /llms.txt"]}}
    link = {"id": "R-001", "finding_id": "F-001", "check_id": "no-llms-txt", "title": "No llms.txt file found",
            "category": "ai_discoverability", "finding_type": "proactive_improvement", "status": "confirmed"}
    baseline = {"id": "R-002", "check_id": "baseline:engagement", "title": "Keep internal linking intentional",
                "suggested_action": {"summary": "Link new pages as they launch"}}
    md = render({"site": SITE + "/", "findings": [finding], "recommendations": [link, baseline],
                 "whats_working": [{"id": "W-001", "check": "titles", "title": "Every page has a title",
                                    "evidence": "All 3 pages checked have a document title."}]})
    section = md.split("## What's working", 1)[1].split("##", 1)[0]
    assert "Every page has a title" in section and "All 3 pages checked" in section
    others = md.split("## Other recommendations", 1)[1].split("##", 1)[0]
    assert "Keep internal linking intentional" in others and "llms.txt" not in others
    assert "## What's working" not in render({"site": SITE + "/", "whats_working": []})


# ------------------------------------------------------------- end to end

def test_full_audit_lists_only_checks_no_finding_contradicts():
    url, stop = start_server(clean=True)
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    items = report["whats_working"]
    assert items, "a clean fixture site passes some checks"
    reported = ww.reported_check_ids(report["findings"] + report["recommendations"])
    for w in items:
        assert not set(w["check_ids"]) & reported, w
    # The fixture is served over plain HTTP on loopback, so HTTPS is never claimed.
    assert "https" not in keys(items)
    md = render(report)
    assert "## What's working" in md and items[0]["title"] in md


def test_blocked_audit_lists_only_site_level_checks():
    url, stop = start_server(robots_body="User-agent: *\nDisallow: /\n")
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert report["coverage"]["pages_analyzed"] == 0
    assert set(keys(report["whats_working"])) <= SITE_LEVEL_KEYS
    assert "robots-txt" not in keys(report["whats_working"])
