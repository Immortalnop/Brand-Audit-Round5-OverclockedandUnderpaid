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
            + (f" The sample reached {coverage.get('sections_analyzed', 0)} of "
               f"{coverage['sections_discovered']} site sections (first path segment)."
               if coverage.get("sections_discovered") else "")
        )

    moved = coverage.get("start_redirect")
    if isinstance(moved, dict) and moved.get("audited_url"):
        out.append(
            f"The start URL {moved.get('requested_url')} redirects to another site; the audit followed that one "
            f"redirect and audited {moved.get('audited_url')} instead, under that site's own robots.txt. Findings "
            f"describe the site visitors actually reach."
        )

    if coverage.get("start_url_out_of_scope"):
        out.append(
            "The start URL is a login page. The audit never signs in, so that page was left out; audit a "
            "public page such as the home page for a full result."
        )
    out_of_scope = coverage.get("pages_out_of_scope", 0)
    if out_of_scope > 0:
        out.append(
            f"{out_of_scope} login or sign-in page(s) were fetched but left out of the analysis (see "
            f"coverage.out_of_scope_pages): the audit never signs in, and judging a login form as content "
            f"would produce false findings. Pages behind a login were not assessed."
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

    off_site = coverage.get("off_site_profiles") or {}
    if off_site.get("lookup") == "disabled":
        out.append(
            "Linked sameAs and review profiles were not fetched (OFF_SITE_LOOKUP=0), so whether they resolve "
            "and belong to the brand was not checked."
        )
    elif off_site.get("profiles_unverified"):
        out.append(
            f"{off_site['profiles_unverified']} linked off-site profile(s) could not be verified: the platform's "
            f"robots.txt forbids crawlers, it answered with a bot challenge or login wall, or the per-audit cap "
            f"was reached (see coverage.off_site_profiles). They are unchecked, not broken."
        )
    if off_site.get("review_platform_search") == "not_run" and not off_site.get("review_platforms_linked") \
            and off_site.get("business_kind") != "public" \
            and coverage.get("agent_corroboration_stage") != "ingested":
        out.append(
            "Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not "
            "searched for the brand: they block automated clients, no search provider was configured, and the "
            "agent stage (AG-06) was not supplied. Only profiles linked from the site were considered."
        )

    vitals = coverage.get("web_vitals") or {}
    if vitals and vitals.get("web_vitals_mode") != "field_data":
        lookup = vitals.get("web_vitals_field_lookup", "not_configured")
        reason = ("no PAGESPEED_API_KEY is configured" if lookup == "not_configured"
                  else f"the field-data lookup did not complete ({lookup})")
        out.append(
            f"Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and {reason}. "
            f"Web-vitals findings are estimates from markup patterns, not measurements."
        )

    llms_links = (coverage.get("llms_txt") or {}).get("llms_txt_link_outcomes") or {}
    unchecked_links = sum(v for k, v in llms_links.items() if k not in ("ok", "broken"))
    if unchecked_links:
        out.append(
            f"{unchecked_links} link(s) listed in llms.txt were not checked (another domain, robots rules, the "
            f"per-audit cap or a fetch error; see coverage.llms_txt)."
        )

    if (coverage.get("accessibility") or {}).get("accessibility_pages_analyzed"):
        out.append(
            "Colour contrast and tap-target size were judged only where inline styles set them; colours and "
            "sizes from stylesheets need a browser to compute and were not assessed."
        )
    weight = coverage.get("non_text_media") or {}
    unmeasured = weight.get("image_weight_candidates", 0) - weight.get("image_weight_probes", 0)
    if unmeasured > 0:
        out.append(
            f"{unmeasured} same-origin content image(s) were not measured for file size (per-audit cap of "
            f"{weight.get('image_weight_probe_cap', 0)} or remaining budget); cross-origin images are never "
            f"requested, so their weight is unassessed."
        )
    hreflang = coverage.get("hreflang") or {}
    if hreflang.get("hreflang_alternates_unverified"):
        out.append(
            f"{hreflang['hreflang_alternates_unverified']} hreflang alternate URL(s) were not crawled, so whether "
            f"they link back was not checked."
        )
    if (coverage.get("overlays") or {}).get("overlay_blocking_pages") or \
            (coverage.get("overlays") or {}).get("overlay_class_only_pages"):
        out.append(
            "Overlays were judged from the delivered HTML only; when and whether they appear on screen was not "
            "measured, so overlay findings are suspected."
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
      - sample_representativeness: how well the analyzed sample stands for the
        site. Every check looks for patterns that repeat across templates, so a
        bounded sample that reaches every section of a large site supports its
        conclusions far better than its raw page share suggests. It is the larger
        of:
          * crawl_completeness = pages_analyzed / pages_discovered (1.0 if
            nothing was discovered and nothing failed; 0.0 when no page could be
            analyzed: a fetched but unanalyzed page is no evidence), and
          * the smaller of section_coverage (sections with an analyzed page /
            sections discovered, a section being the first path segment) and
            sample_size (pages analyzed / min(pages discovered, 30)).
        Without section counts (an older or partial coverage block) it is
        crawl_completeness alone.
      - an execution penalty: 1.0 normally, 0.7 if the run completed with
        timeouts or was degraded, 0.4 if the deadline was reached before
        finishing
    take the minimum, not an average, because either one being poor should pull
    overall confidence down.

    Brand identity is reported beside the score (components and reasons), not
    inside it. A site with no Organization markup gets that as a finding; it does
    not make a complete crawl less trustworthy. Identity only gates the checks
    that depend on it (external corroboration, footprint and review search need
    an identity confidence of 0.85), and those say so when they skip.

    For a reader who is not an expert the result also carries `level` (high,
    medium or low), `limiting_factor` (the part that set the score), `reasons`
    (one plain-English sentence per part, identity included) and `explanation`
    (a short paragraph built from them). The score itself is unchanged by these
    fields.
    """
    discovered = coverage.get("pages_discovered", 0)
    analyzed = _analyzed_pages(coverage)
    if not analyzed and (discovered > 0 or coverage.get("pages_fetched_attempted", 0) > 0):
        crawl_completeness = 0.0
    else:
        crawl_completeness = 1.0 if discovered <= 0 else min(1.0, analyzed / discovered)
    components = {"crawl_completeness": round(crawl_completeness, 2)}
    representativeness = crawl_completeness
    sections = coverage.get("sections_discovered")
    if sections:
        section_coverage = min(1.0, coverage.get("sections_analyzed", 0) / sections)
        sample_size = min(1.0, analyzed / max(1, min(discovered, _ADEQUATE_SAMPLE_PAGES)))
        representativeness = max(crawl_completeness, min(section_coverage, sample_size))
        components.update(section_coverage=round(section_coverage, 2), sample_size=round(sample_size, 2))
    identity_confidence = coverage.get("identity_confidence", 0.0)
    execution_penalty = {
        "completed": 1.0, "completed_with_timeouts": 0.7,
        "degraded": 0.7, "partial_deadline_reached": 0.4,
    }.get(execution_status, 0.5)

    score = min(representativeness, execution_penalty)
    components.update(sample_representativeness=round(representativeness, 2),
                      identity_confidence=round(identity_confidence, 2),
                      execution_penalty=round(execution_penalty, 2))
    parts = {"execution_penalty": execution_penalty,
             "sample_representativeness": representativeness}
    reasons = {
        "sample_representativeness": _sample_reason(coverage, representativeness),
        "identity_confidence": _identity_reason(coverage, identity_confidence),
        "execution_penalty": _execution_reason(execution_status),
    }
    # The part that sets the score. On a tie the more basic cause is named first:
    # an unfinished run, then a thin sample.
    limiting = min(parts, key=lambda name: (parts[name], _PART_ORDER.index(name)))
    return {
        "score": round(score, 2),
        "level": confidence_level(score),
        "method": "min(sample_representativeness, execution_penalty), where "
                  "sample_representativeness = max(crawl_completeness, min(section_coverage, sample_size)) and "
                  "crawl_completeness = pages_analyzed / pages_discovered; a weak link caps the score rather than "
                  "being averaged out. identity_confidence is reported beside the score, not in it: it gates only "
                  "the checks that depend on the brand's identity",
        "components": components,
        "limiting_factor": limiting,
        "reasons": reasons,
        "explanation": _explanation(score, limiting, _weak_parts(parts, coverage), reasons,
                                    identity_confidence),
    }


# Pages enough to see each repeated template more than once on a typical site.
_ADEQUATE_SAMPLE_PAGES = 30

# A part at or above this value does not need explaining as a weakness.
_STRONG_PART = 0.8
_PART_ORDER = ("execution_penalty", "sample_representativeness", "identity_confidence")
_PART_LABELS = {"execution_penalty": "the audit run", "sample_representativeness": "the page sample",
                "identity_confidence": "the brand identity"}

_IDENTITY_REASONS = {
    "resolved": "The brand identity is clear: the Organization markup names one brand.",
    "parent_sub_brand": "The markup names related but different organizations (likely a parent brand and a "
                        "sub-brand), so statements about the brand may mix the two.",
    "multi_brand_conflict": "The markup names unrelated organizations, so it is unclear which brand the site "
                            "represents.",
    "conflicting_sameas": "The markup's sameAs links point to different profiles on the same platform, so the "
                          "brand's identity is in doubt.",
    "name_from_site_metadata": "No Organization markup was found; the brand name was read from the site's own "
                               "metadata (site name, title suffix or copyright line), which is less certain. Adding "
                               "Organization markup confirms it.",
    "no_organization_markup": "No Organization or Product JSON-LD was found on the analyzed pages, so the audit "
                              "could not confirm which brand the site belongs to. Adding Organization markup "
                              "raises this part.",
    "not_completed": "Brand identity could not be resolved in this run.",
}

_EXECUTION_REASONS = {
    "completed": "The audit run completed normally.",
    "completed_with_timeouts": "At least one analysis step ran out of time and was abandoned.",
    "degraded": "Part of the audit could not complete (a failed analysis step, or robots.txt could not be "
                "read, so pages were not fetched).",
    "partial_deadline_reached": "The audit time limit was reached before every step finished.",
}


def confidence_level(score):
    """Plain-English band for a confidence score."""
    return "high" if score >= _STRONG_PART else "medium" if score >= 0.5 else "low"


def identity_resolution(entity_result):
    """One word for how entity resolution went, read from its result: resolved,
    parent_sub_brand, multi_brand_conflict, conflicting_sameas,
    no_organization_markup or not_completed."""
    entity_result = entity_result or {}
    data = entity_result.get("data") or {}
    status = entity_result.get("status")
    if status in ("success", "partial") and "confidence" in data:
        return data.get("ambiguity_type") or "resolved"
    if status == "insufficient_evidence" and data.get("entity_type") == "unknown":
        return "no_organization_markup"
    return "not_completed"


def _sample_reason(coverage, value):
    analyzed = _analyzed_pages(coverage)
    discovered = coverage.get("pages_discovered", 0)
    if not analyzed:
        return "No page could be analyzed, so the site's content was not assessed."
    detail = f"the crawl analyzed {analyzed} of {discovered} discovered page(s)"
    if coverage.get("sections_discovered"):
        detail += (f" and reached {coverage.get('sections_analyzed', 0)} of {coverage['sections_discovered']} "
                   f"site section(s)")
    if value >= _STRONG_PART:
        return "The page sample stands for the site well: " + detail + "."
    return "The page sample is small or one-sided: " + detail + "."


def _identity_reason(coverage, value):
    resolution = coverage.get("identity_resolution")
    if resolution in _IDENTITY_REASONS:
        return _IDENTITY_REASONS[resolution]
    # Older coverage blocks carry only the number.
    if value >= 0.85:
        return _IDENTITY_REASONS["resolved"]
    return "The brand identity was only partly confirmed." if value > 0 else _IDENTITY_REASONS["not_completed"]


def _execution_reason(execution_status):
    return _EXECUTION_REASONS.get(execution_status, f"The audit run ended with status '{execution_status}'.")


def _analyzed_pages(coverage):
    return coverage.get("pages_analyzed", coverage.get("pages_fetched_attempted", 0))


def _weak_parts(parts, coverage):
    """Parts worth naming as weak. A sample with no analyzed page is always weak."""
    weak = {name for name, value in parts.items() if value < _STRONG_PART}
    if not _analyzed_pages(coverage):
        weak.add("sample_representativeness")
    return weak


def _explanation(score, limiting, weak, reasons, identity_confidence=None):
    text = f"Confidence is {confidence_level(score)} ({score:.2f})."
    if score >= _STRONG_PART and not weak:
        text += " The page sample and the audit run both hold up."
    else:
        text += (f" The weaker of its two parts sets the score, here {_PART_LABELS[limiting]}. "
                 f"{reasons[limiting]}")
        others = [reasons[name] for name in _PART_ORDER if name != limiting and name in weak]
        if others:
            text += " Also weak: " + " ".join(others)
    if identity_confidence is not None:
        # Identity is context for the score, never part of it.
        text += (" Brand identity (reported separately, not part of the score): "
                 + reasons["identity_confidence"])
    return (text + " The score rates how far the report speaks for the whole site; each finding has its own "
                   "confidence and status, and a problem seen on a page is still real on that page.")


def unfinished_confidence():
    """Confidence block for an audit whose worker never returned a report."""
    return {
        "score": 0.0,
        "level": "low",
        "method": "no completed audit evidence",
        "components": {},
        "limiting_factor": "execution_penalty",
        "reasons": {"execution_penalty": "The audit did not finish."},
        "explanation": "Confidence is low (0.00). The audit did not finish, so there is no evidence to rate and "
                       "no site-level conclusion can be drawn from this report.",
    }
