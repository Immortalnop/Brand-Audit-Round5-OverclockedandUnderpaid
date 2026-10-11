"""test_login_pages_and_confidence.py -- Plan.md points 4 and 13.

Point 4: login and sign-in pages are fetched (a public, read-only GET) but kept
out of the analyzed sample, listed in coverage with their signals, and the report
warns when the start URL is one. A password box in a home page header does not
make the home page a login page, and /author/ is never an auth path.

Point 13: the confidence block explains itself in plain English: a level, the
limiting factor, one reason per component and a short explanation, while the
score stays the plain min() it always was.
"""
import os
import sys
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from auth_pages import auth_path_segment, names_login, is_login_form, login_page_signals
from html_features import Document
from constants import Limits
from models import make_deadline
from acquire_site import acquire_site
from execution_summary import (overall_confidence, identity_resolution, unfinished_confidence,
                               derive_limitations, confidence_level)
from validate_report import validate_report


def _features(html):
    doc = Document()
    doc.feed(html)
    doc.close()
    return doc, doc.features()


def _signals(url, html, final_url=None):
    doc, features = _features(html)
    title = " ".join("".join(doc.title_parts).split()) or None
    return login_page_signals(url, final_url or url, title, doc.headings, features)


_LONG_TEXT = "<p>" + ("Acme University offers degree programmes in science, arts and engineering. " * 30) + "</p>"
_HEADER_LOGIN = ('<header><nav><a href="/">Home</a></nav><form action="/session" id="quick">'
                 '<input type="text" name="user"><input type="password" name="pw">'
                 '<button>Log in</button></form></header>')


# ---------------------------------------------------------------------------
# Auth paths: whole segments only
# ---------------------------------------------------------------------------

def test_auth_path_matches_whole_segments_only():
    assert auth_path_segment("https://x.test/login") == "login"
    assert auth_path_segment("https://x.test/login/faculty") == "login"
    assert auth_path_segment("https://x.test/user/login?destination=/") == "login"
    assert auth_path_segment("https://x.test/wp-login.php") == "wp-login"
    assert auth_path_segment("https://x.test/Sign-In/") == "sign-in"
    assert auth_path_segment("https://x.test/%6Cogin") == "login"
    assert auth_path_segment("https://x.test/register") == "register"
    # Substrings never count.
    assert auth_path_segment("https://x.test/author/jane") is None
    assert auth_path_segment("https://x.test/authors") is None
    assert auth_path_segment("https://x.test/blog/login-tips") is None
    assert auth_path_segment("https://x.test/catalogin") is None
    assert auth_path_segment("https://x.test/") is None
    assert auth_path_segment("") is None
    assert auth_path_segment(None) is None


def test_login_words_need_word_boundaries():
    for text in ("Sign in", "Log in to Acme", "Log-in", "LOGIN", "Member logon", "Anmelden", "ログイン"):
        assert names_login(text), text
    for text in ("Blogging tips", "Catalog in stock", "Design inspiration", "Dialog on mobile", "", None):
        assert not names_login(text), text


def test_is_login_form_reads_action_attributes_and_labels():
    assert is_login_form({"action": "/user/login", "attrs": "", "labels": []})
    assert is_login_form({"action": "", "attrs": "loginform", "labels": []})
    assert is_login_form({"action": "", "attrs": "", "labels": ["Submit", "Sign in"]})
    assert not is_login_form({"action": "/subscribe", "attrs": "newsletter", "labels": ["Submit"]})


# ---------------------------------------------------------------------------
# Parser: visible password inputs and the forms that hold them
# ---------------------------------------------------------------------------

def test_parser_records_visible_password_forms_with_labels():
    _, f = _features('<form action="/auth" id="login-form"><input type="password">'
                     '<input type="submit" value="Sign in"><button>Help</button></form>')
    assert f["password_inputs"] == 1
    assert f["password_forms"] == [{"action": "/auth", "attrs": "login-form", "labels": ["Sign in", "Help"],
                                    "in_chrome": False}]


