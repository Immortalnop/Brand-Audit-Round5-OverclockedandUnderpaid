"""test_precision_traps.py -- precision and high-severity guards (Plan phases 0 to 2).

Two halves:
  - End to end: the three trap sites in tests/archetype_sites.py (a news
    publisher, a splash page of a nonprofit, a store with consumer segments) are
    audited offline. Page shapes that commonly trip a heuristic must not be
    reported, and the real defects planted next to them must be.
  - Unit tests, one group per rule that changed: question headings, non-HTML
    files in the site graph, date categories, comparison titles, brand terms in
    the repetition check, Google Maps links, signup forms, commerce and site
    kind, the site's own address, href whitespace, merged duplicate checks, the
    severity gate and the evidence behind a rendering gap.

Every rule is a mechanism (what a page shape means), never a site or brand name.
Nothing here touches the network.
"""
import os
import sys
from types import SimpleNamespace

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from archetype_sites import TRAPS, serve
from constants import Limits
from models import (AuditArtifacts, freeze_value, make_deadline, make_finding, apply_severity_gate,
                    severity_gate_ok)
from transport import Response
from acquire_site import _extract_page, normalize_url
from html_features import Document, is_question_heading, is_signup_form

LIMITS = Limits()
SITE = "https://fixture.example"
TEXT = "<p>" + "Plain words about the offer and what it does for the people who use it every day. " * 15 + "</p>"

_OFFLINE_ENV = {"SEARCH_API_URL": "", "SEARCH_API_KEY": "", "PAGESPEED_API_KEY": "", "FIELD_VITALS_LOOKUP": "0",
                "AGENT_FINDINGS_PATH": "", "OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0",
                "ENABLE_RENDERING": "0", "AUDIT_PROGRESS": "0"}


def page(body="", head="", url=SITE + "/", lang="en", ctype="text/html"):
    lang_attr = f' lang="{lang}"' if lang else ""
    html = f"<html{lang_attr}><head>{head}</head><body>{body}</body></html>"
    response = Response(200, {"Content-Type": ctype}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def snapshot(*pages, sitemap=None):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": False, "status": "absent"}),
                          freeze_value(sitemap or {"status": "ok"}),
                          freeze_value({"coverage": coverage}), ())


