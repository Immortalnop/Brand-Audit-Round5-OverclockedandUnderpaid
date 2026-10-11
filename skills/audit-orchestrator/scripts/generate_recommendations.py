"""generate_recommendations.py -- proactive recommendation layer.

Guarantees every successful audit ships a useful, first-class recommendations
section, even when: no defects are confirmed, all evidence is insufficient, the
site is small, or the site is already well-structured. Recommendations are:

  - evidence-aware   : derived from actual SkillResult/metrics/findings, not invented.
  - non-duplicative  : reuse merge_findings' normalize/similarity logic so a
                        recommendation never restates a confirmed defect's fix.
  - calibrated       : confidence and specificity reflect how much evidence backs them.
  - separated        : always finding_type == "proactive_improvement", carried in the
                        report's own `recommendations` array, never mixed into
                        `findings`.
  - linked, not copied: a proactive finding appears here as a short reference
                        ({id, finding_id, check_id, category, title, status});
                        its evidence, steps and fix stay on the finding itself.
                        Only the baseline items, which have no finding, carry
                        their own action.
"""
from merge_findings import dedup_key, similarity
from models import apply_invariant_i1
from check_catalog import enrich_finding
from action_catalog import baseline_action, evidence_status_mode

_GENERIC_BASELINE = [
    {
        "category": "ai_discoverability",
        "title": "Periodically re-audit AI discoverability as content changes",
        "rationale": "No discoverability defects were confirmed in this audit, but "
                     "crawlers, robots policies, and structured-data conventions "
                     "change independently of visible site content.",
        "steps": ["Re-run this audit on a recurring schedule",
                  "Re-validate JSON-LD after any template or CMS change"],
        "confidence": 0.5,
    },
    {
        "category": "engagement",
        "title": "Keep internal linking intentional as the site grows",
        "rationale": "No orphan or dead-end pages were confirmed now, but new pages "
                     "commonly launch without inbound links or a clear next step.",
        "steps": ["Add new pages to relevant navigation or related-content sections",
                  "Give every page at least one outbound next step"],
        "confidence": 0.5,
    },
    {
        "category": "off_site_presence",
        "title": "Continue building independent, identity-matched off-site mentions",
        "rationale": "Off-site presence is cumulative; even a well-corroborated brand "
                     "benefits from continued, diverse independent mentions.",
        "steps": ["List on relevant directories", "Keep sameAs/social profiles active"],
        "confidence": 0.4,
    },
]


def is_finding_reference(item) -> bool:
    """True for a recommendation that points at a finding instead of carrying
    its own evidence and action."""
    return isinstance(item, dict) and "finding_id" in item


def _recommendation_from_finding(rid: int, finding: dict) -> dict:
    """A pointer to a proactive finding: its ID, check and title. The finding
    holds the evidence, steps and fix, so none of it is copied here."""
    return {
        "id": f"R-{rid:03d}",
        "finding_id": finding["id"],
        "check_id": finding.get("check_id"),
        "check_ids": list(finding.get("check_ids") or []),
        "category": finding["category"],
        "finding_type": "proactive_improvement",
        "title": finding["title"],
        "status": finding["status"],
        "provenance": {"source": "finding_reference"},
    }


def _recommendation_from_baseline(rid: int, item: dict) -> dict:
    # 2.4: draw ticket-level action content from the rich action catalog when the
    # category has a dedicated maintenance action, falling back to the item's own
    # stub otherwise. v6's calibrated baseline confidence is retained unchanged.
    rich = baseline_action(item["category"])
    steps = list(rich["steps"]) if rich else item["steps"]
    status = "insufficient_evidence" if item["confidence"] < 0.6 else "confirmed"
    action = {
        "summary": item["title"], "steps": steps, "priority": "low",
        "effort": "low", "expected_benefit": "Maintains current AI-readiness posture",
        "verification": rich["verification"] if rich else "Re-audit periodically",
    }
    if rich:
        action["implementation_detail"] = rich["implementation_detail"]
        action["expected_outcome"] = rich["expected_outcome"]
    return apply_invariant_i1({
        "id": f"R-{rid:03d}",
        "check_id": "baseline:" + item["category"],
        "category": item["category"],
        "finding_type": "proactive_improvement",
        "title": item["title"],
        "severity": "low",
        "confidence": item["confidence"],
        "status": status,
        "evidence_status": evidence_status_mode(status),
        "affected_pages": [],
        "root_cause": item["rationale"],
        "evidence": [],
        "evidence_text": "",
        "suggested_action": action,
        "provenance": {"source": "baseline_calibrated"},
    })


def generate_recommendations(skill_results: list, merged_findings: list) -> list:
    defect_keys = {dedup_key(f) for f in merged_findings if f["finding_type"] == "defect"}
    proactive = [f for f in merged_findings if f["finding_type"] == "proactive_improvement"]

    recommendations, seen_keys = [], []
    rid = 0
    for f in proactive:
        key = dedup_key(f)
        # Non-duplicative w.r.t. confirmed defects: don't recommend fixing something
        # already reported as a defect in the same category/scope.
        if any(key[0] == dk[0] and key[2] == dk[2] and similarity(key[1], dk[1]) >= 0.85 for dk in defect_keys):
            continue
        # Non-duplicative w.r.t. recommendations already added this run.
        if any(key[0] == sk[0] and key[2] == sk[2] and similarity(key[1], sk[1]) >= 0.85 for sk in seen_keys):
            continue
        rid += 1
        recommendations.append(_recommendation_from_finding(rid, f))
        seen_keys.append(key)

    covered_categories = {r["category"] for r in recommendations} | {dk[0] for dk in defect_keys}
    for item in _GENERIC_BASELINE:
        if item["category"] in covered_categories:
            continue  # already covered by a real finding/recommendation -- no filler duplicate
        rid += 1
        recommendations.append(_recommendation_from_baseline(rid, item))

    return [r if is_finding_reference(r) else enrich_finding(r) for r in recommendations]
