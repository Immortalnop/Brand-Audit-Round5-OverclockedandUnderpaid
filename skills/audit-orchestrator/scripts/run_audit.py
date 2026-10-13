"""run_audit.py -- entrypoint: validate input, acquire once, schedule the DAG,
enforce budgets, merge, prioritize, generate recommendations, validate, emit the
report.

Skill folder names contain hyphens (agentskills.io convention) so this module wires
sibling scripts via sys.path rather than hyphenated package imports.
"""
import os
import sys
import uuid
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
from json_boundary import validate_tree
from packet_contract import emitted_json, emitted_bytes, fit_packet, nonready_packet
from instrumentation import Instrumentation
from capabilities import detect_capabilities, capability_report
from field_vitals import start_field_lookup

from acquire_site import acquire_site
from merge_findings import merge_findings, fold_into
from prioritize_findings import prioritize_findings, annotate_action_plan, top_actions, quick_wins
from fix_snippets import attach_fix_snippets
from generate_recommendations import generate_recommendations, is_finding_reference
from validate_report import validate_report
from whats_working import whats_working
from execution_summary import (derive_execution_status, derive_limitations, overall_confidence,
                               identity_resolution, unfinished_confidence, discovery_state)

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
from analyze_media_text import analyze_media_text
from analyze_citation_schema import analyze_citation_schema
from analyze_web_vitals import analyze_web_vitals
from analyze_international import analyze_international
from analyze_graphics_text import analyze_graphics_text
from analyze_image_context import analyze_image_context
from analyze_image_weight import analyze_image_weight
from analyze_answer_format import analyze_answer_format
from analyze_context_signals import analyze_context_signals

from extract_claims import extract_claims
from identify_important_facts import identify_important_facts
from resolve_entity_identity import resolve_entity_identity
from assess_freshness import assess_freshness
from corroborate_claims import corroborate_claims
from assess_external_footprint import assess_external_footprint
from check_knowledge_graph import check_knowledge_graph
from check_off_site_profiles import check_off_site_profiles
from analyze_authorship import analyze_authorship
from check_offer_expiry import check_offer_expiry
from check_fact_consistency import check_fact_consistency

from build_site_graph import build_site_graph
from analyze_engagement import analyze_engagement
from analyze_accessibility import analyze_accessibility
from analyze_overlays import analyze_overlays
from analyze_context_retention import analyze_context_retention

from ingest_agent_findings import ingest_agent_findings, not_supplied_record
from agent_evidence import build_evidence_packet, code_version, snapshot_digest
import network_budget

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
        "media_text": lambda: analyze_media_text(artifacts, deadline),
        "citation_schema": lambda: analyze_citation_schema(artifacts, deadline),
        "authorship": lambda: analyze_authorship(artifacts, deadline),
        "claims": lambda: extract_claims(artifacts, deadline),
        "entity_identity": lambda: resolve_entity_identity(artifacts, deadline),
        "site_graph": lambda: build_site_graph(artifacts, deadline),
        "international": lambda: analyze_international(artifacts, deadline),
        "graphics_text": lambda: analyze_graphics_text(artifacts, deadline),
        "image_context": lambda: analyze_image_context(artifacts, deadline),
        "image_weight": lambda: analyze_image_weight(artifacts, deadline),
        "accessibility": lambda: analyze_accessibility(artifacts, deadline),
        "overlays": lambda: analyze_overlays(artifacts, deadline),
        "answer_format": lambda: analyze_answer_format(artifacts, deadline),
        "context_signals": lambda: analyze_context_signals(artifacts, deadline),
        "context_retention": lambda: analyze_context_retention(artifacts, deadline),
        "offer_expiry": lambda: check_offer_expiry(artifacts, deadline),
        "fact_consistency": lambda: check_fact_consistency(artifacts, deadline),
    }
    results = _run_jobs(jobs, deadline, limits, instrumentation, "independent_batch")
    instrumentation.end_stage("independent_batch")
    return results


def run_dependent_batch(facts, entity_identity, artifacts, site_graph, rendering_result,
                         deadline, limits, instrumentation, capabilities, claims=None, field_handle=None):
    instrumentation.start_stage("dependent_batch")
    jobs = {
        "freshness": lambda: assess_freshness(facts, artifacts, deadline, claims),
        "answer_content": lambda: analyze_answer_content(artifacts, entity_identity, deadline),
        "corroboration": lambda: corroborate_claims(facts, entity_identity, artifacts, deadline, limits, instrumentation),
        "footprint": lambda: assess_external_footprint(artifacts, entity_identity, deadline, limits, instrumentation),
        "knowledge_graph": lambda: check_knowledge_graph(artifacts, entity_identity, deadline, limits, instrumentation),
        "off_site_profiles": lambda: check_off_site_profiles(artifacts, entity_identity, deadline, limits, instrumentation),
        "web_vitals": lambda: analyze_web_vitals(artifacts, deadline, field_handle),
        "engagement": lambda: analyze_engagement(artifacts, site_graph, rendering_result, deadline),
        "agent_corroboration": lambda: ingest_agent_findings(artifacts, entity_identity, deadline, capabilities),
    }
    results = _run_jobs(jobs, deadline, limits, instrumentation, "dependent_batch")
    instrumentation.end_stage("dependent_batch")
    return results


