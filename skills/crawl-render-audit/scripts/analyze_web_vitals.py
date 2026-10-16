"""analyze_web_vitals.py -- Core Web Vitals: measured when possible, estimated otherwise.

Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS) and Interaction to
Next Paint (INP) can only be measured in a browser. Two tiers:

  - Field data (optional): with PAGESPEED_API_KEY set, common/field_vitals.py
    fetches the Chrome UX Report 75th percentiles for the audited URL (or its
    origin) at audit start. A metric rated "needs improvement" or "poor" is
    cwv-field-poor, a confirmed defect measured from real users.
  - Static estimate (always): markup patterns known to hurt each metric, read
    from the acquisition snapshot. A page is listed for a metric when it shows one
    strong pattern or two moderate ones. These are cwv-risk suggestions, labelled
    as estimates; nothing is measured. When field data rates a metric "good", its
    estimate is not reported, because the measurement outranks the guess.

Patterns (strong / moderate):
  LCP: HTML slower than 3 s to arrive (strong); HTML slower than 1.8 s
       (moderate); first content image lazy-loaded (moderate, because some
       frameworks lazy-load every image in the HTML and make the first one eager
       in the browser); 8 or more render-blocking scripts and stylesheets in the
       head (moderate); HTML over 500 KB (moderate).
  CLS: video or iframe embeds without reserved size (moderate); most images
       without width and height (moderate); otherwise, the first content image
       without width and height (moderate).
  INP: over 300 KB of inline script (strong); 60 or more external scripts
       (strong); over 100 KB of inline script (moderate); 30 or more external
       scripts (moderate); scripts from 10 or more third-party hosts (moderate).
"""
from field_vitals import THRESHOLDS, UNITS
from check_catalog import calibrated_confidence
from check_helpers import eligible_pages
from models import make_finding, skill_result
from platforms import host_of

_NAMES = {"LCP": "Largest Contentful Paint", "CLS": "Cumulative Layout Shift", "INP": "Interaction to Next Paint"}
_ROOT_CAUSE = {
    "LCP": "Markup patterns that delay the largest paint were observed: the main content may appear slowly",
    "CLS": "Markup patterns that let content move during loading were observed: layout may shift",
    "INP": "Markup patterns that load heavy JavaScript were observed: the page may respond slowly to input",
}
_STEPS = {
    "LCP": ["Do not lazy-load the first large image; give it fetchpriority=\"high\" or preload it",
            "Defer or async non-critical scripts and inline only critical CSS",
            "Reduce server response time with caching"],
    "CLS": ["Give every image, video and iframe width and height attributes or a CSS aspect-ratio",
            "Reserve space for embeds, banners and late-loading content"],
    "INP": ["Remove unused scripts and third-party tags",
            "Split long JavaScript tasks and defer work that is not needed for the first interaction",
            "Move large inline scripts to cached external files loaded with defer"],
}


def _int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def page_factors(page, site_host):
    """{metric: (strong, moderate)} lists of observed patterns for one page."""
    f = page.features or {}
    lcp_s, lcp_m, cls_m, inp_s, inp_m = [], [], [], [], []
    image = f.get("lcp_image") or {}
    if image.get("loading") == "lazy":
        lcp_m.append("the first content image is lazy-loaded in the HTML")
    duration = f.get("network_duration_ms")
    if isinstance(duration, (int, float)) and duration > 1800:
        (lcp_s if duration > 3000 else lcp_m).append(f"the HTML took {int(duration)} ms to arrive")
    blocking = (f.get("head_blocking_scripts") or 0) + (f.get("blocking_stylesheets") or 0)
    if blocking >= 8:
        lcp_m.append(f"{blocking} render-blocking scripts and stylesheets in the head")
    if (f.get("html_bytes") or 0) > 500_000:
        lcp_m.append(f"{f['html_bytes'] // 1024} KB of HTML")
    if (f.get("embeds_missing_dims") or 0) >= 1:
        cls_m.append(f"{f['embeds_missing_dims']} video or iframe embed(s) without reserved size")
    images, missing = f.get("images") or 0, f.get("images_missing_dims") or 0
    if images >= 5 and missing >= 5 and missing / images >= 0.5:
        cls_m.append(f"{missing} of {images} images without width and height")
    elif image and not (_int(image.get("width")) and _int(image.get("height"))):
        # Counted only when the pattern above did not already cover this image.
        cls_m.append("the first content image has no width and height")
    inline = f.get("inline_script_bytes") or 0
    external = f.get("external_scripts") or 0
    if inline > 300_000:
        inp_s.append(f"{inline // 1024} KB of inline script")
    elif inline > 100_000:
        inp_m.append(f"{inline // 1024} KB of inline script")
    if external >= 60:
        inp_s.append(f"{external} external scripts")
    elif external >= 30:
        inp_m.append(f"{external} external scripts")
    third = [h for h in f.get("script_hosts", ()) if site_host and not (
        h == site_host or h.endswith("." + site_host) or site_host.endswith("." + h))]
    if len(third) >= 10:
        inp_m.append(f"scripts from {len(third)} third-party hosts")
    return {"LCP": (lcp_s, lcp_m), "CLS": ([], cls_m), "INP": (inp_s, inp_m)}


