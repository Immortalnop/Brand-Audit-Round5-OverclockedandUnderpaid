"""run_audit.py -- entrypoint: validate input, acquire once, schedule the DAG,
enforce budgets, merge, prioritize, generate recommendations, validate, emit the
report.

Skill folder names contain hyphens (agentskills.io convention) so this module wires
sibling scripts via sys.path rather than hyphenated package imports.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError, wait
from datetime import datetime, timezone
from time import monotonic
from urllib.parse import urlparse
try:
    from dotenv import load_dotenv
except ImportError:  # standard-library default; .env loading is optional
    def load_dotenv(*_args, **_kwargs):
        return False

load_dotenv()  # optional local-development convenience; production uses environment variables


def _progress(msg):
    """Progress to stderr only. The CLI enables it by default; API callers use
    AUDIT_PROGRESS=1. Stdout stays pure JSON for the evaluation harness.
    A long crawl of a large site is work, not a hang, and this makes that visible.
    """
    if os.environ.get("AUDIT_PROGRESS") == "1":
        sys.stderr.write("[audit] " + msg + "\n")
        sys.stderr.flush()

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for _rel in (
    "common",
    "skills/audit-orchestrator/scripts",
    "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts",
    "skills/engagement-audit/scripts",
    "skills/entity-corroboration-agent/scripts",
):
    _p = os.path.join(_ROOT, _rel)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from constants import DEFAULT_LIMITS
from models import make_deadline, _jsonable
from instrumentation import Instrumentation
from capabilities import detect_capabilities, capability_report

from acquire_site import acquire_site
from merge_findings import merge_findings
from prioritize_findings import prioritize_findings
from generate_recommendations import generate_recommendations
from validate_report import validate_report
from execution_summary import derive_execution_status, derive_limitations, overall_confidence

from analyze_crawlability import analyze_crawlability
from analyze_directives import analyze_directives
from analyze_metadata import analyze_metadata
from analyze_performance import analyze_performance
from analyze_answer_content import analyze_answer_content
from analyze_rendering import analyze_rendering
from analyze_machine_readability import analyze_machine_readability
from check_ai_crawler_access import check_ai_crawler_access
from check_llms_txt import check_llms_txt
from analyze_non_text import analyze_non_text

from extract_claims import extract_claims
from identify_important_facts import identify_important_facts
from resolve_entity_identity import resolve_entity_identity
from assess_freshness import assess_freshness
from corroborate_claims import corroborate_claims
from assess_external_footprint import assess_external_footprint
from check_knowledge_graph import check_knowledge_graph

from build_site_graph import build_site_graph
from analyze_engagement import analyze_engagement

from ingest_agent_findings import ingest_agent_findings

# Per-worker timeout used only to *detect and record* a hung specialist so the
# instrumentation layer can report it; the shared AuditDeadline remains the source
# of truth for stage budgets.
_WORKER_TIMEOUT_S = 30


def validate_input(url: str) -> str:
    p = urlparse(url)
    if not p.scheme:
        url = "https://" + url
        p = urlparse(url)
    if not p.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return url


def _await_result(future, name, stage, instrumentation):
    try:
        return future.result(timeout=_WORKER_TIMEOUT_S)
    except FutureTimeoutError:
        instrumentation.record_worker_timeout(stage, name)
        return {"skill": name, "status": "insufficient_evidence", "findings": [], "metrics": {},
                "warnings": [f"specialist '{name}' exceeded {_WORKER_TIMEOUT_S}s and was abandoned"],
                "coverage": {"pages_analyzed": 0, "pages_skipped": 0,
                             "queries_attempted": 0, "queries_completed": 0}}
    except Exception as exc:
        return {"skill": name, "status": "failed", "findings": [], "metrics": {},
                "warnings": [f"specialist failed: {exc}"],
                "coverage": {"pages_analyzed": 0, "pages_skipped": 0,
                             "queries_attempted": 0, "queries_completed": 0}}


def _run_jobs(jobs, deadline, limits, instrumentation, stage):
    pool = ThreadPoolExecutor(max_workers=limits.MAX_ANALYSIS_WORKERS)
    futures = {name: pool.submit(fn) for name, fn in jobs.items()}
    budget = max(0., min(_WORKER_TIMEOUT_S, deadline.remaining_seconds() - min(20., limits.FINALIZATION_RESERVE_S, deadline.remaining_seconds() * .1)))
    done, pending = wait(futures.values(), timeout=budget)
    results = {}
    for name, future in futures.items():
        if future in done:
            results[name] = _await_result(future, name, stage, instrumentation)
        else:
            instrumentation.record_worker_timeout(stage, name)
            future.cancel()
            results[name] = {"skill": name, "status": "insufficient_evidence", "findings": [], "metrics": {}, "data": {}, "warnings": [f"{name}: stage deadline reached"]}
    pool.shutdown(wait=False, cancel_futures=True)
    # The outer process watchdog stops abandoned workers after the report is received.
    return results


def run_independent_batch(artifacts, deadline, limits, capabilities, instrumentation):
    instrumentation.start_stage("independent_batch")
    jobs = {
        "crawlability": lambda: analyze_crawlability(artifacts, deadline),
        "directives": lambda: analyze_directives(artifacts, deadline),
        "metadata": lambda: analyze_metadata(artifacts, deadline),
        "performance": lambda: analyze_performance(artifacts, deadline),
        "rendering": lambda: analyze_rendering(artifacts, deadline, limits, capabilities),
        "machine_readability": lambda: analyze_machine_readability(artifacts, deadline),
        "ai_crawler_access": lambda: check_ai_crawler_access(artifacts, deadline),
        "llms_txt": lambda: check_llms_txt(artifacts, deadline),
        "non_text": lambda: analyze_non_text(artifacts, deadline),
        "claims": lambda: extract_claims(artifacts, deadline),
        "entity_identity": lambda: resolve_entity_identity(artifacts, deadline),
        "site_graph": lambda: build_site_graph(artifacts, deadline),
    }
    results = _run_jobs(jobs, deadline, limits, instrumentation, "independent_batch")
    instrumentation.end_stage("independent_batch")
    return results


def run_dependent_batch(facts, entity_identity, artifacts, site_graph, rendering_result,
                         deadline, limits, instrumentation, capabilities, claims=None):
    instrumentation.start_stage("dependent_batch")
    jobs = {
        "freshness": lambda: assess_freshness(facts, artifacts, deadline, claims),
        "answer_content": lambda: analyze_answer_content(artifacts, entity_identity, deadline),
        "corroboration": lambda: corroborate_claims(facts, entity_identity, artifacts, deadline, limits, instrumentation),
        "footprint": lambda: assess_external_footprint(artifacts, entity_identity, deadline, limits, instrumentation),
        "knowledge_graph": lambda: check_knowledge_graph(artifacts, entity_identity, deadline, limits, instrumentation),
        "engagement": lambda: analyze_engagement(artifacts, site_graph, rendering_result, deadline),
        "agent_corroboration": lambda: ingest_agent_findings(artifacts, entity_identity, deadline, capabilities),
    }
    results = _run_jobs(jobs, deadline, limits, instrumentation, "dependent_batch")
    instrumentation.end_stage("dependent_batch")
    return results


def _run_audit_impl(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets: bool = False) -> dict:
    """allow_private_targets defaults to False (safe): the CLI and any production
    caller never sets it. It exists only so tests can point the audit at a local
    ThreadingHTTPServer on 127.0.0.1 without weakening the default SSRF policy."""
    site_url = validate_input(site_url)
    deadline = make_deadline(limits)
    instrumentation = Instrumentation()
    capabilities = detect_capabilities()

    _progress("acquiring " + site_url)
    artifacts = acquire_site(site_url, deadline, limits, instrumentation,
                              allow_private_targets=allow_private_targets)
    _progress("acquired " + str(len(artifacts.pages)) + " page(s); running analysis")

    independent = run_independent_batch(artifacts, deadline, limits, capabilities, instrumentation)

    # Mandatory sequential step, wired into the executable schedule -- not only the
    # architecture diagram. Consumes extract_claims' output.
    instrumentation.start_stage("identify_important_facts")
    facts = identify_important_facts(independent["claims"], deadline)
    instrumentation.end_stage("identify_important_facts")

    dependent = run_dependent_batch(
        facts, independent["entity_identity"], artifacts,
        independent["site_graph"], independent["rendering"], deadline, limits, instrumentation,
        capabilities, claims=independent["claims"],
    )
    _progress("analysis complete; merging and validating report")

    skill_results = [
        independent["metadata"], independent["performance"], dependent["answer_content"],
        independent["crawlability"], independent["directives"], independent["rendering"], independent["machine_readability"],
        independent["ai_crawler_access"], independent["llms_txt"], independent["non_text"],
        dependent["freshness"], dependent["corroboration"], dependent["footprint"], dependent["knowledge_graph"],
        dependent["engagement"],
        dependent["agent_corroboration"],
    ]

    merged = merge_findings(skill_results)
    prioritized = prioritize_findings(merged)
    for idx, finding in enumerate(prioritized, 1):
        finding["id"] = f"F-{idx:03d}"
    recommendations = generate_recommendations(skill_results, prioritized)

    memory_peak_mb = instrumentation.stop_memory_tracking_mb()
    telemetry = instrumentation.as_dict(memory_peak_mb)

    acq_coverage = artifacts.acquisition_metadata.get("coverage", {})
    coverage = {
        # Factual, non-equated coverage counts (Round-3 handout, Priority 2 #3):
        # discovered/fetched/analyzed are different numbers and must not collapse
        # into one len(pages) reused three times.
        "pages_discovered": acq_coverage.get("urls_discovered", len(artifacts.pages)),
        "pages_fetched_attempted": acq_coverage.get("urls_fetched_attempted", len(artifacts.pages)),
        "pages_fetched_ok": acq_coverage.get("urls_fetched_ok", len(artifacts.pages)),
        "pages_analyzed": acq_coverage.get("urls_analyzed", len(artifacts.pages)),
        "pages_blocked": acq_coverage.get("urls_blocked", 0),
        "robots_permission": "unknown" if artifacts.robots_data.get("conservative_fail_closed") else "disallowed" if artifacts.robots_data.get("general_disallow") else "evaluated" if artifacts.robots_data.get("status") in ("ok","absent") else "unknown",
        "transport_diagnostics": artifacts.acquisition_metadata.get("transport_diagnostics", []),
        "transport_environment": artifacts.acquisition_metadata.get("transport_environment", {}),
        "robots_attempt_outcomes": artifacts.robots_data.get("attempt_outcomes", []),
        "pages_timed_out": acq_coverage.get("urls_timed_out", 0),
        "pages_failed_other": acq_coverage.get("urls_failed_other", 0),
        "pages_never_attempted": acq_coverage.get("urls_never_attempted", 0),
        "pages_skipped": telemetry["pages_skipped"],
        "skip_reason_counts": acq_coverage.get("skip_reason_counts", {}),
        "rendered_pages": independent["rendering"].get("metrics", {}).get("rendered_pages", 0),
        "non_text_media": dict((artifacts.media_data or {}).get("summary", {})),
        "external_claims_checked": dependent["corroboration"].get("metrics", {}).get("claims_checked", 0),
        "external_footprint_queries": dependent["footprint"].get("metrics", {}).get("queries_attempted", 0),
        "knowledge_graph": {k: v for k, v in dependent["knowledge_graph"].get("metrics", {}).items()
                            if k in ("lookup", "organization_pages", "declared_wikidata", "declared_wikipedia",
                                     "verdict", "entity", "robots", "lookup_failures")},
        "freshness_update_signals": {k: v for k, v in dependent["freshness"].get("metrics", {}).items()
                                     if k.startswith(("sitemap_lastmod", "update_dates_from", "last_modified",
                                                      "pages_with_update_date", "page_update_date"))},
        "agent_corroboration_stage": dependent["agent_corroboration"].get("metrics", {}).get("agent_stage", "not_supplied"),
        "external_fetches": telemetry["external_fetches_attempted"],
        "identity_confidence": independent["entity_identity"].get("data", {}).get("confidence", 0.0),
        "memory_budget_used_mb": memory_peak_mb,  # None if unmeasured, never a fabricated 0
        "runtime_seconds": round(monotonic() - deadline.started_monotonic, 3),  # measured, not derived from the budget
        "deadline_reached": deadline.expired(),
        "capabilities": capability_report(capabilities),
        "instrumentation": telemetry,
    }

    report = {
        "site": site_url,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "summary": {},
        "coverage": coverage,
        "warnings": list(artifacts.warnings) + [w for result in skill_results for w in result.get("warnings", [])],
        "findings": prioritized,
        "recommendations": recommendations,
    }

    # Never-empty, never-misleading report fields (Round-3 handout item 6): every
    # audit -- success, degraded, or deadline-truncated -- gets a real
    # execution_status, a limitations list derived from actual telemetry (not
    # boilerplate), and an overall confidence score with its method shown.
    execution_status = derive_execution_status(deadline, skill_results, telemetry["worker_timeout_events"])
    if artifacts.robots_data.get("conservative_fail_closed") and execution_status == "completed":
        execution_status = "degraded"
    report["execution_status"] = execution_status
    report["limitations"] = derive_limitations(artifacts, capabilities, coverage, execution_status)
    report["confidence"] = overall_confidence(coverage, execution_status)

    report["coverage_limited"] = {"sample_only": True, "pages_not_analyzed": max(0, coverage["pages_discovered"]-coverage["pages_analyzed"]), "unassessed_capabilities": [k for k,v in capabilities.items() if not v]}
    report["top_actions"] = [{"finding_id": f["id"], "summary": f["suggested_action"]["summary"], "priority": f["suggested_action"]["priority"]} for f in prioritized if f["finding_type"] == "defect"][:3]
    return _jsonable(validate_report(report, strict_catalog=True))


def run_audit(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets=False) -> dict:
    """Public bounded API. A stalled DNS call or analysis cannot hold the caller indefinitely."""
    from subprocess_isolation import run_isolated
    from dataclasses import replace
    import math
    if not math.isfinite(limits.TOTAL_AUDIT_TIMEOUT_S) or limits.TOTAL_AUDIT_TIMEOUT_S <= 0:
        raise ValueError("Audit timeout must be a positive finite number")
    limits=replace(limits,TOTAL_AUDIT_TIMEOUT_S=min(270.,limits.TOTAL_AUDIT_TIMEOUT_S))
    site_url = validate_input(site_url)
    _progress("started; total limit " + str(limits.TOTAL_AUDIT_TIMEOUT_S) + "s")
    result = run_isolated(_run_audit_impl, args=(site_url, limits, allow_private_targets),
                          timeout_s=limits.TOTAL_AUDIT_TIMEOUT_S,
                          on_wait=lambda elapsed: _progress(f"working ({elapsed:.0f}s elapsed); Ctrl+C cancels cleanly"))
    if result.ok:
        return result.value
    # A timeout is an execution limitation, never a fabricated site defect.
    return validate_report({
        "site": site_url, "audited_at": datetime.now(timezone.utc).isoformat(), "summary": {},
        "findings": [], "recommendations": generate_recommendations([], []),
        "coverage": {"pages_discovered": 0, "pages_analyzed": 0, "deadline_reached": result.timed_out,
                     "measurements_unavailable": True, "cancelled": result.cancelled},
        "execution_status": "partial_deadline_reached" if result.timed_out else "degraded",
        "limitations": ["The audit worker did not return a complete report. No site-level conclusions can be drawn.", result.error or "Worker failed"],
        "confidence": {"score": 0.0, "method": "no completed audit evidence"},
        "warnings": [result.error or "Worker failed"]}, strict_catalog=True)


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(
        description="Brand AI-Readiness Audit. Emits one JSON report to stdout.")
    parser.add_argument("site", nargs="?", default="https://example.com",
                        help="Target URL or bare domain to audit.")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Override the total audit wall-clock cap in seconds "
                             "(default 270, handout limit 300). Lower it for a quick "
                             "interactive run on a large site.")
    parser.add_argument("-v", "--progress", action="store_true",
                        help="Print stage progress to stderr (stdout stays pure JSON).")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress on stderr; JSON output is unchanged.")
    parsed = parser.parse_args(argv)
    import math
    if parsed.timeout is not None and (not math.isfinite(parsed.timeout) or parsed.timeout<=0):
        parser.error("--timeout must be a positive finite number")
    if not parsed.quiet:
        os.environ["AUDIT_PROGRESS"] = "1"
    else:
        os.environ["AUDIT_PROGRESS"] = "0"
    active_limits = DEFAULT_LIMITS
    if parsed.timeout is not None:
        from dataclasses import replace as _dc_replace
        active_limits = _dc_replace(DEFAULT_LIMITS, TOTAL_AUDIT_TIMEOUT_S=parsed.timeout)
    try:
        report=run_audit(parsed.site, limits=active_limits)
        print(json.dumps(report, indent=2, default=str))
        if report.get("coverage",{}).get("cancelled"):raise SystemExit(130)
    except KeyboardInterrupt:
        print("[audit] cancelled",file=sys.stderr)
        raise SystemExit(130)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