def by_id(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


def features(html):
    doc = Document()
    doc.feed(html)
    doc.close()
    return doc.features()


# ---------------------------------------------------------------------------
# End to end: trap sites
# ---------------------------------------------------------------------------

# check ID -> paths it must name (None: any).
EXPECTED = {
    "news": {"citation-schema-opportunity": {"/faq"}, "question-answer-indirect": {"/faq"}, "no-llms-txt": None},
    "splash": {"render-gap-unconfirmed": {"/"}, "no-llms-txt": None},
    "store": {"location-markup-missing": None, "context-retention-missing": None,
              "review-platform-missing": None},
}
# Check IDs each trap site must not raise.
ABSENT = {
    # Linked question headlines, a quoted gallery address, audio filed under
    # /category/, an archive date, a trailing space in an href, a repeated brand
    # name, and a publisher that is not reviewed on consumer review sites.
    "news": {"render-gap", "broken-pages", "context-retention-missing", "location-markup-missing",
             "stale-dates:operational", "stale-dates:editorial", "stale-dates:commercial", "term-repetition",
             "comparison-table-missing", "review-platform-missing"},
    # A splash chooser, a Markdown file for agents, a contact form, "Alternative"
    # as an adjective, section labels phrased with question words, a nonprofit.
    "splash": {"render-gap", "orphan-pages", "dead-ends", "isolated-clusters", "no-internal-navigation",
               "email-summary", "email-summary-readable", "comparison-table-missing", "question-answer-indirect",
               "review-platform-missing", "broken-pages"},
    # Men, Women and Kids navigation; one descriptive alt on four views of one shoe.
    "store": {"audience-segment-missing", "alt-text-quality", "email-summary", "email-summary-readable",
              "broken-pages", "render-gap"},
}


@pytest.fixture(scope="module")
def trap_audits():
    from run_audit import run_audit
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    results = {}
    try:
        for name, site in TRAPS.items():
            base, stop, seen = serve(site)
            try:
                results[name] = (base, run_audit(base + "/", limits=Limits(), allow_private_targets=True), list(seen))
            finally:
                stop()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return results


def _by_check(base, report):
    out = {}
    for item in report["findings"] + report["recommendations"]:
        paths = {p[len(base):] for p in item.get("affected_pages", []) if str(p).startswith(base)}
        for check_id in item.get("check_ids") or [item["check_id"]]:
            out.setdefault(check_id, set()).update(paths)
    return out


def test_trap_corpus_is_complete():
    assert set(TRAPS) == set(EXPECTED) == set(ABSENT)


@pytest.mark.parametrize("name", sorted(TRAPS))
def test_traps_are_not_reported(trap_audits, name):
    base, report, _ = trap_audits[name]
    wrongly = ABSENT[name] & set(_by_check(base, report))
    assert not wrongly, f"{name}: false positives {sorted(wrongly)}"


@pytest.mark.parametrize("name", sorted(TRAPS))
def test_real_defects_next_to_traps_are_reported(trap_audits, name):
    base, report, _ = trap_audits[name]
    found = _by_check(base, report)
    for check_id, pages in EXPECTED[name].items():
        assert check_id in found, f"{name}: expected {check_id}, got {sorted(found)}"
        if pages is not None:
            assert found[check_id] == pages, f"{name}: {check_id} named {sorted(found[check_id])}"


def test_newsletter_signup_is_a_stated_limit_not_a_finding(trap_audits):
    # The emails a signup sends are out of reach of a site audit: the report says
    # so in its warnings and raises no finding about them.
    _, report, _ = trap_audits["store"]
    assert any(w.startswith("An email signup form appears on ") and "was not checked" in w
               for w in report["warnings"])
    _, splash, _ = trap_audits["splash"]
    # A contact form with an email field is not a signup.
    assert not any(w.startswith("An email signup form") for w in splash["warnings"])


@pytest.mark.parametrize("name", sorted(TRAPS))
def test_trap_runs_are_offline_read_only_bounded_and_gated(trap_audits, name):
    from check_catalog import CATALOG
    _, report, seen = trap_audits[name]
    assert report["execution_status"] == "completed"
    assert report["coverage"]["external_fetches"] == 0
    assert {method for method, _ in seen} == {"GET"}
    assert report["coverage"]["runtime_seconds"] < 60
    assert all(item["check_id"] in CATALOG for item in report["findings"] + report["recommendations"])
    assert all(severity_gate_ok(f) for f in report["findings"])


def test_href_whitespace_is_stripped_before_requesting(trap_audits):
    _, _, seen = trap_audits["news"]
    paths = [p for _, p in seen]
    assert "/culture" in paths and not any("%20" in p or p.endswith(" ") for p in paths)


def test_markdown_file_is_fetched_but_never_a_graph_node(trap_audits):
    base, report, seen = trap_audits["splash"]
    assert "/agents.md" in [p for _, p in seen]
    for pages in _by_check(base, report).values():
        assert "/agents.md" not in pages


# ---------------------------------------------------------------------------
# 1. Question headings
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", ["What is Acme?", "How do I reset my password", "Can I pay by card",
                                  "Why?", "How much does it cost", "Is it free?", "Does the plan include support",
                                  "Where is the office?”", "What's included?"])
def test_question_headings(text):
    assert is_question_heading(text)


@pytest.mark.parametrize("text", ["How it works", "How to style", "What we offer", "What we’re building",
                                  "Who we are", "Why choose us", "When to visit", "Where we work", "Plans", ""])
def test_section_labels_are_not_questions(text):
    assert not is_question_heading(text)


def test_linked_headlines_are_not_questions_this_page_answers():
    f = features('<article><a href="/a"><h2>Is coffee good for you?</h2></a><p>Teaser.</p></article>'
                 '<h3><a href="/b">Why are rents rising?</a></h3><p>Teaser.</p>'
                 '<h2>How do I subscribe?</h2><p>Call the desk.</p>')
    assert f["question_headings"] == 1 and f["linked_question_headings"] == 2
    assert [q["question"] for q in f["question_answers"]] == ["How do I subscribe?"]


def test_heading_with_a_small_inline_link_is_still_a_question():
    f = features('<h2>How do I contact <a href="/support">support</a> after hours?</h2><p>Email us.</p>')
    assert f["question_headings"] == 1 and f["linked_question_headings"] == 0


