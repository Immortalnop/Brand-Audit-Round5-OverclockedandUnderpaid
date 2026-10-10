"""Page update dates (sitemap lastmod, HTTP Last-Modified) and knowledge-graph links.

Covers update_signals.py and its use in assess_freshness.py, the lastmod capture
in acquire_site.py, check_knowledge_graph.py (with a fake transport, so no test
touches the network), the AG-05 agent handoff, and a full fixture audit.
"""
import json
import sys
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
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
from models import AuditArtifacts, freeze_value, make_deadline, intermediate_artifact
from transport import Response
from acquire_site import _extract_page, acquire_site
from update_signals import (parse_w3c_date, parse_lastmod, parse_http_date, sitemap_lastmod_quality,
                            page_update_claims)
from assess_freshness import assess_freshness
from check_knowledge_graph import check_knowledge_graph, parse_kg_links, LOOKUP_ENV
from ingest_agent_findings import ingest_agent_findings
from execution_summary import derive_limitations
from check_catalog import CATALOG, get_entry
from instrumentation import Instrumentation
from run_audit import run_audit
from fixtures_server import start_server

LIMITS = Limits()
SITE = "https://fixture.example"
NOW = datetime.now(timezone.utc)
OLD_YEAR = NOW.year - 6


def page(html="<html><body><p>Hello</p></body></html>", url=SITE + "/", headers=None, status=200):
    response = Response(status, {"Content-Type": "text/html", **(headers or {})}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def snapshot(pages, sitemap=None):
    sitemap = sitemap if sitemap is not None else {"status": "ok"}
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": True, "status": "ok"}), freeze_value(sitemap),
                          freeze_value({"coverage": coverage}), ())


def http_date(dt):
    return format_datetime(dt.astimezone(timezone.utc), usegmt=True)


def no_facts():
    return intermediate_artifact("important_facts", data={"facts": []})


def freshness(pages, sitemap=None, claims=None):
    return assess_freshness(no_facts(), snapshot(pages, sitemap), make_deadline(LIMITS), claims)


def ids(result):
    return [f["check_id"] for f in result["findings"]]


# ---------------------------------------------------------------- date parsing

@pytest.mark.parametrize("value,expected", [
    ("2024", date(2024, 1, 1)),
    ("2024-03", date(2024, 3, 1)),
    ("2024-03-05", date(2024, 3, 5)),
    ("2024-03-05T10:20+01:00", date(2024, 3, 5)),
    ("2024-03-05T10:20:30.5Z", date(2024, 3, 5)),
    (" 2024-03-05T10:20:30Z ", date(2024, 3, 5)),
    ("2024-13-01", None),
    ("2024-02-30", None),
    ("05/03/2024", None),
    ("2024-03-05T25:00Z", None),
    ("2024-03-05T10:61Z", None),
    ("", None),
    (None, None),
    (20240305, None),
])
def test_parse_w3c_date(value, expected):
    assert parse_w3c_date(value) == expected


def test_parse_lastmod_accepts_space_separated_form_as_nonstandard():
    assert parse_lastmod("2023-07-25T15:19:07+00:00") == (date(2023, 7, 25), True)
    assert parse_lastmod("2023-07-25 15:19:07") == (date(2023, 7, 25), False)
    assert parse_lastmod("2023-07-25 15:19") == (date(2023, 7, 25), False)
    assert parse_lastmod("2023-07-25 25:19:07") == (None, False)
    assert parse_lastmod("2023-07-25  junk") == (None, False)
    quality = sitemap_lastmod_quality({"url_entries": 1, "lastmod": {SITE + "/": "2023-07-25 15:19:07"}})
    assert quality["valid"] == {SITE + "/": date(2023, 7, 25)}
    assert [i["issue"] for i in quality["invalid"]] == ["nonstandard"]


def test_parse_http_date():
    parsed = parse_http_date("Wed, 01 Mar 2017 10:00:00 GMT")
    assert parsed == datetime(2017, 3, 1, 10, 0, tzinfo=timezone.utc)
    assert parse_http_date("Wed, 01 Mar 2017 10:00:00 +0200").hour == 8
    for bad in ("", "yesterday", "Wed, 99 Foo 2017", None, 5):
        assert parse_http_date(bad) is None


# ---------------------------------------------------------- sitemap lastmod

