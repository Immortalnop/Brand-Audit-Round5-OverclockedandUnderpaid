"""Points 6 to 11: concrete finding titles, personalization and context signals,
answer formats, ready-to-paste fix snippets, readable implementation details,
and the impact x effort plan.

Unit tests build pages from HTML strings and never touch the network; the
end-to-end test runs against the local fixture server only.
"""
import json
import re
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline, make_finding, join_steps
from transport import Response
from acquire_site import _extract_page
from check_catalog import CATALOG
from capabilities import CHECK_TIERS
from analyze_metadata import analyze_metadata
from analyze_performance import analyze_performance
from analyze_experience import analyze_experience
from analyze_answer_format import analyze_answer_format, answer_problem
from analyze_context_signals import analyze_context_signals
from analyze_context_retention import analyze_context_retention
from fix_snippets import site_facts, build_snippet, attach_fix_snippets
from prioritize_findings import impact_of, quadrant_of, annotate_action_plan, top_actions, quick_wins
from run_audit import run_audit
from fixtures_server import start_server

LIMITS = Limits()
SITE = "https://fixture.example"
NEW_IDS = {"question-answer-indirect", "table-headers-missing", "comparison-table-missing", "spec-list-missing",
           "location-markup-missing", "local-business-incomplete", "audience-segment-missing",
           "site-search-missing", "context-retention-missing", "deep-link-params-dropped"}
TEXT = "<p>" + "Plain words about the offer and what it does for the people who use it every day. " * 15 + "</p>"


def page(body="", head="", url=SITE + "/", lang="en", final_url=None):
    lang_attr = f' lang="{lang}"' if lang else ""
    html = f"<html{lang_attr}><head>{head}</head><body>{body}</body></html>"
    response = Response(200, {"Content-Type": "text/html"}, html.encode(), final_url or url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def snapshot(*pages, sitemap=None, discovered=None):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": discovered or len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": False, "status": "absent"}),
                          freeze_value(sitemap or {"status": "ok"}),
                          freeze_value({"coverage": coverage}), ())


def run(check, *pages, **kw):
    return check(snapshot(*pages, **kw), make_deadline(LIMITS))


def by_id(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj) + "</script>"


# ------------------------------------------------------------- wiring

def test_new_checks_are_catalogued_and_tiered():
    assert NEW_IDS <= set(CATALOG)
    for key in ("answer_format_checks", "location_and_audience_signals", "context_retention_checks",
                "fix_snippets", "impact_effort_matrix"):
        assert CHECK_TIERS[key] == "executable"


def test_new_checks_respect_expired_deadline():
    expired = make_deadline(replace(LIMITS, TOTAL_AUDIT_TIMEOUT_S=0.000001))
    for check in (analyze_answer_format, analyze_context_signals, analyze_context_retention):
        result = check(snapshot(page(TEXT)), expired)
        assert result["status"] == "insufficient_evidence" and not result["findings"]


# ------------------------------------------------------------- 10: readable steps

def test_join_steps_ends_every_step_as_a_sentence():
    assert join_steps(["Identify page types", "Add matching blocks."]) == "Identify page types. Add matching blocks."
    assert join_steps(["  spaced   out ", "", "Done!"]) == "spaced out. Done!"
    assert join_steps([]) == ""


_JOINED = re.compile(r"[a-z0-9)] (?:Add|Identify|Check|Create|List|Link|Re-run|Repair|Correct|Validate|Preserve"
                     r"|Structure|Use|Place|Expose|Ensure|Audit|Open|Compare|Remove|Give|Write|Confirm|Point"
                     r"|Publish|Set|State)\b")


def test_no_catalog_entry_runs_steps_together():
    for check_id, entry in CATALOG.items():
        assert not _JOINED.search(entry["implementation_detail"]), check_id


def test_uncatalogued_finding_joins_steps_with_sentence_breaks():
    finding = make_finding("engagement", "defect", "low", "confirmed", 0.9, "t", "cause", [],
                           {"summary": "s", "steps": ["Identify page types", "Add blocks"], "priority": "low"},
                           {"rule_id": "not-in-catalog"})
    assert finding["suggested_action"]["implementation_detail"] == "Identify page types. Add blocks."


