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
import json
from collections.abc import Mapping
from models import skill_result, make_finding, coverage_ratio
from check_helpers import content_pages, meta_value
from identity_signals import best_name
from structured_data import ORGANIZATION_TYPES
from url_keys import template_key

# Expected schema.org @type(s) for each page_type that should realistically carry
# structured data. Types not listed here (e.g. "other", "category") are not held
# to any expectation -- absence there is not evidence of anything.
_EXPECTED_SCHEMA = {
    "service": {"types": {"Service"}, "severity": "low", "label": "Service"},
    "software": {"types": {"SoftwareApplication", "MobileApplication", "WebApplication"}, "severity": "low", "label": "SoftwareApplication"},
    "home": {"types": {"WebSite"} | ORGANIZATION_TYPES, "severity": "high",
             "label": "Organization/WebSite"},
    "product": {"types": {"Product", "Offer"}, "severity": "high", "label": "Product/Offer"},
    "article": {"types": {"Article", "BlogPosting", "NewsArticle"}, "severity": "medium",
                "label": "Article/BlogPosting"},
    "contact": {"types": {"ContactPage"} | ORGANIZATION_TYPES, "severity": "medium",
                "label": "LocalBusiness/Organization/ContactPage"},
    "about": {"types": {"AboutPage"} | ORGANIZATION_TYPES, "severity": "low", "label": "Organization/AboutPage"},
}


from structured_data import iter_nodes, types_of

def _page_jsonld_types(page):
    return set().union(*(types_of(n) for n in iter_nodes(page.jsonld_blocks)))


def proposed_snippet(page, page_type, brand):
    """A ready-to-review JSON-LD draft built only from facts already on the page
    (title, description, canonical, og:image, brand name). Recommend-only: it is
    text in the report, never applied to the site."""
    url = page.canonical_url or page.final_url or page.url
    title = (page.title or '').strip()
    desc = (page.meta_description or meta_value(page, 'og:description') or '').strip()
    image = meta_value(page, 'og:image')
    if page_type == 'home':
        node = {"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "@id": url.rstrip('/') + "/#organization", "name": brand or title,
             "url": url, **({"logo": image} if image else {}), "sameAs": ["<official profile URLs>"]},
            {"@type": "WebSite", "@id": url.rstrip('/') + "/#website", "name": brand or title, "url": url,
             "publisher": {"@id": url.rstrip('/') + "/#organization"}}]}
    elif page_type == 'product':
        node = {"@context": "https://schema.org", "@type": "Product", "name": (page.headings or [title])[0] or title,
                **({"description": desc} if desc else {}), **({"image": image} if image else {}),
                **({"brand": {"@type": "Brand", "name": brand}} if brand else {}),
                "offers": {"@type": "Offer", "price": "<price as shown on page>", "priceCurrency": "<ISO 4217 code>",
                           "availability": "https://schema.org/InStock", "url": url}}
    elif page_type == 'article':
        node = {"@context": "https://schema.org", "@type": "Article", "headline": (page.headings or [title])[0] or title,
                "datePublished": "<ISO 8601 date>", "dateModified": "<ISO 8601 date>",
                "author": {"@type": "Person", "name": "<author>"}, **({"image": image} if image else {}),
                **({"publisher": {"@type": "Organization", "name": brand}} if brand else {})}
    elif page_type in ('contact', 'about'):
        node = {"@context": "https://schema.org", "@type": "ContactPage" if page_type == 'contact' else "AboutPage",
                "url": url, "mainEntity": {"@type": "Organization", "name": brand or title,
                                           "telephone": "<phone>", "address": "<postal address>"}}
    else:
        node = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url,
                **({"description": desc} if desc else {})}
    return json.dumps(node, indent=2, ensure_ascii=False)