def test_parser_ignores_hidden_password_inputs():
    _, f = _features('<div style="display:none"><form><input type="password"></form></div>'
                     '<form hidden><input type="password"></form><input type="password" aria-hidden="true">')
    assert f["password_inputs"] == 0
    assert f["password_forms"] == []


def test_parser_marks_forms_in_page_chrome_and_keeps_unclosed_forms():
    _, f = _features(_HEADER_LOGIN)
    assert f["password_forms"][0]["in_chrome"] is True
    _, f = _features('<main><form action="/login"><input type="password"><button>Go')
    assert f["password_inputs"] == 1 and len(f["password_forms"]) == 1
    assert f["password_forms"][0]["in_chrome"] is False


def test_parser_password_outside_a_form_counts_without_a_form_record():
    _, f = _features('<div id="app"><input type="password"></div>')
    assert f["password_inputs"] == 1 and f["password_forms"] == []


# ---------------------------------------------------------------------------
# Page classification
# ---------------------------------------------------------------------------

def test_no_password_input_means_in_scope_even_on_an_auth_path():
    assert _signals("https://x.test/login", "<title>Login</title><p>We moved.</p>") == []


def test_auth_path_with_password_is_out_of_scope():
    s = _signals("https://x.test/login/faculty", "<title>Faculty</title><form><input type='password'></form>")
    assert s[0] == "password_input" and "auth_path:login" in s


def test_redirect_to_login_uses_the_final_url():
    s = _signals("https://x.test/dashboard", "<title>Portal</title><input type='password'>",
                 final_url="https://x.test/login?next=/dashboard")
    assert "auth_path:login" in s


def test_login_title_or_h1_with_password_is_out_of_scope():
    assert "login_title" in _signals("https://x.test/portal", "<title>Sign in to the portal</title>"
                                                              "<input type='password'>")
    assert "login_title" in _signals("https://x.test/portal", "<title>Portal</title><h1>Log in</h1>"
                                                              "<input type='password'>")


def test_login_form_as_main_content_is_out_of_scope():
    s = _signals("https://x.test/portal", "<title>Student portal</title><main><form id='loginform'>"
                                          "<input name='u'><input type='password'><button>Go</button></form></main>")
    assert "login_form" in s and "login_form_is_main_content" in s


def test_home_page_with_a_header_login_box_stays_in_scope():
    html = "<title>Acme University</title>" + _HEADER_LOGIN + "<main><h1>Welcome</h1>" + _LONG_TEXT + "</main>"
    assert _signals("https://x.test/", html) == []
    # A header login box on a short page is still page chrome, not the page's content.
    assert _signals("https://x.test/", "<title>Acme</title>" + _HEADER_LOGIN + "<p>Hi</p>") == []


def test_author_page_with_a_header_login_box_stays_in_scope():
    html = "<title>Jane Doe, author</title>" + _HEADER_LOGIN + "<main><h1>Jane Doe</h1>" + _LONG_TEXT + "</main>"
    assert _signals("https://x.test/author/jane", html) == []


def test_password_form_without_any_login_signal_stays_in_scope():
    html = ("<title>Change settings</title><main><form action='/settings'><input type='password'>"
            "<button>Save</button></form></main>")
    assert _signals("https://x.test/settings", html) == []


def test_long_page_is_never_skipped_whatever_its_login_signals():
    long_login = ("<title>Sign in</title><main><h1>Log in</h1><form action='/login' id='loginform'>"
                  "<input type='password'><button>Sign in</button></form>" + _LONG_TEXT + "</main>")
    assert _signals("https://x.test/login", long_login) == []
    # Just over the limit is kept; at the limit a bare login page is skipped.
    from auth_pages import MAX_LOGIN_PAGE_CHARS
    doc, features = _features("<title>Login</title><input type='password'>")
    for chars, skipped in ((MAX_LOGIN_PAGE_CHARS, True), (MAX_LOGIN_PAGE_CHARS + 1, False)):
        f = dict(features, full_visible_chars=chars)
        assert bool(login_page_signals("https://x.test/login", None, "Login", doc.headings, f)) is skipped


def test_missing_text_length_keeps_the_page():
    doc, features = _features("<title>Login</title><input type='password'>")
    features.pop("full_visible_chars")
    assert login_page_signals("https://x.test/login", None, "Login", doc.headings, features) == []


