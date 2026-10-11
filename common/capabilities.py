"""capabilities.py -- central registry distinguishing what actually runs in this
deployment from what is architecturally described but environment-gated.

Three tiers, surfaced in every report's coverage.capabilities block:
  - "executable"  : runs today, no external dependency beyond what's already used.
  - "fallback"     : has a real primary implementation, but degrades to a documented
                     fallback when a dependency (headless browser, search provider,
                     outbound network) is unavailable -- the fallback itself is
                     executable and evidence-honest (insufficient_evidence), never
                     a silent skip.
  - "optional"     : the enhanced path only; whether it actually ran this audit.
"""
import importlib.util
import os
from types import MappingProxyType

from field_vitals import lookup_enabled as field_lookup_enabled

CHECK_TIERS = MappingProxyType({
    "robots_and_ai_crawler_access": "executable",
    "crawlability": "executable",
    "machine_readability_jsonld": "executable",
    "llms_txt_presence": "executable",
    "sitemap_discovery": "executable",
    "claim_extraction_heuristic": "executable",
    "entity_resolution_from_jsonld": "executable",
    "site_graph_engagement": "executable",
    "freshness_from_dated_facts": "executable",
    "dedup_merge_prioritize_validate": "executable",
    "rendering_gap_heuristic": "executable",
    "non_text_svg_and_pdf_text": "executable",
    "structured_date_freshness": "executable",
    "sitemap_lastmod_and_last_modified_freshness": "executable",
    "knowledge_graph_link_check": "executable",
    "knowledge_graph_entity_verification": "fallback",
    "alt_text_quality": "executable",
    "media_transcripts_and_schema": "executable",
    "citation_schema_types": "executable",
    "author_eeat_signals": "executable",
    "llms_txt_structure_and_links": "executable",
    "llms_full_txt_probe": "executable",
    "same_as_static_validation": "executable",
    "review_platform_links": "executable",
    "web_vitals_static_estimate": "executable",
    "hreflang_annotations": "executable",
    "noscript_fallback": "executable",
    "canvas_svg_icon_font_text": "executable",
    "image_caption_context": "executable",
    "image_weight_measurement": "executable",
    "accessibility_html_checks": "executable",
    "overlay_and_consent_detection": "executable",
    "answer_format_checks": "executable",
    "location_and_audience_signals": "executable",
    "context_retention_checks": "executable",
    "expired_offer_dates": "executable",
    "on_site_fact_consistency": "executable",
    "ai_crawler_purpose_labels": "executable",
    "fix_snippets": "executable",
    "impact_effort_matrix": "executable",
    "same_as_profile_verification": "fallback",
    "review_platform_search": "fallback",
    "web_vitals_field_data": "fallback",
    "rendering_headless_browser": "fallback",
    "external_corroboration": "fallback",
    "external_footprint_search": "fallback",
    "agent_entity_corroboration": "optional",
    "agent_image_vision": "optional",
    "agent_knowledge_graph_search": "optional",
    "agent_review_platform_search": "optional",
})


def _headless_browser_available() -> bool:
    """True only if playwright is importable AND a browser binary is actually
    installed on disk -- the package being importable is not enough (a common false
    positive, since `chromium.executable_path` is just a string, not a liveness check)."""
    if importlib.util.find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            return os.path.exists(p.chromium.executable_path)
    except Exception:
        return False


def _search_provider_available() -> bool:
    return bool(os.environ.get("SEARCH_API_URL"))


def detect_capabilities() -> dict:
    """Probed once per process; cheap enough to call per audit."""
    return {
        "headless_rendering": os.environ.get("ENABLE_RENDERING") == "1" and _headless_browser_available(),
        "external_search": _search_provider_available(),
    }


def capability_report(capabilities: dict) -> dict:
    """Coverage-block-ready summary: which tiered checks actually ran with which
    implementation this audit."""
    return {
        "check_tiers": dict(CHECK_TIERS),
        "capabilities_detected": dict(capabilities),
        "rendering_mode": "headless_browser" if capabilities.get("headless_rendering") else "heuristic_only",
        "external_analysis_mode": "search_provider" if capabilities.get("external_search") else "unavailable",
        # Core Web Vitals: real-user field data only with a PageSpeed Insights key.
        "web_vitals_mode": "field_data" if field_lookup_enabled() else "static_estimate",
    }