# ------------------------------------------------------------- 6: concrete titles

def test_no_heuristic_title_asks_the_reader_to_review():
    bare = page("<p>" + "word " * 120 + "</p>", head="<title>A</title>")
    titles = [f["title"] for check in (analyze_metadata, analyze_performance, analyze_experience)
              for f in run(check, bare, sitemap={"status": "absent"})["findings"]]
    assert titles and not [t for t in titles if t.startswith(("Review", "Consider"))], titles


def test_titles_state_the_gap_with_counts():
    full = page("<main><h1>Topic</h1></main>", head='<title>Acme useful topic guide</title>'
                '<meta property="og:title" content="A"><meta property="og:url" content="https://fixture.example/">')
    bare = page("<main><h1>Other</h1></main>", head="<title>Acme other useful topic</title>", url=SITE + "/b")
    result = run(analyze_metadata, full, bare)
    og = by_id(result, "social-metadata")[0]["title"]
    assert og.startswith("Open Graph tags missing: og:description on 2/2 sampled pages, og:image on 2/2")
    assert "og:title on 1/2" in og and "og:url on 1/2" in og
    assert by_id(result, "missing-canonical")[0]["title"] == "No rel=canonical tag on 2/2 sampled pages"
    assert by_id(result, "twitter-card")[0]["title"] == "No valid twitter:card tag on 2/2 sampled pages"


def test_sitemap_title_names_the_status():
    one = page(TEXT)
    assert by_id(run(analyze_performance, one, sitemap={"status": "absent"}), "sitemap-unavailable")[0]["title"] \
        == "No XML sitemap found"
    assert by_id(run(analyze_performance, one, sitemap={"status": "malformed"}), "sitemap-unavailable")[0]["title"] \
        == "XML sitemap could not be parsed"


# ------------------------------------------------------------- 8: answer formats

@pytest.mark.parametrize("answer,fragment", [
    ("Acme is a scheduling tool for clinics.", None),
    ("", "no text"),
    ("Great question. Acme is a tool.", "filler"),
    ("In this article we explain everything.", "filler"),
    (" ".join(["word"] * 45) + ".", "45 words"),
])
def test_answer_problem(answer, fragment):
    problem = answer_problem(answer)
    assert (problem is None) if fragment is None else (fragment in problem)


def test_question_heading_without_direct_answer_is_reported():
    good = page("<h2>What is Acme?</h2><p>Acme is a scheduling tool for clinics.</p>")
    bad = page("<h2>How much does it cost?</h2><p>Great question, let us explain.</p><h2>Why?</h2><h2>Next</h2>",
               url=SITE + "/faq")
    result = run(analyze_answer_format, good, bad)
    finding = by_id(result, "question-answer-indirect")[0]
    assert finding["affected_pages"] == [SITE + "/faq"] and finding["status"] == "suspected"
    text = finding["evidence"][0]["description"]
    assert "filler" in text and "no text before the next heading" in text
    assert result["metrics"]["answer_format_question_headings_checked"] == 3


def test_cta_headings_and_questions_answered_by_subheadings_are_not_reported():
    long_cta = " ".join(["Contact the admissions office by phone or email"] * 8)
    html = (f"<h2>Need more information?</h2><p>{long_cta}</p>"
            "<h2>Want to be a part of our school?</h2><p>" + long_cta + "</p>"
            "<h2>Why choose Acme?</h2><h3>Faculty</h3><p>Small classes.</p><h3>Campus</h3><p>Green.</p>")
    result = run(analyze_answer_format, page(html))
    assert not by_id(result, "question-answer-indirect")
    assert result["metrics"]["answer_format_question_headings_checked"] == 0


def test_question_check_is_english_only():
    french = page("<h2>Pourquoi?</h2><h2>Suite</h2>", lang="fr")
    assert not by_id(run(analyze_answer_format, french), "question-answer-indirect")


