"""action_catalog.py -- ticket-level action content and evidence-status modes.

Two responsibilities, both kept out of the detection scripts so the wording is
reviewed once and stays consistent:

1. Baseline action content. When the recommendation engine emits a
   category-level proactive item (no confirmed defect in that category), it draws
   concrete steps, implementation_detail, expected_outcome and verification from
   here instead of a thin inline stub. Detectors still own observed evidence; this
   only enriches the always-on maintenance recommendations.

2. Evidence-status modes. A single explicit mapping from a finding/recommendation
   status to a short reader-facing description of what that status means. This
   makes the confirmed / suspected / insufficient_evidence distinction explicit on
   every recommendation rather than implicit in the numbers. It records the meaning
   of a status; it never changes severity or type, which remain governed by
   Invariant I-1 (make_finding / apply_invariant_i1).
"""
from types import MappingProxyType

# Reader-facing meaning of each status. insufficient_evidence is the absence of a
# result, not a result of absence, so it is advisory by Invariant I-1.
EVIDENCE_STATUS_MODES = MappingProxyType({
    "confirmed": "The observed evidence directly demonstrates the reported condition.",
    "suspected": "The signal is real but a confounder could not be ruled out with "
                 "the evidence gathered in this run.",
    "not_applicable": "General best practice: no site defect is asserted; the item "
                      "is offered because nothing was found in its category.",
    "insufficient_evidence": "The check could not be completed on this run; this is "
                             "the absence of a result, not evidence of a defect, so "
                             "it is reported as advisory only.",
})


def evidence_status_mode(status):
    """Return the reader-facing description for a status, defaulting to the
    advisory meaning for any unknown value rather than raising."""
    return EVIDENCE_STATUS_MODES.get(status, EVIDENCE_STATUS_MODES["insufficient_evidence"])


# Category-level maintenance actions. Richer than a one-line stub: each carries the
# same four-part action shape the detectors use, so baseline recommendations read
# like real tickets. Confidence is NOT set here; the recommendation engine keeps
# the calibrated baseline confidence so severity/confidence stay consistent.
BASELINE_ACTIONS = MappingProxyType({
    "ai_discoverability": MappingProxyType({
        "steps": (
            "Re-run this audit on a recurring schedule so drift is caught early",
            "Re-validate JSON-LD after any template or CMS change",
            "Confirm robots and AI-crawler directives still match the intended policy",
        ),
        "implementation_detail": "Schedule a periodic re-audit and re-validate "
                                 "structured data and crawler directives after "
                                 "template, CMS or policy changes.",
        "expected_outcome": "Discoverability regressions are caught close to the "
                            "change that caused them rather than months later.",
        "verification": "Compare each scheduled run against the previous baseline "
                        "and investigate new blocks or invalid markup.",
    }),
    "engagement": MappingProxyType({
        "steps": (
            "Add every new page to relevant navigation or related-content sections",
            "Give each page at least one descriptive outbound next step",
            "Use descriptive, destination-naming anchor text for internal links",
        ),
        "implementation_detail": "Treat internal linking as part of publishing: link "
                                 "new pages inbound and outbound with descriptive "
                                 "anchors as they launch.",
        "expected_outcome": "Pages stay reachable and hand visitors a relevant next "
                            "step as the site grows, instead of accumulating orphans.",
        "verification": "Re-crawl after publishing and confirm new pages have both "
                        "inbound and outbound internal links.",
    }),
    "off_site_presence": MappingProxyType({
        "steps": (
            "List the brand on relevant, reputable directories",
            "Keep sameAs and social profiles active and identity-consistent",
            "Encourage independent, identity-matched mentions over time",
        ),
        "implementation_detail": "Maintain a small set of authoritative, "
                                 "identity-consistent off-site profiles and pursue "
                                 "diverse independent mentions.",
        "expected_outcome": "Corroboration of the brand's identity grows more robust "
                            "and less dependent on any single source.",
        "verification": "Periodically confirm off-site profiles resolve to the same "
                        "canonical identity as the site.",
    }),
})


def baseline_action(category):
    """Return the rich action block for a category, or None when the category has
    no dedicated maintenance action (the engine then falls back to its stub)."""
    return BASELINE_ACTIONS.get(category)
