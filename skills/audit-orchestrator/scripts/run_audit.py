"""run_audit.py -- entrypoint: validate input, acquire once, schedule the DAG,
enforce budgets, merge, prioritize, generate recommendations, validate, emit the
report.

Skill folder names contain hyphens (agentskills.io convention) so this module wires
sibling scripts via sys.path rather than hyphenated package imports.
"""
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError, wait
from datetime import datetime, timezone
from time import monotonic
from urllib.parse import urlparse, urljoin
try:
    from dotenv import load_dotenv
except ImportError:  # standard-library default; .env loading is optional
    def load_dotenv(*_args, **_kwargs):
        return False

load_dotenv()  # optional local-development convenience; production uses environment variables


def _progress(msg):
    """Progress to stderr only. The CLI enables it by default; API callers use
    AUDIT_PROGRESS=1. Stdout stays pure JSON for the evaluation harness.
    A long crawl of a large site is work, not a hang, and this makes that visible.
    """
    if os.environ.get("AUDIT_PROGRESS") == "1":
        sys.stderr.write("[audit] " + msg + "\n")
        sys.stderr.flush()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _bootstrap import ensure_paths  # noqa: E402  (A24: clear error if installed outside the marketplace)
_ROOT = ensure_paths()

from constants import DEFAULT_LIMITS
from models import make_deadline, _jsonable
from instrumentation import Instrumentation
from capabilities import detect_capabilities, capability_report

from acquire_site import acquire_site
from merge_findings import merge_findings
from prioritize_findings import prioritize_findings
from generate_recommendations import generate_recommendations
from validate_report import validate_report
from execution_summary import derive_execution_status, derive_limitations, overall_confidence

from analyze_access import analyze_access
from validate_structured_data import validate_structured_data
from analyze_nontext_facts import analyze_nontext_facts
from scoring import ScoringContext, apply_scoring
from check_catalog import meta_for
from check_helpers import content_pages
from structured_data import iter_nodes, types_of
from generate_recommendations import build_action_plan, top_actions, quick_wins
from whats_working import whats_working
from fix_snippets import attach_fix_snippets
from analyze_citation_schema import analyze_citation_schema
from analyze_contact_markup import analyze_contact_markup
from update_signals import check_sitemap_lastmod
from check_entity_links import check_entity_links
from analyze_crawlability import analyze_crawlability
from analyze_directives import analyze_directives
from analyze_metadata import analyze_metadata
from analyze_performance import analyze_performance
from analyze_answer_content import analyze_answer_content
from analyze_rendering import analyze_rendering
from analyze_machine_readability import analyze_machine_readability
from check_ai_crawler_access import check_ai_crawler_access
from check_llms_txt import check_llms_txt

from extract_claims import extract_claims
from identify_important_facts import identify_important_facts
from resolve_entity_identity import resolve_entity_identity
from assess_freshness import assess_freshness
from corroborate_claims import corroborate_claims
from assess_external_footprint import assess_external_footprint

from build_site_graph import build_site_graph
from analyze_engagement import analyze_engagement

from ingest_agent_findings import ingest_agent_findings

# Per-worker timeout used only to *detect and record* a hung specialist so the
# instrumentation layer can report it; the shared AuditDeadline remains the source
# of truth for stage budgets.
_WORKER_TIMEOUT_S = 30


def validate_input(url: str) -> str:
    p = urlparse(url)
    if not p.scheme:
        url = "https://" + url
        p = urlparse(url)
    if not p.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return url


def _await_result(future, name, stage, instrumentation):
    try:
        return future.result(timeout=_WORKER_TIMEOUT_S)
    except FutureTimeoutError:
        instrumentation.record_worker_timeout(stage, name)
        return {"skill": name, "status": "insufficient_evidence", "findings": [], "metrics": {},
                "warnings": [f"specialist '{name}' exceeded {_WORKER_TIMEOUT_S}s and was abandoned"],
                "coverage": {"pages_analyzed": 0, "pages_skipped": 0,
                             "queries_attempted": 0, "queries_completed": 0}}
    except Exception as exc:
        return {"skill": name, "status": "failed", "findings": [], "metrics": {},
                "warnings": [f"specialist failed: {exc}"],
                "coverage": {"pages_analyzed": 0, "pages_skipped": 0,
                             "queries_attempted": 0, "queries_completed": 0}}


