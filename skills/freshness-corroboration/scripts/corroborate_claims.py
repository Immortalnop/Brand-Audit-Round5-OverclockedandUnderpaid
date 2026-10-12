"""corroborate_claims.py -- consumes the shared identity artifact; bounded external
checks.

calibration this module enforces:
  - compares claim VALUES against result content, not just "did a search return
    anything" -- a claim is corroborated only when its normalized value actually
    appears in an independent result, and is flagged as suspected-contradicted
    only when a *different* value of the same shape (phone/price/date) is found
    and the claim's own value is not
  - "not checked" (provider unconfigured/failed) is never conflated with
    "not found" (a real search ran and found nothing matching)
  - the actual query issued for each fact is recorded (bounded), not just a count
  - zero search results/unavailable providers/incomplete queries never create a
    confirmed defect -- contradictions are reported as `status="suspected"`,
    never `"confirmed"` (Invariant I-1 does not require this, but the absence-of-
    proof asymmetry does: a search-based mismatch is evidence of a discrepancy
    worth checking, not proof one exists)
"""
import re
from models import (skill_result, make_finding, insufficient_evidence_result,
                     coverage_ratio, scale_confidence)
from search_provider import is_configured, search, SearchProviderError

_DIGITS_RE = re.compile(r"\d+")
_MAX_RECORDED_QUERIES = 20


