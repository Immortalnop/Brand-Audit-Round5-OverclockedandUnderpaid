"""render_report.py -- turns report.json into report.md for a non-expert reader (A25).

Standard library only. Layout:
  1. header: site, date, execution status, confidence (with its method), sample
  2. top actions: rank, action, severity, effort, owner, finding ids
  3. severity summary
  4. one card per core finding: what we found / why it matters / evidence /
     how to fix (with any proposed JSON-LD snippet) / how to verify
  5. recommendations beyond the defects
  6. limitations and coverage
  7. appendix: SEO hygiene items as a compact table

Usage: python3 render_report.py report.json [-o report.md]
"""
import json
import sys

_SEV_ICON = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}


def _esc(text):
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ")


def _finding_card(f):
    out = []
    a = f.get("suggested_action") or {}
    r = f.get("severity_rationale") or {}
    out.append(f"### {f['id']} - {f['title']}")
    out.append(f"**{_SEV_ICON.get(f['severity'], f['severity'])}** | status: {f['status']} | confidence: "
               f"{f.get('confidence')} | owner: {a.get('owner_role', '-')} | effort: {a.get('effort', '-')}")
    if r:
        out.append(f"*Why this severity:* gate **{r.get('gate')}**, scope {r.get('scope')} ({r.get('prevalence')})"
                   + (f", {r.get('adjustment')}" if r.get('adjustment') not in (None, 'none') else ""))
    if f.get("check_ids") and len(f["check_ids"]) > 1:
        out.append(f"*Combines checks:* {', '.join(f['check_ids'])}")
    out.append("")
    out.append(f"**What we found.** {f.get('root_cause', '')}")
    out.append("")
    out.append(f"**Why it matters.** {f.get('mechanism', '')}")
    out.append("")
    ev = [e for e in (f.get("evidence") or []) if isinstance(e, dict)][:5]
    if ev:
        out.append("**Evidence.**")
        for e in ev:
            urls = ", ".join((e.get("urls") or [])[:3])
            out.append(f"- {e.get('description', e.get('type', ''))}" + (f" ({urls})" if urls else ""))
        out.append("")
    out.append(f"**How to fix.** {a.get('summary', '')}")
    for i, step in enumerate(a.get("steps") or [], 1):
        out.append(f"{i}. {step}")
    for url, snippet in (a.get("proposed_snippets") or {}).items():
        out.append("")
        out.append(f"Draft JSON-LD for {url} (review values before use):")
        out.append("```json")
        out.append(snippet)
        out.append("```")
    out.append("")
    out.append(f"**How to verify.** {a.get('verification', '')}")
    out.append("")
    return out


def render_markdown(report):
    s = report.get("summary", {})
    conf = report.get("confidence") or {}
    cov = report.get("coverage") or {}
    out = [f"# AI-readiness audit: {report.get('site')}", ""]
    out.append(f"Audited {report.get('audited_at')} | status **{report.get('execution_status')}** | "
               f"report confidence **{conf.get('score')}**")
    out.append("")
    out.append(f"Sample: {cov.get('pages_analyzed', 0)} content page(s) across {cov.get('templates_sampled', 0)} "
               f"page template(s); {cov.get('pages_discovered', 0)} URL(s) discovered; "
               f"{cov.get('pages_challenged', 0)} bot-challenged.")
    out.append(f"Confidence method: {conf.get('method', '')}")
    out.append("")
    out.append("## Top actions")
    out.append("")
    plan = report.get("action_plan") or report.get("top_actions") or []
    if plan:
        out.append("| # | Action | Severity | Effort | Owner | Finding |")
        out.append("|---|---|---|---|---|---|")
        for i, a in enumerate(plan[:5], 1):
            fid = ", ".join(a.get("finding_ids") or [a.get("finding_id", "")])
            out.append(f"| {a.get('rank', i)} | {_esc(a.get('summary'))} | {a.get('severity', '')} | "
                       f"{a.get('effort', '')} | {a.get('owner_role', '')} | {fid} |")
    else:
        out.append("No actionable findings in this sample.")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append(f"{s.get('total_findings', 0)} finding(s): {s.get('critical', 0)} critical, {s.get('high', 0)} high, "
               f"{s.get('medium', 0)} medium, {s.get('low', 0)} low. {s.get('hygiene_items', 0)} SEO-hygiene item(s) "
               f"in the appendix. Agent corroboration stage: {(report.get('agent_stage') or {}).get('status', 'n/a')}.")
    out.append("")
    out.append("## Findings")
    out.append("")
    for f in report.get("findings", []):
        out.extend(_finding_card(f))
    recs = report.get("recommendations") or []
    if recs:
        out.append("## Recommendations beyond the defects")
        out.append("")
        for r in recs:
            a = r.get("suggested_action") or {}
            out.append(f"### {r['id']} - {r['title']}")
            out.append(f"{r.get('root_cause', '')}")
            for i, step in enumerate(a.get("steps") or [], 1):
                out.append(f"{i}. {step}")
            if r.get("affected_pages"):
                out.append(f"Pages: {', '.join(r['affected_pages'][:5])}")
            out.append("")
    lim = report.get("limitations") or []
    if lim:
        out.append("## Limitations")
        out.append("")
        out.extend(f"- {x}" for x in lim)
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
    with open(args.report, encoding="utf-8") as fh:
        md = render_markdown(json.load(fh))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