def test_faq_opportunity_needs_answered_questions():
    from analyze_citation_schema import analyze_citation_schema
    unanswered = page("<h2>What is it?</h2><h2>How big is it?</h2><h2>Who makes it?</h2><h2>Specs</h2>",
                      url=SITE + "/q")
    result = analyze_citation_schema(snapshot(unanswered), make_deadline(LIMITS))
    assert not by_id(result, "citation-schema-opportunity")


# ---------------------------------------------------------------------------
# 2. Non-HTML files are not graph nodes
# ---------------------------------------------------------------------------

def test_site_graph_skips_non_html_files():
    from build_site_graph import build_site_graph
    home = page('<a href="/b">B</a>', url=SITE + "/")
    other = page('<a href="/">Home</a>', url=SITE + "/b")
    markdown = page("# Notes", url=SITE + "/agents.md", ctype="text/markdown")
    assert "non_html_content" in markdown.warnings
    graph = build_site_graph(snapshot(home, other, markdown), make_deadline(LIMITS))["data"]
    assert SITE + "/agents.md" not in graph["nodes"]
    assert not graph["orphans"] and not graph["dead_ends"] and not graph["isolated_clusters"]


# ---------------------------------------------------------------------------
# 3. Date categories
# ---------------------------------------------------------------------------

def _claims(*pages):
    from extract_claims import extract_claims
    return {c["value"]: c["category"] for c in extract_claims(snapshot(*pages), make_deadline(LIMITS))["data"]["claims"]
            if c["type"] == "date"}


def test_dates_on_unclassified_pages_need_an_operational_cue():
    essay = page("<p>Written on Feb 6, 1998 by the founder.</p>", url=SITE + "/doc/essays/")
    note = page("<p>Note added on Jan 9, 2003 by the editor.</p>", url=SITE + "/doc/notes")
    hours = page("<p>Opening hours valid until March 1, 2020. Closed on public holidays.</p>", url=SITE + "/visit")
    news = page("<p>The fair took place on August 3, 2022 in the main hall.</p>", url=SITE + "/home/")
    archive = page("<p>Prices as of May 1, 2001.</p>", url=SITE + "/archive/old-prices")
    # An archive-style path makes its dates history, even next to an operational cue.
    assert _claims(essay, note, hours, news, archive) == {
        "Feb 6, 1998": "historical", "Jan 9, 2003": "unclassified", "March 1, 2020": "operational",
        "August 3, 2022": "unclassified", "May 1, 2001": "historical"}


def test_page_types_still_decide_their_dates():
    product = page("<p>Offer from Jan 5, 2015.</p>", url=SITE + "/products/kettle")
    article = page("<p>Published Jan 5, 2015.</p>", url=SITE + "/blog/post")
    assert set(_claims(product).values()) == {"commercial"} and set(_claims(article).values()) == {"editorial"}


def test_unclassified_dates_are_never_reported_as_stale():
    from assess_freshness import assess_freshness
    from extract_claims import extract_claims
    essay = page("<p>Written on Feb 6, 1998.</p>" + TEXT, url=SITE + "/doc/essays/")
    artifacts = snapshot(essay)
    claims = extract_claims(artifacts, make_deadline(LIMITS))
    result = assess_freshness({"data": {"facts": []}}, artifacts, make_deadline(LIMITS), claims=claims)
    assert not [f for f in result["findings"] if f["check_id"].startswith("stale-dates")]


# ---------------------------------------------------------------------------
# 4. Comparison titles
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title,comparison", [
    ("Slack vs Teams", True), ("Acme versus Rival", True), ("Compare plans", True), ("Plan comparison", True),
    ("Best Slack alternatives", True), ("Alternatives to Slack", True), ("Top alternatives in 2026", True),
    ("Alternative Python implementations", False), ("Alternative routes to campus", False),
    ("Our services", False), ("Vsauce channel", False),
])
def test_comparison_titles(title, comparison):
    from analyze_answer_format import _COMPARISON
    assert bool(_COMPARISON.search(title)) is comparison


# ---------------------------------------------------------------------------
# 5. Brand terms are not keyword stuffing
# ---------------------------------------------------------------------------

