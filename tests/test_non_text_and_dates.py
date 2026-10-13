"""Facts locked in non-text media (images, PDFs) and structured-date freshness.

Covers the standard-library helpers (common/non_text.py, common/pdf_text.py),
the analysis rules (analyze_non_text.py, assess_freshness.py), the agent vision
handoff (AG-04), and a full audit against a local fixture that must respect
robots.txt, same-origin and fetch caps while finding the locked facts.
"""
import json
import struct
import sys
import time
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
from non_text import extract_facts, raster_dimensions, svg_text, fact_keywords, image_tokens
from pdf_text import extract_pdf_text
from analyze_non_text import analyze_non_text
from assess_freshness import assess_freshness
from extract_claims import structured_date_claims
from ingest_agent_findings import ingest_agent_findings
from merge_findings import merge_findings
from check_catalog import CATALOG, get_entry
from run_audit import run_audit
from fixtures_server import (start_server, build_pdf, pdf_stream, text_pdf, image_only_pdf,
                             png_header)

LIMITS = Limits()
SITE = "https://fixture.example"
NOW_YEAR = datetime.now(timezone.utc).year


def page(html, url=SITE + "/", headers=None):
    response = Response(200, {"Content-Type": "text/html", **(headers or {})}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def snapshot(pages, media=None, discovered=None):
    analyzed = len(pages)
    coverage = {"urls_analyzed": analyzed, "urls_discovered": discovered or analyzed}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": True, "status": "ok"}), freeze_value({"status": "ok"}),
                          freeze_value({"coverage": coverage}), (),
                          media_data=freeze_value(media) if media is not None else None)


def image(url, pages, **extra):
    tokens = image_tokens(url, extra.get("alt"), extra.get("title"))
    entry = {"url": url, "pages": pages, "alt": None, "title": None, "width_attr": None,
             "height_attr": None, "kind": "raster", "keywords": list(fact_keywords(tokens)),
             "excluded": False, "same_origin": True, "fetch_status": "ok"}
    entry.update(extra)
    return entry


def media(images=(), pdfs=()):
    return {"images": list(images), "pdfs": list(pdfs), "summary": {"images_observed": len(images)}}


def checks(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


DEADLINE = lambda: make_deadline(LIMITS)  # noqa: E731


# ---------------------------------------------------------------------------
# Helpers: fact extraction, image headers, SVG text
# ---------------------------------------------------------------------------

def test_extract_facts_shapes_and_false_positive_guards():
    facts = extract_facts("Call +1 555-123-4567 or (020) 7946 0958. Basic $1,299.00 or EUR 49. "
                          "Output 500 W, weight 2.5 kg. Released 2019-03-01. Table 100 200 300. 3 in stock.")
    kinds = {(k, key) for k, _, key in facts}
    assert ("price", "1299") in kinds and ("price", "49") in kinds
    assert ("spec", "500") in kinds and ("spec", "2.5") in kinds
    assert ("phone", "5551234567") in kinds and ("phone", "2079460958") in kinds
    # Dates, bare number runs and ordinary words are never facts.
    assert all(key not in ("20190301", "100200300", "3") for _, _, key in facts)


def test_raster_dimensions_reads_headers_without_decoding_pixels():
    assert raster_dimensions(png_header(800, 600)) == ("png", 800, 600)
    assert raster_dimensions(b"GIF89a" + struct.pack("<HH", 10, 20) + b"\x00" * 10) == ("gif", 10, 20)
    jpeg = (b"\xff\xd8\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
            + b"\xff\xc0" + struct.pack(">HBHH", 17, 8, 480, 640) + b"\x00" * 20)
    assert raster_dimensions(jpeg) == ("jpeg", 640, 480)
    webp = b"RIFF" + b"\x00" * 4 + b"WEBPVP8X" + b"\x00" * 8 + (799).to_bytes(3, "little") + (599).to_bytes(3, "little")
    assert raster_dimensions(webp) == ("webp", 800, 600)
    assert raster_dimensions(b"\x89PNG\r\n") is None
    assert raster_dimensions(b"not an image at all") is None


def test_svg_text_reads_text_and_refuses_entities():
    status, text = svg_text(b'<svg xmlns="http://www.w3.org/2000/svg"><text>Plan <tspan>$49</tspan> '
                            b'per month</text><title>ignored</title></svg>')
    assert status == "ok" and text == "Plan $49 per month"
    assert svg_text(b'<!DOCTYPE svg [<!ENTITY x "boom">]><svg><text>&x;</text></svg>')[0] == "unsupported"
    assert svg_text(b"<svg><text>unterminated")[0] == "malformed"
    assert svg_text(b"<html></html>")[0] == "not_svg"


def test_image_keywords_exclude_interface_images():
    assert fact_keywords(image_tokens(SITE + "/img/Price-List_2024.png", None, None)) == ("price",)
    assert fact_keywords(image_tokens(SITE + "/img/opening-hours.jpg", "Opening hours", None))
    assert fact_keywords(image_tokens(SITE + "/img/menu-icon.svg", None, None)) == ()
    assert fact_keywords(image_tokens(SITE + "/img/hero.jpg", "Our team", None)) == ()


def test_html_image_records_are_absolute_and_skip_data_uris():
    p = page('<img src="/a/price.png" alt="Price list"><img data-src="b.jpg">'
             '<img src="data:image/png;base64,AA"><div hidden><img src="/hidden.png"></div>',
             url=SITE + "/menu/")
    srcs = [r["src"] for r in p.features["image_records"]]
    assert srcs == [SITE + "/a/price.png", SITE + "/menu/b.jpg"]


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def test_pdf_text_simple_font_with_escapes_and_tj_arrays():
    pdf = build_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>",
        pdf_stream(b"", b"BT /F1 12 Tf (Price list \\(2026\\)) Tj 0 -14 Td [(Widget) -250 ($49.99)] TJ "
                        b"T* (Call +1 555-123-4567) Tj ET"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ])
    result = extract_pdf_text(pdf)
    assert result["status"] == "ok" and result["pages"] == 1
    assert result["text"] == "Price list (2026)\nWidget $49.99\nCall +1 555-123-4567"


