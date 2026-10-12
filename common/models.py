"""Immutable shared dataclasses and schema helpers."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from time import monotonic
from types import MappingProxyType
from typing import Optional


def freeze_value(value):
    """Recursively wrap dicts/lists in read-only views. Second-layer defense on top
    of frozen(=True) dataclasses (section 2): a MappingProxyType raises TypeError on
    any write attempt, so accidental mutation fails loudly instead of silently
    corrupting shared state.
    """
    if isinstance(value, dict):
        return MappingProxyType({k: freeze_value(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(freeze_value(v) for v in value)
    if isinstance(value, tuple):
        return tuple(freeze_value(v) for v in value)
    return value


def _jsonable(value):
    """Recursive, deepcopy-free conversion to JSON-safe structures. Written by hand
    (rather than dataclasses.asdict, which deepcopies every leaf and cannot deepcopy
    a MappingProxyType) so it works directly on the frozen artifacts, mutation-proof
    dict fields included."""
    from dataclasses import is_dataclass, fields
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, MappingProxyType):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def hash_artifacts(artifacts) -> str:
    """Stable content hash used by the frozen-artifact acceptance test: any change to
    artifacts between two hashes (including a nested-dict mutation that `frozen=True`
    alone would not catch) is detected."""
    payload = _jsonable(artifacts)
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@dataclass(frozen=True)
class PageArtifact:
    """Acquisition-owned observations only. No analysis conclusions belong here (section 2)."""
    url: str
    status_code: Optional[int]
    content_type: Optional[str]
    evidence_snippet: Optional[str]
    visible_text: str
    title: Optional[str]
    meta_description: Optional[str]
    canonical_url: Optional[str]
    headings: tuple
    internal_links: tuple
    external_links: tuple
    jsonld_blocks: tuple
    page_type: Optional[str]
    fetch_duration_ms: Optional[int]
    render_status: str
    breadcrumb_visible: tuple
    breadcrumb_schema: Optional[dict]
    ai_crawler_directives: dict
    warnings: tuple = ()
    features: object = None
    response_headers: object = None
    final_url: Optional[str] = None


@dataclass(frozen=True)
class AuditArtifacts:
    """Immutable, read-only snapshot. No specialist may mutate, append to, or replace
    fields on it (section 1 invariant)."""
    site_url: str
    normalized_origin: str
    pages: tuple
    robots_data: dict
    llms_txt_data: dict
    sitemap_data: dict
    acquisition_metadata: dict
    warnings: tuple


@dataclass(frozen=True)
class AuditDeadline:
    started_monotonic: float
    deadline_monotonic: float
    stage_deadlines: dict

    def remaining_seconds(self) -> float:
        return max(0.0, self.deadline_monotonic - monotonic())

    def expired(self) -> bool:
        return self.remaining_seconds() <= 0.0


def make_deadline(limits) -> AuditDeadline:
    now = monotonic()
    return AuditDeadline(
        started_monotonic=now,
        deadline_monotonic=now + limits.TOTAL_AUDIT_TIMEOUT_S,
        stage_deadlines={
            "acquisition": now + min(limits.ACQUISITION_BUDGET_S, limits.TOTAL_AUDIT_TIMEOUT_S * .6),
            "rendering": now + limits.ACQUISITION_BUDGET_S + limits.RENDERING_BUDGET_S,
            "external_analysis": now + limits.ACQUISITION_BUDGET_S
            + limits.RENDERING_BUDGET_S + limits.EXTERNAL_ANALYSIS_BUDGET_S,
        },
    )


def skill_result(skill: str, findings=None, metrics=None, warnings=None,
                  coverage=None, status="success") -> dict:
    return {
        "skill": skill,
        "status": status,
        "findings": findings or [],
        "metrics": metrics or {},
        "warnings": warnings or [],
        "coverage": coverage or {"pages_analyzed": 0, "pages_skipped": 0,
                                  "queries_attempted": 0, "queries_completed": 0},
    }


def insufficient_evidence_result(skill: str, reason: str, metrics=None) -> dict:
    return skill_result(skill, status="insufficient_evidence",
                         warnings=[reason], metrics=metrics or {})


def intermediate_artifact(artifact_type: str, data=None, status="success", warnings=None) -> dict:
    return {"artifact_type": artifact_type, "status": status,
            "data": data or {}, "warnings": warnings or []}


_FINDING_COUNTER = {"n": 0}


def coverage_ratio(observed, total) -> float:
    """Fraction of the relevant population actually observed/checked. Returns 1.0
    when total is 0/unknown -- there is nothing incomplete to report relative to a
    denominator that doesn't exist, so an unknown population is never treated as
    evidence of poor coverage."""
    if not total or total <= 0:
        return 1.0
    return max(0.0, min(1.0, observed / total))


def scale_confidence(base_confidence: float, ratio: float, floor: float = 0.3) -> float:
    """Pulls a rule's base confidence toward `floor` in proportion to how much of the
    relevant population backs it. ratio=1.0 (full coverage) leaves confidence
    unchanged; lower ratios pull it down. Confidence never rises above what the rule
    would have reported under full coverage, and never falls below `floor` -- partial
    evidence should never look MORE confident than complete evidence would, but a
    single sample is still worth reporting, just at reduced confidence rather than
    suppressed outright (suppression is Invariant I-1's job, for the no-evidence case)."""
    ratio = max(0.0, min(1.0, ratio))
    scaled = floor + (base_confidence - floor) * ratio
    return round(max(floor, min(base_confidence, scaled)), 3)


_SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def step_down_severity(severity: str, ratio: float, threshold: float = 0.5) -> str:
    """Kept for the query-coverage case in assess_external_footprint.py only. Detectors
    no longer scale severity by crawl coverage: since Round 5 severity is impact and
    scope (common/scoring.py), and sample size affects confidence only.

    Steps a defect's severity down exactly one tier when the evidence behind it
    covers less than `threshold` of the relevant population -- e.g. a defect
    confirmed on 2 of 40 crawled pages is real, but shouldn't carry the same severity
    as one confirmed across a complete crawl. Never raises severity, never steps
    below 'low', and is orthogonal to Invariant I-1 (which governs the different case
    of no confirmed defect at all, i.e. status == insufficient_evidence)."""
    if severity not in _SEVERITY_ORDER or ratio >= threshold:
        return severity
    idx = _SEVERITY_ORDER.index(severity)
    return _SEVERITY_ORDER[max(0, idx - 1)]


def weakest_link_confidence(**components: float) -> dict:
    """Generalizes the report-level 'weak link' method already used by
    execution_summary.overall_confidence into a reusable primitive for individual
    findings: takes named confidence components (e.g. identity_confidence=0.9,
    coverage_confidence=0.4) and returns their minimum plus a labeled breakdown.
    This keeps distinct dimensions -- e.g. how well an entity was identified vs. how
    much of the intended search coverage actually completed -- visible and separate
    rather than collapsed into one opaque number. A weak link in any one dimension caps
    the result; it is never averaged away by a strong one."""
    if not components:
        return {"score": 0.0, "method": "no components provided", "components": {}}
    score = min(components.values())
    return {
        "score": round(score, 3),
        "method": "min(" + ", ".join(components.keys()) + ") -- the weakest dimension "
                  "caps the result rather than being averaged out",
        "components": {k: round(v, 3) for k, v in components.items()},
    }


def apply_invariant_i1(finding: dict) -> dict:
    """Invariant I-1 (section 9): insufficient_evidence implies proactive_improvement + low."""
    if finding.get("status") == "insufficient_evidence":
        finding["finding_type"] = "proactive_improvement"
        finding["severity"] = "low"
        finding["suggested_action"]["priority"] = "low"
    return finding


def make_evidence_text(evidence) -> str:
    """Project structured evidence entries into a clean, flat string summary."""
    if not evidence:
        return ""
    parts = []
    for e in evidence:
        if isinstance(e, dict):
            desc = e.get("description") or e.get("snippet") or e.get("text") or ""
            if desc:
                parts.append(str(desc).strip())
            elif "type" in e:
                parts.append(str(e["type"]).strip())
        elif isinstance(e, str):
            if e.strip():
                parts.append(e.strip())
    # A16: identical descriptions are reported once.
    return "; ".join(dict.fromkeys(p for p in parts if p)).strip()


def make_finding(category, finding_type, severity, status, confidence, title,
                  root_cause, evidence, suggested_action, provenance,
                  affected_pages=None, evidence_text=None) -> dict:
    _FINDING_COUNTER["n"] += 1
    evidence_str = str(evidence_text) if evidence_text is not None else make_evidence_text(evidence)
    finding = {
        "id": f"F-{_FINDING_COUNTER['n']:03d}",
        "category": category,
        "finding_type": finding_type,
        "title": title,
        "severity": severity,
        "confidence": confidence,
        "status": status,
        "affected_pages": sorted(set(affected_pages or [u for e in evidence if isinstance(e, dict) for u in e.get("urls", [])])),
        "root_cause": root_cause,
        "evidence": evidence,
        "evidence_text": evidence_str,
        "suggested_action": suggested_action,
        "provenance": provenance,
    }
    from check_catalog import enrich_finding
    finding = enrich_finding(finding)
    finding.setdefault("mechanism", root_cause)
    action = finding["suggested_action"]
    from check_helpers import numbered
    action.setdefault("implementation_detail", numbered(action.get("steps", [])))
    action.setdefault("expected_outcome", action.get("expected_benefit", "Review and verify the proposed improvement"))
    return apply_invariant_i1(finding)