def test_table_without_header_cells_is_a_defect_and_layout_tables_are_ignored():
    bare = page("<table><tr><td>Plan</td><td>Price</td></tr><tr><td>Pro</td><td>10</td></tr></table>")
    labelled = page("<table><tr><th>Plan</th><th>Price</th></tr><tr><td>Pro</td><td>10</td></tr></table>",
                    url=SITE + "/b")
    layout = page('<table role="presentation"><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>',
                  url=SITE + "/c")
    finding = by_id(run(analyze_answer_format, bare, labelled, layout), "table-headers-missing")[0]
    assert finding["affected_pages"] == [SITE + "/"] and finding["finding_type"] == "defect"
    assert "2 rows x 2 columns" in finding["evidence"][0]["description"]


def test_comparison_page_without_table_and_product_without_spec_list():
    compare = page(TEXT, head="<title>Acme vs Rival: which is better</title>", url=SITE + "/acme-vs-rival")
    product = page(TEXT, url=SITE + "/products/widget")
    listed = page(TEXT + "<ul><li>Size: 3 m</li><li>Weight: 2 kg</li><li>Colour: red</li></ul>",
                  url=SITE + "/products/gadget")
    result = run(analyze_answer_format, compare, product, listed)
    assert by_id(result, "comparison-table-missing")[0]["affected_pages"] == [SITE + "/acme-vs-rival"]
    assert by_id(result, "spec-list-missing")[0]["affected_pages"] == [SITE + "/products/widget"]


def test_well_formatted_pages_are_quiet():
    html = ("<h2>What is Acme?</h2><p>Acme is a tool.</p>"
            "<table><caption>Plans</caption><tr><th>Plan</th><th>Price</th></tr><tr><td>A</td><td>1</td></tr></table>")
    assert run(analyze_answer_format, page(html, head="<title>Acme comparison</title>"))["findings"] == []


# ------------------------------------------------------------- 7: personalization and context

def test_location_shown_without_markup_is_a_confirmed_defect_with_two_kinds_of_evidence():
    html = ('<address>12 High Street, Springfield 4000</address>'
            '<iframe src="https://www.google.com/maps/embed?pb=1"></iframe>')
    finding = by_id(run(analyze_context_signals, page(html)), "location-markup-missing")[0]
    assert finding["finding_type"] == "defect" and finding["severity"] == "medium"
    assert "12 High Street" in finding["evidence"][0]["description"]


def test_single_location_signal_is_a_suggestion_and_markup_silences_it():
    weak = page('<a href="https://maps.apple.com/?q=Acme">Directions</a>')
    finding = by_id(run(analyze_context_signals, weak), "location-markup-missing")[0]
    assert finding["finding_type"] == "proactive_improvement" and finding["severity"] == "low"
    marked = page('<address>12 High Street, Springfield 4000</address>',
                  head=jsonld({"@type": "Organization", "name": "Acme", "address": "12 High Street"}))
    assert not by_id(run(analyze_context_signals, marked), "location-markup-missing")


def test_email_only_address_block_is_not_location_evidence():
    assert not by_id(run(analyze_context_signals, page("<address>hello at acme dot com</address>")),
                     "location-markup-missing")


def test_local_business_without_address_is_a_medium_defect():
    head = jsonld({"@type": "Restaurant", "name": "Acme Diner", "telephone": "1"})
    finding = by_id(run(analyze_context_signals, page(TEXT, head=head)), "local-business-incomplete")[0]
    assert finding["severity"] == "medium" and "address" in finding["evidence"][0]["description"]
    complete = jsonld({"@type": "Restaurant", "name": "Acme Diner", "address": "1 Road", "areaServed": "Springfield"})
    assert not by_id(run(analyze_context_signals, page(TEXT, head=complete)), "local-business-incomplete")