def test_pdf_text_keeps_split_blocks_on_one_line_and_words_whole():
    pdf = build_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        pdf_stream(b"", b"BT /F1 9 Tf 72 700 Td (Price) Tj ET BT /F1 9 Tf 120 700 Td ($1,299) Tj ET "
                        b"BT /F1 9 Tf 1 0 0 1 72 680 Tm (Hel) Tj (lo) Tj ET"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ])
    assert extract_pdf_text(pdf)["text"] == "Price $1,299\nHello"


def test_pdf_text_cid_font_uses_tounicode_cmap():
    cmap = (b"begincmap 1 begincodespacerange <0000> <FFFF> endcodespacerange "
            b"2 beginbfchar <0001> <0048> <0002> <0069> endbfchar "
            b"1 beginbfrange <0010> <0012> <0041> endbfrange endcmap")
    def cid_pdf(font_extra):
        return build_pdf([
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /C0 5 0 R >> >> /Contents [4 0 R] >>",
            pdf_stream(b"", b"BT /C0 10 Tf <00010002> Tj T* <001000110012> Tj ET"),
            b"<< /Type /Font /Subtype /Type0 /BaseFont /X /Encoding /Identity-H" + font_extra + b" >>",
            pdf_stream(b"", cmap),
        ])
    result = extract_pdf_text(cid_pdf(b" /ToUnicode 6 0 R"))
    assert result["status"] == "ok" and result["text"] == "Hi\nABC"
    # Without a ToUnicode map the glyph codes cannot be mapped: never guessed.
    assert extract_pdf_text(cid_pdf(b""))["status"] == "unsupported"


def test_pdf_text_reads_objects_inside_object_streams():
    page_obj = b"<< /Type /Page /Parent 2 0 R /Contents 4 0 R /Resources << /Font << /F1 6 0 R >> >> >>"
    font_obj = b"<< /Type /Font /Subtype /Type1 >>"
    header = b"3 0 6 %d " % (len(page_obj) + 1)
    body = header + page_obj + b" " + font_obj
    pdf = build_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"null",
        pdf_stream(b"", b"BT /F1 9 Tf (Spec sheet 500 W 2.5 kg) Tj ET"),
        pdf_stream(b"/Type /ObjStm /N 2 /First %d" % len(header), body),
    ]).replace(b"3 0 obj\nnull\nendobj\n", b"")
    result = extract_pdf_text(pdf)
    assert result["status"] == "ok" and result["text"] == "Spec sheet 500 W 2.5 kg"


