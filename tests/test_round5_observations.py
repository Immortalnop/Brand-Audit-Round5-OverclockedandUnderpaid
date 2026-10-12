"""test_round5_observations.py -- Round 5 plan, phases 1 and 2.

Each test pins one acceptance case of ROUND5_PLAN.md with the positive control
that must keep working:
  - T1.1 observation ledger: every fetch is recorded with its scope; truncated
    pages are counted as partly observed.
  - T1.2 redirect aliases: a link to a URL whose copy was dropped still reaches
    the page that was kept.
  - T1.3 URL identity: query variants with different content are different pages;
    the same path with the same content is one.
  - T2.1 waiting rooms: gated as an acquisition limitation, never analyzed; a
    normal article about queue software and a thin app shell are not gated.
  - T2.2 graph completeness: a failed or truncated linker, or a page built by
    JavaScript, leaves the graph unresolved; a complete static dead end is kept.
  - T2.3 attribute state: data-page state is detected, bounded and labelled; a
    large settings attribute on a rich page is not.
  - T2.4 confidence: a truncated page never yields full assurance; unknown
    discovery is stated and caps whole-site assurance.
  - T2.5 JSON-LD parse location and reach-based severity.
  - T2.6 directive grouping without losing scope.
  - T2.7 critical fetch timeout for robots.txt and the start URL.

Every rule is a mechanism, never a site name. Nothing here touches the network
beyond 127.0.0.1.
"""
import json
import os
import sys
import threading
import time
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from acquire_site import _extract_page, acquire_site
from analyze_directives import analyze_directives
from analyze_engagement import analyze_engagement
from analyze_experience import shared_title_pages
from analyze_machine_readability import analyze_machine_readability
from analyze_rendering import analyze_rendering
from archetype_sites import ALLOW_ALL, serve
from bot_challenge import waiting_room_signals
from build_site_graph import build_site_graph
from check_helpers import page_observation
from constants import Limits
from execution_summary import discovery_state, observation_completeness, overall_confidence
from models import AuditArtifacts, freeze_value, make_deadline
from test_precision_traps import _OFFLINE_ENV, SITE, page, snapshot
from transport import Response

LIMITS = Limits()
TEXT = "<p>" + "Plain words about the offer and what it does for the people who use it every day. " * 15 + "</p>"
NAV = '<nav><a href="/">Home</a> <a href="/about">About</a></nav>'


def html(title, body, head=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>{head}</head>'
            f"<body>{body}</body></html>")


