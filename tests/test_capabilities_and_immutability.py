"""Capability-tier registry and the MappingProxyType second-defense immutability
layer (frozen-artifact acceptance test, generalized)."""
import os
import sys
from types import MappingProxyType

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts"):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from capabilities import detect_capabilities, capability_report, CHECK_TIERS
from models import PageArtifact, AuditArtifacts, freeze_value, hash_artifacts


def test_capability_tiers_cover_every_documented_check():
    tiers = set(CHECK_TIERS.values())
    assert tiers <= {"executable", "fallback", "optional"}
    assert "rendering_headless_browser" in CHECK_TIERS
    assert CHECK_TIERS["rendering_headless_browser"] == "fallback"
    assert CHECK_TIERS["crawlability"] == "executable"
    assert CHECK_TIERS["agent_entity_corroboration"] == "optional"


def test_capability_report_reflects_detected_capabilities():
    caps = {"headless_rendering": False, "external_search": False}
    report = capability_report(caps)
    assert report["rendering_mode"] == "heuristic_only"
    assert report["external_analysis_mode"] == "unavailable"


def test_detect_capabilities_runs_without_error_and_returns_booleans():
    caps = detect_capabilities()
    assert set(caps.keys()) == {"headless_rendering", "external_search"}
    assert isinstance(caps["headless_rendering"], bool)
    assert isinstance(caps["external_search"], bool)
    # No SEARCH_API_URL is configured by default in this environment.
    assert caps["external_search"] is False


def _fixture_page():
    return PageArtifact(
        url="https://example.com/", status_code=200, content_type="text/html",
        evidence_snippet="e", visible_text="v", title="t", meta_description=None,
        canonical_url=None, headings=(), internal_links=(), external_links=(),
        jsonld_blocks=(freeze_value({"@type": "Organization", "name": "Ex", "nested": {"a": 1}}),),
        page_type=None, fetch_duration_ms=1, render_status="not_rendered",
        breadcrumb_visible=(), breadcrumb_schema=None,
        ai_crawler_directives=freeze_value({"GPTBot": "allow"}), warnings=(),
    )


def test_nested_dict_fields_are_read_only_mapping_proxies():
    page = _fixture_page()
    assert isinstance(page.ai_crawler_directives, MappingProxyType)
    assert isinstance(page.jsonld_blocks[0], MappingProxyType)
    assert isinstance(page.jsonld_blocks[0]["nested"], MappingProxyType)


def test_mutation_attempt_on_frozen_nested_dict_raises():
    page = _fixture_page()
    try:
        page.ai_crawler_directives["GPTBot"] = "disallow"
        assert False, "MappingProxyType should have rejected the write"
    except TypeError:
        pass
    try:
        page.jsonld_blocks[0]["name"] = "Changed"
        assert False, "nested MappingProxyType should have rejected the write"
    except TypeError:
        pass


def test_frozen_dataclass_rejects_field_reassignment():
    page = _fixture_page()
    try:
        page.url = "https://other.com/"
        assert False, "frozen dataclass should reject attribute assignment"
    except Exception:
        pass


def test_hash_artifacts_is_stable_and_detects_no_false_changes():
    artifacts = AuditArtifacts(
        site_url="https://example.com/", normalized_origin="https://example.com",
        pages=(_fixture_page(),), robots_data=freeze_value({"allowed_general": True}),
        llms_txt_data=freeze_value({}), sitemap_data=freeze_value({}),
        acquisition_metadata=freeze_value({}), warnings=(),
    )
    h1 = hash_artifacts(artifacts)
    h2 = hash_artifacts(artifacts)
    assert h1 == h2  # same immutable object -> identical hash, nothing silently changed


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"OK: {name}")
