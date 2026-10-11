"""analyze_machine_readability.py -- headings, JSON-LD, semantic linkage.

Page-type-aware structured-data evaluation: whether a page is "missing structured
data" depends on what kind of page it is. A flat "0/N pages have JSON-LD" check
cannot tell a product-detail page missing Product/Offer markup apart from a legal
page that never needed any -- and cannot separately flag "the home page has no
Organization markup" from "product pages have no Product markup", which call for
different fixes at different priorities. page_type is set during acquisition
(acquire_site._classify_page_type) from URL shape and any JSON-LD already present;
this script only reads it, never assigns it.
"""
from collections.abc import Mapping
from check_helpers import commerce_evidence
from models import skill_result, make_finding, coverage_ratio, scale_confidence, step_down_severity

# Expected schema.org @type(s) for each page_type that should realistically carry
# structured data. Types not listed here (e.g. "other", "category") are not held
# to any expectation -- absence there is not evidence of anything.
from structured_data import iter_nodes, types_of, ORGANIZATION_TYPES

# Organization and LocalBusiness are matched with their subtypes (Plumber,
# CollegeOrUniversity...), which are Organizations too.
_EXPECTED_SCHEMA = {
    "service": {"types": {"Service"}, "severity": "low", "label": "Service"},
    "software": {"types": {"SoftwareApplication", "MobileApplication", "WebApplication"}, "severity": "low", "label": "SoftwareApplication"},
    "home": {"types": ORGANIZATION_TYPES | {"WebSite"}, "severity": "high",
             "label": "Organization/WebSite"},
    "product": {"types": {"Product", "Offer"}, "severity": "high", "label": "Product/Offer"},
    "article": {"types": {"Article", "BlogPosting", "NewsArticle"}, "severity": "medium",
                "label": "Article/BlogPosting"},
    "contact": {"types": ORGANIZATION_TYPES | {"ContactPage"}, "severity": "medium",
                "label": "LocalBusiness/Organization/ContactPage"},
    "about": {"types": ORGANIZATION_TYPES | {"AboutPage"}, "severity": "low", "label": "Organization/AboutPage"},
}

def _page_jsonld_types(page):
    return set().union(*(types_of(n) for n in iter_nodes(page.jsonld_blocks)))


