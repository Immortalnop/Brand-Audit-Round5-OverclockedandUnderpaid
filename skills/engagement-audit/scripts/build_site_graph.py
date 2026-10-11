"""build_site_graph.py -- immutable graph artifact: degree, orphan/dead-end status,
clusters, importance, and crawl-scope accounting.

Two additions beyond flat in/out-degree:
  - Weakly-connected clusters: in-degree alone can't tell "one orphan page" apart
    from "a whole sub-section of the site that's disconnected from the main
    navigation" -- the latter is a much bigger engagement problem and needs its
    own finding, not N separate orphan-page findings.
  - Crawl-scope accounting: orphan/dead-end status is only ever a statement about
    the CRAWLED subgraph. If the crawl didn't reach every discovered URL (hit
    MAX_PAGES_CRAWLED, MAX_CRAWL_DEPTH, or the deadline), a page that looks like an
    orphan here might actually be linked from a page that was never fetched -- so
    that must be recorded and surfaced, not silently treated as equivalent to a
    complete-crawl orphan finding.
"""
from models import intermediate_artifact


def _weakly_connected_components(urls, pages):
    adjacency = {u: set() for u in urls}
    for p in pages:
        for link in p.internal_links:
            if link in adjacency:
                adjacency[p.url].add(link)
                adjacency[link].add(p.url)

    visited = set()
    components = []
    for start in sorted(urls):
        if start in visited:
            continue
        stack = [start]
        component = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(sorted(adjacency[node] - component))
        visited |= component
        components.append(component)
    return components


def build_site_graph(artifacts, deadline):
    # Only HTML pages are nodes. A Markdown, text or PDF file the crawl fetched
    # (an llms.txt target such as /agents.md) has no navigation to link out with
    # and is not a page a visitor browses, so it is never an orphan or dead end.
    pages = tuple(p for p in artifacts.pages if p.status_code == 200 and "non_html_content" not in p.warnings)
    urls = sorted({p.url for p in pages})
    in_degree = {u: 0 for u in urls}
    out_degree = {u: 0 for u in urls}
    for p in pages:
        out_degree[p.url] = len(p.internal_links)
        for link in p.internal_links:
            if link in in_degree:
                in_degree[link] += 1

    orphans = [u for u in urls if in_degree.get(u, 0) == 0 and u != artifacts.site_url]
    dead_ends = [u for u in urls if out_degree.get(u, 0) == 0]

    components = _weakly_connected_components(urls, pages)
    main_component = next((c for c in components if artifacts.site_url in c), max(components, key=len, default=set()))
    isolated_clusters = [sorted(c) for c in components if c is not main_component and len(c) > 0]
    cluster_id_by_url = {}
    for idx, component in enumerate(components):
        for u in component:
            cluster_id_by_url[u] = idx

    nodes = {
        u: {
            "in_degree": in_degree.get(u, 0),
            "out_degree": out_degree.get(u, 0),
            "is_orphan": u in orphans,
            "is_dead_end": u in dead_ends,
            "cluster_id": cluster_id_by_url.get(u, 0),
            "importance": min(1.0, in_degree.get(u, 0) / max(1, len(urls))),
        }
        for u in urls
    }

    coverage = artifacts.acquisition_metadata.get("coverage", {})
    urls_never_attempted = coverage.get("urls_never_attempted", 0)
    crawl_scope = {
        "urls_discovered": coverage.get("urls_discovered", len(urls)),
        "urls_analyzed": coverage.get("urls_analyzed", len(urls)),
        "urls_never_attempted": urls_never_attempted,
        # Only a complete crawl can turn "orphan/dead-end within the crawled
        # subgraph" into a confirmed, whole-site statement.
        "complete": urls_never_attempted == 0,
    }

    return intermediate_artifact("site_graph", data={
        "nodes": nodes, "orphans": orphans, "dead_ends": dead_ends,
        "isolated_clusters": isolated_clusters, "main_cluster_size": len(main_component),
        "crawl_scope": crawl_scope,
    })