def analyze_machine_readability(artifacts, deadline):
    pages = tuple(content_pages(artifacts, require_features=False))
    no_jsonld = [p for p in pages if not p.jsonld_blocks and not (p.features or {}).get("alternative_structured_markup")]
    no_headings = [p for p in pages if not p.headings]

    # Evidence-completeness ratio: these findings only ever speak for the pages
    # actually crawled. "0/N have JSON-LD" is strong evidence when N is most of
    # the discovered site, weaker when the crawl only reached a small slice of it
    # -- confidence/severity below are scaled accordingly.
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
            status="confirmed", confidence=0.9,
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

    # Page-type gaps are always computed (previously skipped when the site had no
    # JSON-LD at all, which left only a generic "add Organization/Product/Article").
    by_type_gaps = {}
    for page in pages:
        spec = _EXPECTED_SCHEMA.get(page.page_type)
        if not spec or (page.features or {}).get("alternative_structured_markup"):
            continue
        if not (_page_jsonld_types(page) & spec["types"]):
            by_type_gaps.setdefault(page.page_type, []).append(page)
    brand = best_name(pages, artifacts.normalized_origin)

    if pages and len(no_jsonld) == len(pages):
        # No structured data anywhere: one site-wide finding whose steps name every
        # page type found and attach a draft snippet per type (recommend-only).
        type_steps = [f"{t.capitalize()} pages ({len(ps)} sampled, e.g. {ps[0].url}): add {_EXPECTED_SCHEMA[t]['label']}"
                      for t, ps in sorted(by_type_gaps.items(), key=lambda kv: -len(kv[1]))]
        drafts = {}
        home = next((p for p in pages if p.page_type == 'home'), pages[0])
        drafts[home.url] = proposed_snippet(home, 'home', brand)
        for t, ps in sorted(by_type_gaps.items()):
            if t != 'home' and len(drafts) < 4:
                drafts[ps[0].url] = proposed_snippet(ps[0], t, brand)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="high",
            status="confirmed", confidence=0.85,
            title="No structured data (JSON-LD) found on any crawled page",
            root_cause="None of the sampled pages carries schema.org JSON-LD or microdata, so entity type, identity, "
                       "prices and dates must be inferred from free text"
                       + ("" if crawl_ratio >= 0.999 else
                          f" (observed on the {len(pages)} pages actually crawled out of "
                          f"{acq_coverage.get('urls_discovered', len(pages))} discovered)"),
            evidence=[{"type": "structured_data", "description": f"0/{len(pages)} sampled pages contain JSON-LD",
                       "urls": [p.url for p in pages][:10]}],
            affected_pages=[p.url for p in pages],
            suggested_action={
                "summary": "Add JSON-LD matching each page type, starting with Organization/WebSite on the homepage",
                "steps": [f"Homepage ({home.url}): add Organization + WebSite with name, url, logo and sameAs"]
                         + type_steps[:5] + ["Validate every block with a schema.org validator before release"],
                "priority": "high", "effort": "medium",
                "expected_benefit": "Facts become machine-extractable and the brand is disambiguated",
                "verification": "Re-run the audit: no-jsonld disappears and the page-type checks pass",
                "proposed_snippets": drafts,
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py",
                        "rule_id": "no-jsonld"},
        ))
        # The denominator behind this absence claim: the pages this check
        # could judge, which is what scoring uses for its sample strength.
        findings[-1]["assessed_pages"] = len(pages)
        findings[-1]["assessed_templates"] = len({template_key(p.url) for p in pages})
    else:
        # Some structured data exists somewhere -- check it's the RIGHT structured
        # data for each page's role, per type.
        for page_type, gap_pages in by_type_gaps.items():
            spec = _EXPECTED_SCHEMA[page_type]
            urls = [p.url for p in gap_pages]
            findings.append(make_finding(
                category="ai_discoverability", finding_type="defect",
                severity=spec["severity"], status="confirmed", confidence=0.8,
                title=f"{page_type.capitalize()} pages are missing {spec['label']} structured data",
                root_cause=f"{len(urls)} page(s) classified as '{page_type}' carry no "
                           f"{spec['label']} JSON-LD, so explicit machine-readable context is missing",
                evidence=[{"type": "structured_data",
                           "description": f"{len(urls)} '{page_type}' page(s) missing {spec['label']} markup",
                           "urls": urls[:10]}],
                affected_pages=urls,
                suggested_action={
                    "summary": f"Add {spec['label']} JSON-LD to {page_type} pages",
                    "steps": [f"Add {spec['label']} schema.org JSON-LD matching each {page_type} page's content",
                              "Validate with a schema.org/Rich Results validator"],
                    "priority": spec["severity"], "effort": "medium",
                    "expected_benefit": f"{page_type.capitalize()} facts become machine-extractable and citable",
                    "verification": "Re-crawl and confirm the expected @type is present",
                    "proposed_snippets": {gap_pages[0].url: proposed_snippet(gap_pages[0], page_type, brand)},
                },
                provenance={"skill": "crawl-render-audit", "script": "analyze_machine_readability.py",
                            "rule_id": f"page-type-schema-gap:{page_type}"},
            ))

    if no_headings:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.7,
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
        findings[-1]["assessed_pages"] = len(pages)
        findings[-1]["assessed_templates"] = len({template_key(p.url) for p in pages})

    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"pages_with_jsonld": len(pages) - len(no_jsonld), "pages_without_headings": len(no_headings),
                 "crawl_coverage_ratio": round(crawl_ratio, 3)},
    )
