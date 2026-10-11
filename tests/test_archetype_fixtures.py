"""test_archetype_fixtures.py -- Plan.md point 15: generalization tested by construction.

Each archetype in tests/archetype_sites.py (single-page app, e-commerce shop,
local business, documentation site, blog, multi-language site) is audited end to
end, offline. For each one the test asserts:
  - the check IDs its planted defects must raise (and on which pages), and
  - the check IDs its good practice must NOT raise (false-positive guards).
Every run must also stay offline (no external fetch), use GET only, finish
well inside the time limit and produce a report that validates cleanly.

The corpus found four false positives, fixed alongside it and pinned by the unit
tests at the end of this file: render-gap on short pages that run no script,
Organization subtypes (Plumber) not counted as Organization markup, a brand
definition written with "sells" or "runs" not recognised, and a section index
such as /blog/ held to article markup.
"""
import os
import sys
from types import SimpleNamespace

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from archetype_sites import ARCHETYPES, serve
from constants import Limits

# Optional lookups that would leave the machine are switched off; .env loading
# never overrides a variable that is already set, even to "".
_OFFLINE_ENV = {"SEARCH_API_URL": "", "SEARCH_API_KEY": "", "PAGESPEED_API_KEY": "", "FIELD_VITALS_LOOKUP": "0",
                "AGENT_FINDINGS_PATH": "", "OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0",
                "ENABLE_RENDERING": "0", "AUDIT_PROGRESS": "0"}

# check ID -> pages (paths) it must name; None means "any pages".
EXPECTED = {
    "spa": {"render-gap": {"/", "/pricing", "/about"}, "hash-routing": None, "no-jsonld": None,
            "no-headings": None},
    "shop": {"page-type-schema-gap:product": {"/products/camp-stove"},
             "image-context-missing": {"/products/camp-stove"}},
    "local": {"local-business-incomplete": {"/"}, "location-markup-missing": None,
              "contact-markup-missing": None},
    "docs": {"llms-txt-broken-links": None, "heading-hierarchy": {"/docs/getting-started", "/docs/api"},
             "long-paragraphs": None},
    "blog": {"author-missing": {"/blog/cold-proofing", "/blog/feeding-a-starter"},
             "stale-dates:editorial": None, "brand-definition": {"/"}},
    "intl": {"hreflang-invalid": None, "missing-language": {"/fr/"}},
}

# Check IDs each archetype's good practice must not raise.
ABSENT = {
    # Pages built by JavaScript are not judged on what the bundle may build.
    "spa": {"site-search-missing", "context-retention-missing", "comparison-table-missing", "spec-list-missing",
            "audience-segment-missing"},
    "shop": {"site-search-missing", "spec-list-missing", "comparison-table-missing", "no-jsonld", "render-gap",
             "brand-definition", "page-type-schema-gap:home"},
    "local": {"page-type-schema-gap:home", "render-gap", "no-jsonld", "brand-definition"},
    "docs": {"no-llms-txt", "site-search-missing", "render-gap", "structured-date-invalid", "no-jsonld"},
    # /blog/ and /news/ are section indexes: no article markup is expected, and
    # two of them are not a shop missing saved items.
    "blog": {"page-type-schema-gap:article", "render-gap", "site-search-missing", "no-jsonld",
             "context-retention-missing"},
    "intl": {"render-gap", "hreflang-missing", "no-jsonld"},
}


@pytest.fixture(scope="module")
def audits():
    """One offline audit per archetype: {name: (base_url, report, requests)}."""
    from run_audit import run_audit
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    results = {}
    try:
        for name, site in ARCHETYPES.items():
            base, stop, seen = serve(site)
            try:
                results[name] = (base, run_audit(base + "/", limits=Limits(), allow_private_targets=True), list(seen))
            finally:
                stop()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return results


