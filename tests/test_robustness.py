"""test_robustness.py -- a valid, honest report on every run (Plan phase 5).

  - Empty or blocked acquisition: with no page analyzed, the report keeps only
    checks that never read page content, its status is insufficient_evidence,
    and the summary, limitations and confidence lead with the reason.
  - Bot challenges: interstitials are recognised, never analyzed as content,
    never retried, and a run of them ends the crawl.
  - Encoding: byte order mark, HTTP charset, <meta charset>, UTF-8, and a
    windows-1252 fallback for mislabelled single-byte pages.
  - --out writes the report as UTF-8 whatever the shell.

Every site is served from 127.0.0.1 (tests/archetype_sites.py); nothing here
touches the network.
"""
import json
import io
import os
import sys
from dataclasses import replace

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from archetype_sites import ALLOW_ALL, CHALLENGE_PAGE, FASTLY_CHALLENGE_PAGE, ROBUSTNESS, serve
from acquire_site import acquire_site, acquisition_failure
from bot_challenge import challenge_signals
from constants import Limits
from execution_summary import overall_confidence
from instrumentation import Instrumentation
from models import make_deadline
from transport import Response, decode_body, detect_encoding

LIMITS = Limits()
CURLY = "\u2019"
E_ACUTE = "\u00e9"

_OFFLINE_ENV = {"SEARCH_API_URL": "", "SEARCH_API_KEY": "", "PAGESPEED_API_KEY": "", "FIELD_VITALS_LOOKUP": "0",
                "AGENT_FINDINGS_PATH": "", "OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0",
                "ENABLE_RENDERING": "0", "AUDIT_PROGRESS": "0"}


def acquire(site):
    """Acquisition only (no analysis, no worker process): (artifacts, requests)."""
    base, stop, seen = serve(site)
    try:
        artifacts = acquire_site(base + "/", make_deadline(LIMITS), LIMITS, Instrumentation(),
                                 allow_private_targets=True)
    finally:
        stop()
    return base, artifacts, list(seen)


@pytest.fixture(scope="module")
def audits():
    """Full audits of the blocked sites, run once for the module."""
    from run_audit import run_audit
    sites = {
        "guarded": ROBUSTNESS["guarded"],
        "mixed_guard": ROBUSTNESS["mixed_guard"],
        "fastly_guarded": {**ROBUSTNESS["guarded"], "responses": {
            p: (200, FASTLY_CHALLENGE_PAGE, "text/html; charset=utf-8")
            for p in ROBUSTNESS["guarded"]["responses"]}},
        "fastly_mixed": {**ROBUSTNESS["mixed_guard"], "pages": {
            path: body.replace('</body>', '<script src="/_fs-ch-example/challenge.js" defer></script></body>')
            for path, body in ROBUSTNESS["mixed_guard"]["pages"].items()}, "responses": {
                "/members": (200, FASTLY_CHALLENGE_PAGE, "text/html; charset=utf-8")}},
        "forbidden": {"robots": ALLOW_ALL, "pages": {},
                      "responses": {"/": (403, "<html><body><h1>Forbidden</h1></body></html>", "text/html")}},
        "disallowed": {"robots": "User-agent: *\nDisallow: /\n", "pages": {"/": "<p>Hello</p>"}},
    }
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    out = {}
    try:
        for name, site in sites.items():
            base, stop, seen = serve(site)
            try:
                out[name] = (base, run_audit(base + "/", limits=LIMITS, allow_private_targets=True), list(seen))
            finally:
                stop()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return out


