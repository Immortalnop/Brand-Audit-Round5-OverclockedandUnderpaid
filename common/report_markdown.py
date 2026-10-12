"""report_markdown.py -- turns a finished JSON audit report into a Markdown report
a non-expert can read and act on (Plan.md point 12).

It reads the report and nothing else: no network, no re-crawl, no change to any
check. Run it on the JSON the audit printed:

    python common/report_markdown.py results.json            # writes results.md
    python common/report_markdown.py results.json report.md
    python common/report_markdown.py results.json -          # prints to stdout

The input may be UTF-8, UTF-8 with a byte-order mark, or UTF-16 (what
PowerShell's ">" redirect writes). The output file is always UTF-8.

Every string that can come from the audited site (titles, evidence, URLs, fix
snippets) is escaped: it is shown as text and can never add a heading, a table
column, a link or HTML of its own. Fix snippets go in a code fence longer than
any run of backticks inside them.
"""
import html
import json
import os
import re
import sys
from urllib.parse import quote, urlsplit
from json_boundary import read_json, validate_report_shape, atomic_write_text

# Reports are a few hundred kilobytes; this only stops a wrong file being read whole.
MAX_INPUT_BYTES = 50 * 1024 * 1024
# Per-item caps that keep the Markdown readable on a large report.
MAX_TEXT_CHARS = 600
MAX_PAGES_LISTED = 10
MAX_EVIDENCE_ITEMS = 5
MAX_EVIDENCE_URLS = 5

_STATUS_TEXT = {
    "completed": "Completed",
    "completed_with_timeouts": "Completed, but at least one analysis step ran out of time",
    "degraded": "Partly completed (an analysis step failed or robots.txt could not be read)",
    "partial_deadline_reached": "Stopped at the time limit before every step finished",
    "insufficient_evidence": "No page could be analyzed, so the site's pages were not assessed",
}
_FINDING_STATUS_TEXT = {
    "confirmed": "confirmed",
    "suspected": "suspected (likely, not proven)",
    "insufficient_evidence": "not enough evidence to judge",
    "not_applicable": "not applicable",
    "analysis_failed": "analysis failed",
}
_TYPE_TEXT = {"defect": "Defect", "proactive_improvement": "Improvement opportunity"}
_SNIPPET_LANG = {"json-ld": "html", "jsonld": "html", "json": "json", "html": "html", "markdown": "markdown",
                 "text": "text", "txt": "text"}
# Characters with a meaning inside a line of Markdown: emphasis, code, links,
# table cells, strikethrough, headings and backslash itself. <, > and & are
# HTML-escaped instead. Text is always one line, so nothing else can start a block.
_MD_SPECIAL = re.compile(r"([\\`*_\[\]|~#])")
# What can start a block when it opens a line: a list item, a quote, a heading
# underline, a thematic break or a numbered list.
_LINE_START = re.compile(r"^([-+=*>])|^(\d+)([.)])")


def text(value, limit=MAX_TEXT_CHARS):
    """Untrusted value as one line of plain Markdown text: whitespace collapsed,
    HTML escaped, Markdown punctuation escaped, cut to limit characters. Safe
    anywhere inside a line."""
    if value is None:
        return ""
    s = " ".join(str(value).split())
    if len(s) > limit:
        s = s[:limit - 3].rstrip() + "..."
    s = html.escape(s, quote=False)
    return _MD_SPECIAL.sub(r"\\\1", s)


def para(value, limit=MAX_TEXT_CHARS):
    """Untrusted value that opens its own line: text() plus an escaped first
    character, so it can never become a list item, heading or break."""
    s = text(value, limit)
    return _LINE_START.sub(lambda m: "\\" + m.group(1) if m.group(1) else m.group(2) + "\\" + m.group(3), s, count=1)


