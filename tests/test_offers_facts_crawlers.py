"""Recall checks with no new requests: expired offers (check_offer_expiry.py),
on-site fact consistency (check_fact_consistency.py) and the labelled AI
crawler list (common/ai_crawlers.py). Pages are built from HTML strings; the
end-to-end test uses the local fixture server only."""
import json
import re
import sys
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

import ai_crawlers
from acquire_site import AI_CRAWLERS, _ai_crawler_directives, _ai_crawler_section_blocks, _extract_page
from check_ai_crawler_access import check_ai_crawler_access
from check_catalog import CATALOG
from check_fact_consistency import check_fact_consistency, parse_price, phone_key, price_shown
from check_offer_expiry import check_offer_expiry, text_deadlines
from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline
from robots_policy import RobotsPolicy
from transport import USER_AGENT, Response
from run_audit import run_audit
from fixtures_server import start_server

LIMITS = Limits()
SITE = "https://shop.example"
TODAY = date(2026, 10, 11)
FILLER = "<p>" + "Hand made goods shipped from our workshop to customers every single week of the year. " * 6 + "</p>"


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj) + "</script>"


def page(path="/", body="", head="<title>Shop</title>", lang="en", limits=LIMITS):
    url = SITE + path
    lang_attr = f' lang="{lang}"' if lang else ""
    html = f"<html{lang_attr}><head>{head}</head><body>{FILLER}{body}</body></html>"
    response = Response(200, {"Content-Type": "text/html"}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, limits)


def snapshot(*pages):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": False, "status": "absent"}), freeze_value({"status": "ok"}),
                          freeze_value({"coverage": coverage}), ())


def deadline():
    return make_deadline(LIMITS)


def expired(*pages, today=TODAY):
    return check_offer_expiry(snapshot(*pages), deadline(), today=today)


def facts(*pages):
    return check_fact_consistency(snapshot(*pages), deadline())


def ids(result):
    return {f["check_id"] for f in result["findings"]}


def evidence_of(result, check_id):
    return [e for f in result["findings"] if f["check_id"] == check_id for e in f["evidence"]]


# ===================================================================== 11: expired offers

def test_expired_offer_in_text_is_a_confirmed_medium_defect():
    result = expired(page("/products/mug", "<p>Summer sale ends 31 August 2025. Order today.</p>"))
    (finding,) = result["findings"]
    assert finding["check_id"] == "expired-offer" and finding["check_id"] in CATALOG
    assert finding["severity"] == "medium" and finding["status"] == "confirmed"
    assert finding["affected_pages"] == [SITE + "/products/mug"]
    (item,) = finding["evidence"]
    assert item["type"] == "expired_offer_text" and "2025-08-31" in item["description"]
    assert "Summer sale ends 31 August 2025" in item["description"]
    assert result["metrics"]["offer_deadlines_found"] == 1


def test_date_formats_that_are_read():
    for text, expected in [("Offer valid until 12/31/2025.", date(2025, 12, 31)),
                           ("Discount expires on March 3rd, 2026.", date(2026, 3, 3)),
                           ("Promo code good through 2026-01-15.", date(2026, 1, 15)),
                           ("This deal runs until Friday, 4 September 2026!", date(2026, 9, 4)),
                           ("Coupon valid till 1st of Feb 2026.", date(2026, 2, 1))]:
        (found,) = text_deadlines(text)
        assert expected in found[1], text


def test_live_past_tense_yearless_and_ambiguous_deadlines_are_not_expired():
    for text in ("Sale ends 31 December 2026.",            # still running
                 "The summer sale ended on 31 August 2025.",  # past tense: history
                 "Offer ends 31 August.",                   # no year
                 "Offer valid until 05/11/2026.",           # 5 Nov (future) or 11 May (past)
                 "Offers and free delivery through our partners in 2020."):  # no date after the deadline
        result = expired(page("/products/mug", f"<p>{text}</p>"))
        assert not result["findings"], text
    # Both readings of an ambiguous numeric date are past: expired.
    assert ids(expired(page("/products/mug", "<p>Offer valid until 05/06/2026.</p>"))) == {"expired-offer"}


def test_a_deadline_from_yesterday_is_not_yet_reported():
    yesterday = (TODAY - timedelta(days=1)).strftime("%d %B %Y")
    two_days = (TODAY - timedelta(days=2)).strftime("%d %B %Y")
    assert not expired(page("/products/mug", f"<p>Sale ends {yesterday}.</p>"))["findings"]
    assert expired(page("/products/mug", f"<p>Sale ends {two_days}.</p>"))["findings"]


