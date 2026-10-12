"""test_review_regressions.py -- the boundary cases an external review reproduced.

Each test here pins one defect that an independent review of this branch found
and that the branch's own suite did not cover. They are grouped by the review's
identifiers (A1..A13) so a regression can be traced back to the case that
motivated the rule. Everything here is offline: fixtures, pure functions and
one local ThreadingHTTPServer.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    sys.path.insert(0, str(ROOT / rel))

SITE = "https://shop.example/"


# --------------------------------------------------------------- A1 agent input
def _ingest(tmp_path, payload, site=SITE):
    from ingest_agent_findings import load_agent_findings
    path = tmp_path / "ag.json"
    path.write_text(json.dumps(payload))
    return load_agent_findings(str(path), site)


def test_a1_claim_without_an_observation_is_not_published(tmp_path):
    """[{"check": "AG-03"}] used to become a confirmed, high, 0.7-confidence
    contradiction with a generic fallback observation."""
    result, stage = _ingest(tmp_path, [{"check": "AG-03"}])
    assert result["findings"] == []
    assert result["metrics"]["rejection_reasons"] == ["AG-03:no_observation"]
    assert stage == "empty_unspecified"


def test_a1_evidence_with_urls_but_no_description_does_not_raise(tmp_path):
    """A dict carrying only urls used to raise KeyError('description')."""
    result, _ = _ingest(tmp_path, [{"check": "AG-03", "evidence": [{"type": "x", "urls": ["https://a.example/t"]}]}])
    assert result["findings"] == []  # a URL alone is not an observation


def test_a1_severity_ceiling_per_check(tmp_path):
    """The agent may lower a severity but never raise it past the check's meaning,
    and no agent finding is ever critical."""
    result, _ = _ingest(tmp_path, [{"check": "AG-01", "severity": "critical", "status": "confirmed",
                                    "evidence": [{"description": "The opening names no product and no market.",
                                                  "urls": [SITE + "about"]}]}])
    assert result["findings"][0]["severity"] == "medium"
    result, _ = _ingest(tmp_path, [{"check": "AG-02", "severity": "high", "status": "confirmed",
                                    "evidence": "Ran the brand and category queries; nothing independent came back."}])
    assert result["findings"][0]["severity"] == "low"


def test_a1_contradiction_without_a_source_is_capped_at_suspected(tmp_path):
    result, _ = _ingest(tmp_path, [{"check": "AG-03", "status": "confirmed",
                                    "evidence": "Two directories list it as a freight broker; the site says payroll."}])
    f = result["findings"][0]
    assert f["status"] == "suspected" and f["confidence"] <= 0.5
    assert f["provenance"]["evidence_gaps"] == ["no independent source URL was supplied"]
    assert any(e["type"] == "evidence_gap" for e in f["evidence"])


def test_a1_contradiction_with_a_source_is_confirmed_and_origin_split(tmp_path):
    result, _ = _ingest(tmp_path, [{"check": "AG-03", "status": "confirmed", "evidence": [
        {"description": "A directory lists it as a freight broker; the site says payroll.",
         "urls": ["https://dir.example/x", SITE + "about"]}]}])
    f = result["findings"][0]
    assert f["status"] == "confirmed" and f["severity"] == "high"
    # The third-party thread is evidence, never a page of the site with the defect.
    assert f["affected_pages"] == [SITE + "about"]
    assert f["provenance"]["source_references"] == ["https://dir.example/x"]


def test_a1_absence_claim_needs_a_recorded_search(tmp_path):
    bare = [{"check": "AG-02", "status": "confirmed",
             "evidence": "Searched the brand name and category; nothing independent came back."}]
    result, _ = _ingest(tmp_path, bare)
    assert result["findings"][0]["status"] == "suspected"
    result, _ = _ingest(tmp_path, {"search": {"available": True, "queries_run": 3}, "findings": bare})
    assert result["findings"][0]["status"] == "confirmed"


def test_a1_empty_array_is_not_an_all_pass(tmp_path):
    result, stage = _ingest(tmp_path, [])
    assert stage == "empty_unspecified"
    assert set(result["metrics"]["check_outcomes"].values()) == {"unreported"}
    assert any("not assessed rather than passed" in w for w in result["warnings"])
    # With explicit per-check outcomes the stage can say what actually passed.
    result, stage = _ingest(tmp_path, {"findings": [], "checks": {"AG-01": "pass", "AG-02": "not_assessed"},
                                       "search": {"available": False}})
    assert stage == "assessed_no_findings"
    assert result["metrics"]["check_outcomes"]["AG-01"] == "pass"
    assert result["metrics"]["check_outcomes"]["AG-03"] == "unreported"


def test_a1_findings_bound_to_another_site_are_refused(tmp_path):
    result, stage = _ingest(tmp_path, {"site": "https://other.example/",
                                       "findings": [{"check": "AG-03", "evidence": "x" * 60}]})
    assert stage == "not_supplied" and result["findings"] == []
    assert result["metrics"]["rejection_reasons"] == ["site_mismatch"]


def test_a1_oversized_handoff_is_a_skip_not_a_crash(tmp_path):
    from ingest_agent_findings import load_agent_findings, MAX_FINDINGS_BYTES
    path = tmp_path / "ag.json"
    path.write_text(json.dumps([{"check": "AG-03", "evidence": "x" * (MAX_FINDINGS_BYTES + 100)}]))
    result, stage = load_agent_findings(str(path), SITE)
    assert stage == "not_supplied" and result["status"] == "insufficient_evidence"


def test_a1_non_http_urls_and_overlong_text_are_sanitized(tmp_path):
    from ingest_agent_findings import MAX_EVIDENCE_CHARS
    result, _ = _ingest(tmp_path, [{"check": "AG-04", "evidence": [
        {"description": "The price-list image shows three prices absent from the page text. " + "z" * 2000,
         "urls": ["javascript:alert(1)", "data:text/html,x", SITE + "menu"]}]}])
    f = result["findings"][0]
    assert f["affected_pages"] == [SITE + "menu"]
    assert f["evidence"][0]["urls"] == [SITE + "menu"]
    assert len(f["evidence"][0]["description"]) <= MAX_EVIDENCE_CHARS


def test_a1_placeholder_text_is_not_an_observation(tmp_path):
    for text in ("n/a", "see above", "unknown", "Agent-supplied qualitative observation"):
        result, _ = _ingest(tmp_path, [{"check": "AG-03", "status": "confirmed", "evidence": text}])
        assert result["findings"] == [], text


def test_a1_malformed_and_blank_handoffs_stay_skips(tmp_path):
    from ingest_agent_findings import load_agent_findings
    path = tmp_path / "ag.json"
    for body in ("{ not json ,,,", "", "null", '{"findings": "nope"}'):
        path.write_text(body)
        result, stage = load_agent_findings(str(path), SITE)
        assert stage == "not_supplied", body
        assert result["status"] == "insufficient_evidence"
    # A partially usable list keeps the good entry and counts the bad ones.
    result, stage = _ingest(tmp_path, [{"check": "AG-99", "evidence": "y" * 60}, "nonsense",
                                       {"check": "AG-01", "status": "suspected", "evidence": [
                                           {"description": "The opening names no product or market.",
                                            "urls": [SITE + "about"]}]}])
    assert stage == "ingested" and len(result["findings"]) == 1
    assert result["metrics"]["findings_rejected"] == 2
