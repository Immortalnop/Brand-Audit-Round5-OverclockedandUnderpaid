"""ingest_agent_findings.py -- in-process bridge for the agent-executed stage.

The entity-corroboration-agent skill is the one qualitative stage in this
marketplace: the calling agent, not a deterministic script, judges About-page
concreteness (AG-01) and cross-web agreement or contradiction (AG-02 / AG-03)
using its own reading and web_search tools, per the handout's explicit allowance
to query public community platforms such as Reddit and Quora. That judgment is
handed back as a small JSON array; this module ingests it in-process and returns
a SkillResult in exactly the same shape as every other specialist.

Two entry points share one builder. The normal two-pass flow is: run_audit
writes agent_brief.json, the agent searches, then finalize_report.py calls
load_agent_findings(path). ingest_agent_findings() is kept for callers that set
AGENT_FINDINGS_PATH before a single-pass run. Either way every ingested finding is
reconstructed through common.models.make_finding, so the catalog enrichment and
Invariant I-1 capping that govern script findings govern agent findings too. The
agent never constructs the final finding object; it supplies only what it
observed.

Graceful skip: when no agent findings are supplied -- the
common case in an evaluation harness that has not run the qualitative stage --
the stage records not_supplied and returns insufficient_evidence. It never
upgrades "the stage did not run" into "no corroboration exists"; that asymmetry
is the single most common way an audit manufactures a false negative.
"""
import json
import os

from models import (skill_result, make_finding, insufficient_evidence_result,
                     apply_invariant_i1)

# Environment variable naming the agent's findings file. Kept as an env var (not a
# fixed workdir path) so nothing about this stage assumes a subprocess
# workdir convention; when it is unset, the stage simply skips.
_FINDINGS_ENV = "AGENT_FINDINGS_PATH"

# AG check IDs -> catalog rule IDs, category, and the honest status/severity the
# agent stage is allowed to assert. AG-02 and AG-03 are confirmed only because a
# real search ran; the caller must not emit them for the "could not check" case,
# which is represented by the graceful skip instead.
_AG_RULES = {
    "AG-01": {
        "rule_id": "about-concreteness",
        "category": "answer_content",
        "default_severity": "medium",
        "default_status": "suspected",
        "default_type": "proactive_improvement",
        "title": "About-page self-description is not concrete enough to quote",
        "summary": "Rewrite the opening of the About page to name who the organization is, "
                   "what it sells or does, and in which category.",
        "steps": ("State plainly who the organization is in the first two sentences",
                  "Name the specific product or service and its market or category",
                  "Keep the wording factual and consistent with Organization markup"),
    },
    "AG-02": {
        "rule_id": "no-independent-mention",
        "category": "off_site_presence",
        "default_severity": "low",
        "default_status": "confirmed",
        "default_type": "proactive_improvement",
        "title": "No independent mention of the brand was found",
        "summary": "Build authentic, identity-matched presence where the brand's category "
                   "is discussed.",
        "steps": ("Participate substantively in relevant community platforms",
                  "Ensure the name used off-site matches the site exactly",
                  "Pursue diverse, independent mentions over time"),
    },
    "AG-03": {
        "rule_id": "independent-contradiction",
        "category": "corroboration",
        "default_severity": "high",
        "default_status": "confirmed",
        "default_type": "defect",
        "title": "Independent sources describe the brand differently from the site",
        "summary": "Reconcile the conflicting fact on-site and in Organization markup, and "
                   "correct the third-party sources that state the wrong version.",
        "steps": ("Identify the specific contradicted fact and its source",
                  "Correct the fact where it is wrong",
                  "State the accurate version explicitly on-site and in markup"),
    },
    # AG-04: the agent read an image listed in brief.ag04.images with its own
    # vision and found facts (prices, hours, items) that the page text does not
    # state. Same check as the script's facts-in-images, so the two merge.
    "AG-04": {
        "rule_id": "facts-in-images",
        "category": "ai_discoverability",
        "default_severity": "medium",
        "default_status": "confirmed",
        "default_type": "defect",
        "title": "Facts are carried inside images (read by the agent)",
        "summary": "Publish the facts shown in the image as HTML text on the same page.",
        "steps": ("Copy the prices, hours or items shown in the image into an HTML table or list",
                  "Give the image alt text that states what it shows",
                  "Keep the image as decoration or a download, not as the only source"),
    },
    # AG-05: a namesake search found other entities with the brand's name and
    # nothing on the site tells them apart (Appendix D: mistaken identity).
    "AG-05": {
        "rule_id": "kg-namesake-ambiguity",
        "category": "corroboration",
        "default_severity": "medium",
        "default_status": "confirmed",
        "default_type": "defect",
        "title": "Other entities share the brand's name and the site does not distinguish itself",
        "summary": "Declare the brand's own knowledge-graph entity and use its distinctive full name.",
        "steps": ("Add the brand's Wikidata item (create one if eligible) to Organization sameAs",
                  "Use the full distinctive name, with category or location, in titles and the About passage",
                  "Keep the name and profile links identical across official profiles"),
    },
    # AG-06: the agent searched the review/directory platforms the brand's
    # category uses and found no profile for the brand.
    "AG-06": {
        "rule_id": "review-platform-missing",
        "category": "off_site_presence",
        "default_severity": "low",
        "default_status": "confirmed",
        "default_type": "proactive_improvement",
        "title": "No profile on the review or directory platforms the category uses",
        "summary": "Claim or create the brand's profile on the platforms its category uses.",
        "steps": ("Pick the two or three platforms the category uses (for example G2 or Capterra for software, "
                  "Google Business Profile or Yelp for a local business)",
                  "Use the exact brand name and site URL there",
                  "Link the profiles from Organization sameAs"),
    },
}

