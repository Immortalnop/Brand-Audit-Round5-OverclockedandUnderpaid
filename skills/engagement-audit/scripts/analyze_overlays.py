"""analyze_overlays.py -- cookie banners, modals and other overlays.

A visitor arriving from an answer who first meets a blocking dialog may leave, and
consent-banner text that sits where the page summary should be can be quoted
instead of the page. Static HTML cannot show timing or what is on screen, so
overlay findings stay suspected. This check reads the acquisition snapshot only
(no requests). Signals, strongest first:

  - a dialog (role="dialog" or "alertdialog", or <dialog open>) marked
    aria-modal="true" in the delivered HTML;
  - an inline style that fixes an element over the whole viewport;
  - a scroll lock on <html> or <body> (overflow hidden, or classes such as
    modal-open);
  - consent-platform markup or scripts (OneTrust, Cookiebot, Didomi and others),
    which identify a dialog or banner as a consent prompt;
  - overlay class names (newsletter-popup, modal-backdrop, interstitial).

Reported:
  - overlay (suggestion, suspected): a blocking dialog or full-screen layer is
    in the HTML; medium when the page is also scroll-locked, so it most likely
    blocks the content on arrival. Overlay class names alone stay low. A
    non-blocking consent banner is legally required and never reported.
  - consent-text-leak: cookie-consent wording in the meta description, the
    og:description or the title (confirmed defect: this text is shown as the
    page summary), or at the very start of the page text (suspected: text
    extractors read it before the content).
"""
import re

from check_helpers import eligible_pages
from models import make_finding, skill_result
from platforms import is_consent_host

# Consent-prompt sentences only. Link labels such as "Cookie settings" or "Cookie
# policy" are ordinary navigation and do not count.
_COOKIE_TEXT = re.compile(
    r"\b(?:we|this (?:site|website)|our (?:site|website)) uses? cookies\b|\baccept (?:all )?cookies\b"
    r"|\bby (?:clicking|continuing|using)[^.]{0,60}\bcookies\b", re.I)
# A cookie or privacy policy page may describe itself with cookie wording.
_POLICY_PAGE = re.compile(r"cookie|privacy|gdpr|datenschutz|confidentialit", re.I)
_NEWSLETTER = re.compile(r"newsletter|subscribe|sign up|discount|% off|join our", re.I)


def consent_platform(page):
    f = page.features or {}
    hosts = [h for h in f.get("script_hosts", ()) if is_consent_host(h)]
    return list(f.get("consent_markup") or ()) + hosts


def overlay_signals(page):
    """(signals, blocking, kind) for one page."""
    f = page.features or {}
    signals, blocking = [], False
    dialogs = list(f.get("modal_dialogs") or ())
    modal = [d for d in dialogs if d.get("modal")]
    if modal:
        blocking = True
        signals.append(f"{len(modal)} aria-modal dialog(s) in the delivered HTML")
    if f.get("fullscreen_fixed"):
        blocking = True
        signals.append("an inline style fixes an element over the whole viewport")
    if f.get("scroll_lock"):
        signals.append("page scrolling is locked on <html> or <body>")
    if f.get("overlay_pattern"):
        signals.append("overlay class names such as modal-backdrop or newsletter-popup")
    platform = consent_platform(page)
    text = " ".join(d.get("text") or "" for d in dialogs)
    if any(d.get("consent") for d in dialogs) or _COOKIE_TEXT.search(text):
        kind = "cookie consent prompt"
    elif _NEWSLETTER.search(text):
        kind = "newsletter or promotion dialog"
    else:
        kind = "dialog or overlay"
    if platform:
        signals.append("consent platform: " + ", ".join(dict.fromkeys(platform[:4])))
    return signals, blocking, kind


def consent_leak(page):
    """('summary', where) when cookie wording is in the summary fields,
    ('opening', snippet) when it opens the page text, else None."""
    if _POLICY_PAGE.search(page.url or "") or _POLICY_PAGE.search(page.title or ""):
        return None
    meta = (page.features or {}).get("meta") or {}
    for label, values in (("meta description", [page.meta_description or ""]),
                          ("og:description", list(meta.get("og:description", ()))),
                          ("title", [page.title or ""])):
        for value in values:
            if _COOKIE_TEXT.search(value or ""):
                return "summary", label
    opening = (page.visible_text or "")[:300]
    m = _COOKIE_TEXT.search(opening)
    if m:
        return "opening", opening[max(0, m.start() - 40):m.end() + 40]
    return None


