"""ingest_agent_findings.py -- in-process bridge for the agent-executed stage.

The entity-corroboration-agent skill is the one qualitative stage in this
marketplace: the calling agent, not a deterministic script, judges About-page
concreteness (AG-01) and cross-web agreement or contradiction (AG-02 / AG-03)
using its own reading and web_search tools, per the handout's explicit allowance
to query public community platforms such as Reddit and Quora, and reads facts
drawn inside raster images with its own vision (AG-04), searches knowledge
graphs for entities that share the brand name (AG-05), and searches review and
directory platforms for the brand's profiles (AG-06). That judgment is
handed back as a small JSON array; this module ingests it in-process and returns
a SkillResult in exactly the same shape as every other v6 specialist.

Re-plumbed for v6 (Step 2.0): the donor ran this as a subprocess with a workdir
JSON handoff. Here there is no subprocess and no second orchestration model. The
orchestrator calls ingest_agent_findings() as an ordinary in-process function on
the shared immutable AuditArtifacts snapshot, and every ingested finding is
reconstructed through common.models.make_finding, so the catalog enrichment and
Invariant I-1 capping that govern script findings govern agent findings too. The
agent never constructs the final finding object; it supplies only what it
observed.

Graceful skip (Step 2.5 requirement): when no agent findings are supplied -- the
common case in an evaluation harness that has not run the qualitative stage --
the stage records not_supplied and returns insufficient_evidence. It never
upgrades "the stage did not run" into "no corroboration exists"; that asymmetry
is the single most common way an audit manufactures a false negative.
"""
import json
import os

from models import (skill_result, make_finding, insufficient_evidence_result,
                     apply_invariant_i1)
from check_catalog import get_entry
from url_safety import same_origin

# Environment variable naming the agent's findings file. Kept as an env var (not a
# fixed workdir path) so nothing about this stage assumes the donor's subprocess
# workdir convention; when it is unset, the stage simply skips.
_FINDINGS_ENV = "AGENT_FINDINGS_PATH"

# AG check IDs -> v6 catalog rule IDs, category, and the honest status/severity the
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
    # AG-04 is the vision half of the deterministic facts-in-images check: scripts
    # can read SVG text but never raster pixels, so the calling agent looks at the
    # images and reports facts it saw that the page text does not state. It shares
    # the facts-in-images rule and root cause, so merge_findings folds an AG-04
    # finding into the script finding for the same pages.
    "AG-04": {
        "rule_id": "facts-in-images",
        "category": "ai_discoverability",
        "default_severity": "medium",
        "default_status": "confirmed",
        "default_type": "defect",
        "root_cause_from_catalog": True,
        "title": "Facts are drawn inside images instead of stated in text",
        "summary": "State the facts shown in these images as real text on the page",
        "steps": ("Write the prices, hours or specifications shown in each listed image as HTML "
                  "text near the image",
                  "Give each image alt text that says what it shows",
                  "Where the facts are structured, also state them in JSON-LD"),
        "expected_benefit": "Crawlers and assistants that read text can quote these facts",
    },
    # AG-05 is the search half of the knowledge-graph check. robots.txt for
    # wikidata.org and wikipedia.org disallows their search APIs, so the scripts
    # only verify an entity the site already declares; the agent looks the brand
    # name up with its own web search and reports same-named entities.
    "AG-05": {
        "rule_id": "kg-namesake-ambiguity",
        "category": "ai_discoverability",
        "default_severity": "medium",
        "default_status": "confirmed",
        "default_type": "proactive_improvement",
        "root_cause_from_catalog": True,
        "title": "Other knowledge-graph entities share the brand name",
        "summary": "Declare the brand's own knowledge-graph entity and state what sets it apart",
        "steps": ("Add the brand's Wikidata item to Organization sameAs, or create one if the "
                  "organization meets Wikidata's notability policy",
                  "State distinguishing facts on the site: category, location and founding year",
                  "Use the same name and description in markup and on the About page"),
        "expected_benefit": "Assistants stop merging facts about same-named entities into the brand",
    },
    # AG-06 is the search half of the review-platform check. Review and directory
    # sites (Trustpilot, G2, Capterra, Google Business Profile, Yelp) block
    # automated clients or forbid them in robots.txt, so the scripts only see the
    # profiles the site links; the agent searches those platforms, plus Reddit and
    # Quora, by name with its own tools and reports where the brand has no profile.
    "AG-06": {
        "rule_id": "review-platform-missing",
        "category": "off_site_presence",
        "default_severity": "low",
        "default_status": "confirmed",
        "default_type": "proactive_improvement",
        "root_cause_from_catalog": True,
        "title": "The brand has no profile on the review platforms that fit its business",
        "summary": "Claim and link review profiles on the platforms that fit the business",
        "steps": ("Claim or create profiles on the review and directory platforms the agent found missing",
                  "Link them from the site and list them in Organization sameAs",
                  "Ask real customers for reviews and answer them publicly"),
        "expected_benefit": "Independent ratings and reviews corroborate the brand in assistant answers",
    },
}