def code_span(value, limit=200):
    """Untrusted value as inline code. The fence is longer than any backtick run
    inside, and padding keeps a leading or trailing backtick apart from it."""
    s = " ".join(str(value).split())[:limit]
    if not s:
        return ""
    longest = max((len(m) for m in re.findall(r"`+", s)), default=0)
    fence = "`" * (longest + 1)
    return f"{fence} {s} {fence}" if longest or s.startswith(" ") else f"{fence}{s}{fence}"


def code_block(value, lang=""):
    """Untrusted multi-line value as a fenced code block."""
    s = str(value).replace("\r\n", "\n").replace("\r", "\n")
    longest = max((len(m) for m in re.findall(r"`+", s)), default=0)
    fence = "`" * max(3, longest + 1)
    lang = re.sub(r"[^a-z0-9-]", "", str(lang).lower())[:20]
    return f"{fence}{lang}\n{s}\n{fence}"


def link(url, label=None):
    """A clickable link for an http(s) URL, or escaped text for anything else. The
    URL goes in an autolink with every character that could end it encoded."""
    s = str(url or "").strip()
    try:
        scheme = urlsplit(s).scheme.lower()
    except ValueError:
        scheme = ""
    if scheme not in ("http", "https") or len(s) > 2000:
        return text(s, 300)
    safe = quote(s, safe="/:?#[]@!$&'()*+,;=%-._~")
    if label is None:
        return f"<{safe}>"
    return f"[{text(label, 200)}]({safe.replace('(', '%28').replace(')', '%29')})"


def _cell(value, limit=200):
    return text(value, limit) or " "


def _num(value, digits=2):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:.{digits}f}"


def _list(value):
    return value if isinstance(value, list) else []


def _dict(value):
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _header(report):
    cov = _dict(report.get("coverage"))
    lines = [f"# Brand AI-Readiness Audit: {text(report.get('site') or 'unknown site', 200)}", ""]
    lines.append(f"- **Audited at:** {text(report.get('audited_at') or 'unknown', 60)}")
    status = report.get("execution_status")
    lines.append(f"- **Run:** {text(_STATUS_TEXT.get(status, status or 'unknown'), 200)}")
    if "pages_analyzed" in cov:
        pages = f"{text(cov.get('pages_analyzed'))} analyzed of {text(cov.get('pages_discovered', 0))} discovered"
        if cov.get("sections_discovered"):
            pages += (f"; {text(cov.get('sections_analyzed', 0))} of {text(cov['sections_discovered'])} "
                      f"site sections reached")
        lines.append(f"- **Pages:** {pages}")
    if cov.get("pages_out_of_scope"):
        lines.append(f"- **Login pages left out:** {text(cov['pages_out_of_scope'])}")
    if cov.get("pages_challenged"):
        lines.append(f"- **Pages that answered with a bot challenge:** {text(cov['pages_challenged'])}")
    if cov.get("pages_partially_observed"):
        lines.append(f"- **Pages read only in part:** {text(cov['pages_partially_observed'])} (checks that need the "
                     "whole page skip them)")
    if isinstance(cov.get("runtime_seconds"), (int, float)):
        lines.append(f"- **Run time:** {_num(cov['runtime_seconds'], 1)} seconds")
    timing = _dict(report.get("timing"))
    if isinstance(timing.get("core_limit_s"), (int, float)):
        lines.append(f"- **Time limits:** audit worker stopped at {_num(timing['core_limit_s'], 0)} seconds "
                     f"(enforced); {_num(timing.get('agent_time_left_s', 0), 0)} seconds left for the "
                     f"optional agent stage (not enforced by the audit)")
    budget = _dict(cov.get("network_budget"))
    site_pool = _dict(_dict(budget.get("pools")).get("site"))
    if isinstance(site_pool.get("requests"), int):
        lines.append(f"- **Requests to the site:** {text(site_pool['requests'])} of at most "
                     f"{text(site_pool.get('max_requests'))}")
    lines.append("")
    lines.append("This report checks a sample of pages from outside, the way an AI assistant or crawler sees "
                 "the site. It changes nothing on the site.")
    return lines