def test_pdf_text_statuses_for_unreadable_inputs():
    scan = extract_pdf_text(image_only_pdf())
    assert scan["status"] == "no_text_layer" and scan["has_images"] and scan["text"] == ""
    assert extract_pdf_text(b"%PDF-1.4\n1 0 obj << /Encrypt 2 0 R >> endobj")["status"] == "encrypted"
    assert extract_pdf_text(b"<html>not a pdf</html>")["status"] == "not_pdf"
    assert extract_pdf_text(b"%PDF-1.4 garbage \x00\xff obj << [[[[")["status"] == "malformed"
    deep = build_pdf([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] >>",
                      b"<< /Type /Page /Contents 4 0 R >>", pdf_stream(b"", b"BT " + b"[" * 5000 + b" ET")])
    assert extract_pdf_text(deep)["status"] == "unsupported"
    # A truncated download that yields no text is a limitation, not proof of a scan.
    truncated = text_pdf(b"hello")[:60]
    assert extract_pdf_text(truncated, truncated=True)["status"] != "no_text_layer"


def test_pdf_text_is_bounded_against_hostile_input():
    bomb = build_pdf([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] >>",
                      b"<< /Type /Page /Contents 4 0 R >>", pdf_stream(b"", b"\x00" * 200_000_000)])
    start = time.monotonic()
    assert extract_pdf_text(bomb)["status"] in ("no_text_layer", "unsupported")
    assert time.monotonic() - start < 3

    busy = build_pdf([b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] >>",
                      b"<< /Type /Page /Contents 4 0 R >>",
                      pdf_stream(b"", b"BT " + b"1 0 0 1 0 0 cm " * 400_000 + b"ET")])
    start = time.monotonic()
    result = extract_pdf_text(busy, time_budget_s=0.5)
    assert time.monotonic() - start < 2.5
    assert result["time_limited"] and result["status"] == "unsupported"


# ---------------------------------------------------------------------------
# analyze_non_text rules
# ---------------------------------------------------------------------------

PRICING = SITE + "/pricing"


def _pricing(body="<p>See our plans below.</p>", jsonld=""):
    return page("<html><head><title>Pricing</title>" + jsonld + "</head><body><h1>Pricing</h1>"
                + body + "</body></html>", url=PRICING)


def test_svg_text_only_facts_are_confirmed():
    entry = image(SITE + "/img/rates.svg", [PRICING], kind="svg", svg_status="ok",
                  svg_text="Basic $19.99 Pro $49.99 call +1 555-010-2000")
    result = analyze_non_text(snapshot([_pricing()], media([entry])), DEADLINE())
    [finding] = checks(result, "facts-in-images")
    assert finding["status"] == "confirmed" and finding["severity"] == "medium"
    assert finding["finding_type"] == "defect" and finding["affected_pages"] == [PRICING]
    assert "$19.99" in finding["evidence"][0]["description"]


@pytest.mark.parametrize("body,jsonld", [
    ("<p>Basic $19.99 and Pro $49.99. Call +1 555-010-2000.</p>", ""),
    ("<p>Plans below.</p>", '<script type="application/ld+json">{"@type":"Product","name":"Basic",'
                            '"offers":[{"@type":"Offer","price":"19.99"},{"@type":"Offer","price":"49.99"}],'
                            '"telephone":"+1 555-010-2000"}</script>'),
])
def test_svg_facts_already_in_text_or_jsonld_are_not_reported(body, jsonld):
    entry = image(SITE + "/img/rates.svg", [PRICING], kind="svg", svg_status="ok",
                  svg_text="Basic $19.99 Pro $49.99 call +1 555-010-2000")
    result = analyze_non_text(snapshot([_pricing(body, jsonld)], media([entry])), DEADLINE())
    assert not checks(result, "facts-in-images")


