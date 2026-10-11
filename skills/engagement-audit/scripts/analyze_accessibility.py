"""analyze_accessibility.py -- accessibility beyond alt text, from the HTML alone.

Visitors who use screen readers, voice control or zoom, and AI agents that browse
and act on a page through its accessibility tree, all depend on labelled controls
and readable text. This check reads the acquisition snapshot only (no requests):

  - form-label-missing (defect, confirmed): visible form fields with no label
    element, aria-label, aria-labelledby, title or placeholder. Nothing names the
    field, so it cannot be filled in reliably. Fields named only by a
    placeholder are counted in the metrics, not reported.
  - control-name-missing (defect, confirmed): links and buttons with no text,
    no alt text on an image inside, no SVG title and no aria-label, typically
    icon-only controls. They are announced as "link" or "button" and nothing
    else.
  - low-contrast-text (defect, confirmed): text whose inline style sets both
    the colour and an opaque background, with a contrast ratio below WCAG AA
    (4.5:1, or 3:1 for large text).
  - tap-target-small (suggestion, suspected): links and buttons whose inline
    style makes them smaller than 24 by 24 CSS pixels (WCAG 2.2 target size).
    Spacing around them is not measured.

Colours and sizes set in stylesheets need a browser to compute, so only inline
styles are judged; the report states this as a limitation.
"""
from check_helpers import eligible_pages
from models import make_finding, skill_result


def _action(summary, steps, priority):
    return {"summary": summary, "steps": steps, "priority": priority, "effort": "low",
            "expected_benefit": "Visitors using assistive technology, and AI agents that act through the "
                                "accessibility tree, can identify and use the affected elements",
            "verification": "Re-run the audit and check the pages with a screen reader or an accessibility checker"}


def _field_label(f):
    name = f.get("name") or f.get("id")
    return f"<{f['tag']}{' type=' + f['type'] if f['tag'] == 'input' else ''}{' name=' + name if name else ''}>"


def _control_label(c):
    target = f" href={c['href'][:80]}" if c.get("href") else ""
    return f"<{c['tag']}{target}>" + (" with only an icon" if c.get("icon") else " with no content")


