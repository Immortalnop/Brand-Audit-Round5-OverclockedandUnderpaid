"""test_round5_budget_reports.py -- Round 5 plan, phases 5 and 6.

  - T5.1 one shared network ledger: reservations are atomic across threads, a
    second transport (a re-anchored origin, the HTTPS probe) inherits what is
    left, the headless child is charged a reserved slice, and the report shows
    the enforced ceilings and per-stage use.
  - T5.2 the host workflow time plan: the core limit leaves time for the agent
    stage inside the 270-second target, and the merge records measured time.
  - T5.3 affected pages are the full set, never the ten-URL evidence sample.
  - T6.1 Markdown shows agent check outcomes and keeps defects and improvement
    opportunities apart; start_here is only ever a confirmed defect.
  - T6.2 generic structured-data absence is an improvement opportunity, and the
    catalog states unmeasured effects as such.
  - T6.3 every finding says where its confidence comes from; the scorer never
    floors a failing rule at 0.5.

Nothing here touches the network beyond 127.0.0.1.
"""
import os
import sys
import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

import network_budget
from acquire_site import acquire_site
from analyze_engagement import analyze_engagement
from analyze_machine_readability import analyze_machine_readability
from archetype_sites import ALLOW_ALL, serve
from check_catalog import CALIBRATED_CONFIDENCE, CATALOG, confidence_basis
from constants import Limits
from instrumentation import Instrumentation
from merge_agent_stage import workflow_elapsed
from models import make_deadline
from prioritize_findings import top_actions
from report_markdown import render
from run_audit import timing_plan,parse_workflow_start,workflow_worker_budget,run_audit_with_evidence
import pytest
from test_precision_traps import SITE, TEXT, page, snapshot
from transport import Transport

LIMITS = Limits()


def html(title, body):
    return f'<!doctype html><html lang="en"><head><title>{title}</title></head><body>{body}</body></html>'


def _server(body=b"x" * 1000):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}", httpd.shutdown


def _transport(base, budget, **kw):
    limits = replace(LIMITS, REQUEST_DELAY_S=0)
    return Transport(base, make_deadline(LIMITS).deadline_monotonic, limits, Instrumentation(), allow_private=True,
                     budget=budget, **kw)


# ---------------------------------------------------------------------------
# T5.1 shared ledger
# ---------------------------------------------------------------------------

def test_reservations_never_exceed_the_ceiling_across_threads():
    budget = network_budget.NetworkBudget(50, 10_000, 5, 1_000)
    granted = []

    def worker():
        for _ in range(20):
            granted.append(budget.reserve("site", "pages", 300))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    used = budget.snapshot()["pools"]["site"]
    assert used["requests"] <= 50 and used["bytes"] <= 10_000
    assert sum(1 for g in granted if g) == used["requests"]
    assert used["refused"] == sum(1 for g in granted if not g)


def test_unused_bytes_are_refunded_and_requests_are_kept():
    budget = network_budget.NetworkBudget(10, 1_000, 1, 100)
    assert budget.reserve("site", "pages", 600) == 600
    budget.settle("site", "pages", 600, 150)
    snap = budget.snapshot()
    assert snap["pools"]["site"]["requests"] == 1 and snap["pools"]["site"]["bytes"] == 150
    assert snap["stages"]["pages"] == {"pool": "site", "requests": 1, "bytes": 150}
    # The external pool is separate and has its own ceiling.
    assert budget.reserve("external", "knowledge_graph", 500) == 100
    assert budget.reserve("external", "knowledge_graph", 1) == 0


def test_second_transport_inherits_what_the_first_left():
    base, stop = _server()
    try:
        budget = network_budget.NetworkBudget(3, 1_000_000, 1, 1)
        first = _transport(base, budget)
        for _ in range(2):
            assert first.get(base + "/a", robots_exempt=True)[1] == "ok"
        # A new transport for the same audit (a re-anchored origin) gets one request, not a fresh three.
        second = _transport(base, budget, stage="https_probe")
        assert second.get(base + "/b", robots_exempt=True)[1] == "ok"
        assert second.get(base + "/c", robots_exempt=True)[1] == "budget_exhausted"
        snap = budget.snapshot()
        assert snap["pools"]["site"]["requests"] == 3
        assert snap["stages"]["https_probe"]["requests"] == 1
        # Bytes charged are the bytes read, not the reservation.
        assert snap["pools"]["site"]["bytes"] == 3000
    finally:
        stop()


