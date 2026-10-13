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
from check_catalog import calibrated_confidence
from check_helpers import commerce_evidence, script_dependent
from models import skill_result, make_finding, coverage_ratio, scale_confidence, step_down_severity

# Expected schema.org @type(s) for each page_type that should realistically carry
# structured data. Types not listed here (e.g. "other", "category") are not held
# to any expectation -- absence there is not evidence of anything.
from structured_data import iter_nodes, types_of, ORGANIZATION_TYPES
from schema_values import value_observations

# Organization and LocalBusiness are matched with their subtypes (Plumber,
# CollegeOrUniversity...), which are Organizations too. A gap is an improvement
# opportunity at most medium: the markup is optional for indexing, and no
# specific machine-use requirement is established by its absence alone.
_EXPECTED_SCHEMA = {
    "service": {"types": {"Service"}, "severity": "low", "label": "Service"},
    "software": {"types": {"SoftwareApplication", "MobileApplication", "WebApplication"}, "severity": "low", "label": "SoftwareApplication"},
    "home": {"types": ORGANIZATION_TYPES | {"WebSite"}, "severity": "medium",
             "label": "Organization/WebSite"},
    "product": {"types": {"Product", "Offer"}, "severity": "medium", "label": "Product/Offer"},
    "article": {"types": {"Article", "BlogPosting", "NewsArticle"}, "severity": "medium",
                "label": "Article/BlogPosting"},
    "contact": {"types": ORGANIZATION_TYPES | {"ContactPage"}, "severity": "medium",
                "label": "LocalBusiness/Organization/ContactPage"},
    "about": {"types": ORGANIZATION_TYPES | {"AboutPage"}, "severity": "low", "label": "Organization/AboutPage"},
}

def _page_jsonld_types(page):
    return set().union(*(types_of(n) for n in iter_nodes(page.jsonld_blocks)))


def _block_word(n):
    return "block" if n == 1 else "blocks"


def _parse_error_text(page):
    """One line naming where each JSON-LD block on page failed to parse."""
    parts = []
    total = (page.features or {}).get("jsonld_block_count")
    for e in (page.features or {}).get("jsonld_errors") or ():
        where = f"block {e.get('block_index')}" + (f" of {total}" if total else "")
        if e.get("line"):
            where += f", line {e['line']}, column {e.get('column')}"
        text = f"{where}: {e.get('message')}"
        if e.get("excerpt"):
            text += f" near \"{e['excerpt']}\""
        parts.append(text)
    return "; ".join(parts) or "a JSON-LD block could not be parsed"


def _malformed_jsonld(pages):
    """One finding for JSON-LD blocks that fail to parse, or None.

    The parse failure is observed directly, so it is confirmed; its severity
    follows its reach: the share of pages carrying JSON-LD that hold a broken
    block, and whether a broken page keeps no usable typed entity from another
    block (the failed block was central, not one optional block among several).
    Pages cut by the byte budget are never in `pages`: a prefix of a valid block
    is a transport limit, not malformed source JSON."""
    affected = [p for p in pages if "malformed_jsonld_block" in p.warnings]
    if not affected:
        return None
    with_jsonld = [p for p in pages if p.jsonld_blocks or "malformed_jsonld_block" in p.warnings]
    reach = len(affected) / max(1, len(with_jsonld))
    central = [p for p in affected if not _page_jsonld_types(p)]
    if reach >= 0.5 and central:
        severity = "high"
    elif reach >= 0.2 or any(p.page_type in ("home", "product") for p in central):
        severity = "medium"
    else:
        severity = "low"
    broken_blocks = sum(len((p.features or {}).get("jsonld_errors") or ()) or 1 for p in affected)
    return make_finding(
        category="ai_discoverability", finding_type="defect", severity=severity,
        status="confirmed", confidence=0.85,
        title="Malformed JSON-LD blocks prevent reliable fact extraction",
        root_cause=(f"{len(affected)} of {len(with_jsonld)} sampled page(s) with JSON-LD hold at least one block that "
                    f"is not valid JSON ({broken_blocks} {_block_word(broken_blocks)} in all), so automated readers "
                    "discard that block's facts"
                    + (f"; on {len(central)} of them no other block supplies a typed entity" if central else
                       "; each affected page still has another valid typed block")),
        evidence=[{"type": "structured_data", "description": _parse_error_text(p), "urls": [p.url]}
                  for p in affected[:10]],
        suggested_action={
            "summary": "Repair and validate every application/ld+json block",
            "steps": ["Fix the JSON syntax at the block, line and column named in the evidence",
                      "Preserve valid @graph nodes and required properties",
                      "Re-run a structured-data validator after deployment"],
            "priority": severity, "effort": "low",
            "expected_benefit": "Prevents parsers from dropping important entity and product facts",
            "verification": "All sampled JSON-LD blocks parse successfully"},
        provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py", "rule_id": "malformed-jsonld"},
        affected_pages=[p.url for p in affected])