_VALID_SEVERITY = {"critical", "high", "medium", "low"}
_VALID_STATUS = {"confirmed", "suspected", "insufficient_evidence"}
_VALID_EFFORT = {"low", "medium", "high"}

# Bounds on what one agent handoff can put into the report. The agent's text is
# kept as evidence, so it is capped like any other observation.
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_AGENT_FINDINGS = 50
_MAX_EVIDENCE_ITEMS = 10
_MAX_URLS = 20
_MAX_TEXT = 2000
_MAX_TITLE = 300
_MAX_STEPS = 8

# Warning of the graceful skip; run_audit.py --from-report removes it once the
# stage has been merged into a saved report.
NOT_SUPPLIED_WARNING = (
    "Agent corroboration stage not supplied (no AGENT_FINDINGS_PATH); the "
    "qualitative About-concreteness and cross-web corroboration checks were "
    "not run this audit (not checked, not \"no corroboration found\"). See "
    "skills/entity-corroboration-agent/SKILL.md.")


class AgentFindingsError(ValueError):
    """The agent findings file cannot be used: missing, too large, not JSON, or
    not a list of findings."""


def load_agent_findings(path):
    """The list of raw agent findings in the file at path: a JSON array, or an
    object with a "findings" array. UTF-8 (with or without a byte order mark)
    and UTF-16, which PowerShell's > redirect writes, are both read. Raises
    AgentFindingsError with a plain-English reason when the file cannot be used."""
    if not path or not os.path.isfile(path):
        raise AgentFindingsError(f"no such file: {path}")
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            raise AgentFindingsError(f"{path} is larger than {MAX_FILE_BYTES // (1024 * 1024)} MB")
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise AgentFindingsError(f"cannot read {path}: {exc}") from exc
    try:
        text = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig")
        data = json.loads(text)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise AgentFindingsError(f"{path} is not valid JSON ({exc})") from exc
    items = data.get("findings") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise AgentFindingsError(f"{path} must hold a JSON array of findings, or an object with a \"findings\" array")
    return items


def _load_supplied(path):
    """Return the list of raw agent findings, or None when nothing was supplied.
    A malformed or unreadable file is treated as not_supplied rather than an error
    so a bad handoff never takes the audit down."""
    if not path or not os.path.isfile(path):
        return None
    try:
        return load_agent_findings(path)
    except AgentFindingsError:
        return None


def _text(value, limit):
    """value as one line of at most limit characters, or '' when it is not text."""
    return " ".join(value.split())[:limit] if isinstance(value, str) else ""


def _urls(value):
    """The http(s) URLs in value (a list), at most _MAX_URLS of them."""
    if not isinstance(value, (list, tuple)):
        return []
    return [u.strip()[:_MAX_TEXT] for u in value
            if isinstance(u, str) and u.strip().lower().startswith(("http://", "https://"))][:_MAX_URLS]