def _confidence(report):
    conf = _dict(report.get("confidence"))
    if not conf:
        return []
    lines = ["## How far to trust this report", ""]
    level = conf.get("level")
    lines.append(f"**Confidence:** {text(level or 'unknown', 20)} ({_num(conf.get('score'))})")
    lines.append("")
    if conf.get("explanation"):
        lines += [para(conf["explanation"], 2000), ""]
    reasons = _dict(conf.get("reasons"))
    components = _dict(conf.get("components"))
    # Newer reports keep brand identity out of the score; their method says so.
    identity_label = ("Brand identity (not in the score)" if "beside the score" in str(conf.get("method", ""))
                      else "Brand identity")
    labels = (("sample_representativeness", "Page sample"), ("identity_confidence", identity_label),
              ("execution_penalty", "Audit run"))
    rows = [(label, components.get(key), reasons.get(key)) for key, label in labels if key in reasons]
    if rows:
        lines += ["| Part | Score | Why |", "| --- | --- | --- |"]
        lines += [f"| {label} | {_num(score)} | {_cell(reason, 400)} |" for label, score, reason in rows]
        lines.append("")
    return lines


def _summary(report):
    s = _dict(report.get("summary"))
    lines = ["## Summary", ""]
    if s.get("status_reason"):
        lines += [f"**Why this report is short:** {text(s['status_reason'], 600)}", ""]
    if not s.get("total_findings"):
        lines += ["No findings were reported." if report.get("execution_status") == "completed"
                  else "No findings were reported, and the run did not complete, so nothing can be concluded.", ""]
    rows = (("Findings", "total_findings"), ("Critical", "critical"), ("High", "high"), ("Medium", "medium"),
            ("Low", "low"), ("Improvement suggestions (not defects)", "proactive_improvements"),
            ("Not enough evidence to judge", "insufficient_evidence_items"),
            ("Recommendations", "total_recommendations"))
    lines += ["| | Count |", "| --- | --- |"]
    lines += [f"| {label} | {text(s.get(key, 0))} |" for label, key in rows]
    lines.append("")
    return lines


