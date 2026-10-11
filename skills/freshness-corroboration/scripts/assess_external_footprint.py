"""assess_external_footprint.py -- calibrated footprint findings.
Search non-detection is never proof of real-world absence. Uses the pluggable
search_provider (fallback/optional capability); degrades to insufficient_evidence,
never a confirmed absence, whenever the provider is unconfigured or fails.

Round-3 handout, Priority 2 #4 additions: the actual query strings issued are
recorded (bounded, for reproducibility); "source quality" is approximated by
counting distinct domains among matched hits (source_diversity) -- a handful of
hits from the same domain is weaker signal than the same count spread across
independent domains, even though both count the same toward `matched_hits`."""
from urllib.parse import urlsplit
from models import (skill_result, make_finding, insufficient_evidence_result,
                     coverage_ratio, weakest_link_confidence, step_down_severity)
from search_provider import is_configured, search, SearchProviderError


def _domain_of(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower()
    except ValueError:
        return ""


def assess_external_footprint(artifacts, identity, deadline, limits, instrumentation=None):
    if identity.get("status") != "success" or identity.get("data", {}).get("confidence", 0) < 0.85:
        return insufficient_evidence_result(
            "freshness-corroboration",
            "External footprint not assessed: identity unresolved or below confidence threshold.",
        )

    if not is_configured():
        return insufficient_evidence_result(
            "freshness-corroboration",
            "No external search provider configured (SEARCH_API_URL unset); "
            "footprint assessment is an optional capability in this deployment "
            "(not checked, not \"no presence found\").",
            metrics={"queries_attempted": 0, "queries_completed": 0, "provider_configured": False,
                     "queries_issued": []},
        )

    name = identity["data"]["canonical_name"]
    queries = [name, f"{name} reviews", f"{name} official", f"{name} contact"][: limits.MAX_FOOTPRINT_QUERIES]
    attempted, completed, matched_hits = 0, 0, []
    queries_issued = []  # {"query":..., "hits_matched":...} -- the actual query formulation used
    deadline_exceeded = False

    for q in queries:
        # Cooperative cancellation (see corroborate_claims.py for why a
        # between-iterations check is sufficient here): each search() call has its
        # own hard per-fetch timeout, so the shared audit deadline is always
        # observed promptly between queries even without process-level isolation.
        if deadline is not None and deadline.expired():
            deadline_exceeded = True
            break
        # MAX_EXTERNAL_FETCHES is a combined budget shared with corroborate_claims,
        # which runs concurrently in the same dependent batch.
        if instrumentation is not None and instrumentation.search_queries_attempted >= limits.MAX_EXTERNAL_FETCHES:
            break
        attempted += 1
        try:
            hits = search(q, max_results=5, timeout_s=limits.PER_FETCH_TIMEOUT_MS / 1000)
            if instrumentation is not None:
                instrumentation.record_external_fetch(ok=True, search=True)
            completed += 1
            new_matches = [h for h in hits if identity["data"]["domain"] not in h.get("url", "")]
            matched_hits.extend(new_matches)
            queries_issued.append({"query": q, "hits_matched": len(new_matches)})
        except SearchProviderError:
            if instrumentation is not None:
                instrumentation.record_external_fetch(ok=False, search=True)
            queries_issued.append({"query": q, "hits_matched": None, "error": "provider_failed"})
            break  # bounded: stop on first failure, don't retry-storm

    if completed == 0:
        reason = ("Audit deadline reached before any footprint query completed."
                   if deadline_exceeded else
                   "External search provider failed before any query completed.")
        return insufficient_evidence_result(
            "freshness-corroboration", reason,
            metrics={"queries_attempted": attempted, "queries_completed": completed,
                     "provider_configured": True, "queries_issued": queries_issued,
                     "deadline_exceeded": deadline_exceeded},
        )

    # Source-quality proxy: how many INDEPENDENT domains the matched hits span,
    # not just how many hits there are -- five hits on one directory is weaker
    # evidence than five hits across five different domains.
    distinct_domains = {_domain_of(h.get("url", "")) for h in matched_hits if h.get("url")}
    source_diversity = len(distinct_domains)

    coverage_adequate = completed == len(queries)

    # Coverage confidence (did we run enough of the intended queries) and identity
    # confidence (how well the brand's identity was resolved) are two genuinely
    # different dimensions of confidence and are kept separate here rather than
    # collapsed into one opaque min() -- a well-resolved identity checked with only
    # 1 of 4 queries should read differently from a poorly-resolved identity
    # checked exhaustively, even though a naive min() could report the same number
    # for both (Round-3 review item 2: "coverage confidence vs. site-quality
    # separation"). Both components are also surfaced in metrics below.
    identity_confidence = identity["data"]["confidence"]
    query_coverage_confidence = coverage_ratio(completed, len(queries))
    confidence_breakdown = weakest_link_confidence(
        identity_confidence=identity_confidence,
        coverage_confidence=query_coverage_confidence,
    )
    severity = step_down_severity(
        "medium" if (not matched_hits and coverage_adequate) else "low",
        query_coverage_confidence,
    )
    findings = [make_finding(
        category="off_site_presence", finding_type="proactive_improvement",
        severity=severity, status="confirmed" if matched_hits or coverage_adequate else "insufficient_evidence",
        confidence=confidence_breakdown["score"],
        title="Limited independent web presence found under the resolved brand identity"
        if not matched_hits else "Independent web presence found under the resolved brand identity",
        root_cause="Few identity-matched independent sources were found within tested coverage"
        if not matched_hits else f"Independent sources reference the resolved brand identity across "
                                  f"{source_diversity} distinct domain(s)",
        evidence=[{"type": "search_hit", "description": h.get("title", ""), "urls": [h.get("url", "")]}
                  for h in matched_hits[:5]],
        suggested_action={
            "summary": "Strengthen off-site presence (directories, press, social profiles)"
            if not matched_hits else "Maintain and diversify existing off-site mentions"
            if source_diversity > 1 else "Diversify off-site mentions beyond the current single source",
            "steps": ["List on relevant directories", "Pursue press or partner mentions",
                      "Keep social/sameAs profiles active"],
            "priority": "low", "effort": "medium",
            "expected_benefit": "Improves independent corroboration signals used by AI assistants",
            "verification": "Re-run footprint assessment after outreach",
        },
        provenance={"skill": "freshness-corroboration", "script": "assess_external_footprint.py",
                    "rule_id": "footprint-signal"},
    )]

    return skill_result(
        "freshness-corroboration", findings=findings,
        metrics={"queries_attempted": attempted, "queries_completed": completed,
                 "matched_hits": len(matched_hits), "source_diversity": source_diversity,
                 "provider_configured": True, "queries_issued": queries_issued,
                 "deadline_exceeded": deadline_exceeded,
                 # Kept distinct on purpose -- see confidence_breakdown above.
                 "identity_confidence": round(identity_confidence, 3),
                 "coverage_confidence": round(query_coverage_confidence, 3),
                 "confidence_breakdown": confidence_breakdown},
        warnings=["Stopped early: audit deadline reached before all footprint queries were issued."]
        if deadline_exceeded else None,
    )