def analyze_machine_readability(artifacts, deadline):
    pages = tuple(p for p in artifacts.pages if p.status_code == 200 and "html_parse_incomplete" not in p.warnings and "non_html_content" not in p.warnings and "response_truncated_at_byte_budget" not in p.warnings)
    no_jsonld = [p for p in pages if not p.jsonld_blocks and not (p.features or {}).get("alternative_structured_markup")
                and (p.features or {}).get('jsonld_block_count', 0) == 0]
    # A page built by JavaScript has its headings added after load; its raw HTML
    # cannot show that the page lacks them.
    no_headings = [p for p in pages if not p.headings and not script_dependent(p)]

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

    malformed = _malformed_jsonld(pages)
    if malformed:
        findings.append(malformed)
    value_errors, processing_limits = [], []
    for page in pages:
        invalid, limits = value_observations(page)
        if invalid:
            value_errors.append((page, invalid))
        for limitation in limits:
            processing_limits.append(f'{page.url}: {limitation}')
        for limitation in (page.features or {}).get('jsonld_limitations') or ():
            processing_limits.append(f"{page.url}: JSON-LD block {limitation['block_index']} {limitation['state']}: {limitation['message']}")
    if value_errors:
        findings.append(make_finding(category='ai_discoverability', finding_type='defect', severity='medium',
            status='confirmed', confidence=0.8, title='Some schema.org values cannot be interpreted under supported value rules',
            root_cause='Acquired schema.org numeric, calendar or IRI property values fail the documented limited interpretation rules.',
            evidence=[{'type': 'structured_value', 'description': '; '.join(f'{key}={value!r}: expected {expected}' for key,value,expected in invalid[:5]),
                       'urls': [page.url]} for page,invalid in value_errors[:10]],
            affected_pages=[page.url for page,_ in value_errors],
            suggested_action={'summary':'Repair the cited values while preserving their actual subjects and context',
                              'steps':['Use finite monetary numbers rather than booleans or junk', 'Use valid calendar dates',
                                       'Keep supported IRI base/vocabulary/coercion semantics'],
                              'priority':'medium','effort':'low','verification':'Validate the corrected block and re-audit'},
            provenance={'skill':'crawl-render-audit','script':'analyze_machine_readability.py','rule_id':'schema-value-invalid'}))

    if pages and len(no_jsonld) == len(pages):
        # No structured data anywhere -- the coarsest, most severe version of this
        # gap. Kept as its own finding rather than folded into the per-type checks
        # below, since it's evidence about the whole site, not one page type.
        # The absence is observed directly (confirmed), but structured data is
        # optional for indexing: an improvement opportunity, not a high defect.
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement",
            severity=step_down_severity("medium", crawl_ratio),
            status="confirmed", confidence=0.85,
            title="No structured data (JSON-LD) found on any crawled page",
            root_cause="Pages lack schema.org JSON-LD markup"
                       + ("" if crawl_ratio >= 0.999 else
                          f" (observed on the {len(pages)} of "
                          f"{acq_coverage.get('urls_discovered', len(pages))} discovered pages that were "
                          "actually crawled)"),
            evidence=[{"type": "structured_data", "description": f"0/{len(pages)} pages contain JSON-LD",
                       "urls": [p.url for p in pages][:10]}],
            affected_pages=[p.url for p in pages],
            suggested_action={
                "summary": "Add Organization/Product/Article JSON-LD to key pages",
                "steps": ["Identify page types", "Add matching schema.org JSON-LD blocks"],
                "priority": "medium", "effort": "medium",
                "expected_benefit": "Key facts are also stated as explicit structured data; no ranking or citation gain is implied",
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
            if (page.features or {}).get('jsonld_block_count', 0) and not page.jsonld_blocks:
                continue  # Present malformed/unsupported/ambiguous is not absence.
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
                category="ai_discoverability", finding_type="proactive_improvement",
                severity=step_down_severity(spec["severity"], crawl_ratio),
                status="confirmed", confidence=calibrated_confidence(f"page-type-schema-gap:{page_type}", 0.8),
                title=f"{page_type.capitalize()} pages are missing {spec['label']} structured data",
                root_cause=f"{len(urls)} page(s) classified as '{page_type}' carry no "
                           f"{spec['label']} JSON-LD, so explicit machine-readable context may be improved",
                evidence=[{"type": "structured_data",
                           "description": f"{len(urls)} '{page_type}' page(s) missing {spec['label']} markup",
                           "urls": urls[:10]}],
                affected_pages=urls,
                suggested_action={
                    "summary": f"Add {spec['label']} JSON-LD to {page_type} pages",
                    "steps": [f"Add {spec['label']} schema.org JSON-LD matching each {page_type} page's content",
                              "Validate with a schema.org/Rich Results validator"],
                    "priority": spec["severity"], "effort": "medium",
                    "expected_benefit": f"{page_type.capitalize()} facts are also stated as explicit structured data; "
                                        "no ranking, rich-result or citation gain is implied",
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
            affected_pages=[p.url for p in no_headings],
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
                 'schema_value_invalid_pages': len(value_errors), 'schema_value_limitations': len(processing_limits),
                 'currency_membership': 'not_verified; supported format is not ISO membership proof',
                 "crawl_coverage_ratio": round(crawl_ratio, 3)},
        warnings=sorted(set(processing_limits))[:20],
    )