def test_lastmod_quality_flags_invalid_future_and_uniform():
    future = (NOW.date() + timedelta(days=30)).isoformat()
    quality = sitemap_lastmod_quality({"url_entries": 3, "lastmod": {
        SITE + "/a": "2024-01-02", SITE + "/b": "not a date", SITE + "/c": future}})
    assert set(quality["valid"]) == {SITE + "/a"}
    assert sorted(i["issue"] for i in quality["invalid"]) == ["future", "unparseable"]
    assert quality["trusted"] and quality["uniform"] is None

    stamped = {f"{SITE}/{n}": "2025-05-05T00:00:00Z" for n in range(5)}
    quality = sitemap_lastmod_quality({"url_entries": 5, "lastmod": stamped})
    assert quality["uniform"] == {"date": "2025-05-05", "count": 5, "of": 5}
    assert not quality["trusted"]

    varied = {f"{SITE}/{n}": f"2025-05-{n + 1:02d}" for n in range(5)}
    assert sitemap_lastmod_quality({"url_entries": 5, "lastmod": varied})["trusted"]
    # Missing or malformed sitemap data never raises.
    assert sitemap_lastmod_quality({})["url_entries"] == 0
    assert sitemap_lastmod_quality({"lastmod": "oops", "url_entries": "x"})["url_entries"] == 0


# ---------------------------------------------------------- page update claims

def test_page_update_claims_choose_latest_trusted_signal_and_category():
    product = page(url=SITE + "/product", headers={"Last-Modified": "Wed, 01 Mar 2017 10:00:00 GMT",
                                                   "Date": http_date(NOW)})
    home = page(url=SITE + "/", headers={"last-modified": http_date(NOW - timedelta(days=400)),
                                         "date": http_date(NOW)})
    about = page(url=SITE + "/about")
    sitemap = {"status": "ok", "url_entries": 3, "lastmod": {
        SITE + "/product": "2016-01-01", SITE + "/about": "2015-06-01", SITE + "/": "2010-01-01"}}
    claims, metrics, _ = page_update_claims([product, home, about], sitemap, NOW)
    by_url = {c["source"]: c for c in claims}
    assert by_url[SITE + "/product"]["predicate"] == "HTTP Last-Modified"
    assert by_url[SITE + "/product"]["iso_date"] == "2017-03-01"
    assert by_url[SITE + "/product"]["category"] == "commercial"
    # Lower-case header names are read too; the newer header beats the old lastmod.
    assert by_url[SITE + "/"]["predicate"] == "HTTP Last-Modified"
    assert by_url[SITE + "/"]["category"] == "operational"
    about_claim = by_url[SITE + "/about"]
    assert (about_claim["predicate"], about_claim["iso_date"], about_claim["category"]) == \
        ("sitemap lastmod", "2015-06-01", "editorial")
    assert metrics["update_dates_from_sitemap_lastmod"] == 1
    assert metrics["update_dates_from_last_modified"] == 2
    assert metrics["sitemap_lastmod_trusted"] is True


def test_generated_future_and_unparseable_last_modified_are_ignored():
    served = NOW - timedelta(hours=2)
    pages = [
        page(url=SITE + "/a", headers={"Last-Modified": http_date(served), "Date": http_date(served)}),
        page(url=SITE + "/b", headers={"Last-Modified": http_date(NOW + timedelta(days=9)),
                                       "Date": http_date(NOW)}),
        page(url=SITE + "/c", headers={"Last-Modified": "sometime"}),
        page(url=SITE + "/d", headers={"Last-Modified": http_date(NOW - timedelta(seconds=30))}),
        page(url=SITE + "/e"),
    ]
    claims, metrics, _ = page_update_claims(pages, {"status": "ok"}, NOW)
    assert claims == []
    assert metrics["last_modified_header"] == {"generated_per_request": 2, "future": 1,
                                              "unparseable": 1, "absent": 1}


def test_failed_pages_and_build_stamped_sitemap_give_no_claims():
    broken = page(url=SITE + "/gone", status=404,
                  headers={"Last-Modified": "Wed, 01 Mar 2017 10:00:00 GMT", "Date": http_date(NOW)})
    stamped = {f"{SITE}/{n}": "2016-02-02" for n in range(6)}
    pages = [broken] + [page(url=f"{SITE}/{n}") for n in range(6)]
    claims, metrics, quality = page_update_claims(pages, {"status": "ok", "url_entries": 6,
                                                          "lastmod": stamped}, NOW)
    assert claims == [] and not quality["trusted"]
    assert metrics["sitemap_lastmod_trusted"] is False


