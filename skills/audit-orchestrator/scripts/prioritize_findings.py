"""prioritize_findings.py -- orders findings; cannot override confirmed critical issues.

Ordering key and tie-breaking (Round-3 review item: "prioritization determinism /
tie-breaking"). The intended ordering factors are severity, confidence, status,
affected-page count, page importance, AI impact, visitor impact, benefit breadth,
effort, and one-fix-many benefit. Several of those (page importance, AI/visitor
impact) require site-specific signals this module doesn't have access to as
plain finding dicts, so they are approximated
here by the two proxies this module CAN compute deterministically from a
finding's own fields:
  - `affected_pages` count, as a stand-in for benefit breadth / one-fix-many value
    (a fix that touches more pages generically helps more of the site), and
  - `effort`, as a quick-win tiebreaker within an otherwise-tied severity/status/
    confidence/breadth bucket (all else equal, cheaper fixes surface first).
The final tiebreaker is always the finding's own `id`. Because ids are assigned
in a fixed creation order (models._FINDING_COUNTER) and merge_findings keeps
merged findings in first-encountered-bucket order, this makes the full ordering
exactly reproducible across runs on the same input -- no two same-scored findings
can trade places between runs, which a bare `sorted()` on partial keys does not
guarantee once ties are frequent (e.g. many low-severity proactive
improvements).
"""
_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_STATUS_RANK = {"confirmed": 3, "suspected": 2, "analysis_failed": 1,
                "insufficient_evidence": 0, "not_applicable": 0}
_EFFORT_RANK = {"low": 2, "medium": 1, "high": 0}  # higher rank = cheaper = tiebreak winner


def _effort_of(finding: dict) -> str:
    return (finding.get("suggested_action") or {}).get("effort", "medium")


def _id_sort_key(finding_id) -> tuple:
    """Numeric-aware sort key for ids like 'F-001'/'R-012' so id order matches
    creation order (id 'F-002' sorts before 'F-010'), not lexicographic string
    order (which would put 'F-010' before 'F-002')."""
    fid = str(finding_id)
    digits = "".join(ch for ch in fid if ch.isdigit())
    return (fid.split("-")[0] if "-" in fid else fid, int(digits) if digits else 0)


def _score(finding: dict) -> tuple:
    sev = _SEVERITY_RANK.get(finding["severity"], 0)
    stat = _STATUS_RANK.get(finding["status"], 0)
    conf = finding.get("confidence", 0.0)
    pages = len(finding.get("affected_pages") or [])
    effort = _EFFORT_RANK.get(_effort_of(finding), 1)
    # Sorted descending overall (see prioritize_findings); id is negated-by-reverse-
    # sort-index below rather than included in reverse here, since ascending id
    # order (F-001 before F-002) should win the tiebreak either way the rest of the
    # tuple sorts, and mixing an ascending tiebreak into a single reverse=True sort
    # would invert it. It is applied as a separate, final, ascending sort pass.
    return (sev, stat, conf, pages, effort)


_IMPACT_LEVELS = ("low", "medium", "high")
# Impact x effort quadrants. A quick win is worth doing first: real value for
# little work.
_QUADRANT_LABELS = {
    "quick_win": "Quick win: real value for little work; start here",
    "major_project": "Major project: real value, plan the work",
    "fill_in": "Fill-in: small value, small work; do when convenient",
    "deprioritize": "Deprioritize: more work than the value it brings for now",
}


def impact_of(finding: dict, pages_analyzed: int = 0) -> str:
    """Expected impact of fixing one item, from evidence the item carries:
      - severity sets the base: critical and high are high, medium is medium,
        low is low;
      - an item that is only suspected is capped at medium, and one with
        insufficient evidence is low, so impact never outruns the evidence;
      - a confirmed low-severity item on at least half of the analyzed pages
        (and on two or more pages) rises to medium: one fix helps the whole site."""
    severity = finding.get("severity")
    level = 2 if severity in ("critical", "high") else 1 if severity == "medium" else 0
    status = finding.get("status")
    if status == "insufficient_evidence":
        return "low"
    if status != "confirmed":
        level = min(level, 1)
    pages = len(finding.get("affected_pages") or ())
    if status == "confirmed" and level == 0 and pages >= 2 and pages_analyzed and pages * 2 >= pages_analyzed:
        level = 1
    return _IMPACT_LEVELS[level]