def sitemap(paths):
    return ("<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            + "".join(f"<url><loc>http://HOST{p}</loc></url>" for p in paths) + "</urlset>")


def acquire(site, limits=LIMITS):
    base, stop, seen = serve(site)
    try:
        return base, acquire_site(base + "/", make_deadline(limits), limits, allow_private_targets=True), seen
    finally:
        stop()


def deadline():
    return make_deadline(LIMITS)


def rule_ids(result):
    return {f["provenance"]["rule_id"] for f in result["findings"]}


def engagement_of(artifacts):
    graph = build_site_graph(artifacts, deadline())
    return graph, analyze_engagement(artifacts, graph, {"metrics": {}}, deadline())


def run_offline(site):
    from run_audit import run_audit
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    base, stop, seen = serve(site)
    try:
        return base, run_audit(base + "/", limits=LIMITS, allow_private_targets=True), seen
    finally:
        stop()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ---------------------------------------------------------------------------
# T2.1 waiting rooms
# ---------------------------------------------------------------------------

HOLDING = html("Hang Tight! Routing to checkout...",
               "<h1>Hang Tight!</h1><p>Routing to checkout...</p>"
               "<img src='/media/sitedownpage/images/logo.png' alt='logo'>")


def test_every_url_a_waiting_room_is_insufficient_evidence():
    site = {"robots": ALLOW_ALL, "sitemap": sitemap(["/", "/shop", "/about"]),
            "pages": {"/": HOLDING, "/shop": HOLDING, "/about": HOLDING}}
    _, report, seen = run_offline(site)
    cov = report["coverage"]
    assert cov["pages_analyzed"] == 0 and cov["pages_waiting_room"] >= 1
    assert report["execution_status"] == "insufficient_evidence"
    assert cov["acquisition_failure"]["reason"] == "waiting_room"
    assert cov["waiting_room_pages"][0]["reason"] == "waiting_room"
    assert "queue_wording" in cov["waiting_room_pages"][0]["signals"]
    # Only checks that never read page content are reported, and nothing passed.
    from run_audit import SITE_LEVEL_CHECKS
    assert {f["check_id"] for f in report["findings"]} <= SITE_LEVEL_CHECKS
    # Resource observations (a robots.txt that was read) may pass; no page check does.
    from whats_working import CHECKS
    assert {w["check"] for w in report["whats_working"]} <= {c[0] for c in CHECKS if c[5]}
    # Never retried: each page path was requested at most once.
    paths = [p for _, p in seen if p in ("/", "/shop", "/about")]
    assert len(paths) == len(set(paths))
    assert report["confidence"]["score"] == 0.0


def test_mixed_site_keeps_real_pages_and_lists_the_gated_path():
    site = {"robots": ALLOW_ALL, "sitemap": None,
            "pages": {"/": html("Fixture shop", "<main><h1>Fixture shop</h1>" + TEXT + NAV
                                + '<a href="/drop">Limited drop</a></main>'),
                      "/about": html("About the shop", "<main><h1>About</h1>" + TEXT + NAV + "</main>"),
                      "/drop": html("Waiting room",
                                    "<h1>You are now in line</h1><p>Your estimated wait time is 4 minutes.</p>"
                                    "<meta http-equiv='refresh' content='30'>")}}
    _, artifacts, _ = acquire(site)
    cov = artifacts.acquisition_metadata["coverage"]
    analyzed = {p.url.rsplit("/", 1)[-1] for p in artifacts.pages}
    assert analyzed == {"", "about"}
    assert cov["urls_waiting_room"] == 1
    assert cov["waiting_room_pages"][0]["url"].endswith("/drop")
    scopes = {r["requested_url"].rsplit("/", 1)[-1]: r["scope"] for r in artifacts.acquisition_metadata["observations"]}
    assert scopes["drop"] == "waiting_room" and scopes[""] == "complete"


def test_article_about_queue_software_is_not_a_waiting_room():
    body = ("<main><h1>How a virtual waiting room protects a launch</h1>" + TEXT * 2
            + "<p>You are now in line, the queue page says, and your estimated wait time is shown.</p>"
            + NAV + "</main><script src='https://static.queue-it.net/script/queueclient.min.js'></script>")
    article = page(body, head="<title>Waiting rooms explained</title>", url=SITE + "/blog/waiting-rooms")
    assert waiting_room_signals(200, body, article.title, article.headings, article.visible_text,
                                len(article.internal_links)) == []


def test_thin_app_shell_without_queue_wording_reaches_rendering():
    from archetype_sites import _spa_shell
    shell_html = _spa_shell("Tripboard")
    shell = page(shell_html.split("<body>", 1)[1].rsplit("</body>", 1)[0], head="<title>Tripboard</title>")
    assert waiting_room_signals(200, shell_html, shell.title, shell.headings, shell.visible_text,
                                len(shell.internal_links)) == []
    # A queue provider's script alone on a thin shell, with no queue wording and
    # no refresh or queue status, is not a waiting room either.
    vendor = shell_html.replace("</body>", "<script src='https://static.queue-it.net/q.js'></script></body>")
    assert waiting_room_signals(200, vendor, shell.title, shell.headings, shell.visible_text, 0) == []
    result = analyze_rendering(snapshot(shell), deadline(), LIMITS, capabilities={"headless_rendering": False})
    assert "render-gap" in rule_ids(result)


# ---------------------------------------------------------------------------
# T1.2 redirect aliases
# ---------------------------------------------------------------------------

def test_link_to_a_dropped_redirect_alias_reaches_the_kept_page():
    moved = (301, "", "text/html", (("Location", "/destination"),))
    site = {"robots": ALLOW_ALL, "sitemap": sitemap(["/a_alias"]),
            "pages": {"/": html("Home", "<main><h1>Home</h1>" + TEXT + '<a href="/z_alias">Destination</a></main>'),
                      "/destination": html("Destination", "<main><h1>Destination</h1>" + TEXT
                                           + '<a href="/">Home</a></main>')},
            "responses": {"/a_alias": moved, "/z_alias": moved}}
    _, artifacts, _ = acquire(site)
    aliases = artifacts.acquisition_metadata["url_aliases"]
    assert {u.rsplit("/", 1)[-1] for u in aliases} == {"a_alias", "z_alias"}
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["urls_redirect_duplicates"] == 1 and cov["urls_analyzed"] == 2
    graph, result = engagement_of(artifacts)
    assert graph["data"]["orphans"] == []
    destination = next(n for u, n in graph["data"]["nodes"].items() if u.endswith("/destination"))
    assert {a.rsplit("/", 1)[-1] for a in destination["aliases"]} == {"a_alias", "z_alias"}
    assert "orphan-pages" not in rule_ids(result)


# ---------------------------------------------------------------------------
# T1.3 URL identity
# ---------------------------------------------------------------------------

def test_query_pages_with_different_content_are_different_pages():
    red = page("<main><h1>Red jacket</h1>" + TEXT + "<p>Red, waxed cotton, size M.</p></main>",
               head="<title>Product</title>", url=SITE + "/product?id=red")
    blue = page("<main><h1>Blue jacket</h1>" + TEXT + "<p>Blue, nylon shell, size L.</p></main>",
                head="<title>Product</title>", url=SITE + "/product?id=blue")
    assert {p.url for p in shared_title_pages([red, blue])} == {red.url, blue.url}
    # A ?tab= view of the same item: one page, and the reason is recorded.
    tab = page("<main><h1>Red jacket</h1>" + TEXT + "<p>Red, waxed cotton, size M.</p></main>",
               head="<title>Product</title>", url=SITE + "/product?id=red&tab=reviews")
    suppressed = []
    assert shared_title_pages([red, tab], suppressed) == []
    assert suppressed[0]["reason"] == "query_view_variant"
    # A different item parameter with the same visible content: one page.
    same = page("<main><h1>Red jacket</h1>" + TEXT + "<p>Red, waxed cotton, size M.</p></main>",
                head="<title>Product</title>", url=SITE + "/product?sku=r1")
    suppressed = []
    assert shared_title_pages([red, same], suppressed) == []
    assert suppressed[0]["reason"] == "same_path_same_content"


# ---------------------------------------------------------------------------
# T2.2 graph completeness and navigation scope
# ---------------------------------------------------------------------------

def test_failed_linking_page_prevents_an_orphan_claim():
    site = {"robots": ALLOW_ALL, "sitemap": sitemap(["/hub", "/target"]),
            "pages": {"/": html("Home", "<main><h1>Home</h1>" + TEXT + '<a href="/hub">Hub</a></main>'),
                      "/target": html("Target", "<main><h1>Target</h1>" + TEXT + '<a href="/">Home</a></main>')},
            # /hub would link /target, but it answers 503.
            "responses": {"/hub": (503, "<html><body>busy</body></html>", "text/html")}}
    _, artifacts, _ = acquire(site)
    graph, result = engagement_of(artifacts)
    scope = graph["data"]["crawl_scope"]
    assert not scope["complete"]
    assert any(u["url"].endswith("/hub") and u["reason"] == "http_error" for u in scope["unresolved"])
    assert "orphan-pages" not in rule_ids(result)
    assert any("not assessed" in w for w in result["warnings"])


def test_truncated_page_is_partial_and_never_a_dead_end():
    big = html("Long page", "<main><h1>Long page</h1>" + TEXT * 40 + '<a href="/about">About</a></main>')
    site = {"robots": ALLOW_ALL, "sitemap": None, "pages": {"/": big}}
    limits = replace(LIMITS, MAX_RESPONSE_BYTES=4000)
    _, artifacts, _ = acquire(site, limits)
    home = artifacts.pages[0]
    assert page_observation(home)["status"] == "partial"
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["urls_partially_observed"] == 1
    graph, result = engagement_of(artifacts)
    assert graph["data"]["dead_ends"] == [] and graph["data"]["dead_ends_unassessed"]
    assert not graph["data"]["crawl_scope"]["complete"]
    assert "dead-ends" not in rule_ids(result)


def test_heading_free_app_shell_gets_no_absence_findings():
    from archetype_sites import SPA
    _, artifacts, _ = acquire(SPA)
    assert artifacts.pages and all(page_observation(p)["script_dependent"] for p in artifacts.pages)
    graph, result = engagement_of(artifacts)
    assert not graph["data"]["crawl_scope"]["complete"]
    assert not {"dead-ends", "orphan-pages", "no-internal-navigation", "isolated-clusters"} & rule_ids(result)
    assert "no-headings" not in rule_ids(analyze_machine_readability(artifacts, deadline()))


def test_complete_static_dead_end_is_still_reported():
    site = {"robots": ALLOW_ALL, "sitemap": None,
            "pages": {"/": html("Home", "<main><h1>Home</h1>" + TEXT + '<a href="/end">The end</a></main>'),
                      "/end": html("End", "<main><h1>End</h1>" + TEXT + "</main>")}}
    _, artifacts, _ = acquire(site)
    graph, result = engagement_of(artifacts)
    assert [u.rsplit("/", 1)[-1] for u in graph["data"]["dead_ends"]] == ["end"]
    assert "dead-ends" in rule_ids(result)
    # The static page with no headings is still reported: it is not built by JavaScript.
    bare = page("<p>" + "Words that a reader can read without any heading at all on this page. " * 10 + "</p>",
                head="<title>Bare</title>")
    assert "no-headings" in rule_ids(analyze_machine_readability(snapshot(bare), deadline()))


# ---------------------------------------------------------------------------
# T2.3 attribute state
# ---------------------------------------------------------------------------

def _state_page(attr_value, body_extra="", url=SITE + "/"):
    body = f"<div id=\"app\" data-page='{attr_value}'></div>{body_extra}<script src=\"/build/assets/app.js\"></script>"
    return page(body, head="<title>Fixture</title>", url=url)


def test_attribute_state_is_detected_bounded_and_labelled():
    state = {"component": "Home", "props": {"intro": "We repair bicycles and sell refurbished frames to riders "
                                                     "across the city every single day of the week.",
                                            "items": ["Same day wheel truing for commuter and road bikes alike"] * 5}}
    shell = _state_page(json.dumps(state))
    f = shell.features
    assert f["state_blob"] and list(f["state_sources"]) == ["attr:data-page"]
    assert f["state_text_chars"] >= 300 and not f["state_extraction_limited"]
    result = analyze_rendering(snapshot(shell), deadline(), LIMITS, capabilities={"headless_rendering": False})
    gap = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "render-gap")
    assert gap["status"] == "suspected"
    assert any(e["type"] == "state_discrepancy" and "attr:data-page" in e["description"] for e in gap["evidence"])
    assert result["warnings"] and "not extracted" in result["warnings"][0]