def test_lastmod_matches_final_url_after_redirect():
    redirected = replace(page(url=SITE + "/old"), final_url=SITE + "/new")
    claims, _, _ = page_update_claims([redirected], {"status": "ok", "url_entries": 1,
                                                     "lastmod": {SITE + "/new": "2018-08-08"}}, NOW)
    assert claims[0]["source"] == SITE + "/old" and claims[0]["iso_date"] == "2018-08-08"


# ---------------------------------------------------------- assess_freshness

def test_old_last_modified_on_product_page_is_stale_commercial():
    product = page(url=SITE + "/product", headers={"Last-Modified": f"Wed, 01 Mar {OLD_YEAR} 10:00:00 GMT",
                                                   "Date": http_date(NOW)})
    result = freshness([product])
    assert ids(result) == ["stale-dates:commercial"]
    assert "HTTP Last-Modified" in result["findings"][0]["evidence_text"]
    assert result["metrics"]["page_update_date_facts"] == 1


def test_recent_page_update_supersedes_old_editorial_text_dates():
    article = page(url=SITE + "/blog/post", headers={"Last-Modified": http_date(NOW - timedelta(days=20)),
                                                     "Date": http_date(NOW)})
    claim = {"source": SITE + "/blog/post", "subject": "date_mention", "predicate": "mentions_date",
             "value": f"March 3, {OLD_YEAR}", "type": "date", "category": "editorial"}
    claims = intermediate_artifact("claims", data={"claims": [claim]})
    result = freshness([article], claims=claims)
    assert ids(result) == []
    assert result["metrics"]["text_dates_superseded_by_structured_update"] == 1
    # Without the update signal the same text date is reported.
    assert ids(freshness([page(url=SITE + "/blog/post")], claims=claims)) == ["stale-dates:editorial"]


def test_page_update_older_than_jsonld_date_is_not_double_counted():
    recent = (NOW.date() - timedelta(days=10)).isoformat()
    html = ('<html><head><script type="application/ld+json">{"@type":"Article","dateModified":"'
            + recent + '"}</script></head><body><p>Post</p></body></html>')
    article = page(html, url=SITE + "/blog/post",
                   headers={"Last-Modified": f"Wed, 01 Mar {OLD_YEAR} 10:00:00 GMT", "Date": http_date(NOW)})
    result = freshness([article])
    assert ids(result) == []
    assert result["metrics"]["page_update_date_facts"] == 0
    assert result["metrics"]["structured_date_facts"] == 1


@pytest.mark.parametrize("sitemap,status,in_evidence", [
    ({"status": "ok", "url_entries": 4, "lastmod": {}}, "confirmed", "None of the 4 sitemap URL entries"),
    ({"status": "ok", "url_entries": 1, "lastmod": {SITE + "/": "last week"}}, "confirmed",
     "is not a date in W3C Datetime form"),
    ({"status": "ok", "url_entries": 1, "lastmod": {SITE + "/": "2023-07-25 15:19:07"}}, "confirmed",
     "a 'T' must separate date and time"),
    ({"status": "ok", "url_entries": 6, "lastmod": {f"{SITE}/{n}": "2025-01-01" for n in range(6)}},
     "suspected", "6 of 6 valid lastmod values are the same date"),
])
def test_sitemap_lastmod_unreliable(sitemap, status, in_evidence):
    result = freshness([page()], sitemap)
    finding = next(f for f in result["findings"] if f["check_id"] == "sitemap-lastmod-unreliable")
    assert finding["status"] == status and finding["severity"] == "low"
    assert in_evidence in finding["evidence_text"]


@pytest.mark.parametrize("sitemap", [
    {"status": "absent", "url_entries": 0},
    {"status": "ok"},
    {"status": "ok", "url_entries": 3, "lastmod": {f"{SITE}/{n}": f"2025-0{n + 1}-01" for n in range(3)}},
])
def test_sitemap_lastmod_quiet_when_not_read_or_fine(sitemap):
    assert "sitemap-lastmod-unreliable" not in ids(freshness([page()], sitemap))


# ---------------------------------------------------------- acquisition