def test_entity_markup_keeps_a_login_page():
    html = "<title>Login</title><form><input type='password'></form>"
    doc, features = _features(html)
    org = [{"@context": "https://schema.org", "@type": "Organization", "name": "Acme"}]
    assert login_page_signals("https://x.test/login", None, "Login", doc.headings, features, org) == []
    nested = [{"@graph": [{"@type": "WebPage", "publisher": {"@type": "Organization", "name": "Acme"}}]}]
    assert login_page_signals("https://x.test/login", None, "Login", doc.headings, features, nested) == []
    boilerplate = [{"@graph": [{"@type": "WebPage"}, {"@type": "BreadcrumbList",
                                                       "itemListElement": [{"@type": "ListItem"}]}]}]
    assert login_page_signals("https://x.test/login", None, "Login", doc.headings, features, boilerplate)
    # Microdata counts too.
    _, micro = _features('<div itemscope itemtype="https://schema.org/Product"><span>Widget</span></div>' + html)
    assert login_page_signals("https://x.test/login", None, "Login", doc.headings, micro) == []


def test_entity_markup_types_ignores_page_boilerplate():
    from auth_pages import entity_markup_types
    assert entity_markup_types([{"@type": ["WebPage", "WebSite"]}], ["BreadcrumbList"]) == []
    assert entity_markup_types([{"@type": "https://schema.org/Product"}]) == ["Product"]
    assert entity_markup_types((), ["Event"]) == ["Event"]
    assert entity_markup_types(None, None) == []
    assert entity_markup_types(["not a node", 3, {"name": "untyped"}]) == []


def test_frozen_features_are_accepted():
    from models import freeze_value
    doc, features = _features("<title>Login</title><input type='password'>")
    assert login_page_signals("https://x.test/a", None, "Login", tuple(doc.headings), freeze_value(features))


# ---------------------------------------------------------------------------
# Crawl integration against a local server
# ---------------------------------------------------------------------------

_PAGES = {
    "/": ("<html><head><title>Acme University</title></head><body>" + _HEADER_LOGIN +
          "<main><h1>Welcome</h1>" + _LONG_TEXT +
          '<a href="/about">About</a> <a href="/login">Login</a> <a href="/login/faculty">Faculty</a> '
          '<a href="/author/jane">Jane</a> <a href="/portal">Portal</a> <a href="/blog/login-tips">Tips</a> '
          '<a href="/login/help">Help</a> <a href="/signin">Shop sign in</a>'
          "</main></body></html>"),
    "/about": "<html><head><title>About</title></head><body><h1>About</h1><p>About Acme.</p>"
              '<a href="/">Home</a></body></html>',
    "/login": "<html><head><title>Login</title></head><body><form action='/login' method='post'>"
              "<input name='user'><input type='password' name='pw'><button>Log in</button></form>"
              '<a href="/about">About</a></body></html>',
    "/login/faculty": "<html><head><title>Faculty</title></head><body><form>"
                      "<input type='password'></form></body></html>",
    "/author/jane": ("<html><head><title>Jane Doe</title></head><body>" + _HEADER_LOGIN +
                     "<main><h1>Jane Doe</h1>" + _LONG_TEXT + "</main></body></html>"),
    "/portal": "<html><head><title>Sign in to the portal</title></head><body><div id='app'>"
               "<input type='password'></div></body></html>",
    "/blog/login-tips": "<html><head><title>Login tips</title></head><body><h1>Login tips</h1>"
                        "<p>Use a password manager.</p></body></html>",
    # Useful pages that carry a login form: real copy, or entity markup. Both stay in scope.
    "/login/help": ("<html><head><title>Log in help</title></head><body><main><h1>Log in</h1>"
                    "<form action='/login'><input type='password'><button>Log in</button></form>"
                    + _LONG_TEXT + "</main></body></html>"),
    "/signin": ("<html><head><title>Sign in</title><script type='application/ld+json'>"
                '{"@context":"https://schema.org","@type":"Organization","name":"Acme University"}'
                "</script></head><body><form><input type='password'><button>Sign in</button></form>"
                "</body></html>"),
}


