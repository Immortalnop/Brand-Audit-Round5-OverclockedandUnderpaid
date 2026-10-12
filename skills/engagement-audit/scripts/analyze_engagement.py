"""analyze_engagement.py -- navigation, orphans, dead ends, breadcrumb cross-check.
Consumes artifacts, site_graph, and rendering_result; runs in the dependent batch
so it overlaps external-analysis work; never writes to either input.
"""
from check_helpers import page_observation
from models import skill_result, make_finding


def analyze_engagement(artifacts, site_graph, rendering_result, deadline):
    from analyze_experience import analyze_experience
    experience = analyze_experience(artifacts, deadline)
    findings = experience["findings"]
    graph = site_graph.get("data", {})
    orphans = graph.get("orphans", [])
    dead_ends = graph.get("dead_ends", [])
    isolated_clusters = graph.get("isolated_clusters", [])
    crawl_scope = graph.get("crawl_scope", {"complete": True, "urls_never_attempted": 0})
    crawl_complete = crawl_scope.get("complete", True)

    # Orphan and cluster status is a statement about the crawled subgraph only.
    # A complete crawl makes it a whole-site statement. A sampled crawl cannot:
    # a page nothing in the sample links to may be linked from a page that was
    # never fetched, and even its own section index may reach it only through
    # pagination or a "load more" script (build_site_graph.py). So both are
    # reported on complete crawls only; on a sample they are counted in metrics.
    reported_orphans = orphans if crawl_complete else []
    if reported_orphans:
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity="medium",
            status="confirmed", confidence=0.75,
            title="Orphan pages with no internal links pointing to them",
            root_cause="Pages exist but are not linked from anywhere else on the site",
            evidence=[{"type": "site_graph",
                       "description": f"{len(reported_orphans)} page(s) that none of the "
                                      f"{crawl_scope.get('urls_discovered', len(graph.get('nodes') or ()))} discovered "
                                      "URLs links to; every discovered URL was fetched and its links were read in full. "
                                      "Pages the crawl did not discover were not checked",
                       "urls": reported_orphans[:10]}],
            affected_pages=reported_orphans,
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

    if isolated_clusters and crawl_complete:
        # A disconnected cluster of pages (reachable from each other, but not from
        # the main site graph) is a bigger structural problem than N unrelated
        # orphan pages, and calls for a different fix (link the section into
        # navigation, not link each page individually).
        total_isolated_pages = sum(len(c) for c in isolated_clusters)
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity="medium",
            status="confirmed", confidence=0.7,
            title="Isolated page clusters not reachable from the main site structure",
            root_cause=f"{len(isolated_clusters)} cluster(s) totalling {total_isolated_pages} page(s) are "
                       "internally linked to each other but have no path from the main navigation/homepage",
            evidence=[{"type": "site_graph", "description": f"Isolated cluster of {len(c)} page(s)",
                       "urls": c[:10]} for c in isolated_clusters[:5]],
            affected_pages=[u for c in isolated_clusters for u in c],
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
            root_cause="The delivered HTML of these pages links to no other page of the site, so a visitor or crawler "
                       "reading it has no next step",
            evidence=[{"type": "site_graph",
                       "description": f"{len(dead_ends)} page(s) whose delivered HTML, read in full, has no link to "
                                      "another page of the site",
                       "urls": dead_ends[:10]}],
            affected_pages=dead_ends,
            suggested_action={
                "summary": "Add related links or calls-to-action on dead-end pages",
                "steps": ["Add related-content links", "Add a clear next-step call-to-action"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Each listed page offers a next step; visitor behaviour is not measured",
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
                title="Homepage opening headings do not state a short value proposition",
                root_cause="The sampled homepage contains substantial text but none of its first three headings, in source "
                           "order, is short; source order does not establish what appears in the first screen",
                evidence=[{"type": "orientation", "description": f"Homepage contains approximately {len(home_text.split())} visible words; first headings: {list(home.headings[:3])}"}],
                suggested_action={
                    "summary": "Lead with a concise value proposition and one primary next step",
                    "steps": ["State what the organization offers and for whom in the first viewport", "Use a descriptive H1 and scannable H2 sections", "Place one relevant CTA near the opening content"],
                    "priority": "low", "effort": "low",
                    "expected_benefit": "The homepage opens with a short statement of what it offers; visitor behaviour is not measured",
                    "verification": "Re-run the audit and confirm one of the first three headings is short; check the first screen on mobile and desktop in a browser"},
                provenance={"skill": "engagement-audit", "script": "analyze_engagement.py", "rule_id": "homepage-orientation"},
                affected_pages=[home.url]))

    # Navigation is judged on HTML pages only: a fetched Markdown or PDF file has no
    # navigation to offer.
    # A page built by JavaScript, or one not read in full, may have navigation
    # its delivered HTML does not show: "no links in the HTML" is not "visitors
    # cannot navigate". Only pages whose links are fully known are judged.
    html_pages = [p for p in artifacts.pages if p.status_code == 200 and "non_html_content" not in p.warnings]
    judged = [p for p in html_pages if page_observation(p)["link_graph"]]
    if len(judged) >= 3 and len(judged) == len(html_pages):
        # Do not infer a missing nav from flattened headings; use link density and
        # cross-page reachability instead, which is observable in this artifact model.
        pages_with_links = sum(1 for p in judged if p.internal_links)
        if pages_with_links == 0:
            findings.append(make_finding(
                category="engagement", finding_type="defect", severity="medium",
                status="confirmed", confidence=0.78,
                title="Sampled pages expose no internal navigation links",
                root_cause="The delivered HTML of the sampled pages, read in full, links to no other page of the site",
                evidence=[{"type": "navigation", "description": f"0/{len(judged)} sampled pages contain internal links in "
                                                                "their delivered HTML", "urls": [p.url for p in judged[:10]]}],
                affected_pages=[p.url for p in judged],
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
            affected_pages=breadcrumb_mismatches,
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
    warnings = list(experience.get("warnings") or ())
    if not crawl_complete and graph.get("nodes"):
        unresolved = crawl_scope.get("unresolved_count", 0)
        warnings.append("Orphan pages and isolated page clusters were not assessed: "
                        + ("the crawl analyzed a sample, and a page the sample does not link to may be linked from a "
                           "page that was not fetched." if crawl_scope.get("urls_never_attempted")
                           else f"{unresolved} fetched page(s) could not be read in full or build their links with "
                                "JavaScript (see the site graph's crawl_scope.unresolved), so links from them are "
                                "unknown."))
    unassessed_dead_ends = graph.get("dead_ends_unassessed") or []
    if unassessed_dead_ends:
        warnings.append(f"{len(unassessed_dead_ends)} page(s) show no outgoing link in their delivered HTML but were not "
                        "judged as dead ends: the HTML was not read in full or the page builds its content with "
                        "JavaScript, so its real navigation is unknown.")
    return skill_result(
        "engagement-audit", findings=findings, warnings=warnings,
        metrics={"orphan_pages": len(orphans), "orphan_pages_reported": len(reported_orphans),
                 "dead_end_pages": len(dead_ends),
                 "isolated_clusters": len(isolated_clusters),
                 "isolated_clusters_reported": len(isolated_clusters) if crawl_complete else 0,
                 "rendering_gap_pages": len(gap_pages),
                 "dead_end_pages_unassessed": len(unassessed_dead_ends),
                 "duplicate_titles_suppressed": (experience.get("metrics") or {}).get("duplicate_titles_suppressed", []),
                 "crawl_scope_complete": crawl_complete},
        coverage={"pages_analyzed": len(graph.get("nodes", {})), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
