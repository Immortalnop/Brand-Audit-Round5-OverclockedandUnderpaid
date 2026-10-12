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

The agent is a cooperating author, not a trusted one. Four rules make an
agent-supplied claim no stronger than the evidence that came with it:

  bounded input      the file is read under MAX_FINDINGS_BYTES and sanitized;
                     over-long text, non-http URLs and junk keys are dropped,
                     and a malformed handoff is a skip, never an exception.
  audit binding      an envelope naming a different site than the audit under
                     way is refused outright (a findings file from another run
                     must not silently re-score this report).
  per-check evidence each AG check states what it must be given to be asserted
                     at all (_AG_RULES[...]["requires"]). A claim with nothing
                     observable behind it is rejected and counted, not
                     published; a claim missing only its corroborating source
                     is capped at suspected with reduced confidence.
  severity ceiling   each check carries max_severity. The agent can lower a
                     severity but never raise it past what the check can mean,
                     and no agent finding is ever critical.

Target-origin split: URLs the agent supplies are separated by origin. Pages on
the audited site become affected_pages (so the finding merges with the script
finding for the same page); everything else becomes source_references -- a
third-party thread is the evidence for a finding, never a page of the site that
has the defect.

Graceful skip and the empty-array problem: when no agent findings are supplied --
the common case in an evaluation harness that has not run the qualitative stage --
the stage records not_supplied and returns insufficient_evidence. A supplied but
empty findings array is *also* not an all-pass: it means "this file reports no
findings", which covers both "every check passed" and "my search tool was
unavailable". Only an explicit per-check outcome map (`checks`) can say which, so
an empty array without one records empty_unspecified and the affected checks stay
unassessed. It never upgrades "the stage did not run" into "no corroboration
exists"; that asymmetry is the single most common way an audit manufactures a
false negative.
"""
import json
import os
from urllib.parse import urlsplit

from models import (skill_result, make_finding, insufficient_evidence_result,
                     apply_invariant_i1)
from url_safety import same_origin

# Environment variable naming the agent's findings file. Kept as an env var (not a
# fixed workdir path) so nothing about this stage assumes a subprocess
# workdir convention; when it is unset, the stage simply skips.
_FINDINGS_ENV = "AGENT_FINDINGS_PATH"

# Bounded input. The agent writes this file; the audit reads it defensively, with
# the same kind of cap the HTTP transport puts on a response body.
MAX_FINDINGS_BYTES = 256_000
MAX_FINDINGS_ENTRIES = 40
MAX_EVIDENCE_ITEMS = 8
MAX_EVIDENCE_CHARS = 600
MAX_EVIDENCE_URLS = 5
MAX_AFFECTED_PAGES = 10
MAX_SOURCE_REFERENCES = 10

# AG check IDs -> catalog rule IDs, category, and the honest status/severity the
# agent stage is allowed to assert.
#
# requires says what the check needs to be asserted:
#   observation      a description of what was actually read or seen (every check)
#   target_page      a URL on the audited site the finding is about (AG-01, AG-04:
#                    the agent read that page or an image on it)
#   external_source  at least one off-site URL backing the claim (AG-03, AG-05:
#                    a contradiction or a namesake must name where it was seen)
#   search_ran       evidence that a search was actually performed (AG-02, AG-06:
#                    these are absence claims, and absence is only meaningful
#                    once someone looked)
# A missing `observation` rejects the entry outright. A missing corroboration
# requirement (external_source / search_ran) caps it at suspected instead.
_AG_RULES = {
    "AG-01": {
        "rule_id": "about-concreteness",
        "category": "answer_content",
        "default_severity": "medium",
        "max_severity": "medium",
        "default_status": "suspected",
        "default_type": "proactive_improvement",
        "requires": ("observation", "target_page"),
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
        "max_severity": "low",
        "default_status": "confirmed",
        "default_type": "proactive_improvement",
        "requires": ("observation", "search_ran"),
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
        "max_severity": "high",
        "default_status": "confirmed",
        "default_type": "defect",
        "requires": ("observation", "external_source"),
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
        "max_severity": "medium",
        "default_status": "confirmed",
        "default_type": "defect",
        "requires": ("observation", "target_page"),
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
        "max_severity": "medium",
        "default_status": "confirmed",
        "default_type": "defect",
        "requires": ("observation", "external_source"),
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
        "max_severity": "low",
        "default_status": "confirmed",
        "default_type": "proactive_improvement",
        "requires": ("observation", "search_ran"),
        "title": "No profile on the review or directory platforms the category uses",
        "summary": "Claim or create the brand's profile on the platforms its category uses.",
        "steps": ("Pick the two or three platforms the category uses (for example G2 or Capterra for software, "
                  "Google Business Profile or Yelp for a local business)",
                  "Use the exact brand name and site URL there",
                  "Link the profiles from Organization sameAs"),
    },
}

AG_CHECKS = tuple(sorted(_AG_RULES))
_VALID_SEVERITY = {"critical", "high", "medium", "low"}
_SEVERITY_ORDER = ("low", "medium", "high", "critical")
_VALID_STATUS = {"confirmed", "suspected", "insufficient_evidence"}
_STATUS_ORDER = ("insufficient_evidence", "suspected", "confirmed")
# Per-check outcomes the agent may declare in the `checks` map. Anything else is
# recorded verbatim as unknown rather than guessed at.
_VALID_OUTCOMES = {"pass", "fail", "not_assessed"}
# An observation has to say something about what was read or seen. The gate is
# "did you state what you observed", not "did you write a paragraph", so a terse
# real sentence passes and a placeholder does not.
MIN_OBSERVATION_CHARS = 15
_PLACEHOLDERS = frozenset({"n/a", "na", "none", "nothing", "see above", "see brief", "unknown",
                           "not applicable", "no comment", "tbd", "todo", "-", "--",
                           "agent-supplied reference", "agent-supplied qualitative observation"})


class _Supplied:
    """One parsed, bounded agent handoff."""

    def __init__(self, items, checks=None, search=None, site=None):
        self.items = items
        self.checks = checks or {}
        self.search = search or {}
        self.site = site

    def search_ran(self):
        """Did a search actually run? True only on a positive signal, so the
        absence checks (AG-02 / AG-06) cannot be confirmed by silence."""
        s = self.search
        if not isinstance(s, dict):
            return False
        if s.get("available") is False:
            return False
        for key in ("queries_run", "queries", "searches", "results_seen"):
            v = s.get(key)
            if isinstance(v, (int, float)) and v > 0:
                return True
            if isinstance(v, (list, tuple)) and v:
                return True
        return bool(s.get("available") is True and s.get("provider"))


def _cap(value, limit):
    text = " ".join(str(value or "").split())
    return text[:limit]


def _clean_urls(raw):
    """http(s) URLs only, de-duplicated, capped. A javascript:, data: or
    otherwise unparseable reference from the agent never reaches the report."""
    out = []
    for u in (raw if isinstance(raw, (list, tuple)) else [raw]):
        if not isinstance(u, str) or not u.strip():
            continue
        try:
            p = urlsplit(u.strip())
        except ValueError:
            continue
        if p.scheme.lower() in ("http", "https") and p.hostname and u.strip() not in out:
            out.append(u.strip())
    return out


def _load_supplied(path):
    """Return a _Supplied, or None when nothing usable was supplied.

    A malformed, unreadable or over-long file is treated as not_supplied rather
    than an error so a bad handoff never takes the audit down."""
    if not path or not os.path.isfile(path):
        return None
    try:
        if os.path.getsize(path) > MAX_FINDINGS_BYTES:
            return None
        with open(path, "rb") as handle:
            raw = handle.read(MAX_FINDINGS_BYTES + 1)
        if len(raw) > MAX_FINDINGS_BYTES:
            return None
        data = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    if isinstance(data, dict):
        items = data.get("findings", [])
        checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
        search = data.get("search") if isinstance(data.get("search"), dict) else {}
        site = data.get("site") or data.get("audit_site")
        site = site if isinstance(site, str) else None
    else:
        items, checks, search, site = data, {}, {}, None
    if not isinstance(items, list):
        return None
    return _Supplied(items[:MAX_FINDINGS_ENTRIES], checks, search, site)


def _binding_ok(supplied, site_url):
    """A findings file may name the audit it belongs to. When it names a
    different site than the one being audited, the handoff is refused: a file
    from another run must never re-score this report."""
    if not supplied.site or not site_url:
        return True
    return same_origin(supplied.site, site_url)


def _check_outcomes(supplied):
    """{AG-xx: pass|fail|not_assessed|unreported|unknown:<value>} for every check.
    Checks the agent said nothing about stay 'unreported' -- which is not 'pass'."""
    out = {}
    for check in AG_CHECKS:
        raw = supplied.checks.get(check)
        if raw is None:
            raw = supplied.checks.get(check.lower())
        if raw is None:
            out[check] = "unreported"
            continue
        value = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
        value = {"passed": "pass", "ok": "pass", "clear": "pass", "fired": "fail",
                 "failed": "fail", "skipped": "not_assessed",
                 "unavailable": "not_assessed"}.get(value, value)
        out[check] = value if value in _VALID_OUTCOMES else "unknown:" + _cap(raw, 40)
    return out


def _evidence_list(raw, site_url):
    """(evidence, target_pages, source_references) from whatever the agent sent.

    Accepts a plain string or a list of evidence objects, always returning the
    list-of-dicts evidence shape. Every description is length-capped and every
    URL is validated and split by origin: pages of the audited site are the
    finding's pages, third-party references are its sources."""
    ev = raw.get("evidence")
    items = []
    if isinstance(ev, str) and ev.strip():
        items = [{"type": "agent_observation", "description": ev}]
    elif isinstance(ev, list):
        items = [e for e in ev if isinstance(e, (dict, str))]
    cleaned, targets, sources = [], [], []
    for item in items[:MAX_EVIDENCE_ITEMS]:
        if isinstance(item, str):
            item = {"type": "agent_observation", "description": item}
        urls = _clean_urls(item.get("urls") or item.get("url") or ())
        for u in urls:
            bucket = targets if (site_url and same_origin(u, site_url)) else sources
            if u not in bucket:
                bucket.append(u)
        description = _cap(item.get("description") or item.get("snippet") or item.get("text") or "",
                           MAX_EVIDENCE_CHARS)
        if not description and not urls:
            continue
        entry = {"type": _cap(item.get("type") or "agent_observation", 40) or "agent_observation",
                 "description": description or "Agent-supplied reference"}
        if urls:
            entry["urls"] = urls[:MAX_EVIDENCE_URLS]
        cleaned.append(entry)
    return cleaned, targets, sources


