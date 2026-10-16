"""analyze_image_weight.py -- image file size, format and responsive variants.

Heavy images slow the largest paint and waste mobile data, so visitors arriving
from an answer wait or leave. Two tiers:

  - image-weight (measured): acquisition reads the first bytes of up to 4 of
    the largest same-origin content images with a Range GET that accepts AVIF and
    WebP like a browser does (common/constants.py MAX_IMAGE_WEIGHT_PROBES). From
    the response it learns the full file size, the served format and the pixel
    size. Reported: files of 300 KB or more; images at least twice as wide as the
    width they are displayed at, with no srcset; and 100 KB or larger files still
    served as JPEG, PNG or GIF to a client that accepts AVIF and WebP.
  - responsive-images (markup, suspected): the likely largest image of a page
    (the first content image) has neither srcset nor a <picture> source, so every
    screen downloads the same file.

Cross-origin images (CDNs) are never requested; they get only the markup check.
"""
from check_catalog import calibrated_confidence
from check_helpers import eligible_pages
from models import make_finding, skill_result
from non_text import image_tokens, is_excluded_image

_HEAVY = 300_000
_VERY_HEAVY = 1_000_000
_LCP_HEAVY = 500_000
_LEGACY = {"image/jpeg": "JPEG", "image/jpg": "JPEG", "image/png": "PNG", "image/gif": "GIF",
           "image/bmp": "BMP", "image/tiff": "TIFF"}


def _kb(n):
    return f"{n / 1024:.0f} KB" if n < 1_000_000 else f"{n / 1_048_576:.1f} MB"


def image_problems(entry):
    """([problem, ...], severity) for one measured image entry."""
    problems, severity = [], None
    size = entry.get("bytes_total")
    if isinstance(size, int) and size >= _HEAVY:
        problems.append(f"the file is {_kb(size)}")
        severity = "medium" if size >= _VERY_HEAVY or (entry.get("lcp") and size >= _LCP_HEAVY) else "low"
    width, shown = entry.get("width"), entry.get("width_attr")
    if isinstance(width, int) and isinstance(shown, int) and shown > 0 and not entry.get("responsive") \
            and width >= 2 * shown and width - shown >= 400:
        problems.append(f"it is {width} px wide but displayed at {shown} px, with no srcset")
        severity = severity or "low"
    ctype = entry.get("content_type") or ""
    if entry.get("accept_sent") and ctype in _LEGACY and isinstance(size, int) and size >= 100_000:
        problems.append(f"it is served as {_LEGACY[ctype]} although the request accepted AVIF and WebP")
    return problems, severity


def _responsive_gaps(page):
    for record in (page.features or {}).get("image_records", ()):
        if not record.get("lcp"):
            continue
        src = (record.get("src") or "").split("?")[0].lower()
        if src.endswith(".svg") or record.get("srcset") or record.get("picture_types"):
            return None
        # A logo or icon picked as the first image is small and not the main image.
        if is_excluded_image(image_tokens(record.get("src") or "", record.get("alt"), record.get("title"))):
            return None
        return record
    return None


def analyze_image_weight(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Image weight checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    media = artifacts.media_data or {}
    measured, heavy = [], []
    for entry in media.get("images", ()):
        if entry.get("fetch_status") != "ok" or entry.get("kind") != "raster":
            continue
        measured.append(entry)
        problems, severity = image_problems(entry)
        if problems:
            heavy.append((entry, problems, severity))
    findings = []
    if heavy:
        defect = any(sev for _, _, sev in heavy)
        severity = "medium" if any(sev == "medium" for _, _, sev in heavy) else "low"
        findings.append(make_finding(
            category="engagement", finding_type="defect" if defect else "proactive_improvement",
            severity=severity, status="confirmed", confidence=0.9,
            title="Images are heavier than they need to be",
            root_cause="Large, oversized or legacy-format image files delay the largest paint and cost mobile "
                       "visitors data, so visitors arriving from search or an AI answer wait longer",
            affected_pages=sorted({u for e, _, _ in heavy for u in e.get("pages", ())}),
            evidence=[{"type": "image_weight",
                       "description": f"{e['url'][:150]}: " + "; ".join(problems)
                                      + (" (likely the largest image on the page)" if e.get("lcp") else ""),
                       "urls": list(e.get("pages", ()))[:5]} for e, problems, _ in heavy[:10]],
            suggested_action={
                "summary": "Compress, resize and convert the listed images",
                "steps": ["Serve AVIF or WebP, with JPEG or PNG only as a fallback in <picture>",
                          "Resize each image to the largest size it is displayed at and add srcset and sizes "
                          "for smaller screens",
                          "Compress photos, aiming for under 200 KB for the largest image of a page"],
                "priority": severity, "effort": "medium",
                "expected_benefit": "Faster largest paint and less data for visitors on mobile",
                "verification": "Re-run the audit and confirm the listed images are smaller"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_image_weight.py",
                        "rule_id": "image-weight"},
        ))
    gaps = [(p, r) for p in pages for r in [_responsive_gaps(p)] if r]
    if gaps:
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=calibrated_confidence("responsive-images", 0.55),
            title="The main image of a page has no responsive variants",
            root_cause="Without srcset or <picture> sources, phones download the same large file as desktops, "
                       "which delays the largest paint on mobile",
            affected_pages=[p.url for p, _ in gaps],
            evidence=[{"type": "responsive_images",
                       "description": f"First content image {(r.get('src') or '')[:150]} has no srcset and no "
                                      "<picture> source; actual file size was not measured unless listed "
                                      "under image-weight",
                       "urls": [p.url]} for p, r in gaps[:10]],
            suggested_action={
                "summary": "Add srcset and sizes to the main image of each page",
                "steps": ["Generate the image at several widths and list them in srcset with a sizes attribute",
                          "Use <picture> with AVIF or WebP sources where the format matters"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Each screen downloads an image no larger than it needs",
                "verification": "Re-run the audit and confirm the pages are no longer listed"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_image_weight.py",
                        "rule_id": "responsive-images"},
        ))
    summary = media.get("summary") or {}
    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"image_weight_measured": len(measured),
                 "image_weight_probes": summary.get("image_weight_probes", 0),
                 "image_weight_problems": len(heavy),
                 "image_weight_bytes_largest": max((e.get("bytes_total") or 0 for e in measured), default=0),
                 "responsive_image_gaps": len(gaps)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
