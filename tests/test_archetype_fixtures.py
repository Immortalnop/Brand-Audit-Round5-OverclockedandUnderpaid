"""test_archetype_fixtures.py -- generalization tested by construction.

tests/archetype_sites.py builds nine small sites offline: six archetypes (a
single-page app, an e-commerce shop, a local business, a documentation site, a
blog, a multi-language site) and three precision traps (a news publisher, a
splash page with a nonprofit behind it, a store with consumer segments). Each has
defects planted on purpose and good practice -- or page shapes that commonly trip
a heuristic -- that must not be reported.

For every site the test asserts:
  - EXPECTED: the check IDs the planted defects must raise, and on which pages;
  - ABSENT: the check IDs the site must not raise (false-positive guards);
  - the run stays offline, uses GET only, never touches a sensitive route,
    finishes well inside the time limit and validates cleanly;
  - "what's working" never contradicts a finding.

The corpus found these false positives, fixed alongside it: render-gap-unconfirmed
on short pages that run no script and on a login page; facts-in-images on product
photos next to a price stated in text; brand-definition missing "sells" / "fixes";
datePublished treated as required Article markup; page-orientation on short but
clear H1s; /blog/ and /news/ held to Article markup; an href with a trailing space
reported as a broken page and an orphan; a masthead name counted as term
repetition; email-summary-readable on an ordinary product gallery; and
kg-link-missing suggested to every organization.

http-transport fires on every site because the fixtures really are served over
plain HTTP; it is not listed.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from archetype_sites import ARCHETYPES, TRAPS, serve  # noqa: E402
from constants import Limits  # noqa: E402

SITES = {**ARCHETYPES, **TRAPS}

# Lookups that could leave the machine are switched off.
OFFLINE_ENV = {"SEARCH_API_URL": "", "SEARCH_API_KEY": "", "AGENT_FINDINGS_PATH": "", "ENABLE_RENDERING": "0",
               "AUDIT_PROGRESS": "0"}

# check ID -> paths it must name (None: any pages).
EXPECTED = {
    "spa": {"render-gap": {"/", "/pricing", "/about"}, "hash-routing": None, "no-jsonld": None, "no-headings": None},
    "shop": {"page-type-schema-gap:product": {"/products/camp-stove"}},
    "local": {"schema-missing-required": {"/"}, "contact-markup-missing": None},
    "docs": {"heading-hierarchy": {"/docs/getting-started", "/docs/api"}, "long-paragraphs": None},
    "blog": {"brand-definition": {"/"}, "sitemap-lastmod-unreliable": None},
    "intl": {"missing-language": {"/fr/"}},
    "news": {"citation-schema-opportunity": {"/faq"}, "no-llms-txt": None},
    "splash": {"render-gap-unconfirmed": {"/"}, "no-llms-txt": None},
    "store": {"email-summary": None},
}

# check IDs each site must not raise.
ABSENT = {
    "spa": {"broken-pages", "missing-title", "email-summary"},
    # Product photos next to prices in text; a brand defined with "sells"; a login page.
    "shop": {"no-jsonld", "render-gap", "render-gap-unconfirmed", "brand-definition", "page-type-schema-gap:home",
             "facts-in-images", "email-summary", "kg-link-missing"},
    # A Plumber subtype is the site's Organization; "fixes" defines the brand.
    "local": {"page-type-schema-gap:home", "render-gap", "no-jsonld", "brand-definition", "kg-link-missing",
              "identity-not-declared"},
    # Short but clear H1s; TechArticle without datePublished is not invalid.
    "docs": {"no-llms-txt", "render-gap", "render-gap-unconfirmed", "no-jsonld", "page-orientation",
             "schema-missing-required"},
    # /blog/ and /news/ are section indexes; old posts are not stale facts.
    "blog": {"page-type-schema-gap:article", "render-gap", "render-gap-unconfirmed", "no-jsonld",
             "stale-update-claim", "expired-offer"},
    "intl": {"render-gap", "render-gap-unconfirmed", "no-jsonld"},
    # Linked question teasers, a quoted gallery address, an archive date, an href
    # with a trailing space, a masthead name repeated on the front page.
    "news": {"render-gap", "render-gap-unconfirmed", "broken-pages", "fetch-failure", "orphan-pages",
             "term-repetition", "stale-update-claim", "stale-copyright", "expired-offer", "contact-markup-missing"},
    # A splash chooser, a contact form with an email field, a nonprofit.
    "splash": {"render-gap", "orphan-pages", "dead-ends", "isolated-clusters", "email-summary",
               "email-summary-readable", "broken-pages", "kg-link-missing"},
    # A product gallery with descriptive alt text and the price in text.
    "store": {"email-summary-readable", "facts-in-images", "broken-pages", "render-gap", "missing-alt"},
}


@pytest.fixture(scope="module")
def audits():
    """One offline audit per site: {name: (base_url, report, requests)}."""
    from run_audit import run_audit
    saved = {k: os.environ.get(k) for k in OFFLINE_ENV}
    os.environ.update(OFFLINE_ENV)
    results = {}
    try:
        for name, site in SITES.items():
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


def by_check(base, report):
    """check ID -> affected paths, over findings, hygiene items and recommendations
    (merged findings count under every check they combine)."""
    out = {}
    for item in report["findings"] + report.get("hygiene_findings", []) + report["recommendations"]:
        paths = {p[len(base):] for p in item.get("affected_pages", []) if str(p).startswith(base)}
        for check_id in item.get("check_ids") or [item["check_id"]]:
            out.setdefault(check_id, set()).update(paths)
    return out


def test_corpus_is_complete():
    assert set(SITES) == set(EXPECTED) == set(ABSENT)


@pytest.mark.parametrize("name", sorted(SITES))
def test_planted_defects_are_reported(audits, name):
    base, report, _ = audits[name]
    found = by_check(base, report)
    for check_id, pages in EXPECTED[name].items():
        assert check_id in found, f"{name}: expected {check_id}, got {sorted(found)}"
        if pages is not None:
            assert found[check_id] == pages, f"{name}: {check_id} named {sorted(found[check_id])}"


@pytest.mark.parametrize("name", sorted(SITES))
def test_good_practice_and_traps_are_not_reported(audits, name):
    base, report, _ = audits[name]
    wrongly = ABSENT[name] & set(by_check(base, report))
    assert not wrongly, f"{name}: false positives {sorted(wrongly)}"


@pytest.mark.parametrize("name", sorted(SITES))
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
    for item in report["findings"] + report["hygiene_findings"] + report["recommendations"]:
        assert all(c in CATALOG for c in item.get("check_ids") or [item["check_id"]])
    assert report["confidence"]["explanation"].startswith("Confidence is ")


@pytest.mark.parametrize("name", sorted(SITES))
def test_whats_working_never_contradicts_a_finding(audits, name):
    _, report, _ = audits[name]
    reported = {c for item in report["findings"] + report["hygiene_findings"] + report["recommendations"]
                for c in item.get("check_ids") or [item["check_id"]]}
    for w in report["whats_working"]:
        assert not reported & set(w["check_ids"]), (name, w["check"])
    assert report["whats_working"], f"{name}: a working site lists no passed check"


def test_shop_never_requests_the_cart_and_keeps_login_out(audits):
    base, report, seen = audits["shop"]
    paths = [p for _, p in seen]
    assert "/cart" not in paths
    assert paths.count("/login") == 1
    assert [e["url"] for e in report["coverage"]["out_of_scope_pages"]] == [base + "/login"]
    for pages in by_check(base, report).values():
        assert "/login" not in pages


def test_local_business_subtype_resolves_the_brand(audits):
    _, report, _ = audits["local"]
    assert report["coverage"]["identity_confidence"] >= 0.85
    brief = report["agent_stage"]["brief"]
    assert brief["brand_name"] == "Harbour Plumbing" and brief["ag06"]["business_kind"] == "local"


def test_local_contact_snippet_uses_the_details_the_site_shows(audits):
    """The footer phone (shown on every page) fills the draft. The email is on
    another domain than the audited host (the fixture is served from 127.0.0.1), so
    it is never put into the brand's markup: it stays a placeholder."""
    _, report, _ = audits["local"]
    finding = next(f for f in report["findings"] if "contact-markup-missing" in (f.get("check_ids") or [f["check_id"]]))
    snippet = finding["suggested_action"]["snippet"]
    assert "+442392000111" in snippet["code"] and "jobs@harbourplumbing.test" not in snippet["code"]
    assert "REPLACE_WITH_EMAIL" in snippet["placeholders"]


def test_news_trailing_space_href_is_the_page_itself(audits):
    base, report, seen = audits["news"]
    assert ("GET", "/culture%20") not in seen
    assert report["coverage"]["pages_analyzed"] == 8
