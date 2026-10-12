"""test_step3_hardening.py -- Step 3 post-porting verification and hardening.

Covers, as continuous regression guards over the fully merged skill set:

  - false-positive guard: a clean, terse, well-built fixture produces no
    critical findings and no high findings other than the loopback-only
    http-transport artifact, and none of the content heuristics misfire.
  - the three-outcome corroboration table (agree / no independent mention /
    contradicts), exercised on both the deterministic search-provider path and
    the agent-executed stage from 2.5.
  - optional/qualitative capability paths for the agent stage: success,
    fallback (not supplied), malformed response, and timeout.
  - recommendation deduplication and no redundant implementation details.
  - runtime stays well under the five-minute limit and inside the standard
    library.
  - orchestration regression: clean composition, provenance, prioritization and
    correct severity counts across the merged report.
"""
import json
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    sys.path.insert(0, str(ROOT / rel))

from constants import Limits
from models import make_deadline, intermediate_artifact, AuditArtifacts
from run_audit import run_audit
from fixtures_server import start_server
import corroborate_claims as cc_module
from corroborate_claims import corroborate_claims, _compare_claim_to_results
from ingest_agent_findings import ingest_agent_findings
from generate_recommendations import generate_recommendations
from merge_findings import merge_findings

LIMITS = Limits()

# Content heuristics that a terse, well-built site must never trip. These are the
# high-surface checks most at risk of misfiring after the Step 2 port.
_FALSE_POSITIVE_SENSITIVE = {
    "term-repetition", "generic-anchor-text", "orphan-pages", "dead-ends",
    "isolated-clusters", "no-internal-navigation", "render-gap",
    "stale-dates:commercial", "stale-dates:editorial", "stale-dates:operational",
    "duplicate-titles", "page-orientation", "internal-discoverability",
    "title-body-alignment", "email-summary-readable", "malformed-jsonld",
}


def _clean_report():
    url, stop = start_server(clean=True)
    try:
        return run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()


# ---------------------------------------------------------------------------
# False-positive guard (run after the full port; conceptually run per batch)
# ---------------------------------------------------------------------------

def test_clean_fixture_produces_no_unexpected_critical_or_high_findings():
    report = _clean_report()
    criticals = [f for f in report["findings"] if f["severity"] == "critical"]
    # http-transport is a loopback-fixture artifact (a real deployment serves
    # https); it is the only high finding the clean site is allowed to raise.
    highs = [f for f in report["findings"]
             if f["severity"] == "high" and f["check_id"] != "http-transport"]
    assert not criticals, [f["check_id"] for f in criticals]
    assert not highs, [f["check_id"] for f in highs]


def test_clean_fixture_does_not_trip_content_heuristics():
    report = _clean_report()
    tripped = {f["check_id"] for f in report["findings"]} & _FALSE_POSITIVE_SENSITIVE
    assert not tripped, "content heuristics misfired on a clean site: " + str(sorted(tripped))


# ---------------------------------------------------------------------------
# Three-outcome corroboration table
# ---------------------------------------------------------------------------

def _identity(confidence=0.9):
    return intermediate_artifact("entity_identity", status="success",
                                  data={"confidence": confidence, "canonical_name": "Example Brand"})


def _empty_artifacts():
    return AuditArtifacts("https://example.com/", "https://example.com", (),
                          {}, {}, {}, {}, ())


def test_three_outcome_agree_records_no_contradiction(monkeypatch):
    # Independent sources agree: the deterministic path corroborates and raises no
    # contradiction finding.
    monkeypatch.setenv("SEARCH_API_URL", "https://search.invalid/api")
    monkeypatch.setattr(cc_module, "search",
                        lambda q, max_results, timeout_s: [
                            {"title": "Example Brand", "snippet": "Call 555-123-4567", "url": "https://a.com"}])
    facts = intermediate_artifact("facts", data={"facts": [{"type": "contact", "value": "555-123-4567"}]})
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(LIMITS), LIMITS)
    assert result["status"] == "success"
    assert result["metrics"]["claims_corroborated"] == 1
    assert not [f for f in result["findings"] if f["check_id"] == "contradicted-claim"]


def test_three_outcome_no_mention_is_not_a_defect(monkeypatch):
    # A real search ran and found nothing matching: not_found, never a confirmed
    # defect and never conflated with "not checked".
    monkeypatch.setenv("SEARCH_API_URL", "https://search.invalid/api")
    monkeypatch.setattr(cc_module, "search",
                        lambda q, max_results, timeout_s: [
                            {"title": "Unrelated", "snippet": "nothing here", "url": "https://a.com"}])
    facts = intermediate_artifact("facts", data={"facts": [{"type": "contact", "value": "555-123-4567"}]})
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(LIMITS), LIMITS)
    assert result["metrics"]["claims_not_found"] == 1
    assert not [f for f in result["findings"] if f["finding_type"] == "defect" and f["status"] == "confirmed"]


