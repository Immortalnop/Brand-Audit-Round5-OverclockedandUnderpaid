"""test_report_completeness.py -- Priority item 6: the final report always
populates site/timestamp/summary/findings/recommendations/coverage/capabilities/
limitations/execution_status/confidence, and none of it is boilerplate --
execution_status and limitations are derived from real signals, and confidence
shows its own calculation rather than asserting false precision.
"""
import os
import sys
from dataclasses import replace

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import Limits
from models import make_deadline
from execution_summary import derive_execution_status, derive_limitations, overall_confidence
from run_audit import run_audit
from fixtures_server import start_server

_REQUIRED_TOP_LEVEL_FIELDS = (
    "site", "audited_at", "summary", "coverage", "warnings", "findings",
    "recommendations", "execution_status", "limitations", "confidence",
)


# ---------------------------------------------------------------------------
# execution_status
# ---------------------------------------------------------------------------

def test_execution_status_completed_when_nothing_went_wrong():
    class FakeDeadline:
        def expired(self):
            return False
    assert derive_execution_status(FakeDeadline(), [{"status": "success"}], []) == "completed"


def test_execution_status_reflects_deadline_reached_above_all_else():
    class FakeDeadline:
        def expired(self):
            return True
    # Even with a failed skill AND a worker timeout present, deadline takes priority
    # -- it is the most severe, most informative single fact about this run.
    status = derive_execution_status(FakeDeadline(), [{"status": "failed"}], [{"stage": "x"}])
    assert status == "partial_deadline_reached"


def test_execution_status_degraded_on_failed_skill():
    class FakeDeadline:
        def expired(self):
            return False
    status = derive_execution_status(FakeDeadline(), [{"status": "failed"}], [])
    assert status == "degraded"


def test_execution_status_completed_with_timeouts():
    class FakeDeadline:
        def expired(self):
            return False
    status = derive_execution_status(FakeDeadline(), [{"status": "success"}], [{"stage": "x"}])
    assert status == "completed_with_timeouts"


# ---------------------------------------------------------------------------
# limitations: gated on real signals, never unconditional boilerplate
# ---------------------------------------------------------------------------

class _FakeArtifacts:
    def __init__(self, robots_data, sitemap_data):
        self.robots_data = robots_data
        self.sitemap_data = sitemap_data


def test_no_limitations_fabricated_when_everything_worked():
    artifacts = _FakeArtifacts(
        robots_data={"conservative_fail_closed": False, "status": "ok"},
        sitemap_data={"status": "ok"},
    )
    capabilities = {"headless_rendering": True, "external_search": True}
    coverage = {"pages_never_attempted": 0, "pages_timed_out": 0}
    limitations = derive_limitations(artifacts, capabilities, coverage, "completed")
    assert limitations == []


def test_limitation_reported_when_robots_conservative():
    artifacts = _FakeArtifacts(
        robots_data={"conservative_fail_closed": True, "status": "timeout"},
        sitemap_data={"status": "ok"},
    )
    capabilities = {"headless_rendering": True, "external_search": True}
    coverage = {"pages_never_attempted": 0, "pages_timed_out": 0}
    limitations = derive_limitations(artifacts, capabilities, coverage, "completed")
    assert any("robots.txt" in l for l in limitations)


def test_limitation_reported_when_external_search_unavailable():
    artifacts = _FakeArtifacts(
        robots_data={"conservative_fail_closed": False, "status": "ok"},
        sitemap_data={"status": "ok"},
    )
    capabilities = {"headless_rendering": True, "external_search": False}
    coverage = {"pages_never_attempted": 0, "pages_timed_out": 0}
    limitations = derive_limitations(artifacts, capabilities, coverage, "completed")
    assert any("search provider" in l and "not the same as" in l for l in limitations)