def test_acquisition_records_lastmod_and_audit_uses_both_signals():
    base, stop = start_server(sitemap_mode="lastmod")
    try:
        limits = Limits(TOTAL_AUDIT_TIMEOUT_S=60, REQUEST_DELAY_S=0)
        artifacts = acquire_site(base, make_deadline(limits), limits, allow_private_targets=True)
        lastmod = artifacts.sitemap_data["lastmod"]
        assert artifacts.sitemap_data["url_entries"] == 3
        assert lastmod[base + "/about"] == "2015-06-01"
        assert lastmod[base + "/product"] == "2016-01-01T08:00:00+00:00"
        report = run_audit(base, limits=limits, allow_private_targets=True)
    finally:
        stop()
    signals = report["coverage"]["freshness_update_signals"]
    assert signals["sitemap_lastmod_trusted"] is True
    assert signals["update_dates_from_last_modified"] >= 1
    evidence = " ".join(f["evidence_text"] for f in report["findings"] if f["check_id"].startswith("stale-dates"))
    assert "HTTP Last-Modified Wed, 01 Mar 2017" in evidence
    assert "sitemap lastmod 2015-06-01" in evidence
    # The fixture declares no knowledge-graph link: the deterministic check fires and
    # no third-party request is made.
    assert "kg-link-missing" in {f["check_id"] for f in report["findings"]}
    assert report["coverage"]["knowledge_graph"]["lookup"] == "not_needed"
    assert report["coverage"]["external_fetches"] == 0


# ---------------------------------------------------------- knowledge graph

class FakeTransport:
    """Mimics Transport.get for one origin: robots enforcement and canned responses."""

    def __init__(self, origin, routes, log):
        self.origin, self.routes, self.log = origin, routes, log
        self.robots = None
        self.delay = 0.0

    def get(self, url, *, robots_exempt=False, max_bytes=None, headers=None):
        if not robots_exempt and self.robots is not None and not self.robots.can_fetch("x", url):
            return None, "robots_disallowed"
        self.log.append((url, dict(headers or {})))
        route = self.routes.get(url)
        if route is None:
            return Response(404, {"Content-Type": "text/html"}, b"missing", url), "ok"
        if isinstance(route, str) and not route.startswith(("{", "<", "User", "\n")):
            return None, route  # a transport failure status such as "timeout"
        status, body = route if isinstance(route, tuple) else (200, route)
        body = body.encode() if isinstance(body, str) else body
        truncated = max_bytes is not None and len(body) > max_bytes
        return Response(status, {"Content-Type": "application/json"}, body[:max_bytes], url, truncated), "ok"


WD = "https://www.wikidata.org"
WP = "https://en.wikipedia.org"
ALLOW = "User-agent: *\nDisallow: /w/\n"


def entity_json(qid, label, websites=(), aliases=()):
    return json.dumps({"entities": {qid: {
        "id": qid, "labels": {"en": {"language": "en", "value": label}},
        "aliases": {"en": [{"language": "en", "value": a} for a in aliases]},
        "claims": {"P856": [{"mainsnak": {"datavalue": {"value": w}}} for w in websites]}}}})


def kg(same_as, routes, name="Acme Widgets", site=SITE, identity=None, extra_blocks=()):
    blocks = [{"@type": "Organization", "name": name, "sameAs": same_as}, *extra_blocks]
    pages = (SimpleNamespace(url=site + "/", jsonld_blocks=tuple(freeze_value(b) for b in blocks)),)
    artifacts = SimpleNamespace(pages=pages, site_url=site + "/", normalized_origin=site)
    log, made = [], []

    def factory(origin, deadline, limits):
        made.append(origin)
        return FakeTransport(origin, routes, log)

    identity = identity or {"status": "success", "data": {"canonical_name": name, "confidence": .92}}
    inst = Instrumentation()
    result = check_knowledge_graph(artifacts, identity, make_deadline(LIMITS), LIMITS, inst,
                                   transport_factory=factory)
    return result, log, made, inst


def test_parse_kg_links_forms():
    wikidata, wikipedia, malformed = parse_kg_links([
        "https://www.wikidata.org/wiki/Q42", "http://wikidata.org/entity/Q7", "https://m.wikidata.org/wiki/Q8/",
        "https://www.wikidata.org/wiki/Special:EntityPage/Q9", "https://www.wikidata.org/wiki/Property:P31",
        "https://de.wikipedia.org/wiki/Acme%20GmbH", "https://en.m.wikipedia.org/wiki/Acme",
        "https://en.wikipedia.org/wiki/Special:Search", "https://www.wikipedia.org/", "https://twitter.com/x",
        "ftp://www.wikidata.org/wiki/Q1", 42, "http://[bad"])
    assert [q for _, q in wikidata] == ["Q42", "Q7", "Q8", "Q9"]
    assert [(lang, title) for _, lang, title in wikipedia] == [("de", "Acme GmbH"), ("en", "Acme")]
    assert malformed == ["https://www.wikidata.org/wiki/Property:P31", "https://en.wikipedia.org/wiki/Special:Search"]