def analyze_overlays(artifacts, deadline):
    if deadline.expired():
        return skill_result("engagement-audit", status="insufficient_evidence",
                            warnings=["Overlay checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    blocking, weak, summary_leaks, opening_leaks = [], [], [], []
    consent_pages = 0
    for p in pages:
        signals, is_blocking, kind = overlay_signals(p)
        if consent_platform(p):
            consent_pages += 1
        if is_blocking:
            blocking.append((p, signals, kind, bool((p.features or {}).get("scroll_lock"))))
        elif (p.features or {}).get("overlay_pattern"):
            weak.append((p, signals))
        leak = consent_leak(p)
        if leak and leak[0] == "summary":
            summary_leaks.append((p, leak[1]))
        elif leak:
            opening_leaks.append((p, leak[1]))

    findings = []
    if blocking or weak:
        severity = "medium" if any(locked for *_, locked in blocking) else "low"
        evidence = [{"type": "overlay", "description": f"Likely {kind}: " + "; ".join(signals),
                     "urls": [p.url]} for p, signals, kind, _ in blocking[:10]]
        evidence += [{"type": "overlay", "description": "; ".join(signals) + "; no blocking dialog observed",
                      "urls": [p.url]} for p, signals in weak[:max(0, 10 - len(evidence))]]
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity=severity,
            status="suspected", confidence=0.65 if blocking else 0.5,
            title="A dialog or overlay may cover the content on arrival",
            root_cause="The delivered HTML contains a blocking dialog or full-screen layer"
                       + (" and locks page scrolling" if severity == "medium" else "")
                       + "; visitors arriving from an answer may meet it before the content. Timing and "
                         "visibility were not measured",
            affected_pages=[p.url for p, *_ in blocking] + [p.url for p, _ in weak],
            evidence=evidence,
            suggested_action={
                "summary": "Make sure arriving visitors reach the content before any optional dialog",
                "steps": ["Show cookie consent as a non-blocking banner where the law allows, not a full-screen wall",
                          "Delay newsletter or promotion dialogs until the visitor has engaged, and give each a "
                          "visible close control",
                          "Do not lock page scrolling unless a dialog really requires an answer"],
                "priority": severity, "effort": "low",
                "expected_benefit": "Visitors see the content they came for straight away",
                "verification": "Open the affected pages on a phone in a private window and check what appears first"},
            provenance={"skill": "engagement-audit", "script": "analyze_overlays.py", "rule_id": "overlay"},
        ))
    if summary_leaks:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="medium", status="confirmed",
            confidence=0.9,
            title="Cookie-consent text is used as the page summary",
            root_cause="The meta description, og:description or title holds cookie-consent wording, so search "
                       "results, link previews and assistants describe the page with the cookie notice",
            affected_pages=[p.url for p, _ in summary_leaks],
            evidence=[{"type": "consent_text", "description": f"Cookie-consent wording in the {where}",
                       "urls": [p.url]} for p, where in summary_leaks[:10]],
            suggested_action={
                "summary": "Write a real description and title for each affected page",
                "steps": ["Set a page-specific meta description and og:description that summarise the content",
                          "Fix the template or plugin that copies the first text on the page, the consent "
                          "banner, into the description"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Search results, previews and assistants describe the page itself",
                "verification": "Re-run the audit and confirm no description contains cookie wording"},
            provenance={"skill": "engagement-audit", "script": "analyze_overlays.py", "rule_id": "consent-text-leak"},
        ))
    elif opening_leaks:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.55,
            title="Cookie-consent text comes before the content in the page HTML",
            root_cause="Text extractors read the HTML in order, so a consent banner placed before the content is "
                       "read first and may be taken as the page's opening statement",
            affected_pages=[p.url for p, _ in opening_leaks],
            evidence=[{"type": "consent_text", "description": f"Page text opens with: \"{snippet.strip()}\"",
                       "urls": [p.url]} for p, snippet in opening_leaks[:10]],
            suggested_action={
                "summary": "Place the consent banner markup after the main content",
                "steps": ["Move the banner to the end of <body> or inject it with the consent script",
                          "Keep the page's own heading and summary first in the HTML"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Assistants and previews quote the page's own opening, not the cookie notice",
                "verification": "Re-run the audit and confirm the page text opens with its own content"},
            provenance={"skill": "engagement-audit", "script": "analyze_overlays.py", "rule_id": "consent-text-leak"},
        ))
    return skill_result(
        "engagement-audit", findings=findings,
        metrics={"overlay_pages_analyzed": len(pages), "overlay_blocking_pages": len(blocking),
                 "overlay_class_only_pages": len(weak), "consent_platform_pages": consent_pages,
                 "consent_text_summary_pages": len(summary_leaks), "consent_text_opening_pages": len(opening_leaks),
                 "overlay_timing_measured": False},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