def _observation(evidence):
    """The agent's own words for what it observed, or '' when it supplied none."""
    for item in evidence:
        text = item.get("description") or ""
        if len(text) >= MIN_OBSERVATION_CHARS and text.strip().strip(".").lower() not in _PLACEHOLDERS:
            return text
    return ""


def _cap_severity(severity, ceiling):
    if severity not in _SEVERITY_ORDER or ceiling not in _SEVERITY_ORDER:
        return ceiling
    return severity if _SEVERITY_ORDER.index(severity) <= _SEVERITY_ORDER.index(ceiling) else ceiling


def _cap_status(status, ceiling):
    if status not in _STATUS_ORDER or ceiling not in _STATUS_ORDER:
        return ceiling
    return status if _STATUS_ORDER.index(status) <= _STATUS_ORDER.index(ceiling) else ceiling


def _build_finding(raw, supplied, site_url):
    """Reconstruct one agent finding through make_finding so catalog
    enrichment and Invariant I-1 apply.

    Returns (finding, None) on success, or (None, reason) when the entry cannot
    be published: an unknown check, or a claim with no observation behind it."""
    check = str(raw.get("check") or raw.get("check_id") or "").strip().upper()
    rule = _AG_RULES.get(check)
    if rule is None:
        return None, "unknown_check:" + (_cap(check, 20) or "(none)")

    evidence, target_pages, source_refs = _evidence_list(raw, site_url)
    observed = _observation(evidence)
    requires = rule["requires"]
    if "observation" in requires and not observed:
        # The single most important gate: a check that fired with nothing
        # observable behind it is not a finding about the site.
        return None, check + ":no_observation"

    # Pages the agent named explicitly, kept only when they are on the audited
    # site; anything else is a source reference, not an affected page.
    for u in _clean_urls(raw.get("affected_pages") or ()):
        bucket = target_pages if (site_url and same_origin(u, site_url)) else source_refs
        if u not in bucket:
            bucket.append(u)
    pages = target_pages[:MAX_AFFECTED_PAGES]
    source_refs = source_refs[:MAX_SOURCE_REFERENCES]

    status = str(raw.get("status") or rule["default_status"]).lower()
    if status not in _VALID_STATUS:
        status = rule["default_status"]
    severity = str(raw.get("severity") or rule["default_severity"]).lower()
    if severity not in _VALID_SEVERITY:
        severity = rule["default_severity"]
    severity = _cap_severity(severity, rule["max_severity"])

    # Corroboration requirements. Missing ones do not void the finding; they cap
    # what it may claim, and the gap is stated in the evidence so a reader sees
    # exactly why the claim is only suspected.
    unmet = []
    if "target_page" in requires and not pages:
        unmet.append("no page of the audited site was named")
    if "external_source" in requires and not source_refs:
        unmet.append("no independent source URL was supplied")
    if "search_ran" in requires and not supplied.search_ran():
        unmet.append("the handoff does not record that a search actually ran")
    if unmet:
        status = _cap_status(status, "suspected")
        evidence = evidence + [{"type": "evidence_gap",
                                "description": "Reported by the agent stage without full corroboration: "
                                               + "; ".join(unmet) + "."}]
    if source_refs:
        evidence = evidence + [{"type": "source_reference",
                                "description": f"{len(source_refs)} independent source(s) cited by the agent",
                                "urls": source_refs}]
    confidence = (0.3 if status == "insufficient_evidence"
                  else 0.5 if unmet or status == "suspected"
                  else 0.7)

    action = raw.get("suggested_action")
    action = action if isinstance(action, dict) else {}
    summary = _cap(action.get("summary") or rule["summary"], 400)
    steps = action.get("steps")
    steps = ([_cap(s, 300) for s in steps][:8]
             if isinstance(steps, (list, tuple)) and steps else list(rule["steps"]))
    effort = str(action.get("effort") or "medium").lower()
    if effort not in ("low", "medium", "high"):
        effort = "medium"

    finding = make_finding(
        category=rule["category"],
        finding_type=rule["default_type"],
        severity=severity,
        status=status,
        confidence=confidence,
        title=_cap(raw.get("title") or rule["title"], 200),
        root_cause=observed or rule["title"],
        evidence=evidence,
        affected_pages=pages or None,
        suggested_action={
            "summary": summary,
            "steps": steps,
            "priority": severity,
            "effort": effort,
            "expected_benefit": "Improves identity clarity and independent corroboration",
            "verification": "Re-run the qualitative corroboration stage after changes",
        },
        provenance={"skill": "entity-corroboration-agent",
                    "script": "ingest_agent_findings.py", "rule_id": rule["rule_id"],
                    "agent_check": check, "evidence_gaps": unmet,
                    "source_references": source_refs},
    )
    # make_finding already applies Invariant I-1; re-apply defensively so an
    # agent-authored insufficient_evidence entry is capped no matter how it was
    # constructed. This is the same rule (apply_invariant_i1), not a second one.
    return apply_invariant_i1(finding), None


