"""execution_summary.py -- ensures every report is fully populated and never
misleading about what did and didn't happen (Round-3 handout item 6):
site/timestamp/summary/findings/recommendations/coverage/capabilities are
already assembled by run_audit.py; this module adds the three fields that were
previously missing -- `execution_status`, `limitations`, and `confidence` -- all
derived from real signals recorded elsewhere in the run, never hardcoded
boilerplate and never fabricated precision.
"""


def derive_execution_status(deadline, skill_results: list, worker_timeout_events: list) -> str:
    """One of, in priority order:
      "partial_deadline_reached" -- the shared audit deadline was hit
      "degraded"                 -- at least one specialist crashed (status "failed")
      "completed_with_timeouts"  -- at least one specialist was abandoned after
                                     exceeding its per-worker timeout, but the
                                     overall deadline was not hit
      "completed"                -- normal completion
    These are read directly off real state (deadline.expired(), each skill's own
    reported status, and instrumentation's worker-timeout log) -- never inferred
    from counts that could be stale."""
    if deadline.expired():
        return "partial_deadline_reached"
    if any(r.get("status") == "failed" for r in skill_results):
        return "degraded"
    if worker_timeout_events:
        return "completed_with_timeouts"
    return "completed"


def derive_limitations(artifacts, capabilities: dict, coverage: dict, execution_status: str) -> list:
    """Plain-English limitations. Each line is gated on a real signal from this
    run -- nothing here is boilerplate that runs regardless of what happened, and
    nothing that is unassessed is ever implied to have passed (Round-3 handout:
    "Never imply unassessed check passed")."""
    out = []

    if artifacts.robots_data.get("conservative_fail_closed"):
        out.append(
            f"robots.txt could not be reliably retrieved or parsed (status: "
            f"'{artifacts.robots_data.get('status')}'); no pages were fetched without known "
            f"permission, so most on-site checks "
            f"in this report are insufficient_evidence rather than confirmed."
        )

    never_attempted = coverage.get("pages_never_attempted", 0)
    if never_attempted > 0:
        out.append(
            f"{never_attempted} discovered URL(s) were never fetched (permission, acquisition failure, or "
            f"budget constraints; out of {coverage.get('pages_discovered', 0)} discovered); findings "
            f"reflect only the {coverage.get('pages_fetched_attempted', 0)} page(s) actually crawled, "
            f"not the whole site."
        )

    if coverage.get("pages_timed_out", 0) > 0:
        out.append(
            f"{coverage['pages_timed_out']} page fetch(es) timed out and were not analyzed for content."
        )

    if not capabilities.get("headless_rendering"):
        out.append(
            "Headless browser rendering was not available in this environment; rendering-gap "
            "findings are based on a static-content heuristic only and are reported as "
            "suspected/insufficient_evidence rather than confirmed."
        )

    if not capabilities.get("external_search"):
        out.append(
            "No external search provider was configured; claim corroboration and off-site "
            "footprint assessment were not checked this run (not the same as \"nothing found\")."
        )

    media = coverage.get("non_text_media") or {}
    unread_raster = [e for e in (getattr(artifacts, "media_data", None) or {}).get("images", ())
                     if e.get("keywords") and e.get("svg_status") != "ok"]
    if unread_raster and coverage.get("agent_corroboration_stage") != "ingested":
        out.append(
            f"{len(unread_raster)} image(s) whose file name or alt text suggests prices, hours or "
            f"specifications were not read: the scripts never interpret raster pixels, and the agent "
            f"vision stage (AG-04) was not supplied, so facts inside those images are suspected, not confirmed."
        )
    skipped_pdfs = media.get("pdfs_discovered", 0) - media.get("pdfs_fetch_attempted", 0)
    if skipped_pdfs > 0:
        out.append(
            f"{skipped_pdfs} linked PDF(s) were not fetched (robots rules, a cross-origin redirect, the "
            f"per-audit cap of {media.get('pdf_fetch_cap', 0)}, or remaining budget; see "
            f"coverage.non_text_media.pdf_outcomes); their contents were not assessed."
        )

    kg = coverage.get("knowledge_graph") or {}
    if kg.get("lookup") in ("disabled", "incomplete"):
        out.append(
            "The Wikidata or Wikipedia entity declared in Organization sameAs could not be fully verified "
            f"(lookup {kg['lookup']}; see coverage.knowledge_graph), so a mismatch with the brand was not "
            "ruled out."
        )
    if kg.get("organization_pages") and coverage.get("agent_corroboration_stage") != "ingested":
        out.append(
            "No search for same-named knowledge-graph entities was run: robots.txt for Wikidata and "
            "Wikipedia disallows their search endpoints, so only the agent stage (AG-05) can look the "
            "brand name up; namesake ambiguity is unassessed."
        )

    if artifacts.sitemap_data.get("status") not in ("ok", "absent"):
        out.append(
            f"sitemap.xml could not be checked (status: '{artifacts.sitemap_data.get('status')}'); "
            f"crawl coverage may be incomplete relative to a site that publishes one."
        )

    if execution_status == "partial_deadline_reached":
        out.append("The shared audit deadline was reached before every analysis stage finished; "
                    "unfinished work is reported as insufficient_evidence, not silently dropped.")
    elif execution_status == "completed_with_timeouts":
        out.append("At least one analysis specialist exceeded its per-worker time budget and was "
                    "abandoned; its findings are insufficient_evidence rather than fabricated.")
    elif execution_status == "degraded":
        out.append("Acquisition or an analysis specialist could not complete; affected checks remain "
                    "unassessed rather than being treated as passed.")

    return out


def overall_confidence(coverage: dict, execution_status: str) -> dict:
    """A single, honestly-derived overall confidence score plus the method used to
    compute it -- explicit rather than implied precision (Round-3 handout,
    Priority 3 #19: "avoid false precision; document calculation").

    Method: the minimum of --
      - crawl_completeness = pages_fetched_attempted / pages_discovered (1.0 if
        nothing was discovered at all -- there is nothing incomplete to report)
      - identity_confidence, as resolved by entity resolution
      - an execution penalty: 1.0 normally, 0.7 if the run completed with
        timeouts or was degraded, 0.4 if the deadline was reached before
        finishing
    take the minimum, not an average, because any one of these being poor should
    pull overall confidence down -- a high identity_confidence should not paper
    over a crawl that only reached 10% of the site.
    """
    discovered = coverage.get("pages_discovered", 0)
    fetched = coverage.get("pages_fetched_attempted", 0)
    crawl_completeness = 1.0 if discovered <= 0 else min(1.0, fetched / discovered)
    identity_confidence = coverage.get("identity_confidence", 0.0)
    execution_penalty = {
        "completed": 1.0, "completed_with_timeouts": 0.7,
        "degraded": 0.7, "partial_deadline_reached": 0.4,
    }.get(execution_status, 0.5)

    score = min(crawl_completeness, identity_confidence, execution_penalty)
    return {
        "score": round(score, 2),
        "method": "min(crawl_completeness, identity_confidence, execution_penalty) -- "
                  "a weak link in any one dimension caps overall confidence rather than being averaged out",
        "components": {
            "crawl_completeness": round(crawl_completeness, 2),
            "identity_confidence": round(identity_confidence, 2),
            "execution_penalty": round(execution_penalty, 2),
        },
    }