def _run_jobs(jobs, deadline, limits, instrumentation, stage):
    pool = ThreadPoolExecutor(max_workers=limits.MAX_ANALYSIS_WORKERS)
    futures = {name: pool.submit(fn) for name, fn in jobs.items()}
    budget = max(0., min(_WORKER_TIMEOUT_S, deadline.remaining_seconds() - min(20., limits.FINALIZATION_RESERVE_S, deadline.remaining_seconds() * .1)))
    done, pending = wait(futures.values(), timeout=budget)
    results = {}
    for name, future in futures.items():
        if future in done:
            results[name] = _await_result(future, name, stage, instrumentation)
        else:
            instrumentation.record_worker_timeout(stage, name)
            future.cancel()
            results[name] = {"skill": name, "status": "insufficient_evidence", "findings": [], "metrics": {}, "data": {}, "warnings": [f"{name}: stage deadline reached"]}
    pool.shutdown(wait=False, cancel_futures=True)
    # The outer process watchdog stops abandoned workers after the report is received.
    return results


def run_independent_batch(artifacts, deadline, limits, capabilities, instrumentation):
    instrumentation.start_stage("independent_batch")
    jobs = {
        "access": lambda: analyze_access(artifacts, deadline),
        "structured_data_validity": lambda: validate_structured_data(artifacts, deadline),
        "nontext_facts": lambda: analyze_nontext_facts(artifacts, deadline),
        "crawlability": lambda: analyze_crawlability(artifacts, deadline),
        "directives": lambda: analyze_directives(artifacts, deadline),
        "metadata": lambda: analyze_metadata(artifacts, deadline),
        "performance": lambda: analyze_performance(artifacts, deadline),
        "rendering": lambda: analyze_rendering(artifacts, deadline, limits, capabilities),
        "machine_readability": lambda: analyze_machine_readability(artifacts, deadline),
        "ai_crawler_access": lambda: check_ai_crawler_access(artifacts, deadline),
        "llms_txt": lambda: check_llms_txt(artifacts, deadline),
        "citation_schema": lambda: analyze_citation_schema(artifacts, deadline),
        "contact_markup": lambda: analyze_contact_markup(artifacts, deadline),
        "sitemap_lastmod": lambda: check_sitemap_lastmod(artifacts, deadline),
        "entity_links": lambda: check_entity_links(artifacts, deadline),
        "claims": lambda: extract_claims(artifacts, deadline),
        "entity_identity": lambda: resolve_entity_identity(artifacts, deadline),
        "site_graph": lambda: build_site_graph(artifacts, deadline),
    }
    results = _run_jobs(jobs, deadline, limits, instrumentation, "independent_batch")
    instrumentation.end_stage("independent_batch")
    return results


def run_dependent_batch(facts, entity_identity, artifacts, site_graph, rendering_result,
                         deadline, limits, instrumentation, capabilities):
    instrumentation.start_stage("dependent_batch")
    jobs = {
        "freshness": lambda: assess_freshness(facts, artifacts, deadline),
        "answer_content": lambda: analyze_answer_content(artifacts, entity_identity, deadline),
        "corroboration": lambda: corroborate_claims(facts, entity_identity, artifacts, deadline, limits, instrumentation),
        "footprint": lambda: assess_external_footprint(artifacts, entity_identity, deadline, limits, instrumentation),
        "engagement": lambda: analyze_engagement(artifacts, site_graph, rendering_result, deadline),
        "agent_corroboration": lambda: ingest_agent_findings(artifacts, entity_identity, deadline, capabilities),
    }
    results = _run_jobs(jobs, deadline, limits, instrumentation, "dependent_batch")
    instrumentation.end_stage("dependent_batch")
    return results


_ABOUT_INTENTS = ("about", "about-us", "company", "team")
# "About", "About us", "About <Brand>" (up to three words), "Who we are", "Our story".
_ABOUT_TEXT = re.compile(r"^\s*(about(\s+[\w&.'-]+){0,3}|who we are|our (story|company)|company)\s*$", re.I)


def _about_link_seen(artifacts, pages):
    """Was any link to an About-type page observed anywhere in the sample?"""
    from url_keys import intent_of
    for p in pages:
        for href, text in (p.features or {}).get("anchors", ()):
            if (href and intent_of(urljoin(p.final_url or p.url, href)) in _ABOUT_INTENTS) or _ABOUT_TEXT.match(text or ""):
                return urljoin(p.final_url or p.url, href)
    return None