def test_no_organization_markup_is_not_assessed():
    artifacts = SimpleNamespace(pages=(SimpleNamespace(url=SITE + "/", jsonld_blocks=()),),
                                site_url=SITE + "/", normalized_origin=SITE)
    result = check_knowledge_graph(artifacts, {}, make_deadline(LIMITS), LIMITS)
    assert result["status"] == "insufficient_evidence" and result["findings"] == []


def test_missing_link_is_low_and_medium_under_ambiguity_without_any_request():
    result, log, made, _ = kg(["https://twitter.com/acme", "https://www.wikidata.org/wiki/Property:P1"], {})
    (finding,) = result["findings"]
    assert finding["check_id"] == "kg-link-missing" and finding["severity"] == "low"
    assert "names no item" in finding["evidence_text"]
    assert log == [] and made == []
    ambiguous = {"status": "partial", "data": {"canonical_name": "Acme", "confidence": .55,
                                                "ambiguity_type": "multi_brand_conflict"}}
    result, _, _, _ = kg([], {}, identity=ambiguous)
    assert result["findings"][0]["severity"] == "medium"


def test_verified_entity_has_no_finding_and_uses_robots_then_gzip_get():
    routes = {WD + "/robots.txt": ALLOW,
              WD + "/wiki/Special:EntityData/Q5.json": entity_json("Q5", "Acme", ["https://acme.example/"])}
    result, log, made, inst = kg(["https://www.wikidata.org/wiki/Q5"], routes, site="https://www.acme.example")
    assert result["findings"] == [] and result["metrics"]["verdict"] == "verified"
    assert made == [WD]
    assert [u for u, _ in log] == [WD + "/robots.txt", WD + "/wiki/Special:EntityData/Q5.json"]
    assert log[1][1] == {"Accept-Encoding": "gzip"}
    assert inst.external_fetches_attempted == 2
    # Subdomain of the declared official website also verifies.
    result, _, _, _ = kg(["https://www.wikidata.org/wiki/Q5"], routes, site="https://shop.acme.example")
    assert result["metrics"]["verdict"] == "verified"


@pytest.mark.parametrize("entity,check,status,text", [
    (entity_json("Q5", "Acme Widgets", ["https://other.example/"]), "kg-entity-mismatch", "confirmed",
     "official website as https://other.example/"),
    (entity_json("Q5", "Universe"), "kg-entity-mismatch", "suspected", "matches none of the brand names"),
    (entity_json("Q5", "Acme Widgets Inc."), "kg-link-missing", "confirmed", "has no official website (P856)"),
    (entity_json("Q5", "Something", aliases=["ACME WIDGETS"]), "kg-link-missing", "confirmed", "P856"),
    ((404, "{}"), "kg-entity-mismatch", "confirmed", "does not exist or was deleted"),
    (json.dumps({"entities": {"Q5": {"id": "Q5", "missing": ""}}}), "kg-entity-mismatch", "confirmed",
     "does not exist"),
])
def test_declared_entity_verdicts(entity, check, status, text):
    routes = {WD + "/robots.txt": ALLOW, WD + "/wiki/Special:EntityData/Q5.json": entity}
    result, _, _, _ = kg(["https://www.wikidata.org/wiki/Q5"], routes, site="https://acme.example")
    (finding,) = result["findings"]
    assert (finding["check_id"], finding["status"]) == (check, status)
    assert text in finding["evidence_text"]