def test_brand_name_is_not_counted_as_a_repeated_term():
    from analyze_answer_content import analyze_answer_content
    # The brand is 2 of every 19 words (over 6%); every other word stays under 6%.
    body = "<p>" + ("Fixture helps small groups plan their weekly work, share notes, track deadlines and ship "
                    "projects on time, says Fixture. " * 20) + "</p>"
    branded = page(body, url=SITE + "/a")
    identity = {"data": {"canonical_name": "Fixture", "confidence": 0.9}}
    assert not by_id(analyze_answer_content(snapshot(branded), identity, make_deadline(LIMITS)), "term-repetition")
    # Repetition of a word that is not the brand is still reported.
    other = page(("<p>" + "widgets " * 60 + "</p>") + body, url=SITE + "/b")
    assert by_id(analyze_answer_content(snapshot(other), identity, make_deadline(LIMITS)), "term-repetition")


# ---------------------------------------------------------------------------
# 6. Google Maps links
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url,kind", [
    ("https://www.google.com/maps/place/Acme/@51.5,-0.1,17z", "place"),
    ("https://maps.google.com/?cid=1234567890", "place"),
    ("https://g.page/acme-plumbing", "place"),
    ("https://maps.app.goo.gl/AbCdEf", "place"),
    ("https://search.google.com/local/writereview?placeid=XYZ", "place"),
    ("https://www.google.co.in/maps/@28.53,77.57,2a,75y,223h,90t/data=!3m8", "not_place"),
    ("https://www.google.com/maps/dir/A/B", "not_place"),
    ("https://www.google.com/maps?q=coffee", "not_place"),
    ("https://www.trustpilot.com/review/acme.com", None),
])
def test_google_maps_links(url, kind):
    from platforms import google_maps_link, review_platform
    assert google_maps_link(url) == kind
    if kind == "place":
        assert review_platform(url) == ("Google Business Profile", "local")
    if kind == "not_place":
        assert review_platform(url) is None


def test_map_position_in_same_as_is_not_a_profile():
    from check_off_site_profiles import static_problem
    assert "map position" in static_problem("https://www.google.com/maps/@51.5,-0.12,15z", "acme.test")
    assert static_problem("https://www.google.com/maps/place/Acme", "acme.test") is None


# ---------------------------------------------------------------------------
# 7. Signup forms
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("html,signup", [
    ('<form><input type="email" name="email"><button>Subscribe</button></form>', True),
    ('<form action="/newsletter"><input type="email"><button>Go</button></form>', True),
    ('<form><input type="email" placeholder="Join our mailing list"><input type="submit" value="OK"></form>', True),
    ('<form><input type="email"><textarea name="message"></textarea><button>Send</button></form>', False),
    ('<form><input type="email" name="email"><input type="password"><button>Sign up</button></form>', False),
    ('<form role="search"><input type="search" name="q"><button>Search</button></form>', False),
])
def test_signup_forms(html, signup):
    assert (features(html)["signup_forms"] == 1) is signup


def test_signup_form_record_helper():
    assert not is_signup_form({"labels": ["Subscribe"]})
    assert is_signup_form({"email": True, "labels": ["Subscribe"]})


# ---------------------------------------------------------------------------
# 8. Commerce evidence and site kind
# ---------------------------------------------------------------------------

def test_commerce_evidence():
    from check_helpers import commerce_evidence
    assert commerce_evidence(page("<p>Price: $24.00</p>", url=SITE + "/products/a")) == "price"
    assert commerce_evidence(page("<button>Add to cart</button>", url=SITE + "/products/a")) == "buy_control"
    assert commerce_evidence(page('<a href="/cart">Bag</a>', url=SITE + "/products/a")) == "cart_link"
    assert commerce_evidence(page('<a href="https://shop.test/en-gb/basket/">Basket</a>', url=SITE + "/p")) == \
        "cart_link"
    # A product page about a checkout feature is not a cart.
    assert commerce_evidence(page('<a href="/in/payments/checkout">Checkout</a>', url=SITE + "/products")) == ""
    marked = page("", head='<script type="application/ld+json">{"@type":"Product","name":"A"}</script>')
    assert commerce_evidence(marked) == "product_markup"
    assert commerce_evidence(page(TEXT + '<a href="/blog">Check out the blog</a>', url=SITE + "/products/x")) == ""


