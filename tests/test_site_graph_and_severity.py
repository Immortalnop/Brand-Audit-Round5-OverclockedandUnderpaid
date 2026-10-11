"""test_site_graph_and_severity.py -- precision guards for the site graph and two severity rules.

  - Site graph: a redirected URL is the page at its final URL, so it is never an
    orphan of its own; several URLs that redirect to one page are one node; a
    trailing slash does not hide a link; a start page that reaches no other
    sampled page does not make the rest of the site an "isolated cluster".
  - Sampled crawls: when the crawl did not reach every discovered URL, orphan
    pages and isolated clusters are counted, never reported, and the report says
    they were not assessed. Complete crawls still report them.
  - End to end: a site whose sitemap is far larger than the crawl cap, with
    paginated section indexes (each lists only its first items) and a redirected
    sitemap URL, produces no orphan or cluster finding.
  - Rendering: a framework bundle and its serialized state count as one sign of
    client-side rendering, so a thin Next.js-style page alone is medium, not high.

Every rule is a mechanism (what a page or crawl shape means), never a site name.
Nothing here touches the network beyond 127.0.0.1.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from acquire_site import _extract_page
from analyze_engagement import analyze_engagement
from analyze_rendering import analyze_rendering, independent_sign_count
from archetype_sites import ALLOW_ALL, serve
from build_site_graph import build_site_graph, page_key
from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline, severity_gate_ok
from transport import Response

LIMITS = Limits()
SITE = "https://fixture.example"
NAV = '<nav><a href="/">Home</a> <a href="/news/">News</a> <a href="/about/">About</a></nav>'
COPY = "<p>" + "Plain words about the offer and what it does for the people who use it every day. " * 6 + "</p>"


def fetched(url, body, final_url=None):
    """A crawled page; final_url differs from url when the request redirected."""
    html = f'<html lang="en"><head><title>Page</title></head><body>{body}</body></html>'
    response = Response(200, {"Content-Type": "text/html"}, html.encode(), final_url or url)
    response.network_duration_ms = 40
    return _extract_page(url, response, 40, LIMITS)


def artifacts(*pages, discovered=None):
    """A snapshot; discovered larger than the page count makes the crawl a sample."""
    discovered = len(pages) if discovered is None else discovered
    coverage = {"urls_analyzed": len(pages), "urls_discovered": discovered,
                "urls_never_attempted": max(0, discovered - len(pages))}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": False, "status": "absent"}), freeze_value({"status": "ok"}),
                          freeze_value({"coverage": coverage}), ())


def graph_of(*pages, discovered=None):
    snap = artifacts(*pages, discovered=discovered)
    return snap, build_site_graph(snap, make_deadline(LIMITS))


def engagement(snap, graph):
    return analyze_engagement(snap, graph, {"metrics": {}}, make_deadline(LIMITS))


def rules(result):
    return {f["provenance"]["rule_id"] for f in result["findings"]}


# ---------------------------------------------------------------------------
# Site graph: nodes are pages at their final URL
# ---------------------------------------------------------------------------

def test_page_key_ignores_trailing_slash_scheme_www_and_host_case():
    assert page_key("https://WWW.Example.com/a/") == page_key("http://example.com/a")
    assert page_key("https://example.com/") == page_key("https://example.com")
    assert page_key("https://example.com/a?x=1") != page_key("https://example.com/a")
    assert page_key("not a url") is None


def test_redirected_url_is_not_an_orphan_when_its_final_url_is_linked():
    home = fetched(SITE + "/", NAV + '<a href="/library/">Library</a>')
    # The sitemap lists /old-library/, which redirects to /library/.
    moved = fetched(SITE + "/old-library/", NAV, final_url=SITE + "/library/")
    about = fetched(SITE + "/about/", NAV)
    news = fetched(SITE + "/news/", NAV)
    _, graph = graph_of(home, moved, about, news)
    data = graph["data"]
    assert data["orphans"] == []
    assert SITE + "/library/" in data["nodes"]
    assert data["nodes"][SITE + "/library/"]["aliases"] == [SITE + "/old-library/"]
    assert SITE + "/old-library/" not in data["nodes"]


def test_urls_redirecting_to_one_page_are_one_node():
    home = fetched(SITE + "/", NAV)
    a = fetched(SITE + "/a/", NAV, final_url=SITE + "/news/")
    b = fetched(SITE + "/b/", NAV, final_url=SITE + "/news/")
    news = fetched(SITE + "/news/", NAV)
    about = fetched(SITE + "/about/", NAV)
    _, graph = graph_of(home, a, b, news, about)
    nodes = graph["data"]["nodes"]
    assert sorted(nodes) == [SITE + "/", SITE + "/about/", SITE + "/news/"]
    assert nodes[SITE + "/news/"]["aliases"] == [SITE + "/a/", SITE + "/b/"]
    assert graph["data"]["orphans"] == []


def test_link_without_trailing_slash_reaches_the_page():
    home = fetched(SITE + "/", '<a href="/guide">Guide</a>')
    guide = fetched(SITE + "/guide/", '<a href="/">Home</a>')
    _, graph = graph_of(home, guide)
    assert graph["data"]["orphans"] == [] and graph["data"]["dead_ends"] == []


def test_link_to_itself_is_no_way_onward():
    home = fetched(SITE + "/", '<a href="/loop/">Loop</a>')
    loop = fetched(SITE + "/loop/", '<a href="/loop/">Again</a>')
    _, graph = graph_of(home, loop)
    assert graph["data"]["dead_ends"] == [SITE + "/loop/"]


def test_splash_start_page_does_not_isolate_the_rest_of_the_site():
    # The start page links only to a page outside the sample (a language chooser,
    # a page built by JavaScript); every other page is well linked.
    splash = fetched(SITE + "/", '<a href="/en/">English</a>')
    news = fetched(SITE + "/news/", '<a href="/about/">About</a>')
    about = fetched(SITE + "/about/", '<a href="/news/">News</a>')
    snap, graph = graph_of(splash, news, about)
    data = graph["data"]
    assert data["isolated_clusters"] == []
    assert data["main_cluster_size"] == 2
    assert "isolated-clusters" not in rules(engagement(snap, graph))


def test_complete_crawl_still_reports_a_real_orphan_and_isolated_cluster():
    home = fetched(SITE + "/", '<a href="/about/">About</a>')
    about = fetched(SITE + "/about/", '<a href="/">Home</a>')
    lonely = fetched(SITE + "/lonely/", '<a href="/">Home</a>')
    a = fetched(SITE + "/cluster-a/", '<a href="/cluster-b/">B</a>')
    b = fetched(SITE + "/cluster-b/", '<a href="/cluster-a/">A</a>')
    snap, graph = graph_of(home, about, lonely, a, b)
    data = graph["data"]
    assert data["crawl_scope"]["complete"]
    assert SITE + "/lonely/" in data["orphans"]
    assert [SITE + "/cluster-a/", SITE + "/cluster-b/"] in data["isolated_clusters"]
    result = engagement(snap, graph)
    (orphan,) = [f for f in result["findings"] if f["provenance"]["rule_id"] == "orphan-pages"]
    assert orphan["status"] == "confirmed" and orphan["severity"] == "medium"
    assert SITE + "/lonely/" in orphan["affected_pages"]
    assert "isolated-clusters" in rules(result)
    assert not result["warnings"]


# ---------------------------------------------------------------------------
# Sampled crawls: counted, never reported
# ---------------------------------------------------------------------------

def test_sampled_crawl_does_not_report_orphans_or_clusters():
    home = fetched(SITE + "/", NAV)
    index = fetched(SITE + "/news/", NAV + "".join(f'<a href="/news/item-{i}/">Item {i}</a>' for i in range(5)))
    deep = fetched(SITE + "/news/item-40/", NAV)            # linked from index page 8, never fetched
    a = fetched(SITE + "/archive/x/", '<a href="/archive/y/">Y</a>')
    b = fetched(SITE + "/archive/y/", '<a href="/archive/x/">X</a>')
    snap, graph = graph_of(home, index, deep, a, b, discovered=300)
    data = graph["data"]
    assert not data["crawl_scope"]["complete"]
    assert SITE + "/news/item-40/" in data["orphans"]          # still counted
    assert data["isolated_clusters"]                            # still counted
    result = engagement(snap, graph)
    assert not {"orphan-pages", "isolated-clusters"} & rules(result)
    assert result["metrics"]["orphan_pages"] >= 1 and result["metrics"]["orphan_pages_reported"] == 0
    assert result["metrics"]["isolated_clusters_reported"] == 0
    assert any("not assessed" in w for w in result["warnings"])


def test_sampled_crawl_still_reports_dead_ends():
    # A dead end is a statement about the page itself, so a sample can judge it.
    home = fetched(SITE + "/", '<a href="/stuck/">Stuck</a>')
    stuck = fetched(SITE + "/stuck/", COPY)
    snap, graph = graph_of(home, stuck, discovered=200)
    assert "dead-ends" in rules(engagement(snap, graph))


# ---------------------------------------------------------------------------
# End to end: a large sitemap sampled down to a few pages
# ---------------------------------------------------------------------------

def _html(title, body):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title></head>'
            f"<body>{body}</body></html>")


def _large_site():
    sections = ("news", "people", "research")
    items = {s: [f"/{s}/item-{i}/" for i in range(40)] for s in sections}
    nav = "<nav>" + " ".join(f'<a href="/{s}/">{s.title()}</a>' for s in sections) + ' <a href="/">Home</a></nav>'
    pages = {"/": _html("Home", nav + "<main><h1>Welcome</h1>" + COPY + "</main>")}
    for s in sections:
        # Each index lists only its five newest items; the rest are on later pages.
        newest = "".join(f'<a href="{u}">Item {u}</a> ' for u in items[s][:5])
        pages[f"/{s}/"] = _html(s.title(), nav + f"<main><h1>{s.title()}</h1>" + newest
                                + f'<a href="/{s}/?page=2">Older</a>' + COPY + "</main>")
        for u in items[s]:
            pages[u] = _html(u, nav + f"<main><h1>{u}</h1>" + COPY + "</main>")
    urls = ["/", "/old-news/"] + [f"/{s}/" for s in sections] + [u for s in sections for u in items[s]]
    sitemap = ("<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
               + "".join(f"<url><loc>http://HOST{u}</loc></url>" for u in urls) + "</urlset>")
    return {"robots": ALLOW_ALL, "sitemap": sitemap, "pages": pages,
            # A retired URL the sitemap still lists, redirecting to the news index.
            "responses": {"/old-news/": (301, "", "text/html", (("Location", "/news/"),))}}


@pytest.fixture(scope="module")
def large_site_report():
    from run_audit import run_audit
    from test_precision_traps import _OFFLINE_ENV
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    base, stop, seen = serve(_large_site())
    try:
        report = run_audit(base + "/", limits=Limits(MAX_PAGES_CRAWLED=20), allow_private_targets=True)
    finally:
        stop()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return base, report, list(seen)


def test_large_sampled_site_reports_no_orphans_or_clusters(large_site_report):
    base, report, seen = large_site_report
    assert report["execution_status"] == "completed"
    assert report["coverage"]["pages_analyzed"] <= 20
    assert report["coverage"]["pages_discovered"] > 100
    checks = {c for f in report["findings"] + report["recommendations"] for c in (f.get("check_ids") or [f["check_id"]])}
    assert not {"orphan-pages", "isolated-clusters"} & checks
    assert any("Orphan pages and isolated page clusters were not assessed" in w for w in report["warnings"])
    # Read-only and bounded.
    assert {method for method, _ in seen} == {"GET"}
    assert len(seen) <= Limits().MAX_TOTAL_HTTP_REQUESTS


# ---------------------------------------------------------------------------
# Rendering: correlated framework signs count once
# ---------------------------------------------------------------------------

def _render(*pages):
    snap = artifacts(*pages)
    return analyze_rendering(snap, make_deadline(LIMITS), LIMITS, capabilities={})


def _gap(result):
    return [f for f in result["findings"] if f["provenance"]["rule_id"] == "render-gap"]


def test_independent_sign_count():
    assert independent_sign_count({"framework_bundle", "serialized_state"}) == 1
    assert independent_sign_count({"framework_bundle", "serialized_state", "app_shell"}) == 2
    assert independent_sign_count({"framework_bundle", "state_content"}) == 2
    assert independent_sign_count({"app_shell", "noscript"}) == 2
    assert independent_sign_count(set()) == 0


def test_framework_bundle_and_state_alone_are_one_sign_medium():
    # A short server-rendered Next.js page carries both artifacts; that alone is
    # not two independent observations.
    thin = fetched(SITE + "/", '<h1>Hi</h1><script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>'
                               '<script src="/_next/static/chunks/main.js"></script>')
    (gap,) = _gap(_render(thin))
    assert gap["severity"] == "medium" and gap["status"] == "suspected"
    assert gap["confidence"] == 0.6


def test_framework_bundle_and_state_with_an_empty_mount_point_is_high():
    shell = fetched(SITE + "/", '<div id="__next"></div>'
                                '<script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>'
                                '<script src="/_next/static/chunks/main.js"></script>')
    (gap,) = _gap(_render(shell))
    assert gap["severity"] == "high" and severity_gate_ok(gap)