def test_audience_segments_missing_only_on_commercial_sites():
    pages = [page(TEXT, url=SITE + "/"), page(TEXT, url=SITE + "/products/a"), page(TEXT, url=SITE + "/about")]
    assert by_id(run(analyze_context_signals, *pages), "audience-segment-missing")
    with_segment = pages[:2] + [page('<a href="/for-schools">Acme for schools</a>' + TEXT, url=SITE + "/about")]
    assert not by_id(run(analyze_context_signals, *with_segment), "audience-segment-missing")
    blog = [page(TEXT, url=SITE + "/"), page(TEXT, url=SITE + "/blog/a"), page(TEXT, url=SITE + "/blog/b")]
    assert not by_id(run(analyze_context_signals, *blog), "audience-segment-missing")


def test_site_search_missing_on_large_site_only():
    pages = [page(TEXT), page(TEXT, url=SITE + "/b")]
    finding = by_id(run(analyze_context_retention, *pages, sitemap={"status": "ok", "url_entries": 80}),
                    "site-search-missing")[0]
    assert "80 URLs" in finding["title"]
    assert not by_id(run(analyze_context_retention, *pages), "site-search-missing")
    searchable = [page('<form role="search" action="/search"><input name="q"></form>' + TEXT), pages[1]]
    assert not by_id(run(analyze_context_retention, *searchable, sitemap={"status": "ok", "url_entries": 80}),
                     "site-search-missing")


def test_shop_without_saved_state_and_with_wishlist():
    price = "<p>Price: $24.00</p>"
    shop = [page(price + TEXT, url=SITE + "/products/a"), page(price + TEXT, url=SITE + "/products/b")]
    assert by_id(run(analyze_context_retention, *shop), "context-retention-missing")
    # Product and category paths with nothing for sale (a news site filing audio
    # by category) are not a shop.
    unpriced = [page(TEXT, url=SITE + "/category/a"), page(TEXT, url=SITE + "/category/b")]
    assert not by_id(run(analyze_context_retention, *unpriced), "context-retention-missing")
    saved = [page("<button>Add to wishlist</button>" + TEXT, url=SITE + "/products/a"), shop[1]]
    assert not by_id(run(analyze_context_retention, *saved), "context-retention-missing")


def test_redirect_that_drops_content_parameters_is_a_defect_but_tracking_is_ignored():
    dropped = page(TEXT, url=SITE + "/shoes?colour=red&utm_source=x", final_url=SITE + "/shoes")
    tracking = page(TEXT, url=SITE + "/hats?utm_source=x", final_url=SITE + "/hats")
    finding = by_id(run(analyze_context_retention, dropped, tracking), "deep-link-params-dropped")[0]
    assert finding["affected_pages"] == [SITE + "/shoes?colour=red&utm_source=x"]
    assert finding["evidence"][0]["description"].endswith("dropping: colour")


# ------------------------------------------------------------- 9: fix snippets

def _identity(name="Acme", confidence=0.92, same_as=()):
    return {"data": {"canonical_name": name, "confidence": confidence, "same_as_urls": list(same_as)}}


def test_site_facts_use_observed_sources_and_never_guess_the_brand():
    home = page(TEXT, head='<title>Home</title><link rel="apple-touch-icon" href="/touch.png">')
    facts = site_facts(snapshot(home), {"data": {"confidence": 0.0}})
    assert facts["name"] == "REPLACE_WITH_BRAND_NAME" and "name" not in facts["sources"]
    assert facts["logo"] == SITE + "/touch.png"
    named = page(TEXT, head='<title>Fixture | Smart widgets</title>')
    assert site_facts(snapshot(named))["name"] == "Fixture"
    og = page(TEXT, head='<meta property="og:site_name" content="Acme Co">')
    assert site_facts(snapshot(og))["sources"]["name"] == "og:site_name on the home page"