def test_site_kind_needs_positive_evidence():
    from check_helpers import site_kind
    news = page("", head='<script type="application/ld+json">{"@type":"NewsArticle","headline":"A"}</script>')
    assert site_kind([news]) == "publisher"
    donate_home = page('<a href="/donate">Donate</a>' + TEXT, url=SITE + "/")
    assert site_kind([donate_home]) == "nonprofit"
    nav = '<nav><a href="/give">Support us</a></nav>'
    assert site_kind([page(nav + TEXT, url=SITE + "/a"), page(nav + TEXT, url=SITE + "/b")]) == "nonprofit"
    # One donation link on one inner page is not enough, and a shop is never a nonprofit.
    assert site_kind([page(nav + TEXT, url=SITE + "/a")]) == "unknown"
    shop = page('<a href="/donate">Donate</a><p>Price: $5.00</p>', url=SITE + "/products/a")
    assert site_kind([donate_home, shop]) == "unknown"
    # A salary on a jobs page does not make a nonprofit a shop.
    jobs = page("<p>Salary $90,000 a year.</p>" + TEXT, url=SITE + "/jobs/engineer")
    assert site_kind([donate_home, jobs]) == "nonprofit"
    assert site_kind([page(TEXT)]) == "unknown"


def test_review_platform_check_skips_publishers_and_nonprofits(monkeypatch):
    from check_off_site_profiles import check_off_site_profiles
    monkeypatch.setenv("OFF_SITE_LOOKUP", "0")
    monkeypatch.setenv("SEARCH_API_URL", "")
    identity = {"data": {"canonical_name": "Acme", "confidence": 0.9}}
    org = '<script type="application/ld+json">{"@type":"Organization","name":"Acme"}</script>'
    run = lambda *pages: check_off_site_profiles(snapshot(*pages), identity, make_deadline(LIMITS), LIMITS)
    business = run(page(TEXT, head=org))
    assert by_id(business, "review-platform-missing")
    nonprofit = run(page('<a href="/donate">Donate</a>' + TEXT, head=org))
    assert not by_id(nonprofit, "review-platform-missing")
    assert nonprofit["metrics"]["review_platform_check"] == "not_applicable_nonprofit"


def test_product_path_without_anything_for_sale_needs_no_product_markup():
    from analyze_machine_readability import analyze_machine_readability
    org = '<script type="application/ld+json">{"@type":"Organization","name":"Acme"}</script>'
    index = page("<h1>Products</h1>" + TEXT, url=SITE + "/products", head=org)
    priced = page("<h1>Kettle</h1><p>Price: $39.00</p>" + TEXT, url=SITE + "/products/kettle", head=org)
    gaps = by_id(analyze_machine_readability(snapshot(index, priced), make_deadline(LIMITS)),
                 "page-type-schema-gap:product")
    assert len(gaps) == 1 and gaps[0]["evidence"][0]["urls"] == [SITE + "/products/kettle"]


def test_consumer_segments_count_as_audiences():
    from analyze_context_signals import _audience_signals
    assert _audience_signals(page('<nav><a href="/c/1">Men</a></nav>', url=SITE + "/a"))
    assert _audience_signals(page("<nav><a href=\"/c/2\">Shop Women's</a></nav>", url=SITE + "/a"))
    assert _audience_signals(page('<a href="/collections/kids-shoes">All</a>', url=SITE + "/a"))
    assert not _audience_signals(page('<a href="/menu">Menu</a><a href="/c">Mentions</a>', url=SITE + "/a"))


# ---------------------------------------------------------------------------
# 9. The site's own address
# ---------------------------------------------------------------------------

def test_address_quoted_in_one_article_is_not_the_sites_location():
    from analyze_context_signals import analyze_context_signals
    quote = "<p>The show runs at the Halcyon Gallery, 56 Brewer Street, London W1F 9TE, until June.</p>"
    article = page(TEXT + quote, url=SITE + "/culture/article/review")
    other = page(TEXT, url=SITE + "/news/a")
    result = analyze_context_signals(snapshot(article, other), make_deadline(LIMITS))
    assert not by_id(result, "location-markup-missing")


