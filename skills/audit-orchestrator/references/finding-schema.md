# Finding schema

Required fields: id, category, finding_type (defect | proactive_improvement),
title, severity (critical | high | medium | low), confidence, status
(confirmed | suspected | insufficient_evidence | not_applicable |
analysis_failed), affected_pages, root_cause (what was observed), evidence,
suggested_action (summary, steps, priority, effort, owner_role, verification,
optional proposed_snippets), provenance.

Added by scoring: severity_rationale, priority_score, tier.

Invariant I-1: if status == "insufficient_evidence", then finding_type must be
"proactive_improvement" and severity must be "low". Enforced at creation time
(`common/models.py: apply_invariant_i1`), in scoring, and again at validation time
(`validate_report.py`).