def test_byte_ceiling_caps_the_read_itself():
    base, stop = _server(b"y" * 5000)
    try:
        budget = network_budget.NetworkBudget(10, 2_000, 1, 1)
        response, status = _transport(base, budget).get(base + "/big", robots_exempt=True)
        assert status == "ok" and response.truncated and len(response.content) <= 2_000
        assert budget.snapshot()["pools"]["site"]["bytes"] <= 2_000
    finally:
        stop()


def test_acquisition_charges_the_active_ledger_including_retries_and_robots():
    site = {"robots": ALLOW_ALL, "pages": {"/": html("Home", "<main><h1>Home</h1>" + TEXT + "</main>")}}
    base, stop, seen = serve(site)
    budget = network_budget.activate(network_budget.from_limits(LIMITS))
    try:
        artifacts = acquire_site(base + "/", make_deadline(LIMITS), LIMITS, allow_private_targets=True)
    finally:
        network_budget.deactivate(budget)
        stop()
    snap = budget.snapshot()
    assert artifacts.pages
    # Every request the server answered, plus the HTTPS probe to port 443 that
    # nothing answers here: it was still sent, so it is still charged.
    assert snap["pools"]["site"]["requests"] == artifacts.acquisition_metadata["total_requests"] == len(seen) + 1
    assert {"robots", "pages", "sitemap", "llms_txt", "https_probe"} <= set(snap["stages"])
    assert snap["stages"]["https_probe"]["requests"] == 1
    assert network_budget.active() is None


def test_headless_child_is_charged_its_reserved_slice(monkeypatch):
    import subprocess_isolation
    from analyze_rendering import _render_with_headless_browser
    calls = []

    def fake_run_isolated(target, args=(), kwargs=None, timeout_s=30., **_):
        calls.append(args)
        return subprocess_isolation.IsolatedResult(True, {}, False, None)

    monkeypatch.setattr(subprocess_isolation, "run_isolated", fake_run_isolated)
    budget = network_budget.activate(network_budget.NetworkBudget(90, 40_000_000, 1, 1))
    try:
        for _ in range(80):
            budget.reserve("site", "pages", 1)
        _render_with_headless_browser([SITE + "/"], LIMITS, timeout_s=1)
        # Only 10 requests were left: the child is capped at those, and they are charged.
        assert calls[-1][3] == 10
        assert budget.snapshot()["stages"]["headless_rendering"]["requests"] == 10
        lengths, timed_out, error = _render_with_headless_browser([SITE + "/"], LIMITS, timeout_s=1)
        assert lengths == {} and not timed_out and "allowance" in error and len(calls) == 1
    finally:
        network_budget.deactivate(budget)


def test_report_shows_enforced_ceilings_and_stage_use():
    from test_round5_observations import run_offline
    site = {"robots": ALLOW_ALL, "pages": {"/": html("Home", "<main><h1>Home</h1>" + TEXT + "</main>")}}
    _, report, seen = run_offline(site)
    budget = report["coverage"]["network_budget"]
    assert budget["pools"]["site"]["max_requests"] == LIMITS.MAX_TOTAL_HTTP_REQUESTS
    assert budget["pools"]["external"]["max_requests"] == LIMITS.MAX_EXTERNAL_HTTP_REQUESTS
    assert budget["pools"]["site"]["requests"] == report["coverage"]["instrumentation"].get("requests_attempted",
                                                                                          len(seen) + 1)
    assert "host-agent tool calls" in budget["not_counted"][0]
    timing = report["timing"]
    assert timing["core_limit_s"] == LIMITS.TOTAL_AUDIT_TIMEOUT_S and timing["agent_stage_recommended"]
    assert "Requests to the site" in render(report)


# ---------------------------------------------------------------------------
# T5.2 time plan
# ---------------------------------------------------------------------------

def test_default_core_limit_is_270_and_a_fast_audit_leaves_agent_time():
    assert LIMITS.TOTAL_AUDIT_TIMEOUT_S == 270
    plan = timing_plan(LIMITS, 1_000_000.0, 1_000_000.0 + 60)
    assert plan["core_limit_s"] == 270 and plan["workflow_target_s"] == 270
    assert plan["agent_stage_budget_s"] == 180 and plan["agent_time_left_s"] == 150
    assert plan["agent_stage_recommended"]
    assert datetime.fromisoformat(plan['agent_deadline_at']).timestamp() == 1_000_000 + 210
    assert "not enforced" in plan["enforcement"]["agent_stage"]
    assert timing_plan(LIMITS, 0.0, 180.0)["agent_time_left_s"] == 30
    assert timing_plan(LIMITS, 0.0, 230.0)["agent_time_left_s"] == 0
    assert timing_plan(LIMITS, 0.0, 5.0)["agent_time_left_s"] == 180


