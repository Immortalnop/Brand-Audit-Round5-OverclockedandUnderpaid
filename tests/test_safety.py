"""test_safety.py -- Priority-1 hard safety requirements: SSRF/URL validation,
robots.txt failure handling (never fail open), streaming byte budgets, redirect
safety, and a read-only-methods guard. All network-free: SSRF classification is
unit-tested directly (with DNS resolution mocked where needed), and acquisition
behavior is tested against the local fixture server.
"""
import ast
import os
import socket
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
from url_safety import classify_url, is_safe_url, same_origin

from fixtures_server import start_server


# ---------------------------------------------------------------------------
# url_safety unit tests
# ---------------------------------------------------------------------------

def test_rejects_disallowed_schemes():
    for scheme in ("ftp://example.com/", "file:///etc/passwd", "javascript:alert(1)", "gopher://x/"):
        assert not is_safe_url(scheme), scheme


def test_rejects_credentials_in_url():
    assert not is_safe_url("http://user:pass@example.com/")


def test_rejects_loopback_by_default():
    r = classify_url("http://127.0.0.1/", allow_private=False)
    assert not r.safe and r.reason == "loopback_address"
    r6 = classify_url("http://[::1]/", allow_private=False)
    assert not r6.safe


def test_rejects_private_ranges_by_default():
    for host in ("http://10.1.2.3/", "http://192.168.1.1/", "http://172.16.0.5/"):
        r = classify_url(host, allow_private=False)
        assert not r.safe and r.reason == "private_address", host


def test_rejects_link_local_and_metadata_even_with_allow_private():
    # 169.254.169.254 (cloud instance metadata) is blocked unconditionally --
    # allow_private only exists for test loopback targets, never for this.
    r = classify_url("http://169.254.169.254/latest/meta-data/", allow_private=True)
    assert not r.safe and r.reason == "cloud_metadata_address"
    r2 = classify_url("http://metadata.google.internal/", allow_private=True)
    assert not r2.safe and r2.reason == "cloud_metadata_hostname"


def test_allows_loopback_when_allow_private_true():
    r = classify_url("http://127.0.0.1:8080/", allow_private=True)
    assert r.safe


def test_dns_resolution_failure_is_unsafe_not_skipped(monkeypatch):
    def _boom(*a, **k):
        raise socket.gaierror("simulated resolution failure")
    monkeypatch.setattr(socket, "getaddrinfo", _boom)
    r = classify_url("http://this-host-does-not-resolve.invalid/", allow_private=True)
    assert not r.safe and r.reason == "dns_resolution_failed"


def test_same_origin_matches_scheme_host_port():
    assert same_origin("http://example.com/a", "http://example.com")
    assert not same_origin("https://example.com/a", "http://example.com")
    assert not same_origin("http://evil.com/a", "http://example.com")
    assert same_origin("https://www.nytimes.com/robots.txt", "https://nytimes.com")
    assert same_origin("https://nytimes.com/robots.txt", "https://www.nytimes.com")
    assert same_origin("http://www2.pnwx.com/", "http://pnwx.com")
    assert not same_origin("https://evilnytimes.com/", "https://nytimes.com")
    assert not same_origin("https://notnytimes.com/", "https://nytimes.com")


# ---------------------------------------------------------------------------
# acquire_site: initial URL SSRF gate
# ---------------------------------------------------------------------------

def test_initial_url_blocked_by_default_when_private():
    limits = Limits()
    deadline = make_deadline(limits)
    instrumentation = Instrumentation()
    # allow_private_targets defaults to False: a loopback target must be blocked,
    # not silently crawled, even though no server needs to be running to prove it.
    artifacts = acquire_site("http://127.0.0.1:1/", deadline, limits, instrumentation)
    assert artifacts.pages == ()
    assert any("initial_url_blocked" in w for w in artifacts.warnings)
    assert len(instrumentation.safety_blocks) == 1


def test_initial_url_allowed_when_flag_set_and_server_present():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert len(artifacts.pages) > 0
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# robots.txt: every state, and "never fail open"
# ---------------------------------------------------------------------------

def test_robots_absent_is_allow_all():
    base_url, shutdown = start_server(robots_mode="absent")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.robots_data["status"] == "absent"
        assert artifacts.robots_data["allowed_general"] is True
        assert artifacts.robots_data["conservative_fail_closed"] is False
        assert len(artifacts.pages) > 1  # normal multi-page crawl proceeded
    finally:
        shutdown()


def test_robots_ok_allow_all_crawls_normally():
    base_url, shutdown = start_server(robots_mode="ok")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.robots_data["status"] == "ok"
        assert artifacts.robots_data["general_disallow"] is False
        assert len(artifacts.pages) > 1
    finally:
        shutdown()


def test_robots_disallow_all_blocks_every_page():
    from fixtures_server import _ROBOTS_DISALLOW_ALL
    base_url, shutdown = start_server(robots_body=_ROBOTS_DISALLOW_ALL, robots_mode="ok")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.robots_data["general_disallow"] is True
        assert artifacts.pages == ()
    finally:
        shutdown()


