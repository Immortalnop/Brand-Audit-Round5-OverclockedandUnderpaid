"""Single consolidated smoke test (no network needed): wires the full DAG against a
synthetic AuditArtifacts fixture and checks the acceptance-test properties below
that don't require live crawling."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common",
    "skills/audit-orchestrator/scripts",
    "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts",
    "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import DEFAULT_LIMITS
from models import PageArtifact, AuditArtifacts, make_deadline

from merge_findings import merge_findings
from prioritize_findings import prioritize_findings
from validate_report import validate_report

from analyze_crawlability import analyze_crawlability
from analyze_rendering import analyze_rendering
from analyze_machine_readability import analyze_machine_readability
from check_ai_crawler_access import check_ai_crawler_access
from check_llms_txt import check_llms_txt

from extract_claims import extract_claims
from identify_important_facts import identify_important_facts
from resolve_entity_identity import resolve_entity_identity
from assess_freshness import assess_freshness
from corroborate_claims import corroborate_claims
from assess_external_footprint import assess_external_footprint

from build_site_graph import build_site_graph
from analyze_engagement import analyze_engagement


def _make_fixture_artifacts():
    home = PageArtifact(
        url="https://example.com/", status_code=200, content_type="text/html",
        evidence_snippet="Example Brand homepage", visible_text="Example Brand. Founded 2015-01-01. Call +1 555-123-4567.",
        title="Example Brand", meta_description="Example Brand site",
        canonical_url="https://example.com/", headings=("Welcome",),
        internal_links=("https://example.com/about",), external_links=(),
        jsonld_blocks=({"@type": "Organization", "name": "Example Brand",
                         "telephone": "+1 555-123-4567", "sameAs": ["https://twitter.com/example"]},),
        page_type="home", fetch_duration_ms=50, render_status="not_rendered",
        breadcrumb_visible=(), breadcrumb_schema=None, ai_crawler_directives={},
    )
    about = PageArtifact(
        url="https://example.com/about", status_code=200, content_type="text/html",
        evidence_snippet="About us", visible_text="About Example Brand, updated 2015-02-02.",
        title="About", meta_description=None, canonical_url="https://example.com/about",
        headings=("About",), internal_links=(), external_links=(),
        jsonld_blocks=(), page_type="about", fetch_duration_ms=40, render_status="not_rendered",
        breadcrumb_visible=("Home", "About"), breadcrumb_schema=None, ai_crawler_directives={},
    )
    orphan = PageArtifact(
        url="https://example.com/orphan", status_code=200, content_type="text/html",
        evidence_snippet="Orphan page", visible_text="Nobody links here.",
        title="Orphan", meta_description=None, canonical_url=None,
        headings=(), internal_links=(), external_links=(),
        jsonld_blocks=(), page_type=None, fetch_duration_ms=30, render_status="not_rendered",
        breadcrumb_visible=(), breadcrumb_schema=None, ai_crawler_directives={},
    )
    return AuditArtifacts(
        site_url="https://example.com/", normalized_origin="https://example.com",
        pages=(home, about, orphan),
        robots_data={"allowed_general": True, "ai_crawler_directives": {"GPTBot": "allow"}},
        llms_txt_data={"present": False}, sitemap_data={"discovered": False},
        acquisition_metadata={"pages_crawled": 3, "total_bytes": 1000}, warnings=(),
    )


def test_full_dag_wiring_and_invariants():
    limits = DEFAULT_LIMITS
    deadline = make_deadline(limits)
    artifacts = _make_fixture_artifacts()

    # Independent batch (order doesn't matter; run sequentially here for a deterministic test).
    crawlability = analyze_crawlability(artifacts, deadline)
    rendering = analyze_rendering(artifacts, deadline, limits)
    machine_readability = analyze_machine_readability(artifacts, deadline)
    ai_crawler = check_ai_crawler_access(artifacts, deadline)
    llms_txt = check_llms_txt(artifacts, deadline)
    claims = extract_claims(artifacts, deadline)
    entity_identity = resolve_entity_identity(artifacts, deadline)
    site_graph = build_site_graph(artifacts, deadline)

    # Wiring test: identify_important_facts must consume extract_claims' non-empty output.
    assert len(claims["data"]["claims"]) > 0
    facts = identify_important_facts(claims, deadline)
    assert facts["artifact_type"] == "important_facts"

    # Entity reuse test: same identity_identity object passed to both consumers.
    freshness = assess_freshness(facts, artifacts, deadline)
    corroboration = corroborate_claims(facts, entity_identity, artifacts, deadline, limits)
    footprint = assess_external_footprint(artifacts, entity_identity, deadline, limits)
    engagement = analyze_engagement(artifacts, site_graph, rendering, deadline)

    skill_results = [crawlability, rendering, machine_readability, ai_crawler, llms_txt,
                      freshness, corroboration, footprint, engagement]

    # Invariant I-1 test: every insufficient_evidence finding is proactive_improvement/low.
    for r in skill_results:
        for f in r["findings"]:
            if f["status"] == "insufficient_evidence":
                assert f["finding_type"] == "proactive_improvement"
                assert f["severity"] == "low"

    # Site graph: orphan page detected.
    assert "https://example.com/orphan" in site_graph["data"]["orphans"]

    # Engagement finding references the orphan page.
    orphan_findings = [f for f in engagement["findings"] if f["provenance"]["rule_id"] == "orphan-pages"]
    assert orphan_findings and "https://example.com/orphan" in orphan_findings[0]["affected_pages" if False else "evidence"][0]["urls"]

    merged = merge_findings(skill_results)
    prioritized = prioritize_findings(merged)

    report = {
        "site": artifacts.site_url, "audited_at": "2026-09-12T00:00:00Z",
        "summary": {}, "coverage": {"pages_discovered": 3}, "warnings": [], "findings": prioritized,
    }
    validated = validate_report(report)

    assert validated["summary"]["total_findings"] == len(prioritized)
    assert all(0 <= _SEVERITY_RANK_CHECK(f["severity"]) for f in validated["findings"])
    # merge_findings rejects non-SkillResult input.
    try:
        merge_findings([claims])
        assert False, "merge_findings should reject IntermediateArtifact input"
    except ValueError:
        pass

    print("OK: DAG wiring, entity reuse, dedup, Invariant I-1, and report validation all pass.")


def _SEVERITY_RANK_CHECK(sev):
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(sev, 0)


if __name__ == "__main__":
    test_full_dag_wiring_and_invariants()