_VALID_SEVERITY = {"critical", "high", "medium", "low"}
_VALID_STATUS = {"confirmed", "suspected", "insufficient_evidence"}


def _load_supplied(path):
    """Return the list of raw agent findings, or None when nothing was supplied.
    A malformed or unreadable file is treated as not_supplied rather than an error
    so a bad handoff never takes the audit down."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    items = data.get("findings", []) if isinstance(data, dict) else data
    return items if isinstance(items, list) else None


def _evidence_list(raw):
    """Accept either a plain string or a list of evidence objects, always returning
    the list-of-dicts evidence shape."""
    ev = raw.get("evidence")
    if isinstance(ev, str) and ev.strip():
        return [{"type": "agent_observation", "description": ev.strip()}]
    if isinstance(ev, list):
        cleaned = [e for e in ev if isinstance(e, dict)]
        if cleaned:
            return cleaned
    return [{"type": "agent_observation", "description": "Agent-supplied qualitative observation"}]


def _build_finding(raw):
    """Reconstruct one agent finding through make_finding so catalog
    enrichment and Invariant I-1 apply. Returns None when the entry cannot be
    mapped to a known AG check."""
    check = str(raw.get("check") or raw.get("check_id") or "").strip().upper()
    rule = _AG_RULES.get(check)
    if rule is None:
        return None

    status = str(raw.get("status") or rule["default_status"]).lower()
    if status not in _VALID_STATUS:
        status = rule["default_status"]
    severity = str(raw.get("severity") or rule["default_severity"]).lower()
    if severity not in _VALID_SEVERITY:
        severity = rule["default_severity"]
    finding_type = rule["default_type"]

    action = raw.get("suggested_action")
    action = action if isinstance(action, dict) else {}
    summary = str(action.get("summary") or rule["summary"])
    steps = action.get("steps")
    steps = list(steps) if isinstance(steps, (list, tuple)) and steps else list(rule["steps"])

    evidence = _evidence_list(raw)
    # Evidence may name the page or image it is about; those become the
    # finding's pages so it can merge with the script finding for the same pages.
    pages = [str(u) for u in (raw.get("affected_pages") or []) if isinstance(u, str)][:10]
    finding = make_finding(
        category=rule["category"],
        finding_type=finding_type,
        severity=severity,
        status=status,
        confidence=0.7 if status == "confirmed" else 0.55,
        title=str(raw.get("title") or rule["title"]),
        root_cause=evidence[0]["description"],
        evidence=evidence,
        affected_pages=pages or None,
        suggested_action={
            "summary": summary,
            "steps": steps,
            "priority": severity,
            "effort": str(action.get("effort") or "medium"),
            "expected_benefit": "Improves identity clarity and independent corroboration",
            "verification": "Re-run the qualitative corroboration stage after changes",
        },
        provenance={"skill": "entity-corroboration-agent",
                    "script": "ingest_agent_findings.py", "rule_id": rule["rule_id"]},
    )
    # make_finding already applies Invariant I-1; re-apply defensively so an
    # agent-authored insufficient_evidence entry is capped no matter how it was
    # constructed. This is the same rule (apply_invariant_i1), not a second one.
    return apply_invariant_i1(finding)


def load_agent_findings(path):
    """Ingest an agent findings file without a live snapshot (used by
    finalize_report.py after the agent stage). Returns (SkillResult, stage) where
    stage is "ingested", "empty" (valid file, nothing fired) or "not_supplied"."""
    supplied = _load_supplied(path)
    if supplied is None:
        return (insufficient_evidence_result(
            "entity-corroboration-agent",
            "Agent corroboration stage not supplied; About-concreteness and cross-web corroboration were "
            "not checked this audit (not checked, not \"no corroboration found\").",
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0}), "not_supplied")
    findings = [f for f in (_build_finding(raw) for raw in supplied if isinstance(raw, dict)) if f is not None]
    stage = "ingested" if findings else "empty"
    return (skill_result("entity-corroboration-agent", findings=findings,
                         metrics={"agent_stage": stage, "findings_ingested": len(findings),
                                  "findings_supplied": len(supplied)}), stage)


def ingest_agent_findings(artifacts, entity_identity, deadline, capabilities=None):
    """In-process ingest of the agent-executed corroboration stage.

    Returns a SkillResult. When no findings are supplied, returns an
    insufficient_evidence skip that is explicitly "not checked", never "not found".
    """
    if deadline is not None and deadline.expired():
        return insufficient_evidence_result(
            "entity-corroboration-agent",
            "Audit deadline reached before the agent corroboration stage was ingested.",
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0},
        )

    supplied = _load_supplied(os.environ.get(_FINDINGS_ENV))
    if supplied is None:
        # Graceful not_supplied skip. The qualitative stage is optional and
        # agent-driven; its absence says nothing about the site.
        return insufficient_evidence_result(
            "entity-corroboration-agent",
            "Agent corroboration stage not supplied (no AGENT_FINDINGS_PATH); the "
            "qualitative About-concreteness and cross-web corroboration checks were "
            "not run this audit (not checked, not \"no corroboration found\"). See "
            "skills/entity-corroboration-agent/SKILL.md.",
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0},
        )

    findings = []
    for raw in supplied:
        if not isinstance(raw, dict):
            continue
        built = _build_finding(raw)
        if built is not None:
            findings.append(built)

    return skill_result(
        "entity-corroboration-agent", findings=findings,
        metrics={"agent_stage": "ingested", "findings_ingested": len(findings),
                 "findings_supplied": len(supplied)},
        coverage={"pages_analyzed": len(artifacts.pages), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