def analyze_accessibility(artifacts, deadline):
    if deadline.expired():
        return skill_result("engagement-audit", status="insufficient_evidence",
                            warnings=["Accessibility checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    fields, controls, contrast, targets = [], [], [], []
    totals = {"form_fields": 0, "placeholder_only": 0, "controls": 0, "contrast_checked": 0}
    for p in pages:
        f = p.features or {}
        totals["form_fields"] += f.get("form_fields") or 0
        totals["placeholder_only"] += f.get("placeholder_only_fields") or 0
        totals["controls"] += f.get("controls") or 0
        totals["contrast_checked"] += f.get("contrast_checked") or 0
        if f.get("unlabeled_field_count"):
            fields.append((p, f["unlabeled_field_count"], list(f.get("unlabeled_fields") or ())))
        if f.get("unnamed_control_count"):
            controls.append((p, f["unnamed_control_count"], list(f.get("unnamed_controls") or ())))
        if f.get("contrast_issues"):
            contrast.append((p, list(f["contrast_issues"])))
        if f.get("small_targets"):
            targets.append((p, list(f["small_targets"])))

    findings = []
    if fields:
        total = sum(n for _, n, _ in fields)
        severity = "medium" if total >= 3 else "low"
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity=severity, status="confirmed", confidence=0.85,
            title="Form fields have no label",
            root_cause="A field with no label, aria-label or title has no name in the accessibility tree, so "
                       "screen-reader users and AI agents filling the form cannot tell what it asks for",
            affected_pages=[p.url for p, _, _ in fields],
            evidence=[{"type": "form_labels",
                       "description": f"{n} unlabeled field(s): " + ", ".join(_field_label(x) for x in examples[:4]),
                       "urls": [p.url]} for p, n, examples in fields[:10]],
            suggested_action=_action(
                "Give every form field a visible label tied to it",
                ["Add <label for=\"field-id\"> with visible text for each field, or wrap the field in <label>",
                 "Use aria-label only where a visible label is impossible; a placeholder is not a label"],
                severity),
            provenance={"skill": "engagement-audit", "script": "analyze_accessibility.py",
                        "rule_id": "form-label-missing"},
        ))
    if controls:
        total = sum(n for _, n, _ in controls)
        severity = "medium" if total >= 3 else "low"
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity=severity, status="confirmed", confidence=0.85,
            title="Links or buttons have no accessible name",
            root_cause="A link or button with no text, no image alt text and no aria-label is announced only as "
                       "'link' or 'button', so screen-reader users and AI agents cannot tell where it leads",
            affected_pages=[p.url for p, _, _ in controls],
            evidence=[{"type": "control_names",
                       "description": f"{n} unnamed control(s): " + ", ".join(_control_label(c) for c in examples[:4]),
                       "urls": [p.url]} for p, n, examples in controls[:10]],
            suggested_action=_action(
                "Name every icon-only link and button",
                ["Add an aria-label that says what the control does, such as aria-label=\"Open cart\"",
                 "Or add visually hidden text inside the control",
                 "Mark the icon itself aria-hidden=\"true\""],
                severity),
            provenance={"skill": "engagement-audit", "script": "analyze_accessibility.py",
                        "rule_id": "control-name-missing"},
        ))
    if contrast:
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity="low", status="confirmed", confidence=0.9,
            title="Text colour has too little contrast with its background",
            root_cause="Text below the WCAG AA contrast ratio is hard to read for many visitors, especially on "
                       "phones in daylight and for people with low vision",
            affected_pages=[p.url for p, _ in contrast],
            evidence=[{"type": "contrast",
                       "description": "; ".join(f"\"{i['text']}\" {i['color']} on {i['background']} is "
                                                f"{i['ratio']}:1 (needs {i['required']}:1)" for i in issues[:3])
                                      + ". Only inline styles were checked.",
                       "urls": [p.url]} for p, issues in contrast[:10]],
            suggested_action=_action(
                "Darken the text or lighten the background until it reaches 4.5:1",
                ["Adjust the listed colour pairs to at least 4.5:1, or 3:1 for large text",
                 "Check the same colours where they are set in stylesheets"],
                "low"),
            provenance={"skill": "engagement-audit", "script": "analyze_accessibility.py",
                        "rule_id": "low-contrast-text"},
        ))
    if targets:
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low", status="suspected",
            confidence=0.5,
            title="Some links or buttons are smaller than 24 by 24 pixels",
            root_cause="Small tap targets are easy to miss on a touch screen; WCAG 2.2 asks for at least 24 by 24 "
                       "CSS pixels unless the target has enough space around it",
            affected_pages=[p.url for p, _ in targets],
            evidence=[{"type": "target_size",
                       "description": ", ".join(f"<{t['tag']}> {t['width']:g}x{t['height']:g} px" for t in items[:4])
                                      + " set by inline style; surrounding spacing not measured",
                       "urls": [p.url]} for p, items in targets[:10]],
            suggested_action=_action(
                "Make small controls at least 24 by 24 pixels, or space them apart",
                ["Increase the size or padding of each listed control",
                 "Keep at least 24 px between the centres of neighbouring small targets"],
                "low"),
            provenance={"skill": "engagement-audit", "script": "analyze_accessibility.py",
                        "rule_id": "tap-target-small"},
        ))
    return skill_result(
        "engagement-audit", findings=findings,
        metrics={"accessibility_pages_analyzed": len(pages),
                 "accessibility_form_fields": totals["form_fields"],
                 "accessibility_unlabeled_fields": sum(n for _, n, _ in fields),
                 "accessibility_placeholder_only_fields": totals["placeholder_only"],
                 "accessibility_controls": totals["controls"],
                 "accessibility_unnamed_controls": sum(n for _, n, _ in controls),
                 "accessibility_contrast_pairs_checked": totals["contrast_checked"],
                 "accessibility_stylesheet_styles_measured": False},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