def test_editorial_legal_archive_and_event_pages_are_skipped():
    text = "<p>Our spring sale ends 1 March 2024.</p>"
    for path in ("/blog/spring-sale", "/news", "/terms", "/archive/2024/sale"):
        assert not expired(page(path, text))["findings"], path
    event = jsonld({"@type": "Event", "name": "Spring fair",
                    "offers": {"@type": "Offer", "price": "10", "validThrough": "2024-03-01"}})
    assert not expired(page("/events/fair", text, head="<title>Fair</title>" + event))["findings"]


def test_expired_offer_markup_is_a_second_kind_of_evidence():
    past = jsonld({"@type": "Product", "name": "Mug",
                   "offers": {"@type": "Offer", "price": "12.00", "priceValidUntil": "2025-12-31"}})
    result = expired(page("/products/mug", "<p>Offer ends 1 January 2026.</p>", head="<title>Mug</title>" + past))
    kinds = {e["type"] for e in evidence_of(result, "expired-offer")}
    assert kinds == {"expired_offer_text", "expired_offer_markup"}
    future = jsonld({"@type": "Product", "name": "Mug",
                     "offers": {"@type": "Offer", "price": "12.00", "priceValidUntil": "2027-12-31"}})
    result = expired(page("/products/mug", head="<title>Mug</title>" + future))
    assert not result["findings"] and result["metrics"]["offer_deadlines_found"] == 1


def test_offer_expiry_stops_at_the_deadline():
    from models import AuditDeadline
    gone = AuditDeadline(0.0, 0.0, {})
    result = check_offer_expiry(snapshot(page("/products/mug", "<p>Sale ends 1 March 2024.</p>")), gone)
    assert result["status"] == "insufficient_evidence" and not result["findings"]


# ===================================================================== 10: fact consistency

ORG_PHONE = jsonld({"@type": "Organization", "name": "Acme", "telephone": "+1 555 010 0100"})


def test_markup_telephone_shown_nowhere_while_the_page_shows_another_is_a_mismatch():
    result = facts(page("/contact", "<p>Phone: (555) 010-0199</p>", head="<title>Contact</title>" + ORG_PHONE))
    (item,) = evidence_of(result, "fact-markup-mismatch")
    assert item["fact"] == "telephone" and "+1 555 010 0100" in item["description"]
    (finding,) = result["findings"]
    assert finding["status"] == "suspected" and finding["severity"] == "medium"
    assert "telephone" in finding["title"]


def test_the_same_telephone_written_differently_or_only_as_a_link_matches():
    shown = facts(page("/contact", "<p>Phone: (555) 010-0100</p>", head="<title>C</title>" + ORG_PHONE))
    assert not shown["findings"] and shown["metrics"]["facts_compared_with_text"] == 1
    linked = facts(page("/contact", '<p>Phone: (555) 010-0199</p><a href="tel:+15550100100">Call sales</a>',
                        head="<title>C</title>" + ORG_PHONE))
    assert not linked["findings"]
    # Shown on another sampled page (a head-office number in the footer of the about page).
    other = facts(page("/contact", "<p>Phone: (555) 010-0199</p>", head="<title>C</title>" + ORG_PHONE),
                  page("/about", "<p>Head office: +1 555-010-0100</p>"))
    assert not other["findings"]


def test_nothing_shown_on_the_page_is_no_comparison():
    result = facts(page("/contact", "<p>Write to us any time.</p>", head="<title>C</title>" + ORG_PHONE))
    assert not result["findings"] and result["metrics"]["facts_compared_with_text"] == 0


def test_postal_code_mismatch_and_match():
    org = jsonld({"@type": "Organization", "name": "Acme",
                  "address": {"@type": "PostalAddress", "streetAddress": "10 Downing Street",
                              "postalCode": "SW1A 1AA"}})
    wrong = facts(page("/contact", "<p>Address: 10 Downing Street, London SW1A 2AA</p>",
                       head="<title>C</title>" + org))
    assert [e["fact"] for e in evidence_of(wrong, "fact-markup-mismatch")] == ["postal_code"]
    right = facts(page("/contact", "<p>Address: 10 Downing Street, London SW1A 1AA</p>", head="<title>C</title>" + org))
    assert not right["findings"] and right["metrics"]["facts_compared_with_text"] == 1


