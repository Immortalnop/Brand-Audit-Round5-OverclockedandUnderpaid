"""Scenario fixtures against the local fixture server (tests/fixtures_server.py),
added per Round-3 review: a multi-brand (conflicting-identity) site, a page with
stale commercial facts, a broken-navigation (sitemap-only isolated cluster) site,
and external-search-unavailable combos evaluated against a real, fixture-crawled
identity rather than a synthetic one."""
import os
import sys

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
from analyze_rendering import analyze_rendering
from build_site_graph import build_site_graph
from analyze_engagement import analyze_engagement
from extract_claims import extract_claims
from identify_important_facts import identify_important_facts
from assess_freshness import assess_freshness
from resolve_entity_identity import resolve_entity_identity
from assess_external_footprint import assess_external_footprint

from fixtures_server import start_server


def _acquire(sitemap_mode="absent", multi_brand=False):
    base_url, shutdown = start_server(sitemap_mode=sitemap_mode, multi_brand=multi_brand)
    limits = Limits()
    deadline = make_deadline(limits)
    instrumentation = Instrumentation()
    artifacts = acquire_site(base_url + "/", deadline, limits, instrumentation, allow_private_targets=True)
    return base_url, shutdown, limits, deadline, artifacts


# ---------------------------------------------------------------------------
# Multi-brand site: two unrelated Organization JSON-LD blocks on the same site.
# ---------------------------------------------------------------------------

def test_multi_brand_site_lowers_identity_confidence_and_flags_conflict():
    base_url, shutdown, limits, deadline, artifacts = _acquire(multi_brand=True)
    try:
        identity = resolve_entity_identity(artifacts, deadline)
        assert identity["data"]["confidence"] < 0.85
        assert identity["data"]["ambiguity_type"] == "multi_brand_conflict"
        assert identity["data"]["ambiguity_set"]
    finally:
        shutdown()


def test_multi_brand_site_suppresses_footprint_even_with_provider_configured(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "http://fake.invalid/search")
    calls = []

    def _fake_search(query, max_results, timeout_s):
        calls.append(query)
        return [{"title": "hit", "url": "https://example.org/hit", "snippet": ""}]

    import search_provider
    monkeypatch.setattr(search_provider, "search", _fake_search)

    base_url, shutdown, limits, deadline, artifacts = _acquire(multi_brand=True)
    try:
        identity = resolve_entity_identity(artifacts, deadline)
        result = assess_external_footprint(artifacts, identity, deadline, limits)
        # Confidence gate must suppress the search entirely -- an ambiguous
        # identity is never allowed to run a broad name-only query.
        assert result["status"] == "insufficient_evidence"
        assert calls == []
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# Stale commercial facts: an old date on a /product page.
# ---------------------------------------------------------------------------

def test_stale_commercial_facts_are_flagged_high_severity():
    base_url, shutdown, limits, deadline, artifacts = _acquire()
    try:
        claims = extract_claims(artifacts, deadline)
        product_claims = [c for c in claims["data"]["claims"]
                           if c["type"] == "date" and c["category"] == "commercial"]
        assert product_claims, "expected a commercial-category date claim from /product"

        facts = identify_important_facts(claims, deadline)
        freshness = assess_freshness(facts, artifacts, deadline)
        commercial_findings = [f for f in freshness["findings"]
                                if f["provenance"]["rule_id"] == "stale-dates:commercial"]
        assert commercial_findings
        assert commercial_findings[0]["severity"] == "high"
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# Broken navigation: an isolated cluster reachable only via sitemap.xml, never
# via a page link from the main site.
# ---------------------------------------------------------------------------

def test_broken_navigation_isolated_cluster_counted_not_claimed_beside_script_page():
    base_url, shutdown, limits, deadline, artifacts = _acquire(sitemap_mode="broken_nav")
    try:
        urls = {p.url for p in artifacts.pages}
        assert base_url + "/cluster-a" in urls and base_url + "/cluster-b" in urls

        graph = build_site_graph(artifacts, deadline)
        clusters = graph["data"]["isolated_clusters"]
        assert any(
            {base_url + "/cluster-a", base_url + "/cluster-b"} <= set(c) for c in clusters
        )

        rendering = analyze_rendering(artifacts, deadline, limits)
        engagement = analyze_engagement(artifacts, graph, rendering, deadline)
        isolated_findings = [f for f in engagement["findings"]
                              if f["provenance"]["rule_id"] == "isolated-clusters"]
        # The fixture also serves /js-heavy, a page built by JavaScript: links it
        # may add after load are unknown, so the cluster is counted but not
        # claimed (ROUND5_PLAN T2.2), and the report says why. A complete graph
        # still reports clusters (test_site_graph_and_severity.py).
        scope = graph["data"]["crawl_scope"]
        assert not scope["complete"]
        assert [u["reason"] for u in scope["unresolved"]] == ["script_dependent"]
        assert not isolated_findings
        assert engagement["metrics"]["isolated_clusters"] >= 1
        assert any("not assessed" in w for w in engagement["warnings"])
    finally:
        shutdown()


# ---------------------------------------------------------------------------
# External-search-unavailable combos, against a real (single-brand) resolved
# identity from a fixture-crawled site -- not a synthetic identity dict.
# ---------------------------------------------------------------------------

def test_footprint_insufficient_when_provider_unconfigured(monkeypatch):
    monkeypatch.delenv("SEARCH_API_URL", raising=False)
    base_url, shutdown, limits, deadline, artifacts = _acquire()
    try:
        identity = resolve_entity_identity(artifacts, deadline)
        result = assess_external_footprint(artifacts, identity, deadline, limits)
        assert result["status"] == "insufficient_evidence"
        assert result["metrics"]["provider_configured"] is False
    finally:
        shutdown()


def test_footprint_insufficient_when_provider_fails_mid_query(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "http://fake.invalid/search")

    import search_provider

    def _always_fails(query, max_results, timeout_s):
        raise search_provider.SearchProviderError("simulated provider failure")

    monkeypatch.setattr(search_provider, "search", _always_fails)

    base_url, shutdown, limits, deadline, artifacts = _acquire()
    try:
        identity = resolve_entity_identity(artifacts, deadline)
        assert identity["data"]["confidence"] >= 0.85  # single-brand site: gate is open
        result = assess_external_footprint(artifacts, identity, deadline, limits)
        # Provider failure never becomes a confirmed absence.
        assert result["status"] == "insufficient_evidence"
        assert result["metrics"]["provider_configured"] is True
        assert result["metrics"]["queries_completed"] == 0
    finally:
        shutdown()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and "monkeypatch" not in fn.__code__.co_varnames:
            fn()
            print(f"OK: {name}")