def test_raster_image_named_as_price_list_is_suspected_low():
    entry = image(SITE + "/img/price-list.png", [PRICING], alt="Price list", width=1200, height=900)
    result = analyze_non_text(snapshot([_pricing()], media([entry])), DEADLINE())
    [finding] = checks(result, "facts-in-images")
    assert finding["status"] == "suspected" and finding["severity"] == "low"
    assert finding["finding_type"] == "proactive_improvement"
    assert "were not read" in finding["evidence"][0]["description"]


@pytest.mark.parametrize("extra,body", [
    ({"width": 64, "height": 64}, "<p>Plans below.</p>"),                     # too small to hold facts
    ({"alt": "Price list: Basic 19.99"}, "<p>Plans below.</p>"),              # fact already in alt text
    ({}, "<p>Basic $19 Pro $29 Team $99 per month.</p>"),                     # prices already in text
])
def test_raster_candidates_are_not_reported_when_mitigated(extra, body):
    entry = image(SITE + "/img/price-list.png", [PRICING], **extra)
    result = analyze_non_text(snapshot([_pricing(body)], media([entry])), DEADLINE())
    assert not checks(result, "facts-in-images")


def test_pdf_only_facts_confirmed_on_complete_crawl_and_stepped_down_otherwise():
    doc = {"url": SITE + "/docs/specs.pdf", "linked_from": [SITE + "/"], "fetch_status": "ok",
           "extraction": "ok", "text": "Model H500 output 4500 W weight 12.5 kg price $1,299.00", "pages": 1}
    home = page("<html><body><h1>Heaters</h1><p>Industrial heaters.</p></body></html>")
    [complete] = checks(analyze_non_text(snapshot([home], media(pdfs=[doc])), DEADLINE()), "pdf-only-facts")
    assert complete["status"] == "confirmed" and complete["severity"] == "medium"
    assert "$1,299.00" in complete["evidence"][0]["description"]
    [partial] = checks(analyze_non_text(snapshot([home], media(pdfs=[doc]), discovered=4), DEADLINE()),
                       "pdf-only-facts")
    assert partial["status"] == "suspected" and partial["severity"] == "low"
    assert partial["confidence"] < complete["confidence"]


def test_pdf_facts_stated_in_html_or_single_fact_are_not_reported():
    doc = {"url": SITE + "/docs/specs.pdf", "linked_from": [SITE + "/"], "fetch_status": "ok",
           "extraction": "ok", "text": "Model H500 output 4500 W price $1,299.00"}
    home = page("<html><body><p>The H500 delivers 4500 W and costs $1,299.</p></body></html>")
    assert not checks(analyze_non_text(snapshot([home], media(pdfs=[doc])), DEADLINE()), "pdf-only-facts")
    single = dict(doc, text="Price $1,299.00")
    bare = page("<html><body><p>Heaters.</p></body></html>")
    assert not checks(analyze_non_text(snapshot([bare], media(pdfs=[single])), DEADLINE()), "pdf-only-facts")


def test_image_only_pdf_is_reported_and_unreadable_pdf_is_only_a_warning():
    home = page("<html><body><p>Brochures.</p></body></html>")
    scan = {"url": SITE + "/docs/scan.pdf", "linked_from": [SITE + "/"], "fetch_status": "ok",
            "extraction": "no_text_layer", "has_images": True, "pages": 2}
    locked = {"url": SITE + "/docs/locked.pdf", "linked_from": [SITE + "/"], "fetch_status": "ok",
              "extraction": "encrypted"}
    result = analyze_non_text(snapshot([home], media(pdfs=[scan, locked])), DEADLINE())
    [finding] = checks(result, "pdf-image-only")
    assert finding["status"] == "confirmed" and SITE + "/docs/scan.pdf" in finding["evidence"][0]["description"]
    assert not checks(result, "pdf-only-facts")
    assert any("locked.pdf" in w and "encrypted" in w for w in result["warnings"])
    assert result["metrics"]["pdfs_unreadable"] == 1


def test_snapshot_without_media_reports_nothing():
    result = analyze_non_text(snapshot([page("<html><body>x</body></html>")]), DEADLINE())
    assert result["findings"] == [] and result["metrics"]["non_text_media_assessed"] is False


# ---------------------------------------------------------------------------
# Agent vision stage (AG-04)
# ---------------------------------------------------------------------------

