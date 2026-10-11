"""analyze_image_context.py -- does any text say what a content image shows?

An assistant that reads a page learns what an image shows from text tied to it:
alt text, a <figcaption>, a title or aria-label, or the text of the link the image
sits in. This check reads the acquisition snapshot only (no requests):

  - image-context-missing (suggestion, suspected): a content image (outside the
    header, navigation and footer, not tiny, not named as a logo or icon, not
    marked decorative with alt="" or role="presentation") whose alt text is
    missing or meaningless and that has no caption, title, aria-label or link
    text either. Nothing in the page says what it shows.

Images that do have a caption or link text but weak alt text are counted in the
metrics: the caption gives readers context, but alt text is still the
description screen readers announce, so alt-text-quality may still list them.
"""
import re

from analyze_media_text import junk_alt_reason
from check_helpers import eligible_pages
from models import make_finding, skill_result
from non_text import image_tokens, is_excluded_image


def _int(value):
    return int(value) if isinstance(value, str) and re.fullmatch(r"[0-9]{1,6}", value.strip()) else None


def _context(record):
    """Which text, other than alt, ties an image to its meaning."""
    for key, label in (("caption", "figcaption"), ("title", "title"), ("link_text", "link text")):
        if (record.get(key) or "").strip():
            return label
    return "aria-label" if record.get("aria_label") else None


def classify(record):
    """'skip', 'has_alt', 'context:<source>' or 'none' for one image record."""
    if (record.get("role") or "") in ("presentation", "none") or record.get("in_chrome"):
        return "skip"
    alt = record.get("alt")
    if isinstance(alt, str) and not alt.strip():
        return "skip"  # alt="" marks a decorative image
    w, h = _int(record.get("width")), _int(record.get("height"))
    dims = [d for d in (w, h) if d is not None]
    if dims and (min(dims) < 48 or max(dims) < 100):
        return "skip"
    src = record.get("src") or ""
    if is_excluded_image(image_tokens(src, alt, record.get("title"))):
        return "skip"
    if isinstance(alt, str) and not junk_alt_reason(alt, src):
        return "has_alt"
    source = _context(record)
    return "context:" + source if source else "none"


def analyze_image_context(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Image context checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    flagged, counts = [], {"content_images": 0, "with_alt": 0, "context_only": 0, "no_context": 0,
                           "with_caption": 0}
    for page in pages:
        bare = []
        for record in (page.features or {}).get("image_records", ()):
            if (record.get("caption") or "").strip():
                counts["with_caption"] += 1
            kind = classify(record)
            if kind == "skip":
                continue
            counts["content_images"] += 1
            if kind == "has_alt":
                counts["with_alt"] += 1
            elif kind == "none":
                counts["no_context"] += 1
                bare.append(record)
            else:
                counts["context_only"] += 1
        if bare:
            flagged.append((page, bare))
    findings = []
    if flagged:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.6,
            title="Content images have no alt text, caption or other text saying what they show",
            root_cause="Text-based crawlers, assistants and screen readers learn what an image shows only from "
                       "text tied to it; with no alt text, figcaption, title or link text, the image says nothing",
            affected_pages=[p.url for p, _ in flagged],
            evidence=[{"type": "image_context",
                       "description": f"{len(bare)} content image(s) with no usable alt text and no caption, "
                                      "title, aria-label or link text, for example "
                                      + ", ".join((r.get("src") or "")[:100] for r in bare[:3]),
                       "urls": [p.url]} for p, bare in flagged[:10]],
            suggested_action={
                "summary": "Describe each informative image in its alt text, and caption images that need context",
                "steps": ["Write a short alt text that says what each informative image shows",
                          "Wrap images that need explanation in <figure> with a <figcaption>",
                          "Mark purely decorative images with alt=\"\""],
                "priority": "low", "effort": "low",
                "expected_benefit": "Crawlers, assistants and screen readers can tell what each image shows",
                "verification": "Re-run the audit and confirm the affected pages are no longer listed"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_image_context.py",
                        "rule_id": "image-context-missing"},
        ))
    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"image_context_" + k: v for k, v in counts.items()},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
