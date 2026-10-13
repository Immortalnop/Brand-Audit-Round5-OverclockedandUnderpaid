"""Unit tests for every finding-producing script: normal fixtures, malformed input,
insufficient-evidence paths, and (via run_audit's worker wrapper) timeouts. Confirms
Invariant I-1 holds in every case and malformed input never silently fabricates a
confirmed defect."""
import os
import sys
import time
import pytest
from concurrent.futures import ThreadPoolExecutor

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import DEFAULT_LIMITS
from models import PageArtifact, AuditArtifacts, make_deadline, intermediate_artifact
from instrumentation import Instrumentation

from analyze_crawlability import analyze_crawlability
from analyze_rendering import analyze_rendering
from analyze_machine_readability import analyze_machine_readability
from check_ai_crawler_access import check_ai_crawler_access
from check_llms_txt import check_llms_txt
from assess_freshness import assess_freshness
from corroborate_claims import corroborate_claims
from assess_external_footprint import assess_external_footprint
from analyze_engagement import analyze_engagement
from build_site_graph import build_site_graph
from run_audit import _await_result

_LIMITS = DEFAULT_LIMITS


def _empty_artifacts():
    return AuditArtifacts(
        site_url="https://example.com/", normalized_origin="https://example.com",
        pages=(), robots_data={"allowed_general": True, "status": "ok", "general_disallow": False,
                                "ai_crawler_directives": {}},
        llms_txt_data={"present": False, "status": "absent"},
        sitemap_data={"discovered": False, "status": "absent", "urls": []},
        acquisition_metadata={}, warnings=(),
    )


def _page(url, jsonld_blocks=(), visible_text="text", status_code=200):
    return PageArtifact(
        url=url, status_code=status_code, content_type="text/html",
        evidence_snippet=visible_text[:500], visible_text=visible_text, title="T",
        meta_description=None, canonical_url=None, headings=("H",),
        internal_links=(), external_links=(), jsonld_blocks=jsonld_blocks, page_type=None,
        fetch_duration_ms=10, render_status="not_rendered", breadcrumb_visible=(),
        breadcrumb_schema=None, ai_crawler_directives={}, warnings=(),
    )


def _assert_invariant(result):
    for f in result["findings"]:
        if f["status"] == "insufficient_evidence":
            assert f["finding_type"] == "proactive_improvement"
            assert f["severity"] == "low"


def test_analyze_crawlability_empty_site_no_crash():
    deadline = make_deadline(_LIMITS)
    result = analyze_crawlability(_empty_artifacts(), deadline)
    assert result["findings"] == []
    _assert_invariant(result)


def test_analyze_crawlability_broken_pages_confirmed_defect():
    artifacts = _empty_artifacts()
    artifacts = artifacts.__class__(**{**artifacts.__dict__, "pages": (_page("https://example.com/x", status_code=500),)})
    deadline = make_deadline(_LIMITS)
    result = analyze_crawlability(artifacts, deadline)
    assert any(f["provenance"]["rule_id"] == "broken-pages" for f in result["findings"])
    _assert_invariant(result)


def test_analyze_rendering_no_pages_is_insufficient_evidence():
    deadline = make_deadline(_LIMITS)
    result = analyze_rendering(_empty_artifacts(), deadline, _LIMITS, capabilities={})
    assert result["status"] == "insufficient_evidence"
    _assert_invariant(result)


def test_analyze_machine_readability_handles_non_dict_jsonld_gracefully():
    # Malformed input: a jsonld_blocks entry that is a string, not a dict.
    page = _page("https://example.com/x", jsonld_blocks=("not-a-dict",))
    artifacts = _empty_artifacts()
    artifacts = artifacts.__class__(**{**artifacts.__dict__, "pages": (page,)})
    deadline = make_deadline(_LIMITS)
    # jsonld_blocks is non-empty (truthy) even though malformed, so no-jsonld rule
    # correctly does not fire; the point is this must not raise.
    result = analyze_machine_readability(artifacts, deadline)
    _assert_invariant(result)


def test_check_ai_crawler_access_missing_directives_defaults_safely():
    artifacts = _empty_artifacts()
    artifacts = artifacts.__class__(**{**artifacts.__dict__, "robots_data": {}})
    deadline = make_deadline(_LIMITS)
    result = check_ai_crawler_access(artifacts, deadline)
    assert result["findings"] == []
    _assert_invariant(result)


def test_check_llms_txt_absent_is_observation_only():
    deadline = make_deadline(_LIMITS)
    result = check_llms_txt(_empty_artifacts(), deadline)
    assert not result["findings"]
    assert result["metrics"]["llms_txt_present"] is False