def test_ag04_is_ingested_as_facts_in_images_and_merges_with_script_finding(tmp_path, monkeypatch):
    path = tmp_path / "agent.json"
    path.write_text(json.dumps([{"check": "AG-04", "affected_pages": [PRICING],
                                 "evidence": "The price-list image shows Basic $19 and Pro $29; "
                                             "the page text states no prices."}]), encoding="utf-8")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    artifacts = snapshot([_pricing()], media([image(SITE + "/img/price-list.png", [PRICING])]))
    agent = ingest_agent_findings(artifacts, None, DEADLINE())
    [vision] = agent["findings"]
    assert vision["check_id"] == "facts-in-images" and vision["status"] == "suspected"
    assert vision["root_cause"] == get_entry("facts-in-images")["mechanism"]
    assert vision["affected_pages"] == [PRICING]
    script = analyze_non_text(artifacts, DEADLINE())
    merged = [f for f in merge_findings([script, agent]) if f["check_id"] == "facts-in-images"]
    assert len(merged) == 1 and merged[0]['status'] == 'suspected'
    assert sum(len(f["evidence"]) for f in merged) == 2


# ---------------------------------------------------------------------------
# Full audit against the media fixture
# ---------------------------------------------------------------------------

def _media_audit():
    seen = []
    url, stop = start_server(media=True, requests_seen=seen)
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    return report, seen


def test_media_fixture_audit_finds_locked_facts_and_respects_guardrails():
    report, seen = _media_audit()
    by_check = {}
    for f in report["findings"]:
        by_check.setdefault(f["check_id"], []).append(f)
    images = by_check["facts-in-images"]
    assert any(f["status"] == "confirmed" for f in images)
    evidence = " ".join(e["description"] for f in images for e in f["evidence"])
    assert "rates.svg" in evidence and "$19.99" in evidence and "price-list.png" in evidence
    assert "1200x900" in evidence
    assert "specs.pdf" in by_check["pdf-only-facts"][0]["evidence"][0]["description"]
    assert "scan.pdf" in by_check["pdf-image-only"][0]["evidence"][0]["description"]
    # Guardrails: robots-disallowed PDF, decorative logo and cross-origin image never requested.
    assert "/private/secret.pdf" not in seen and "/img/logo.svg" not in seen
    assert not any("cdn.example.test" in p for p in seen)
    assert seen.count("/docs/specs.pdf") == 1 and seen.count("/img/rates.svg") == 1
    media_cov = report["coverage"]["non_text_media"]
    assert media_cov["pdfs_discovered"] == 3 and media_cov["pdfs_fetch_attempted"] == 2
    assert media_cov["svg_text_read"] == 1 and media_cov["pdfs_text_extracted"] == 1
    assert any("AG-04" in line for line in report["limitations"])
    assert any("linked PDF(s) were not fetched" in line for line in report["limitations"])
    assert report["execution_status"] == "completed"
    assert all(f["check_id"] in CATALOG for f in report["findings"])