def test_full_length_core_leaves_no_agent_time():
    plan = timing_plan(LIMITS, 0.0, 262.0)
    assert plan["agent_time_left_s"] == 0 and not plan["agent_stage_recommended"]


def test_merge_records_measured_workflow_time():
    started = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
    plan = timing_plan(LIMITS, started.timestamp(), started.timestamp() + 100)
    on_time = workflow_elapsed(plan, started + timedelta(seconds=200))
    assert on_time["workflow_elapsed_s"] == 200 and on_time["within_workflow_target"]
    assert not on_time['after_agent_deadline'] and on_time['agent_elapsed_s'] == 100
    late = workflow_elapsed(plan, started + timedelta(seconds=300))
    assert not late["within_workflow_target"] and late["after_agent_deadline"]
    assert workflow_elapsed(None, started) is None


def test_host_preparation_is_charged_without_changing_default_core_or_page_cap():
    start=1_000_000.
    assert LIMITS.MAX_PAGES_CRAWLED==50
    assert workflow_worker_budget(LIMITS,start+25,None)==270
    assert workflow_worker_budget(LIMITS,start+25,start)==185
    plan=timing_plan(replace(LIMITS,TOTAL_AUDIT_TIMEOUT_S=185),start+25,start+55,start)
    assert plan['preparation_elapsed_s']==25 and plan['core_elapsed_s']==30
    assert plan['agent_time_left_s']==155
    assert datetime.fromisoformat(plan['session_deadline_at']).timestamp()==start+270
    measured=workflow_elapsed(plan,datetime.fromtimestamp(start+100,timezone.utc))
    assert measured['workflow_elapsed_s']==100 and measured['agent_elapsed_s']==45


@pytest.mark.parametrize('value',[True,123,'garbage','2026-10-14T00:00:00','2026-10-15T00:00:00Z'])
def test_invalid_or_future_host_clocks_cannot_reset_the_budget(value):
    with pytest.raises(ValueError,match='workflow-started-at'):
        parse_workflow_start(value,datetime(2026,10,14,tzinfo=timezone.utc).timestamp())


def test_expired_shared_clock_makes_no_worker_or_network_request(monkeypatch):
    import subprocess_isolation
    def refuse(*args,**kwargs):raise AssertionError('Worker must not be launched')
    monkeypatch.setattr(subprocess_isolation,'run_isolated',refuse)
    report,packet=run_audit_with_evidence('https://example.com/',workflow_started_at='2020-01-01T00:00:00Z')
    assert report['execution_status']=='partial_deadline_reached'
    assert not packet['ready_for_assessment']
    assert report['timing']['core_limit_s']==0
    assert report['timing']['agent_time_left_s']==0


# ---------------------------------------------------------------------------
# T5.3 full affected sets
# ---------------------------------------------------------------------------

def test_twelve_orphans_stay_twelve():
    urls = [f"{SITE}/p{i}" for i in range(12)]
    graph = {"data": {"orphans": urls, "dead_ends": urls, "isolated_clusters": [urls[:6], urls[6:]],
                      "crawl_scope": {"complete": True, "urls_never_attempted": 0, "urls_discovered": 13},
                      "nodes": {u: {} for u in urls}}}
    home = page("<main><h1>Home</h1>" + TEXT + "</main>")
    result = analyze_engagement(snapshot(home), graph, {"metrics": {}}, make_deadline(LIMITS))
    by_rule = {f["provenance"]["rule_id"]: f for f in result["findings"]}
    for rule in ("orphan-pages", "dead-ends", "isolated-clusters"):
        assert len(by_rule[rule]["affected_pages"]) == 12, rule
        assert all(len(e.get("urls") or ()) <= 10 for e in by_rule[rule]["evidence"])
    assert result["metrics"]["orphan_pages"] == 12