def test_opening_hours_mismatch_match_and_24_hour_markup():
    def hours(spec, text):
        org = jsonld({"@type": "Bakery", "name": "Acme Bakery", "openingHours": spec})
        return facts(page("/visit", f"<p>{text}</p>", head="<title>Visit</title>" + org))
    wrong = hours("Mo-Fr 09:00-17:00", "Opening hours: Monday to Friday 10am - 6pm")
    assert [e["fact"] for e in evidence_of(wrong, "fact-markup-mismatch")] == ["opening_hours"]
    assert not hours("Mo-Fr 09:00-17:00", "Opening hours: Monday to Friday 9am - 5pm")["findings"]
    assert not hours("Mo-Fr 09:00-17:00", "Opening hours: Mon-Fri 09.00-17.00")["findings"]
    assert not hours("Mo-Su 00:00-23:59", "Opening hours: every day 10am - 6pm")["findings"]
    spec = jsonld({"@type": "Bakery", "name": "Acme Bakery", "openingHoursSpecification": [
        {"@type": "OpeningHoursSpecification", "dayOfWeek": "Monday", "opens": "08:00:00", "closes": "16:00:00"}]})
    result = facts(page("/visit", "<p>Hours: Monday 8am to 4pm</p>", head="<title>Visit</title>" + spec))
    assert not result["findings"] and result["metrics"]["facts_compared_with_text"] == 1


def _product(price, currency="USD", extra_offer=None):
    offers = [{"@type": "Offer", "price": price, "priceCurrency": currency}] + ([extra_offer] if extra_offer else [])
    return "<title>Mug</title>" + jsonld({"@type": "Product", "name": "Mug", "sku": "MUG", "gtin13": "0012345678905", "offers": offers})


def test_price_mismatch_only_with_one_offer_in_a_currency_the_page_shows():
    wrong = facts(page("/products/mug", "<p>Now $59.99. Pair it with a saucer for $12.00.</p>", head=_product("49.99")))
    (item,) = evidence_of(wrong, "fact-markup-mismatch")
    assert item["fact"] == "price" and "49.99" in item["description"]
    assert not facts(page("/products/mug", "<p>Now $49.99.</p>", head=_product("49.99")))["findings"]
    assert not facts(page("/products/mug", "<p>Now $1,299.00.</p>", head=_product("1299")))["findings"]
    # Geo-pricing: the page shows rupees, the markup dollars. Nothing to compare.
    assert not facts(page("/products/mug", "<p>Now \u20b94,150.</p>", head=_product("49.99")))["findings"]
    # Variants with two prices: nothing single to compare.
    variant = {"@type": "Offer", "price": "59.99", "priceCurrency": "USD"}
    assert not facts(page("/products/mug", "<p>Now $59.99.</p>", head=_product("49.99", extra_offer=variant)))[
        "findings"]


def test_pages_built_by_javascript_or_cut_short_are_not_compared():
    shell = page("/products/mug", '<div id="root"></div><script src="/app.js"></script>', head=_product("49.99"))
    shell = replace(shell, visible_text="", features=freeze_value(dict(shell.features, full_visible_chars=0)))
    assert not facts(shell)["findings"]
    short = page("/contact", "<p>Phone: (555) 010-0199</p>", head="<title>C</title>" + ORG_PHONE,
                 limits=replace(LIMITS, VISIBLE_TEXT_MAX_CHARS=50))
    assert not facts(short)["findings"]


def test_same_organization_with_two_telephones_on_two_pages_is_a_conflict():
    a = jsonld({"@type": "Organization", "name": "Acme", "telephone": "+1 555 010 0100"})
    b = jsonld({"@type": "Organization", "name": "ACME", "telephone": "+1 555 010 0199"})
    result = facts(page("/", head="<title>Home</title>" + a), page("/about", head="<title>About</title>" + b))
    (finding,) = [f for f in result["findings"] if f["check_id"] == "fact-inconsistent-across-pages"]
    assert finding["status"] == "confirmed" and finding["severity"] == "medium"
    (item,) = finding["evidence"]
    assert "telephone" in item["description"] and len(item["urls"]) == 2
    same = jsonld({"@type": "Organization", "name": "Acme", "telephone": "(555) 010-0100"})
    assert not facts(page("/", head="<title>H</title>" + a), page("/about", head="<title>A</title>" + same))["findings"]