def opening_passage(page, limit=1500):
    """The page's own opening, without navigation boilerplate: H1, meta
    description, then the first paragraphs of body copy. This is what an
    assistant would lift for "what is <brand>?" and what AG-01 judges."""
    f = page.features or {}
    parts = []
    if page.headings:
        parts.append(page.headings[0])
    if page.meta_description:
        parts.append(page.meta_description.strip())
    for para in f.get("opening_paragraphs") or ():
        para = " ".join(str(para).split())
        if len(para) >= 40 and para not in parts:
            parts.append(para)
        if sum(len(x) for x in parts) >= limit:
            break
    text = "\n\n".join(parts)
    return text[:limit]


def section_passage(page, fragment=None, limit=1500):
    """When the About link is a fragment (/help/#about), the About text is a
    section of an acquired page. The parser captures the prose under an
    "About ..." heading at acquisition time, independent of the visible-text cap
    (html_features). If nothing was captured, return None: guessing from the
    (possibly truncated) page text could hand the agent a table-of-contents entry
    or an unrelated paragraph to judge."""
    captured = (page.features or {}).get("about_section")
    return captured[:limit] if captured else None


def build_agent_brief(artifacts, identity, facts):
    """Everything the calling agent needs for the entity-corroboration stage (A3),
    taken from the acquired snapshot, so the agent never has to re-fetch the site.

    AG-01 needs a specific passage: the About page's opening, or the homepage's
    when the site has no About page. about_source says which one was supplied
    and why, so the agent never judges the wrong page:
      about_page                   an About-type page was acquired; judge it
      about_section                the About link points to a section of an
                                   acquired page (/help/#about); judge that section
      homepage_no_about_page       no link to an About page exists; judging the
                                   homepage is what the check prescribes
      about_section_not_captured   the About section's page was acquired but the
                                   section text could not be isolated; not assessed
      homepage_about_not_acquired  an About link was seen but the page could not
                                   be acquired (robots, budget, error); AG-01 must
                                   be recorded as not assessed, not judged on the
                                   homepage
      none                         no content page was acquired at all
    """
    from url_keys import intent_of
    data = (identity or {}).get("data", {}) or {}
    pages = content_pages(artifacts, require_features=False)
    from url_keys import visit_key
    about = next((p for p in pages if p.page_type == "about" or intent_of(p.url) in _ABOUT_INTENTS), None)
    home = next((p for p in pages if p.page_type == "home"), None)
    about_link = None if about else _about_link_seen(artifacts, pages)
    section = None
    if about_link:
        # The About link may point at a page that WAS acquired (often a section,
        # e.g. /help/#about): resolve it without the fragment before deciding.
        target = next((p for p in pages if visit_key(p.url) == visit_key(about_link)
                       or visit_key(p.final_url or "") == visit_key(about_link)), None)
        if target is not None:
            fragment = about_link.split("#", 1)[1] if "#" in about_link else ""
            section = (target, section_passage(target, fragment) if fragment else None)
    if about:
        source, passage_page = "about_page", about
    elif section is not None and section[1]:
        source, passage_page = "about_section", section[0]
    elif section is not None and "#" not in (about_link or ""):
        source, passage_page = "about_page", section[0]
    elif section is not None:
        # The About section lives on an acquired page but its text could not be
        # isolated: not assessable, rather than judging the wrong passage.
        source, passage_page = "about_section_not_captured", section[0]
    elif home and not about_link:
        source, passage_page = "homepage_no_about_page", home
    elif home:
        source, passage_page = "homepage_about_not_acquired", home
    else:
        source, passage_page = "none", None
    types = sorted({t for p in pages for n in iter_nodes(p.jsonld_blocks) for t in types_of(n)})[:15]
    category_hint = {"jsonld_types": types,
                     "home_meta_description": (home.meta_description if home else None),
                     "home_h1": (home.headings[0] if home and home.headings else None)}
    brand = data.get("canonical_name") or ""
    category_word = (category_hint["home_h1"] or category_hint["home_meta_description"] or "")[:60]
    return {
        "site": artifacts.site_url, "domain": artifacts.normalized_origin,
        "brand_name": brand, "aliases": data.get("aliases", []),
        "identity_confidence": data.get("confidence", 0.0), "identity_sources": data.get("identity_sources", []),
        "same_as": data.get("same_as_urls", []), "category_hint": category_hint,
        "ag01": {
            "about_source": source,
            "passage_url": passage_page.url if passage_page else None,
            "about_link_seen": about_link,
            "assessable": source in ("about_page", "about_section", "homepage_no_about_page"),
            "opening_passage": ((section[1] if section is not None and section[1] else opening_passage(passage_page))
                                if passage_page else ""),
            "raw_visible_excerpt": (passage_page.visible_text or "")[:1200] if passage_page else "",
        },
        # Kept for agents written against the first Round-5 brief.
        "about_url": passage_page.url if passage_page else None,
        "about_text": ((section[1] if section is not None and section[1] else opening_passage(passage_page))
                       if passage_page else ""),
        "key_claims": [{"value": str(c.get("value"))[:120], "type": c.get("type"), "source": c.get("source")}
                       for c in (facts or {}).get("data", {}).get("facts", [])[:10]],
        "suggested_queries": ([f'"{brand}" {category_word}'.strip(), f'"{brand}" site:reddit.com OR site:quora.com',
                               f'"{brand}" reviews', f'"{brand}" {artifacts.normalized_origin.split("//")[-1]}']
                              if brand else []),
        "ag04": {"images": _fact_images(pages)},
        "ag05": _namesake_brief(artifacts, brand, category_word),
        "ag06": _platform_brief(artifacts, pages, brand),
        "search_budget": {"max_searches": 8, "max_seconds": 150},
        "output_contract": "Write a JSON array of findings (AG-01 to AG-06) as described in "
                           "skills/entity-corroboration-agent/SKILL.md, or [] if nothing fires.",
    }


