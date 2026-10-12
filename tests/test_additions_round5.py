"""test_additions_round5.py -- the checks, report sections and precision fixes added
on top of the Round 5 engine (features merged from the add_md branch, and the
fixes found by comparing the two engines on live sites).

Every test runs offline: unit tests on synthetic pages, plus a few end-to-end
audits of the local fixture sites in tests/archetype_sites.py.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

from constants import Limits  # noqa: E402
from models import AuditArtifacts, freeze_value, make_deadline  # noqa: E402
from transport import Response  # noqa: E402
from acquire_site import _extract_page, normalize_url, _classify_page_type  # noqa: E402

LIMITS = Limits()
SITE = "https://shop.example"


def page(html, url=SITE + "/", headers=None):
    response = Response(200, {"Content-Type": "text/html", **(headers or {})}, html.encode(), url, False)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def snapshot(pages, robots=None, sitemap=None, llms=None, site=SITE + "/"):
    return AuditArtifacts(site, SITE, tuple(pages), freeze_value(robots or {"status": "ok"}),
                          freeze_value(llms or {"present": True, "status": "ok"}),
                          freeze_value(sitemap or {"status": "ok", "urls": []}), freeze_value({}), ())


def ids(result):
    out = set()
    for f in result["findings"]:
        out.update(f.get("check_ids") or [f["check_id"]])
    return out


def html(body, head="", title="T", lang="en"):
    return f'<html lang="{lang}"><head><title>{title}</title>{head}</head><body>{body}</body></html>'


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj) + "</script>"


# ------------------------------------------------------------- parser features
def test_forms_are_classified_by_purpose():
    f = page(html("<form id='nl'><input type=email><button>Subscribe to our newsletter</button></form>"
                  "<form action='/trial'><input type=email><button>Start free trial</button></form>"
                  "<form action='/login'><input type=email><input type=password><button>Subscribe</button></form>")).features
    assert [r["newsletter"] for r in f["form_records"]] == [True, False, False]
    assert f["newsletter_signup"] is True and f["password_inputs"] == 1


def test_question_answers_skip_linked_teasers():
    f = page(html("<h2>What is Acme?</h2><p>Acme makes widgets.</p>"
                  "<h2><a href='/x'>How do kettles work?</a></h2><p>Teaser.</p>"
                  "<h3>Why us?</h3><h4>Fast</h4>")).features
    qs = {q["question"]: q for q in f["question_answers"]}
    assert set(qs) == {"What is Acme?", "Why us?"}
    assert qs["What is Acme?"]["answer"] == "Acme makes widgets."
    assert qs["Why us?"]["answered_by_subheadings"]


def test_contact_details_and_executable_scripts():
    f = page(html("<footer>Mail hello@shop.example Phone: +1 (555) 010-2030 "
                  "<a href='mailto:Sales@Shop.example?subject=x'>m</a><a href='tel:+15550102030'>t</a></footer>"
                  + jsonld({"@type": "Organization"}) + "<script type='application/json'>{}</script>")).features
    assert list(f["contact_emails"]) == ["sales@shop.example", "hello@shop.example"]
    assert list(f["contact_phones"]) == ["+15550102030"]
    assert f["executable_scripts"] == 0


def test_href_whitespace_is_stripped_like_a_browser():
    assert normalize_url(" /culture ", SITE + "/") == SITE + "/culture"


def test_section_indexes_are_listings_and_markup_still_wins():
    assert _classify_page_type(SITE + "/blog/", SITE, [], "/blog/") == "listing"
    assert _classify_page_type(SITE + "/news", SITE, [], "/news") == "listing"
    assert _classify_page_type(SITE + "/blog/post", SITE, [], "/blog/post") == "article"
    assert _classify_page_type(SITE + "/blog/", SITE, [{"@type": "BlogPosting"}], "/blog/") == "article"


# ------------------------------------------------------------- login pages
def test_login_page_is_out_of_scope_but_a_home_with_a_login_box_is_not():
    login = page(html("<h1>Sign in</h1><form action='/login'><input type=email><input type=password></form>",
                      title="Sign in"), url=SITE + "/login")
    assert "login_page" in login.warnings
    home = page(html("<header><form><input type=password></form></header><h1>Shop</h1><p>" + "Real copy. " * 200 + "</p>",
                     title="Shop"))
    assert "login_page" not in home.warnings
    from check_helpers import content_pages
    assert content_pages(snapshot([login, home])) == [home]


# ------------------------------------------------------------- scoring
def test_absence_claims_from_a_tiny_sample_are_capped_at_medium():
    from scoring import ScoringContext, apply_scoring
    from models import make_finding
    f = make_finding(category="ai_discoverability", finding_type="defect", severity="high", status="confirmed",
                     confidence=0.85, title="No JSON-LD", root_cause="r",
                     evidence=[{"type": "x", "description": "0/1", "urls": [SITE + "/"]}],
                     suggested_action={"summary": "s", "steps": ["s"], "priority": "high", "effort": "medium"},
                     provenance={"rule_id": "no-jsonld"})
    small = apply_scoring(dict(f), ScoringContext(1, 1, {}, SITE + "/"))
    assert small["severity"] == "medium" and "capped at medium" in small["severity_rationale"]["adjustment"]
    large = apply_scoring(dict(f, severity_rationale=None), ScoringContext(20, 5, {}, SITE + "/"))
    assert large["severity"] == "high"


# ------------------------------------------------------------- engagement precision
def test_page_orientation_only_for_missing_or_generic_h1():
    from analyze_experience import analyze_experience
    long = "<p>" + "word " * 350 + "</p>"
    clear = page(html("<h1>API reference</h1>" + long), url=SITE + "/docs/api")
    generic = page(html("<h1>Welcome</h1>" + long), url=SITE + "/guide")
    found = analyze_experience(snapshot([clear, generic]), make_deadline(LIMITS))
    orient = [f for f in found["findings"] if f["check_id"] == "page-orientation"]
    assert orient and orient[0]["affected_pages"] == [SITE + "/guide"]


def test_email_summary_readable_needs_image_carried_substance():
    from analyze_experience import analyze_experience
    signup = "<form><input type=email><button>Subscribe</button></form>"
    gallery = "".join(f"<img src='/s{i}.jpg' alt='Shoe view {i}'>" for i in range(4))
    banners = "".join(f"<img src='/b{i}.jpg'>" for i in range(4))
    fired = lambda body: ids(analyze_experience(snapshot([page(html(signup + body))]), make_deadline(LIMITS)))
    assert "email-summary-readable" not in fired(gallery + "<p>Price $120.</p>")
    assert "email-summary-readable" in fired(banners + "<p>Join us.</p>")


# ------------------------------------------------------------- access
def test_robots_429_is_reported_and_only_the_homepage_is_fetched():
    from archetype_sites import serve
    from run_audit import run_audit
    site = {"pages": {"/": html("<h1>Shop</h1><p>" + "Copy. " * 100 + "</p>"), "/about": html("<h1>About</h1>")},
            "responses": {"/robots.txt": (429, "slow down", "text/plain", [("Retry-After", "60")])}}
    base, stop, seen = serve(site)
    try:
        report = run_audit(base + "/", limits=Limits(), allow_private_targets=True)
    finally:
        stop()
    rate = [f for f in report["findings"] if "robots-rate-limited" in (f.get("check_ids") or [f["check_id"]])]
    assert rate and rate[0]["severity"] == "medium" and rate[0]["status"] == "suspected"
    assert [p for _, p in seen if p not in ("/robots.txt",)] == ["/"]
    assert not any(f["check_id"] == "robots-unreachable" for f in report["findings"])
    assert any("HTTP 429" in x for x in report["limitations"])


# ------------------------------------------------------------- citation markup
def test_citation_schema_invalid_and_opportunity():
    from analyze_citation_schema import analyze_citation_schema
    bad = page(html("<h1>FAQ</h1><p>Questions.</p>", head=jsonld(
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Q?"}]})), url=SITE + "/faq")
    qa = "".join(f"<h2>How do I do thing {i}?</h2><p>You do it like this, step by step.</p>" for i in range(3))
    unmarked = page(html("<h1>Help</h1>" + qa), url=SITE + "/help")
    result = analyze_citation_schema(snapshot([bad, unmarked]), make_deadline(LIMITS))
    by_id = {f["check_id"]: f for f in result["findings"]}
    assert by_id["citation-schema-invalid"]["affected_pages"] == [SITE + "/faq"]
    assert by_id["citation-schema-opportunity"]["affected_pages"] == [SITE + "/help"]


# ------------------------------------------------------------- sitemap lastmod
def test_sitemap_lastmod_missing_and_build_stamped():
    from update_signals import check_sitemap_lastmod
    urls = [f"{SITE}/p{i}" for i in range(6)]
    missing = {"status": "ok", "urls": urls, "url_entries": 6, "lastmod_entries": 0, "lastmod": {}}
    uniform = {"status": "ok", "urls": urls, "url_entries": 6, "lastmod_entries": 6,
               "lastmod": {u: "2026-01-02T10:00:00Z" for u in urls}}
    varied = dict(uniform, lastmod={u: f"2026-01-0{i + 1}" for i, u in enumerate(urls)})
    run = lambda s: check_sitemap_lastmod(snapshot([], sitemap=s), make_deadline(LIMITS))["findings"]
    assert "no <lastmod>" in run(missing)[0]["title"]
    assert "build time" in run(uniform)[0]["title"]
    assert run(varied) == [] and run(dict(missing, url_entries=3, urls=urls[:3])) == []


# ------------------------------------------------------------- entity links
def test_kg_link_missing_only_for_brands_that_maintain_same_as():
    from check_entity_links import check_entity_links
    org = {"@type": "Organization", "name": "Acme", "url": SITE}
    run = lambda node: ids(check_entity_links(snapshot([page(html("<h1>A</h1>", head=jsonld(node)))]),
                                              make_deadline(LIMITS)))
    assert run(org) == set()
    assert run(dict(org, sameAs=["https://www.linkedin.com/company/acme"])) == {"kg-link-missing"}
    assert run(dict(org, sameAs=["https://www.wikidata.org/wiki/Q42", "https://x.com/acme"])) == set()
    assert "same-as-invalid" in run(dict(org, sameAs=["https://www.facebook.com/sharer/sharer.php?u=x",
                                                      "https://twitter.com/", SITE + "/about"]))


def test_organization_subtype_on_the_home_page_is_the_brand():
    from resolve_entity_identity import resolve_entity_identity
    home = page(html("<h1>Harbour</h1>", head=jsonld({"@type": "Plumber", "name": "Harbour Plumbing"})))
    listing = page(html("<h1>Places</h1>", head=jsonld({"@type": "Restaurant", "name": "Cafe A"})), url=SITE + "/places")
    deadline = make_deadline(LIMITS)
    assert resolve_entity_identity(snapshot([home]), deadline)["data"]["canonical_name"] == "Harbour Plumbing"
    assert resolve_entity_identity(snapshot([page(html("<h1>Home</h1>")), listing]), deadline)["data"].get(
        "canonical_name") != "Cafe A"


# ------------------------------------------------------------- contact markup
def test_contact_markup_counts_only_the_sites_own_details():
    from analyze_contact_markup import analyze_contact_markup
    org = jsonld({"@type": "Organization", "name": "Shop"})
    readme = page(html("<p>Write to me@example.com</p>", head=org), url=SITE + "/project/x")
    run = lambda *ps: ids(analyze_contact_markup(snapshot(list(ps)), make_deadline(LIMITS)))
    assert run(readme) == set()
    own = page(html("<footer>help@shop.example</footer>", head=org))
    assert run(own) == {"contact-markup-missing"}
    declared = page(html("<footer>help@shop.example</footer>",
                         head=jsonld({"@type": "Organization", "name": "Shop", "email": "help@shop.example"})))
    assert run(declared) == set()
    assert run(page(html("<footer>help@shop.example</footer>"))) == set()  # no JSON-LD at all: no-jsonld covers it


def test_contact_snippet_uses_a_role_mailbox_never_a_personal_address():
    from fix_snippets import build_snippet, site_facts
    org = jsonld({"@type": "Organization", "name": "Shop"})
    personal = snapshot([page(html("<footer>jason@shop.example jason@shop.example</footer>", head=org))])
    snippet = build_snippet("contact-markup-missing", [], personal, site_facts(personal))
    assert "jason@shop.example" not in snippet["code"] and "REPLACE_WITH_EMAIL" in snippet["placeholders"]
    both = snapshot([page(html("<footer>jason@shop.example hello@shop.example</footer>", head=org))])
    assert '"email": "hello@shop.example"' in build_snippet("contact-markup-missing", [], both, site_facts(both))["code"]


# ------------------------------------------------------------- fix snippets
def test_fix_snippets_fill_from_observed_facts_and_list_placeholders():
    from fix_snippets import attach_fix_snippets
    home = page(html("<h1>Shop</h1>", title="Shop", head='<meta name="description" content="Cookware.">'))
    about = page(html("<h1>About</h1>", title="About us"), url=SITE + "/about")
    arts = snapshot([home, about])
    identity = {"data": {"canonical_name": "Shop", "confidence": 0.9}}
    items = [{"check_id": "no-llms-txt", "affected_pages": [], "suggested_action": {}},
             {"check_id": "missing-canonical", "affected_pages": [SITE + "/about"], "suggested_action": {}},
             {"check_id": "no-jsonld", "affected_pages": [], "suggested_action": {"proposed_snippets": {"x": "{}"}}}]
    attach_fix_snippets(items, arts, identity)
    llms = items[0]["suggested_action"]["snippet"]
    assert llms["code"].startswith("# Shop\n\n> Cookware.") and f"[About us]({SITE}/about)" in llms["code"]
    assert '<link rel="canonical" href="https://shop.example/about">' in items[1]["suggested_action"]["snippet"]["code"]
    assert "snippet" not in items[2]["suggested_action"]  # the detector's own draft is kept, not duplicated


# ------------------------------------------------------------- report rendering
def test_markdown_escapes_site_text():
    from render_report import render_markdown
    finding = {"id": "F-001", "title": "T", "severity": "low", "status": "confirmed", "confidence": 0.9,
               "root_cause": "Title is '# Owned | <script>'", "mechanism": "m", "evidence": [
                   {"description": "[click](javascript:x)", "urls": ["https://a.example/x", "javascript:alert(1)"]}],
               "suggested_action": {"summary": "s", "steps": [], "snippet": {"format": "html", "code": "```x```",
                                                                            "placeholders": [], "filled_from": {}}}}
    md = render_markdown({"site": "s", "findings": [finding], "confidence": {}, "coverage": {}})
    assert "\\# Owned \\| \\<script\\>" in md and "\\[click\\](javascript:x)" in md
    assert "<https://a.example/x>" in md and "<javascript:alert(1)>" not in md
    assert "````html\n```x```\n````" in md


def test_confidence_explains_itself_and_ignores_login_pages():
    from execution_summary import overall_confidence
    c = overall_confidence({"pages_analyzed": 4, "pages_fetched_attempted": 5, "pages_out_of_scope": 1,
                            "templates_sampled": 2}, "completed")
    assert c["components"]["access_quality"] == 1.0 and c["level"] == "low"
    assert c["limiting_factor"] == "sample_quality" and c["explanation"].startswith("Confidence is low")
    assert set(c["reasons"]) == {"sample_quality", "access_quality", "execution_penalty"}


def test_quick_wins_and_start_here():
    from generate_recommendations import build_action_plan, quick_wins
    mk = lambda i, sev, effort, conf: {"id": f"F-00{i}", "title": "t", "severity": sev, "status": "confirmed",
                                       "confidence": conf, "priority_score": 1,
                                       "suggested_action": {"summary": "s", "effort": effort, "priority": sev}}
    plan = build_action_plan([mk(1, "high", "medium", .9), mk(2, "medium", "low", .9), mk(3, "medium", "low", .4),
                              mk(4, "low", "low", .9)])
    assert plan[0]["start_here"] and not any(a["start_here"] for a in plan[1:])
    assert quick_wins(plan) == ["F-002"]


# ------------------------------------------------------------- agent stage
def test_agent_checks_ag04_to_ag06_and_whats_working_after_finalize(tmp_path):
    from finalize_report import finalize
    report = json.loads((ROOT / "examples" / "sample-report.json").read_text())
    report["whats_working"] = [{"id": "W-001", "check": "x", "title": "x", "check_ids": ["facts-in-images"],
                                "evidence": "e", "pages_checked": 1}]
    agent = tmp_path / "agent.json"
    agent.write_text(json.dumps([
        {"check": "AG-04", "evidence": "Price list image shows 3 prices not in the page text",
         "affected_pages": ["http://shop.example/product"]},
        {"check": "AG-05", "evidence": "Two other companies named Example Brand appear in the first results"},
        {"check": "AG-06", "evidence": "No profile on Trustpilot or Crunchbase"}]))
    final = finalize(report, str(agent))
    got = {c for f in final["findings"] for c in f.get("check_ids") or [f["check_id"]]}
    assert {"facts-in-images", "kg-namesake-ambiguity", "review-platform-missing"} <= got
    assert final["whats_working"] == []
    assert final["agent_stage"]["status"] == "ingested" and final["quick_wins"] is not None


def test_agent_brief_lists_fact_images_and_platform_kind():
    from run_audit import build_agent_brief
    p = page(html("<h1>Menu</h1><img src='/img/menu.jpg' alt='Our menu'>"), url=SITE + "/menu")
    brief = build_agent_brief(snapshot([page(html("<h1>Cafe</h1>")), p]), {"data": {"canonical_name": "Cafe"}}, {})
    assert brief["ag04"]["images"] == [{"page": SITE + "/menu", "image": SITE + "/img/menu.jpg", "alt": "Our menu",
                                        "why": "image named/alt-texted as a fact carrier"}]
    assert brief["ag06"]["business_kind"] == "general" and brief["ag05"]["queries"][0].startswith('"Cafe"')


# ------------------------------------------------------------- determinism and --explain
def test_two_audits_of_one_site_produce_the_same_report():
    """Determinism is a claim the README and SKILL.md make, so it is pinned here:
    the same site audited twice gives the same findings, scores, order, hygiene
    split, action plan and passed checks. Only the clock and the measured timings
    differ."""
    from fixtures_server import start_server
    from run_audit import run_audit
    url, stop = start_server(sitemap_mode="broken_nav")
    try:
        first, second = (run_audit(url + "/", allow_private_targets=True) for _ in range(2))
    finally:
        stop()
    shape = lambda r: json.dumps({
        "findings": [[f["id"], f["check_id"], sorted(f.get("check_ids") or []), f["severity"], f["confidence"],
                      f["priority_score"], sorted(f["affected_pages"])] for f in r["findings"]],
        "hygiene": [[f["id"], f["check_id"]] for f in r["hygiene_findings"]],
        "plan": r["action_plan"], "quick_wins": r["quick_wins"],
        "working": [[w["check"], w["evidence"]] for w in r["whats_working"]],
        "confidence": r["confidence"]["score"],
    }, sort_keys=True, default=str)
    assert shape(first) == shape(second)


def test_explain_reports_measured_behaviour():
    from run_audit import explain_run
    report = json.loads((ROOT / "examples" / "sample-report.json").read_text())
    text = explain_run(report)
    cov = report["coverage"]
    assert f"{cov['runtime_seconds']} s (budget 270 s)" in text
    assert f"{cov['instrumentation']['requests_attempted']} attempted" in text
    assert f"{cov['pages_analyzed']} analysed of {cov['pages_fetched_attempted']} fetched" in text
    assert "acquisition" in text and "% of measured stage time" in text
    # Every line is prefixed, so it can never be mistaken for the JSON on stdout.
    assert all(line.startswith("[explain]") for line in text.splitlines())


def test_explain_survives_a_report_with_no_telemetry():
    """A timed-out run has no instrumentation; --explain must still print."""
    from run_audit import explain_run
    text = explain_run({"coverage": {}, "confidence": {}})
    assert text.startswith("[explain]") and "budget 270 s" in text


# ------------------------------------------------------------- hygiene
def test_catalog_source_has_no_placeholder_text():
    source = (ROOT / "common" / "check_catalog.py").read_text()
    assert "The observed condition can limit" not in source
    from check_catalog import CATALOG
    for check_id, entry in CATALOG.items():
        assert entry["mechanism"].strip() != entry["implementation_detail"].strip(), check_id


@pytest.mark.parametrize("name", ["guarded", "mixed_guard", "legacy_encoding"])
def test_robustness_sites(name):
    """A site behind a bot wall, one section behind a challenge, and a legacy
    encoding: each still yields a valid, honest report."""
    from archetype_sites import ROBUSTNESS, serve
    from run_audit import run_audit
    base, stop, _ = serve(ROBUSTNESS[name])
    try:
        report = run_audit(base + "/", limits=Limits(), allow_private_targets=True)
    finally:
        stop()
    got = {c for f in report["findings"] for c in f.get("check_ids") or [f["check_id"]]}
    assert "broken-pages" not in got
    if name == "guarded":
        assert "bot-challenge-sitewide" in got and report["coverage"]["pages_analyzed"] == 0
    elif name == "mixed_guard":
        assert report["coverage"]["pages_challenged"] == 1 and report["coverage"]["pages_analyzed"] == 2
    else:
        assert "Café crème" in json.dumps(report["agent_stage"]["brief"], ensure_ascii=False)
