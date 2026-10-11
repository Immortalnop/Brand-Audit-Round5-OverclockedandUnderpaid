"""analyze_graphics_text.py -- text drawn by canvas, inline SVG and icon fonts.

Crawlers and assistants read text. Text that only exists as pixels or as a glyph
picked from an icon font is invisible or meaningless to them. This check reads the
acquisition snapshot only (no requests):

  - canvas-text (suggestion, suspected): a visible <canvas> of content size with
    no fallback text or image between its tags, no aria-label and no title.
    Whatever a script draws on it (chart values, prices, labels) is pixels only.
    A decorative canvas is not a problem, so this is a suspicion, not a defect.
  - svg-inline-facts (suggestion, suspected): prices, phone numbers or
    specifications written only inside an inline <svg> <text> element and
    nowhere else in the page text, alt text, meta description or JSON-LD. Some
    text extractors drop SVG, so those facts may be lost. Facts in SVG files
    referenced by <img> are the separate facts-in-images check.
  - icon-font-text (suggestion, confirmed): icon-font glyph characters
    (Unicode Private Use Area) or ligature icon names such as "shopping_cart"
    that are not hidden from assistive technology, so extracted text carries
    meaningless symbols or stray words.
"""
import json
import re
from collections import Counter

from check_helpers import eligible_pages
from models import make_finding, skill_result
from non_text import PHONE_RE, extract_facts, normalize_number, phone_digits

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _int(value):
    return int(value) if isinstance(value, str) and re.fullmatch(r"[0-9]{1,6}", value.strip()) else None


def _numbers(text):
    return Counter(normalize_number(m.group(0)) for m in _NUMBER.finditer(text or ""))


def _phones(text):
    return Counter(d for m in PHONE_RE.finditer(text or "") for d in [phone_digits(m.group(0))] if d)


def _other_texts(page):
    """Readable channels other than the body text: title, description, alt, JSON-LD."""
    features = page.features or {}
    texts = [page.title or "", page.meta_description or ""]
    texts.extend(r.get("alt") or "" for r in features.get("image_records", ()))
    for block in page.jsonld_blocks:
        try:
            texts.append(json.dumps(block, default=lambda v: dict(v.items()) if hasattr(v, "items")
                                    else list(v) if isinstance(v, tuple) else str(v), ensure_ascii=False))
        except (TypeError, ValueError):
            continue
    return " ".join(texts)


def svg_only_facts(page):
    """Facts in inline SVG text that appear in no other readable channel."""
    svg = (page.features or {}).get("inline_svg_text") or ""
    facts = extract_facts(svg)
    if not facts:
        return []
    body_n, svg_n = _numbers(page.visible_text), _numbers(svg)
    body_p, svg_p = _phones(page.visible_text), _phones(svg)
    other = _other_texts(page)
    other_n, other_p = _numbers(other), _phones(other)
    missing = []
    for kind, shown, key in facts:
        if kind == "phone":
            present = body_p[key] > svg_p[key] or other_p[key] > 0
        else:
            present = body_n[key] > svg_n[key] or other_n[key] > 0
        if not present:
            missing.append(shown)
    return missing


def _bare_canvases(page):
    out = []
    for c in (page.features or {}).get("canvases", ()):
        if c.get("label") or c.get("fallback_alt") or (c.get("fallback_chars") or 0) >= 20:
            continue
        if (c.get("role") or "") in ("presentation", "none"):
            continue
        w, h = _int(c.get("width")), _int(c.get("height"))
        if (w is not None and w < 100) or (h is not None and h < 50):
            continue
        out.append(c)
    return out


def _action(summary, steps):
    return {"summary": summary, "steps": steps, "priority": "low", "effort": "low",
            "expected_benefit": "Facts and labels become readable text for crawlers, assistants and screen readers",
            "verification": "Re-run the audit and confirm the affected pages are no longer listed"}


