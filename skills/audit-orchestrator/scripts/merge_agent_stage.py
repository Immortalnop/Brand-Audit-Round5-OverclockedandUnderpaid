"""merge_agent_stage.py -- fold the agent stage (AG-01 to AG-06) into a saved report.

The deterministic audit runs first and writes its report and, with
--evidence-out, the bounded evidence packet (common/agent_evidence.py). The
calling agent then performs the entity-corroboration-agent checks from that
packet and writes one outcome per check (the outcome envelope). This module
merges the envelope into the saved report without crawling again: it makes no
request of any kind and reads nothing but the files it is given, so the merge
takes well under a second.

Before anything is written the envelope is bound and validated
(ingest_agent_findings.validate_envelope): its audit_id and snapshot_sha256 must
match the report and the packet, every evidence reference must name a packet
record, and each pass or finding must carry the evidence its check needs. Any
failure raises ReportMergeError and leaves the report as it was.

The merge goes through the same steps as a live audit: every entry is rebuilt by
the shared finding factory (catalog wording and Invariant I-1), folded into the
finding that already reports it (merge_findings.fold_into), and the findings are
prioritized, numbered and validated again. The recommendations, impact x effort
plan, top actions and quick wins are rebuilt from the new findings. What the
merge cannot rebuild without the site snapshot is kept from the saved report:
fix snippets on the findings it already had, the confidence score (it rates the
crawl, which did not change), and the passed checks, less any that a merged
finding now contradicts.

Only the limitations of checks the envelope actually assessed are cleared. The
legacy findings array is still merged, as legacy_partial: it clears none.
"""
import copy
import math
from datetime import datetime, timezone

from execution_summary import AG04_NOT_SUPPLIED, AG05_NOT_SUPPLIED, AG06_NOT_SUPPLIED
from generate_recommendations import generate_recommendations, is_finding_reference
from ingest_agent_findings import (NOT_SUPPLIED_WARNING, LEGACY_WARNING, EnvelopeError, build_agent_findings,
                                   legacy_checks, stage_record, validate_envelope)
from agent_evidence import AG_CHECKS
from merge_findings import fold_into
from prioritize_findings import annotate_action_plan, prioritize_findings, quick_wins, top_actions
from validate_report import REQUIRED_FINDING_FIELDS, validate_report
from whats_working import reported_check_ids
from json_boundary import validate_report_shape

# The limitation each agent check lifts once it is actually assessed.
_LIMITATION_OF_CHECK = {"AG-04": AG04_NOT_SUPPLIED, "AG-05": AG05_NOT_SUPPLIED, "AG-06": AG06_NOT_SUPPLIED}
_MERGED_STAGES = {"ingested", "legacy_partial", "partial", "complete", "not_run"}


class ReportMergeError(ValueError):
    """The saved report cannot take agent findings."""


def _check_report(report):
    """Raise ReportMergeError unless report is a complete audit report that
    analyzed at least one page and has no agent findings merged yet."""
    try:
        validate_report_shape(report)
    except ValueError as exc:
        raise ReportMergeError(str(exc)) from exc
    if not isinstance(report, dict) or not isinstance(report.get("coverage"), dict) \
            or not isinstance(report.get("findings"), list) or not isinstance(report.get("recommendations"), list):
        raise ReportMergeError("the file is not an audit report written by run_audit.py")
    for finding in report["findings"]:
        if not isinstance(finding, dict) or REQUIRED_FINDING_FIELDS - finding.keys():
            raise ReportMergeError("the report holds a finding without the fields run_audit.py writes; "
                                   "merge into an unedited report")
        for key in ('affected_pages', 'check_ids'):
            if key in finding and (not isinstance(finding[key], list) or
                                   any(not isinstance(v, str) for v in finding[key])):
                raise ReportMergeError(f'finding.{key} must be a list of strings')
        if not isinstance(finding.get('suggested_action'), dict) or not isinstance(finding.get('provenance'), dict):
            raise ReportMergeError('finding action/provenance must be objects')
    for key in ('warnings', 'limitations'):
        if key in report and (not isinstance(report[key], list) or any(not isinstance(v, str) for v in report[key])):
            raise ReportMergeError(f'report.{key} must be a list of strings')
    coverage = report["coverage"]
    submitted = (coverage.get("agent_stage") or {}).get("submission_status") \
        if isinstance(coverage.get("agent_stage"), dict) else None
    stage = coverage.get('agent_corroboration_stage')
    if stage is not None and not isinstance(stage, str):
        raise ReportMergeError('agent_corroboration_stage must be a string')
    count = coverage.get('pages_analyzed')
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ReportMergeError('pages_analyzed must be a nonnegative integer')
    if submitted in ("legacy", "envelope") or stage in _MERGED_STAGES:
        raise ReportMergeError("agent findings were already merged into this report; merge into the report "
                               "the audit wrote")
    if not coverage.get("pages_analyzed"):
        # As in a live audit, where only robots.txt, llms.txt, sitemap and TLS
        # findings are kept when nothing on the site was assessed.
        raise ReportMergeError("the audit analyzed no page of the site, so agent findings about it cannot be "
                               "merged; run the audit again first")


