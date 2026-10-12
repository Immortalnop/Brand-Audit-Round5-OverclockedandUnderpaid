"""finalize_report.py -- pass 2 of the audit: merge the agent's corroboration
findings into an existing report without re-crawling the site.

Flow (see skills/audit-orchestrator/SKILL.md):
  pass 1  run_audit.py <url> --out-dir audit_out
          -> audit_out/report.json, audit_out/agent_brief.json, audit_out/report.md
  agent   follows skills/entity-corroboration-agent/SKILL.md using agent_brief.json,
          writes audit_out/agent_findings.json ([] if nothing fires)
  pass 2  finalize_report.py --report audit_out/report.json \
                             --agent-findings audit_out/agent_findings.json

Agent findings are rebuilt through the shared finding factory (catalog
enrichment + Invariant I-1), merged with the existing findings by root-cause
group, re-scored with the report's own scoring_context, re-ordered, re-numbered
and re-validated. Scoring is idempotent, so running this twice gives the same
report. Deterministic given the same two input files.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bootstrap import ensure_paths  # noqa: E402
_ROOT = ensure_paths()

from scoring import ScoringContext  # noqa: E402
from merge_findings import _group_merge  # noqa: E402
from generate_recommendations import build_action_plan, top_actions, quick_wins  # noqa: E402
from whats_working import reported_check_ids  # noqa: E402
from validate_report import validate_report  # noqa: E402
from ingest_agent_findings import load_agent_findings  # noqa: E402


def finalize(report, agent_findings_path):
    from run_audit import finalize_findings
    report = dict(report)
    result, stage = load_agent_findings(agent_findings_path)
    ctx = ScoringContext.from_dict(report.get("scoring_context") or {})
    existing = list(report.get("findings", [])) + list(report.get("hygiene_findings", []))
    # Drop any agent findings from a previous finalize so re-running is idempotent.
    existing = [f for f in existing
                if not any((p or {}).get("skill") == "entity-corroboration-agent"
                           for p in ((f.get("provenance") or {}).get("contributing_skills") or [f.get("provenance") or {}]))]
    for f in existing:
        f["tier_override"] = f.pop("tier", None)
    merged = _group_merge(existing + list(result["findings"]))
    core, hygiene = finalize_findings(merged, ctx)
    report["findings"], report["hygiene_findings"] = core, hygiene
    report["action_plan"] = build_action_plan(core)
    report["top_actions"] = top_actions(report["action_plan"])
    report["quick_wins"] = quick_wins(report["action_plan"])
    # An agent finding can contradict a check listed as passing (e.g. AG-04 reads
    # a fact inside an image): such entries leave "what's working".
    flagged = reported_check_ids(core + hygiene + list(report.get("recommendations", [])))
    report["whats_working"] = [w for w in report.get("whats_working", []) if not flagged & set(w.get("check_ids", ()))]
    stage_info = dict(report.get("agent_stage") or {})
    stage_info["status"] = stage
    stage_info["findings_ingested"] = result["metrics"].get("findings_ingested", 0)
    report["agent_stage"] = stage_info
    cov = dict(report.get("coverage") or {})
    cov["agent_corroboration_stage"] = stage
    report["coverage"] = cov
    if stage != "not_supplied":
        report["warnings"] = [w for w in report.get("warnings", []) if "Agent corroboration stage not supplied" not in w]
    report["limitations"] = [l for l in report.get("limitations", []) if "agent corroboration" not in l.lower()]
    if stage == "not_supplied":
        report["limitations"].append("The agent corroboration stage did not run; cross-web agreement and About-page "
                                     "concreteness were not checked (not the same as \"no problem found\").")
    return validate_report(report, strict_catalog=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Merge agent corroboration findings into an audit report.")
    ap.add_argument("--report", required=True)
    ap.add_argument("--agent-findings", default=os.environ.get("AGENT_FINDINGS_PATH"))
    ap.add_argument("--out", default=None, help="Output path (default: overwrite --report)")
    args = ap.parse_args(argv)
    with open(args.report, encoding="utf-8") as fh:
        report = json.load(fh)
    final = finalize(report, args.agent_findings)
    out = args.out or args.report
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(final, fh, indent=2, default=str)
    from render_report import render_markdown
    md_path = os.path.join(os.path.dirname(os.path.abspath(out)), "report.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(final))
    s = final["summary"]
    sys.stderr.write(f"[finalize] agent stage: {final['agent_stage']['status']}; findings {s['total_findings']} "
                     f"(critical {s['critical']}, high {s['high']}, medium {s['medium']}, low {s['low']}); "
                     f"wrote {out} and {md_path}\n")
    print(json.dumps(final, indent=2, default=str))


if __name__ == "__main__":
    main()