def test_large_settings_attribute_on_a_rich_page_is_not_state():
    settings = json.dumps({"tracking": {"id": "UA-1", "flags": list(range(600))}, "theme": "dark"})
    rich = page("<main><h1>Guide</h1>" + TEXT + f"<div data-settings='{settings}'></div>" + NAV + "</main>"
                "<script src='/app.js'></script>", head="<title>Guide</title>", url=SITE + "/guide")
    assert not rich.features["state_blob"]
    result = analyze_rendering(snapshot(rich), deadline(), LIMITS, capabilities={"headless_rendering": False})
    assert "render-gap" not in rule_ids(result)


def test_json_ld_and_data_blocks_are_not_executable_scripts():
    p = page('<script type="application/ld+json">{"@type":"Thing"}</script>'
             '<script type="application/json" src="/data.json"></script><p>Hello</p>')
    assert p.features["executable_scripts"] == 0 and p.features["external_scripts"] == 0
    p = page('<script src="/app.js"></script><script>var a=1;</script><p>Hello</p>')
    assert p.features["executable_scripts"] == 2


def test_correlated_shell_signs_alone_do_not_make_an_inner_page_high():
    shell = page('<div id="root"></div><noscript>You need to enable JavaScript to run this app.</noscript>'
                 '<script src="/static/js/main.js"></script>', head="<title>Pricing</title>", url=SITE + "/pricing")
    result = analyze_rendering(snapshot(shell), deadline(), LIMITS, capabilities={"headless_rendering": False})
    gap = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "render-gap")
    assert gap["severity"] == "medium"