def test_assess_freshness_no_dates_is_insufficient_evidence():
    facts = intermediate_artifact("important_facts", data={"facts": []})
    deadline = make_deadline(_LIMITS)
    result = assess_freshness(facts, _empty_artifacts(), deadline)
    assert result["status"] == "insufficient_evidence"
    _assert_invariant(result)


def test_assess_freshness_malformed_fact_raises_and_is_caught_upstream():
    # Malformed input: a fact missing required keys. The script is allowed to raise;
    # run_audit's worker wrapper (_await_result) is what must contain the blast radius.
    facts = intermediate_artifact("important_facts", data={"facts": [{"type": "date"}]})  # no "value"
    deadline = make_deadline(_LIMITS)
    with pytest.raises(KeyError):
        assess_freshness(facts, _empty_artifacts(), deadline)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(assess_freshness, facts, _empty_artifacts(), deadline)
        result = _await_result(future, "freshness", "dependent_batch", Instrumentation())
    assert result["status"] == "failed"
    assert result["findings"] == []


def test_corroborate_claims_unresolved_identity_is_insufficient_evidence():
    identity = intermediate_artifact("entity_identity", status="insufficient_evidence", data={"confidence": 0.0})
    facts = intermediate_artifact("important_facts", data={"facts": []})
    deadline = make_deadline(_LIMITS)
    result = corroborate_claims(facts, identity, _empty_artifacts(), deadline, _LIMITS)
    assert result["status"] == "insufficient_evidence"
    _assert_invariant(result)


def test_corroborate_claims_no_provider_configured_is_insufficient_evidence(monkeypatch):
    monkeypatch.delenv("SEARCH_API_URL", raising=False)
    identity = intermediate_artifact("entity_identity", status="success", data={"confidence": 0.9, "canonical_name": "Example"})
    facts = intermediate_artifact("important_facts", data={"facts": []})
    deadline = make_deadline(_LIMITS)
    result = corroborate_claims(facts, identity, _empty_artifacts(), deadline, _LIMITS)
    assert result["status"] == "insufficient_evidence"


def test_assess_external_footprint_low_confidence_identity_is_insufficient_evidence():
    identity = intermediate_artifact("entity_identity", status="partial", data={"confidence": 0.5, "canonical_name": "Example"})
    deadline = make_deadline(_LIMITS)
    result = assess_external_footprint(_empty_artifacts(), identity, deadline, _LIMITS)
    assert result["status"] == "insufficient_evidence"
    _assert_invariant(result)


def test_assess_external_footprint_search_failure_is_insufficient_evidence(monkeypatch):
    import search_provider
    monkeypatch.setenv("SEARCH_API_URL", "http://127.0.0.1:1")  # nothing listens here
    identity = intermediate_artifact("entity_identity", status="success",
                                      data={"confidence": 0.95, "canonical_name": "Example", "domain": "example.com"})
    deadline = make_deadline(_LIMITS)
    result = assess_external_footprint(_empty_artifacts(), identity, deadline, _LIMITS)
    assert result["status"] == "insufficient_evidence"
    _assert_invariant(result)


def test_analyze_engagement_missing_rendering_metrics_defaults_safely():
    artifacts = _empty_artifacts()
    deadline = make_deadline(_LIMITS)
    graph = build_site_graph(artifacts, deadline)
    result = analyze_engagement(artifacts, graph, {"metrics": {}}, deadline)
    assert result["findings"] == []
    _assert_invariant(result)


def test_worker_timeout_is_recorded_and_downgraded_to_insufficient_evidence():
    def _slow():
        time.sleep(2)
        return {"skill": "slow", "status": "success", "findings": [], "metrics": {}, "warnings": [],
                "coverage": {"pages_analyzed": 0, "pages_skipped": 0, "queries_attempted": 0, "queries_completed": 0}}

    instrumentation = Instrumentation()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_slow)
        import run_audit as ra
        original_timeout = ra._WORKER_TIMEOUT_S
        ra._WORKER_TIMEOUT_S = 0.1
        try:
            result = _await_result(future, "slow_worker", "independent_batch", instrumentation)
        finally:
            ra._WORKER_TIMEOUT_S = original_timeout
    assert result["status"] == "insufficient_evidence"
    assert len(instrumentation.worker_timeout_events) == 1
    _assert_invariant(result)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and "monkeypatch" not in fn.__code__.co_varnames:
            fn()
            print(f"OK: {name}")