def test_ambiguous_identity_does_not_name_the_brand_after_a_department():
    dept = jsonld({"@type": "Organization", "name": "School of Engineering",
                   "sameAs": ["https://www.linkedin.com/school/engineering"]})
    home = page(TEXT, head="<title>Fixture Example University</title>" + dept)
    conflict = {"data": {"canonical_name": "School of Engineering", "confidence": 0.55,
                         "same_as_urls": ["https://www.linkedin.com/school/engineering"]}}
    facts = site_facts(snapshot(home), conflict)
    assert facts["name"] == "Fixture Example University" and facts["same_as"] == []
    home_org = page(TEXT, head=jsonld({"@type": "Organization", "name": "Fixture Labs"}) + dept)
    assert site_facts(snapshot(home_org), conflict)["sources"]["name"] == "Organization JSON-LD on the home page"


def test_brand_matches_domain_initials():
    snu = AuditArtifacts("https://snu.example/", "https://snu.example",
                         (page(TEXT, head="<title>Shiv Nadar University</title>", url="https://snu.example/"),),
                         freeze_value({"status": "ok"}), freeze_value({}), freeze_value({}),
                         freeze_value({"coverage": {}}), ())
    assert site_facts(snu)["name"] == "Shiv Nadar University"


def test_og_image_never_uses_an_svg():
    home = page('<header><img src="/logo.svg" alt="Acme" width="300" height="300"></header>' + TEXT,
                head='<title>Acme</title><link rel="icon" href="/logo.svg">')
    art = snapshot(home)
    og = build_snippet("social-metadata", [home], art, site_facts(art, _identity()))["code"]
    assert ".svg" not in og and 'content="REPLACE_WITH_SHARE_IMAGE_URL"' in og


def test_no_jsonld_snippet_is_valid_json_with_listed_placeholders():
    home = page(TEXT, head='<title>Acme</title><meta name="description" content="Acme makes widgets.">'
                '<link rel="icon" href="/logo.png">', url=SITE + "/")
    product = page("<h1>Widget Pro</h1>" + TEXT, head='<meta name="description" content="Fits a </script> tag">',
                   url=SITE + "/products/widget")
    art = snapshot(home, product)
    facts = site_facts(art, _identity(same_as=["https://www.linkedin.com/company/acme"]))
    snippet = build_snippet("no-jsonld", [home, product], art, facts)
    blocks = re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', snippet["code"], re.S)
    assert len(blocks) == 2
    site, item = (json.loads(b) for b in blocks)
    org = next(n for n in site["@graph"] if n["@type"] == "Organization")
    assert org["name"] == "Acme" and org["logo"] == SITE + "/logo.png" and org["description"] == "Acme makes widgets."
    assert org["sameAs"] == ["https://www.linkedin.com/company/acme"]
    assert item["@type"] == "Product" and item["name"] == "Widget Pro"
    assert item["description"] == "Fits a </script> tag"
    assert "<\\/script>" in snippet["code"]
    assert "REPLACE_WITH_PRICE" in snippet["placeholders"] and snippet["filled_from"]["name"]


def test_llms_canonical_og_and_twitter_snippets():
    home = page(TEXT, head='<title>Acme</title><meta name="description" content="Acme widgets.">')
    about = page(TEXT, head='<title>About [Acme]</title><meta property="og:title" content="About">',
                 url=SITE + "/about?utm_source=news", final_url=SITE + "/about?utm_source=news")
    art = snapshot(home, about)
    facts = site_facts(art, _identity())
    llms = build_snippet("no-llms-txt", [], art, facts)["code"]
    assert llms.startswith("# Acme\n\n> Acme widgets.\n\n## Key pages") and "- [About Acme](" in llms
    canonical = build_snippet("missing-canonical", [about], art, facts)
    assert '<link rel="canonical" href="https://fixture.example/about">' in canonical["code"]
    assert canonical["filled_from"].keys() == {"href"}
    og = build_snippet("social-metadata", [about], art, facts)["code"]
    assert 'property="og:title"' not in og and 'property="og:description"' in og
    twitter = build_snippet("twitter-card", [about], art, facts)["code"]
    assert 'content="summary"' in twitter
    assert build_snippet("viewport", [about], art, facts) is None