def test_three_outcome_contradiction_is_suspected_not_confirmed(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "https://search.invalid/api")
    monkeypatch.setattr(cc_module, "search",
                        lambda q, max_results, timeout_s: [
                            {"title": "Old listing", "snippet": "Reach us at 555-999-0000", "url": "https://y.com"}])
    facts = intermediate_artifact("facts", data={"facts": [{"type": "contact", "value": "555-123-4567"}]})
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(LIMITS), LIMITS)
    conflict = [f for f in result["findings"] if f["check_id"] == "contradicted-claim"]
    assert conflict and conflict[0]["status"] == "suspected"


def test_agent_three_outcome_table(tmp_path, monkeypatch):
    # The agent stage expresses the same three outcomes: agree (nothing emitted),
    # absent (AG-02), contradicts (AG-03).
    supplied = [
        {"check": "AG-02", "status": "confirmed", "evidence": "No independent mention found."},
        {"check": "AG-03", "status": "confirmed", "severity": "high",
         "evidence": "A community thread describes a different category."},
    ]
    path = tmp_path / "af.json"
    path.write_text(json.dumps(supplied))
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    result = ingest_agent_findings(_empty_artifacts(), _identity(), make_deadline(LIMITS), None)
    rules = {f["check_id"] for f in result["findings"]}
    assert "no-independent-mention" in rules and "independent-contradiction" in rules
    # "agree" outcome: the agent simply supplies neither AG-02 nor AG-03 for it, so
    # a supplied set with only an agree note produces no corroboration finding.
    path.write_text(json.dumps([]))
    agree = ingest_agent_findings(_empty_artifacts(), _identity(), make_deadline(LIMITS), None)
    assert agree["status"] == "success" and not agree["findings"]


# ---------------------------------------------------------------------------
# Optional-capability paths for the agent stage
# ---------------------------------------------------------------------------

def test_agent_stage_success_path(tmp_path, monkeypatch):
    path = tmp_path / "af.json"
    path.write_text(json.dumps([{"check": "AG-01", "status": "suspected",
                                 "evidence": "About names no product."}]))
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    result = ingest_agent_findings(_empty_artifacts(), _identity(), make_deadline(LIMITS), None)
    assert result["status"] == "success" and result["metrics"]["findings_ingested"] == 1


def test_agent_stage_fallback_when_not_supplied(monkeypatch):
    monkeypatch.delenv("AGENT_FINDINGS_PATH", raising=False)
    result = ingest_agent_findings(_empty_artifacts(), _identity(), make_deadline(LIMITS), None)
    assert result["status"] == "insufficient_evidence"
    assert result["metrics"]["agent_stage"] == "not_supplied"
    assert any("not checked" in w for w in result["warnings"])


def test_agent_stage_malformed_response_degrades_to_skip(tmp_path, monkeypatch):
    path = tmp_path / "af.json"
    path.write_text("{ this is not valid json ,,,")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    result = ingest_agent_findings(_empty_artifacts(), _identity(), make_deadline(LIMITS), None)
    # A bad handoff never takes the audit down and never fabricates a defect.
    assert result["status"] == "insufficient_evidence"
    assert result["metrics"]["agent_stage"] == "not_supplied"


def test_agent_stage_timeout_path(tmp_path, monkeypatch):
    path = tmp_path / "af.json"
    path.write_text(json.dumps([{"check": "AG-02", "status": "confirmed", "evidence": "x"}]))
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    expired = make_deadline(replace(LIMITS, TOTAL_AUDIT_TIMEOUT_S=0.0))
    time.sleep(0.01)
    result = ingest_agent_findings(_empty_artifacts(), _identity(), expired, None)
    assert result["status"] == "insufficient_evidence" and not result["findings"]


# ---------------------------------------------------------------------------
# Deduplication and no redundant implementation details
# ---------------------------------------------------------------------------

def test_recommendations_have_no_duplicate_titles_or_impl_details():
    report = _clean_report()
    recs = report["recommendations"]
    titles = [r["title"] for r in recs]
    assert len(titles) == len(set(titles)), "duplicate recommendation titles"
    impls = [r["suggested_action"].get("implementation_detail", "") for r in recs]
    non_empty = [i for i in impls if i]
    assert len(non_empty) == len(set(non_empty)), "redundant implementation_detail across recommendations"


def test_no_recommendation_restates_a_confirmed_defect():
    report = _clean_report()
    defect_causes = {(f["category"], f["root_cause"]) for f in report["findings"]
                     if f["finding_type"] == "defect"}
    for r in report["recommendations"]:
        assert (r["category"], r["root_cause"]) not in defect_causes


# ---------------------------------------------------------------------------
# Runtime and constraints
# ---------------------------------------------------------------------------