# ---------------------------------------------------------------------------
# Empty or blocked acquisition
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,reason,stage,status", [
    ("guarded", "blocked_by_challenge", "start_url", 403),
    ("forbidden", "access_denied", "start_url", 403),
    ("disallowed", "robots_disallowed", "start_url", None),
])
def test_zero_page_report_is_insufficient_evidence_with_its_reason(audits, name, reason, stage, status):
    from run_audit import SITE_LEVEL_CHECKS
    from validate_report import validate_report
    _, report, _ = audits[name]
    failure = report["coverage"]["acquisition_failure"]
    assert report["coverage"]["pages_analyzed"] == 0
    assert report["execution_status"] == "insufficient_evidence"
    assert (failure["reason"], failure["stage"], failure["http_status"]) == (reason, stage, status)
    # The reason leads the summary, the limitations and the confidence explanation.
    assert next(iter(report["summary"])) == "status_reason"
    assert report["summary"]["status_reason"] == failure["detail"]
    assert report["limitations"][0].startswith(failure["detail"])
    assert report["confidence"]["score"] == 0.0 and report["confidence"]["limiting_factor"] == "execution_penalty"
    assert failure["detail"] in report["confidence"]["explanation"]
    # Nothing drawn from page content is reported.
    for item in report["findings"] + report["recommendations"]:
        for check_id in item.get("check_ids") or [item["check_id"]]:
            assert check_id in SITE_LEVEL_CHECKS or check_id.startswith("baseline:"), check_id
    # Still a valid report.
    assert len(validate_report(report, strict_catalog=True)["findings"]) == len(report["findings"])


def test_site_level_findings_survive_a_zero_page_run(audits):
    _, report, _ = audits["disallowed"]
    checks = {f["check_id"] for f in report["findings"]}
    assert {"robots-block", "ai-crawler-blocked"} <= checks


def test_access_denied_start_page_is_not_reported_as_a_broken_page(audits):
    _, report, _ = audits["forbidden"]
    assert "broken-pages" not in {f["check_id"] for f in report["findings"]}


def test_markdown_leads_with_the_reason(audits):
    from report_markdown import render
    _, report, _ = audits["guarded"]
    md = render(report)
    assert "**Why this report is short:**" in md
    assert md.index("Why this report is short") < md.index("| Findings |")
    assert "No page could be analyzed, so the site's pages were not assessed" in md
    assert "Pages that answered with a bot challenge:** 2" in md


@pytest.mark.parametrize("args,reason,stage", [
    (("dns_error", None, "inaccessible", [], None, None), "dns_error", "robots_txt"),
    (("tls_certificate_error", None, "inaccessible", [], None, None), "tls_error", "robots_txt"),
    (("timeout", None, "timeout", [], None, None), "timeout", "robots_txt"),
    (("ok", 403, "inaccessible", ["cf_challenge"], None, None), "blocked_by_challenge", "robots_txt"),
    (("ok", 401, "inaccessible", [], None, None), "access_denied", "robots_txt"),
    (("ok", 429, "inaccessible", [], None, None), "rate_limited", "robots_txt"),
    (("ok", 200, "malformed", [], None, None), "robots_unavailable", "robots_txt"),
    (("ok", 200, "ok", [], False, None), "not_fetched", "start_url"),
    (("ok", 200, "ok", [], False, {"fetch_status": "cross_origin_redirect_blocked", "http_status": None}),
     "cross_origin_redirect", "start_url"),
    (("ok", 404, "absent", [], False, {"fetch_status": "dns_error", "http_status": None}), "dns_error", "start_url"),
    (("ok", 200, "ok", [], False, {"fetch_status": "ok", "http_status": 429, "challenge": []}),
     "rate_limited", "start_url"),
    (("ok", 200, "ok", [], False, {"fetch_status": "ok", "http_status": 410, "challenge": []}),
     "not_found", "start_url"),
    (("ok", 200, "ok", [], False, {"fetch_status": "ok", "http_status": 502, "challenge": []}),
     "server_error", "start_url"),
    (("ok", 200, "ok", [], False, {"fetch_status": "ok", "http_status": 200, "challenge": [], "login": True}),
     "login_page", "start_url"),
    (("ok", 200, "ok", [], False, {"fetch_status": "ok", "http_status": 200, "challenge": []}),
     "no_content", "start_url"),
])
def test_failure_reasons(args, reason, stage):
    fetch, http, robots_status, challenge, disallow, start = args
    failure = acquisition_failure("https://site.test/robots.txt", fetch, http, robots_status, challenge, disallow,
                                  "https://site.test/", start)
    assert (failure["reason"], failure["stage"]) == (reason, stage)
    assert failure["detail"].startswith("No page could be analyzed: ") and failure["detail"].endswith(".")
    assert "\u2014" not in failure["detail"]


