"""analyze_engagement.py -- navigation, orphans, dead ends, breadcrumb cross-check.
Consumes artifacts, site_graph, and rendering_result; runs in the dependent batch
so it overlaps external-analysis work; never writes to either input.
"""
from models import skill_result, make_finding, coverage_ratio, scale_confidence

_ANALYZED_KEY = "urls_analyzed"
_DISCOVERED_KEY = "urls_discovered"


def analyze_engagement(artifacts, site_graph, rendering_result, deadline):
    from analyze_experience import analyze_experience
    findings = analyze_experience(artifacts, deadline)["findings"]
    graph = site_graph.get("data", {})
    orphans = graph.get("orphans", [])
    dead_ends = graph.get("dead_ends", [])
    isolated_clusters = graph.get("isolated_clusters", [])
    crawl_scope = graph.get("crawl_scope", {"complete": True, "urls_never_attempted": 0})
    crawl_complete = crawl_scope.get("complete", True)
    # Proportional evidence-completeness ratio (Round-3 review item 1): a crawl
    # that reached 45/50 discovered pages is much stronger evidence for an orphan
    # finding than one that reached 5/50, even though both are technically
    # "incomplete". This replaces the previous complete/incomplete binary
    # (confidence 0.75 vs 0.5) with a proportional scale; status (confirmed vs.
    # suspected) stays binary since that's a statement about certainty of kind,
    # not degree.
    graph_ratio = coverage_ratio(
        crawl_scope.get(_ANALYZED_KEY, len(graph.get("nodes", {}))),
        crawl_scope.get(_DISCOVERED_KEY, len(graph.get("nodes", {}))),
    )

    if orphans:
        # Orphan status is a statement about the crawled subgraph only. When the
        # crawl didn't reach every discovered URL, a page that looks orphaned here
        # may actually be linked from a page that was never fetched -- so this is
        # reported as suspected, with a note on the incomplete scope, rather than
        # confirmed, whenever coverage is incomplete.
        status = "confirmed" if crawl_complete else "suspected"
        confidence = scale_confidence(0.75, graph_ratio)
        root_cause = "Pages exist but are not linked from anywhere else on the site"
        if not crawl_complete:
            root_cause += (
                f" (within the {len(graph.get('nodes', {}))} pages actually crawled; "
                f"{crawl_scope.get('urls_never_attempted', 0)} discovered URLs were never fetched, "
                "so a linking page may simply not have been crawled)"
            )
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity="medium",
            status=status, confidence=confidence,
            title="Orphan pages with no internal links pointing to them",
            root_cause=root_cause,
            evidence=[{"type": "site_graph", "description": f"{len(orphans)} orphan pages found",
                       "urls": orphans[:10]}],
            suggested_action={
                "summary": "Add internal links to orphan pages from relevant navigation or content",
                "steps": ["Identify high-value orphan pages", "Link them from navigation or related content"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Improves discoverability and visitor navigation",
                "verification": "Confirm pages have inbound internal links",
            },
            provenance={"skill": "engagement-audit", "script": "analyze_engagement.py",
                        "rule_id": "orphan-pages"},
        ))

    if isolated_clusters:
        # A disconnected cluster of pages (reachable from each other, but not from
        # the main site graph) is a bigger structural problem than N unrelated
        # orphan pages, and calls for a different fix (link the section into
        # navigation, not link each page individually).
        total_isolated_pages = sum(len(c) for c in isolated_clusters)
        status = "confirmed" if crawl_complete else "suspected"
        confidence = scale_confidence(0.7, graph_ratio)
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity="medium",
            status=status, confidence=confidence,
            title="Isolated page clusters not reachable from the main site structure",
            root_cause=f"{len(isolated_clusters)} cluster(s) totalling {total_isolated_pages} page(s) are "
                       "internally linked to each other but have no path from the main navigation/homepage"
                       + ("" if crawl_complete else " (crawl coverage was incomplete, so this may include "
                                                     "clusters only reachable from uncrawled pages)"),
            evidence=[{"type": "site_graph", "description": f"Isolated cluster of {len(c)} page(s)",
                       "urls": c[:10]} for c in isolated_clusters[:5]],
            suggested_action={
                "summary": "Link isolated page clusters into the main navigation structure",
                "steps": ["Identify which cluster(s) contain valuable content",
                          "Add navigation or contextual links connecting them to the main site"],
                "priority": "medium", "effort": "medium",
                "expected_benefit": "Makes an entire section reachable instead of one page at a time",
                "verification": "Re-run and confirm the cluster merges into the main component",
            },
            provenance={"skill": "engagement-audit", "script": "analyze_engagement.py",
                        "rule_id": "isolated-clusters"},
        ))

    if dead_ends:
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.7,
            title="Dead-end pages with no outgoing links",
            root_cause="Pages provide no next step for the visitor",
            evidence=[{"type": "site_graph", "description": f"{len(dead_ends)} dead-end pages found",
                       "urls": dead_ends[:10]}],
            suggested_action={
                "summary": "Add related links or calls-to-action on dead-end pages",
                "steps": ["Add related-content links", "Add a clear next-step call-to-action"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Keeps visitors engaged longer",
                "verification": "Confirm pages link to at least one next step",
            },
            provenance={"skill": "engagement-audit", "script": "analyze_engagement.py",
                        "rule_id": "dead-ends"},
        ))

    breadcrumb_mismatches = [p.url for p in artifacts.pages if p.breadcrumb_visible and not p.breadcrumb_schema]
    # Lightweight visitor-orientation checks adapted from AS. These use only the
    # immutable acquisition snapshot and are deliberately conservative: absence is
    # reported only when the sampled evidence is sufficient to support it.
    home = next((p for p in artifacts.pages if p.status_code == 200 and p.page_type == "home"), None)
    if home:
        home_text = (home.visible_text or "").lower()
        if len(home_text.split()) > 250 and not any(len(h.split()) <= 14 for h in home.headings[:3]):
            findings.append(make_finding(
                category="engagement", finding_type="proactive_improvement", severity="low",
                status="confirmed", confidence=0.62,
                title="Homepage content may need stronger above-the-fold orientation",
                root_cause="The sampled homepage contains substantial text but no short heading signal was observed in its first heading entries",
                evidence=[{"type": "orientation", "description": f"Homepage contains approximately {len(home_text.split())} visible words; first headings: {list(home.headings[:3])}"}],
                suggested_action={
                    "summary": "Lead with a concise value proposition and one primary next step",
                    "steps": ["State what the organization offers and for whom in the first viewport", "Use a descriptive H1 and scannable H2 sections", "Place one relevant CTA near the opening content"],
                    "priority": "low", "effort": "low",
                    "expected_benefit": "Visitors arriving from an AI answer can orient quickly and continue to a relevant action",
                    "verification": "Review the first viewport on mobile and desktop"},
                provenance={"skill": "engagement-audit", "script": "analyze_engagement.py", "rule_id": "homepage-orientation"},
                affected_pages=[home.url]))

    # Navigation is judged on HTML pages only: a fetched Markdown or PDF file has no
    # navigation to offer.
    html_pages = [p for p in artifacts.pages if p.status_code == 200 and "non_html_content" not in p.warnings]
    if len(html_pages) >= 3:
        # Do not infer a missing nav from flattened headings; use link density and
        # cross-page reachability instead, which is observable in this artifact model.
        pages_with_links = sum(1 for p in html_pages if p.internal_links)
        if pages_with_links == 0:
            findings.append(make_finding(
                category="engagement", finding_type="defect", severity="medium",
                status="confirmed", confidence=0.78,
                title="Sampled pages expose no internal navigation links",
                root_cause="Visitors landing on the sampled pages have no observed internal link path to related content",
                evidence=[{"type": "navigation", "description": f"0/{len(html_pages)} sampled pages contain internal links", "urls": [p.url for p in html_pages[:10]]}],
                suggested_action={
                    "summary": "Add persistent navigation and contextual next-step links",
                    "steps": ["Expose primary destinations in a semantic nav landmark", "Link related pages from body content", "Ensure every important landing page has a clear next step"],
                    "priority": "medium", "effort": "medium",
                    "expected_benefit": "Reduces dead ends and helps both visitors and crawlers discover deeper content",
                    "verification": "Re-crawl and confirm internal links connect the important page types"},
                provenance={"skill": "engagement-audit", "script": "analyze_engagement.py", "rule_id": "no-internal-navigation"}))

    if breadcrumb_mismatches:
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.65,
            title="Visible breadcrumbs lack matching BreadcrumbList structured data",
            root_cause="Breadcrumb navigation is visible but not machine-readable",
            evidence=[{"type": "breadcrumb", "description": "Visible breadcrumb without schema",
                       "urls": breadcrumb_mismatches[:10]}],
            suggested_action={
                "summary": "Add BreadcrumbList JSON-LD matching visible breadcrumbs",
                "steps": ["Add BreadcrumbList schema to pages with visible breadcrumbs"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Improves machine understanding of site structure",
                "verification": "Validate BreadcrumbList JSON-LD",
            },
            provenance={"skill": "engagement-audit", "script": "analyze_engagement.py",
                        "rule_id": "breadcrumb-mismatch"},
        ))

    gap_pages = rendering_result.get("metrics", {}).get("raw_rendered_gap_pages", [])
    return skill_result(
        "engagement-audit", findings=findings,
        metrics={"orphan_pages": len(orphans), "dead_end_pages": len(dead_ends),
                 "isolated_clusters": len(isolated_clusters),
                 "rendering_gap_pages": len(gap_pages),
                 "crawl_scope_complete": crawl_complete},
        coverage={"pages_analyzed": len(graph.get("nodes", {})), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