def test_limitation_reported_for_never_attempted_pages():
    artifacts = _FakeArtifacts(
        robots_data={"conservative_fail_closed": False, "status": "ok"},
        sitemap_data={"status": "ok"},
    )
    capabilities = {"headless_rendering": True, "external_search": True}
    coverage = {"pages_never_attempted": 7, "pages_discovered": 10, "pages_fetched_attempted": 3,
                "pages_timed_out": 0}
    limitations = derive_limitations(artifacts, capabilities, coverage, "completed")
    assert any("7 discovered URL" in l for l in limitations)


# ---------------------------------------------------------------------------
# confidence: shows its method, weak-link (min) not averaged
# ---------------------------------------------------------------------------

def test_confidence_shows_its_method_and_components():
    result = overall_confidence({"pages_discovered": 10, "pages_fetched_attempted": 20, "pages_analyzed": 20,
                                  "templates_sampled": 5, "identity_confidence": 0.4}, "completed")
    assert "method" in result and "components" in result
    # Identity confidence is reported but does not cap report confidence --
    # it only limits the off-site findings that depend on it (scoring.py).
    assert result["score"] == 1.0
    assert result["components"]["identity_confidence"] == 0.4


def test_large_site_is_not_penalised_for_being_large():
    # 20 pages across 5 templates is an adequate sample however many URLs exist.
    result = overall_confidence({"pages_discovered": 10000, "pages_fetched_attempted": 20, "pages_analyzed": 20,
                                  "templates_sampled": 5}, "completed")
    assert result["score"] == 1.0


def test_confidence_is_capped_by_thin_or_challenged_sample():
    thin = overall_confidence({"pages_discovered": 100, "pages_fetched_attempted": 2, "pages_analyzed": 2,
                                "templates_sampled": 1}, "completed")
    assert thin["score"] <= 0.3
    walled = overall_confidence({"pages_discovered": 40, "pages_fetched_attempted": 20, "pages_analyzed": 4,
                                  "templates_sampled": 4}, "completed")
    assert walled["components"]["access_quality"] == 0.2 and walled["score"] <= 0.3


def test_confidence_penalized_when_deadline_reached():
    good_coverage = {"pages_discovered": 10, "pages_fetched_attempted": 20, "pages_analyzed": 20,
                     "templates_sampled": 5}
    completed = overall_confidence(good_coverage, "completed")
    partial = overall_confidence(good_coverage, "partial_deadline_reached")
    assert partial["score"] < completed["score"]


# ---------------------------------------------------------------------------
# end-to-end: a real run_audit() report is fully populated
# ---------------------------------------------------------------------------

def test_real_audit_report_has_every_required_field_populated():
    base_url, shutdown = start_server()
    try:
        report = run_audit(base_url + "/", allow_private_targets=True)
        for field in _REQUIRED_TOP_LEVEL_FIELDS:
            assert field in report, f"missing required field: {field}"
        assert report["execution_status"] in (
            "completed", "completed_with_timeouts", "degraded", "partial_deadline_reached")
        assert isinstance(report["limitations"], list)
        assert "score" in report["confidence"] and "method" in report["confidence"]
        # A healthy small crawl against a reachable site should not be empty/misleading.
        assert report["summary"]["total_findings"] == len(report["findings"])
        assert report["summary"]["total_recommendations"] == len(report["recommendations"])
        assert len(report["recommendations"]) > 0  # guaranteed even on a clean audit
    finally:
        shutdown()


def test_real_audit_reports_limitation_when_search_provider_absent(monkeypatch):
    monkeypatch.delenv("SEARCH_API_URL", raising=False)
    base_url, shutdown = start_server()
    try:
        report = run_audit(base_url + "/", allow_private_targets=True)
        assert any("search provider" in l for l in report["limitations"])
    finally:
        shutdown()


if __name__ == "__main__":
    import pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "monkeypatch" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
                mp = pytest.MonkeyPatch()
                try:
                    fn(mp)
                finally:
                    mp.undo()
            else:
                fn()
            print(f"OK: {name}")