def test_confidence_names_the_reason_without_a_report():
    failure = {"reason": "dns_error", "detail": "No page could be analyzed: the host name could not be resolved "
                                                "(DNS) (while reading robots.txt)."}
    conf = overall_confidence({"pages_discovered": 1, "pages_analyzed": 0, "acquisition_failure": failure},
                              "insufficient_evidence")
    assert conf["score"] == 0.0 and conf["level"] == "low"
    assert conf["reasons"]["execution_penalty"] == failure["detail"]


def test_safety_blocked_start_url_has_a_reason():
    artifacts = acquire_site("http://169.254.169.254/", make_deadline(LIMITS), LIMITS, Instrumentation())
    failure = artifacts.acquisition_metadata["acquisition_failure"]
    assert failure["reason"] == "blocked_by_safety_policy" and not artifacts.pages


def test_analyzed_run_has_no_failure_block():
    _, artifacts, _ = acquire(ROBUSTNESS["mixed_guard"])
    assert "acquisition_failure" not in artifacts.acquisition_metadata


# ---------------------------------------------------------------------------
# Bot challenges
# ---------------------------------------------------------------------------

def test_challenges_end_the_crawl_without_retries(audits):
    base, report, seen = audits["guarded"]
    page_requests = [path for _, path in seen if path not in ("/robots.txt", "/sitemap.xml", "/llms.txt",
                                                                "/llms-full.txt")]
    # Two challenges in a row end the crawl; each URL is requested once.
    assert len(page_requests) == 2 and len(set(page_requests)) == 2
    assert all(method == "GET" for method, _ in seen)
    cov = report["coverage"]
    assert cov["pages_challenged"] == 2 and cov["crawl_stopped_by_challenge"] is True
    assert cov["challenged_pages"][0]["signals"] and cov["challenged_pages"][0]["http_status"] == 403
    assert any("bot-protection challenge" in w for w in report["warnings"])


def test_one_challenged_section_is_skipped_not_reported(audits):
    base, report, seen = audits["mixed_guard"]
    cov = report["coverage"]
    assert report["execution_status"] != "insufficient_evidence" and cov["acquisition_failure"] is None
    assert cov["pages_analyzed"] == 2 and cov["pages_challenged"] == 1
    assert cov["crawl_stopped_by_challenge"] is False
    assert [p["url"] for p in cov["challenged_pages"]] == [base + "/members"]
    for item in report["findings"] + report["recommendations"]:
        assert base + "/members" not in item.get("affected_pages", []), item["check_id"]
    assert any("bot-protection challenge" in line for line in report["limitations"])


def _cf_normal_page():
    # Several protection layers inject a detection script into every page.
    return ("<html><head><title>Docs</title></head><body>" + "<p>Real documentation text. </p>" * 120
            + "<script src=\"/cdn-cgi/challenge-platform/scripts/jsd/main.js\"></script></body></html>")


@pytest.mark.parametrize("status,headers,body,title,chars,expected", [
    (403, {}, CHALLENGE_PAGE, "Just a moment...", 0, True),
    (503, {}, "<script src='https://ct.captcha-delivery.com/c.js'></script>", "", 0, True),
    (429, {}, "<div id='px-captcha'></div>", "Access to this page has been denied", 0, True),
    (403, {"CF-Mitigated": "challenge"}, "", "", 0, True),
    (202, {"x-amzn-waf-action": "challenge"}, "", "", 0, True),
    (200, {}, CHALLENGE_PAGE.replace("_cf_chl_opt", "cf_chl_opt"), "Just a moment...", 40, True),
    # Normal pages.
    (200, {}, _cf_normal_page(), "Docs", 3000, False),
    (200, {}, "<p>Run a security check on your home.</p>", "Security check", 40, False),
    (403, {}, "<h1>Forbidden</h1>", "403 Forbidden", 9, False),
    (404, {}, CHALLENGE_PAGE, "Just a moment...", 0, False),
    (200, {"cf-mitigated": "none"}, "<p>ok</p>", "Home", 2, False),
])
def test_challenge_signals(status, headers, body, title, chars, expected):
    assert bool(challenge_signals(status, headers, body, title, chars)) is expected


