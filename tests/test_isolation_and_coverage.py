"""test_isolation_and_coverage.py -- Priority items:
  1. True timeout/cancellation via subprocess isolation for hanging work.
  2. Distinct request telemetry (redirects, timeouts) and budget-exhaustion vs.
     fetch-failure separation.
  3. Factual coverage metrics: discovered != fetched != analyzed unless genuinely
     equal, with a real breakdown instead of one number reused three times.
"""
import os
import sys
import time
from dataclasses import replace

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import Limits
from models import make_deadline
from instrumentation import Instrumentation
from acquire_site import acquire_site
from subprocess_isolation import run_isolated, _hang_forever, _double, _raises

from fixtures_server import start_server


# ---------------------------------------------------------------------------
# Item 1: subprocess isolation gives a real, hard cancellation guarantee
# ---------------------------------------------------------------------------

def test_run_isolated_returns_fast_result_promptly():
    t0 = time.time()
    result = run_isolated(_double, args=(21,), timeout_s=5)
    elapsed = time.time() - t0
    assert result.ok and result.value == 42 and not result.timed_out
    assert elapsed < 3


def test_run_isolated_kills_a_genuinely_hanging_child_within_bound():
    t0 = time.time()
    result = run_isolated(_hang_forever, args=(), timeout_s=1.5, kill_grace_s=1.0)
    elapsed = time.time() - t0
    # The parent must regain control within timeout_s + kill_grace_s + a small
    # margin -- NOT block forever, regardless of what the child is doing.
    assert result.timed_out and not result.ok
    assert elapsed < 5.0


def test_run_isolated_surfaces_child_exception_without_crashing_parent():
    result = run_isolated(_raises, args=(), timeout_s=3)
    assert not result.ok and not result.timed_out
    assert "child blew up" in (result.error or "")


# ---------------------------------------------------------------------------
# Item 2: redirects and timeouts are counted distinctly, not folded into a
# generic "failed" bucket
# ---------------------------------------------------------------------------

def test_redirects_are_counted_distinctly_from_ordinary_requests():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        acquire_site(base_url + "/", deadline, limits, instrumentation, allow_private_targets=True)
        assert instrumentation.redirects_followed >= 1  # the fixture's /redirect page
    finally:
        shutdown()


def test_timeouts_are_counted_distinctly_from_other_failures():
    base_url, shutdown = start_server(slow_delay_s=2.0)
    try:
        limits = replace(Limits(), PER_FETCH_TIMEOUT_MS=200, MAX_FETCH_RETRIES=0)
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        acquire_site(base_url + "/slow", deadline, limits, instrumentation, allow_private_targets=True)
        assert instrumentation.requests_timed_out >= 1
        assert instrumentation.requests_timed_out <= instrumentation.requests_failed
    finally:
        shutdown()


def test_retries_are_counted():
    base_url, shutdown = start_server(slow_delay_s=2.0)
    try:
        limits = replace(Limits(), PER_FETCH_TIMEOUT_MS=200, MAX_FETCH_RETRIES=2)
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        acquire_site(base_url + "/slow", deadline, limits, instrumentation, allow_private_targets=True)
        assert instrumentation.requests_retried >= 1
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# Item 3: discovered / fetched / analyzed are real, distinct numbers
# ---------------------------------------------------------------------------

def test_discovered_exceeds_fetched_when_page_budget_is_tighter_than_the_site():
    base_url, shutdown = start_server()
    try:
        # The fixture site has 6+ linked pages; cap the crawl at 2 fetched pages.
        limits = replace(Limits(), MAX_PAGES_CRAWLED=2)
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        cov = artifacts.acquisition_metadata["coverage"]
        assert cov["urls_fetched_attempted"] == 2
        assert cov["urls_discovered"] > cov["urls_fetched_attempted"]
        assert cov["urls_never_attempted"] > 0
        assert cov["urls_analyzed"] <= cov["urls_fetched_attempted"]
    finally:
        shutdown()


def test_error_pages_are_fetched_but_not_double_counted_as_analyzed():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/error", deadline, limits, allow_private_targets=True)
        cov = artifacts.acquisition_metadata["coverage"]
        # /error is fetched (a real HTTP round trip completed, status 500) but is
        # not "analyzed" content -- fetched_ok and analyzed both exclude it.
        assert cov["urls_fetched_attempted"] == 1
        assert cov["urls_fetched_error"] == 1
        assert cov["urls_fetched_ok"] == 0
        assert cov["urls_analyzed"] == 0
    finally:
        shutdown()


def test_timed_out_pages_are_categorized_separately_in_coverage():
    base_url, shutdown = start_server(slow_delay_s=2.0)
    try:
        limits = replace(Limits(), PER_FETCH_TIMEOUT_MS=200, MAX_FETCH_RETRIES=0)
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/slow", deadline, limits, allow_private_targets=True)
        cov = artifacts.acquisition_metadata["coverage"]
        assert cov["urls_timed_out"] == 1
        assert cov["urls_analyzed"] == 0
    finally:
        shutdown()


def test_run_audit_coverage_does_not_equate_discovered_fetched_analyzed():
    base_url, shutdown = start_server()
    try:
        from run_audit import run_audit
        limits = replace(Limits(), MAX_PAGES_CRAWLED=2)
        report = run_audit(base_url + "/", limits=limits, allow_private_targets=True)
        cov = report["coverage"]
        assert cov["pages_fetched_attempted"] == 2
        assert cov["pages_discovered"] > cov["pages_fetched_attempted"]
        assert cov["pages_never_attempted"] > 0
        assert "skip_reason_counts" in cov
    finally:
        shutdown()


def test_analyze_crawlability_reports_real_skip_count_not_hardcoded_zero():
    from analyze_crawlability import analyze_crawlability
    base_url, shutdown = start_server()
    try:
        limits = replace(Limits(), MAX_PAGES_CRAWLED=1)
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        result = analyze_crawlability(artifacts, deadline)
        # With the crawl capped at 1 page against a multi-page fixture site, at
        # least one link must have been skipped -- never a hardcoded 0.
        assert result["coverage"]["pages_skipped"] > 0
    finally:
        shutdown()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn) and "monkeypatch" not in fn.__code__.co_varnames:
            fn()
            print(f"OK: {name}")