def _start(robots="User-agent: *\nDisallow:\n"):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append((self.command, self.path))
            path = self.path.split("?")[0]
            if path == "/robots.txt":
                body, ctype, status = robots, "text/plain", 200
            elif path in _PAGES:
                body, ctype, status = _PAGES[path], "text/html", 200
            else:
                body, ctype, status = "not found", "text/plain", 404
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    def stop():
        httpd.shutdown()
        httpd.server_close()
    return f"http://127.0.0.1:{httpd.server_address[1]}", stop, seen


def _acquire(url, **limit_overrides):
    limits = replace(Limits(), **limit_overrides) if limit_overrides else Limits()
    return acquire_site(url, make_deadline(limits), limits, allow_private_targets=True)


def test_crawl_keeps_login_pages_out_of_the_sample_and_lists_them():
    base, stop, seen = _start()
    try:
        artifacts = _acquire(base + "/")
    finally:
        stop()
    paths = {p.url[len(base):] for p in artifacts.pages}
    assert {"/", "/about", "/author/jane", "/blog/login-tips", "/login/help", "/signin"} <= paths
    assert not paths & {"/login", "/login/faculty", "/portal"}
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["urls_out_of_scope"] == 3
    listed = {e["url"][len(base):]: e for e in cov["out_of_scope_pages"]}
    assert set(listed) == {"/login", "/login/faculty", "/portal"}
    assert all(e["reason"] == "login_page" and e["signals"][0] == "password_input" for e in listed.values())
    assert "auth_path:login" in listed["/login/faculty"]["signals"]
    assert "login_title" in listed["/portal"]["signals"]
    assert cov["start_url_out_of_scope"] is False
    assert cov["urls_fetched_attempted"] == len(artifacts.pages) + 3
    assert cov["urls_fetched_ok"] == cov["urls_fetched_attempted"]
    assert cov["urls_analyzed"] == len(artifacts.pages)
    assert cov["skip_reason_counts"].get("login_page_out_of_scope") == 3
    assert not any("login page" in w for w in artifacts.warnings)
    # Read-only: every request was a GET, and each login page was requested once.
    assert {method for method, _ in seen} == {"GET"}
    assert [p for _, p in seen].count("/login") == 1


def test_start_url_that_is_a_login_page_warns_and_the_crawl_continues():
    base, stop, _ = _start()
    try:
        artifacts = _acquire(base + "/login")
    finally:
        stop()
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["start_url_out_of_scope"] is True
    assert any("start URL" in w and "login page" in w for w in artifacts.warnings)
    # Its public links are still followed.
    assert base + "/about" in {p.url for p in artifacts.pages}


def test_login_pages_count_toward_the_page_cap():
    base, stop, seen = _start()
    try:
        artifacts = _acquire(base + "/login", MAX_PAGES_CRAWLED=2)
    finally:
        stop()
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["urls_fetched_attempted"] == 2
    page_requests = [p for _, p in seen if p.split("?")[0] in _PAGES]
    assert len(page_requests) == 2


def test_robots_disallowed_login_page_is_never_requested():
    base, stop, seen = _start(robots="User-agent: *\nDisallow: /login\n")
    try:
        artifacts = _acquire(base + "/")
    finally:
        stop()
    assert not any(p.startswith("/login") for _, p in seen)
    cov = artifacts.acquisition_metadata["coverage"]
    assert {e["url"][len(base):] for e in cov["out_of_scope_pages"]} == {"/portal"}
    assert cov["urls_blocked"] >= 2