def test_challenge_in_place_of_a_file_is_inaccessible_not_malformed():
    challenge_200 = (200, CHALLENGE_PAGE.replace("_cf_chl_opt", "cf_chl_opt"), "text/html")
    site = {"robots": ALLOW_ALL, "pages": {"/": "<html><body><p>" + "Public page text. " * 30 + "</p></body></html>"},
            "responses": {"/sitemap.xml": challenge_200, "/llms.txt": challenge_200, "/llms-full.txt": challenge_200}}
    _, artifacts, _ = acquire(site)
    assert artifacts.sitemap_data["status"] == "inaccessible"
    assert artifacts.llms_txt_data["status"] == "inaccessible"
    assert artifacts.llms_txt_data["full"]["status"] == "inaccessible"
    assert len(artifacts.pages) == 1


def test_off_site_profile_challenge_is_unverified_not_broken():
    from check_off_site_profiles import evaluate_profile
    resp = Response(403, {"Content-Type": "text/html"}, CHALLENGE_PAGE.encode(), "https://social.test/brand")
    assert evaluate_profile("https://social.test/brand", resp, "ok", "brand.test", ["Brand"]) == (
        "unverified", "bot_challenge")


@pytest.mark.parametrize("status", [200, 202, 403, 405, 429, 503])
def test_fastly_client_challenge_is_recognized(status):
    assert challenge_signals(status, {}, FASTLY_CHALLENGE_PAGE, "Client Challenge", 160) == [
        "fastly_challenge", "challenge_title"]


@pytest.mark.parametrize("status", [200, 201, 204, 302, 404, 500])
@pytest.mark.parametrize("title,body,chars", [
    # Fastly's documented embedded script is allowed on an ordinary thin page.
    ("Home", '<h1>Welcome</h1><script src="/_fs-ch-1T1wmsGaOgGaSxcX/challenge.js" defer></script>', 40),
    # A title without a provider marker is not sufficient.
    ("Client Challenge", '<h1>Client Challenge</h1><p>Our client design brief.</p>', 60),
    # A short article can discuss the title and show the provider's path.
    ("Client Challenge integration guide", '<p>Example: /_fs-ch-example/challenge.js</p>', 60),
    # Even an exact title and provider marker do not exclude substantial content.
    ("Client Challenge", FASTLY_CHALLENGE_PAGE + '<p>' + 'Documentation. ' * 100 + '</p>', 1500),
])
def test_fastly_markers_do_not_hide_normal_pages(status, title, body, chars):
    assert challenge_signals(status, {}, body, title, chars) == []


def test_fastly_interstitial_without_title_or_on_unrelated_error_is_not_assumed():
    assert challenge_signals(200, {}, FASTLY_CHALLENGE_PAGE, "", 160) == []
    assert challenge_signals(404, {}, FASTLY_CHALLENGE_PAGE, "Client Challenge", 160) == []
    # File probes supply no visible-text count; the existing small-body guard applies.
    assert challenge_signals(200, {}, FASTLY_CHALLENGE_PAGE, "Client Challenge") == [
        "fastly_challenge", "challenge_title"]
    assert challenge_signals(200, {}, FASTLY_CHALLENGE_PAGE + " " * 20000, "Client Challenge") == []


@pytest.mark.parametrize("body", [
    '<title>Home</title><script src="/_fs-ch-example/challenge.js" defer></script>',
    '<title>Client Challenge integration guide</title><p>Example: /_fs-ch-example/challenge.js</p>',
    '<!-- <title>Client Challenge</title> --><p>Example: /_fs-ch-example/challenge.js</p>',
    '<svg><title>Client Challenge</title></svg><p>Example: /_fs-ch-example/challenge.js</p>',
    '<title>Client<!-- comment -->Challenge</title><p>Example: /_fs-ch-example/challenge.js</p>',
])
def test_fastly_title_fallback_preserves_embedded_scripts_and_examples(body):
    assert challenge_signals(200, {}, body) == []