# ---------------------------------------------------------------------------
# T2.4 confidence
# ---------------------------------------------------------------------------

def _coverage(**extra):
    base = {"pages_discovered": 1, "pages_analyzed": 1, "pages_fetched_attempted": 1, "sections_discovered": 1,
            "sections_analyzed": 1, "pages_never_attempted": 0, "sitemap_status": "ok"}
    base.update(extra)
    base.update(discovery_state(base))
    return base


def test_truncated_single_page_never_gets_full_assurance():
    cov = _coverage(pages_partially_observed=1)
    assert observation_completeness(cov) == 0.5
    conf = overall_confidence(cov, "completed")
    assert conf["score"] == 0.5 and conf["limiting_factor"] == "observation_completeness"
    assert cov["coverage_scope"] == "sample"


def test_unknown_discovery_is_stated_and_capped():
    cov = _coverage(sitemap_status="absent")
    assert cov["discovery_reliable"] == "unknown" and cov["coverage_scope"] == "all_discovered_urls"
    conf = overall_confidence(cov, "completed")
    assert conf["score"] == 0.9 and conf["level"] == "high"
    assert "unknown" in conf["reasons"]["sample_representativeness"]
    # A fully read sitemap and a complete, fully read crawl: discovery is reliable.
    good = _coverage()
    assert good["discovery_reliable"] is True and overall_confidence(good, "completed")["score"] == 1.0
    # A readable sitemap does not hide a challenged fetch or a cut sitemap.
    assert overall_confidence(_coverage(pages_challenged=1), "completed")["score"] < 1.0
    assert _coverage(sitemap_partial=True)["discovery_reliable"] is False
    assert _coverage(sitemap_status="malformed")["discovery_reliable"] is False


