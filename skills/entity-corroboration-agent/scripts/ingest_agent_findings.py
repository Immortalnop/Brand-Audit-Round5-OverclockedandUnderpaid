"""ingest_agent_findings.py -- in-process bridge for the agent-executed stage.

The entity-corroboration-agent skill is the one qualitative stage in this
marketplace: the calling agent, not a deterministic script, judges About-page
concreteness (AG-01) and cross-web agreement or contradiction (AG-02 / AG-03)
using its own reading and web_search tools, per the handout's explicit allowance
to query public community platforms such as Reddit and Quora, and reads facts
drawn inside raster images with its own vision (AG-04), searches knowledge
graphs for entities that share the brand name (AG-05), and searches review and
directory platforms for the brand's profiles (AG-06).

Two handoff shapes are read:

  - The outcome envelope (schema_version 1.0, ROUND5_PLAN T4.1): one outcome per
    AG check (pass, finding, not_assessed or error), bound to one audit by
    audit_id and snapshot_sha256, with source references into the evidence
    packet that audit exported (common/agent_evidence.py). validate_envelope
    checks it against the report and the packet before anything is merged:
    known checks only, one outcome each, valid evidence IDs and URLs, the
    evidence each check needs, and a severity ceiling per check. Omitted checks
    become not_assessed, never passes.
  - The legacy findings array. It is still read, as legacy_partial: it never
    clears a missing-stage limitation, an entry without evidence is dropped
    rather than given a generic description, and no legacy entry earns more
    than medium severity.

Every ingested finding is rebuilt through common.models.make_finding, so the
catalog enrichment and Invariant I-1 capping that govern script findings govern
agent findings too. The agent never constructs the final finding object, and
nothing it quotes from a website can set a severity, a status or a destination.

Graceful skip: when no agent findings are supplied the stage records
not_supplied and returns insufficient_evidence. It never upgrades "the stage did
not run" into "no corroboration exists".
"""
import json
import os
from urllib.parse import urlsplit

from models import (skill_result, make_finding, insufficient_evidence_result,
                     apply_invariant_i1)
from check_catalog import get_entry
from url_safety import same_origin
from agent_evidence import AG_CHECKS, evidence_ids

# Environment variable naming the agent's findings file. Kept as an env var (not a
# fixed workdir path) so nothing about this stage assumes the donor's subprocess
# workdir convention; when it is unset, the stage simply skips.
_FINDINGS_ENV = "AGENT_FINDINGS_PATH"

# AG check IDs -> v6 catalog rule IDs, category, and the honest status/severity the
# agent stage is allowed to assert. The severity ceilings live in
# agent_evidence.AG_CHECKS.
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
        "title": "No independent mention of the brand was found in the searches run",
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
        "title": "An independent source describes the brand differently from the site",
        "summary": "Reconcile the conflicting fact: confirm which version is accurate, then correct "
                   "whichever source is wrong.",
        "steps": ("Confirm which version of the fact is accurate",
                  "Correct the source that is wrong: the site, its markup or the third-party page",
                  "Where the site is right, state the fact plainly on-site and in Organization markup"),
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
        "title": "No matching profile was found on the review platforms searched",
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
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
# Without the envelope's evidence contract no agent entry earns more than this.
_LEGACY_MAX_SEVERITY = "medium"

ENVELOPE_SCHEMA_VERSION = "1.0"
OUTCOMES = ("pass", "finding", "not_assessed", "error")
ASSESSED_OUTCOMES = ("pass", "finding")
_SOURCE_KINDS = {"inspected_page", "search_result", "search_snippet", "viewed_image", "knowledge_graph_page"}
_UNANSWERED = {"who", "offering", "category"}
_MAX_CHECK_ENTRIES = 20
_MAX_REFS = 20
_MAX_SOURCES = 10
_MAX_QUERIES = 12
_MAX_ENTITIES = 10