def test_fastly_title_fallback_decodes_html_and_respects_scan_bound():
    body = FASTLY_CHALLENGE_PAGE.replace('Client Challenge', 'client&#32;challenge')
    assert challenge_signals(200, {}, body) == ["fastly_challenge", "challenge_title"]
    assert challenge_signals(200, {}, " " * 65536 + body, "Client Challenge", 160) == []


def test_fastly_guarded_report_has_no_content_findings_and_stops(audits):
    from run_audit import SITE_LEVEL_CHECKS
    from validate_report import validate_report
    _, report, seen = audits["fastly_guarded"]
    cov = report["coverage"]
    assert len(validate_report(report, strict_catalog=True)["findings"]) == len(report["findings"])
    assert report["execution_status"] == "insufficient_evidence"
    assert cov["pages_analyzed"] == 0 and cov["pages_challenged"] == 2
    assert cov["acquisition_failure"]["reason"] == "blocked_by_challenge"
    assert cov["crawl_stopped_by_challenge"] is True
    assert all(p["http_status"] == 200 and p["signals"] == ["fastly_challenge", "challenge_title"]
               for p in cov["challenged_pages"])
    for item in report["findings"] + report["recommendations"]:
        assert all(check_id in SITE_LEVEL_CHECKS or check_id.startswith("baseline:")
                   for check_id in item.get("check_ids") or [item["check_id"]])
    # No retry, rendering or Fastly asset fetch occurs; crawl ends after two pages.
    page_requests = [path for _, path in seen if path not in (
        "/robots.txt", "/sitemap.xml", "/llms.txt", "/llms-full.txt")]
    assert page_requests == ["/", "/about"]
    assert seen[-2:] == [("GET", "/"), ("GET", "/about")]


def test_fastly_mixed_report_preserves_real_pages(audits):
    base, report, _ = audits["fastly_mixed"]
    cov = report["coverage"]
    assert report["execution_status"] != "insufficient_evidence"
    assert cov["pages_analyzed"] == 2 and cov["pages_challenged"] == 1
    assert cov["crawl_stopped_by_challenge"] is False
    assert [p["url"] for p in cov["challenged_pages"]] == [base + "/members"]
    for item in report["findings"] + report["recommendations"]:
        assert base + "/members" not in item.get("affected_pages", []), item["check_id"]
    assert any("bot-protection challenge" in line for line in report["limitations"])


@pytest.mark.parametrize("path", ["/sitemap.xml", "/llms.txt", "/llms-full.txt"])
def test_fastly_in_place_of_a_file_is_inaccessible(path):
    site = {"robots": ALLOW_ALL, "pages": {"/": "<h1>Home</h1><p>Public page text.</p>"},
            "responses": {path: (200, FASTLY_CHALLENGE_PAGE, "text/html; charset=utf-8")}}
    _, artifacts, seen = acquire(site)
    data = (artifacts.sitemap_data if path == "/sitemap.xml" else artifacts.llms_txt_data
            if path == "/llms.txt" else artifacts.llms_txt_data["full"])
    assert data["status"] == "inaccessible"
    assert len(artifacts.pages) == 1
    assert sum(request_path == path for _, request_path in seen) == 1


def test_fastly_off_site_profile_is_unverified_not_broken():
    from check_off_site_profiles import evaluate_profile
    resp = Response(200, {"Content-Type": "text/html"}, FASTLY_CHALLENGE_PAGE.encode(), "https://social.test/brand")
    assert evaluate_profile("https://social.test/brand", resp, "ok", "brand.test", ["Brand"]) == (
        "unverified", "bot_challenge")


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

LEGACY = "\u201cCaf\u00e9\u201d we\u2019re"