def _evidence_list(raw):
    """Accept either a plain string (donor shape) or a list of evidence objects,
    always returning the v6 list-of-dicts evidence shape. Each object keeps only
    a text type, a description and a list of http(s) URLs, so nothing the agent
    writes can change how the report reads its evidence."""
    ev = raw.get("evidence")
    if isinstance(ev, str) and ev.strip():
        return [{"type": "agent_observation", "description": _text(ev, _MAX_TEXT)}]
    cleaned = []
    if isinstance(ev, list):
        for e in ev[:_MAX_EVIDENCE_ITEMS]:
            if not isinstance(e, dict):
                continue
            description = next((_text(e.get(k), _MAX_TEXT) for k in ("description", "snippet", "text")
                                if _text(e.get(k), _MAX_TEXT)), "")
            urls = _urls(e.get("urls"))
            if not description and not urls:
                continue
            item = {"type": _text(e.get("type"), 60) or "agent_observation",
                    "description": description or "Agent-supplied observation"}
            if urls:
                item["urls"] = urls
            cleaned.append(item)
    return cleaned or [{"type": "agent_observation", "description": "Agent-supplied qualitative observation"}]


def _build_finding(raw, origin=None):
    """Reconstruct one agent finding through v6's make_finding so catalog
    enrichment and Invariant I-1 apply. Returns None when the entry cannot be
    mapped to a known AG check. affected_pages keeps only URLs on the audited
    origin when it is known: they name pages of the site, never a third-party
    profile (those belong in evidence)."""
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
    summary = _text(action.get("summary"), _MAX_TEXT) or rule["summary"]
    steps = [_text(s, _MAX_TEXT) for s in action.get("steps") or ()][:_MAX_STEPS] \
        if isinstance(action.get("steps"), (list, tuple)) else []
    steps = [s for s in steps if s] or list(rule["steps"])
    effort = str(action.get("effort") or "medium").lower()
    effort = effort if effort in _VALID_EFFORT else "medium"

    evidence = _evidence_list(raw)
    pages = _urls(raw.get("affected_pages"))
    if origin:
        pages = [u for u in pages if same_origin(u, origin)]
    finding = make_finding(
        category=rule["category"],
        finding_type=finding_type,
        severity=severity,
        status=status,
        confidence=0.7 if status == "confirmed" else 0.55,
        title=_text(raw.get("title"), _MAX_TITLE) or rule["title"],
        root_cause=(get_entry(rule["rule_id"])["mechanism"] if rule.get("root_cause_from_catalog")
                    else evidence[0]["description"]),
        evidence=evidence,
        affected_pages=pages or None,
        suggested_action={
            "summary": summary,
            "steps": steps,
            "priority": severity,
            "effort": effort,
            "expected_benefit": rule.get("expected_benefit",
                                         "Improves identity clarity and independent corroboration"),
            "verification": "Re-run the qualitative agent stage after changes",
        },
        provenance={"skill": "entity-corroboration-agent",
                    "script": "ingest_agent_findings.py", "rule_id": rule["rule_id"]},
    )
    # make_finding falls back to the evidence URLs when no page is named; those
    # may be third-party profiles, so the pages are set from affected_pages alone.
    finding["affected_pages"] = sorted(set(pages))
    # make_finding already applies Invariant I-1; re-apply defensively so an
    # agent-authored insufficient_evidence entry is capped no matter how it was
    # constructed. This is the same rule (apply_invariant_i1), not a second one.
    return apply_invariant_i1(finding)


def build_agent_findings(items, origin=None):
    """Findings for the raw entries in items (at most MAX_AGENT_FINDINGS are
    read). Entries that are not objects or name no known AG check are skipped."""
    findings = []
    for raw in list(items or ())[:MAX_AGENT_FINDINGS]:
        if not isinstance(raw, dict):
            continue
        built = _build_finding(raw, origin)
        if built is not None:
            findings.append(built)
    return findings


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
            "entity-corroboration-agent", NOT_SUPPLIED_WARNING,
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0},
        )

    findings = build_agent_findings(supplied, getattr(artifacts, "normalized_origin", None))

    return skill_result(
        "entity-corroboration-agent", findings=findings,
        metrics={"agent_stage": "ingested", "findings_ingested": len(findings),
                 "findings_supplied": len(supplied)},
        coverage={"pages_analyzed": len(artifacts.pages), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
