"""Dedup algorithm tests (near-duplicate merge vs distinct non-merge) and the
recommendations layer's four required scenarios: no defects, all insufficient
evidence, a small site, and an already-well-structured site."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from models import make_finding, skill_result
from merge_findings import merge_findings
from generate_recommendations import generate_recommendations


def _finding(category, root_cause, pages, finding_type="defect", status="confirmed", severity="medium"):
    return make_finding(
        category=category, finding_type=finding_type, severity=severity, status=status, confidence=0.8,
        title=root_cause, root_cause=root_cause, evidence=[{"type": "t", "description": "d", "urls": pages}],
        suggested_action={"summary": "s", "steps": [], "priority": "low", "effort": "low",
                           "expected_benefit": "b", "verification": "v"},
        provenance={"skill": "test", "script": "test.py", "rule_id": "r"}, affected_pages=pages,
    )


def test_near_duplicates_from_different_skills_merge():
    a = _finding("ai_discoverability", "robots.txt blocks crawler access to the site", ["https://x/"])
    b = _finding("ai_discoverability", "robots.txt is blocking crawler access on the site", ["https://x/"])
    results = [skill_result("skillA", findings=[a]), skill_result("skillB", findings=[b])]
    merged = merge_findings(results)
    assert len(merged) == 1
    assert len(merged[0]["provenance"]["contributing_skills"]) == 2


def test_distinct_findings_same_category_and_scope_do_not_merge():
    a = _finding("ai_discoverability", "robots.txt blocks crawler access", ["https://x/"])
    b = _finding("ai_discoverability", "page returns a 500 server error", ["https://x/"])
    results = [skill_result("skillA", findings=[a, b])]
    merged = merge_findings(results)
    assert len(merged) == 2


def test_merge_findings_rejects_intermediate_artifact_input():
    try:
        merge_findings([{"artifact_type": "claims", "status": "success", "data": {}, "warnings": []}])
        assert False, "should have raised"
    except ValueError:
        pass


def test_recommendations_present_when_no_defects_confirmed():
    results = [skill_result("s", findings=[])]
    recs = generate_recommendations(results, [])
    assert len(recs) > 0
    assert all(r["finding_type"] == "proactive_improvement" for r in recs)


def test_recommendations_present_when_all_evidence_insufficient():
    insufficient = _finding("freshness", "no dated facts found", [], finding_type="proactive_improvement",
                             status="insufficient_evidence", severity="low")
    results = [skill_result("s", findings=[insufficient])]
    recs = generate_recommendations(results, [insufficient])
    assert len(recs) > 0
    # The insufficient-evidence finding itself should surface as a recommendation, not be lost.
    assert any(r.get("finding_id") == insufficient["id"] for r in recs)


def test_recommendations_present_for_small_well_structured_site():
    # No findings at all -- fully clean audit -- must still produce calibrated baseline recs.
    recs = generate_recommendations([], [])
    assert len(recs) >= 1
    assert {r["category"] for r in recs}.issubset({"ai_discoverability", "engagement", "off_site_presence"})


def test_recommendations_do_not_duplicate_confirmed_defects():
    same_cause = "no structured data json ld found on any crawled page"
    defect = _finding("ai_discoverability", same_cause, ["https://x/"])
    proactive = _finding("ai_discoverability", same_cause,
                          ["https://x/"], finding_type="proactive_improvement", status="confirmed", severity="low")
    results = [skill_result("s", findings=[defect, proactive])]
    merged = [defect, proactive]
    recs = generate_recommendations(results, merged)
    # The proactive near-duplicate of the confirmed defect must be suppressed as a recommendation.
    assert not any(r.get("finding_id") == proactive["id"] for r in recs)


def test_robots_inaccessible_cascade_merges_into_single_finding():
    f1 = make_finding(
        category="ai_discoverability", finding_type="proactive_improvement", severity="low",
        status="insufficient_evidence", confidence=0.3, title="robots.txt could not be retrieved or parsed",
        root_cause="robots.txt fetch/parse status was 'inaccessible'",
        evidence=[{"type": "robots", "description": "robots status inaccessible", "urls": ["https://x/"]}],
        suggested_action={"summary": "s", "steps": [], "priority": "low", "effort": "low", "expected_benefit": "b", "verification": "v"},
        provenance={"skill": "crawl-render-audit", "script": "analyze_crawlability.py", "rule_id": "robots-unreachable"},
        affected_pages=["https://x/"],
    )
    f2 = make_finding(
        category="ai_discoverability", finding_type="proactive_improvement", severity="low",
        status="insufficient_evidence", confidence=0.3, title="Acquisition could not assess a URL",
        root_cause="This audit client encountered cross_origin_redirect_blocked.",
        evidence=[{"type": "transport_limitation", "description": "Acquisition outcome: ...", "urls": ["https://x/robots.txt"]}],
        suggested_action={"summary": "s", "steps": [], "priority": "low", "effort": "low", "expected_benefit": "b", "verification": "v"},
        provenance={"skill": "crawl-render-audit", "script": "analyze_directives.py", "rule_id": "fetch-failure"},
        affected_pages=["https://x/robots.txt"],
    )
    f3 = make_finding(
        category="ai_discoverability", finding_type="proactive_improvement", severity="low",
        status="insufficient_evidence", confidence=0.3, title="AI-crawler access could not be checked",
        root_cause="robots.txt status was 'inaccessible'; AI-crawler directives were not evaluated",
        evidence=[{"type": "directives", "description": "unchecked", "urls": []}],
        suggested_action={"summary": "s", "steps": [], "priority": "low", "effort": "low", "expected_benefit": "b", "verification": "v"},
        provenance={"skill": "crawl-render-audit", "script": "analyze_directives.py", "rule_id": "ai-crawler-unchecked"},
        affected_pages=[],
    )
    results = [skill_result("crawl-render-audit", findings=[f1, f2, f3])]
    merged = merge_findings(results)
    assert len(merged) == 1
    assert set(merged[0]["check_ids"]) == {"ai-crawler-unchecked", "fetch-failure", "robots-unreachable"}
    assert "https://x/robots.txt" in merged[0]["affected_pages"]
    assert "https://x/" in merged[0]["affected_pages"]


def test_recommendation_links_to_its_finding_instead_of_copying_it():
    f = _finding("ai_discoverability", "pages lack description", ["https://x/page1", "https://x/page2"],
                 finding_type="proactive_improvement", status="suspected", severity="low")
    recs = generate_recommendations([skill_result("s", findings=[f])], [f])
    linked = [r for r in recs if r.get("finding_id") == f["id"]]
    assert len(linked) == 1
    ref = linked[0]
    assert ref["provenance"] == {"source": "finding_reference"}
    assert ref["title"] == f["title"] and ref["category"] == f["category"]
    assert ref["finding_type"] == "proactive_improvement"
    # Nothing of the finding's body is copied: no evidence, pages, action or wording.
    for key in ("evidence", "evidence_text", "affected_pages", "suggested_action", "root_cause",
                "mechanism", "implementation_detail", "expected_outcome"):
        assert key not in ref, key


def test_validation_keeps_links_to_reported_findings_and_drops_dangling_ones():
    from validate_report import validate_report
    f = _finding("ai_discoverability", "pages lack description", ["https://x/p"],
                 finding_type="proactive_improvement", status="suspected", severity="low")
    recs = generate_recommendations([skill_result("s", findings=[f])], [f])
    base = {"site": "https://x/", "audited_at": "t", "summary": {}, "coverage": {}, "execution_status": "completed",
            "limitations": [], "confidence": {"score": 1, "explanation": "e"}}
    kept = validate_report(dict(base, findings=[f], recommendations=list(recs)))
    assert [r["id"] for r in kept["recommendations"]] == [r["id"] for r in recs]
    assert kept["summary"]["total_recommendations"] == len(recs)
    # The finding is gone, so the link to it is dropped, with a warning.
    gone = validate_report(dict(base, findings=[], recommendations=list(recs)))
    assert not any(r.get("finding_id") for r in gone["recommendations"])
    assert any(f["id"] + " is not in the report" in w for w in gone["warnings"])
    # Malformed links and a link listed twice are dropped without raising.
    bad = [{"id": "R-101", "finding_id": ["F-001"], "title": "t", "finding_type": "proactive_improvement"},
           {"id": "R-102", "finding_id": f["id"], "title": "t", "finding_type": "defect"},
           {"id": 7, "finding_id": f["id"], "title": "t", "finding_type": "proactive_improvement"}]
    twice = [r for r in recs if r.get("finding_id")] * 2
    out = validate_report(dict(base, findings=[f], recommendations=bad + twice))
    assert [r["id"] for r in out["recommendations"]] == [twice[0]["id"]]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"OK: {name}")
