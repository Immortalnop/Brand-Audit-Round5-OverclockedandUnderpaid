"""build_site_graph.py -- immutable graph artifact: degree, orphan/dead-end status,
clusters, importance, and crawl-scope accounting.

Nodes are pages as a visitor reaches them: a crawled URL that redirected is the
page at its final URL, and several URLs that redirect to one page are one node.
A link reaches a node when it points at the node's requested or final URL; a
trailing slash, letter case in the host and the scheme do not matter. Without
this, every redirected URL would look like a page that nothing links to.

Beyond flat in/out-degree:
  - Weakly-connected clusters: in-degree alone can't tell "one orphan page" apart
    from "a whole sub-section of the site that's disconnected from the main
    navigation" -- the latter is a much bigger engagement problem and needs its
    own finding, not N separate orphan-page findings. The main component is the
    one that holds the start page, unless the start page reaches no other
    sampled page (a splash or language chooser, or a page built by JavaScript):
    then it is the largest component, and the start page's own component is not
    reported as isolated.
  - Crawl-scope accounting: orphan and cluster status is only ever a statement
    about the CRAWLED subgraph. When the crawl did not reach every discovered URL
    (a sample of a large sitemap, MAX_PAGES_CRAWLED, MAX_CRAWL_DEPTH or the
    deadline), a page that nothing in the sample links to may be linked from a
    page that was never fetched, and a group of pages whose linking pages were
    not fetched looks exactly like an isolated one. Even the page's own section
    index is no proof: a news or staff index lists its newest or first items and
    reaches the rest through pagination, "load more" scripts or search. So on an
    incomplete crawl, orphans and clusters are counted (crawl_scope.complete is
    False) and the engagement check does not report them.
"""
from urllib.parse import urlsplit

from models import intermediate_artifact


def page_key(url):
    """Identity of a page URL for link matching: host (lower case, without a
    leading www.), path without a trailing slash, and query. None when the URL
    cannot be parsed."""
    try:
        p = urlsplit(url or "")
    except ValueError:
        return None
    host = (p.hostname or "").lower()
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]
    path = (p.path or "/").rstrip("/") or "/"
    return host, path, p.query


def _weakly_connected_components(keys, edges):
    adjacency = {k: set() for k in keys}
    for source, targets in edges.items():
        for target in targets:
            adjacency[source].add(target)
            adjacency[target].add(source)
    visited = set()
    components = []
    for start in sorted(keys):
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

    # One node per final URL. alias maps every requested and final URL key to it.
    node_url, alias, members = {}, {}, {}
    for p in pages:
        key = page_key(p.final_url or p.url) or page_key(p.url)
        if key is None:
            continue
        if key not in node_url:
            node_url[key] = p.final_url or p.url
            members[key] = []
        members[key].append(p)
        for u in (p.url, p.final_url):
            k = page_key(u)
            if k is not None:
                alias.setdefault(k, key)

    keys = sorted(node_url)
    edges = {k: set() for k in keys}
    out_links = {k: set() for k in keys}
    for key in keys:
        for p in members[key]:
            for link in p.internal_links:
                lk = page_key(link)
                if lk is None:
                    continue
                target = alias.get(lk, lk)
                if target == key:
                    continue  # a link to the page itself is no way onward
                out_links[key].add(target)
                if target in edges:
                    edges[key].add(target)

    in_degree = {k: 0 for k in keys}
    for source in keys:
        for target in edges[source]:
            in_degree[target] += 1
    out_degree = {k: len(out_links[k]) for k in keys}

    start_key = alias.get(page_key(artifacts.site_url)) if page_key(artifacts.site_url) else None
    orphan_keys = [k for k in keys if in_degree[k] == 0 and k != start_key]
    dead_end_keys = [k for k in keys if out_degree[k] == 0]

    components = _weakly_connected_components(keys, edges)
    start_component = next((c for c in components if start_key in c), None)
    largest = max(components, key=lambda c: (len(c), sorted(c)), default=set())
    # A start page that reaches no other sampled page says nothing about which
    # pages belong to the site's structure; the largest component does.
    main_component = start_component if start_component is not None and len(start_component) > 1 else largest
    isolated_components = [c for c in components if c is not main_component and c is not start_component]

    coverage = artifacts.acquisition_metadata.get("coverage", {})
    urls_never_attempted = coverage.get("urls_never_attempted", 0)
    complete = urls_never_attempted == 0

    cluster_id_by_key = {}
    for idx, component in enumerate(components):
        for k in component:
            cluster_id_by_key[k] = idx

    url_of = node_url.__getitem__
    nodes = {
        url_of(k): {
            "in_degree": in_degree[k],
            "out_degree": out_degree[k],
            "is_orphan": k in orphan_keys,
            "is_dead_end": k in dead_end_keys,
            "cluster_id": cluster_id_by_key.get(k, 0),
            "importance": min(1.0, in_degree[k] / max(1, len(keys))),
            "aliases": sorted({p.url for p in members[k]} - {url_of(k)}),
        }
        for k in keys
    }

    crawl_scope = {
        "urls_discovered": coverage.get("urls_discovered", len(keys)),
        "urls_analyzed": coverage.get("urls_analyzed", len(keys)),
        "urls_never_attempted": urls_never_attempted,
        # Only a complete crawl can turn "orphan/dead-end within the crawled
        # subgraph" into a confirmed, whole-site statement.
        "complete": complete,
    }

    return intermediate_artifact("site_graph", data={
        "nodes": nodes,
        # Every page nothing in the crawled sample links to; a whole-site
        # statement only when crawl_scope.complete is True.
        "orphans": sorted(url_of(k) for k in orphan_keys),
        "dead_ends": sorted(url_of(k) for k in dead_end_keys),
        "isolated_clusters": sorted(sorted(url_of(k) for k in c) for c in isolated_components),
        "main_cluster_size": len(main_component),
        "crawl_scope": crawl_scope,
    })