def analyze_machine_readability(artifacts, deadline):
    pages = tuple(p for p in artifacts.pages if p.status_code == 200 and "html_parse_incomplete" not in p.warnings and "non_html_content" not in p.warnings and "response_truncated_at_byte_budget" not in p.warnings)
    no_jsonld = [p for p in pages if not p.jsonld_blocks and not (p.features or {}).get("alternative_structured_markup")]
    no_headings = [p for p in pages if not p.headings]

    # Evidence-completeness ratio: these findings only ever speak for the pages
    # actually crawled. "0/N have JSON-LD" is strong evidence when N is most of
    # the discovered site, weaker when the crawl only reached a small slice of it
    # (Round-3 review item 1) -- confidence/severity below are scaled accordingly.
    acq_coverage = artifacts.acquisition_metadata.get("coverage", {})
    crawl_ratio = coverage_ratio(
        acq_coverage.get("urls_analyzed", len(pages)),
        acq_coverage.get("urls_discovered", len(pages)),
    )

    findings = []

    malformed_pages = [p for p in pages if "malformed_jsonld_block" in p.warnings]
    if malformed_pages:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="high",
            status="confirmed", confidence=0.85,
            title="Malformed JSON-LD blocks prevent reliable fact extraction",
            root_cause="One or more sampled pages contain JSON-LD that could not be parsed, so structured facts may be discarded by automated readers",
            evidence=[{"type": "structured_data", "description": f"{len(malformed_pages)} sampled page(s) contain malformed JSON-LD", "urls": [p.url for p in malformed_pages[:10]]}],
            suggested_action={
                "summary": "Repair and validate every application/ld+json block",
                "steps": ["Validate each JSON-LD block as strict JSON", "Preserve valid @graph nodes and required properties", "Re-run a structured-data validator after deployment"],
                "priority": "high", "effort": "low",
                "expected_benefit": "Prevents parsers from dropping important entity and product facts",
                "verification": "All sampled JSON-LD blocks parse successfully"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py", "rule_id": "malformed-jsonld"},
            affected_pages=[p.url for p in malformed_pages]))

    if pages and len(no_jsonld) == len(pages):
        # No structured data anywhere -- the coarsest, most severe version of this
        # gap. Kept as its own finding rather than folded into the per-type checks
        # below, since it's evidence about the whole site, not one page type.
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect",
            severity=step_down_severity("high", crawl_ratio),
            status="confirmed", confidence=0.85,
            title="No structured data (JSON-LD) found on any crawled page",
            root_cause="Pages lack schema.org JSON-LD markup"
                       + ("" if crawl_ratio >= 0.999 else
                          f" (observed on the {len(pages)} of "
                          f"{acq_coverage.get('urls_discovered', len(pages))} discovered pages that were "
                          "actually crawled)"),
            evidence=[{"type": "structured_data", "description": f"0/{len(pages)} pages contain JSON-LD",
                       "urls": [p.url for p in pages][:10]}],
            suggested_action={
                "summary": "Add Organization/Product/Article JSON-LD to key pages",
                "steps": ["Identify page types", "Add matching schema.org JSON-LD blocks"],
                "priority": "high", "effort": "medium",
                "expected_benefit": "Facts become machine-extractable",
                "verification": "Validate JSON-LD with a schema.org validator",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py",
                        "rule_id": "no-jsonld"},
        ))
    else:
        # Some structured data exists somewhere -- check it's the RIGHT structured
        # data for each page's role, per type.
        by_type_gaps = {}
        for page in pages:
            spec = _EXPECTED_SCHEMA.get(page.page_type)
            if not spec or (page.features or {}).get("alternative_structured_markup"):
                continue
            # A /products path is held to Product/Offer markup only when the page
            # shows something for sale (a price, a buy control or a cart link): an
            # index of software products or a product-line overview is not an offer.
            if page.page_type == "product" and not commerce_evidence(page):
                continue
            if not (_page_jsonld_types(page) & spec["types"]):
                by_type_gaps.setdefault(page.page_type, []).append(page.url)

        for page_type, urls in by_type_gaps.items():
            spec = _EXPECTED_SCHEMA[page_type]
            findings.append(make_finding(
                category="ai_discoverability", finding_type="defect",
                severity=step_down_severity(spec["severity"], crawl_ratio),
                status="confirmed", confidence=0.8,
                title=f"{page_type.capitalize()} pages are missing {spec['label']} structured data",
                root_cause=f"{len(urls)} page(s) classified as '{page_type}' carry no "
                           f"{spec['label']} JSON-LD, so explicit machine-readable context may be improved",
                evidence=[{"type": "structured_data",
                           "description": f"{len(urls)} '{page_type}' page(s) missing {spec['label']} markup",
                           "urls": urls[:10]}],
                suggested_action={
                    "summary": f"Add {spec['label']} JSON-LD to {page_type} pages",
                    "steps": [f"Add {spec['label']} schema.org JSON-LD matching each {page_type} page's content",
                              "Validate with a schema.org/Rich Results validator"],
                    "priority": spec["severity"], "effort": "medium",
                    "expected_benefit": f"{page_type.capitalize()} facts become machine-extractable and citable",
                    "verification": "Re-crawl and confirm the expected @type is present",
                },
                provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py",
                            "rule_id": f"page-type-schema-gap:{page_type}"},
            ))

    if no_headings:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.8,
            title="Some pages lack semantic headings",
            root_cause="Pages have no h1-h6 elements",
            evidence=[{"type": "headings", "description": f"{len(no_headings)} pages have no headings",
                       "urls": [p.url for p in no_headings][:10]}],
            suggested_action={
                "summary": "Add semantic heading structure",
                "steps": ["Add an h1 per page", "Structure sections with h2/h3"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Improves text extraction quality",
                "verification": "Inspect DOM for heading tags",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py",
                        "rule_id": "no-headings"},
        ))

    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"pages_with_jsonld": len(pages) - len(no_jsonld), "pages_without_headings": len(no_headings),
                 "crawl_coverage_ratio": round(crawl_ratio, 3)},
    )