def test_footer_address_on_several_pages_and_contact_address_count():
    from analyze_context_signals import analyze_context_signals
    footer = "<footer><p>Acme Ltd, 12 Harbour Road, Bristol BS1 5TT</p></footer>"
    repeated = [page(TEXT + footer, url=SITE + "/a"), page(TEXT + footer, url=SITE + "/b")]
    assert by_id(analyze_context_signals(snapshot(*repeated), make_deadline(LIMITS)), "location-markup-missing")
    contact = page(TEXT + "<p>Visit us at 12 Harbour Road, Bristol BS1 5TT</p>", url=SITE + "/contact")
    assert by_id(analyze_context_signals(snapshot(contact), make_deadline(LIMITS)), "location-markup-missing")


# ---------------------------------------------------------------------------
# 10. href whitespace
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("href,expected", [
    ("culture ", SITE + "/culture"), (" /about\n", SITE + "/about"), ("/a\tb", SITE + "/ab"),
    ("/x y", SITE + "/x y"),
])
def test_normalize_url_strips_whitespace_like_a_browser(href, expected):
    assert normalize_url(href, SITE + "/") == expected


# ---------------------------------------------------------------------------
# 11. Duplicate checks merge into one finding
# ---------------------------------------------------------------------------

def _finding(rule, severity="low", pages=("/a",), status="suspected", title="T", evidence_types=("x",)):
    return make_finding(
        category="engagement", finding_type="proactive_improvement", severity=severity, status=status,
        confidence=0.7, title=title, root_cause="Cause of " + rule,
        evidence=[{"type": t, "description": rule + " " + t, "urls": [SITE + p for p in pages]}
                  for t in evidence_types],
        suggested_action={"summary": "Fix " + rule, "steps": ["Fix"], "priority": severity, "effort": "low",
                          "expected_benefit": "b", "verification": "v"},
        provenance={"skill": "s", "script": "x.py", "rule_id": rule},
        affected_pages=[SITE + p for p in pages])


def test_related_checks_merge_into_one_finding():
    from merge_findings import merge_findings
    results = [{"skill": "a", "findings": [_finding("missing-alt", pages=("/a",)),
                                           _finding("h1", pages=("/a",))]},
               {"skill": "b", "findings": [_finding("image-context-missing", severity="medium", pages=("/b",)),
                                           _finding("page-orientation", pages=("/c",))]}]
    merged = {tuple(f["check_ids"]): f for f in merge_findings(results)}
    images = merged[("image-context-missing", "missing-alt")]
    assert images["severity"] == "medium"
    assert images["affected_pages"] == [SITE + "/a", SITE + "/b"]
    assert images["title"].startswith("Images have no text alternative")
    headings = merged[("h1", "page-orientation")]
    assert headings["title"].startswith("Pages lack a descriptive primary heading")
    assert len(merged) == 2


def test_a_single_family_member_keeps_its_own_title():
    from merge_findings import merge_findings
    (only,) = merge_findings([{"skill": "a", "findings": [_finding("h1", title="Pages have no primary H1 heading")]}])
    assert only["title"] == "Pages have no primary H1 heading"


def test_repeated_descriptive_alt_on_a_gallery_is_not_junk():
    from analyze_media_text import analyze_media_text
    gallery = "".join(f'<img src="/img/shoe-{v}.jpg" alt="Ridge Runner walking shoe in grey wool">'
                      for v in ("side", "top", "back", "sole"))
    assert not by_id(analyze_media_text(snapshot(page(gallery)), make_deadline(LIMITS)), "alt-text-quality")


# ---------------------------------------------------------------------------
# 12. Severity gate
# ---------------------------------------------------------------------------

def test_unconfirmed_single_evidence_high_is_lowered():
    f = apply_severity_gate(_finding("render-gap", severity="high"))
    assert f["severity"] == "medium" and f["suggested_action"]["priority"] == "medium"
    assert f["severity_gate"]["from"] == "high" and f["severity_gate"]["to"] == "medium"
    critical = apply_severity_gate(_finding("x", severity="critical"))
    assert critical["severity"] == "medium" and critical["severity_gate"]["from"] == "critical"


def test_confirmed_or_corroborated_high_is_kept():
    confirmed = apply_severity_gate(_finding("x", severity="high", status="confirmed"))
    assert confirmed["severity"] == "high" and "severity_gate" not in confirmed
    corroborated = apply_severity_gate(_finding("x", severity="high", evidence_types=("render_gap", "noscript")))
    assert corroborated["severity"] == "high" and "severity_gate" not in corroborated