def test_schema_absence_lists_every_page():
    pages = [page("<main><h1>P</h1>" + TEXT + "</main>", url=f"{SITE}/p{i}") for i in range(12)]
    result = analyze_machine_readability(snapshot(*pages), make_deadline(LIMITS))
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "no-jsonld")
    assert len(finding["affected_pages"]) == 12


# ---------------------------------------------------------------------------
# T6.1 and T6.2 report presentation and wording
# ---------------------------------------------------------------------------

def test_no_jsonld_is_a_proportional_improvement_opportunity():
    pages = [page("<main><h1>P</h1>" + TEXT + "</main>", url=f"{SITE}/p{i}") for i in range(3)]
    result = analyze_machine_readability(snapshot(*pages), make_deadline(LIMITS))
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "no-jsonld")
    assert finding["finding_type"] == "proactive_improvement" and finding["status"] == "confirmed"
    assert finding["severity"] in ("medium", "low")


def test_catalog_states_unmeasured_effects_without_guarantees():
    banned = ("engaged longer", "with confidence", "qualifies for", "confidently by assistants",
              "orient quickly")
    for check_id, entry in CATALOG.items():
        outcome = entry["expected_outcome"].lower()
        assert not any(b in outcome for b in banned), check_id
    assert "no longer appear" in CATALOG["citation-schema-opportunity"]["implementation_detail"]
    assert "not a search eligibility requirement" in CATALOG["no-llms-txt"]["expected_outcome"]


def _finding(fid, status, finding_type="defect", quick_win=True):
    return {"id": fid, "title": fid, "status": status, "finding_type": finding_type,
            "suggested_action": {"summary": "s", "priority": "medium", "impact": "high", "effort": "low",
                                 "quick_win": quick_win}}


def test_start_here_is_only_a_confirmed_defect():
    rows = top_actions([_finding("F-001", "suspected"), _finding("F-002", "confirmed", quick_win=False)])
    assert [r["finding_id"] for r in rows if r["start_here"]] == ["F-002"]
    assert not any(r["start_here"] for r in top_actions([_finding("F-001", "suspected")]))
    report = {"site": SITE, "top_actions": top_actions([_finding("F-001", "suspected")]), "findings": []}
    text = render(report)
    assert "## Start here" not in text and "## Top actions" in text


def test_markdown_shows_agent_outcomes_and_finding_types():
    report = {"site": SITE, "coverage": {"pages_analyzed": 2, "pages_discovered": 2, "pages_partially_observed": 1,
                                         "agent_stage": {"submission_status": "envelope", "assessment_status": "partial",
                                                         "assessed_count": 1,
                                                         "checks": {"AG-01": {"outcome": "pass", "reason": "clear"},
                                                                    "AG-04": {"outcome": "not_assessed",
                                                                              "reason": "no image viewing"}}}},
              "findings": [dict(_finding("F-001", "confirmed", "proactive_improvement"), severity="low",
                                affected_pages=[], confidence=0.8)]}
    text = render(report)
    assert "## Agent checks" in text and "AG-04 Facts drawn inside images | not assessed | no image viewing" in text
    assert "A check that was not assessed is not a pass." in text
    assert "Improvement opportunity" in text and "Pages read only in part" in text


# ---------------------------------------------------------------------------
# T6.3 confidence provenance
# ---------------------------------------------------------------------------

def test_every_calibrated_value_has_its_basis():
    for check_id, value in CALIBRATED_CONFIDENCE.items():
        basis = confidence_basis(check_id)
        assert basis["base_value"] == value and basis["method"] == "heuristic"
        assert basis["labelled"] >= 5 and basis["sites"] >= 1 and not basis["labels_reviewed_by_person"]
        assert basis["tp"] + basis["fp"] + basis["irrelevant"] == basis["labelled"]
        assert basis["evidence_class"] in ("observed_fact", "heuristic_applicability")
    assert confidence_basis("dead-ends") == {"method": "script_rule"}


def test_findings_carry_their_confidence_basis():
    pages = [page("<main><h1>P</h1>" + TEXT + "</main>", url=f"{SITE}/p{i}") for i in range(3)]
    result = analyze_machine_readability(snapshot(*pages), make_deadline(LIMITS))
    assert all(f.get("confidence_basis", {}).get("method") for f in result["findings"])


def test_markdown_agent_names_match_the_check_table():
    from agent_evidence import AG_CHECKS
    from report_markdown import _AG_NAMES
    assert _AG_NAMES == {k: v["name"] for k, v in AG_CHECKS.items()}