def test_robots_timeout_fails_closed_not_open():
    base_url, shutdown = start_server(robots_mode="timeout", slow_delay_s=0.3)
    try:
        limits = replace(Limits(), PER_FETCH_TIMEOUT_MS=100)  # shorter than the 0.3s delay
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.robots_data["status"] == "timeout"
        assert artifacts.robots_data["conservative_fail_closed"] is True
        assert artifacts.robots_data["general_disallow"] is None  # never inferred, never fabricated
        # Conservative crawl: at most the single initial page, never the full site.
        assert len(artifacts.pages) <= 1
        assert any("robots_txt_timeout_conservative_crawl" in w for w in artifacts.warnings)
    finally:
        shutdown()


def test_robots_inaccessible_fails_closed():
    base_url, shutdown = start_server(robots_mode="error")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.robots_data["status"] == "inaccessible"
        assert artifacts.robots_data["conservative_fail_closed"] is True
        assert len(artifacts.pages) <= 1
    finally:
        shutdown()


def test_robots_malformed_fails_closed():
    base_url, shutdown = start_server(robots_mode="malformed")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.robots_data["status"] == "malformed"
        assert artifacts.robots_data["conservative_fail_closed"] is True
        assert len(artifacts.pages) <= 1
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# sitemap.xml / llms.txt: actually fetched, states distinguished
# ---------------------------------------------------------------------------

def test_sitemap_ok_is_discovered_and_parsed():
    base_url, shutdown = start_server(sitemap_mode="ok")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.sitemap_data["status"] == "ok"
        assert artifacts.sitemap_data["discovered"] is True
        assert len(artifacts.sitemap_data["urls"]) == 2
    finally:
        shutdown()


def test_sitemap_absent_is_recorded_not_fabricated():
    base_url, shutdown = start_server(sitemap_mode="absent")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.sitemap_data["status"] == "absent"
        assert artifacts.sitemap_data["discovered"] is False
    finally:
        shutdown()


def test_sitemap_malformed_is_distinguished_from_absent():
    base_url, shutdown = start_server(sitemap_mode="malformed")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.sitemap_data["status"] == "malformed"
    finally:
        shutdown()


def test_llms_txt_present_is_actually_fetched():
    base_url, shutdown = start_server(llms_txt_mode="ok")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.llms_txt_data == {"present": True, "status": "ok"}
    finally:
        shutdown()


def test_llms_txt_absent_is_actually_checked():
    base_url, shutdown = start_server(llms_txt_mode="absent")
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        assert artifacts.llms_txt_data == {"present": False, "status": "absent"}
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# byte-budget streaming: enforced during download, not after
# ---------------------------------------------------------------------------

def test_large_response_is_truncated_mid_stream_not_after_full_download():
    base_url, shutdown = start_server(big_body_bytes=2_000_000)
    try:
        limits = replace(Limits(), MAX_TOTAL_BYTES=10_000)  # far smaller than /big's 2MB
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        artifacts = acquire_site(base_url + "/big", deadline, limits, instrumentation,
                                  allow_private_targets=True)
        assert instrumentation.responses_truncated >= 1
        # The retained page content must be bounded near the budget, not the full 2MB.
        page = artifacts.pages[0]
        assert len(page.visible_text) <= limits.VISIBLE_TEXT_MAX_CHARS
        assert instrumentation.bytes_downloaded <= limits.MAX_TOTAL_BYTES + 8192  # one chunk of slack
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# redirect safety: same-origin enforced, cross-origin redirects not followed
# ---------------------------------------------------------------------------

def test_same_origin_redirect_is_followed():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        artifacts = acquire_site(base_url + "/", deadline, limits, allow_private_targets=True)
        redirected_page = next(p for p in artifacts.pages if p.url == base_url + "/redirect")
        assert redirected_page.status_code == 200  # followed through to /about
        assert any(w.startswith("redirected_") for w in redirected_page.warnings)
    finally:
        shutdown()


def test_cross_origin_redirect_is_not_followed():
    base_url, shutdown = start_server()
    try:
        limits = Limits()
        deadline = make_deadline(limits)
        instrumentation = Instrumentation()
        artifacts = acquire_site(base_url + "/redirect-external", deadline, limits, instrumentation,
                                  allow_private_targets=True)
        page = artifacts.pages[0]
        assert "fetch_cross_origin_redirect_blocked" in page.warnings
        # Never actually reached the cross-origin target.
        assert "example.invalid.test" not in "".join(instrumentation.pages_skipped_reasons)
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# read-only guarantee: static guard against mutating HTTP methods
# ---------------------------------------------------------------------------

def test_acquire_site_never_calls_mutating_http_methods():
    src = open(os.path.join(_ROOT, "skills/audit-orchestrator/scripts/acquire_site.py")).read()
    tree = ast.parse(src)
    mutating = {"post", "put", "patch", "delete", "request"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in mutating:
            raise AssertionError(f"acquire_site.py calls requests.{node.attr} -- must be GET-only")


def test_rendering_script_never_submits_forms_or_evaluates_js():
    src = open(os.path.join(_ROOT, "skills/crawl-render-audit/scripts/analyze_rendering.py")).read()
    tree = ast.parse(src)
    forbidden = {"click", "fill", "type", "evaluate", "check", "select_option", "set_input_files"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            raise AssertionError(f"analyze_rendering.py calls page.{node.attr} -- rendering must stay read-only")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and "monkeypatch" not in fn.__code__.co_varnames:
            fn()
            print(f"OK: {name}")
