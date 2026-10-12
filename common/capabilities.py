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
    "rendering_headless_browser": "fallback",
    "external_corroboration": "fallback",
    "external_footprint_search": "fallback",
    "agent_entity_corroboration": "optional",
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
    }