@pytest.mark.parametrize("body,ctype,codec,source", [
    (b"\xef\xbb\xbf<p>hi</p>", "text/html; charset=iso-8859-1", "utf-8", "bom"),
    (b"\xff\xfeh\x00i\x00", "text/plain", "utf-16-le", "bom"),
    (b"<p>x</p>", "text/html; charset=Shift_JIS", "shift_jis", "http"),
    (b"<p>x</p>", "text/html; charset=ISO-8859-1", "cp1252", "http"),
    (b'<meta charset="windows-1252"><p>x</p>', "text/html", "cp1252", "meta"),
    (b'<meta http-equiv="Content-Type" content="text/html; charset=koi8-r">', "text/html", "koi8-r", "meta"),
    (b'<meta charset="utf-16"><p>x</p>', "text/html", "utf-8", "meta"),
    # Labels that are not web encodings are ignored.
    (b'<meta charset="base64"><p>x</p>', "text/html", "utf-8", "default"),
    (b"<p>x</p>", "text/html; charset=rot13", "utf-8", "default"),
    # A meta tag past the first 2 KB, or in a non-HTML body, is not read.
    (b" " * 2100 + b'<meta charset="windows-1252">', "text/html", "utf-8", "default"),
    (b'<meta charset="windows-1252">', "text/plain", "utf-8", "default"),
])
def test_detect_encoding(body, ctype, codec, source):
    assert detect_encoding(body, ctype) == (codec, source)


def test_decode_body_reads_declared_and_mislabelled_pages():
    meta = b'<meta charset="windows-1252"><p>' + LEGACY.encode("cp1252") + b"</p>"
    text, codec, source = decode_body(meta, "text/html")
    assert LEGACY in text and "\ufffd" not in text and (codec, source) == ("cp1252", "meta")
    # Declared UTF-8 but written in windows-1252: read as windows-1252.
    text, codec, source = decode_body(b"<p>" + LEGACY.encode("cp1252") * 3 + b"</p>", "text/html; charset=utf-8")
    assert LEGACY in text and (codec, source) == ("cp1252", "utf8_fallback")
    # A real UTF-8 page with a few stray bytes stays UTF-8.
    real = ("<p>" + LEGACY * 20 + "</p>").encode("utf-8") + b"\xff\xfe\xfd"
    text, codec, source = decode_body(real, "text/html; charset=utf-8")
    assert codec == "utf-8" and LEGACY in text
    # The byte order mark is not text.
    assert decode_body(b"\xef\xbb\xbfUser-agent: *", "text/plain")[0] == "User-agent: *"


def test_response_text_is_decoded_on_first_use_only():
    resp = Response(200, {"Content-Type": "image/png"}, b"\x89PNG\r\n", "https://site.test/a.png")
    assert "_decoded" not in resp.__dict__ and resp.ok
    assert resp.encoding == "utf-8" and "_decoded" in resp.__dict__


def test_legacy_encoded_page_is_read_correctly_end_to_end():
    _, artifacts, _ = acquire(ROBUSTNESS["legacy_encoding"])
    (page,) = artifacts.pages
    assert "we" + CURLY + "re known for" in page.visible_text
    assert "Caf" + E_ACUTE + " Rue Barr" + E_ACUTE == page.title
    assert "\ufffd" not in page.visible_text


def test_robots_txt_byte_order_mark_does_not_hide_the_first_rule():
    site = {"pages": {"/": "<html><body><p>" + "Public page text. " * 30 + '</p><a href="/private/x">x</a>'
                           "</body></html>",
                      "/private/x": "<p>secret</p>"},
            "responses": {"/robots.txt": (200, b"\xef\xbb\xbfUser-agent: *\nDisallow: /private/\n", "text/plain")}}
    _, artifacts, seen = acquire(site)
    assert artifacts.robots_data["status"] == "ok"
    assert ("GET", "/private/x") not in seen


# ---------------------------------------------------------------------------
# --out
# ---------------------------------------------------------------------------

def _fake_run(monkeypatch, report):
    import run_audit
    calls = []
    monkeypatch.setattr(run_audit, "run_audit", lambda site, limits=None: calls.append(site) or report)
    return run_audit, calls