def test_confidence_is_described_as_heuristic():
    conf = overall_confidence(_coverage(), "completed")
    assert "not a calibrated probability" in conf["interpretation"]


# ---------------------------------------------------------------------------
# T2.5 JSON-LD parse location and reach
# ---------------------------------------------------------------------------

ORG = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Fixture"}</script>'
BROKEN = '<script type="application/ld+json">{"@context":"https://schema.org",\n "@type":"Organization"\n "name":"x"}</script>'


def _jsonld_pages(broken, total):
    return [page("<main><h1>P</h1>" + TEXT + "</main>" + (BROKEN if i < broken else ORG),
                 head="<title>P</title>", url=f"{SITE}/p{i}") for i in range(total)]


def test_one_bad_block_among_many_is_proportionate_and_located():
    result = analyze_machine_readability(snapshot(*_jsonld_pages(1, 38)), deadline())
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "malformed-jsonld")
    assert finding["severity"] == "low" and finding["status"] == "confirmed"
    assert "1 of 38" in finding["root_cause"]
    text = finding["evidence"][0]["description"]
    assert "block 1 of 1" in text and "line 3" in text and "column" in text and "delimiter" in text


def test_widespread_bad_blocks_escalate():
    result = analyze_machine_readability(snapshot(*_jsonld_pages(20, 30)), deadline())
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "malformed-jsonld")
    assert finding["severity"] == "high"
    assert len(finding["affected_pages"]) == 20


def test_raw_control_character_is_identified():
    p = page('<script type="application/ld+json">{"@type":"Organization","name":"Fix\tture"}</script>' + TEXT,
             head="<title>P</title>")
    error = p.features["jsonld_errors"][0]
    assert "control character" in error["message"] and "\\u0009" in error["excerpt"]