def _format(metric, value):
    if metric == "CLS":
        return f"{value:.2f}"
    return f"{value / 1000:.1f} s" if value >= 1000 else f"{int(value)} ms"


def _field_finding(field, site_url):
    bad = {m: v for m, v in field["metrics"].items() if v["rating"] != "good"}
    if not bad:
        return None
    severity = "medium" if any(v["rating"] == "poor" for v in bad.values()) else "low"
    scope = "this URL" if field.get("scope") == "url" else "the whole origin"
    return make_finding(
        category="engagement", finding_type="defect", severity=severity, status="confirmed", confidence=0.9,
        title="Real users experience slow or unstable pages (Core Web Vitals field data)",
        root_cause="Chrome UX Report data from real visitors rates one or more Core Web Vitals below 'good', "
                   "so pages load slowly, shift or respond late for many visitors",
        evidence=[{"type": "web_vitals_field",
                   "description": f"{_NAMES[m]} ({m}) 75th percentile is {_format(m, v['p75'])}, rated "
                                  f"{v['rating'].replace('_', ' ')} (good is {_format(m, THRESHOLDS[m][0])} or "
                                  f"less), from Chrome UX Report field data for {scope}",
                   "urls": [site_url]} for m, v in bad.items()],
        affected_pages=[site_url],
        suggested_action={
            "summary": "Fix the Core Web Vitals rated below good, starting with the worst",
            "steps": [step for m in bad for step in _STEPS[m][:2]],
            "priority": severity, "effort": "medium",
            "expected_benefit": "Faster, steadier pages for visitors who arrive from search and AI answers",
            "verification": "Check the PageSpeed Insights field data again after 28 days of traffic"},
        provenance={"skill": "crawl-render-audit", "script": "analyze_web_vitals.py", "rule_id": "cwv-field-poor"},
    )


def analyze_web_vitals(artifacts, deadline, field_handle=None):
    field = None
    if field_handle is not None:
        field = field_handle.result(timeout=min(20.0, max(0.0, deadline.remaining_seconds() - 25.0)))
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Core Web Vitals checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    site_host = host_of(artifacts.site_url) or host_of(artifacts.normalized_origin)
    measured = field.get("metrics", {}) if field and field.get("status") == "ok" else {}
    findings = []
    if measured:
        finding = _field_finding(field, artifacts.site_url)
        if finding:
            findings.append(finding)

    flagged = {m: [] for m in _NAMES}
    for page in pages:
        for metric, (strong, moderate) in page_factors(page, site_host).items():
            if strong or len(moderate) >= 2:
                flagged[metric].append((page, strong + moderate))
    suppressed = []
    for metric, hits in flagged.items():
        if not hits:
            continue
        if measured.get(metric, {}).get("rating") == "good":
            suppressed.append(metric)
            continue
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=calibrated_confidence("cwv-risk", 0.5),
            title=f"Likely {_NAMES[metric]} ({metric}) risk, estimated from markup and not measured",
            root_cause=_ROOT_CAUSE[metric],
            affected_pages=[p.url for p, _ in hits],
            evidence=[{"type": "web_vitals_estimate",
                       "description": "Estimate, not a measurement: " + "; ".join(reasons[:4]),
                       "urls": [page.url]} for page, reasons in hits[:10]],
            suggested_action={
                "summary": f"Check {metric} in a browser or with field data, and remove the listed patterns",
                "steps": _STEPS[metric] + ["Confirm with PageSpeed Insights or the Chrome UX Report"],
                "priority": "low", "effort": "medium",
                "expected_benefit": f"Lower risk of a poor {_NAMES[metric]} score",
                "verification": "Measure the page with PageSpeed Insights and re-run the audit"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_web_vitals.py", "rule_id": "cwv-risk"},
        ))
    mode = ("field_data" if measured else "static_estimate")
    metrics = {"web_vitals_mode": mode, "web_vitals_pages_estimated": len(pages),
               "web_vitals_estimate_pages": {m: len(h) for m, h in flagged.items()},
               "web_vitals_estimates_suppressed_by_field_data": suppressed,
               "web_vitals_field_lookup": (field or {}).get("status", "not_configured")}
    if measured:
        metrics["web_vitals_field_scope"] = field.get("scope")
        metrics["web_vitals_field"] = {m: {"p75": v["p75"], "unit": UNITS[m], "rating": v["rating"]}
                                       for m, v in measured.items()}
    return skill_result("crawl-render-audit", findings=findings, metrics=metrics,
                        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                                  "queries_attempted": 1 if field_handle is not None else 0,
                                  "queries_completed": 1 if measured else 0})