def test_local_businesses_languages_and_relative_ids_are_not_compared():
    a = jsonld({"@type": "Restaurant", "name": "Joe's", "telephone": "+1 555 010 0100"})
    b = jsonld({"@type": "Restaurant", "name": "Joe's", "telephone": "+1 555 010 0199"})
    assert not facts(page("/store/a", head="<title>A</title>" + a), page("/store/b", head="<title>B</title>" + b))[
        "findings"]
    org_a = jsonld({"@type": "Organization", "name": "Acme", "telephone": "+44 20 7946 0000"})
    org_b = jsonld({"@type": "Organization", "name": "Acme", "telephone": "+1 555 010 0199"})
    assert not facts(page("/uk/", head="<title>A</title>" + org_a, lang="en-GB"),
                     page("/fr/", head="<title>B</title>" + org_b, lang="fr"))["findings"]
    rel_a = jsonld({"@type": "LocalBusiness", "@id": "#biz", "telephone": "+1 555 010 0100"})
    rel_b = jsonld({"@type": "LocalBusiness", "@id": "#biz", "telephone": "+1 555 010 0199"})
    assert not facts(page("/a", head="<title>A</title>" + rel_a), page("/b", head="<title>B</title>" + rel_b))[
        "findings"]


def test_same_gtin_two_prices_conflicts_only_in_one_currency_with_single_values():
    listing = "<title>Shop</title>" + jsonld({"@type": "Product", "name": "Mug", "sku": "MUG", "gtin13": "0012345678905",
                                              "offers": {"@type": "Offer", "price": "39.99", "priceCurrency": "USD"}})
    result = facts(page("/shop", head=listing), page("/products/mug", head=_product("49.99")))
    assert [f["check_id"] for f in result["findings"]] == ["fact-inconsistent-across-pages"]
    euro = "<title>Shop</title>" + jsonld({"@type": "Product", "name": "Mug", "sku": "MUG", "gtin13": "0012345678905",
                                           "offers": {"@type": "Offer", "price": "39.99", "priceCurrency": "EUR"}})
    assert not facts(page("/shop", head=euro), page("/products/mug", head=_product("49.99")))["findings"]
    variant = {"@type": "Offer", "price": "39.99", "priceCurrency": "USD"}
    assert not facts(page("/shop", head=listing),
                     page("/products/mug", head=_product("49.99", extra_offer=variant)))["findings"]
    # Colourway pages that share a family SKU but no GTIN are different items.
    def colour(price):
        return "<title>Mug</title>" + jsonld({"@type": "Product", "name": "Mug", "sku": "MUG",
                                              "offers": {"@type": "Offer", "price": price, "priceCurrency": "USD"}})
    assert not facts(page("/products/mug-red", head=colour("49.99")),
                     page("/products/mug-blue", head=colour("24.99")))["findings"]


def test_number_parsing_helpers():
    assert parse_price("1,299.00") == 1299.0 and parse_price("1.299,00") == 1299.0
    assert parse_price("49,99") == 49.99 and parse_price(12) == 12.0 and parse_price(True) is None
    assert parse_price("free") is None
    assert phone_key("+44 20 7946 0000") == phone_key("020 7946 0000")
    assert phone_key("12345") is None
    assert price_shown(49.99, "only 49,99 EUR") and not price_shown(49.99, "now 149.99")
    assert not price_shown(49.0, "now 49.50")


# ===================================================================== 12: AI crawler list

def test_crawler_list_is_labelled_unique_and_never_names_bing():
    names = [name for name, _, _ in ai_crawlers.CRAWLERS]
    assert len(names) == len(set(names)) and tuple(names) == AI_CRAWLERS
    assert {purpose for _, _, purpose in ai_crawlers.CRAWLERS} == {"search", "training", "user_fetch"}
    for required in ("Applebot-Extended", "Amazonbot", "Meta-ExternalAgent", "Claude-User", "Perplexity-User"):
        assert required in names
    source = (ROOT / "common" / "ai_crawlers.py").read_text(encoding="utf-8").lower()
    assert "bing" not in source and not any("bing" in n.lower() for n in names)


