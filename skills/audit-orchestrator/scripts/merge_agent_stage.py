"""merge_agent_stage.py -- fold the agent stage (AG-01 to AG-06) into a saved report.

The deterministic audit runs first and writes its report. The calling agent then
performs the entity-corroboration-agent checks, reading that report, and writes
its observations to a JSON file. This module merges that file into the saved
report without crawling again: it makes no request of any kind and reads nothing
but the two files, so the merge takes well under a second.

The merge goes through the same steps as a live audit with AGENT_FINDINGS_PATH
set: every entry is rebuilt by the shared finding factory (catalog wording and
Invariant I-1), folded into the finding that already reports it
(merge_findings.fold_into), and the findings are prioritized, numbered and
validated again. The recommendations, impact x effort plan, top actions and quick
wins are rebuilt from the new findings. What the merge cannot rebuild without the
site snapshot is kept from the saved report: fix snippets on the findings it
already had, the confidence score (it rates the crawl, which did not change),
and the passed checks, less any that a merged finding now contradicts.
"""
import copy
from datetime import datetime, timezone

from execution_summary import AGENT_STAGE_LIMITATION_MARKS
from generate_recommendations import generate_recommendations, is_finding_reference
from ingest_agent_findings import NOT_SUPPLIED_WARNING, build_agent_findings
from merge_findings import fold_into
from prioritize_findings import annotate_action_plan, prioritize_findings, quick_wins, top_actions
from validate_report import REQUIRED_FINDING_FIELDS, validate_report
from whats_working import reported_check_ids


class ReportMergeError(ValueError):
    """The saved report cannot take agent findings."""


def _check_report(report):
    """Raise ReportMergeError unless report is a complete audit report that
    analyzed at least one page and has no agent findings merged yet."""
    if not isinstance(report, dict) or not isinstance(report.get("coverage"), dict) \
            or not isinstance(report.get("findings"), list) or not isinstance(report.get("recommendations"), list):
        raise ReportMergeError("the file is not an audit report written by run_audit.py")
    for finding in report["findings"]:
        if not isinstance(finding, dict) or REQUIRED_FINDING_FIELDS - finding.keys():
            raise ReportMergeError("the report holds a finding without the fields run_audit.py writes; "
                                   "merge into an unedited report")
    coverage = report["coverage"]
    if coverage.get("agent_corroboration_stage") == "ingested":
        raise ReportMergeError("agent findings were already merged into this report; merge into the report "
                               "the audit wrote")
    if not coverage.get("pages_analyzed"):
        # As in a live audit, where only robots.txt, llms.txt, sitemap and TLS
        # findings are kept when nothing on the site was assessed.
        raise ReportMergeError("the audit analyzed no page of the site, so agent findings about it cannot be "
                               "merged; run the audit again first")


def merge_agent_findings(report, items, source=None):
    """A new report: report with the raw agent entries in items merged in.
    source names the agent findings file in coverage.agent_corroboration. The
    input report is not changed. Raises ReportMergeError when the report cannot
    take agent findings."""
    _check_report(report)
    items = list(items or ())
    report = copy.deepcopy(report)
    coverage = report["coverage"]
    origin = coverage.get("audited_url") or report.get("site")
    added = build_agent_findings(items, origin)
    findings, folded = fold_into(report["findings"], added)

    prioritized = prioritize_findings(findings)
    for index, finding in enumerate(prioritized, 1):
        finding["id"] = f"F-{index:03d}"
        finding["coverage"] = {"affected_pages": len(finding.get("affected_pages") or ()),
                               "pages_analyzed": coverage.get("pages_analyzed", 0),
                               "pages_discovered": coverage.get("pages_discovered", 0)}

    coverage["agent_corroboration_stage"] = "ingested"
    coverage["agent_corroboration"] = {
        "merged_from": source, "merged_at": datetime.now(timezone.utc).isoformat(),
        "findings_supplied": len(items), "findings_ingested": len(added),
        "findings_folded_into_existing": folded, "findings_added": len(added) - folded,
    }
    report["findings"] = prioritized
    report["recommendations"] = generate_recommendations([], prioritized)
    report["warnings"] = [w for w in report.get("warnings") or () if w != NOT_SUPPLIED_WARNING]
    report["limitations"] = [line for line in report.get("limitations") or ()
                             if not any(mark in str(line) for mark in AGENT_STAGE_LIMITATION_MARKS)]
    saved = report.get("whats_working")
    passed = [w for w in saved if isinstance(w, dict)] if isinstance(saved, list) else []
    for key in ("top_actions", "quick_wins", "whats_working"):
        report.pop(key, None)

    validated = validate_report(report, strict_catalog=True)
    annotate_action_plan(validated["findings"] + [r for r in validated["recommendations"]
                                                  if not is_finding_reference(r)],
                         coverage.get("pages_analyzed", 0))
    validated["top_actions"] = top_actions(validated["findings"])
    validated["quick_wins"] = quick_wins(validated["findings"], validated["recommendations"])
    flagged = reported_check_ids(validated["findings"] + validated["recommendations"])
    kept = [w for w in passed if not flagged & set(w.get("check_ids") or ())]
    validated["whats_working"] = [dict(w, id=f"W-{index:03d}") for index, w in enumerate(kept, 1)]
    return validated
