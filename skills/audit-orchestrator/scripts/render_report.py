"""render_report.py -- turns report.json into report.md for a non-expert reader (A25).

Standard library only. Layout:
  1. header: site, date, execution status, sample
  2. how far to trust this report: confidence level, limiting factor, reasons
  3. start here, top actions (with quick wins), severity summary
  4. one card per core finding: what we found / why it matters / evidence /
     how to fix (with any ready-to-paste snippet) / how to verify
  5. what's working: checks that ran and passed
  6. recommendations beyond the defects
  7. limitations, pages kept out of scope
  8. appendix: SEO hygiene items as a compact table

Text that comes from the audited site (titles, evidence, URLs) is escaped, so a
page title cannot add headings, links, table columns or HTML to the report.
Snippets are fenced with more backticks than any run inside them.

Usage: python3 render_report.py report.json [-o report.md]
"""
import json
import re
import sys

_SEV_ICON = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
_MD_SPECIAL = re.compile(r"([\\`*_\[\]<>|#~])")


def _esc(text):
    """Inline-safe text: Markdown and HTML control characters escaped, one line."""
    text = " ".join(str(text if text is not None else "").split())
    return _MD_SPECIAL.sub(r"\\\1", text)


def _fence(code):
    longest = max((len(m) for m in re.findall(r"`+", code or "")), default=0)
    return "`" * max(3, longest + 1)


def _url_list(urls, limit=3):
    return ", ".join(f"<{u}>" if re.match(r"^https?://[^\s<>]+$", u or "") else _esc(u) for u in (urls or [])[:limit])


def _snippet_block(snippet):
    out = [f"Ready-to-paste fix ({_esc(snippet.get('format', 'html'))}). Placement: {_esc(snippet.get('placement', ''))}."]
    code = snippet.get("code", "")
    lang = {"markdown": "markdown", "html": "html"}.get(snippet.get("format"), "")
    fence = _fence(code)
    out += [fence + lang, code, fence]
    filled = snippet.get("filled_from") or {}
    if filled:
        out.append("Filled from: " + "; ".join(f"{_esc(k)}: {_esc(v)}" for k, v in filled.items()) + ".")
    if snippet.get("placeholders"):
        out.append("Replace before publishing: " + ", ".join(f"`{p}`" for p in snippet["placeholders"]) + ".")
    return out


def _finding_card(f):
    out = []
    a = f.get("suggested_action") or {}
    r = f.get("severity_rationale") or {}
    out.append(f"### {f['id']} - {_esc(f['title'])}")
    out.append(f"**{_SEV_ICON.get(f['severity'], f['severity'])}** | status: {f['status']} | confidence: "
               f"{f.get('confidence')} | owner: {a.get('owner_role', '-')} | effort: {a.get('effort', '-')}")
    if r:
        out.append(f"*Why this severity:* gate **{r.get('gate')}**, scope {r.get('scope')} ({_esc(r.get('prevalence'))})"
                   + (f", {_esc(r.get('adjustment'))}" if r.get('adjustment') not in (None, 'none') else ""))
    if f.get("check_ids") and len(f["check_ids"]) > 1:
        out.append(f"*Combines checks:* {', '.join(f['check_ids'])}")
    out.append("")
    out.append(f"**What we found.** {_esc(f.get('root_cause', ''))}")
    out.append("")
    out.append(f"**Why it matters.** {_esc(f.get('mechanism', ''))}")
    out.append("")
    ev = [e for e in (f.get("evidence") or []) if isinstance(e, dict)][:5]
    if ev:
        out.append("**Evidence.**")
        for e in ev:
            urls = _url_list(e.get("urls"))
            out.append(f"- {_esc(e.get('description', e.get('type', '')))}" + (f" ({urls})" if urls else ""))
        out.append("")
    out.append(f"**How to fix.** {_esc(a.get('summary', ''))}")
    for i, step in enumerate(a.get("steps") or [], 1):
        out.append(f"{i}. {_esc(step)}")
    for url, snippet in (a.get("proposed_snippets") or {}).items():
        out.append("")
        out.append(f"Draft JSON-LD for {_url_list([url])} (review values before use):")
        fence = _fence(snippet)
        out += [fence + "json", snippet, fence]
    if a.get("snippet"):
        out.append("")
        out += _snippet_block(a["snippet"])
    out.append("")
    out.append(f"**How to verify.** {_esc(a.get('verification', ''))}")
    out.append("")
    return out