def _fact_images(pages):
    """AG-04: images that look like fact carriers on text-poor pages, with absolute
    URLs, for the agent to read with its own vision (scripts never read pixels)."""
    from analyze_nontext_facts import fact_image_candidates
    out = []
    for page, img, why in fact_image_candidates(pages)[:6]:
        src = img.get("src") or ""
        if not src or src.startswith("data:"):
            continue
        out.append({"page": page.url, "image": urljoin(page.final_url or page.url, src), "alt": img.get("alt"),
                    "why": why})
    return out


def _namesake_brief(artifacts, brand, category_word):
    """AG-05: the declared knowledge-graph links and the queries that find namesakes."""
    from check_entity_links import organization_markup, kg_links
    _, same_as = organization_markup(artifacts)
    wikidata, wikipedia, _ = kg_links(same_as)
    return {"declared_wikidata": [u for u, _ in wikidata], "declared_wikipedia": [u for u, _, _ in wikipedia],
            "queries": ([f'"{brand}" -site:{urlparse(artifacts.normalized_origin).hostname}',
                         f'"{brand}" site:wikidata.org OR site:wikipedia.org'] if brand else [])}


_PLATFORMS = {
    "local": ["Google Business Profile", "Yelp", "Tripadvisor", "an industry directory"],
    "software": ["G2", "Capterra", "TrustRadius", "Product Hunt"],
    "public": [],
    "general": ["Trustpilot", "Crunchbase", "an industry directory"],
}


def _platform_brief(artifacts, pages, brand):
    """AG-06: which review or directory platforms suit this kind of business.
    Public bodies (schools, government) are not reviewed on consumer platforms."""
    from structured_data import LOCAL_BUSINESS_TYPES
    types = {t for p in pages for n in iter_nodes(p.jsonld_blocks) for t in types_of(n)}
    host = urlparse(artifacts.normalized_origin).hostname or ""
    if types & LOCAL_BUSINESS_TYPES:
        kind = "local"
    elif types & {"SoftwareApplication", "WebApplication", "MobileApplication"} or any(p.page_type == "software" for p in pages):
        kind = "software"
    elif types & {"GovernmentOrganization", "EducationalOrganization", "CollegeOrUniversity", "School"} \
            or re.search(r"\.(gov|mil|edu|ac)(\.[a-z]{2})?$", host):
        kind = "public"
    else:
        kind = "general"
    return {"business_kind": kind, "platforms": _PLATFORMS[kind],
            "queries": [f'"{brand}" {p}' for p in _PLATFORMS[kind] if not p.startswith("an ")][:3] if brand else []}