# Bounds on what one agent handoff can put into the report. The agent's text is
# kept as evidence, so it is capped like any other observation.
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_AGENT_FINDINGS = 50
_MAX_EVIDENCE_ITEMS = 10
_MAX_URLS = 20
_MAX_URL_CHARS = 2000
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
LEGACY_WARNING = (
    "Agent findings were supplied as a legacy findings array (legacy_partial): it carries no per-check "
    "outcomes or evidence contract, so checks it does not mention are not assessed, no missing-stage "
    "limitation is cleared and no agent finding exceeds medium severity. Supply an outcome envelope "
    "bound to the audit's evidence packet instead.")
ENVELOPE_LIVE_WARNING = (
    "An agent outcome envelope was supplied during the audit. An envelope is bound to a finished audit's "
    "report and evidence packet, so it can only be merged afterwards with run_audit.py --from-report; it "
    "was not read.")

LEGACY_NOT_ASSESSED = "Legacy findings array: a check it does not mention is not assessed, not passed."
OMITTED_NOT_ASSESSED = "Not included in the outcome envelope; an omitted check is not a pass."
NOT_SUPPLIED_REASON = "The agent stage was not supplied."


class AgentFindingsError(ValueError):
    """The agent findings file cannot be used: missing, too large, not JSON, or
    not a list of findings."""


class EnvelopeError(AgentFindingsError):
    """The outcome envelope fails validation; reasons lists every problem."""

    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


def read_agent_input(path):
    """The parsed JSON in the agent file at path. UTF-8 (with or without a byte
    order mark) and UTF-16, which PowerShell's > redirect writes, are both read.
    Raises AgentFindingsError with a plain-English reason when the file cannot
    be used."""
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
        return json.loads(text)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise AgentFindingsError(f"{path} is not valid JSON ({exc})") from exc


def is_envelope(data):
    """True when data is an outcome envelope rather than a legacy findings array."""
    return isinstance(data, dict) and "checks" in data and "schema_version" in data


def load_agent_input(path):
    """('envelope', dict) or ('legacy', list) for the agent file at path."""
    data = read_agent_input(path)
    if is_envelope(data):
        return "envelope", data
    items = data.get("findings") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise AgentFindingsError(f"{path} must hold an outcome envelope (schema_version and checks), a JSON "
                                 "array of findings, or an object with a \"findings\" array")
    return "legacy", items


def load_agent_findings(path):
    """The list of raw legacy agent findings in the file at path: a JSON array,
    or an object with a "findings" array. Raises AgentFindingsError with a
    plain-English reason when the file cannot be used, including when it holds
    an outcome envelope (merge that with run_audit.py --from-report)."""
    kind, data = load_agent_input(path)
    if kind == "envelope":
        raise AgentFindingsError(f"{path} holds an outcome envelope, which is merged into the finished "
                                 "report with --from-report, not read during an audit")
    return data


def _text(value, limit):
    """value as one line of at most limit characters, or '' when it is not text."""
    return " ".join(value.split())[:limit] if isinstance(value, str) else ""