def test_full_audit_reports_login_pages_and_explains_confidence():
    from run_audit import run_audit
    base, stop, _ = _start()
    try:
        report = run_audit(base + "/", limits=Limits(), allow_private_targets=True)
    finally:
        stop()
    cov = report["coverage"]
    assert cov["pages_out_of_scope"] == 3
    assert {e["url"][len(base):] for e in cov["out_of_scope_pages"]} == {"/login", "/login/faculty", "/portal"}
    assert any("login or sign-in page(s)" in line for line in report["limitations"])
    skipped = {base + p for p in ("/login", "/login/faculty", "/portal")}
    for item in report["findings"] + report["recommendations"]:
        for page in item.get("affected_pages", []):
            assert str(page) not in skipped, (item["check_id"], page)
    conf = report["confidence"]
    assert conf["level"] in ("high", "medium", "low")
    assert conf["limiting_factor"] in conf["components"]
    assert conf["explanation"].startswith("Confidence is ")
    # The only Organization markup sits on /signin, a sign-in page that was kept
    # because of it, so the brand identity still resolves.
    assert cov["identity_resolution"] == "resolved"
    assert conf["reasons"]["identity_confidence"].startswith("The brand identity is clear")
    assert "Report confidence has no plain-English explanation." not in report["warnings"]


# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------

class _Artifacts:
    robots_data = {}
    sitemap_data = {"status": "ok"}
    media_data = {}


def test_limitations_mention_login_pages_and_a_login_start_url():
    lines = derive_limitations(_Artifacts(), {"headless_rendering": True, "external_search": True},
                               {"pages_out_of_scope": 2, "start_url_out_of_scope": True}, "completed")
    assert any(line.startswith("The start URL is a login page") for line in lines)
    assert any(line.startswith("2 login or sign-in page(s)") for line in lines)
    lines = derive_limitations(_Artifacts(), {"headless_rendering": True, "external_search": True},
                               {"pages_out_of_scope": 0}, "completed")
    assert not any("login" in line for line in lines)


# ---------------------------------------------------------------------------
# Confidence explanation (point 13)
# ---------------------------------------------------------------------------

_GOOD = {"pages_discovered": 40, "pages_fetched_attempted": 40, "pages_analyzed": 40,
         "sections_discovered": 5, "sections_analyzed": 5, "identity_confidence": 0.92,
         "identity_resolution": "resolved"}


def test_zero_identity_is_explained_but_does_not_lower_the_score():
    # A site with no Organization markup gets that as a finding; a complete crawl
    # of it is still a complete crawl.
    conf = overall_confidence({**_GOOD, "identity_confidence": 0.0,
                               "identity_resolution": "no_organization_markup"}, "completed")
    assert conf["score"] == 1.0 and conf["level"] == "high"
    assert conf["limiting_factor"] != "identity_confidence"
    assert conf["components"]["identity_confidence"] == 0.0
    assert "Brand identity (reported separately, not part of the score)" in conf["explanation"]
    assert "No Organization or Product JSON-LD" in conf["explanation"]
    assert "Also weak" not in conf["explanation"]
    assert "each finding has its own confidence" in conf["explanation"]


def test_high_confidence_explanation():
    conf = overall_confidence(_GOOD, "completed")
    assert conf["level"] == "high" and conf["score"] == 1.0
    assert "both hold up" in conf["explanation"]
    assert set(conf["reasons"]) == {"sample_representativeness", "identity_confidence", "execution_penalty"}


def test_thin_sample_is_named_with_its_numbers():
    conf = overall_confidence({**_GOOD, "pages_discovered": 826, "pages_fetched_attempted": 5,
                               "pages_analyzed": 5, "sections_discovered": 12, "sections_analyzed": 2},
                              "completed")
    assert conf["limiting_factor"] == "sample_representativeness"
    assert "analyzed 5 of 826 discovered page(s) and reached 2 of 12 site section(s)" in conf["explanation"]


def test_deadline_is_named_and_ties_go_to_execution():
    conf = overall_confidence({**_GOOD, "identity_confidence": 0.4, "identity_resolution": "not_completed"},
                              "partial_deadline_reached")
    assert conf["score"] == 0.4 and conf["limiting_factor"] == "execution_penalty"
    assert "time limit was reached" in conf["explanation"]
    assert "Also weak" not in conf["explanation"]
    assert "not part of the score): Brand identity could not be resolved" in conf["explanation"]