def finalize_findings(findings, ctx):
    """Score, split core vs hygiene (A17), order and number. Shared by run_audit
    and finalize_report so both paths produce identical structure."""
    for f in findings:
        apply_scoring(f, ctx)
    core, hygiene = [], []
    for f in findings:
        tier = f.get("tier_override") or meta_for(f.get("check_id") or "").get("tier", "core")
        f.pop("tier_override", None)
        f["tier"] = tier
        (hygiene if tier == "hygiene" else core).append(f)
    core = prioritize_findings(core)
    hygiene = prioritize_findings(hygiene)
    for idx, f in enumerate(core, 1):
        f["id"] = f"F-{idx:03d}"
    for idx, f in enumerate(hygiene, 1):
        f["id"] = f"H-{idx:03d}"
    return core, hygiene


def _run_audit_impl(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets: bool = False,
                    seed_urls=None) -> dict:
    """allow_private_targets defaults to False (safe): the CLI and any production
    caller never sets it. It exists only so tests can point the audit at a local
    ThreadingHTTPServer on 127.0.0.1 without weakening the default SSRF policy."""
    site_url = validate_input(site_url)
    deadline = make_deadline(limits)
    instrumentation = Instrumentation()
    capabilities = detect_capabilities()

    _progress("acquiring " + site_url)
    artifacts = acquire_site(site_url, deadline, limits, instrumentation,
                              allow_private_targets=allow_private_targets, seed_urls=seed_urls)
    _progress("acquired " + str(len(artifacts.pages)) + " page(s); running analysis")

    independent = run_independent_batch(artifacts, deadline, limits, capabilities, instrumentation)

    # Mandatory sequential step, wired into the executable schedule -- not only the
    # architecture diagram. Consumes extract_claims' output.
    instrumentation.start_stage("identify_important_facts")
    facts = identify_important_facts(independent["claims"], deadline)
    instrumentation.end_stage("identify_important_facts")

    dependent = run_dependent_batch(
        facts, independent["entity_identity"], artifacts,
        independent["site_graph"], independent["rendering"], deadline, limits, instrumentation,
        capabilities,
    )
    _progress("analysis complete; merging and validating report")

    skill_results = [
        independent["access"], independent["structured_data_validity"], independent["nontext_facts"],
        independent["metadata"], independent["performance"], dependent["answer_content"],
        independent["crawlability"], independent["directives"], independent["rendering"], independent["machine_readability"],
        independent["ai_crawler_access"], independent["llms_txt"],
        independent["citation_schema"], independent["contact_markup"],
        independent["sitemap_lastmod"], independent["entity_links"],
        dependent["freshness"], dependent["corroboration"], dependent["footprint"], dependent["engagement"],
        dependent["agent_corroboration"],
    ]

    identity_conf = independent["entity_identity"].get("data", {}).get("confidence", 0.0)
    ctx = ScoringContext.from_artifacts(artifacts, identity_confidence=identity_conf)
    merged = merge_findings(skill_results)
    prioritized, hygiene = finalize_findings(merged, ctx)
    attach_fix_snippets(prioritized + hygiene, artifacts, independent["entity_identity"])
    recommendations = generate_recommendations(skill_results, prioritized + hygiene, artifacts=artifacts)
    action_plan = build_action_plan(prioritized)

    memory_peak_mb = instrumentation.stop_memory_tracking_mb()
    telemetry = instrumentation.as_dict(memory_peak_mb)

    acq_coverage = artifacts.acquisition_metadata.get("coverage", {})
    coverage = {
        # Factual, non-equated coverage counts:
        # discovered/fetched/analyzed are different numbers and must not collapse
        # into one len(pages) reused three times.
        "pages_discovered": acq_coverage.get("urls_discovered", len(artifacts.pages)),
        "pages_fetched_attempted": acq_coverage.get("urls_fetched_attempted", len(artifacts.pages)),
        "pages_fetched_ok": acq_coverage.get("urls_fetched_ok", len(artifacts.pages)),
        "pages_analyzed": acq_coverage.get("urls_analyzed", len(artifacts.pages)),
        "pages_blocked": acq_coverage.get("urls_blocked", 0),
        "robots_permission": "unknown" if artifacts.robots_data.get("conservative_fail_closed") else "disallowed" if artifacts.robots_data.get("general_disallow") else "evaluated" if artifacts.robots_data.get("status") in ("ok","absent","unavailable_4xx") else "unknown",
        "transport_diagnostics": artifacts.acquisition_metadata.get("transport_diagnostics", []),
        "transport_environment": artifacts.acquisition_metadata.get("transport_environment", {}),
        "robots_attempt_outcomes": artifacts.robots_data.get("attempt_outcomes", []),
        "pages_timed_out": acq_coverage.get("urls_timed_out", 0),
        "pages_failed_other": acq_coverage.get("urls_failed_other", 0),
        "pages_never_attempted": acq_coverage.get("urls_never_attempted", 0),
        "pages_skipped": telemetry["pages_skipped"],
        "pages_challenged": acq_coverage.get("urls_challenged", 0),
        "pages_out_of_scope": acq_coverage.get("urls_out_of_scope", 0),
        "out_of_scope_pages": acq_coverage.get("out_of_scope_pages", []),
        "templates_sampled": acq_coverage.get("templates_sampled", 0),
        "pages_per_template": acq_coverage.get("pages_per_template", {}),
        "key_intents_found": acq_coverage.get("key_intents_found", []),
        "asset_links_found": acq_coverage.get("asset_links_found", 0),
        "targeted_urls": list(seed_urls or []),
        "skip_reason_counts": acq_coverage.get("skip_reason_counts", {}),
        "rendered_pages": independent["rendering"].get("metrics", {}).get("rendered_pages", 0),
        "external_claims_checked": dependent["corroboration"].get("metrics", {}).get("claims_checked", 0),
        "external_footprint_queries": dependent["footprint"].get("metrics", {}).get("queries_attempted", 0),
        "agent_corroboration_stage": dependent["agent_corroboration"].get("metrics", {}).get("agent_stage", "not_supplied"),
        "external_fetches": telemetry["external_fetches_attempted"],
        "identity_confidence": independent["entity_identity"].get("data", {}).get("confidence", 0.0),
        "memory_budget_used_mb": memory_peak_mb,  # None if unmeasured, never a fabricated 0
        "runtime_seconds": round(monotonic() - deadline.started_monotonic, 3),  # measured, not derived from the budget
        "deadline_reached": deadline.expired(),
        "capabilities": capability_report(capabilities),
        "instrumentation": telemetry,
    }

    report = {
        "site": site_url,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "summary": {},
        "coverage": coverage,
        "warnings": list(artifacts.warnings) + [w for result in skill_results for w in result.get("warnings", [])],
        "findings": prioritized,
        "action_plan": action_plan,
        "recommendations": recommendations,
        "hygiene_findings": hygiene,
        "scoring_context": ctx.as_dict(),
        "agent_stage": {
            "status": dependent["agent_corroboration"].get("metrics", {}).get("agent_stage", "not_supplied"),
            "brief": build_agent_brief(artifacts, independent["entity_identity"], facts),
            "next_step": "If a web-search tool is available, follow skills/entity-corroboration-agent/SKILL.md "
                         "using this brief, then run skills/audit-orchestrator/scripts/finalize_report.py.",
        },
    }

    # Never-empty, never-misleading report fields: every
    # audit -- success, degraded, or deadline-truncated -- gets a real
    # execution_status, a limitations list derived from actual telemetry (not
    # boilerplate), and an overall confidence score with its method shown.
    execution_status = derive_execution_status(deadline, skill_results, telemetry["worker_timeout_events"])
    if artifacts.robots_data.get("conservative_fail_closed") and execution_status == "completed":
        execution_status = "degraded"
    report["execution_status"] = execution_status
    report["limitations"] = derive_limitations(artifacts, capabilities, coverage, execution_status)
    report["confidence"] = overall_confidence(coverage, execution_status)

    report["coverage_limited"] = {"sample_only": coverage["pages_never_attempted"] > 0,
                                  "pages_not_analyzed": max(0, coverage["pages_discovered"] - coverage["pages_analyzed"]),
                                  "unassessed_capabilities": [k for k, v in capabilities.items() if not v]}
    report["top_actions"] = top_actions(action_plan)
    report["quick_wins"] = quick_wins(action_plan)
    report = validate_report(report, strict_catalog=True)
    # Passed checks are computed against the validated report, so the section can
    # never contradict a finding, hygiene item or recommendation that shipped.
    results_by_name = {**independent, **dependent}
    report["whats_working"] = whats_working(artifacts, results_by_name,
                                            report["findings"] + report.get("hygiene_findings", []) + report["recommendations"])
    return _jsonable(report)