def test_gate_is_idempotent_and_runs_in_prioritize_and_validate():
    from prioritize_findings import prioritize_findings
    from validate_report import _validate_finding_like
    f = _finding("x", severity="high")
    f["id"] = "F-001"
    prioritize_findings([f])
    assert f["severity"] == "medium"
    record = dict(f["severity_gate"])
    apply_severity_gate(f)
    assert f["severity_gate"] == record
    g = _finding("y", severity="high")
    g["id"] = "F-002"
    (kept,) = _validate_finding_like([g], [], "finding")
    assert kept["severity"] == "medium"


# ---------------------------------------------------------------------------
# 13. Evidence behind a rendering gap (no headless browser)
# ---------------------------------------------------------------------------

def _render(*pages):
    from analyze_rendering import analyze_rendering
    return analyze_rendering(snapshot(*pages), make_deadline(LIMITS), LIMITS, capabilities={})


def test_thin_page_with_no_sign_of_client_rendering_is_only_unconfirmed():
    thin = page('<h1>Welcome</h1><script src="/js/analytics.js"></script>')
    result = _render(thin)
    assert not by_id(result, "render-gap")
    (unconfirmed,) = by_id(result, "render-gap-unconfirmed")
    assert unconfirmed["status"] == "insufficient_evidence" and unconfirmed["severity"] == "low"


def test_splash_page_of_links_is_not_a_rendering_gap():
    splash = page('<h1>Welcome</h1><a href="/north/">North campus</a> <a href="/south/">South campus</a>'
                  '<script src="/static/js/main.4f2a9c1d.js"></script>')
    assert not by_id(_render(splash), "render-gap")


def test_one_sign_is_a_medium_suspected_gap():
    shell = page('<div id="root"></div><script src="/js/site.js"></script>')
    (gap,) = by_id(_render(shell), "render-gap")
    assert gap["severity"] == "medium" and gap["status"] == "suspected"
    assert {e["type"] for e in gap["evidence"]} == {"render_gap", "app_shell"}


def test_two_independent_signs_are_a_high_suspected_gap():
    shell = page('<noscript>You need to enable JavaScript to run this app.</noscript><div id="root"></div>'
                 '<script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>'
                 '<script src="/_next/static/chunks/main.js"></script>')
    (gap,) = by_id(_render(shell), "render-gap")
    assert gap["severity"] == "high" and severity_gate_ok(gap)
    assert {"render_gap", "app_shell", "framework_bundle", "serialized_state", "noscript"} == \
        {e["type"] for e in gap["evidence"]}


def test_page_text_held_only_in_state_is_one_strong_sign():
    prose = ", ".join(f'"p{i}": "Our team plans trips for groups of every size and budget"' for i in range(8))
    js = '<script src="/js/site.js"></script>'
    shell = page('<div id="root"></div><script id="__NEXT_DATA__" type="application/json">{' + prose + '}</script>' + js)
    assert shell.features["state_text_chars"] >= 300
    (gap,) = by_id(_render(shell), "render-gap")
    kinds = {e["type"] for e in gap["evidence"]}
    assert "state_content" in kinds and "serialized_state" not in kinds
    assert gap["severity"] == "high"  # an empty mount point plus page text held in script data
    blob_only = page('<script id="__NEXT_DATA__" type="application/json">{' + prose + '}</script>' + js)
    (gap,) = by_id(_render(blob_only), "render-gap")
    assert gap["severity"] == "medium"


def test_framework_and_state_observations():
    assert features('<script src="/_nuxt/app.js"></script>')["framework_hint"]
    assert features('<div ng-version="17.0.0"></div>')["framework_hint"]
    assert features("<script>window.__INITIAL_STATE__ = {};</script>")["state_blob"]
    assert not features('<script src="/js/analytics.js"></script><script>var a=1;</script>')["framework_hint"]
    assert features('<script src="/assets/react-dom.production.min.js"></script>')["framework_hint"]
    assert not features('<script src="/js/next-slide.js"></script>')["framework_hint"]
    # A cache-busting hash in a file name is not a framework.
    assert not features('<script src="https://cdn.test/scripts/site-bundle.17bbc1daaa96c6be.js"></script>')[
        "framework_hint"]
    assert not features('<script type="application/ld+json">{"@type":"Thing"}</script>')["state_blob"]