# Checks that read robots.txt, llms.txt, the sitemap or the TLS handshake rather
# than page content. When no page could be analyzed only these are reported:
# a finding drawn from zero pages (for example "none of the crawled pages link a
# review profile") would describe the crawl, not the site.
SITE_LEVEL_CHECKS = frozenset({
    "ai-crawler-blocked", "ai-crawler-section-blocked", "ai-crawler-unchecked", "robots-block",
    "robots-unreachable", "no-llms-txt", "llms-txt-invalid", "llms-txt-broken-links", "llms-txt-unchecked",
    "sitemap-unavailable", "tls-health",
})


def site_level_only(skill_results):
    """Copies of skill_results keeping only findings of SITE_LEVEL_CHECKS."""
    def keep(finding):
        check_id = finding.get("check_id") or (finding.get("provenance") or {}).get("rule_id")
        return check_id in SITE_LEVEL_CHECKS
    return [dict(result, findings=[f for f in result.get("findings", []) if keep(f)]) for result in skill_results]


def _run_audit_impl(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets: bool = False,
                    export_evidence: bool = False, audit_id: str = None):
    """allow_private_targets defaults to False (safe): the CLI and any production
    caller never sets it. It exists only so tests can point the audit at a local
    ThreadingHTTPServer on 127.0.0.1 without weakening the default SSRF policy.
    Returns the report, or with export_evidence {"report", "evidence_packet"}:
    the bounded agent evidence packet is built here, while the snapshot exists,
    and only the packet crosses the isolation boundary.

    Every transport of the audit charges one shared network ledger
    (common/network_budget.py), reported as coverage.network_budget."""
    budget = network_budget.activate(network_budget.from_limits(limits))
    try:
        return _audit_in_worker(site_url, limits, allow_private_targets, export_evidence, audit_id, budget)
    finally:
        network_budget.deactivate(budget)