def run_audit(site_url: str, limits=DEFAULT_LIMITS, allow_private_targets=False, seed_urls=None) -> dict:
    """Public bounded API. A stalled DNS call or analysis cannot hold the caller indefinitely."""
    from subprocess_isolation import run_isolated
    from dataclasses import replace
    import math
    if not math.isfinite(limits.TOTAL_AUDIT_TIMEOUT_S) or limits.TOTAL_AUDIT_TIMEOUT_S <= 0:
        raise ValueError("Audit timeout must be a positive finite number")
    limits=replace(limits,TOTAL_AUDIT_TIMEOUT_S=min(270.,limits.TOTAL_AUDIT_TIMEOUT_S))
    site_url = validate_input(site_url)
    _progress("started; total limit " + str(limits.TOTAL_AUDIT_TIMEOUT_S) + "s")
    # seed_urls is only passed when used, so the worker signature stays compatible
    # with callers (and tests) that replace _run_audit_impl with a 3-argument function.
    worker_args = (site_url, limits, allow_private_targets) + ((seed_urls,) if seed_urls else ())
    result = run_isolated(_run_audit_impl, args=worker_args,
                          timeout_s=limits.TOTAL_AUDIT_TIMEOUT_S,
                          on_wait=lambda elapsed: _progress(f"working ({elapsed:.0f}s elapsed); Ctrl+C cancels cleanly"))
    if result.ok:
        return result.value
    # A timeout is an execution limitation, never a fabricated site defect.
    return validate_report({
        "site": site_url, "audited_at": datetime.now(timezone.utc).isoformat(), "summary": {},
        "findings": [], "hygiene_findings": [], "action_plan": [], "top_actions": [], "quick_wins": [], "whats_working": [],
        "recommendations": generate_recommendations([], []),
        "agent_stage": {"status": "not_supplied", "brief": None},
        "coverage": {"pages_discovered": 0, "pages_analyzed": 0, "deadline_reached": result.timed_out,
                     "measurements_unavailable": True, "cancelled": result.cancelled},
        "execution_status": "partial_deadline_reached" if result.timed_out else "degraded",
        "limitations": ["The audit worker did not return a complete report. No site-level conclusions can be drawn.", result.error or "Worker failed"],
        "confidence": {"score": 0.0, "level": "low", "limiting_factor": "execution_penalty",
                       "method": "no completed audit evidence",
                       "explanation": "Confidence is low (0.00): the audit did not finish, so no site-level conclusion "
                                      "can be drawn from this report."},
        "warnings": [result.error or "Worker failed"]}, strict_catalog=True)