def test_score_is_the_plain_minimum_of_sample_and_run():
    for identity in (0.0, 0.55, 0.8, 0.92):
        for status in ("completed", "completed_with_timeouts", "degraded", "partial_deadline_reached"):
            conf = overall_confidence({**_GOOD, "identity_confidence": identity}, status)
            c = conf["components"]
            assert conf["score"] == round(min(c["sample_representativeness"], c["execution_penalty"]), 2)
            assert conf["level"] == confidence_level(conf["score"])
            assert conf["limiting_factor"] in ("sample_representativeness", "execution_penalty")
            assert conf["components"][conf["limiting_factor"]] == min(
                c["sample_representativeness"], c["execution_penalty"])


def test_every_identity_resolution_has_its_own_reason():
    texts = set()
    for resolution in ("resolved", "parent_sub_brand", "multi_brand_conflict", "conflicting_sameas",
                       "no_organization_markup", "not_completed"):
        conf = overall_confidence({**_GOOD, "identity_resolution": resolution}, "completed")
        texts.add(conf["reasons"]["identity_confidence"])
    assert len(texts) == 6


def test_older_coverage_without_resolution_still_explains():
    conf = overall_confidence({"pages_discovered": 10, "pages_fetched_attempted": 10,
                               "identity_confidence": 0.95}, "completed")
    assert conf["reasons"]["identity_confidence"].startswith("The brand identity is clear")
    assert "No page could be analyzed" not in conf["explanation"]
    conf = overall_confidence({"pages_discovered": 10, "pages_fetched_attempted": 10}, "completed")
    assert conf["reasons"]["identity_confidence"] == "Brand identity could not be resolved in this run."


def test_no_analyzed_page_is_said_plainly():
    conf = overall_confidence({"pages_discovered": 1, "pages_fetched_attempted": 0, "pages_analyzed": 0,
                               "identity_confidence": 0.0, "identity_resolution": "no_organization_markup"},
                              "degraded")
    assert conf["reasons"]["sample_representativeness"].startswith("No page could be analyzed")
    assert conf["limiting_factor"] == "sample_representativeness"


def test_fetched_but_unanalyzed_page_scores_zero():
    # A login start URL, or a start URL that redirects away: one URL discovered,
    # one fetched, none analyzed. A fetch that yielded nothing is no evidence.
    coverage = {"pages_discovered": 1, "pages_fetched_attempted": 1, "pages_analyzed": 0,
                "identity_confidence": 0.0, "identity_resolution": "no_organization_markup"}
    conf = overall_confidence(coverage, "completed")
    assert conf["score"] == 0.0 and conf["components"]["crawl_completeness"] == 0.0
    assert conf["limiting_factor"] == "sample_representativeness"
    assert "No page could be analyzed" in conf["explanation"]


def test_identity_resolution_mapping():
    assert identity_resolution({"status": "success", "data": {"confidence": 0.92, "ambiguity_type": None}}) == "resolved"
    assert identity_resolution({"status": "partial", "data": {"confidence": 0.55,
                                                               "ambiguity_type": "multi_brand_conflict"}}) == "multi_brand_conflict"
    assert identity_resolution({"status": "insufficient_evidence",
                                "data": {"confidence": 0.0, "entity_type": "unknown"}}) == "no_organization_markup"
    # A worker timeout or crash carries no data.
    assert identity_resolution({"status": "insufficient_evidence", "data": {}}) == "not_completed"
    assert identity_resolution({"status": "failed"}) == "not_completed"
    assert identity_resolution(None) == "not_completed"


def test_unfinished_audit_confidence_explains_itself():
    conf = unfinished_confidence()
    assert conf["score"] == 0.0 and conf["method"] == "no completed audit evidence"
    assert conf["level"] == "low" and "did not finish" in conf["explanation"]


def test_validate_report_flags_a_confidence_without_explanation():
    base = {"site": "s", "audited_at": "t", "summary": {}, "coverage": {}, "execution_status": "completed",
            "limitations": [], "findings": [], "recommendations": []}
    report = validate_report({**base, "confidence": {"score": 0.5, "method": "m"}})
    assert "Report confidence has no plain-English explanation." in report["warnings"]
    report = validate_report({**base, "confidence": overall_confidence(_GOOD, "completed")})
    assert "Report confidence has no plain-English explanation." not in report["warnings"]