def analyze_graphics_text(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Canvas, inline SVG and icon-font checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    canvas_pages, svg_pages, icon_pages = [], [], []
    for page in pages:
        f = page.features or {}
        bare = _bare_canvases(page)
        if bare:
            canvas_pages.append((page, bare))
        missing = svg_only_facts(page)
        if missing:
            svg_pages.append((page, missing))
        glyphs, ligatures = f.get("pua_chars") or 0, list(f.get("icon_ligatures") or ())
        if glyphs or len(ligatures) >= 3:
            icon_pages.append((page, glyphs, list(f.get("pua_samples") or ()), ligatures))

    findings = []
    if canvas_pages:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.55,
            title="Canvas graphics have no text alternative",
            root_cause="Anything a script draws on a <canvas> exists only as pixels; without fallback text or an "
                       "aria-label, crawlers and assistants cannot read chart values, prices or labels drawn there",
            affected_pages=[p.url for p, _ in canvas_pages],
            evidence=[{"type": "canvas",
                       "description": f"{len(bare)} visible <canvas> element(s) with no fallback content, "
                                      "aria-label or title"
                                      + (f" (first is {bare[0]['width']}x{bare[0]['height']} px)"
                                         if bare[0].get("width") and bare[0].get("height") else ""),
                       "urls": [p.url]} for p, bare in canvas_pages[:10]],
            suggested_action=_action(
                "State what each canvas shows as text",
                ["Put a text summary or data table of the chart between the <canvas> tags or next to it",
                 "Give informative canvases role=\"img\" and an aria-label",
                 "Mark purely decorative canvases aria-hidden=\"true\""]),
            provenance={"skill": "crawl-render-audit", "script": "analyze_graphics_text.py",
                        "rule_id": "canvas-text"},
        ))
    if svg_pages:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.6,
            title="Facts appear only inside inline SVG graphics",
            root_cause="Some crawlers and text extractors drop <svg> content, so prices, phone numbers or "
                       "specifications that exist only as SVG text may never reach an assistant",
            affected_pages=[p.url for p, _ in svg_pages],
            evidence=[{"type": "svg_text",
                       "description": "Only in inline SVG text: " + ", ".join(missing[:6]),
                       "urls": [p.url]} for p, missing in svg_pages[:10]],
            suggested_action=_action(
                "Repeat the facts drawn in inline SVG as HTML text",
                ["Write the values shown in the graphic as text near it",
                 "Give the SVG role=\"img\" and a <title> that summarises it"]),
            provenance={"skill": "crawl-render-audit", "script": "analyze_graphics_text.py",
                        "rule_id": "svg-inline-facts"},
        ))
    if icon_pages:
        def describe(glyphs, samples, ligatures):
            parts = []
            if glyphs:
                parts.append(f"{glyphs} icon-font glyph character(s) in the text, in "
                             + ", ".join(samples[:3] or ["unknown elements"]))
            if len(ligatures) >= 3:
                parts.append("ligature icon names read as words: " + ", ".join(ligatures[:5]))
            return "; ".join(parts)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.8,
            title="Icon-font characters leak into the page text",
            root_cause="Icon fonts draw icons from private-use characters or words; when the icon is not hidden "
                       "from assistive technology, extracted text carries meaningless symbols or stray words",
            affected_pages=[p.url for p, *_ in icon_pages],
            evidence=[{"type": "icon_font", "description": describe(glyphs, samples, ligatures), "urls": [p.url]}
                      for p, glyphs, samples, ligatures in icon_pages[:10]],
            suggested_action=_action(
                "Hide icon-font glyphs from text readers and label what they mean",
                ["Add aria-hidden=\"true\" to every decorative icon element",
                 "Give icon-only links and buttons a text label or aria-label",
                 "Prefer inline SVG icons with a <title> over icon fonts"]),
            provenance={"skill": "crawl-render-audit", "script": "analyze_graphics_text.py",
                        "rule_id": "icon-font-text"},
        ))
    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"canvases_observed": sum(len((p.features or {}).get("canvases", ())) for p in pages),
                 "canvas_pages_without_text": len(canvas_pages),
                 "inline_svg_fact_pages": len(svg_pages), "icon_font_pages": len(icon_pages)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
