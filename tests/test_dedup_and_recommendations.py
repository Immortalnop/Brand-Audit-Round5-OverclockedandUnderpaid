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
    # Round 5 (A15): the insufficient-evidence item stays in `findings` (it is not
    # lost) and is NOT copied into recommendations; recommendations hold only
    # beyond-defect and baseline items.
    assert all(r["provenance"].get("finding_id") is None for r in recs)
    assert all(r["finding_type"] == "proactive_improvement" for r in recs)


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
    assert not any(r["provenance"].get("finding_id") == proactive["id"] for r in recs)


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


def test_recommendations_never_copy_findings_and_action_plan_references_them():
    # Round 5 (A15): a finding appears once, in `findings`; the action plan points
    # at it by id, and recommendations never duplicate it.
    from generate_recommendations import build_action_plan
    f = _finding("ai_discoverability", "pages lack description", ["https://x/page1", "https://x/page2"],
                 finding_type="proactive_improvement", status="suspected", severity="low")
    f["priority_score"] = 0.5
    recs = generate_recommendations([skill_result("s", findings=[f])], [f])
    assert not [r for r in recs if r["provenance"].get("source") == "derived_from_finding"]
    assert all(r["title"] != f["title"] for r in recs)
    plan = build_action_plan([f])
    assert plan and plan[0]["finding_ids"] == [f["id"]]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"OK: {name}")