def _plan(report):
    top = [t for t in _list(report.get("top_actions")) if isinstance(t, dict)]
    wins = [w for w in _list(report.get("quick_wins")) if isinstance(w, dict)]
    lines = []
    # Start here is shown only when the report marks one: a confirmed defect.
    start = next((t for t in top if t.get("start_here")), None)
    if start:
        lines += ["## Start here", "",
                  f"**{text(start.get('finding_id'), 20)}: {text(start.get('title'), 300)}**", ""]
        if start.get("summary"):
            lines += [para(start["summary"], 600), ""]
        lines += [f"Impact {text(start.get('impact', 'n/a'))}, effort {text(start.get('effort', 'n/a'))}. "
                  f"Details are under {text(start.get('finding_id'), 20)} below.", ""]
    if top:
        lines += ["## Top actions", "", "Defects only; improvement opportunities are listed with the findings.", "", "| # | Finding | Action | Priority | Impact | Effort | Quick win |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for n, t in enumerate(top, 1):
            lines.append(f"| {n} | {_cell(t.get('finding_id'), 20)}: {_cell(t.get('title'))} | "
                         f"{_cell(t.get('summary'))} | {_cell(t.get('priority'))} | {_cell(t.get('impact'))} | "
                         f"{_cell(t.get('effort'))} | {'yes' if t.get('quick_win') else 'no'} |")
        lines.append("")
    if wins:
        lines += ["## Quick wins", "", "Valuable changes that take little work:", ""]
        for w in wins:
            lines.append(f"- **{text(w.get('id'), 20)}: {text(w.get('title'), 300)}.** {text(w.get('summary'), 400)} "
                         f"(impact {text(w.get('impact', 'n/a'))}, effort {text(w.get('effort', 'n/a'))})")
        lines.append("")
    return lines


def _findings_table(findings):
    if not findings:
        return []
    lines = ["## All findings", "", "| ID | Type | Severity | Status | Finding | Pages |",
             "| --- | --- | --- | --- | --- | --- |"]
    for f in findings:
        lines.append(f"| {_cell(f.get('id'), 20)} | {_cell(_TYPE_TEXT.get(f.get('finding_type'), f.get('finding_type')))} | "
                     f"{_cell(f.get('severity'))} | "
                     f"{_cell(_FINDING_STATUS_TEXT.get(f.get('status'), f.get('status')))} | {_cell(f.get('title'), 300)} | "
                     f"{len(_list(f.get('affected_pages')))} |")
    lines.append("")
    return lines


def _pages(pages):
    pages = _list(pages)
    if not pages:
        return []
    lines = ["**Pages:**", ""]
    lines += [f"- {link(p)}" for p in pages[:MAX_PAGES_LISTED]]
    if len(pages) > MAX_PAGES_LISTED:
        lines.append(f"- and {len(pages) - MAX_PAGES_LISTED} more")
    return lines + [""]


def _evidence(items):
    items = [e for e in _list(items) if isinstance(e, dict)]
    if not items:
        return []
    lines = ["**Evidence:**", ""]
    for e in items[:MAX_EVIDENCE_ITEMS]:
        lines.append(f"- {text(e.get('description') or e.get('type') or 'observation', 600)}")
        urls = _list(e.get("urls"))
        for u in urls[:MAX_EVIDENCE_URLS]:
            lines.append(f"  - {link(u)}")
        if len(urls) > MAX_EVIDENCE_URLS:
            lines.append(f"  - and {len(urls) - MAX_EVIDENCE_URLS} more")
    if len(items) > MAX_EVIDENCE_ITEMS:
        lines.append(f"- and {len(items) - MAX_EVIDENCE_ITEMS} more observations in the JSON report")
    return lines + [""]


def _snippet(snippet):
    snippet = _dict(snippet)
    if not snippet.get("code"):
        return []
    lines = ["**Ready-to-paste fix:**", ""]
    if snippet.get("placement"):
        lines += [f"Where: {text(snippet['placement'], 400)}", ""]
    lang = _SNIPPET_LANG.get(str(snippet.get("format", "")).lower(), "")
    lines += [code_block(snippet["code"], lang), ""]
    placeholders = [p for p in _list(snippet.get("placeholders")) if p]
    if placeholders:
        lines += ["Replace before publishing: " + ", ".join(code_span(p, 120) for p in placeholders[:20]), ""]
    if snippet.get("note"):
        lines += [para(snippet["note"], 600), ""]
    return lines


def _action(action):
    action = _dict(action)
    lines = []
    if action.get("summary"):
        lines += [f"**What to do:** {text(action['summary'], 600)}", ""]
    steps = [s for s in _list(action.get("steps")) if s]
    if steps:
        lines += [f"{n}. {text(s, 600)}" for n, s in enumerate(steps[:12], 1)] + [""]
    facts = []
    for key, label in (("effort", "Effort"), ("impact", "Impact")):
        if action.get(key):
            facts.append(f"{label}: {text(action[key], 40)}")
    if action.get("quadrant_label"):
        facts.append(text(action["quadrant_label"], 200))
    if facts:
        lines += ["; ".join(facts) + ".", ""]
    if action.get("expected_benefit"):
        lines += [f"**Expected benefit:** {text(action['expected_benefit'], 600)}", ""]
    if action.get("verification"):
        lines += [f"**How to check the fix:** {text(action['verification'], 600)}", ""]
    return lines + _snippet(action.get("snippet"))


def _finding_detail(f):
    lines = [f"### {text(f.get('id'), 20)}: {text(f.get('title'), 300)}", ""]
    facts = [f"Type: {text(_TYPE_TEXT.get(f.get('finding_type'), f.get('finding_type')), 40)}",
             f"Severity: {text(f.get('severity'), 20)}",
             f"Status: {text(_FINDING_STATUS_TEXT.get(f.get('status'), f.get('status')), 60)}",
             f"Confidence: {_num(f.get('confidence'))}"]
    if f.get("check_id"):
        facts.append("Check: " + code_span(f["check_id"], 80))
    reach = _dict(f.get("coverage"))
    analyzed, affected = reach.get("pages_analyzed"), reach.get("affected_pages")
    if all(isinstance(v, int) and not isinstance(v, bool) for v in (analyzed, affected)) and analyzed > 0 \
            and affected > 0:
        facts.append(f"Seen on {affected} of {analyzed} analyzed page(s)")
    lines += ["; ".join(facts), ""]
    if f.get("status_note"):
        lines += [text(f["status_note"], 300), ""]
    gate = _dict(f.get("severity_gate"))
    if gate.get("from") and gate.get("to"):
        lines += [f"**Severity lowered** from {text(gate['from'], 20)} to {text(gate['to'], 20)}: "
                  f"{text(gate.get('reason'), 400)}", ""]
    if f.get("root_cause"):
        lines += [f"**Why it matters:** {text(f['root_cause'], 800)}", ""]
    return lines + _pages(f.get("affected_pages")) + _evidence(f.get("evidence")) + _action(f.get("suggested_action"))


def _recommendations(report, findings):
    covered = {f.get("check_id") for f in findings}
    # A recommendation that points at a finding (finding_id) is that finding,
    # already shown above.
    recs = [r for r in _list(report.get("recommendations")) if isinstance(r, dict) and "finding_id" not in r
            and r.get("check_id") not in covered]
    if not recs:
        return []
    lines = ["## Other recommendations", "", "Good practice to keep, beyond the findings above:", ""]
    for r in recs:
        action = _dict(r.get("suggested_action"))
        lines.append(f"- **{text(r.get('title'), 300)}.** {text(action.get('summary'), 600)}")
    return lines + [""]


def _whats_working(report):
    items = [w for w in _list(report.get("whats_working")) if isinstance(w, dict)]
    if not items:
        return []
    lines = ["## What's working", "", "Checks that ran and found nothing to fix:", ""]
    for w in items:
        lines.append(f"- **{text(w.get('title'), 300)}.** {text(w.get('evidence'), 600)}")
    return lines + [""]


# Names of the agent checks (common/agent_evidence.AG_CHECKS), kept here so the
# renderer imports only the standard library.
_AG_NAMES = {"AG-01": "About-page concreteness", "AG-02": "Independent mentions",
             "AG-03": "Independent contradiction", "AG-04": "Facts drawn inside images",
             "AG-05": "Namesake ambiguity", "AG-06": "Review and profile opportunity"}
_OUTCOME_TEXT = {"pass": "passed", "finding": "finding reported", "not_assessed": "not assessed",
                 "error": "error"}
_SUBMISSION_TEXT = {"not_supplied": "not supplied", "legacy": "legacy findings list (assesses no check)",
                    "envelope": "outcome envelope"}


def _agent_stage(report):
    """What the optional agent stage received and assessed, check by check."""
    stage = _dict(_dict(report.get("coverage")).get("agent_stage"))
    checks = _dict(stage.get("checks"))
    if not stage or not checks:
        return []
    lines = ["## Agent checks", "",
             f"Received: {text(_SUBMISSION_TEXT.get(stage.get('submission_status'), stage.get('submission_status')), 80)}. "
             f"Assessed: {text(stage.get('assessed_count', 0))} of {text(len(checks))} "
             f"({text(stage.get('assessment_status') or 'not_run', 40)}). A check that was not assessed is not a pass.",
             "", "| Check | Outcome | Reason |", "| --- | --- | --- |"]
    for check_id in sorted(checks):
        record = _dict(checks[check_id])
        name = _AG_NAMES.get(check_id)
        label = f"{check_id} {name}" if name else check_id
        lines.append(f"| {_cell(label, 80)} | {_cell(_OUTCOME_TEXT.get(record.get('outcome'), record.get('outcome')))} | "
                     f"{_cell(record.get('reason'), 400)} |")
    return lines + [""]


def _not_checked(report):
    cov = _dict(report.get("coverage"))
    limitations = [x for x in _list(report.get("limitations")) if x]
    skipped = [x for x in _list(cov.get("out_of_scope_pages")) if isinstance(x, dict)]
    notes = [w for w in _list(report.get("warnings")) if w]
    lines = []
    if limitations or skipped:
        lines += ["## What this audit could not check", ""]
        lines += [f"- {text(x, 1200)}" for x in limitations]
        if skipped:
            lines += ["", "Login pages that were fetched but not analyzed:", ""]
            lines += [f"- {link(x.get('url'))} ({text(', '.join(str(s) for s in _list(x.get('signals'))), 300)})"
                      for x in skipped]
        lines.append("")
    if notes:
        lines += ["## Notes from the run", ""] + [f"- {text(w, 1200)}" for w in notes] + [""]
    return lines


def render(report):
    """The Markdown text for one JSON audit report (a dict)."""
    if not isinstance(report, dict):
        raise ValueError("the report must be a JSON object")
    validate_report_shape(report)
    for key in ('coverage', 'summary', 'confidence'):
        if key in report and not isinstance(report[key], dict):
            raise ValueError(f"report.{key} must be an object")
    for key in ('findings', 'recommendations', 'top_actions', 'quick_wins', 'whats_working'):
        if key in report and (not isinstance(report[key], list) or any(not isinstance(v, dict) for v in report[key])):
            raise ValueError(f"report.{key} must be a list of objects")
    findings = [f for f in _list(report.get("findings")) if isinstance(f, dict)]
    lines = _header(report) + [""] + _confidence(report) + _summary(report) + _plan(report)
    lines += _findings_table(findings)
    if findings:
        lines += ["## Finding details", ""]
        for f in findings:
            lines += _finding_detail(f)
    lines += _recommendations(report, findings) + _whats_working(report) + _agent_stage(report) + _not_checked(report)
    lines += ["---", "", "Generated from the JSON audit report by common/report_markdown.py. Findings describe the "
                         "sampled pages; the JSON report holds every detail."]
    out = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", out).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def read_report(path, limit=MAX_INPUT_BYTES):
    """Load a JSON report written as UTF-8, UTF-8 with a BOM, or UTF-16."""
    result = read_json(path, limit)
    if not isinstance(result, dict):
        raise ValueError("the report/packet must be a JSON object")
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Turn a JSON audit report into a Markdown report.")
    parser.add_argument("report", help="JSON report printed by run_audit.py (for example results.json)")
    parser.add_argument("output", nargs="?", default=None,
                        help="Markdown file to write (default: the report path with .md); '-' prints to stdout")
    args = parser.parse_args(argv)
    try:
        markdown = render(read_report(args.report))
    except FileNotFoundError:
        parser.exit(2, f"report_markdown: no such file: {args.report}\n")
    except (UnicodeDecodeError, ValueError) as exc:
        parser.exit(2, f"report_markdown: {args.report} is not a readable JSON audit report ({exc})\n")
    if args.output == "-":
        sys.stdout.write(markdown)
        return 0
    output = args.output or os.path.splitext(args.report)[0] + ".md"
    if os.path.realpath(output) == os.path.realpath(args.report):
        parser.exit(2, "report_markdown: the output would overwrite the JSON report\n")
    try:
        atomic_write_text(output, markdown)
    except OSError as exc:
        parser.exit(2, f"report_markdown: cannot write output ({str(exc)[:300]})\n")
    sys.stderr.write(f"Wrote {output}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