def test_byte_truncated_valid_block_is_not_malformed_source():
    full = ("<html><head><title>P</title><script type=\"application/ld+json\">"
            '{"@context":"https://schema.org","@type":"Organization","name":"Fixture","description":"'
            + "x" * 400 + '"}</script></head><body>' + TEXT + "</body></html>")
    cut = full.encode()[:300]
    response = Response(200, {"Content-Type": "text/html"}, cut, SITE + "/", truncated=True)
    response.network_duration_ms = 10
    truncated = _extract_page(SITE + "/", response, 10, LIMITS)
    assert page_observation(truncated)["status"] == "partial"
    result = analyze_machine_readability(snapshot(truncated), deadline())
    assert "malformed-jsonld" not in rule_ids(result)


# ---------------------------------------------------------------------------
# T2.6 directive grouping
# ---------------------------------------------------------------------------

def _directive_page(path, meta="", header=None):
    head = f'<title>{path}</title><meta name="robots" content="{meta}">' if meta else f"<title>{path}</title>"
    p = page("<main><h1>x</h1>" + TEXT + "</main>", head=head, url=SITE + path)
    if header:
        p = replace(p, response_headers=freeze_value({"X-Robots-Tag": header}))
    return p


def test_noindex_pages_are_grouped_by_scope_without_losing_pages():
    pages = [_directive_page("/guides/a", "noindex"), _directive_page("/guides/a/", "noindex"),
             _directive_page("/item?id=1", "noindex"), _directive_page("/item?id=2", "noindex"),
             _directive_page("/team", header="googlebot: noindex"),
             _directive_page("/press", "nosnippet")]
    findings = analyze_directives(snapshot(*pages), deadline())["findings"]
    noindex = [f for f in findings if f["provenance"]["rule_id"] == "noindex"]
    # meta robots and a googlebot-only header are different scopes.
    assert len(noindex) == 2
    general = next(f for f in noindex if "meta robots" in f["root_cause"])
    # /guides/a and /guides/a/ are one page; the two query pages stay distinct.
    assert len(general["evidence"]) == 3
    assert {SITE + "/item?id=1", SITE + "/item?id=2"} <= set(general["affected_pages"])
    scoped = next(f for f in noindex if "googlebot" in f["root_cause"])
    assert scoped["affected_pages"] == [SITE + "/team"]
    assert [f["provenance"]["rule_id"] for f in findings].count("nosnippet") == 1


def test_homepage_noindex_does_not_claim_the_whole_site():
    findings = analyze_directives(snapshot(_directive_page("/", "noindex")), deadline())["findings"]
    home = next(f for f in findings if f["provenance"]["rule_id"] == "noindex")
    assert home["severity"] == "critical"
    assert "entire site" not in home["root_cause"] and "homepage itself" in home["root_cause"]


def test_intentional_exclusions_stay_skipped():
    findings = analyze_directives(snapshot(_directive_page("/search?q=x", "noindex")), deadline())["findings"]
    assert not findings


# ---------------------------------------------------------------------------
# T2.7 critical fetch timeout
# ---------------------------------------------------------------------------

def _slow_robots_server(delay_s):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/robots.txt":
                time.sleep(delay_s)
                body, ctype = ALLOW_ALL.encode(), "text/plain"
            else:
                body, ctype = html("Home", "<main><h1>Home</h1>" + TEXT + "</main>").encode(), "text/html"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except OSError:
                pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    def stop():
        httpd.shutdown()
        httpd.server_close()
    return f"http://127.0.0.1:{httpd.server_address[1]}", stop