def write_outputs(report, out_dir):
    """--out-dir: report.json, agent_brief.json and report.md side by side."""
    import json
    from render_report import render_markdown
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    brief = (report.get("agent_stage") or {}).get("brief")
    if brief is not None:
        with open(os.path.join(out_dir, "agent_brief.json"), "w", encoding="utf-8") as fh:
            json.dump(brief, fh, indent=2, default=str)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(report))


def explain_run(report):
    """--explain: how the audit spent its budget, from the telemetry this run
    recorded. It reports measured behaviour, never a restated design claim:
    acquisition is where the network cost sits, every analysis stage is CPU over
    one immutable snapshot, and the skipped URLs are the politeness rules as data.
    """
    cov = report.get("coverage") or {}
    tel = cov.get("instrumentation") or {}
    limits = DEFAULT_LIMITS
    stages = tel.get("stage_timings_s") or {}
    total_stage = sum((s or {}).get("duration", 0) for s in stages.values()) or 0
    acquisition = (stages.get("acquisition") or {}).get("duration", 0)
    rows = [
        ("runtime", f"{cov.get('runtime_seconds', 0)} s (budget {limits.TOTAL_AUDIT_TIMEOUT_S:g} s)"),
        ("requests", f"{tel.get('requests_attempted', 0)} attempted, {tel.get('requests_completed', 0)} completed, "
                     f"{tel.get('requests_failed', 0)} failed (budget {limits.MAX_TOTAL_HTTP_REQUESTS})"),
        ("bytes downloaded", f"{(tel.get('bytes_downloaded', 0) / 1_048_576):.2f} MiB "
                             f"(budget {limits.MAX_TOTAL_BYTES // 1_048_576} MiB)"),
        ("pages", f"{cov.get('pages_analyzed', 0)} analysed of {cov.get('pages_fetched_attempted', 0)} fetched; "
                  f"{cov.get('templates_sampled', 0)} distinct templates; {cov.get('pages_discovered', 0)} discovered"),
        ("excluded", f"{cov.get('pages_challenged', 0)} bot-challenged, {cov.get('pages_out_of_scope', 0)} login page(s)"),
        ("stage timings", "; ".join(f"{name} {(s or {}).get('duration', 0):.2f} s" for name, s in stages.items()) or "-"),
        ("acquisition share", f"{(acquisition / total_stage * 100):.0f}% of measured stage time, and all of the "
                              "network cost: every analysis stage is CPU over one immutable snapshot"
         if total_stage else "-"),
        ("skips", ", ".join(f"{n} {reason}" for reason, n in (cov.get("skip_reason_counts") or {}).items()) or "none"),
        ("rendering", "headless browser" if cov.get("rendered_pages") else "heuristic only (no browser available)"),
        ("agent stage", (report.get("agent_stage") or {}).get("status", "not_supplied")),
        ("confidence", f"{(report.get('confidence') or {}).get('score')} "
                       f"({(report.get('confidence') or {}).get('level')}), limited by "
                       f"{(report.get('confidence') or {}).get('limiting_factor')}"),
    ]
    width = max(len(name) for name, _ in rows)
    out = ["[explain] how this audit spent its budget (measured, not configured):"]
    out += [f"[explain]   {name.ljust(width)}  {value}" for name, value in rows]
    return "\n".join(out)