def test_out_writes_utf8_json_and_keeps_stdout_clean(monkeypatch, tmp_path, capsys):
    report = {"site": "https://site.test/", "note": "caf" + E_ACUTE + " we" + CURLY + "re \u0420\u0435\u0448\u0435\u043d\u0438\u044f \u4e2d\u6587 \U0001f600", "coverage": {}}
    module, calls = _fake_run(monkeypatch, report)
    target = tmp_path / "report.json"
    module.main(["https://site.test/", "--out", str(target), "--quiet"])
    captured = capsys.readouterr()
    assert captured.out == "" and "written to" in captured.err
    raw = target.read_bytes()
    assert not raw.startswith((b"\xff\xfe", b"\xfe\xff", b"\xef\xbb\xbf"))
    assert json.loads(raw.decode("utf-8")) == report
    assert report['note'].encode('utf-8') in raw  # --out keeps literal Unicode
    assert [p.name for p in tmp_path.iterdir()] == ["report.json"]  # no temporary file left


@pytest.mark.parametrize("make_target", [lambda tmp: tmp, lambda tmp: tmp / "missing" / "r.json"])
def test_out_rejects_a_bad_path_before_auditing(monkeypatch, tmp_path, make_target):
    module, calls = _fake_run(monkeypatch, {"coverage": {}})
    with pytest.raises(SystemExit) as exc:
        module.main(["https://site.test/", "--out", str(make_target(tmp_path)), "--quiet"])
    assert exc.value.code == 2 and calls == []


def test_out_falls_back_to_stdout_when_the_file_cannot_be_written(monkeypatch, tmp_path, capsys):
    report = {"site": "https://site.test/", "coverage": {}}
    module, _ = _fake_run(monkeypatch, report)

    def fail(*_args, **_kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(module, "write_report", fail)
    module.main(["https://site.test/", "--out", str(tmp_path / "r.json"), "--quiet"])
    captured = capsys.readouterr()
    assert json.loads(captured.out) == report and "could not write" in captured.err


@pytest.mark.parametrize('encoding', ['ascii', 'cp1252', 'cp1251', 'utf-8'])
@pytest.mark.parametrize('fallback', [False, True])
def test_cli_unicode_json_survives_strict_stdout_encodings(monkeypatch, tmp_path, encoding, fallback):
    # Windows redirection uses a strict legacy text stream. Exercise the real
    # CLI emitter, including its file-failure fallback, without a live crawl.
    report = {'site': 'https://site.test/', 'coverage': {},
              '\u4fe1\u606f': '\u0420\u0435\u0448\u0435\u043d\u0438\u044f caf\u00e9 \u4e2d\u6587 \U0001f600',
              'packet_sha256': 'a' * 64, 'confidence': .75}
    module, calls = _fake_run(monkeypatch, report)
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding=encoding, errors='strict')
    monkeypatch.setattr(sys, 'stdout', stream)
    args = ['https://site.test/', '--quiet']
    if fallback:
        def fail(*_args, **_kwargs):
            raise PermissionError('denied')
        monkeypatch.setattr(module, 'write_report', fail)
        args.extend(['--out', str(tmp_path / 'report.json')])
    module.main(args)
    stream.flush()
    raw = buffer.getvalue()
    assert raw.isascii() and json.loads(raw.decode(encoding)) == report
    assert calls == ['https://site.test/']
    assert list(tmp_path.iterdir()) == []


def test_markdown_tool_reads_a_report_written_with_out(monkeypatch, tmp_path, audits):
    import run_audit
    from report_markdown import main as markdown_main
    _, report, _ = audits["mixed_guard"]
    target = tmp_path / "results.json"
    run_audit.write_report(report, str(target))
    markdown_main([str(target), str(tmp_path / "results.md")])
    assert "# Brand AI-Readiness Audit" in (tmp_path / "results.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------

def test_robustness_corpus_runs_in_the_default_suite():
    assert set(ROBUSTNESS) == {"guarded", "mixed_guard", "legacy_encoding"}


def test_limits_unchanged_by_this_module():
    assert replace(LIMITS) == Limits()