def _is_url(value):
    if not isinstance(value, str) or len(value) > _MAX_URL_CHARS:
        return False
    parts = urlsplit(value.strip())
    return parts.scheme.lower() in ("http", "https") and bool(parts.netloc) and not any(c.isspace() for c in value.strip())


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
    writes can change how the report reads its evidence. An entry with no
    evidence gives an empty list: there is no generic fallback description."""
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
    return cleaned


def _cap(severity, ceiling):
    return ceiling if _SEVERITY_RANK[severity] > _SEVERITY_RANK[ceiling] else severity


def _make_agent_finding(rule, severity, status, confidence, title, root_cause, evidence, pages, summary=None,
                        steps=None, effort="medium", confidence_method=None):
    finding = make_finding(
        category=rule["category"],
        finding_type=rule["default_type"],
        severity=severity,
        status=status,
        confidence=confidence,
        title=title or rule["title"],
        root_cause=root_cause,
        evidence=evidence,
        affected_pages=pages or None,
        suggested_action={
            "summary": summary or rule["summary"],
            "steps": list(steps or rule["steps"]),
            "priority": severity,
            "effort": effort,
            "expected_benefit": rule.get("expected_benefit",
                                         "Improves identity clarity and independent corroboration"),
            "verification": "Re-run the agent stage against the evidence packet of a new audit",
        },
        provenance={"skill": "entity-corroboration-agent",
                    "script": "ingest_agent_findings.py", "rule_id": rule["rule_id"],
                    **({"confidence_method": confidence_method} if confidence_method else {})},
    )
    # make_finding falls back to the evidence URLs when no page is named; those
    # may be third-party profiles, so the pages are set from affected_pages alone.
    finding["affected_pages"] = sorted(set(pages))
    # make_finding already applies Invariant I-1; re-apply defensively so an
    # agent-authored insufficient_evidence entry is capped no matter how it was
    # constructed. This is the same rule (apply_invariant_i1), not a second one.
    return apply_invariant_i1(finding)


# ---------------------------------------------------------------- legacy array

def _build_finding(raw, origin=None):
    """Reconstruct one legacy agent finding through v6's make_finding so catalog
    enrichment and Invariant I-1 apply. Returns None when the entry cannot be
    mapped to a known AG check or carries no evidence. affected_pages keeps only
    URLs on the audited origin when it is known: they name pages of the site,
    never a third-party profile (those belong in evidence). Severity is capped
    at the check's ceiling and at medium, and a legacy AG-03 is only suspected:
    a legacy entry has no source contract."""
    check = str(raw.get("check") or raw.get("check_id") or "").strip().upper()
    rule = _AG_RULES.get(check)
    if rule is None:
        return None
    evidence = _evidence_list(raw)
    if not evidence:
        return None

    status = str(raw.get("status") or rule["default_status"]).lower()
    if status not in _VALID_STATUS:
        status = rule["default_status"]
    if check == "AG-03" and status == "confirmed":
        status = "suspected"
    severity = str(raw.get("severity") or rule["default_severity"]).lower()
    if severity not in _VALID_SEVERITY:
        severity = rule["default_severity"]
    severity = _cap(_cap(severity, AG_CHECKS[check]["max_severity"]), _LEGACY_MAX_SEVERITY)

    action = raw.get("suggested_action")
    action = action if isinstance(action, dict) else {}
    summary = _text(action.get("summary"), _MAX_TEXT) or rule["summary"]
    steps = [_text(s, _MAX_TEXT) for s in action.get("steps") or ()][:_MAX_STEPS] \
        if isinstance(action.get("steps"), (list, tuple)) else []
    steps = [s for s in steps if s] or list(rule["steps"])
    effort = str(action.get("effort") or "medium").lower()
    effort = effort if effort in _VALID_EFFORT else "medium"

    pages = _urls(raw.get("affected_pages"))
    if origin:
        pages = [u for u in pages if same_origin(u, origin)]
    finding = _make_agent_finding(
        rule, severity, status, 0.7 if status == "confirmed" else 0.55,
        _text(raw.get("title"), _MAX_TITLE) or rule["title"],
        get_entry(rule["rule_id"])["mechanism"] if rule.get("root_cause_from_catalog") else evidence[0]["description"],
        evidence, pages, summary, steps, effort,
        confidence_method="legacy: fixed by status, no evidence contract")
    finding["provenance"]["agent_contract"] = "legacy"
    return finding


def build_agent_findings(items, origin=None):
    """Findings for the raw legacy entries in items (at most MAX_AGENT_FINDINGS
    are read). Entries that are not objects, name no known AG check or carry no
    evidence are skipped."""
    findings = []
    for raw in list(items or ())[:MAX_AGENT_FINDINGS]:
        if not isinstance(raw, dict):
            continue
        built = _build_finding(raw, origin)
        if built is not None:
            findings.append(built)
    return findings


def legacy_checks(findings):
    """Per-check outcome records for a legacy array: a check with a finding is
    marked as a legacy finding, every other check is not assessed."""
    by_rule = {rule["rule_id"]: check for check, rule in _AG_RULES.items()}
    found = {by_rule.get((f.get("provenance") or {}).get("rule_id")) for f in findings}
    return {check: ({"outcome": "finding", "contract": "legacy",
                     "reason": "Legacy finding without the evidence contract; not counted as an assessment."}
                    if check in found else {"outcome": "not_assessed", "reason": LEGACY_NOT_ASSESSED})
            for check in _AG_RULES}


def stage_record(submission_status, checks, **extra):
    """The coverage.agent_stage block: submission_status ('not_supplied',
    'legacy' or 'envelope') says what was received, assessment_status
    ('not_run', 'partial' or 'complete') how many checks it actually assessed,
    so a received envelope full of explicit skips never reads as complete."""
    assessed = sorted(c for c, r in checks.items()
                      if r.get("outcome") in ASSESSED_OUTCOMES and r.get("contract") != "legacy")
    legacy = sorted(c for c, r in checks.items() if r.get("contract") == "legacy")
    errors = sorted(c for c, r in checks.items() if r.get("outcome") == "error")
    if len(assessed) == len(_AG_RULES):
        status = "complete"
    elif assessed or legacy:
        status = "partial"
    else:
        status = "not_run"
    record = {"submission_status": submission_status, "assessment_status": status,
              "checks_assessed": assessed, "checks_not_assessed": sorted(set(checks) - set(assessed)),
              "assessed_count": len(assessed), "not_assessed_count": len(checks) - len(assessed),
              "checks_with_errors": errors, "checks": checks}
    record.update(extra)
    return record


def not_supplied_record():
    return stage_record("not_supplied", {c: {"outcome": "not_assessed", "reason": NOT_SUPPLIED_REASON}
                                         for c in _AG_RULES})


# ---------------------------------------------------------------- outcome envelope

def _norm(text):
    return " ".join((text or "").split()).lower()


def _refs(raw, ids, errors):
    refs = raw.get("source_refs", [])
    if refs is None:
        refs = []
    if not isinstance(refs, list):
        errors.append("source_refs must be a list of evidence IDs from the packet")
        return []
    out = []
    for ref in refs[:_MAX_REFS]:
        if not isinstance(ref, str) or ref not in ids:
            errors.append(f"unknown evidence reference {str(ref)[:40]!r} (not in the evidence packet)")
        elif ref not in out:
            out.append(ref)
    return out


def _sources(raw, errors):
    value = raw.get("sources", [])
    if value is None:
        value = []
    if not isinstance(value, list):
        errors.append("sources must be a list")
        return []
    out = []
    for item in value[:_MAX_SOURCES]:
        if not isinstance(item, dict):
            errors.append("each source must be an object")
            continue
        url = item.get("url")
        kind = item.get("kind")
        if not _is_url(url):
            errors.append(f"invalid source URL {str(url)[:80]!r}")
            continue
        if kind not in _SOURCE_KINDS:
            errors.append(f"source kind {str(kind)[:40]!r} is not one of {sorted(_SOURCE_KINDS)}")
            continue
        out.append({"url": url.strip(), "kind": kind, "quote": _text(item.get("quote"), _MAX_TEXT),
                    "title": _text(item.get("title"), _MAX_TITLE),
                    "accessed_at": _text(item.get("accessed_at"), 40)})
    return out


def _queries(raw, errors):
    value = raw.get("queries", [])
    if value is None:
        value = []
    if not isinstance(value, list):
        errors.append("queries must be a list")
        return []
    out = []
    for item in value[:_MAX_QUERIES]:
        if not isinstance(item, dict) or not _text(item.get("query"), 300):
            errors.append("each query needs its query text")
            continue
        count = item.get("result_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            errors.append(f"query {_text(item.get('query'), 80)!r} needs a result_count (0 or more)")
            continue
        out.append({"query": _text(item["query"], 300), "platform": _text(item.get("platform"), 80),
                    "result_count": count, "executed_at": _text(item.get("executed_at"), 40)})
    return out


def _domain(url):
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _validate_check(check, outcome, raw, ids, have, origin):
    """(record, finding_or_None, errors) for one envelope entry."""
    errors = []
    spec = AG_CHECKS[check]
    rule = _AG_RULES[check]
    reason = _text(raw.get("reason"), _MAX_TEXT)
    refs = _refs(raw, ids, errors)
    sources = _sources(raw, errors)
    queries = _queries(raw, errors)
    observation = raw.get("observation") if isinstance(raw.get("observation"), dict) else {}
    record = {"outcome": outcome, "reason": reason}
    if refs:
        record["source_refs"] = refs
    if outcome in ("not_assessed", "error"):
        record["reason"] = reason or ("No reason given." if outcome == "not_assessed" else "The agent reported an error.")
        return record, None, errors

    capability = spec["capability"]
    if not have.get(capability):
        errors.append(f"a {outcome} outcome needs the {capability} capability, which the envelope says "
                      "was not available")
    if not reason:
        errors.append(f"a {outcome} outcome needs a reason")
    page_refs = [r for r in refs if ids[r]["ref_kind"] == "page"]
    image_refs = [r for r in refs if ids[r]["ref_kind"] == "image"]
    if queries:
        record["queries"] = queries

    if outcome == "pass":
        if check == "AG-01" and not page_refs:
            errors.append("a pass needs the packet page it read (an E... reference)")
        if capability == "search" and not queries:
            errors.append("a pass needs the searches that ran (queries)")
        if check == "AG-04" and not image_refs:
            errors.append("a pass needs the image candidates viewed (I... references)")
        return record, None, errors

    # outcome == "finding": the evidence each check needs (agent_evidence.AG_CHECKS).
    evidence, pages, root_cause, title = [], [], None, None
    status, confidence, method = rule["default_status"], 0.6, None
    ceiling = spec["max_severity"]
    for ref in refs:
        item = ids[ref]
        if item["ref_kind"] == "page":
            evidence.append({"type": "packet_passage", "evidence_id": ref,
                             "description": f"{item.get('title') or item.get('final_url')} ({item.get('source_kind')})",
                             "urls": [item.get("final_url") or item.get("requested_url")]})
        elif item["ref_kind"] == "claim":
            evidence.append({"type": "packet_claim", "evidence_id": ref,
                             "description": f"Site claim {item.get('predicate')}: {item.get('value')}",
                             "urls": [item.get("source_url")] if item.get("source_url") else []})
        else:
            evidence.append({"type": "packet_image", "evidence_id": ref,
                             "description": f"Image candidate {item.get('url')}", "urls": [item.get("url")]})

    if check == "AG-01":
        unanswered = observation.get("unanswered")
        passage = _text(observation.get("passage"), _MAX_TEXT)
        if not page_refs:
            errors.append("an AG-01 finding needs the packet page it read (an E... reference)")
        if not isinstance(unanswered, list) or not unanswered or not set(unanswered) <= _UNANSWERED:
            errors.append("an AG-01 finding needs observation.unanswered: which of who, offering and category "
                          "the passage leaves unanswered")
            unanswered = []
        if not passage:
            errors.append("an AG-01 finding needs observation.passage, the text it judged")
        elif page_refs and not any(_norm(passage) in _norm(ids[r].get("text")) for r in page_refs):
            errors.append("observation.passage is not in the referenced packet page")
        if unanswered and passage:
            root_cause = (f"The passage read does not say {', '.join(sorted(unanswered))}: \"{passage[:300]}\"")
            evidence.insert(0, {"type": "agent_reading", "description": root_cause})
        status, confidence, method = "suspected", 0.65, "heuristic: passage verified in the packet"
    elif check == "AG-02":
        identity = _text(observation.get("identity"), 300)
        if not queries:
            errors.append("an AG-02 finding needs the queries executed, each with its result count")
        if not identity:
            errors.append("an AG-02 finding needs observation.identity, the name and context searched")
        root_cause = (f"{len(queries)} search(es) for {identity or 'the brand'} found no independent "
                      "mention. This covers those searches only, not the whole web.")
        confidence = round(min(0.65, 0.45 + 0.05 * len(queries)), 2)
        method = "heuristic: count of executed queries"
    elif check == "AG-03":
        claim = _text(observation.get("site_claim"), _MAX_TEXT)
        same_entity = _text(observation.get("same_entity"), _MAX_TEXT)
        context = _text(observation.get("context"), _MAX_TEXT)
        material = observation.get("material")
        inspected = [s for s in sources if s["kind"] == "inspected_page" and s["quote"]]
        if not claim:
            errors.append("an AG-03 finding needs observation.site_claim, the exact claim on the site")
        if not refs:
            errors.append("an AG-03 finding needs the packet page or claim the site claim comes from")
        if not inspected:
            errors.append("an AG-03 finding needs an inspected conflicting page with its URL and quote; "
                          "search snippets and unopened results are not enough")
        if not same_entity:
            errors.append("an AG-03 finding needs observation.same_entity: why the source is about this brand")
        if not context:
            errors.append("an AG-03 finding needs observation.context: the date or context of the conflict")
        if not isinstance(material, bool):
            errors.append("an AG-03 finding needs observation.material (true or false)")
        if not material:
            ceiling = "medium"
        domains = {_domain(s["url"]) for s in inspected}
        status = "confirmed" if len(domains) >= 2 else "suspected"
        confidence = 0.75 if len(domains) >= 2 else 0.6
        method = "heuristic: distinct inspected source domains"
        if inspected and claim:
            root_cause = (f"The site states \"{claim[:300]}\"; {inspected[0]['url']} states "
                          f"\"{inspected[0]['quote'][:300]}\". {same_entity[:200]} Which source is right is "
                          "not established by the conflict itself.")
    elif check == "AG-04":
        transcription = _text(observation.get("transcription"), _MAX_TEXT)
        comparison = _text(observation.get("text_comparison"), _MAX_TEXT)
        if not image_refs:
            errors.append("an AG-04 finding needs the image candidate viewed (an I... reference)")
        if not transcription:
            errors.append("an AG-04 finding needs observation.transcription, the fact read from the image")
        if not comparison:
            errors.append("an AG-04 finding needs observation.text_comparison: why the page text does not "
                          "state the fact")
        pages = sorted({u for r in image_refs for u in ids[r].get("pages") or ()})
        page_records = [i for i in ids.values() if i["ref_kind"] == "page"
                        and (i.get("requested_url") in pages or i.get("final_url") in pages)]
        complete = bool(page_records) and all(p.get("observation_status") == "complete"
                                              and not p.get("text_truncated") for p in page_records)
        # Incomplete page text cannot prove a fact appears only in the image.
        status = "confirmed" if complete else "suspected"
        confidence = 0.7 if complete else 0.55
        method = "heuristic: viewed image, page text read in full or not"
        if transcription:
            evidence.insert(0, {"type": "agent_vision",
                                "description": f"{transcription} ({comparison or 'not compared'})",
                                "urls": [ids[r]["url"] for r in image_refs]})
    elif check == "AG-05":
        entities = observation.get("competing_entities")
        kept = []
        for entity in (entities if isinstance(entities, list) else [])[:_MAX_ENTITIES]:
            if not isinstance(entity, dict):
                continue
            name, fact, url = (_text(entity.get("name"), 200), _text(entity.get("distinguishing"), 500),
                               entity.get("url"))
            if not name or not fact or not _is_url(url):
                errors.append("each competing entity needs a name, a URL and the fact that distinguishes it")
                continue
            kept.append({"type": "namesake_entity", "description": f"{name}: {fact}", "urls": [url.strip()]})
        if not kept and not any("competing entity" in e for e in errors):
            errors.append("an AG-05 finding needs observation.competing_entities")
        evidence.extend(kept)
        confidence, method = 0.6, "heuristic: observed namesake entities"
    elif check == "AG-06":
        applicability = _text(observation.get("business_applicability"), _MAX_TEXT)
        missing = [m for m in (observation.get("platforms_missing") or []) if isinstance(m, str) and m.strip()] \
            if isinstance(observation.get("platforms_missing"), list) else []
        if not queries or any(not q["platform"] for q in queries):
            errors.append("an AG-06 finding needs the platform queries executed, each naming its platform")
        if not applicability:
            errors.append("an AG-06 finding needs observation.business_applicability")
        if not missing:
            errors.append("an AG-06 finding needs observation.platforms_missing")
        evidence.insert(0, {"type": "agent_search",
                            "description": f"No matching profile on {', '.join(m[:60] for m in missing[:8])} in "
                                           f"the searches run. {applicability[:300]}"})
        confidence = round(min(0.65, 0.45 + 0.05 * len(queries)), 2)
        method = "heuristic: count of executed platform queries"

    for query in queries:
        where = f" on {query['platform']}" if query["platform"] else ""
        evidence.append({"type": "search_query",
                         "description": f"Query \"{query['query']}\"{where}: {query['result_count']} result(s)"
                                        + (f" ({query['executed_at']})" if query["executed_at"] else "")})
    for source in sources:
        evidence.append({"type": source["kind"],
                         "description": source["quote"] or source["title"] or "Source opened by the agent",
                         "urls": [source["url"]]})

    requested = raw.get("severity")
    severity = rule["default_severity"]
    if isinstance(requested, str) and requested.lower() in _VALID_SEVERITY:
        severity = requested.lower()
    elif requested is not None:
        record["severity_note"] = f"severity {str(requested)[:40]!r} is not a known severity; the default was used"
    capped = _cap(severity, ceiling)
    if capped != severity:
        record["severity_capped"] = (f"requested {severity}; {check} is capped at {ceiling} in this release")
        severity = capped
    if isinstance(raw.get("status"), str) and raw["status"].lower() == "suspected":
        status = "suspected"

    if errors:
        return record, None, errors
    if not root_cause:
        root_cause = get_entry(rule["rule_id"])["mechanism"]
    if origin:
        pages = [u for u in pages if same_origin(u, origin)]
    affected = _urls(raw.get("affected_pages"))
    pages = sorted(set(pages) | {u for u in affected if not origin or same_origin(u, origin)})
    finding = _make_agent_finding(rule, severity, status, confidence, title, root_cause,
                                  evidence[:_MAX_EVIDENCE_ITEMS + _MAX_SOURCES + _MAX_QUERIES], pages,
                                  confidence_method=method)
    finding["provenance"]["agent_contract"] = "envelope"
    finding["provenance"]["agent_check"] = check
    finding["provenance"]["source_refs"] = refs
    record.update(severity=severity, status=status)
    return record, finding, errors


def validate_envelope(envelope, report, packet):
    """{'checks': {AG: record}, 'findings': [...], 'capabilities': {...}} for an
    outcome envelope bound to report and packet. Raises EnvelopeError listing
    every problem when anything fails: a mismatched audit or snapshot, an
    unknown or repeated check, an unknown outcome, an evidence ID the packet does
    not hold, an invalid URL, or a pass or finding without the evidence its
    check needs. A severity above a check's ceiling is capped, with the reason
    recorded. No URL is fetched. Omitted checks become not_assessed."""
    if not isinstance(envelope, dict):
        raise EnvelopeError(["the outcome envelope is not a JSON object"])
    errors = []
    if envelope.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {ENVELOPE_SCHEMA_VERSION!r}")
    audit_id, snapshot = report.get("audit_id"), report.get("snapshot_sha256")
    if not audit_id or not snapshot:
        errors.append("the report has no audit_id or snapshot_sha256 (it predates audit binding); run the "
                      "audit again with --evidence-out")
    else:
        if envelope.get("audit_id") != audit_id:
            errors.append("audit_id does not match the report")
        if envelope.get("snapshot_sha256") != snapshot:
            errors.append("snapshot_sha256 does not match the report")
    if not isinstance(packet, dict):
        errors.append("no evidence packet was given; pass the packet the audit wrote with --evidence")
        ids = {}
    else:
        if packet.get("audit_id") != audit_id or packet.get("snapshot_sha256") != snapshot:
            errors.append("the evidence packet belongs to a different audit or snapshot")
        ids = evidence_ids(packet)
    caps = envelope.get("capabilities") if isinstance(envelope.get("capabilities"), dict) else {}
    have = {"local_reading": caps.get("local_reading", True) is not False,
            "search": caps.get("search") is True, "vision": caps.get("vision") is True}
    checks = envelope.get("checks")
    if not isinstance(checks, list):
        raise EnvelopeError(errors + ["checks must be a list"])
    if len(checks) > _MAX_CHECK_ENTRIES:
        errors.append(f"checks holds {len(checks)} entries; at most {_MAX_CHECK_ENTRIES} are read")
        checks = checks[:_MAX_CHECK_ENTRIES]
    origin = (report.get("coverage") or {}).get("audited_url") or report.get("site")
    records, findings = {}, []
    for index, raw in enumerate(checks):
        where = f"checks[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{where} is not an object")
            continue
        check = str(raw.get("check") or "").strip().upper()
        if check not in _AG_RULES:
            errors.append(f"{where}: unknown check {str(raw.get('check'))[:40]!r}")
            continue
        if check in records:
            errors.append(f"{check} appears more than once; give exactly one outcome per check")
            continue
        outcome = raw.get("outcome")
        if outcome not in OUTCOMES:
            errors.append(f"{check}: outcome {str(outcome)[:40]!r} is not one of {list(OUTCOMES)}")
            continue
        record, finding, problems = _validate_check(check, outcome, raw, ids, have, origin)
        errors.extend(f"{check}: {p}" for p in problems)
        records[check] = record
        if finding is not None:
            findings.append(finding)
    if errors:
        raise EnvelopeError(errors)
    for check in _AG_RULES:
        records.setdefault(check, {"outcome": "not_assessed", "reason": OMITTED_NOT_ASSESSED})
    return {"checks": {c: records[c] for c in _AG_RULES}, "findings": findings, "capabilities": have}


# ---------------------------------------------------------------- live audit

def _load_supplied(path):
    """(kind, data) for the supplied file, or (None, None) when nothing usable
    was supplied. A malformed or unreadable file is treated as not supplied
    rather than an error so a bad handoff never takes the audit down."""
    if not path or not os.path.isfile(path):
        return None, None
    try:
        return load_agent_input(path)
    except AgentFindingsError:
        return None, None


def ingest_agent_findings(artifacts, entity_identity, deadline, capabilities=None):
    """In-process ingest of the agent-executed corroboration stage during a live
    audit. Only the legacy array can be read here (legacy_partial): an outcome
    envelope is bound to a finished report and is merged with --from-report.

    Returns a SkillResult. When no findings are supplied, returns an
    insufficient_evidence skip that is explicitly "not checked", never "not found".
    """
    if deadline is not None and deadline.expired():
        return insufficient_evidence_result(
            "entity-corroboration-agent",
            "Audit deadline reached before the agent corroboration stage was ingested.",
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0, "stage_record": not_supplied_record()},
        )

    kind, supplied = _load_supplied(os.environ.get(_FINDINGS_ENV))
    if kind == "envelope":
        return insufficient_evidence_result(
            "entity-corroboration-agent", ENVELOPE_LIVE_WARNING,
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0, "stage_record": not_supplied_record()},
        )
    if supplied is None:
        # Graceful not_supplied skip. The qualitative stage is optional and
        # agent-driven; its absence says nothing about the site.
        return insufficient_evidence_result(
            "entity-corroboration-agent", NOT_SUPPLIED_WARNING,
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0, "stage_record": not_supplied_record()},
        )

    findings = build_agent_findings(supplied, getattr(artifacts, "normalized_origin", None))
    result = skill_result(
        "entity-corroboration-agent", findings=findings,
        metrics={"agent_stage": "legacy_partial", "findings_ingested": len(findings),
                 "findings_supplied": len(supplied),
                 "stage_record": stage_record("legacy", legacy_checks(findings))},
        coverage={"pages_analyzed": len(artifacts.pages), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
    result.setdefault("warnings", []).append(LEGACY_WARNING)
    return result