def test_attach_snippets_goes_on_the_finding_not_its_link_and_never_raises():
    home = page(TEXT, head="<title>Acme</title>")
    art = snapshot(home)
    finding = {"id": "F-001", "check_id": "missing-canonical", "affected_pages": [SITE + "/"],
               "suggested_action": {"summary": "s", "steps": [], "priority": "low"}}
    link = {"id": "R-001", "finding_id": "F-001", "check_id": "missing-canonical", "title": "t",
            "category": "ai_discoverability", "finding_type": "proactive_improvement"}
    attach_fix_snippets([finding], [link], art, _identity())
    assert "snippet" in finding["suggested_action"]
    assert "suggested_action" not in link
    attach_fix_snippets([{"id": "F-9", "check_id": "no-jsonld"}], [], art, None)  # malformed item: no raise


# ------------------------------------------------------------- 11: impact x effort

def _item(severity="high", status="confirmed", effort="low", pages=1, kind="defect", fid="F-001"):
    return {"id": fid, "title": fid, "finding_type": kind, "severity": severity, "status": status,
            "affected_pages": [f"{SITE}/{i}" for i in range(pages)],
            "suggested_action": {"summary": "fix " + fid, "steps": [], "priority": severity, "effort": effort}}


def test_impact_follows_severity_evidence_and_breadth():
    assert impact_of(_item("critical")) == "high"
    assert impact_of(_item("high", status="suspected")) == "medium"
    assert impact_of(_item("high", status="insufficient_evidence")) == "low"
    assert impact_of(_item("low", pages=5), pages_analyzed=8) == "medium"
    assert impact_of(_item("low", pages=1), pages_analyzed=8) == "low"
    assert impact_of(_item("low", status="suspected", pages=8), pages_analyzed=8) == "low"


@pytest.mark.parametrize("impact,effort,quadrant", [
    ("high", "low", "quick_win"), ("medium", "low", "quick_win"), ("low", "low", "fill_in"),
    ("high", "high", "major_project"), ("medium", "medium", "major_project"), ("low", "high", "deprioritize"),
])
def test_quadrants(impact, effort, quadrant):
    assert quadrant_of(impact, effort) == quadrant


def test_top_actions_mark_the_first_quick_win_as_start_here():
    items = [_item("high", effort="high", fid="F-001"), _item("high", effort="low", fid="F-002"),
             _item("low", kind="proactive_improvement", fid="F-003")]
    annotate_action_plan(items, pages_analyzed=4)
    rows = top_actions(items)
    assert [r["finding_id"] for r in rows] == ["F-001", "F-002"]
    assert rows[1]["start_here"] and not rows[0]["start_here"]
    assert rows[0]["quadrant"] == "major_project" and rows[1]["quick_win"]
    assert [w["id"] for w in quick_wins(items, [])] == ["F-002"]


def test_unknown_effort_defaults_to_medium():
    item = _item(effort="unknown")
    annotate_action_plan([item])
    assert item["suggested_action"]["effort"] == "medium"


# ------------------------------------------------------------- end to end

def test_full_report_carries_snippets_plan_and_concrete_titles():
    url, stop = start_server()
    try:
        report = run_audit(url + "/", replace(LIMITS, MAX_PAGES_CRAWLED=8), allow_private_targets=True)
    finally:
        stop()
    assert report["top_actions"] and report["quick_wins"]
    assert sum(r["start_here"] for r in report["top_actions"]) == 1
    finding_ids = {f["id"] for f in report["findings"]}
    for item in report["findings"] + report["recommendations"]:
        assert not item["title"].startswith("Review ")
        if "finding_id" in item:
            # A link to a finding: the finding carries the action and its placement.
            assert item["finding_id"] in finding_ids and "suggested_action" not in item
            continue
        action = item["suggested_action"]
        assert action["impact"] in ("low", "medium", "high") and action["quadrant"]
    snippets = [f["suggested_action"]["snippet"] for f in report["findings"] if "snippet" in f["suggested_action"]]
    assert snippets and all(s["code"] and s["note"] for s in snippets)
    for key in ("answer_format", "context_signals", "context_retention"):
        assert report["coverage"][key]