def _build_all(supplied, site_url):
    """(findings, rejected) for one parsed handoff."""
    findings, rejected = [], []
    for raw in supplied.items:
        if not isinstance(raw, dict):
            rejected.append("not_an_object")
            continue
        built, reason = _build_finding(raw, supplied, site_url)
        if built is None:
            rejected.append(reason)
        else:
            findings.append(built)
    return findings, rejected


def _stage_for(findings, supplied):
    """ingested, assessed_no_findings or empty_unspecified.

    An empty findings array only means "this file reports no findings". Treating
    it as "every AG check passed" would turn an unavailable search tool into a
    clean bill of health, so that claim needs an explicit per-check outcome."""
    if findings:
        return "ingested"
    outcomes = _check_outcomes(supplied)
    return "assessed_no_findings" if any(v == "pass" for v in outcomes.values()) else "empty_unspecified"


def _metrics(supplied, findings, rejected, stage):
    return {"agent_stage": stage, "findings_ingested": len(findings),
            "findings_supplied": len(supplied.items),
            "findings_rejected": len(rejected),
            "rejection_reasons": sorted(set(rejected)),
            "check_outcomes": _check_outcomes(supplied),
            "search_ran": supplied.search_ran()}


def _warnings(stage, rejected):
    out = []
    if rejected:
        out.append("The agent stage supplied " + str(len(rejected)) + " entry/entries that could not be published "
                   "(no observation behind the claim, or an unknown check): " + ", ".join(sorted(set(rejected))) + ".")
    if stage == "empty_unspecified":
        out.append("The agent corroboration stage reported no findings but recorded no per-check outcomes, so "
                   "AG-01 to AG-06 are not assessed rather than passed (an empty findings array cannot tell "
                   "\"nothing fired\" apart from \"the search tool was unavailable\").")
    return out