def _normalize_text(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def _digit_sequence(s: str) -> str:
    """Strips everything but digits -- lets '(555) 123-4567' match '555-123-4567'."""
    return "".join(_DIGITS_RE.findall(str(s)))


def _extract_candidate_values(text: str, fact_type: str) -> list:
    """Pulls out other values of the SAME shape as the claim from a result's text,
    using the same patterns extract_claims.py used originally, so a genuinely
    different phone number/price/date found elsewhere can be recognized as a
    candidate contradiction rather than silently ignored."""
    if fact_type == "contact":
        pattern = re.compile(r"\+?\d[\d\-\s\(\)]{7,}\d")
    elif fact_type == "price":
        pattern = re.compile(r"(?:[$€£₹]|INR\s*)\s?\d[\d,]*(?:\.\d{2})?")
    elif fact_type == "date":
        pattern = re.compile(r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b")
    else:
        return []
    return pattern.findall(text) if fact_type != "date" else pattern.findall(text)


def _compare_claim_to_results(fact: dict, results: list) -> tuple:
    """Returns (outcome, detail) where outcome is one of:
    "corroborated" / "contradicted" / "not_found". Never returns "not_checked"
    -- that state is decided by the caller before a search is even attempted."""
    value = fact.get("value", "")
    fact_type = fact.get("type", "")
    combined_text = " ".join(f"{r.get('title', '')} {r.get('snippet', '')}" for r in results)

    if fact_type in ("contact", "price"):
        claim_digits = _digit_sequence(value)
        if claim_digits and any(claim_digits == _digit_sequence(candidate)
                                for r in results
                                for field in ("title", "snippet")
                                for candidate in _extract_candidate_values(r.get(field, ""), fact_type)):
            return "corroborated", None
        # Look for a DIFFERENT value of the same shape -- a genuine candidate
        # contradiction, not just "we didn't happen to see this one repeated".
        for r in results:
            text = f"{r.get('title', '')} {r.get('snippet', '')}"
            for candidate in _extract_candidate_values(text, fact_type):
                cand_digits = _digit_sequence(candidate)
                if cand_digits and claim_digits and cand_digits != claim_digits:
                    return "contradicted", {"claim_value": value, "other_value": candidate,
                                             "source_url": r.get("url", "")}
        return "not_found", None

    # Structured/date/free-text values: require the normalized value (or a
    # meaningful chunk of it) to appear verbatim; no attempt at contradiction
    # detection for free text -- too easy to produce false positives.
    normalized_value = _normalize_text(value)
    if normalized_value and normalized_value in _normalize_text(combined_text):
        return "corroborated", None
    return "not_found", None


def corroborate_claims(facts, entity_identity, artifacts, deadline, limits, instrumentation=None):
    if entity_identity.get("status") not in ("success", "partial"):
        return insufficient_evidence_result(
            "freshness-corroboration", "Entity identity unresolved; corroboration suppressed."
        )

    if not is_configured():
        # "Not checked" -- explicitly distinct from "checked, found nothing".
        return insufficient_evidence_result(
            "freshness-corroboration",
            "No external search provider configured (SEARCH_API_URL unset); "
            "corroboration is an optional capability in this deployment (not checked, not \"not found\").",
            metrics={"claims_checked": 0, "claims_corroborated": 0, "claims_contradicted": 0,
                     "claims_not_found": 0, "provider_configured": False, "queries_issued": []},
        )

    fact_list = facts.get("data", {}).get("facts", [])[: limits.MAX_CLAIMS_CORROBORATED]
    name = entity_identity.get("data", {}).get("canonical_name", "")
    checked, corroborated, contradictions, not_found = 0, 0, [], 0
    queries_issued = []  # {"query":..., "outcome":...} -- bounded, for reproducibility
    provider_failed = False
    deadline_exceeded = False

    for fact in fact_list:
        # Cooperative cancellation: each search() call already has its own hard
        # PER_FETCH_TIMEOUT_MS, but MAX_CLAIMS_CORROBORATED/MAX_EXTERNAL_FETCHES
        # alone don't bound *wall-clock* time -- enough slow-but-not-failing calls
        # could still run past the shared audit deadline. This is a software
        # (cooperative) check between iterations, not the hard process-level kill
        # subprocess_isolation.py gives headless rendering; it's sufficient here
        # because each iteration is bounded by its own fetch timeout, so the loop
        # can always observe the deadline promptly between calls.
        if deadline is not None and deadline.expired():
            deadline_exceeded = True
            break
        if instrumentation is not None and instrumentation.external_fetches_attempted >= limits.MAX_EXTERNAL_FETCHES:
            break
        checked += 1
        query = f"{name} {fact.get('value', '')}".strip()
        try:
            results = search(query, max_results=3, timeout_s=limits.PER_FETCH_TIMEOUT_MS / 1000)
            if instrumentation is not None:
                instrumentation.record_external_fetch(ok=True)
            outcome, detail = _compare_claim_to_results(fact, results)
            if outcome == "corroborated":
                corroborated += 1
            elif outcome == "contradicted":
                contradictions.append({"fact": fact, "detail": detail})
            else:
                not_found += 1
            if len(queries_issued) < _MAX_RECORDED_QUERIES:
                queries_issued.append({"query": query, "outcome": outcome})
        except SearchProviderError:
            if instrumentation is not None:
                instrumentation.record_external_fetch(ok=False)
            provider_failed = True
            break  # bounded: stop on first provider failure rather than retry-storming

    if provider_failed:
        return insufficient_evidence_result(
            "freshness-corroboration",
            "External search provider failed during corroboration; remaining claims "
            "are reported as insufficient evidence, not contradicted or absent.",
            metrics={"claims_checked": checked, "claims_corroborated": corroborated,
                     "claims_contradicted": len(contradictions), "claims_not_found": not_found,
                     "provider_configured": True, "queries_issued": queries_issued},
        )

    # Evidence completeness: confidence reflects how much of the identified
    # important-fact list was actually checked before the run stopped (budget,
    # deadline, or provider limits) -- a contradiction found after checking 2 of 12
    # important facts says less about the whole site than one found after checking
    # all 12.
    check_ratio = coverage_ratio(checked, len(fact_list))

    findings = []
    if contradictions:
        # Each conflicting claim is represented explicitly -- both the on-site
        # value and the differing value found externally, with its source --
        # never collapsed into a vague "some claims may be wrong".
        findings.append(make_finding(
            category="corroboration", finding_type="defect", severity="medium",
            status="suspected", confidence=scale_confidence(0.5, check_ratio),
            title="Independent sources appear to show a different value than the site states",
            root_cause="External search results contain a differing value of the same kind "
                       "(phone number/price) as an on-site claim"
                       + ("" if check_ratio >= 0.999 else
                          f" (found after checking {checked} of {len(fact_list)} identified "
                          "important facts before the run stopped)"),
            evidence=[
                {"type": "corroboration_conflict",
                 "description": f"Site states '{c['detail']['claim_value']}'; found "
                                 f"'{c['detail']['other_value']}' externally",
                 "urls": [c["detail"]["source_url"]] if c["detail"]["source_url"] else []}
                for c in contradictions[:5]
            ],
            suggested_action={
                "summary": "Review and reconcile the conflicting values",
                "steps": ["Compare the on-site value to the external source",
                          "Correct whichever is stale or update the other listing"],
                "priority": "medium", "effort": "medium",
                "expected_benefit": "Reduces risk of assistants surfacing conflicting facts",
                "verification": "Re-run corroboration after updating",
            },
            provenance={"skill": "freshness-corroboration", "script": "corroborate_claims.py",
                        "rule_id": "contradicted-claim"},
        ))

    return skill_result(
        "freshness-corroboration", findings=findings,
        metrics={"claims_checked": checked, "claims_corroborated": corroborated,
                 "claims_contradicted": len(contradictions), "claims_not_found": not_found,
                 "provider_configured": True, "queries_issued": queries_issued,
                 "deadline_exceeded": deadline_exceeded, "check_coverage_ratio": round(check_ratio, 3)},
        warnings=["Stopped early: audit deadline reached before all claims were checked; "
                  "remaining claims are not represented above, not treated as absent."]
        if deadline_exceeded else None,
    )
