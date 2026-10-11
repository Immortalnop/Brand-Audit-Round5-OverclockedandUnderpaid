"""Known limitations 1 and 2 of the context and answer-format checks.

1. Pages built by JavaScript. Their raw HTML is near-empty, so a check that
   concludes something is missing (no search, no saved items, no audience page,
   no comparison table) must not judge them, and the report must say they were
   skipped. Widgets that JavaScript fills in later still leave a trace in the raw
   HTML (a mount point, a data attribute, a script URL, inline configuration),
   and that trace counts as the feature being present.
2. Addresses written as plain text. A postal address in a <div> or <p> is
   location evidence, as an <address> element is.

Unit tests build pages from HTML strings and never touch the network.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/engagement-audit/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline
from transport import Response
from acquire_site import _extract_page
from html_features import find_postal_addresses, find_contact_details
from check_helpers import script_dependent, split_script_dependent
from analyze_answer_format import analyze_answer_format
from analyze_context_signals import analyze_context_signals
from analyze_context_retention import analyze_context_retention
from analyze_rendering import _heuristic_gap_pages
from fix_snippets import site_facts, build_snippet

LIMITS = Limits()
SITE = "https://fixture.example"
TEXT = "<p>" + "Plain words about the offer and what it does for the people who use it every day. " * 15 + "</p>"
SHELL = '<div id="root"></div><script src="/static/app.js"></script>'
LARGE = {"status": "ok", "url_entries": 80}


def page(body="", head="", url=SITE + "/", lang="en"):
    html = f'<html lang="{lang}"><head>{head}</head><body>{body}</body></html>'
    response = Response(200, {"Content-Type": "text/html"}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def run(check, *pages, sitemap=None):
    art = AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                         freeze_value({"present": False, "status": "absent"}),
                         freeze_value(sitemap or {"status": "ok"}),
                         freeze_value({"coverage": {"urls_analyzed": len(pages), "urls_discovered": len(pages)}}), ())
    return check(art, make_deadline(LIMITS))


def by_id(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


# ------------------------------------------------------------- 1: pages built by JavaScript

def test_script_dependent_matches_the_rendering_heuristic():
    shell, full = page(SHELL), page(TEXT, url=SITE + "/b")
    assert script_dependent(shell) and not script_dependent(full)
    assert split_script_dependent([shell, full]) == ([full], [shell])
    assert _heuristic_gap_pages([shell, full]) == [shell.url]


def test_substantial_noscript_fallback_is_not_script_dependent():
    assert not script_dependent(page(SHELL + "<noscript>" + TEXT + "</noscript>"))
    assert script_dependent(page(SHELL + "<noscript>Please enable JavaScript to use this site.</noscript>"))


def test_site_search_is_not_judged_on_pages_built_by_javascript():
    shells = [page(SHELL), page(SHELL, url=SITE + "/b")]
    result = run(analyze_context_retention, *shells, sitemap=LARGE)
    assert not by_id(result, "site-search-missing")
    assert result["metrics"]["context_retention_script_dependent_pages"] == 2
    assert any("2/2 sampled pages carry too little text" in w and "site search" in w for w in result["warnings"])


def test_site_search_counts_only_the_pages_it_judged():
    pages = [page(TEXT), page(SHELL, url=SITE + "/app")]
    finding = by_id(run(analyze_context_retention, *pages, sitemap=LARGE), "site-search-missing")[0]
    assert finding["title"].startswith("No site search on 1/1 sampled page ")


@pytest.mark.parametrize("hint", [
    '<button class="header__search-toggle" aria-label="Open search"></button>',
    '<div id="search-root" hidden></div>',
    '<a href="/search"><svg></svg></a>',
    '<link rel="search" type="application/opensearchdescription+xml" href="/opensearch.xml">',
])
def test_search_hints_left_for_javascript_count_as_search(hint):
    pages = [page(hint + TEXT), page(TEXT, url=SITE + "/b")]
    assert not by_id(run(analyze_context_retention, *pages, sitemap=LARGE), "site-search-missing")


@pytest.mark.parametrize("not_search", [
    '<div class="research-papers"></div>',
    '<a href="https://www.google.com/search?q=acme">Google</a>',
    '<a href="/research">Research</a>',
])
def test_lookalikes_are_not_search_hints(not_search):
    pages = [page(not_search + TEXT), page(TEXT, url=SITE + "/b")]
    assert by_id(run(analyze_context_retention, *pages, sitemap=LARGE), "site-search-missing")


@pytest.mark.parametrize("trace", [
    '<div id="recently-viewed-products"></div>',
    '<div data-wishlist-count="0"></div>',
    '<script src="/assets/wishlist.js" defer></script>',
    '<script>window.theme = {recentlyViewed: true};</script>',
    '<script type="application/json">{"save_for_later": "/api/saved"}</script>',
    '<a href="/account/wishlist" aria-label="Saved"><svg></svg></a>',
])
def test_saved_state_widgets_left_for_javascript_count_as_saved_state(trace):
    shop = [page(trace + TEXT, url=SITE + "/products/a"), page(TEXT, url=SITE + "/products/b")]
    result = run(analyze_context_retention, *shop)
    assert not by_id(result, "context-retention-missing")
    assert result["metrics"]["context_retention_saved_state_hints"]


def test_unrelated_script_configuration_is_not_saved_state():
    # Shopify themes name compare_at_price in every product script; that is a price, not a compare list.
    script = '<script>var product = {"compare_at_price": 1200, "price": 1000};</script>'
    # A shop is recognized from something for sale on its product pages (a price here).
    price = "<p>Price: $10.00</p>"
    shop = [page(script + price + TEXT, url=SITE + "/products/a"), page(price + TEXT, url=SITE + "/products/b")]
    finding = by_id(run(analyze_context_retention, *shop), "context-retention-missing")[0]
    assert "no mount point, data attribute or script" in finding["evidence"][0]["description"]


def test_saved_state_is_not_judged_on_shop_pages_built_by_javascript():
    shop = [page(SHELL, url=SITE + "/products/a"), page(SHELL, url=SITE + "/products/b")]
    assert not by_id(run(analyze_context_retention, *shop), "context-retention-missing")


def test_audience_segments_are_not_judged_on_pages_built_by_javascript():
    shells = [page(SHELL, url=SITE + "/"), page(SHELL, url=SITE + "/products/a"), page(SHELL, url=SITE + "/about")]
    result = run(analyze_context_signals, *shells)
    assert not by_id(result, "audience-segment-missing")
    assert result["metrics"]["context_script_dependent_pages"] == 3
    assert any("location and audience signals" in w for w in result["warnings"])
    full = [page(TEXT, url=SITE + "/"), page(TEXT, url=SITE + "/products/a"), page(TEXT, url=SITE + "/about")]
    assert by_id(run(analyze_context_signals, *full), "audience-segment-missing")


def test_comparison_table_is_not_judged_on_pages_built_by_javascript():
    shell = page(SHELL, head="<title>Acme vs Rival</title>", url=SITE + "/acme-vs-rival")
    result = run(analyze_answer_format, shell)
    assert not by_id(result, "comparison-table-missing")
    assert result["metrics"]["answer_format_script_dependent_pages"] == 1
    assert any("1/1 sampled page carries" in w and "comparison tables" in w for w in result["warnings"])


def test_question_headings_and_tables_in_raw_html_are_still_judged_on_thin_pages():
    thin = page("<h2>How much does it cost?</h2><p>Great question.</p><h2>Plans</h2>"
                "<table><tr><td>A</td><td>1</td></tr><tr><td>B</td><td>2</td></tr></table>"
                '<script src="/static/app.js"></script>')
    assert script_dependent(thin)
    result = run(analyze_answer_format, thin)
    assert by_id(result, "question-answer-indirect") and by_id(result, "table-headers-missing")


def test_full_pages_produce_no_script_dependent_warning():
    result = run(analyze_context_retention, page(TEXT), page(TEXT, url=SITE + "/b"))
    assert result["warnings"] == [] and result["metrics"]["context_retention_script_dependent_pages"] == 0


# ------------------------------------------------------------- 2: addresses written as plain text

@pytest.mark.parametrize("text,expected", [
    ("Contact Address: 12 High Street, Springfield 4000 Phone 555 1234", "12 High Street, Springfield 4000"),
    ("Visit us at 221B Baker Street, London NW1 6XE. Call us", "221B Baker Street, London NW1 6XE."),
    ("Address 5th Floor, Tower B, Sector 62, Noida 201301 Tel +91", "5th Floor, Tower B, Sector 62, Noida 201301"),
    ("Head office 1600 Amphitheatre Parkway Mountain View, CA 94043",
     "1600 Amphitheatre Parkway Mountain View, CA 94043"),
    ("Find us 350 Fifth Avenue, New York, NY 10118 open daily", "350 Fifth Avenue, New York, NY 10118"),
    ("Shiv Nadar University, NH91, Tehsil Dadri, Gautam Buddha Nagar, Uttar Pradesh 201314 India",
     "Shiv Nadar University, NH91, Tehsil Dadri, Gautam Buddha Nagar, Uttar Pradesh 201314"),
])
def test_postal_addresses_in_plain_text_are_found(text, expected):
    assert find_postal_addresses(text) == [expected]


@pytest.mark.parametrize("text", [
    "Email address: hello@acme.com and IP address 10.0.0.1 here",
    "We will address 3 issues in the next release, and more",
    "Top 5 Dr Who episodes ranked",
    "Visit us at booth 42 during the expo",
    "Visit us at www.acme.com/stores 24 hours a day",
    "Plans: Basic, Pro, Enterprise 12345 users",
    "We serve schools, colleges, and 10000 students",
    "Address the gap. Our team, Product, Sales 40000",
    "Order ID 123456 shipped",
    "Join 50,000, 100,000 learners",
    "Copyright 2024 Acme. All rights reserved. 3 Main Street stores worldwide",
])
def test_text_that_is_not_a_postal_address_is_ignored(text):
    assert find_postal_addresses(text) == []


def test_text_scans_read_long_pages_whole_and_huge_pages_at_both_ends():
    filler = "<p>" + "Lorem Ipsum, Dolor Sit 12 amet, consectetur. " * 3000 + "</p>"  # about 138,000 characters
    middle = "<div>Address: 9 Mill Road, Leeds LS1 4AP</div>"
    footer = "<div class='footer'>Address: 12 High Street, Springfield 4000</div>"
    found = page(filler + middle + filler + footer).features["postal_address_text"]
    assert found == ("9 Mill Road, Leeds LS1 4AP", "12 High Street, Springfield 4000")
    huge = "<p>" + "Lorem ipsum dolor sit amet. " * 12000 + "</p>"  # about 336,000 characters
    found = page(huge + middle + huge + footer).features["postal_address_text"]
    assert found == ("12 High Street, Springfield 4000",)  # the middle of a 670,000-character page is not read


def test_address_in_a_plain_div_is_location_evidence():
    div = page('<div class="footer-contact"><h4>Address</h4><p>12 High Street, Springfield 4000</p></div>' + TEXT)
    finding = by_id(run(analyze_context_signals, div), "location-markup-missing")[0]
    assert finding["finding_type"] == "proactive_improvement" and finding["severity"] == "low"
    assert "12 High Street, Springfield 4000" in finding["evidence"][0]["description"]


def test_text_address_and_map_link_make_a_confirmed_defect():
    html = ('<div>Visit us at 221B Baker Street, London NW1 6XE.</div>'
            '<a href="https://maps.google.com/?q=221B+Baker+Street">Directions</a>' + TEXT)
    finding = by_id(run(analyze_context_signals, page(html)), "location-markup-missing")[0]
    assert finding["finding_type"] == "defect" and finding["severity"] == "medium"


def test_text_address_with_location_markup_is_quiet():
    head = '<script type="application/ld+json">' + json.dumps(
        {"@type": "Organization", "name": "Acme", "address": "12 High Street"}) + "</script>"
    html = "<p>Address: 12 High Street, Springfield 4000</p>" + TEXT
    assert not by_id(run(analyze_context_signals, page(html, head=head)), "location-markup-missing")


def test_hidden_text_address_is_not_evidence():
    html = '<div style="display:none">Address: 12 High Street, Springfield 4000</div>' + TEXT
    assert not by_id(run(analyze_context_signals, page(html)), "location-markup-missing")


def test_line_break_inside_an_element_separates_words():
    f = page('<address>12 High Street<br>Springfield 4000</address><a href="/c">Contact<br/>us</a>'
             '<button><br></button>' + TEXT).features
    assert f["address_text"] == ("12 High Street Springfield 4000",)
    assert ("/c", "Contact us") in f["anchors"]
    assert f["unnamed_control_count"] == 1  # a button holding only a line break still has no name


def test_contact_details_written_as_text_and_links_are_found():
    found = find_contact_details("Write to Info@Acme.com. Logo logo@2x.png. Phone: +1 (555) 010-0100 "
                                 "Call us on 020 7946 0958 Order 12345 Tel: 12")
    assert found == {"emails": ["info@acme.com"], "phones": ["+1 (555) 010-0100", "020 7946 0958"]}


def test_contact_shown_without_markup_is_a_suggestion_with_values():
    contact = page('<a href="mailto:hello@fixture.example?subject=Hi">Email us</a><p>Phone: +1 555 010 0100</p>'
                   + TEXT, url=SITE + "/contact")
    finding = by_id(run(analyze_context_signals, page(TEXT), contact), "contact-markup-missing")[0]
    assert finding["finding_type"] == "proactive_improvement" and finding["status"] == "suspected"
    assert finding["title"] == "Email or phone shown on 1/2 sampled pages but stated in no structured data"
    assert finding["evidence"][0]["description"].startswith("email: hello@fixture.example; phone: +1 555 010 0100")


@pytest.mark.parametrize("head,body", [
    ('<script type="application/ld+json">{"@type": "Organization", "telephone": "+1 555 010 0100"}</script>', ""),
    ('<script type="application/ld+json">{"@type": "Organization", "contactPoint": '
     '{"@type": "ContactPoint", "email": "hello@fixture.example"}}</script>', ""),
    ("", '<div itemscope itemtype="https://schema.org/Organization"><span itemprop="telephone">+1 555</span></div>'),
    ("", '<div vocab="https://schema.org/" typeof="Organization"><span property="email">a@b.co</span></div>'),
])
def test_contact_markup_in_any_form_silences_the_check(head, body):
    shown = page(body + '<a href="tel:+15550100100">Call</a>' + TEXT, head=head)
    assert not by_id(run(analyze_context_signals, shown), "contact-markup-missing")


def test_no_contact_details_means_no_contact_finding():
    result = run(analyze_context_signals, page('<a href="mailto:">Email</a><a href="tel:12">x</a>' + TEXT))
    assert not by_id(result, "contact-markup-missing") and result["metrics"]["context_contact_pages"] == 0


def test_contact_snippet_prefers_the_sites_own_generic_mailbox_and_common_phone():
    home = page('<a href="mailto:jane.doe@fixture.example">Jane</a><a href="mailto:info@fixture.example">Info</a>'
                '<a href="mailto:someone@gmail.com">x</a><a href="tel:+44 20 7946 0958">Call</a>' + TEXT)
    other = page('<p>Tel: 020 7946 0958</p><p>Phone: 0161 496 0000</p>' + TEXT, url=SITE + "/about")
    art = AuditArtifacts(SITE + "/", SITE, (home, other), freeze_value({"status": "ok"}),
                         freeze_value({"present": False, "status": "absent"}), freeze_value({"status": "ok"}),
                         freeze_value({"coverage": {"urls_analyzed": 2, "urls_discovered": 2}}), ())
    snippet = build_snippet("contact-markup-missing", [home, other], art, site_facts(art))
    code = json.loads(snippet["code"].split("\n", 2)[2].rsplit("</script>", 1)[0])
    assert code["email"] == "info@fixture.example" and code["telephone"] == "+44 20 7946 0958"
    assert code["contactPoint"][0]["contactType"] == "REPLACE_WITH_CONTACT_TYPE"
    assert {"email", "telephone"} <= set(snippet["filled_from"])
    bare = build_snippet("contact-markup-missing", [], art, site_facts(art))
    assert "REPLACE_WITH_EMAIL" in bare["placeholders"]


def test_location_snippet_uses_the_text_address():
    home = page("<p>Address: 12 High Street, Springfield 4000</p>" + TEXT)
    art = AuditArtifacts(SITE + "/", SITE, (home,), freeze_value({"status": "ok"}),
                         freeze_value({"present": False, "status": "absent"}), freeze_value({"status": "ok"}),
                         freeze_value({"coverage": {"urls_analyzed": 1, "urls_discovered": 1}}), ())
    snippet = build_snippet("location-markup-missing", [home], art, site_facts(art))
    assert '"address": "12 High Street, Springfield 4000"' in snippet["code"]
    assert "REPLACE_WITH_STREET_ADDRESS" not in snippet["code"]
