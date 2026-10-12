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
    about the CRAWLED subgraph. A missing inbound link is a global absence: it
    holds only when every page that could link was observed in full. So the
    graph is complete only when no discovered URL was left unfetched AND every
    fetched page's outgoing links are fully known: a fetch failure or error
    status (other than 404/410), a response cut by the byte budget, a parse
    failure, a link list cut at its cap, a challenge, a waiting room, a login
    page or a page built by JavaScript (its navigation is not in the HTML) each
    leave the graph unresolved (crawl_scope.unresolved says which and why). Even
    the page's own section index is no proof: a news or staff index lists its
    newest or first items and reaches the rest through pagination, "load more"
    scripts or search. On an incomplete graph, orphans and clusters are counted
    and the engagement check does not report them. A complete graph still speaks
    only for the discovered URLs, never for every page of the site.
  - Dead ends are local: a page with no outgoing link in its delivered HTML. It
    is judged only on pages whose links are fully known (link_graph in
    check_helpers.page_observation), whatever the rest of the crawl did.
  - Redirect aliases come from acquisition (acquisition_metadata.url_aliases),
    which records every requested URL that redirected before a duplicate copy
    of the final page is dropped, so a link to a dropped alias still reaches
    the page that was kept.
"""
from check_helpers import page_observation
from models import intermediate_artifact
from url_identity import page_identity

# Ledger scopes that leave a page's outgoing links unknown.
_UNRESOLVED_SCOPES = frozenset({"partial", "fetch_failed", "http_error", "challenge", "waiting_room", "login_page"})
_MAX_UNRESOLVED_LISTED = 20


def page_key(url):
    """Identity of a page URL for link matching: host (lower case, without a
    leading www.), path without a trailing slash, and query
    (url_identity.page_identity). None when the URL cannot be parsed."""
    return page_identity(url)


def _unresolved_observations(artifacts):
    """[{url, reason}] for fetches whose outgoing links are not fully known."""
    out = []
    for record in (artifacts.acquisition_metadata or {}).get("observations") or ():
        scope = record.get("scope")
        status = record.get("http_status")
        if scope == "http_error" and status in (404, 410):
            continue  # a missing page is not a page that could link elsewhere
        reasons = [r for r in record.get("reasons") or () if r in ("link_list_truncated", "script_dependent")]
        if scope in _UNRESOLVED_SCOPES or reasons:
            out.append({"url": record.get("requested_url"),
                        "reason": scope if scope in _UNRESOLVED_SCOPES else reasons[0]})
    # The pages themselves, for snapshots built without a ledger.
    listed = {item["url"] for item in out}
    for p in artifacts.pages:
        seen = page_observation(p)
        if p.url in listed or seen["link_graph"] or seen["status"] == "non_html":
            continue
        if seen["status"] == "http_error" and p.status_code in (404, 410):
            continue
        out.append({"url": p.url, "reason": seen["status"] if seen["status"] != "complete" else seen["reasons"][0]})
    return out


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
    # Requested URLs whose copy acquisition dropped (a second URL redirecting to
    # a page already kept) still resolve to the kept node.
    recorded_aliases = {}
    for requested, final in ((artifacts.acquisition_metadata or {}).get("url_aliases") or {}).items():
        source, target = page_key(requested), page_key(final)
        if source is not None and target in node_url:
            alias.setdefault(source, target)
            recorded_aliases.setdefault(target, set()).add(requested)

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
    # A dead end needs the page's own links fully known: every copy of the node
    # read in full, with no cut link list and no navigation built by JavaScript.
    links_known = {k: all(page_observation(p)["link_graph"] for p in members[k]) for k in keys}
    dead_end_keys = [k for k in keys if out_degree[k] == 0 and links_known[k]]
    dead_ends_unassessed = [k for k in keys if out_degree[k] == 0 and not links_known[k]]

    components = _weakly_connected_components(keys, edges)
    start_component = next((c for c in components if start_key in c), None)
    largest = max(components, key=lambda c: (len(c), sorted(c)), default=set())
    # A start page that reaches no other sampled page says nothing about which
    # pages belong to the site's structure; the largest component does.
    main_component = start_component if start_component is not None and len(start_component) > 1 else largest
    isolated_components = [c for c in components if c is not main_component and c is not start_component]

    coverage = artifacts.acquisition_metadata.get("coverage", {})
    urls_never_attempted = coverage.get("urls_never_attempted", 0)
    unresolved = _unresolved_observations(artifacts)
    complete = urls_never_attempted == 0 and not unresolved

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
            "aliases": sorted(({p.url for p in members[k]} | recorded_aliases.get(k, set())) - {url_of(k)}),
            "links_fully_observed": links_known[k],
        }
        for k in keys
    }

    crawl_scope = {
        "urls_discovered": coverage.get("urls_discovered", len(keys)),
        "urls_analyzed": coverage.get("urls_analyzed", len(keys)),
        "urls_never_attempted": urls_never_attempted,
        # Fetches whose outgoing links are not fully known, and why.
        "unresolved_count": len(unresolved),
        "unresolved": unresolved[:_MAX_UNRESOLVED_LISTED],
        # Only a complete graph can support "nothing among the discovered URLs
        # links to this page"; it never covers pages that were not discovered.
        "complete": complete,
    }

    return intermediate_artifact("site_graph", data={
        "nodes": nodes,
        # Every page nothing in the crawled sample links to; a statement about
        # the discovered URLs only when crawl_scope.complete is True.
        "orphans": sorted(url_of(k) for k in orphan_keys),
        "dead_ends": sorted(url_of(k) for k in dead_end_keys),
        # Pages with no observed outgoing link whose links are not fully known.
        "dead_ends_unassessed": sorted(url_of(k) for k in dead_ends_unassessed),
        "isolated_clusters": sorted(sorted(url_of(k) for k in c) for c in isolated_components),
        "main_cluster_size": len(main_component),
        "crawl_scope": crawl_scope,
    })