def load_agent_findings(path, site_url=None):
    """Ingest an agent findings file without a live snapshot (used by
    finalize_report.py after the agent stage). Returns (SkillResult, stage) where
    stage is one of:
      ingested             at least one finding was published
      assessed_no_findings nothing fired and the agent declared per-check outcomes
      empty_unspecified    nothing fired and no per-check outcomes were declared
      not_supplied         no readable file, or one bound to another site

    site_url binds the handoff to this audit and splits supplied URLs into pages
    of the audited site and third-party sources."""
    supplied = _load_supplied(path)
    if supplied is None:
        return (insufficient_evidence_result(
            "entity-corroboration-agent",
            "Agent corroboration stage not supplied; About-concreteness and cross-web corroboration were "
            "not checked this audit (not checked, not \"no corroboration found\").",
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0}), "not_supplied")
    if not _binding_ok(supplied, site_url):
        return (insufficient_evidence_result(
            "entity-corroboration-agent",
            f"Agent corroboration findings name a different site ({supplied.site}) than the audited one "
            f"({site_url}); the handoff was refused and the stage is recorded as not run.",
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0,
                     "rejection_reasons": ["site_mismatch"]}), "not_supplied")
    findings, rejected = _build_all(supplied, site_url)
    stage = _stage_for(findings, supplied)
    return (skill_result("entity-corroboration-agent", findings=findings,
                         metrics=_metrics(supplied, findings, rejected, stage),
                         warnings=_warnings(stage, rejected)), stage)


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

    site_url = getattr(artifacts, "site_url", None)
    supplied = _load_supplied(os.environ.get(_FINDINGS_ENV))
    if supplied is None or not _binding_ok(supplied, site_url):
        # Graceful not_supplied skip. The qualitative stage is optional and
        # agent-driven; its absence says nothing about the site.
        mismatch = supplied is not None
        return insufficient_evidence_result(
            "entity-corroboration-agent",
            (f"Agent corroboration findings name a different site ({supplied.site}) than the audited one "
             f"({site_url}); the handoff was refused and the stage is recorded as not run." if mismatch else
             "Agent corroboration stage not supplied (no AGENT_FINDINGS_PATH); the "
             "qualitative About-concreteness and cross-web corroboration checks were "
             "not run this audit (not checked, not \"no corroboration found\"). See "
             "skills/entity-corroboration-agent/SKILL.md."),
            metrics={"agent_stage": "not_supplied", "findings_ingested": 0,
                     **({"rejection_reasons": ["site_mismatch"]} if mismatch else {})},
        )

    findings, rejected = _build_all(supplied, site_url)
    stage = _stage_for(findings, supplied)
    return skill_result(
        "entity-corroboration-agent", findings=findings,
        metrics=_metrics(supplied, findings, rejected, stage),
        warnings=_warnings(stage, rejected),
        coverage={"pages_analyzed": len(artifacts.pages), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