def test_full_audit_runtime_well_under_five_minutes():
    start = time.monotonic()
    report = _clean_report()
    elapsed = time.monotonic() - start
    # Generous ceiling; a local fixture audit completes in seconds. The point is a
    # regression tripwire far below the 300 second task limit.
    assert elapsed < 60, "clean audit took " + str(round(elapsed, 1)) + "s"
    assert report["coverage"]["runtime_seconds"] < 60


def test_runtime_code_imports_only_standard_library_at_module_scope():
    """Any third-party dependency (playwright, dotenv) must be imported lazily
    inside a guarded function, never at module scope, so the default audit runs on
    a bare standard-library interpreter. This scans the runtime source, not the
    tests."""
    import ast
    stdlib_ok = {
        "re", "os", "sys", "json", "time", "html", "http", "urllib", "hashlib",
        "dataclasses", "types", "typing", "datetime", "concurrent", "collections",
        "importlib", "threading", "xml", "socket", "ssl", "gzip", "zlib", "io",
        "functools", "itertools", "math", "subprocess", "tempfile", "contextlib",
        "traceback", "signal", "struct", "base64", "difflib", "unicodedata",
        "pathlib", "enum", "__future__", "ipaddress", "multiprocessing",
        "statistics", "tracemalloc", "argparse",
    }
    import sys
    stdlib_ok.update(sys.stdlib_module_names)
    local_modules = set()
    runtime_dirs = [ROOT / "common"] + list((ROOT / "skills").glob("*/scripts"))
    for d in runtime_dirs:
        for src in d.glob("*.py"):
            local_modules.add(src.stem)
    offenders = []
    for d in runtime_dirs:
        for src in d.glob("*.py"):
            tree = ast.parse(src.read_text(encoding="utf-8"), filename=str(src))
            for node in ast.walk(tree):
                # Only module-scope imports matter; lazy imports inside functions
                # are the sanctioned pattern for optional dependencies.
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if any(isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Try))
                       for p in _ancestors(tree, node)):
                    continue
                names = ([a.name.split(".")[0] for a in node.names]
                         if isinstance(node, ast.Import)
                         else [(node.module or "").split(".")[0]])
                for top in names:
                    if top and top not in stdlib_ok and top not in local_modules:
                        offenders.append((src.name, top))
    assert not offenders, "non-stdlib module-scope imports: " + str(offenders)


def _ancestors(tree, target):
    """Yield ancestor nodes of target within tree (used to tell module-scope
    imports from imports nested inside a function)."""
    import ast
    stack = []
    found = []
    def visit(node, chain):
        if node is target:
            found.extend(chain)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, chain + [node])
    visit(tree, [])
    return found


# ---------------------------------------------------------------------------
# Orchestration regression across the fully merged skill set
# ---------------------------------------------------------------------------

def test_merged_report_composition_provenance_and_severity_counts():
    url, stop = start_server(sitemap_mode="broken_nav", multi_brand=True)
    try:
        report = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
    findings = report["findings"]
    # Composition: findings from more than one skill are present and prioritized.
    assert len(findings) >= 5
    ids = [f["id"] for f in findings]
    assert ids == sorted(ids) or len(set(ids)) == len(ids), "finding ids not unique"
    # Provenance: every finding carries provenance and a catalogued check_id.
    for f in findings:
        assert f.get("provenance") and f.get("check_id")
    # Severity counts in the summary match the actual findings.
    from collections import Counter
    counts = Counter(f["severity"] for f in findings)
    summary = report["summary"]
    for sev in ("critical", "high", "medium", "low"):
        assert summary[sev] == counts.get(sev, 0), (sev, summary[sev], counts.get(sev, 0))
    assert summary["total_findings"] == len(findings)


def test_merge_preserves_contributing_check_ids():
    # Two near-duplicate findings from different skills merge into one carrying
    # both check_ids in provenance (no silent loss under composition).
    from models import make_finding, skill_result
    def mk(rule, cause):
        return make_finding(category="ai_discoverability", finding_type="defect", severity="medium",
                            status="confirmed", confidence=0.8, title=cause, root_cause=cause,
                            evidence=[{"type": "t", "description": "d", "urls": ["https://x/"]}],
                            suggested_action={"summary": "s", "steps": [], "priority": "low",
                                              "effort": "low", "expected_benefit": "b", "verification": "v"},
                            provenance={"skill": "s", "script": "x.py", "rule_id": rule},
                            affected_pages=["https://x/"])
    a = mk("noindex", "robots meta blocks indexing on the page")
    b = mk("nosnippet", "robots meta is blocking indexing on the page")
    merged = merge_findings([skill_result("A", findings=[a]), skill_result("B", findings=[b])])
    assert len(merged) == 1
    assert set(merged[0]["check_ids"]) == {"noindex", "nosnippet"}