def _audit_in_worker(site_url, limits, allow_private_targets, export_evidence, audit_id, budget):
    site_url = validate_input(site_url)
    audit_id = audit_id or uuid.uuid4().hex
    deadline = make_deadline(limits)
    instrumentation = Instrumentation()
    capabilities = detect_capabilities()
    # Optional Core Web Vitals field data: started now so the API's latency
    # overlaps the crawl. None unless PAGESPEED_API_KEY is configured.
    field_handle = start_field_lookup(site_url, deadline, limits, instrumentation,
                                      allow_private_targets=allow_private_targets)

    _progress("acquiring " + site_url)
    artifacts = acquire_site(site_url, deadline, limits, instrumentation,
                              allow_private_targets=allow_private_targets)
    _progress("acquired " + str(len(artifacts.pages)) + " page(s); running analysis")
    # Binds the report, the evidence packet and any agent outcome envelope to
    # these acquired observations.
    snapshot_sha256 = snapshot_digest(artifacts)

    independent = run_independent_batch(artifacts, deadline, limits, capabilities, instrumentation)

    # Mandatory sequential step, wired into the executable schedule -- not only the
    # architecture diagram. Consumes extract_claims' output.
    instrumentation.start_stage("identify_important_facts")
    facts = identify_important_facts(independent["claims"], deadline)
    instrumentation.end_stage("identify_important_facts")

    dependent = run_dependent_batch(
        facts, independent["entity_identity"], artifacts,
        independent["site_graph"], independent["rendering"], deadline, limits, instrumentation,
        capabilities, claims=independent["claims"], field_handle=field_handle,
    )
    _progress("analysis complete; merging and validating report")

    skill_results = [
        independent["metadata"], independent["performance"], dependent["answer_content"],
        independent["crawlability"], independent["directives"], independent["rendering"], independent["machine_readability"],
        independent["ai_crawler_access"], independent["llms_txt"], independent["non_text"],
        independent["media_text"], independent["citation_schema"], independent["authorship"],
        dependent["freshness"], dependent["corroboration"], dependent["footprint"], dependent["knowledge_graph"],
        dependent["off_site_profiles"], dependent["web_vitals"],
        dependent["engagement"],
        dependent["agent_corroboration"],
        independent["international"], independent["graphics_text"], independent["image_context"],
        independent["image_weight"], independent["accessibility"],
        independent["overlays"], independent["answer_format"], independent["context_signals"],
        independent["context_retention"], independent["offer_expiry"], independent["fact_consistency"],
    ]

    acq_coverage = artifacts.acquisition_metadata.get("coverage", {})
    pages_analyzed = acq_coverage.get("urls_analyzed", len(artifacts.pages))
    # No analyzed page: only checks that never read page content can be reported.
    if not pages_analyzed:
        merged = merge_findings(site_level_only(skill_results))
    else:
        # Agent findings fold into the script finding that already reports the
        # same check, exactly as run_audit.py --from-report merges them later.
        agent = dependent["agent_corroboration"]
        merged, _ = fold_into(merge_findings([r for r in skill_results if r is not agent]),
                              agent.get("findings") or [])
    prioritized = prioritize_findings(merged)
    for idx, finding in enumerate(prioritized, 1):
        finding["id"] = f"F-{idx:03d}"
    recommendations = generate_recommendations(skill_results, prioritized)

    memory_peak_mb = instrumentation.stop_memory_tracking_mb()
    telemetry = instrumentation.as_dict(memory_peak_mb)

    failure = artifacts.acquisition_metadata.get("acquisition_failure")
    coverage = {
        # Factual, non-equated coverage counts (Round-3 handout, Priority 2 #3):
        # discovered/fetched/analyzed are different numbers and must not collapse
        # into one len(pages) reused three times.
        "pages_discovered": acq_coverage.get("urls_discovered", len(artifacts.pages)),
        "pages_fetched_attempted": acq_coverage.get("urls_fetched_attempted", len(artifacts.pages)),
        "pages_fetched_ok": acq_coverage.get("urls_fetched_ok", len(artifacts.pages)),
        "pages_analyzed": pages_analyzed,
        "pages_blocked": acq_coverage.get("urls_blocked", 0),
        # Login pages: fetched, never analyzed, each listed with its signals.
        "pages_out_of_scope": acq_coverage.get("urls_out_of_scope", 0),
        "out_of_scope_pages": acq_coverage.get("out_of_scope_pages", []),
        "start_url_out_of_scope": acq_coverage.get("start_url_out_of_scope", False),
        # Bot-protection challenges: requested, never analyzed as site content.
        "pages_challenged": acq_coverage.get("urls_challenged", 0),
        "challenged_pages": acq_coverage.get("challenged_pages", []),
        "crawl_stopped_by_challenge": acq_coverage.get("crawl_stopped_by_challenge", False),
        # Waiting-room and queue pages: requested, never analyzed as site content.
        "pages_waiting_room": acq_coverage.get("urls_waiting_room", 0),
        "waiting_room_pages": acq_coverage.get("waiting_room_pages", []),
        "crawl_stopped_by_waiting_room": acq_coverage.get("crawl_stopped_by_waiting_room", False),
        # Of pages_analyzed: read in full, or cut by the byte budget or the parser
        # (positive observations count, absences do not).
        "pages_fully_observed": acq_coverage.get("urls_fully_observed", pages_analyzed),
        "pages_partially_observed": acq_coverage.get("urls_partially_observed", 0),
        # Requests that redirected to a page already analyzed, and requested URLs
        # recorded as redirect aliases of their final page.
        "pages_redirect_duplicates": acq_coverage.get("urls_redirect_duplicates", 0),
        "url_aliases": acq_coverage.get("url_aliases", 0),
        # How URLs were discovered, for judging how far the sample reaches.
        "sitemap_status": acq_coverage.get("sitemap_status", artifacts.sitemap_data.get("status")),
        "sitemap_url_entries": acq_coverage.get("sitemap_url_entries", 0),
        "sitemap_candidates": acq_coverage.get("sitemap_candidates", 0),
        "sitemap_partial": acq_coverage.get("sitemap_partial", False),
        "crawl_limit_reached": acq_coverage.get("crawl_limit_reached", False),
        # Why no page could be analyzed ({reason, stage, url, http_status, detail});
        # None whenever at least one page was analyzed.
        "acquisition_failure": dict(failure) if failure else None,
        "sections_discovered": acq_coverage.get("sections_discovered", 0),
        "sections_analyzed": acq_coverage.get("sections_analyzed", 0),
        "page_types_analyzed": acq_coverage.get("page_types_analyzed", []),
        # Set when the start URL redirected to another origin and that origin was
        # audited instead (acquire_site re-anchors once); None otherwise.
        "start_redirect": (dict(artifacts.acquisition_metadata["start_redirect"])
                           if artifacts.acquisition_metadata.get("start_redirect") else None),
        "audited_url": artifacts.site_url,
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
        "llms_txt": {k: v for k, v in independent["llms_txt"].get("metrics", {}).items()
                     if k.startswith(("llms_txt", "llms_full_txt"))},
        "off_site_profiles": {k: v for k, v in dependent["off_site_profiles"].get("metrics", {}).items()
                              if k in ("lookup", "same_as_links", "profile_outcomes", "profiles", "profiles_unverified",
                                       "review_platforms_linked", "review_platform_search", "robots",
                                       "business_kind", "review_platform_check")},
        "web_vitals": {k: v for k, v in dependent["web_vitals"].get("metrics", {}).items()
                       if k.startswith("web_vitals")},
        "freshness_update_signals": {k: v for k, v in dependent["freshness"].get("metrics", {}).items()
                                     if k.startswith(("sitemap_lastmod", "update_dates_from", "last_modified",
                                                      "pages_with_update_date", "page_update_date"))},
        "hreflang": dict(independent["international"].get("metrics", {})),
        "noscript": {k: v for k, v in independent["rendering"].get("metrics", {}).items() if k.startswith("noscript")},
        "graphics_text": dict(independent["graphics_text"].get("metrics", {})),
        "image_context": dict(independent["image_context"].get("metrics", {})),
        "image_weight": dict(independent["image_weight"].get("metrics", {})),
        "accessibility": dict(independent["accessibility"].get("metrics", {})),
        "overlays": dict(independent["overlays"].get("metrics", {})),
        "answer_format": dict(independent["answer_format"].get("metrics", {})),
        "context_signals": dict(independent["context_signals"].get("metrics", {})),
        "context_retention": dict(independent["context_retention"].get("metrics", {})),
        "offer_expiry": dict(independent["offer_expiry"].get("metrics", {})),
        "fact_consistency": dict(independent["fact_consistency"].get("metrics", {})),
        "ai_crawler_purposes": dict(independent["ai_crawler_access"].get("metrics", {}).get("ai_crawler_purposes") or {}),
        "agent_corroboration_stage": dependent["agent_corroboration"].get("metrics", {}).get("agent_stage", "not_supplied"),
        # Per-check agent outcomes: what was received and what was actually assessed.
        "agent_stage": dependent["agent_corroboration"].get("metrics", {}).get("stage_record") or not_supplied_record(),
        "external_fetches": telemetry["external_fetches_attempted"],
        "identity_confidence": independent["entity_identity"].get("data", {}).get("confidence", 0.0),
        # Why identity_confidence is what it is; the confidence explanation reads it.
        "identity_resolution": identity_resolution(independent["entity_identity"]),
        "memory_budget_used_mb": memory_peak_mb,  # None if unmeasured, never a fabricated 0
        "runtime_seconds": round(monotonic() - deadline.started_monotonic, 3),  # measured, not derived from the budget
        "deadline_reached": deadline.expired(),
        "capabilities": capability_report(capabilities),
        "instrumentation": telemetry,
        # The enforced shared allowance and what each stage used of it.
        "network_budget": budget.snapshot(),
    }
    # Whether the discovered URLs can stand for the site (True, False or
    # "unknown") and what the findings speak for.
    coverage.update(discovery_state(coverage))
    coverage["agent_checks_assessed"] = list(coverage["agent_stage"].get("checks_assessed") or ())

    # How much of the site each finding speaks for, stated beside its confidence
    # instead of being folded into it.
    for finding in prioritized:
        finding["coverage"] = {"affected_pages": len(finding.get("affected_pages") or ()),
                               "pages_analyzed": coverage["pages_analyzed"],
                               "pages_discovered": coverage["pages_discovered"]}

    report = {
        "site": site_url,
        "audit_id": audit_id,
        "snapshot_sha256": snapshot_sha256,
        "code_version": code_version(),
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
    if not pages_analyzed:
        # Nothing on the site was assessed, whatever else happened in the run.
        execution_status = "insufficient_evidence"
    report["execution_status"] = execution_status
    report["limitations"] = derive_limitations(artifacts, capabilities, coverage, execution_status)
    report["confidence"] = overall_confidence(coverage, execution_status)

    report["coverage_limited"] = {"sample_only": True, "pages_not_analyzed": max(0, coverage["pages_discovered"]-coverage["pages_analyzed"]), "unassessed_capabilities": [k for k,v in capabilities.items() if not v]}
    validated = validate_report(report, strict_catalog=True)
    # Ready-to-paste fixes and the impact x effort plan are added after
    # validation: enrichment rewrites suggested_action from the catalog.
    attach_fix_snippets(validated["findings"], validated["recommendations"], artifacts, independent["entity_identity"])
    # A recommendation that points at a finding has no action of its own to place.
    annotate_action_plan(validated["findings"] + [r for r in validated["recommendations"]
                                                  if not is_finding_reference(r)], coverage["pages_analyzed"])
    validated["top_actions"] = top_actions(validated["findings"])
    validated["quick_wins"] = quick_wins(validated["findings"], validated["recommendations"])
    # Checks that ran and passed, each with the observation that shows it.
    validated["whats_working"] = whats_working(artifacts, {**independent, **dependent}, validated["findings"],
                                               validated["recommendations"], pages_analyzed)
    report = _jsonable(validated)
    if not export_evidence:
        return report
    packet = None
    if pages_analyzed:
        try:
            packet = _jsonable(build_evidence_packet(artifacts, independent["entity_identity"], facts, capabilities,
                                                     audit_id, snapshot_sha256, report["audited_at"], coverage))
        except Exception as exc:  # the report never depends on the packet
            report.setdefault("warnings", []).append(f"The agent evidence packet could not be built: {exc}")
    return {"report": report, "evidence_packet": packet}


def run_audit(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets=False, workflow_started_at=None) -> dict:
    """Public bounded API. A stalled DNS call or analysis cannot hold the caller indefinitely."""
    if workflow_started_at is None:return _run_bounded(site_url, limits, allow_private_targets, False)[0]
    return _run_bounded(site_url, limits, allow_private_targets, False, workflow_started_at)[0]


def run_audit_with_evidence(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets=False, workflow_started_at=None):
    """(report, evidence packet or None): run_audit plus the bounded agent
    evidence packet (common/agent_evidence.py). The packet is None when the
    worker did not finish or no page was analyzed: nothing is then ready for
    the agent stage to assess."""
    if workflow_started_at is None:return _run_bounded(site_url, limits, allow_private_targets, True)
    return _run_bounded(site_url, limits, allow_private_targets, True, workflow_started_at)


# Below this many seconds left before the agent deadline, the agent stage is
# not recommended: the deterministic report is kept as the result.
_MIN_AGENT_STAGE_S = 10.0


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def parse_workflow_start(value, now):
    """Validate the host's first-tool UTC clock before any network or worker work."""
    if value is None:return None
    try:
        if not isinstance(value,str):raise ValueError()
        parsed=datetime.fromisoformat(value[:-1]+'+00:00' if value.endswith('Z') else value)
        if parsed.tzinfo is None:raise ValueError()
        stamp=parsed.timestamp()
        if stamp>now:raise ValueError('future')
        return stamp
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError('--workflow-started-at must be an ISO 8601 timestamp with a timezone, not in the future') from exc


def workflow_worker_budget(limits, now, workflow_started_wall):
    """The normal core ceiling, optionally narrowed by the shared host clock."""
    ceiling=min(270.,float(limits.TOTAL_AUDIT_TIMEOUT_S))
    if workflow_started_wall is None:return ceiling
    remaining=workflow_started_wall+limits.WORKFLOW_TARGET_S-limits.MERGE_FINALIZATION_S-now
    return max(0.,min(ceiling,remaining))


def timing_plan(limits, started_wall, core_finished_wall=None, workflow_started_wall=None):
    """The host workflow's time plan for one audit. Absolute deadlines are UTC
    timestamps counted from when the audit started. Only the core worker limit
    is enforced here: the worker process is stopped at core_limit_s. The agent
    stage gets what the worker left before agent_deadline_at, at most
    agent_stage_budget_s; a worker that ran to a full-length limit leaves none.
    The agent stage runs in the calling host, which this code cannot stop, so
    its deadline is advisory and the merge records how long the whole workflow
    actually took."""
    target = float(getattr(limits, "WORKFLOW_TARGET_S", 270.))
    finalization = float(getattr(limits, "MERGE_FINALIZATION_S", 60.))
    core_limit = float(limits.TOTAL_AUDIT_TIMEOUT_S)
    session_start=started_wall if workflow_started_wall is None else workflow_started_wall
    agent_deadline = session_start + target - finalization
    plan = {
        "workflow_target_s": target,
        "core_limit_s": core_limit,
        "agent_stage_budget_s": float(getattr(limits, "AGENT_STAGE_BUDGET_S", 180.)),
        "finalization_budget_s": finalization,
        "session_started_at": _iso(session_start),
        "clock_scope":"host_first_tool" if workflow_started_wall is not None else "engine_start",
        "core_started_at":_iso(started_wall),
        "preparation_elapsed_s":round(started_wall-session_start,3),
        "agent_deadline_at": _iso(agent_deadline),
        "session_deadline_at": _iso(session_start + target),
        "enforcement": {
            "core": "enforced: the audit worker process is stopped at core_limit_s",
            "agent_stage": "not enforced by this code: the host agent must stop by agent_deadline_at",
            "merge": "local only, no network request; elapsed time is recorded",
        },
    }
    if core_finished_wall is not None:
        plan['core_finished_at']=_iso(core_finished_wall)
        plan["core_elapsed_s"] = round(core_finished_wall - started_wall, 3)
        left = agent_deadline - core_finished_wall
        plan["agent_time_left_s"] = round(max(0., min(left, plan["agent_stage_budget_s"])), 3)
        # The absolute deadline must also express the host-stage maximum. A
        # fast core cannot leave the host an accidental 200+ second allowance.
        plan['agent_deadline_at'] = _iso(min(agent_deadline, core_finished_wall + plan['agent_time_left_s']))
        plan["agent_stage_recommended"] = plan["agent_time_left_s"] >= _MIN_AGENT_STAGE_S
    return plan


def _run_bounded(site_url, limits, allow_private_targets, export_evidence, workflow_started_at=None):
    from subprocess_isolation import run_isolated, IsolatedResult
    from dataclasses import replace
    import math
    import time
    if not math.isfinite(limits.TOTAL_AUDIT_TIMEOUT_S) or limits.TOTAL_AUDIT_TIMEOUT_S <= 0:
        raise ValueError("Audit timeout must be a positive finite number")
    started_wall=time.time()
    workflow_started_wall=parse_workflow_start(workflow_started_at,started_wall)
    limits=replace(limits,TOTAL_AUDIT_TIMEOUT_S=workflow_worker_budget(limits,started_wall,workflow_started_wall))
    site_url = validate_input(site_url)
    _progress("started; total limit " + str(limits.TOTAL_AUDIT_TIMEOUT_S) + "s")
    audit_id = uuid.uuid4().hex
    result = run_isolated(_run_audit_impl, args=(site_url, limits, allow_private_targets, export_evidence, audit_id),
                          timeout_s=limits.TOTAL_AUDIT_TIMEOUT_S,
                          on_wait=lambda elapsed: _progress(f"working ({elapsed:.0f}s elapsed); Ctrl+C cancels cleanly")) if limits.TOTAL_AUDIT_TIMEOUT_S>0 else IsolatedResult(False,None,True,'Shared workflow allowance exhausted before acquisition; no requests made.')
    timing = timing_plan(limits, started_wall, time.time(),workflow_started_wall)
    if result.ok:
        if export_evidence:
            report, packet = result.value["report"], result.value["evidence_packet"]
        else:
            report, packet = result.value, None
        report["timing"] = timing
        if export_evidence and packet is None:
            reason = next((w for w in report.get('warnings', []) if 'packet' in w),
                          'No eligible page was analyzed for the agent evidence packet.')
            packet = nonready_packet(audit_id, report.get('snapshot_sha256'), reason, site_url)
        if packet is not None:
            packet["timing"] = {k: timing[k] for k in ("agent_deadline_at", "agent_stage_budget_s",
                                                        "agent_time_left_s", "agent_stage_recommended",
                                                        "session_started_at","session_deadline_at","clock_scope")}
            from agent_evidence import MAX_PACKET_BYTES
            packet = fit_packet(packet, MAX_PACKET_BYTES)
            report['packet_sha256'] = packet['packet_sha256']
            report['coverage']['evidence_packet_bytes'] = emitted_bytes(packet)
            report['coverage']['evidence_packet_ready'] = packet['ready_for_assessment']
            if not packet['ready_for_assessment']:
                report.setdefault('limitations', []).extend(packet['limitations'])
        return report, packet
    # A timeout is an execution limitation, never a fabricated site defect.
    report = validate_report({"timing": timing,
        "site": site_url, "audit_id": audit_id, "snapshot_sha256": None, "code_version": code_version(),
        "audited_at": datetime.now(timezone.utc).isoformat(), "summary": {},
        "findings": [], "recommendations": generate_recommendations([], []),
        "coverage": {"pages_discovered": 0, "pages_analyzed": 0, "deadline_reached": result.timed_out,
                     "measurements_unavailable": True, "cancelled": result.cancelled},
        "execution_status": "partial_deadline_reached" if result.timed_out else "degraded",
        "limitations": ["The audit worker did not return a complete report. No site-level conclusions can be drawn.", result.error or "Worker failed"],
        "confidence": unfinished_confidence(),
        # Nothing was assessed, so nothing can be shown as passed.
        "whats_working": [],
        "warnings": [result.error or "Worker failed"]}, strict_catalog=True)
    packet = nonready_packet(audit_id, None, result.error or 'Audit worker did not return.', site_url) if export_evidence else None
    if packet is not None:
        packet['timing']=timing
        packet=fit_packet(packet,512*1024)
        report['packet_sha256'] = packet['packet_sha256']
        report['coverage'].update(evidence_packet_bytes=emitted_bytes(packet), evidence_packet_ready=False)
    return report, packet


# Hard ceiling for --max-pages. Above it a polite, paced crawl (crawl-delay, a
# 0.2-second gap, 3.5-second fetch timeout) no longer fits the acquisition budget
# of the 5-minute audit limit on an ordinary site.
MAX_PAGES_CEILING = 100


def limits_for_pages(limits, max_pages):
    """Limits for a crawl of max_pages pages. A larger crawl gets proportionally
    more requests and bytes, so pages do not starve the robots, sitemap, llms.txt,
    image and PDF requests that share the budget. A smaller one keeps the default
    budgets. The wall-clock limits never change."""
    from dataclasses import replace as _dc_replace
    max_pages = max(1, min(MAX_PAGES_CEILING, int(max_pages)))
    extra = max(0, max_pages - DEFAULT_LIMITS.MAX_PAGES_CRAWLED)
    scale = max(1.0, max_pages / DEFAULT_LIMITS.MAX_PAGES_CRAWLED)
    return _dc_replace(limits, MAX_PAGES_CRAWLED=max_pages,
                       MAX_TOTAL_HTTP_REQUESTS=max(limits.MAX_TOTAL_HTTP_REQUESTS,
                                                   DEFAULT_LIMITS.MAX_TOTAL_HTTP_REQUESTS + extra),
                       MAX_TOTAL_BYTES=max(limits.MAX_TOTAL_BYTES, int(DEFAULT_LIMITS.MAX_TOTAL_BYTES * scale)))


def write_report(report, path):
    """Write the JSON report to path as UTF-8, whatever the console or shell
    encoding (PowerShell 5's > redirect writes UTF-16). JSON values are the same
    as stdout; the file retains literal Unicode while stdout escapes it for
    legacy console encodings. The file is written next to its destination and then
    moved into place, so a failed run never leaves half a report."""
    import json
    import tempfile
    path = os.path.abspath(path)
    if os.path.isdir(path):
        raise ValueError(f"--out must name a file, not a directory: {path}")
    folder = os.path.dirname(path)
    handle, temp = tempfile.mkstemp(prefix=".report-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as out:
            out.write(emitted_json(report))
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    return path


def _check_out(parser, out, option="--out"):
    """Reject an output path that cannot be written, before any work starts."""
    if out is not None:
        out_dir = os.path.dirname(os.path.abspath(out))
        # Checked before the audit runs, so a typo never costs a five-minute run.
        if os.path.isdir(os.path.abspath(out)) or not os.path.isdir(out_dir):
            parser.error(f"{option} must name a file in an existing folder: {out}")


def _check_distinct(parser, **paths):
    """Reject two options naming the same file: the report, the evidence packet
    and the agent input are never written over one another."""
    seen = {}
    for option, path in paths.items():
        if path is None:
            continue
        key = os.path.normcase(os.path.realpath(os.path.abspath(path)))
        if key in seen:
            parser.error(f"--{seen[key].replace('_', '-')} and --{option.replace('_', '-')} name the same file "
                         f"({path}); give each its own file")
        seen[key] = option


def _emit_packet(packet, path, report=None):
    """Write the agent evidence packet to path, or say why there is none."""
    if path is None:
        return
    if packet is None:
        packet = nonready_packet((report or {}).get('audit_id'), (report or {}).get('snapshot_sha256'),
                                 'No evidence packet returned for the current audit.', (report or {}).get('site'))
    from agent_evidence import MAX_PACKET_BYTES
    if emitted_bytes(packet) > MAX_PACKET_BYTES:
        packet = nonready_packet(packet.get('audit_id'), packet.get('snapshot_sha256'),
                                 'Evidence export exceeded the packet byte limit.', packet.get('site'))
        if report is not None:
            report['packet_sha256'] = packet['packet_sha256']
            report.setdefault('coverage', {}).update(evidence_packet_bytes=emitted_bytes(packet), evidence_packet_ready=False)
    try:
        written = write_report(packet, path)
        state = 'ready' if packet.get('ready_for_assessment') else 'not ready: ' + '; '.join(packet.get('limitations', []))
        print(f"[audit] evidence packet written to {written} (UTF-8; {state})", file=sys.stderr)
        return True
    except (OSError, ValueError) as exc:
        reason = f"Could not write the evidence packet: {str(exc)[:300]}"
        print(f"[audit] {reason}", file=sys.stderr)
        if report is not None:
            report.setdefault('warnings', []).append(reason)
            report.setdefault('coverage', {})['evidence_packet_write_failed'] = True
        return False


def _emit(report, out):
    """Write the report to out as UTF-8, or print it; a failed write prints it."""
    import json
    written = None
    if out is not None:
        try:
            written = write_report(report, out)
            print(f"[audit] report written to {written} (UTF-8)", file=sys.stderr)
        except OSError as exc:
            # The finished audit is never lost: it goes to stdout instead.
            print(f"[audit] could not write {out} ({exc}); printing the report instead", file=sys.stderr)
    if written is None:
        # Redirected Windows stdout may use a legacy code page. JSON escapes
        # preserve every Unicode value without changing the host's stream.
        print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))