def test_robots_product_tokens_match_exactly_for_crawler_rules():
    rp = RobotsPolicy("User-agent: Applebot\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
    assert not rp.can_fetch_token("Applebot", SITE + "/")
    assert rp.can_fetch_token("Applebot-Extended", SITE + "/")
    rp = RobotsPolicy("User-agent: Applebot-Extended\nDisallow: /\n")
    assert rp.can_fetch_token("Applebot", SITE + "/") and not rp.can_fetch_token("Applebot-Extended", SITE + "/")
    rp = RobotsPolicy("user-agent: gptbot/1.0\ndisallow: /private\n")
    assert not rp.can_fetch_token("GPTBot", SITE + "/private/x") and rp.can_fetch_token("GPTBot", SITE + "/")
    # This audit's own crawler keeps the stricter substring match.
    rp = RobotsPolicy("User-agent: BrandAIReadinessAuditBot\nDisallow: /\n")
    assert not rp.can_fetch(USER_AGENT, SITE + "/")


def test_directives_cover_every_listed_crawler():
    rp = RobotsPolicy("User-agent: Amazonbot\nDisallow: /\n")
    directives = _ai_crawler_directives(rp, SITE + "/", conservative=False)
    assert tuple(directives) == AI_CRAWLERS and directives["Amazonbot"] == "disallow"
    assert {v for k, v in directives.items() if k != "Amazonbot"} == {"allow"}
    blocks = _ai_crawler_section_blocks(RobotsPolicy("User-agent: Meta-ExternalAgent\nDisallow: /docs/\n"),
                                        [SITE + "/docs/a", SITE + "/about"], conservative=False)
    assert blocks == {"Meta-ExternalAgent": [SITE + "/docs/a"]}


def _access(directives, sections=None):
    artifacts = SimpleNamespace(robots_data={"status": "ok", "ai_crawler_directives": directives,
                                             "ai_crawler_section_blocks": sections or {}}, site_url=SITE + "/")
    return check_ai_crawler_access(artifacts, deadline())


def test_blocking_a_search_crawler_is_high_and_training_or_user_fetch_is_low():
    allow = {name: "allow" for name in AI_CRAWLERS}
    apple = _access(dict(allow, Applebot="disallow"))
    (finding,) = apple["findings"]
    assert finding["severity"] == "high" and finding["finding_type"] == "defect" and "Applebot" in finding["title"]
    for name in ("Amazonbot", "Applebot-Extended", "Meta-ExternalFetcher", "Claude-User"):
        (finding,) = _access(dict(allow, **{name: "disallow"}))["findings"]
        assert finding["severity"] == "low" and finding["finding_type"] == "proactive_improvement", name
    mixed = _access(dict(allow, GPTBot="disallow", **{"ChatGPT-User": "disallow", "OAI-SearchBot": "disallow"}))
    (finding,) = mixed["findings"]
    descriptions = [e["description"] for e in finding["evidence"]]
    assert descriptions == [
        "robots.txt disallows the AI search crawler(s) OAI-SearchBot for the start URL",
        "robots.txt disallows the user-requested fetch crawler(s) ChatGPT-User for the start URL",
        "robots.txt disallows the model training crawler(s) GPTBot for the start URL"]
    assert "AI search: OAI-SearchBot; user-requested fetch: ChatGPT-User; model training: GPTBot" in finding["root_cause"]
    assert mixed["metrics"]["ai_crawler_purposes"]["Amazonbot"] == "training"


def test_an_unlisted_crawler_name_is_labelled_not_dropped():
    result = _access({"FooBot": "disallow"}, sections={"BarBot": [SITE + "/docs/a"]})
    titles = [f["title"] for f in result["findings"]]
    assert len(titles) == 2 and "FooBot" in titles[0]
    assert "unclassified: FooBot" in result["findings"][0]["root_cause"]
    assert result["metrics"]["ai_crawler_purposes"] == {"FooBot": "unclassified"}


# ===================================================================== end to end

def test_full_audit_runs_the_new_checks_and_reports_their_metrics():
    url, stop = start_server(clean=True)
    try:
        report = run_audit(url + "/", replace(LIMITS, MAX_PAGES_CRAWLED=6), allow_private_targets=True)
    finally:
        stop()
    cov = report["coverage"]
    assert "offer_deadlines_found" in cov["offer_expiry"] and "facts_compared_with_text" in cov["fact_consistency"]
    assert set(cov["ai_crawler_purposes"]) == set(AI_CRAWLERS)
    # The clean fixture states no expired offer and no conflicting fact.
    found = {c for f in report["findings"] for c in (f.get("check_ids") or [f["check_id"]])}
    assert not found & {"expired-offer", "fact-markup-mismatch", "fact-inconsistent-across-pages"}
    assert not any("Dropped" in w for w in report["warnings"])