def _by_check(base, report):
    """check ID -> set of affected paths, over findings and recommendations."""
    out = {}
    for item in report["findings"] + report["recommendations"]:
        paths = {p[len(base):] for p in item.get("affected_pages", []) if str(p).startswith(base)}
        out.setdefault(item["check_id"], set()).update(paths)
    return out


def test_corpus_covers_every_archetype():
    assert set(ARCHETYPES) == {"spa", "shop", "local", "docs", "blog", "intl"}
    assert set(EXPECTED) == set(ARCHETYPES) == set(ABSENT)


@pytest.mark.parametrize("name", sorted(ARCHETYPES))
def test_planted_defects_are_reported(audits, name):
    base, report, _ = audits[name]
    found = _by_check(base, report)
    for check_id, pages in EXPECTED[name].items():
        assert check_id in found, f"{name}: expected {check_id}, got {sorted(found)}"
        if pages is not None:
            assert found[check_id] == pages, f"{name}: {check_id} named {sorted(found[check_id])}"


@pytest.mark.parametrize("name", sorted(ARCHETYPES))
def test_good_practice_is_not_reported(audits, name):
    base, report, _ = audits[name]
    wrongly = ABSENT[name] & set(_by_check(base, report))
    assert not wrongly, f"{name}: false positives {sorted(wrongly)}"


@pytest.mark.parametrize("name", sorted(ARCHETYPES))
def test_every_run_is_offline_read_only_bounded_and_valid(audits, name):
    from check_catalog import CATALOG
    base, report, seen = audits[name]
    cov = report["coverage"]
    assert report["execution_status"] == "completed"
    assert cov["external_fetches"] == 0
    assert {method for method, _ in seen} == {"GET"}
    assert cov["runtime_seconds"] < 60
    assert cov["pages_analyzed"] >= 3
    assert not [w for w in report["warnings"] if w.startswith(("Dropped", "Missing required"))]
    assert all(item["check_id"] in CATALOG for item in report["findings"] + report["recommendations"])
    assert report["confidence"]["explanation"].startswith("Confidence is ")


def test_spa_warns_that_script_built_pages_were_not_judged(audits):
    _, report, _ = audits["spa"]
    assert any("probably built by JavaScript" in w for w in report["warnings"])
    assert report["coverage"]["pages_analyzed"] == 3


def test_shop_never_requests_the_cart_and_keeps_login_out(audits):
    base, report, seen = audits["shop"]
    paths = [p for _, p in seen]
    assert "/cart" not in paths
    assert paths.count("/login") == 1
    assert [e["url"] for e in report["coverage"]["out_of_scope_pages"]] == [base + "/login"]
    for pages in _by_check(base, report).values():
        assert "/login" not in pages


def test_local_business_subtype_resolves_the_brand(audits):
    _, report, _ = audits["local"]
    assert report["coverage"]["identity_resolution"] == "resolved"


def test_multi_language_site_reads_every_language(audits):
    base, report, _ = audits["intl"]
    found = _by_check(base, report)
    assert {"/en/", "/de/"} & found["hreflang-invalid"]
    assert "/fr/" not in found["hreflang-invalid"]


# ---------------------------------------------------------------------------
# Unit tests for the fixes the corpus prompted
# ---------------------------------------------------------------------------

def _page(**kw):
    defaults = dict(url="http://x.test/", status_code=200, page_type="other", visible_text="Short page.",
                    features={"noscript_chars": 0, "external_scripts": 0, "inline_script_bytes": 0},
                    jsonld_blocks=(), warnings=())
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def test_short_page_without_scripts_is_not_script_dependent():
    from check_helpers import script_dependent, runs_scripts
    static = _page()
    assert not runs_scripts(static) and not script_dependent(static)
    bundled = _page(features={"noscript_chars": 0, "external_scripts": 1, "inline_script_bytes": 0})
    assert runs_scripts(bundled) and script_dependent(bundled)
    inline = _page(features={"noscript_chars": 0, "external_scripts": 0, "inline_script_bytes": 40})
    assert script_dependent(inline)
    # A <noscript> saying JavaScript is required is the page's own statement.
    stated = _page(features={"noscript_chars": 0, "external_scripts": 0, "inline_script_bytes": 0,
                             "noscript_js_required": True})
    assert runs_scripts(stated) and script_dependent(stated)
    # Observations without script counts keep the earlier, cautious reading.
    assert script_dependent(_page(features={"noscript_chars": 0}))
    # A page with scripts and plenty of text is not script dependent either.
    assert not script_dependent(_page(visible_text="word " * 200, features=bundled.features))


