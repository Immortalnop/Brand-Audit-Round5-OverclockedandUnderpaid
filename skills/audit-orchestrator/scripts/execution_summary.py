"""execution_summary.py -- ensures every report is fully populated and never
misleading about what did and didn't happen:
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
    nothing that is unassessed is ever implied to have passed."""
    out = []

    if artifacts.robots_data.get("conservative_fail_closed"):
        fetched = coverage.get("pages_fetched_attempted", 0)
        status = artifacts.robots_data.get("status")
        why = ("robots.txt is served behind a bot challenge" if status == "challenged"
               else f"robots.txt could not be reliably retrieved or parsed (status: '{status}')")
        out.append(
            f"{why}; crawl permission is unknown, so the audit fetched {fetched} page(s)"
            + (" (homepage only, to identify the cause)" if fetched == 1 else "")
            + " and most on-site checks are insufficient_evidence rather than confirmed."
        )
    challenged = coverage.get("pages_challenged", 0)
    if challenged:
        out.append(f"{challenged} fetched page(s) returned a bot-protection challenge instead of content; they are "
                   "reported as an access problem and excluded from all content checks.")

    never_attempted = coverage.get("pages_never_attempted", 0)
    if never_attempted > 0:
        out.append(
            f"{never_attempted} discovered URL(s) were never fetched (permission, acquisition failure, or "
            f"budget constraints; out of {coverage.get('pages_discovered', 0)} discovered); findings "
            f"reflect the {coverage.get('pages_fetched_attempted', 0)} page(s) actually crawled "
            f"across {coverage.get('templates_sampled', 0)} distinct page template(s), not every URL."
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
    """Report-level confidence with its method shown (A6).

    min(sample_quality, access_quality, execution_penalty):
      sample_quality   = min(1, content pages / 20) x min(1, templates / 5),
                         floored at 0.3 when at least one page was analysed.
                         Large sites are not penalised for being large: 20 pages
                         across 5 templates is an adequate sample of any site.
      access_quality   = content pages / fetched pages (challenged pages lower it)
      execution_penalty 1.0 completed, 0.7 timeouts/degraded, 0.4 deadline hit
    Identity confidence is deliberately NOT part of this minimum: it only limits
    the off-site findings that depend on knowing who the brand is (scoring.py).
    """
    analysed = coverage.get("pages_analyzed", 0) or 0
    fetched = coverage.get("pages_fetched_attempted", 0) or 0
    templates = coverage.get("templates_sampled", analysed) or 0
    if analysed <= 0:
        sample_quality = 0.0
    else:
        sample_quality = max(0.3, min(1.0, analysed / 20) * min(1.0, max(1, templates) / 5))
    access_quality = 1.0 if fetched <= 0 else min(1.0, analysed / fetched)
    execution_penalty = {
        "completed": 1.0, "completed_with_timeouts": 0.7,
        "degraded": 0.7, "partial_deadline_reached": 0.4,
    }.get(execution_status, 0.5)
    score = min(sample_quality, access_quality, execution_penalty)
    return {
        "score": round(score, 2),
        "method": "min(sample_quality, access_quality, execution_penalty); sample_quality = "
                  "min(1, pages/20) x min(1, templates/5). Identity confidence limits only off-site findings.",
        "components": {
            "sample_quality": round(sample_quality, 2),
            "access_quality": round(access_quality, 2),
            "execution_penalty": round(execution_penalty, 2),
            "identity_confidence": round(coverage.get("identity_confidence", 0.0) or 0.0, 2),
        },
    }