def workflow_elapsed(timing, now):
    """How long the whole host workflow took, from the audit's start to this
    merge, against its target. Measured, not enforced: the agent stage runs in
    the host. None when the report has no timing (written before it existed)."""
    if not isinstance(timing, dict):
        return None
    try:
        started = datetime.fromisoformat(timing["session_started_at"])
        if isinstance(timing['workflow_target_s'], bool):
            return None
        target = float(timing["workflow_target_s"])
        agent_deadline = datetime.fromisoformat(timing["agent_deadline_at"])
        if not math.isfinite(target) or target <= 0 or started.tzinfo is None or agent_deadline.tzinfo is None:
            return None
    except (KeyError, TypeError, ValueError):
        return None
    elapsed = (now - started).total_seconds()
    if elapsed<0:return None
    core = timing.get('core_elapsed_s')
    agent_elapsed = max(0., elapsed - core) if type(core) in (int, float) and math.isfinite(core) else None
    if timing.get('core_finished_at'):
        try:
            finished=datetime.fromisoformat(timing['core_finished_at'])
            if finished.tzinfo is None or finished<started or finished>now:return None
            agent_elapsed=max(0.,(now-finished).total_seconds())
        except (TypeError,ValueError):return None
    return {"workflow_elapsed_s": round(elapsed, 3), "workflow_target_s": target,
            "within_workflow_target": elapsed <= target,
            "after_agent_deadline": now > agent_deadline,
            'agent_elapsed_s': round(agent_elapsed, 3) if agent_elapsed is not None else None,
            'within_agent_deadline': now <= agent_deadline,
            "core_elapsed_s": timing.get("core_elapsed_s"),
            'preparation_elapsed_s':timing.get('preparation_elapsed_s',0),
            "measured": "from "+('the host first tool' if timing.get('clock_scope')=='host_first_tool' else 'the audit start')+" to this merge; rendering and final reply are not included; host time is measured but not enforced"}


def _finish(report, added, record, info, strict_pages=False, warnings=(), limitations=()):
    """report (a copy, changed in place) with added folded in and every derived
    section rebuilt; record is the coverage.agent_stage block."""
    coverage = report["coverage"]
    findings, folded = fold_into(report["findings"], added, strict_pages=strict_pages)

    prioritized = prioritize_findings(findings)
    for index, finding in enumerate(prioritized, 1):
        finding["id"] = f"F-{index:03d}"
        finding["coverage"] = {"affected_pages": len(finding.get("affected_pages") or ()),
                               "pages_analyzed": coverage.get("pages_analyzed", 0),
                               "pages_discovered": coverage.get("pages_discovered", 0)}

    coverage["agent_corroboration_stage"] = ("legacy_partial" if record["submission_status"] == "legacy"
                                             else record["assessment_status"])
    coverage["agent_stage"] = record
    coverage["agent_checks_assessed"] = list(record["checks_assessed"])
    now = datetime.now(timezone.utc)
    coverage["agent_corroboration"] = dict(info, merged_at=now.isoformat(),
                                           findings_ingested=len(added), findings_folded_into_existing=folded,
                                           findings_added=len(added) - folded)
    elapsed = workflow_elapsed(report.get("timing"), now)
    if elapsed is not None:
        coverage["agent_corroboration"]["workflow_timing"] = elapsed
    report["findings"] = prioritized
    report["recommendations"] = generate_recommendations([], prioritized)
    report["warnings"] = [w for w in report.get("warnings") or () if w != NOT_SUPPLIED_WARNING] + list(warnings)
    lifted = [_LIMITATION_OF_CHECK[c] for c in record["checks_assessed"] if c in _LIMITATION_OF_CHECK]
    report["limitations"] = [line for line in report.get("limitations") or ()
                             if not any(mark in str(line) for mark in lifted)] + list(limitations)
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


def merge_agent_findings(report, items, source=None):
    """A new report: report with the raw legacy agent entries in items merged
    in, as legacy_partial. source names the agent findings file in
    coverage.agent_corroboration. The input report is not changed. Raises
    ReportMergeError when the report cannot take agent findings."""
    _check_report(report)
    items = list(items or ())
    report = copy.deepcopy(report)
    origin = report["coverage"].get("audited_url") or report.get("site")
    added = build_agent_findings(items, origin)
    record = stage_record("legacy", legacy_checks(added))
    info = {"merged_from": source, "submission": "legacy", "findings_supplied": len(items)}
    return _finish(report, added, record, info, warnings=[LEGACY_WARNING])


def merge_agent_envelope(report, envelope, packet, source=None, packet_source=None):
    """A new report: report with the outcome envelope merged in. packet is the
    evidence packet the same audit exported. The input report is not changed.
    Raises ReportMergeError, with every reason, when the report cannot take it
    or the envelope fails validation; nothing is merged then."""
    _check_report(report)
    try:
        validated = validate_envelope(envelope, report, packet)
    except EnvelopeError as exc:
        raise ReportMergeError("the outcome envelope was rejected: " + "; ".join(exc.reasons)) from exc
    report = copy.deepcopy(report)
    checks = validated["checks"]
    record = stage_record("envelope", checks, capabilities=validated["capabilities"],
                          audit_id=report.get("audit_id"), snapshot_sha256=report.get("snapshot_sha256"))
    warnings = [f"Agent check {c}: {r['severity_capped']}" for c, r in checks.items() if r.get("severity_capped")]
    limitations = [f"Agent check {c} ({AG_CHECKS[c]['name']}) was not assessed: {r['reason']}"
                   for c, r in checks.items() if r["outcome"] == "not_assessed"]
    limitations += [f"Agent check {c} ({AG_CHECKS[c]['name']}) reported an error: {r['reason']}"
                    for c, r in checks.items() if r["outcome"] == "error"]
    info = {"merged_from": source, "evidence_packet": packet_source, "submission": "envelope",
            "findings_supplied": sum(r["outcome"] == "finding" for r in checks.values())}
    return _finish(report, validated["findings"], record, info, strict_pages=True,
                   warnings=warnings, limitations=limitations)