def test_wikipedia_article_resolves_to_item_and_cross_checks_wikidata():
    article = '<html><script>RLCONF={"wgWikibaseItemId":"Q5","wgPageName":"Acme"}</script>'
    routes = {WP + "/robots.txt": ALLOW, WD + "/robots.txt": ALLOW, WP + "/wiki/Acme_Widgets": article,
              WD + "/wiki/Special:EntityData/Q5.json": entity_json("Q5", "Acme", ["https://acme.example"])}
    result, log, made, _ = kg(["https://en.wikipedia.org/wiki/Acme Widgets"], routes, site="https://acme.example")
    assert result["findings"] == [] and result["metrics"]["entity"]["id"] == "Q5"
    assert made == [WP, WD]
    result, _, _, _ = kg(["https://www.wikidata.org/wiki/Q9", "https://en.wikipedia.org/wiki/Acme_Widgets"],
                         {**routes, WD + "/wiki/Special:EntityData/Q9.json": entity_json("Q9", "Acme Widgets",
                                                                                         ["https://acme.example"])},
                         site="https://acme.example")
    (finding,) = result["findings"]
    assert finding["check_id"] == "kg-entity-mismatch"
    assert "belongs to Q5" in finding["evidence_text"]
    result, _, _, _ = kg(["https://en.wikipedia.org/wiki/Nope"], routes)
    assert "does not exist (HTTP 404)" in result["findings"][0]["evidence_text"]


@pytest.mark.parametrize("routes,expected_requests", [
    ({WD + "/robots.txt": "User-agent: *\nDisallow: /wiki/\n"}, 1),
    ({WD + "/robots.txt": (500, "error")}, 1),
    ({WD + "/robots.txt": "timeout"}, 1),
    ({WD + "/robots.txt": ALLOW, WD + "/wiki/Special:EntityData/Q5.json": "timeout"}, 2),
    ({WD + "/robots.txt": ALLOW, WD + "/wiki/Special:EntityData/Q5.json": "{not json"}, 2),
    ({WD + "/robots.txt": ALLOW, WD + "/wiki/Special:EntityData/Q5.json": "{" + " " * 2_100_000 + "}"}, 2),
    ({WD + "/robots.txt": ALLOW,
      WD + "/wiki/Special:EntityData/Q5.json": json.dumps({"entities": {"Q5": {"labels": [], "claims": 3}}})}, 2),
])
def test_unverifiable_lookup_is_a_warning_never_a_finding(routes, expected_requests):
    result, log, _, _ = kg(["https://www.wikidata.org/wiki/Q5"], routes)
    assert result["findings"] == []
    assert result["metrics"]["lookup"] == "incomplete"
    assert "not a site defect" in result["warnings"][0]
    assert len(log) == expected_requests


def test_lookup_can_be_disabled(monkeypatch):
    monkeypatch.setenv(LOOKUP_ENV, "0")
    result, log, made, _ = kg(["https://www.wikidata.org/wiki/Q5"], {})
    assert result["findings"] == [] and made == [] and result["metrics"]["lookup"] == "disabled"


def test_ag05_ingests_as_namesake_ambiguity(tmp_path, monkeypatch):
    path = tmp_path / "agent.json"
    path.write_text(json.dumps({"findings": [{"check": "AG-05", "evidence": [
        {"type": "knowledge_graph", "description": "Wikidata Q1 and Q2 are both named Acme"}]}]}), encoding="utf-8")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    artifacts = SimpleNamespace(pages=())
    result = ingest_agent_findings(artifacts, {}, make_deadline(LIMITS))
    (finding,) = result["findings"]
    assert finding["check_id"] == "kg-namesake-ambiguity"
    assert finding["root_cause"] == get_entry("kg-namesake-ambiguity")["mechanism"]
    assert finding["finding_type"] == "proactive_improvement"


def test_limitations_explain_unverified_entity_and_unrun_namesake_search():
    artifacts = SimpleNamespace(robots_data={}, sitemap_data={"status": "ok"}, media_data=None)
    caps = {"headless_rendering": True, "external_search": True}
    lines = derive_limitations(artifacts, caps, {"knowledge_graph": {"lookup": "incomplete", "organization_pages": 1}},
                               "completed")
    assert any("could not be fully verified" in line for line in lines)
    assert any("AG-05" in line for line in lines)
    lines = derive_limitations(artifacts, caps, {"knowledge_graph": {"lookup": "completed", "organization_pages": 1},
                                                 "agent_corroboration_stage": "ingested"}, "completed")
    assert not any("knowledge-graph" in line or "AG-05" in line for line in lines)


def test_new_catalog_entries_are_complete():
    for check_id in ("sitemap-lastmod-unreliable", "kg-link-missing", "kg-entity-mismatch",
                     "kg-namesake-ambiguity"):
        assert check_id in CATALOG and get_entry(check_id)