def console_summary(report):
    """Ten-line human summary on stderr; stdout stays pure JSON (A25)."""
    s = report.get("summary", {})
    lines = [f"[audit] {report.get('site')} -- {report.get('execution_status')}, confidence "
             f"{(report.get('confidence') or {}).get('score')}",
             f"[audit] findings: {s.get('total_findings', 0)} (critical {s.get('critical', 0)}, high {s.get('high', 0)}, "
             f"medium {s.get('medium', 0)}, low {s.get('low', 0)}); hygiene items: {s.get('hygiene_items', 0)}"]
    for a in report.get("top_actions", [])[:5]:
        lines.append(f"[audit]   {a.get('finding_id')} [{a.get('severity')}/{a.get('effort')} effort] {a.get('summary')}")
    return "\n".join(lines)


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(
        description="Brand AI-Readiness Audit. Emits one JSON report to stdout.")
    parser.add_argument("site", help="Target URL or bare domain to audit (required).")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Override the total audit wall-clock cap in seconds "
                             "(default 270, handout limit 300). Lower it for a quick "
                             "interactive run on a large site.")
    parser.add_argument("--out-dir", default=None,
                        help="Also write report.json, agent_brief.json and report.md into this directory.")
    parser.add_argument("--urls", default=None,
                        help="File with one same-site URL per line: audit exactly these pages (e.g. the landing "
                             "pages for prompts a brand is losing) instead of a sampled crawl. Still robots-checked.")
    parser.add_argument("-v", "--progress", action="store_true",
                        help="Progress on stderr. This is already the default; the flag is kept so existing "
                             "command lines (e.g. the Round-4 REPLAY file) keep working.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress on stderr; JSON output is unchanged.")
    parser.add_argument("--explain", action="store_true",
                        help="Print how the run spent its budget (timings, requests, sampling, skips) on stderr. "
                             "The same numbers are in coverage.instrumentation; JSON output is unchanged.")
    parsed = parser.parse_args(argv)
    import math
    if parsed.timeout is not None and (not math.isfinite(parsed.timeout) or parsed.timeout<=0):
        parser.error("--timeout must be a positive finite number")
    os.environ["AUDIT_PROGRESS"] = "0" if parsed.quiet else "1"
    active_limits = DEFAULT_LIMITS
    if parsed.timeout is not None:
        from dataclasses import replace as _dc_replace
        active_limits = _dc_replace(DEFAULT_LIMITS, TOTAL_AUDIT_TIMEOUT_S=parsed.timeout)
    seeds = None
    if parsed.urls:
        with open(parsed.urls, encoding="utf-8") as fh:
            seeds = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")][:50]
    try:
        report = run_audit(parsed.site, limits=active_limits, seed_urls=seeds)
        if parsed.out_dir:
            write_outputs(report, parsed.out_dir)
        print(json.dumps(report, indent=2, default=str))
        if parsed.explain:
            # Explicitly asked for, so it prints even under --quiet.
            sys.stderr.write(explain_run(report) + "\n")
        if not parsed.quiet:
            sys.stderr.write(console_summary(report) + "\n")
        if report.get("coverage",{}).get("cancelled"):raise SystemExit(130)
    except KeyboardInterrupt:
        print("[audit] cancelled",file=sys.stderr)
        raise SystemExit(130)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