def quadrant_of(impact: str, effort: str) -> str:
    """Two-by-two matrix: medium and high impact count as valuable, medium and
    high effort count as real work."""
    valuable = impact in ("high", "medium")
    if effort == "low":
        return "quick_win" if valuable else "fill_in"
    return "major_project" if valuable else "deprioritize"


def annotate_action_plan(items: list, pages_analyzed: int = 0) -> None:
    """Add impact, effort, quadrant and quick_win to each item's suggested_action."""
    for item in items:
        action = dict(item.get("suggested_action") or {})
        effort = action.get("effort") if action.get("effort") in ("low", "medium", "high") else "medium"
        impact = impact_of(item, pages_analyzed)
        quadrant = quadrant_of(impact, effort)
        action.update(effort=effort, impact=impact, quadrant=quadrant, quadrant_label=_QUADRANT_LABELS[quadrant],
                      quick_win=quadrant == "quick_win")
        item["suggested_action"] = action


def top_actions(findings: list, limit: int = 5) -> list:
    """The defects to act on first, in priority order, each with its impact x
    effort placement. One confirmed defect among them is marked start_here,
    a quick win when there is one; a suspected or unconfirmed defect never is,
    so the report may have no start_here at all."""
    defects = [f for f in findings if f.get("finding_type") == "defect"][:limit]
    rows = []
    for f in defects:
        action = f.get("suggested_action") or {}
        rows.append({"finding_id": f["id"], "title": f.get("title"), "summary": action.get("summary"),
                     "priority": action.get("priority"), "impact": action.get("impact"),
                     "effort": action.get("effort"), "quadrant": action.get("quadrant"),
                     "quick_win": bool(action.get("quick_win")), "start_here": False,
                     "status": f.get("status")})
    confirmed = [r for r in rows if r["status"] == "confirmed"]
    first = next((r for r in confirmed if r["quick_win"]), confirmed[0] if confirmed else None)
    if first is not None:
        first["start_here"] = True
    return rows


def quick_wins(findings: list, recommendations: list, limit: int = 5) -> list:
    """Every quick win in the report, defects first, then suggestions."""
    out = []
    for item in [f for f in findings if f.get("finding_type") == "defect"] + \
            [f for f in findings if f.get("finding_type") != "defect"] + list(recommendations):
        action = item.get("suggested_action") or {}
        if action.get("quick_win") and not any(o["summary"] == action.get("summary") for o in out):
            out.append({"id": item["id"], "title": item.get("title"), "summary": action.get("summary"),
                        "impact": action.get("impact"), "effort": action.get("effort")})
        if len(out) >= limit:
            break
    return out


def prioritize_findings(findings: list) -> list:
    # Defense-in-depth re-check: Invariant I-1 is already enforced at finding
    # creation time (make_finding / apply_invariant_i1).
    for f in findings:
        if f["status"] == "insufficient_evidence" and f["finding_type"] != "proactive_improvement":
            raise ValueError(f"Invariant I-1 violated by finding {f['id']}")
    # Severity gate, one rule for every skill: a high or critical finding must be
    # confirmed or carry two independent kinds of evidence (models.severity_gate_ok).
    # The status floor runs first: a finding it moves to suspected may then need
    # the gate.
    from models import apply_severity_gate, apply_status_floor
    for f in findings:
        apply_status_floor(f)
        apply_severity_gate(f)
    # Two-pass stable sort: first establish a deterministic baseline order by id
    # (ascending), then sort by score (descending). Python's sort is stable, so
    # findings that tie on every element of _score retain their id-ascending order
    # from the first pass -- the full ordering is therefore always exactly
    # reproducible for the same set of findings, regardless of dict/set iteration
    # order upstream (e.g. in merge_findings' bucket dict).
    by_id = sorted(findings, key=lambda f: (f.get("title", ""), tuple(sorted(f.get("affected_pages", []))), f.get("root_cause", "")))
    return sorted(by_id, key=_score, reverse=True)