def test_media_fetch_caps_are_enforced():
    seen = []
    url, stop = start_server(media=True, requests_seen=seen)
    try:
        limits = Limits(MAX_IMAGE_FETCHES=1, MAX_PDF_FETCHES=1)
        artifacts = acquire_site(url + "/", make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop()
    image_requests = [p for p in seen if p.startswith("/img/")]
    pdf_requests = [p for p in seen if p.endswith(".pdf")]
    assert len(image_requests) == 1 and len(pdf_requests) == 1
    assert artifacts.media_data["summary"]["image_fetches_attempted"] == 1


def test_clean_fixture_raises_no_non_text_or_structured_date_findings():
    url, stop = start_server(clean=True)
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    flagged = {f["check_id"] for f in report["findings"]} & {
        "facts-in-images", "pdf-only-facts", "pdf-image-only", "structured-date-invalid"}
    assert not flagged


# ---------------------------------------------------------------------------
# Structured dates in freshness
# ---------------------------------------------------------------------------

def _article(date_published=None, date_modified=None, body="<p>Article text.</p>", url=SITE + "/blog/post"):
    data = {"@context": "https://schema.org", "@type": "Article", "headline": "Post"}
    if date_published is not None:
        data["datePublished"] = date_published
    if date_modified is not None:
        data["dateModified"] = date_modified
    return page('<html><head><script type="application/ld+json">' + json.dumps(data)
                + "</script></head><body>" + body + "</body></html>", url=url)


NO_FACTS = intermediate_artifact("important_facts", data={"facts": []})
OLD = f"{NOW_YEAR - 6}-02-01"
RECENT = f"{NOW_YEAR}-01-15"


def test_old_jsonld_date_modified_is_assessed_as_stale():
    result = assess_freshness(NO_FACTS, snapshot([_article(OLD, OLD)]), DEADLINE())
    [finding] = [f for f in result["findings"] if f["check_id"] == "stale-dates:editorial"]
    assert "JSON-LD dateModified " + OLD in finding["evidence"][0]["description"]
    assert result["metrics"]["structured_date_facts"] == 1


def test_recent_date_modified_outweighs_old_date_published():
    result = assess_freshness(NO_FACTS, snapshot([_article(OLD, RECENT)]), DEADLINE())
    assert result["status"] == "success" and not result["findings"]


def test_recent_structured_update_supersedes_old_editorial_text_dates_only():
    claims = intermediate_artifact("claims", data={"claims": [
        {"source": SITE + "/blog/post", "predicate": "mentions_date", "value": OLD, "type": "date",
         "category": "editorial"},
        {"source": SITE + "/product", "predicate": "mentions_date", "value": OLD, "type": "date",
         "category": "commercial"},
    ]})
    result = assess_freshness(NO_FACTS, snapshot([_article(RECENT, RECENT)]), DEADLINE(), claims)
    assert result["metrics"]["text_dates_superseded_by_structured_update"] == 1
    assert {f["check_id"] for f in result["findings"]} == {"stale-dates:commercial"}


def test_product_node_dates_are_commercial():
    product = page('<html><head><script type="application/ld+json">{"@type":"Product","name":"W",'
                   '"dateModified":"' + OLD + '"}</script></head><body></body></html>', url=SITE + "/w")
    claims, issues = structured_date_claims([product])
    assert claims[0]["category"] == "commercial" and not issues


def test_invalid_structured_dates_are_reported():
    future = (datetime.now(timezone.utc) + timedelta(days=40)).date().isoformat()
    pages = [_article("2026-99-99", None, url=SITE + "/a"),
             _article(future, None, url=SITE + "/b"),
             _article(RECENT, f"{NOW_YEAR - 1}-01-01", url=SITE + "/c")]
    result = assess_freshness(NO_FACTS, snapshot(pages), DEADLINE())
    [finding] = [f for f in result["findings"] if f["check_id"] == "structured-date-invalid"]
    text = " ".join(e["description"] for e in finding["evidence"])
    assert "impossible calendar date" in text and "in the future" in text and "earlier than datePublished" in text
    assert finding["severity"] == "low" and finding["status"] == "confirmed"


def test_all_text_dates_are_assessed_even_when_ranking_drops_them():
    # identify_important_facts keeps the top 20 claims and dates rank lowest; the
    # claims artifact passed by run_audit makes freshness see every text date.
    ranked = intermediate_artifact("important_facts", data={"facts": [
        {"source": SITE + "/", "predicate": "telephone", "value": "+1 555", "type": "structured",
         "category": "contact"}] * 20})
    claims = intermediate_artifact("claims", data={"claims": [
        {"source": SITE + "/product", "predicate": "mentions_date", "value": v, "type": "date",
         "category": "commercial"} for v in (OLD, f"{NOW_YEAR - 5}-03-01", f"{NOW_YEAR - 7}-09-09")]})
    artifacts = snapshot([page("<html><body>x</body></html>")])
    assert assess_freshness(ranked, artifacts, DEADLINE())["status"] == "insufficient_evidence"
    with_claims = assess_freshness(ranked, artifacts, DEADLINE(), claims)
    [finding] = with_claims["findings"]
    assert finding["check_id"] == "stale-dates:commercial" and finding["severity"] == "high"


def test_new_check_ids_are_catalogued():
    for check_id in ("facts-in-images", "pdf-only-facts", "pdf-image-only", "structured-date-invalid"):
        assert all(get_entry(check_id)[k] for k in ("mechanism", "implementation_detail", "expected_outcome"))
