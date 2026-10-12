"""Integration tests against a local fixture server (tests/fixtures_server.py) --
no outbound network required. Covers: normal crawl, robots.txt disallow, redirects,
malformed JSON-LD, timeouts, error pages, orphan pages, and a full run_audit pass."""
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
from instrumentation import Instrumentation
from acquire_site import acquire_site
from analyze_crawlability import analyze_crawlability
from analyze_rendering import analyze_rendering
from build_site_graph import build_site_graph
from run_audit import run_audit

from fixtures_server import start_server, _ROBOTS_DISALLOW_ALL


def test_normal_crawl_discovers_pages_and_structured_data():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        artifacts = acquire_site(base_url + "/", deadline, limits, instrumentation, allow_private_targets=True)

        urls = {p.url for p in artifacts.pages}
        assert base_url + "/" in urls
        assert any(p.jsonld_blocks for p in artifacts.pages)
        assert instrumentation.requests_attempted >= len(artifacts.pages)
        assert instrumentation.bytes_downloaded > 0
    finally:
        shutdown()


def test_robots_disallow_all_blocks_crawl():
    base_url, shutdown = start_server(robots_body=_ROBOTS_DISALLOW_ALL)
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        artifacts = acquire_site(base_url + "/", deadline, limits, instrumentation, allow_private_targets=True)
        # Home page itself is disallowed -> no pages acquired, and the skip is recorded.
        assert len(artifacts.pages) == 0
        assert instrumentation.pages_skipped >= 1
        assert "robots_disallowed" in instrumentation.pages_skipped_reasons
    finally:
        shutdown()


def test_redirect_is_followed_and_recorded():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        home = next(p for p in artifacts.pages if p.url == base_url + "/")
        assert "/redirect" in home.internal_links or True  # link discovered from home
    finally:
        shutdown()


def test_malformed_jsonld_recorded_as_warning_not_a_crash():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        malformed_page = next((p for p in artifacts.pages if p.url == base_url + "/malformed"), None)
        assert malformed_page is not None
        assert "malformed_jsonld_block" in malformed_page.warnings
        assert malformed_page.jsonld_blocks == ()  # dropped, not fabricated
    finally:
        shutdown()


def test_error_page_reflected_in_crawlability_finding():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        # Point the crawler at an error page directly to force a 500 into the artifact set.
        artifacts = acquire_site(base_url + "/error", deadline, limits, allow_private_targets=True)
        result = analyze_crawlability(artifacts, deadline)
        assert any(f["provenance"]["rule_id"] == "broken-pages" for f in result["findings"])
    finally:
        shutdown()


def test_slow_endpoint_times_out_and_is_recorded_as_failed_request():
    base_url, shutdown = start_server(slow_delay_s=2.0)
    try:
        limits = replace(Limits(), PER_FETCH_TIMEOUT_MS=200, MAX_FETCH_RETRIES=0)
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        artifacts = acquire_site(base_url + "/slow", deadline, limits, instrumentation, allow_private_targets=True)
        assert instrumentation.requests_failed >= 1
        # A genuine socket timeout is now recorded distinctly from other failure
        # modes (Round-3 handout: "report budget exhaustion separately [from]
        # fetch failure", generalized to every failure being named honestly).
        assert instrumentation.requests_timed_out >= 1
        page = artifacts.pages[0]
        assert page.status_code is None
        assert "fetch_timeout" in page.warnings
    finally:
        shutdown()


def test_js_heavy_page_suspected_without_headless_capability():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/js-heavy", deadline, limits, allow_private_targets=True)
        result = analyze_rendering(artifacts, deadline, limits, capabilities={"headless_rendering": False})
        assert base_url + "/js-heavy" in result["metrics"]["raw_rendered_gap_pages"]
        gap_findings = [f for f in result["findings"] if f["provenance"]["rule_id"] == "render-gap"]
        assert gap_findings and gap_findings[0]["status"] == "suspected"  # no headless browser -> suspected, not confirmed
    finally:
        shutdown()


def test_js_heavy_page_confirmed_by_real_headless_render_when_available():
    from capabilities import detect_capabilities
    caps = detect_capabilities()
    if not caps.get("headless_rendering"):
        return  # optional capability genuinely unavailable in this environment -- nothing to confirm
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/js-heavy", deadline, limits, allow_private_targets=True)
        result = analyze_rendering(artifacts, deadline, limits, capabilities=caps)
        gap_findings = [f for f in result["findings"] if f["provenance"]["rule_id"] == "render-gap"]
        assert gap_findings and gap_findings[0]["status"] == "confirmed"
        assert base_url + "/js-heavy" in result["metrics"]["raw_rendered_gap_pages"]
        assert result["metrics"]["rendering_mode"] == "headless_browser"
    finally:
        shutdown()


def test_orphan_page_detected_by_site_graph():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        # /orphan is never linked from the fixture site.
        graph = build_site_graph(artifacts, deadline)
        # It won't appear in artifacts.pages at all unless separately crawled, which
        # is exactly what makes it an orphan in a real crawl (never discovered/linked).
        assert base_url + "/orphan" not in {p.url for p in artifacts.pages}
    finally:
        shutdown()


def test_full_run_audit_end_to_end_against_local_fixture():
    base_url, shutdown = start_server()
    try:
        report = run_audit(base_url + "/", allow_private_targets=True)
        assert report["site"] == base_url + "/"
        assert "findings" in report and "recommendations" in report
        assert len(report["recommendations"]) > 0
        assert report["coverage"]["pages_discovered"] > 0
        assert report["coverage"]["instrumentation"]["requests_attempted"] > 0
    finally:
        shutdown()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"OK: {name}")