def test_section_indexes_are_listing_pages():
    from acquire_site import _classify_page_type
    for path, kind in (("/blog/", "listing"), ("/blog", "listing"), ("/News/", "listing"), ("/press", "listing"),
                       ("/blog/cold-proofing", "article"), ("/blog-tips", "article"),
                       # Shop indexes keep their earlier type.
                       ("/products", "product"), ("/products/camp-stove", "product"), ("/product", "product")):
        assert _classify_page_type("http://x.test" + path, "http://x.test", [], path) == kind, path
    # Markup still wins over the path.
    assert _classify_page_type("http://x.test/blog/", "http://x.test",
                               [{"@type": "BlogPosting"}], "/blog/") == "article"


def test_listing_pages_carry_editorial_dates():
    from extract_claims import _DATE_CATEGORY_BY_PAGE_TYPE
    from update_signals import _UPDATE_CATEGORY_BY_PAGE_TYPE
    assert _DATE_CATEGORY_BY_PAGE_TYPE["listing"] == _DATE_CATEGORY_BY_PAGE_TYPE["article"] == "editorial"
    assert _UPDATE_CATEGORY_BY_PAGE_TYPE["listing"] == "editorial"


def test_organization_subtypes_satisfy_home_and_contact_markup():
    from analyze_machine_readability import _EXPECTED_SCHEMA
    for page_type in ("home", "contact", "about"):
        types = _EXPECTED_SCHEMA[page_type]["types"]
        assert {"Organization", "Plumber", "CollegeOrUniversity", "Restaurant"} <= types
    assert "Plumber" not in _EXPECTED_SCHEMA["product"]["types"]


def _artifacts(*pages):
    return SimpleNamespace(pages=pages, normalized_origin="http://x.test")


def test_identity_falls_back_to_a_subtype_on_the_home_page():
    from resolve_entity_identity import resolve_entity_identity
    deadline = SimpleNamespace(remaining_seconds=lambda: 100, expired=lambda: False)
    home = _page(page_type="home", jsonld_blocks=({"@type": "Plumber", "name": "Harbour Plumbing"},))
    result = resolve_entity_identity(_artifacts(home), deadline)
    assert result["data"]["confidence"] >= 0.85 and result["data"]["canonical_name"] == "Harbour Plumbing"
    # Listings of other businesses away from the home page do not become the brand.
    listing = _page(url="http://x.test/places", jsonld_blocks=({"@type": "Restaurant", "name": "Cafe A"},
                                                               {"@type": "Restaurant", "name": "Diner B"}))
    result = resolve_entity_identity(_artifacts(_page(page_type="home"), listing), deadline)
    assert result["data"]["confidence"] == 0.0 and result["status"] == "insufficient_evidence"
    # A core Organization block still takes precedence over home-page subtypes.
    org = _page(url="http://x.test/about", page_type="about",
                jsonld_blocks=({"@type": "Organization", "name": "Acme"},))
    home_sub = _page(page_type="home", jsonld_blocks=({"@type": "Restaurant", "name": "Other Place"},))
    result = resolve_entity_identity(_artifacts(home_sub, org), deadline)
    assert result["data"]["canonical_name"] == "Acme" and result["data"]["confidence"] >= 0.85


# The brand-definition verbs are pinned end to end: the shop home page defines
# its brand with "sells" and the plumber with "fixes", and neither may raise
# brand-definition (ABSENT above), while the blog, which never defines itself,
# must (EXPECTED above).
