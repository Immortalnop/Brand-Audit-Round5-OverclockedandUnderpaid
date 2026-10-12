"""prioritize_findings.py -- deterministic ordering of findings by impact.

Ordering key (descending), applied after common/scoring.py has set the final
severity, confidence and priority_score of every finding:
  1. severity rank   (critical > high > medium > low) -- impact always leads
  2. priority_score  = impact[severity] x reach(scope) x confidence / effort_cost,
                       i.e. within one severity: broader, surer, cheaper first
  3. status rank     (confirmed > suspected > analysis_failed > insufficient_evidence)
  4. confidence
  5. number of affected pages (breadth / one-fix-many value)
Ties are broken by a stable baseline sort on (title, affected pages, root cause),
so the same set of findings always comes out in exactly the same order,
independent of dict or set iteration order upstream. Ids (F-001 ...) are
assigned by the caller AFTER this ordering, so F-001 is always the top item.
"""
_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_STATUS_RANK = {"confirmed": 3, "suspected": 2, "analysis_failed": 1,
                "insufficient_evidence": 0, "not_applicable": 0}


def _score(finding: dict) -> tuple:
    return (_SEVERITY_RANK.get(finding["severity"], 0),
            finding.get("priority_score", 0.0),
            _STATUS_RANK.get(finding["status"], 0),
            finding.get("confidence", 0.0),
            len(finding.get("affected_pages") or []))


def prioritize_findings(findings: list) -> list:
    # Defense-in-depth re-check: Invariant I-1 is already enforced at finding
    # creation time (make_finding / apply_invariant_i1).
    for f in findings:
        if f["status"] == "insufficient_evidence" and f["finding_type"] != "proactive_improvement":
            raise ValueError(f"Invariant I-1 violated by finding {f['id']}")
    baseline = sorted(findings, key=lambda f: (f.get("title", ""), tuple(sorted(f.get("affected_pages", []))),
                                               f.get("root_cause", "")))
    return sorted(baseline, key=_score, reverse=True)