def _merge_main(parser, parsed):
    """--from-report: merge agent findings into a saved report. No request is made."""
    if parsed.agent_findings is None:
        parser.error("--from-report needs --agent-findings PATH")
    if parsed.site is not None or parsed.max_pages is not None or parsed.timeout is not None \
            or parsed.evidence_out is not None or parsed.workflow_started_at is not None:
        parser.error("--from-report merges into a saved report and does not crawl; "
                     "leave out the site, --max-pages, --timeout, --workflow-started-at and --evidence-out")
    _check_out(parser, parsed.out)
    # The deterministic report stays the merge base; the final report is a new file.
    _check_distinct(parser, from_report=parsed.from_report, agent_findings=parsed.agent_findings,
                    evidence=parsed.evidence, out=parsed.out)
    from report_markdown import read_report
    from ingest_agent_findings import load_agent_input, AgentFindingsError
    from merge_agent_stage import merge_agent_envelope, merge_agent_findings, ReportMergeError
    try:
        report = read_report(parsed.from_report)
    except OSError as exc:
        parser.error(f"--from-report: cannot read {parsed.from_report} ({exc})")
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        parser.error(f"--from-report: {parsed.from_report} is not a readable JSON report ({exc})")
    try:
        kind, data = load_agent_input(parsed.agent_findings)
    except AgentFindingsError as exc:
        parser.error(f"--agent-findings: {exc}")
    packet = None
    if kind == "envelope":
        if parsed.evidence is None:
            parser.error("--agent-findings holds an outcome envelope; pass the evidence packet the audit wrote "
                         "with --evidence PATH")
        try:
            from agent_evidence import MAX_PACKET_BYTES
            packet = read_report(parsed.evidence, limit=MAX_PACKET_BYTES)
        except OSError as exc:
            parser.error(f"--evidence: cannot read {parsed.evidence} ({exc})")
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            parser.error(f"--evidence: {parsed.evidence} is not readable JSON ({exc})")
    try:
        if kind == "envelope":
            merged = merge_agent_envelope(report, data, packet, source=os.path.basename(parsed.agent_findings),
                                          packet_source=os.path.basename(parsed.evidence))
        else:
            merged = merge_agent_findings(report, data, source=os.path.basename(parsed.agent_findings))
    except ReportMergeError as exc:
        parser.error(f"--from-report: {exc}")
    info = merged["coverage"]["agent_corroboration"]
    stage = merged["coverage"]["agent_stage"]
    if not parsed.quiet:
        if kind == "envelope":
            print(f"[audit] merged outcome envelope: {stage['assessed_count']} of "
                  f"{stage['assessed_count'] + stage['not_assessed_count']} agent check(s) assessed "
                  f"({stage['assessment_status']}), {info['findings_ingested']} finding(s): "
                  f"{info['findings_folded_into_existing']} joined existing findings, {info['findings_added']} added",
                  file=sys.stderr)
        else:
            print(f"[audit] merged {info['findings_ingested']} of {info['findings_supplied']} agent finding(s): "
                  f"{info['findings_folded_into_existing']} joined existing findings, {info['findings_added']} added "
                  "(legacy array: legacy_partial, no check counted as assessed)", file=sys.stderr)
    _emit(merged, parsed.out)
    return 0


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description="Brand AI-Readiness Audit. Emits one JSON report to stdout, or to a UTF-8 file with --out.")
    parser.add_argument("site", nargs="?", default=None,
                        help="Target URL or bare domain to audit (default https://example.com).")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Override the audit worker's wall-clock cap in seconds (default 270, handout "
                             "limit 300). The optional agent stage gets what the audit leaves before the "
                             "270-second workflow target, at most 180 seconds (see the report's timing). Lower "
                             "it for a quick interactive run on a large site, or to reserve agent time.")
    parser.add_argument("--max-pages", type=int, default=None,
                        help=f"Pages to crawl (default {DEFAULT_LIMITS.MAX_PAGES_CRAWLED}, at most "
                             f"{MAX_PAGES_CEILING}). The site request and byte allowance grows with it "
                             "(reported in coverage.network_budget); the time limit does not, so a slow "
                             "site may stop early.")
    parser.add_argument("-v", "--progress", action="store_true",
                        help="Print stage progress to stderr (stdout stays pure JSON).")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress on stderr; JSON output is unchanged.")
    parser.add_argument("--out", metavar="PATH", default=None,
                        help="Write the JSON report to PATH as UTF-8 instead of stdout. Use this in Windows "
                             "PowerShell, whose > redirect writes UTF-16.")
    parser.add_argument("--agent-findings", metavar="PATH", default=None,
                        help="JSON findings from the entity-corroboration-agent stage (AG-01 to AG-06). With a "
                             "site, they are ingested during the audit (as AGENT_FINDINGS_PATH would be); with "
                             "--from-report, they are merged into that saved report.")
    parser.add_argument("--from-report", metavar="PATH", default=None,
                        help="Merge-only mode: merge --agent-findings into this saved JSON report and emit the "
                             "final report to a new file (--out) or stdout. Makes no request and does not crawl "
                             "again.")
    parser.add_argument("--evidence-out", metavar="PATH", default=None,
                        help="With a site: also write the bounded agent evidence packet (pages, claims and image "
                             "candidates, bound to this audit) to PATH as UTF-8, for the agent stage to read.")
    parser.add_argument("--evidence", metavar="PATH", default=None,
                        help="With --from-report: the evidence packet the audit wrote with --evidence-out. "
                             "Required when --agent-findings holds an outcome envelope.")
    parser.add_argument('--workflow-started-at',metavar='ISO8601',default=None,
                        help='Host UTC clock captured before reading skills. Counts preparation against the 270-second workflow target and reserves 60 seconds for finalization. The default 50-page cap is unchanged; the worker receives only remaining time. Omit for ordinary direct CLI audits.')
    parsed = parser.parse_args(argv)
    if parsed.from_report is not None:
        return _merge_main(parser, parsed)
    if parsed.evidence is not None:
        parser.error("--evidence is read only with --from-report; use --evidence-out to write a packet")
    parsed.site = parsed.site or "https://example.com"
    import math
    if parsed.timeout is not None and (not math.isfinite(parsed.timeout) or parsed.timeout<=0):
        parser.error("--timeout must be a positive finite number")
    if not parsed.quiet:
        os.environ["AUDIT_PROGRESS"] = "1"
    else:
        os.environ["AUDIT_PROGRESS"] = "0"
    if parsed.max_pages is not None and not 1 <= parsed.max_pages <= MAX_PAGES_CEILING:
        parser.error(f"--max-pages must be between 1 and {MAX_PAGES_CEILING}")
    _check_out(parser, parsed.out)
    _check_out(parser, parsed.evidence_out, "--evidence-out")
    _check_distinct(parser, out=parsed.out, evidence_out=parsed.evidence_out, agent_findings=parsed.agent_findings)
    if parsed.agent_findings is not None:
        from ingest_agent_findings import load_agent_findings, AgentFindingsError
        try:
            # Checked before the audit runs, so a bad handoff never costs a five-minute run.
            load_agent_findings(parsed.agent_findings)
        except AgentFindingsError as exc:
            parser.error(f"--agent-findings: {exc}")
        # The audit worker is a spawned process; it inherits this environment.
        os.environ["AGENT_FINDINGS_PATH"] = os.path.abspath(parsed.agent_findings)
    active_limits = DEFAULT_LIMITS
    if parsed.timeout is not None:
        from dataclasses import replace as _dc_replace
        active_limits = _dc_replace(DEFAULT_LIMITS, TOTAL_AUDIT_TIMEOUT_S=parsed.timeout)
    if parsed.max_pages is not None:
        active_limits = limits_for_pages(active_limits, parsed.max_pages)
    try:
        workflow_options={'workflow_started_at':parsed.workflow_started_at} if parsed.workflow_started_at is not None else {}
        if parsed.evidence_out is not None:
            report, packet = run_audit_with_evidence(parsed.site, limits=active_limits,**workflow_options)
        else:
            report, packet = run_audit(parsed.site, limits=active_limits,**workflow_options), None
        _emit_packet(packet, parsed.evidence_out, report)
        _emit(report, parsed.out)
        if report.get("coverage",{}).get("cancelled"):raise SystemExit(130)
    except KeyboardInterrupt:
        print("[audit] cancelled",file=sys.stderr)
        raise SystemExit(130)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
