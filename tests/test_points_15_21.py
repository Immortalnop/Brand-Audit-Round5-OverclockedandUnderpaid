"""Points 15 to 21: hreflang, <noscript> fallback, canvas/SVG/icon-font text,
image captions and context, image weight, accessibility beyond alt text, and
overlays and consent banners.

Unit tests build pages from HTML strings and never touch the network; the
end-to-end tests run against the local fixture server only.
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
from html_features import Document, parse_color, contrast_ratio
from acquire_site import _extract_page, _total_size, _probe_image_weight
from analyze_international import analyze_international, code_problem
from analyze_rendering import analyze_rendering
from analyze_graphics_text import analyze_graphics_text
from analyze_image_context import analyze_image_context
from analyze_image_weight import analyze_image_weight, image_problems
from analyze_accessibility import analyze_accessibility
from analyze_overlays import analyze_overlays
from check_catalog import CATALOG
from capabilities import CHECK_TIERS
from run_audit import run_audit
from fixtures_server import start_server

LIMITS = Limits()
SITE = "https://fixture.example"
NEW_IDS = {"hreflang-invalid", "hreflang-missing", "canvas-text", "svg-inline-facts", "icon-font-text",
           "image-context-missing", "image-weight", "responsive-images", "form-label-missing",
           "control-name-missing", "low-contrast-text", "tap-target-small", "consent-text-leak"}


def page(body="", head="", url=SITE + "/", lang="en", status=200, headers=None):
    lang_attr = f' lang="{lang}"' if lang else ""
    html = f"<html{lang_attr}><head>{head}</head><body>{body}</body></html>"
    response = Response(status, {"Content-Type": "text/html", **(headers or {})}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def snapshot(*pages, sitemap=None, robots=None, meta=None, media=None):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value(robots or {"status": "ok"}),
                          freeze_value({"present": False, "status": "absent"}),
                          freeze_value(sitemap or {"status": "ok"}),
                          freeze_value({"coverage": coverage, **(meta or {})}), (), media_data=freeze_value(media)
                          if media is not None else None)


def run(check, *pages, **kw):
    return check(snapshot(*pages, **kw), make_deadline(LIMITS))


def ids(result):
    return {f["check_id"] for f in result["findings"]}


def by_id(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


def text_of(finding):
    return " ".join(e["description"] for e in finding["evidence"])


def features(html):
    doc = Document()
    doc.feed(html)
    doc.close()
    return doc, doc.features()


LONG = "<p>" + "Plain content sentence about the service and what it offers to customers. " * 12 + "</p>"


# ------------------------------------------------------------- catalog wiring

def test_every_new_check_is_catalogued_and_tiered():
    assert NEW_IDS <= set(CATALOG)
    for key in ("hreflang_annotations", "noscript_fallback", "canvas_svg_icon_font_text", "image_caption_context",
                "image_weight_measurement", "accessibility_html_checks", "overlay_and_consent_detection"):
        assert CHECK_TIERS[key] == "executable"


# ------------------------------------------------------------- 15: hreflang

@pytest.mark.parametrize("code,fragment", [
    ("en", None), ("en-GB", None), ("pt-BR", None), ("zh-Hant", None), ("zh-Hant-TW", None),
    ("x-default", None), ("EN-gb", None), ("fil", None), ("uk", None),
    ("en_US", "underscore"), ("en-UK", "GB"), ("jp", "country code"), ("cn-zh", "country code"),
    ("es-419", "numeric region"), ("english", "not a language code"), ("", "empty"), ("en-GB-x", "not a language"),
])
def test_hreflang_code_validation(code, fragment):
    problem = code_problem(code)
    assert (problem is None) if fragment is None else (fragment in problem)


def _alt(code, href):
    return f'<link rel="alternate" hreflang="{code}" href="{href}">'


def test_reciprocal_hreflang_cluster_is_quiet():
    en = page(LONG, _alt("en", SITE + "/") + _alt("de", SITE + "/de/") + _alt("x-default", SITE + "/"))
    de = page(LONG, _alt("en", SITE + "/") + _alt("de", SITE + "/de/"), url=SITE + "/de/", lang="de")
    result = run(analyze_international, en, de)
    assert result["findings"] == [] and result["metrics"]["hreflang_pages"] == 2


def test_missing_return_link_and_bad_codes_are_a_medium_defect():
    en = page(LONG, _alt("en", SITE + "/") + _alt("de", SITE + "/de/") + _alt("en_US", SITE + "/us/"))
    de = page(LONG, _alt("de", SITE + "/de/"), url=SITE + "/de/", lang="de")
    finding = by_id(run(analyze_international, en, de), "hreflang-invalid")[0]
    text = text_of(finding)
    assert finding["severity"] == "medium" and finding["status"] == "confirmed" and finding["finding_type"] == "defect"
    assert "does not link back" in text and "underscore" in text
    assert finding["affected_pages"] == [SITE + "/"]


def test_relative_url_and_missing_self_reference_are_low():
    en = page(LONG, _alt("de", "/de/"))
    finding = by_id(run(analyze_international, en), "hreflang-invalid")[0]
    assert finding["severity"] == "low"
    assert "not a full URL" in text_of(finding) and "does not list itself" in text_of(finding)


def test_broken_alternate_and_lang_mismatch_are_reported():
    en = page(LONG, _alt("de", SITE + "/") + _alt("fr", SITE + "/fr/"))
    gone = page("<p>gone</p>", url=SITE + "/fr/", status=404)
    text = text_of(by_id(run(analyze_international, en, gone), "hreflang-invalid")[0])
    assert "answered HTTP 404" in text and "differs from html lang 'en'" in text


def test_link_header_annotations_are_read():
    header = f'<{SITE}/>; rel="alternate"; hreflang="en", <{SITE}/de/>; rel="alternate"; hreflang="de"'
    en = page(LONG, headers={"Link": header})
    result = run(analyze_international, en)
    assert result["metrics"]["hreflang_annotations"] == 2
    assert result["metrics"]["hreflang_alternates_unverified"] == 1 and not result["findings"]


def test_multilingual_site_without_hreflang_is_suspected_but_sitemap_annotations_count():
    en, de = page(LONG), page(LONG, url=SITE + "/de/", lang="de")
    missing = by_id(run(analyze_international, en, de), "hreflang-missing")[0]
    assert missing["status"] == "suspected" and missing["severity"] == "low"
    sitemap = {"status": "ok", "hreflang": {SITE + "/": [{"hreflang": "en", "href": SITE + "/"},
                                                        {"hreflang": "de", "href": SITE + "/de/"}],
                                            SITE + "/de/": [{"hreflang": "en", "href": SITE + "/"},
                                                            {"hreflang": "de", "href": SITE + "/de/"}]}}
    assert run(analyze_international, en, de, sitemap=sitemap)["findings"] == []


def test_single_language_site_raises_nothing():
    assert run(analyze_international, page(LONG), page(LONG, url=SITE + "/about"))["findings"] == []


def test_sitemap_hreflang_is_collected_at_acquisition():
    from xml.etree import ElementTree as ET
    from acquire_site import _collect_sitemap_hreflang
    xml = ("<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>"
           f"<url><loc>{SITE}/</loc><xhtml:link rel='alternate' hreflang='de' href='{SITE}/de/'/></url>"
           f"<url><loc>{SITE}/plain</loc></url></urlset>")
    out = {}
    _collect_sitemap_hreflang(ET.fromstring(xml), SITE, out)
    assert out == {SITE + "/": [{"hreflang": "de", "href": SITE + "/de/"}]}


# ------------------------------------------------------------- 16: noscript

def _gap(*pages):
    return analyze_rendering(snapshot(*pages), make_deadline(LIMITS), LIMITS, {"headless_rendering": False})


def test_noscript_js_required_shell_is_a_gap_with_raised_confidence():
    shell = page('<noscript>You need to enable JavaScript to run this app.</noscript><div id="root"></div>',
                 url=SITE + "/app")
    finding = by_id(_gap(shell), "render-gap")[0]
    assert finding["confidence"] == 0.75 and "JavaScript is required" in text_of(finding)
    assert _gap(shell)["metrics"]["noscript_js_required_pages"] == 1


def test_noscript_boilerplate_no_longer_counts_as_content():
    # 'other' pages need 200 characters; 150 real characters plus noscript boilerplate
    # used to pass the threshold.
    real = "x" * 150
    p = page(f"<p>{real}</p><noscript>This site requires JavaScript. Please turn on JavaScript in your "
             "browser settings and reload.</noscript>", url=SITE + "/thin")
    assert len(p.visible_text) >= 200
    assert SITE + "/thin" in _gap(p)["metrics"]["raw_rendered_gap_pages"]


def test_real_noscript_fallback_is_not_a_gap():
    fallback = "Our full catalogue of espresso machine parts with prices and delivery times. " * 6
    p = page(f'<noscript><p>{fallback}</p></noscript><div id="root"></div>', url=SITE + "/catalogue")
    result = _gap(p)
    assert result["findings"] == [] and result["metrics"]["noscript_fallback_pages"] == [SITE + "/catalogue"]


def test_page_without_noscript_keeps_the_old_behaviour():
    assert _gap(page("<p>tiny</p>", url=SITE + "/t"))["metrics"]["raw_rendered_gap_pages"] == [SITE + "/t"]
    assert _gap(page(LONG, url=SITE + "/ok"))["findings"] == []


# ------------------------------------------- 17: canvas, inline SVG, icon fonts

def test_canvas_without_text_alternative_is_suspected():
    result = run(analyze_graphics_text, page(LONG + '<canvas width="600" height="300"></canvas>'))
    assert by_id(result, "canvas-text")[0]["status"] == "suspected"


@pytest.mark.parametrize("canvas", [
    '<canvas width="600" height="300">Monthly sales: January 120 units, February 140 units</canvas>',
    '<canvas width="600" height="300" aria-label="Monthly sales chart"></canvas>',
    '<canvas width="600" height="300"><img src="/chart.png" alt="Sales chart"></canvas>',
    '<canvas width="40" height="40"></canvas>',
    '<canvas width="600" height="300" aria-hidden="true"></canvas>',
    '<canvas width="600" height="300" role="presentation"></canvas>',
])
def test_canvas_with_alternative_or_decorative_is_quiet(canvas):
    assert "canvas-text" not in ids(run(analyze_graphics_text, page(LONG + canvas)))


def test_fact_only_in_inline_svg_is_reported_and_repeated_fact_is_not():
    svg = '<svg><text x="0" y="10">Plan $29 per month</text><text><tspan>call +1 555-222-3333</tspan></text></svg>'
    finding = by_id(run(analyze_graphics_text, page(LONG + svg)), "svg-inline-facts")[0]
    assert "$29" in text_of(finding) and "555-222-3333" in text_of(finding)
    repeated = page(LONG + svg + "<p>The plan costs $29 per month; call +1 555-222-3333.</p>")
    assert "svg-inline-facts" not in ids(run(analyze_graphics_text, repeated))


def test_icon_font_glyphs_and_ligatures_leak_but_hidden_icons_do_not():
    glyph = page(LONG + '<a href="/c"><i class="icon-phone"></i> Call</a>')
    assert "glyph" in text_of(by_id(run(analyze_graphics_text, glyph), "icon-font-text")[0])
    hidden = page(LONG + '<a href="/c"><i class="icon-phone" aria-hidden="true"></i> Call</a>')
    assert "icon-font-text" not in ids(run(analyze_graphics_text, hidden))
    lig = page(LONG + "".join(f'<span class="material-icons">{n}</span>' for n in ("menu", "search", "shopping_cart")))
    assert "shopping_cart" in text_of(by_id(run(analyze_graphics_text, lig), "icon-font-text")[0])


def test_svg_title_is_not_the_document_title():
    doc, _ = features('<html><head><title>Real title</title></head><body>'
                      '<a href="/"><svg><title>Home icon</title></svg></a></body></html>')
    assert "".join(doc.title_parts) == "Real title"


# ------------------------------------------------- 18: captions and context

def _context(img, wrapper="main"):
    return run(analyze_image_context, page(f"<{wrapper}>{LONG}{img}</{wrapper}>"))


def test_content_image_with_no_text_context_is_suspected():
    finding = by_id(_context('<img src="/img/workshop.jpg" width="800" height="600">'), "image-context-missing")[0]
    assert finding["status"] == "suspected" and "/img/workshop.jpg" in text_of(finding)


@pytest.mark.parametrize("img", [
    '<figure><img src="/img/w.jpg" width="800" height="600"><figcaption>Our Leeds workshop</figcaption></figure>',
    '<img src="/img/w.jpg" width="800" height="600" alt="Technician descaling a machine">',
    '<img src="/img/w.jpg" width="800" height="600" alt="">',
    '<a href="/team"><img src="/img/w.jpg" width="800" height="600"> Meet the team</a>',
    '<img src="/img/w.jpg" width="800" height="600" title="Workshop">',
    '<img src="/img/w.jpg" width="800" height="600" aria-label="Workshop">',
    '<img src="/img/company-logo.png" width="300" height="100">',
    '<img src="/img/w.jpg" width="32" height="32">',
    '<img src="/img/w.jpg" role="presentation" width="800" height="600">',
])
def test_image_with_context_or_decorative_is_quiet(img):
    assert "image-context-missing" not in ids(_context(img))


def test_images_in_page_chrome_are_skipped():
    assert "image-context-missing" not in ids(_context('<img src="/img/w.jpg" width="800" height="600">', "header"))


def test_caption_is_recorded_on_the_image_record():
    records = page('<figure><img src="/a.jpg"><figcaption>Front of the shop</figcaption></figure>'
                   ).features["image_records"]
    assert records[0]["caption"] == "Front of the shop"


# ------------------------------------------------------------ 19: image weight

def _entry(**kw):
    base = {"url": SITE + "/img/a.jpg", "pages": [SITE + "/"], "fetch_status": "ok", "kind": "raster"}
    base.update(kw)
    return base


@pytest.mark.parametrize("entry,severity,fragment", [
    (_entry(bytes_total=1_200_000), "medium", "1.1 MB"),
    (_entry(bytes_total=600_000, lcp=True), "medium", "586 KB"),
    (_entry(bytes_total=350_000), "low", "342 KB"),
    (_entry(width=2400, width_attr=600, bytes_total=90_000), "low", "displayed at 600 px"),
    (_entry(width=2400, width_attr=600, responsive=True, bytes_total=90_000), None, None),
    (_entry(bytes_total=150_000, content_type="image/png", accept_sent=True), None, "served as PNG"),
    (_entry(bytes_total=150_000, content_type="image/webp", accept_sent=True), None, None),
    (_entry(bytes_total=40_000, width=800, width_attr=800), None, None),
])
def test_image_problems(entry, severity, fragment):
    problems, sev = image_problems(entry)
    assert sev == severity
    assert (fragment is None and not problems) or (fragment is not None and fragment in "; ".join(problems))


def test_image_weight_finding_from_media_data():
    media = {"images": [_entry(bytes_total=1_200_000, lcp=True)], "summary": {"image_weight_probes": 1}}
    finding = by_id(run(analyze_image_weight, page(LONG), media=media), "image-weight")[0]
    assert finding["severity"] == "medium" and finding["finding_type"] == "defect" and finding["category"] == "engagement"
    legacy = {"images": [_entry(bytes_total=150_000, content_type="image/jpeg", accept_sent=True)], "summary": {}}
    only_format = by_id(run(analyze_image_weight, page(LONG), media=legacy), "image-weight")[0]
    assert only_format["finding_type"] == "proactive_improvement" and only_format["severity"] == "low"


def test_responsive_images_markup_check():
    plain = page('<main><img src="/hero.jpg" alt="Hero shot of the cafe"></main>')
    assert "responsive-images" in ids(run(analyze_image_weight, plain))
    for img in ('<img src="/hero.jpg" srcset="/hero-2x.jpg 2x" alt="Hero">',
                '<picture><source srcset="/hero.avif" type="image/avif"><img src="/hero.jpg" alt="Hero"></picture>',
                '<img src="/hero.svg" alt="Hero">', '<img src="/img/python-logo.png" alt="Python">'):
        assert "responsive-images" not in ids(run(analyze_image_weight, page(f"<main>{img}</main>")))


def test_total_size_from_range_and_length_headers():
    ranged = Response(206, {"Content-Range": "bytes 0-32767/512000"}, b"x" * 10, SITE + "/a.jpg")
    full = Response(200, {"Content-Length": "4096"}, b"x" * 10, SITE + "/a.jpg", truncated=True)
    whole = Response(200, {}, b"x" * 10, SITE + "/a.jpg")
    cut = Response(200, {}, b"x" * 10, SITE + "/a.jpg", truncated=True)
    assert [_total_size(r) for r in (ranged, full, whole, cut)] == [512000, 4096, 10, None]


class _FakeTransport:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def get(self, url, **kw):
        self.calls.append((url, kw))
        return self.responses.get(url, (None, "failed"))


def test_image_weight_probe_sends_range_and_modern_accept():
    png = b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + (1600).to_bytes(4, "big") + (900).to_bytes(4, "big") + b"\0" * 10
    resp = Response(206, {"Content-Type": "image/png", "Content-Range": "bytes 0-32767/700000"}, png, SITE + "/a.png")
    tr = _FakeTransport({SITE + "/a.png": (resp, "ok")})
    entry = {"url": SITE + "/a.png", "kind": "raster"}
    _probe_image_weight(tr, entry, LIMITS)
    headers = tr.calls[0][1]["headers"]
    assert headers["Range"] == "bytes=0-32767" and "image/avif" in headers["Accept"]
    assert entry["bytes_total"] == 700000 and (entry["width"], entry["height"]) == (1600, 900)
    assert entry["accept_sent"] and entry["content_type"] == "image/png"


# ------------------------------------------------------- 20: accessibility

def test_unlabeled_fields_are_a_defect_and_labelled_ones_are_not():
    form = ('<form><label for="e">Email</label><input id="e" type="email">'
            '<label>Name <input name="n"></label><input aria-label="Search" name="q">'
            '<input name="phone"><textarea name="msg"></textarea><select name="topic"></select>'
            '<input name="city" placeholder="City"><input type="hidden" name="t"><input type="submit"></form>')
    result = run(analyze_accessibility, page(LONG + form))
    finding = by_id(result, "form-label-missing")[0]
    assert finding["severity"] == "medium" and "name=phone" in text_of(finding) and "name=msg" in text_of(finding)
    assert result["metrics"]["accessibility_unlabeled_fields"] == 3
    assert result["metrics"]["accessibility_placeholder_only_fields"] == 1
    single = by_id(run(analyze_accessibility, page(LONG + '<input type="email" name="e">')), "form-label-missing")[0]
    assert single["severity"] == "low"


def test_icon_only_controls_have_no_name():
    controls = ('<a href="/x" class="fa fa-twitter"></a><button><i class="icon-close"></i></button>'
                '<a href="/cart"><svg><title>Cart</title></svg></a><a href="/y" aria-label="Search"><i></i></a>'
                '<a href="/z"><img src="/l.png" alt="Home"></a><a href="/w">Words</a>'
                '<input type="image" src="/go.png">')
    result = run(analyze_accessibility, page(LONG + controls))
    finding = by_id(result, "control-name-missing")[0]
    assert finding["severity"] == "medium" and result["metrics"]["accessibility_unnamed_controls"] == 3


def test_inline_contrast():
    low = page(LONG + '<p style="color:#999;background:#fff">Light text</p>')
    finding = by_id(run(analyze_accessibility, low), "low-contrast-text")[0]
    assert "2.85:1" in text_of(finding) and "Only inline styles" in text_of(finding)
    for style in ("color:#000;background-color:#fff",
                  "color:#949494;background:#fff;font-size:24px",
                  "color:#999;background:linear-gradient(#fff,#eee)",
                  "color:rgba(0,0,0,0.5);background:#fff",
                  "color:#999"):
        assert "low-contrast-text" not in ids(run(analyze_accessibility, page(LONG + f'<p style="{style}">Text</p>')))


@pytest.mark.parametrize("value,expected", [
    ("#fff", (255, 255, 255)), ("#000000", (0, 0, 0)), ("rgb(255, 0, 0)", (255, 0, 0)),
    ("rgb(0 128 0)", (0, 128, 0)), ("rgba(0,0,255,1)", (0, 0, 255)), ("white", (255, 255, 255)),
    ("rgba(0,0,0,.5)", None), ("#ffffff80", None), ("var(--x)", None), ("transparent", None), ("inherit", None),
])
def test_parse_color(value, expected):
    assert parse_color(value) == expected


def test_contrast_ratio_extremes():
    assert round(contrast_ratio((0, 0, 0), (255, 255, 255)), 1) == 21.0
    assert contrast_ratio((10, 10, 10), (10, 10, 10)) == 1.0


def test_small_inline_target_is_suspected():
    result = run(analyze_accessibility, page(LONG + '<a href="/i" style="width:16px;height:16px">i</a>'))
    assert by_id(result, "tap-target-small")[0]["status"] == "suspected"
    big = page(LONG + '<a href="/i" style="width:44px;height:44px">i</a>')
    assert "tap-target-small" not in ids(run(analyze_accessibility, big))


# ------------------------------------------------------ 21: overlays, consent

def test_blocking_consent_dialog_with_scroll_lock_is_medium():
    html = (LONG + '<div id="onetrust-banner-sdk" role="dialog" aria-modal="true">We use cookies. '
            'Accept all cookies</div>')
    # Scroll lock counts only on <html> or <body>, not on an inner element.
    body_locked = _extract_page(SITE + "/", Response(200, {"Content-Type": "text/html"},
                                f'<html lang="en"><body style="overflow:hidden">{html}</body></html>'.encode(),
                                SITE + "/"), 50, LIMITS)
    inner_locked = page('<div style="overflow:hidden">' + html + "</div>")
    finding = by_id(run(analyze_overlays, body_locked), "overlay")[0]
    assert finding["severity"] == "medium" and finding["status"] == "suspected"
    assert "cookie consent prompt" in text_of(finding) and "onetrust" in text_of(finding)
    assert inner_locked.features["scroll_lock"] is False
    assert by_id(run(analyze_overlays, inner_locked), "overlay")[0]["severity"] == "low"


def test_non_blocking_consent_banner_is_not_an_overlay():
    banner = page(LONG + '<div class="cookie-banner">We use cookies. <button>OK</button></div>')
    result = run(analyze_overlays, banner)
    assert "overlay" not in ids(result) and result["metrics"]["consent_platform_pages"] == 1


def test_full_screen_fixed_layer_and_class_only_overlay():
    fixed = page(LONG + '<div style="position:fixed;inset:0;z-index:999">Subscribe to our newsletter</div>')
    assert "overlay" in ids(run(analyze_overlays, fixed))
    weak = page(LONG + '<div class="newsletter-popup">Join</div>')
    finding = by_id(run(analyze_overlays, weak), "overlay")[0]
    assert finding["severity"] == "low" and "no blocking dialog observed" in text_of(finding)


def test_cookie_text_in_meta_description_is_a_confirmed_defect():
    leak = page(LONG, head='<meta name="description" content="This website uses cookies to improve your experience.">')
    finding = by_id(run(analyze_overlays, leak), "consent-text-leak")[0]
    assert finding["status"] == "confirmed" and finding["severity"] == "medium" and "meta description" in text_of(finding)


def test_cookie_text_opening_the_page_is_suspected():
    opening = page('<div>We use cookies to give you the best experience. Accept all cookies.</div>' + LONG)
    finding = by_id(run(analyze_overlays, opening), "consent-text-leak")[0]
    assert finding["status"] == "suspected" and finding["severity"] == "low"
    assert "consent-text-leak" not in ids(run(analyze_overlays, page(LONG + "<p>Read our cookie policy.</p>")))


def test_cookie_policy_page_and_cookie_links_are_not_leaks():
    policy = page(LONG, head='<meta name="description" content="This website uses cookies. Read how we use them.">',
                  url=SITE + "/cookie-policy")
    assert "consent-text-leak" not in ids(run(analyze_overlays, policy))
    nav = page('<nav><a href="/c">Cookie settings</a> <a href="/p">Cookie policy</a></nav>' + LONG)
    assert "consent-text-leak" not in ids(run(analyze_overlays, nav))


def test_bootstrap_style_hidden_modal_is_not_an_overlay():
    hidden = page(LONG + '<div class="modal fade" role="dialog" aria-modal="true" aria-hidden="true">Sign in</div>')
    assert "overlay" not in ids(run(analyze_overlays, hidden))


# ------------------------------------------------------------ end to end

def _extras_audit():
    seen = []
    url, stop = start_server(extras=True, requests_seen=seen)
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    return report, seen


def test_extras_fixture_audit_reports_points_15_to_21():
    report, seen = _extras_audit()
    found = {f["check_id"]: f for f in report["findings"]}
    expected = {"hreflang-invalid", "render-gap", "canvas-text", "svg-inline-facts", "image-context-missing",
                "image-weight", "form-label-missing", "control-name-missing", "low-contrast-text",
                "tap-target-small", "overlay", "consent-text-leak"}
    assert expected <= set(found), sorted(expected - set(found))
    assert "does not link back" in text_of(found["hreflang-invalid"])
    assert any("JavaScript is required" in e["description"] for e in found["render-gap"]["evidence"])
    weight = text_of(found["image-weight"])
    # 391 KB: heavy (300 KB or more) but under the 500 KB bar for a likely-LCP image to be medium.
    assert "team-photo.jpg" in weight and "391 KB" in weight and "displayed at 800 px" in weight
    assert "served as PNG" in weight and found["image-weight"]["severity"] == "low"
    assert found["overlay"]["severity"] == "medium"
    assert found["consent-text-leak"]["status"] == "confirmed"
    # Guardrails: one verification probe, the photo once, the logo never, nothing off the fixture host.
    assert seen.count("/img/team-photo.jpg") == 1 and "/BingSiteAuth.xml" not in seen
    assert "/img/logo.png" not in seen
    cov = report["coverage"]
    assert cov["image_weight"]["image_weight_measured"] == 1
    assert cov["hreflang"]["hreflang_pages"] == 2 and cov["accessibility"]["accessibility_unnamed_controls"] >= 1
    assert any("inline styles" in line for line in report["limitations"])
    assert report["execution_status"] == "completed"
    assert report["coverage"]["runtime_seconds"] < 60
    assert all(f["check_id"] in CATALOG for f in report["findings"] + report["recommendations"])


def test_clean_fixture_does_not_trip_points_15_to_21():
    url, stop = start_server(clean=True)
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    tripped = {f["check_id"] for f in report["findings"]} & (NEW_IDS | {"overlay"})
    assert not tripped, sorted(tripped)


def test_new_checks_respect_expired_deadline():
    expired = SimpleNamespace(expired=lambda: True)
    a = snapshot(page(LONG))
    for check in (analyze_international, analyze_graphics_text, analyze_image_context, analyze_image_weight,
                  analyze_accessibility, analyze_overlays):
        result = check(a, expired)
        assert result["status"] == "insufficient_evidence" and not result["findings"]


def test_no_em_dash_in_new_files():
    for rel in ("skills/crawl-render-audit/scripts/analyze_international.py",
                "skills/crawl-render-audit/scripts/analyze_graphics_text.py",
                "skills/crawl-render-audit/scripts/analyze_image_context.py",
                "skills/crawl-render-audit/scripts/analyze_image_weight.py",
                "skills/engagement-audit/scripts/analyze_accessibility.py",
                "skills/engagement-audit/scripts/analyze_overlays.py",
                "common/html_features.py", "tests/test_points_15_21.py"):
        assert chr(0x2014) not in (ROOT / rel).read_text(encoding="utf-8"), rel