def render_markdown(report):
    s = report.get("summary", {})
    conf = report.get("confidence") or {}
    cov = report.get("coverage") or {}
    out = [f"# AI-readiness audit: {_esc(report.get('site'))}", ""]
    out.append(f"Audited {report.get('audited_at')} | status **{report.get('execution_status')}**")
    out.append("")
    out.append(f"Sample: {cov.get('pages_analyzed', 0)} content page(s) across {cov.get('templates_sampled', 0)} "
               f"page template(s); {cov.get('pages_discovered', 0)} URL(s) discovered; "
               f"{cov.get('pages_challenged', 0)} bot-challenged; {cov.get('pages_out_of_scope', 0)} login page(s) "
               "kept out of scope. The audit reads the site from outside, the way a crawler does, and changes nothing.")
    out.append("")
    out.append("## How far to trust this report")
    out.append("")
    out.append(f"**Confidence: {conf.get('level', '-')} ({conf.get('score')})**. "
               + _esc(conf.get("explanation", "")))
    reasons = conf.get("reasons") or {}
    comps = conf.get("components") or {}
    if reasons:
        out.append("")
        out.append("| Part | Score | Why |")
        out.append("|---|---|---|")
        for k, why in reasons.items():
            out.append(f"| {k.replace('_', ' ')} | {comps.get(k, '')} | {_esc(why)} |")
    out.append("")
    out.append(f"Method: {_esc(conf.get('method', ''))}")
    out.append("")
    plan = report.get("action_plan") or report.get("top_actions") or []
    first = next((a for a in plan if a.get("start_here")), plan[0] if plan else None)
    if first:
        out.append("## Start here")
        out.append("")
        fid = ", ".join(first.get("finding_ids") or [first.get("finding_id", "")])
        out.append(f"**{_esc(first.get('summary'))}** ({first.get('severity')} severity, {first.get('effort')} effort; "
                   f"details under {fid}).")
        out.append("")
    out.append("## Top actions")
    out.append("")
    if plan:
        out.append("| # | Action | Severity | Effort | Quick win | Owner | Finding |")
        out.append("|---|---|---|---|---|---|---|")
        for i, a in enumerate(plan[:5], 1):
            fid = ", ".join(a.get("finding_ids") or [a.get("finding_id", "")])
            out.append(f"| {a.get('rank', i)} | {_esc(a.get('summary'))} | {a.get('severity', '')} | "
                       f"{a.get('effort', '')} | {'yes' if a.get('quick_win') else ''} | {a.get('owner_role', '')} | {fid} |")
        wins = report.get("quick_wins") or []
        if wins:
            out.append("")
            out.append("Quick wins (medium impact or more, low effort, solid evidence): " + ", ".join(wins) + ".")
    else:
        out.append("No actionable findings in this sample.")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append(f"{s.get('total_findings', 0)} finding(s): {s.get('critical', 0)} critical, {s.get('high', 0)} high, "
               f"{s.get('medium', 0)} medium, {s.get('low', 0)} low. {s.get('hygiene_items', 0)} SEO-hygiene item(s) "
               f"in the appendix. {len(report.get('whats_working') or [])} check(s) passed. Agent corroboration stage: "
               f"{(report.get('agent_stage') or {}).get('status', 'n/a')}.")
    out.append("")
    out.append("## Findings")
    out.append("")
    for f in report.get("findings", []):
        out.extend(_finding_card(f))
    working = report.get("whats_working") or []
    if working:
        out.append("## What's working")
        out.append("")
        out.append("Checks that ran to completion and found nothing to fix:")
        out.append("")
        for w in working:
            out.append(f"- **{_esc(w.get('title'))}.** {_esc(w.get('evidence'))}")
        out.append("")
    recs = report.get("recommendations") or []
    if recs:
        out.append("## Recommendations beyond the defects")
        out.append("")
        for r in recs:
            a = r.get("suggested_action") or {}
            out.append(f"### {r['id']} - {_esc(r['title'])}")
            out.append(_esc(r.get("root_cause", "")))
            for i, step in enumerate(a.get("steps") or [], 1):
                out.append(f"{i}. {_esc(step)}")
            if r.get("affected_pages"):
                out.append(f"Pages: {_url_list(r['affected_pages'], 5)}")
            out.append("")
    lim = report.get("limitations") or []
    if lim:
        out.append("## Limitations")
        out.append("")
        out.extend(f"- {_esc(x)}" for x in lim)
        out.append("")
    oos = cov.get("out_of_scope_pages") or []
    if oos:
        out.append("## Pages kept out of scope")
        out.append("")
        out.extend(f"- {_url_list([p.get('url')])}: {_esc(p.get('reason'))} ({_esc(', '.join(p.get('signals') or []))})"
                   for p in oos)
        out.append("")
    hyg = report.get("hygiene_findings") or []
    if hyg:
        out.append("## Appendix: SEO hygiene")
        out.append("")
        out.append("| Id | Item | Pages | Fix |")
        out.append("|---|---|---|---|")
        for h in hyg:
            out.append(f"| {h['id']} | {_esc(h['title'])} | {len(h.get('affected_pages') or [])} | "
                       f"{_esc((h.get('suggested_action') or {}).get('summary', ''))} |")
        out.append("")
    return "\n".join(out) + "\n"


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Render an audit report.json as Markdown.")
    p.add_argument("report")
    p.add_argument("-o", "--out", default=None)
    args = p.parse_args(argv)
    # utf-8-sig also reads a report saved with a byte order mark (PowerShell).
    with open(args.report, encoding="utf-8-sig") as fh:
        md = render_markdown(json.load(fh))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