def test_slow_robots_uses_the_critical_allowance():
    base, stop = _slow_robots_server(0.6)
    try:
        limits = replace(LIMITS, PER_FETCH_TIMEOUT_MS=200, CRITICAL_FETCH_TIMEOUT_MS=3000, MAX_FETCH_RETRIES=0)
        artifacts = acquire_site(base + "/", make_deadline(limits), limits, allow_private_targets=True)
        assert artifacts.robots_data["status"] == "ok" and artifacts.pages
        # A short configured limit fails closed.
        limits = replace(limits, CRITICAL_FETCH_TIMEOUT_MS=200)
        artifacts = acquire_site(base + "/", make_deadline(limits), limits, allow_private_targets=True)
        assert artifacts.robots_data["conservative_fail_closed"] and not artifacts.pages
    finally:
        stop()


def test_nearly_expired_stage_returns_promptly():
    base, stop = _slow_robots_server(5.0)
    try:
        limits = replace(LIMITS, TOTAL_AUDIT_TIMEOUT_S=1.0, MAX_FETCH_RETRIES=1)
        started = time.monotonic()
        artifacts = acquire_site(base + "/", make_deadline(limits), limits, allow_private_targets=True)
        assert time.monotonic() - started < 3.0
        assert artifacts.robots_data["conservative_fail_closed"]
    finally:
        stop()


def test_view_and_paging_query_variants_stay_one_page_with_different_text():
    # The earlier false-alarm fix: a ?tab=, ?sort= or ?page=2 view of one path
    # often shows different text under one title. It is still one page.
    base = page("<main><h1>Search</h1>" + TEXT + "<p>People</p></main>", head="<title>Search</title>",
                url=SITE + "/search")
    views = [page("<main><h1>Search</h1>" + TEXT + f"<p>{body}</p></main>", head="<title>Search</title>",
                  url=SITE + "/search" + query)
             for query, body in (("/?tab=directory", "Directory listing of offices"),
                                 ("?sort=name&utm_source=mail", "Sorted by name"),
                                 ("?page=2", "Second page of results"))]
    suppressed = []
    assert shared_title_pages([base] + views, suppressed) == []
    assert {s["reason"] for s in suppressed} == {"query_view_variant"}
    # An item parameter that changes alongside a view parameter is still a different page.
    red = page("<main><h1>Red</h1>" + TEXT + "<p>Red, waxed cotton.</p></main>", head="<title>Product</title>",
               url=SITE + "/product?id=red&tab=specs")
    blue = page("<main><h1>Blue</h1>" + TEXT + "<p>Blue, nylon shell.</p></main>", head="<title>Product</title>",
                url=SITE + "/product?id=blue&tab=specs")
    assert {p.url for p in shared_title_pages([red, blue])} == {red.url, blue.url}


def test_holding_page_with_a_long_contact_list_is_still_a_waiting_room():
    # Found on a live run: the holding page lists support numbers per country,
    # which takes it past the thin-page limit. Title wording, a "this page will
    # refresh" message and a refresh with no links still gate it.
    contacts = "".join(f"<p>Region {i}: call 0{i}00 555 0{i}{i}{i} or email help{i}@fixture.example</p>"
                       for i in range(30))
    body = ("<meta http-equiv='refresh' content='30'><h1>Sit tight</h1><p>We have our hands full at the moment "
            "but we should be up and moving shortly. This page will automatically refresh and bring you into "
            "the website as soon as we can.</p>" + contacts)
    holding = page(body, head="<title>Hang Tight! Routing to checkout...</title>")
    assert len(holding.visible_text) > 1000
    signals = waiting_room_signals(200, body, holding.title, holding.headings, holding.visible_text,
                                   len(holding.internal_links))
    assert {"queue_wording", "holding_message", "meta_refresh"} <= set(signals)
    # A long article titled with queue wording, without a holding message, is content.
    article_body = ("<main><h1>Waiting rooms explained</h1>" + TEXT * 2 + NAV
                    + "<p>A queue page tells visitors their estimated wait time.</p></main>")
    article = page(article_body, head="<title>Waiting room software explained</title>")
    assert waiting_room_signals(200, article_body, article.title, article.headings, article.visible_text,
                                len(article.internal_links)) == []
    # A refresh notice on a long page whose title has no queue wording is content too.
    notice = page(body, head="<title>Store contacts</title>")
    assert waiting_room_signals(200, body, notice.title, notice.headings, notice.visible_text, 0) == []
