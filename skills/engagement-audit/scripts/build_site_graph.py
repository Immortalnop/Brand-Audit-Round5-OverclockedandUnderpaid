"""build_site_graph.py -- immutable graph artifact: degree, orphan/dead-end status,
clusters, importance, and crawl-scope accounting.

Four things beyond flat in/out-degree, each of them a limit on what the graph is
allowed to claim:

  - Weakly-connected clusters: in-degree alone can't tell "one orphan page" apart
    from "a whole sub-section of the site that's disconnected from the main
    navigation" -- the latter is a much bigger engagement problem and needs its
    own finding, not N separate orphan-page findings.

  - Final-page identity. Nodes are keyed by the page that was actually DELIVERED,
    not by the URL that was requested. If /a and /b both redirect to /c, that is
    one page with two aliases, not two nodes -- and a link to either alias is a
    link to the same node. Keying by requested URL inflated the node count and
    split the inbound links of one page across two entries, which could make a
    well-linked page look like an orphan.

  - Link evidence completeness, not just crawl completeness. An orphan is a claim
    about every page that *could* have linked to it. That claim needs each of
    those pages to have been read, so "complete" requires more than "no URL was
    left unattempted": a discovered URL that answered 503, timed out, was
    refused by robots or returned a bot challenge is a page whose outbound links
    were never seen. Excluding the failed node from the graph does not supply the
    inbound links it might have carried. link_evidence is a ledger of exactly
    that, and `complete` is true only when nothing is missing from it.

  - Raw-versus-rendered scope. This graph is built from delivered HTML. A page
    whose navigation is assembled by JavaScript delivers no links in that HTML,
    so calling it a dead end, or counting it toward "no page exposes internal
    navigation", states a rendering fact as an engagement defect. Such nodes are
    marked raw_shell, kept out of the dead-end set and out of the outbound-link
    denominator, and reported separately in rendering_scope.
"""
from models import intermediate_artifact
from url_keys import visit_key
from check_helpers import content_pages, is_challenged

# Warnings that mean a discovered URL's outbound links were never observed, so
# any absence-of-inbound-links claim about other pages is incomplete.
_UNREAD_WARNINGS = ('fetch_timeout', 'bot_challenge', 'rate_limited', 'response_truncated_at_byte_budget',
                    'html_parse_incomplete')


def _weakly_connected_components(urls, adjacency):
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


def _raw_shell(page):
    """Does this page's navigation live in JavaScript rather than in the HTML we
    were served? True only when the delivered HTML has no internal links AND the
    page can build them in the browser (an empty SPA mount node, or scripts plus
    a hydration payload). A genuinely link-free static page is not a shell."""
    if page.internal_links:
        return False
    f = page.features or {}
    if f.get('spa_mount_empty'):
        return True
    return bool(f.get('executable_scripts')) and bool(f.get('hydration_strings'))


def _identity_map(pages):
    """(node key -> representative URL, alias URL -> node key, node -> aliases).

    One node per delivered page. The representative URL is the shortest requested
    URL that reached it, so the node is named by the canonical-looking address."""
    by_identity = {}
    for p in pages:
        key = visit_key(p.final_url or p.url)
        by_identity.setdefault(key, []).append(p)
    representative, alias_to_key, aliases = {}, {}, {}
    for key, group in by_identity.items():
        urls = sorted({p.url for p in group} | {p.final_url for p in group if p.final_url},
                      key=lambda u: (len(u), u))
        representative[key] = urls[0]
        aliases[key] = urls
        for u in urls:
            alias_to_key.setdefault(visit_key(u), key)
    return representative, alias_to_key, aliases


def build_site_graph(artifacts, deadline):
    # Only real content pages are graph nodes: a bot-challenge interstitial has no
    # links and would otherwise show up as a "dead end".
    pages = tuple(content_pages(artifacts, require_features=False))
    representative, alias_to_key, aliases = _identity_map(pages)
    node_keys = sorted(representative)
    urls = [representative[k] for k in node_keys]
    url_of = representative

    # Every page that reached a node contributes that node's outbound links.
    out_links, shell = {k: set() for k in node_keys}, {}
    for p in pages:
        key = visit_key(p.final_url or p.url)
        for link in p.internal_links:
            target = alias_to_key.get(visit_key(link))
            if target is not None and target != key:
                out_links[key].add(target)
        shell[key] = shell.get(key, True) and _raw_shell(p)

    in_degree = {k: 0 for k in node_keys}
    out_degree = {k: len(out_links[k]) for k in node_keys}
    for key in node_keys:
        for target in out_links[key]:
            in_degree[target] += 1

    adjacency = {k: set() for k in node_keys}
    for key in node_keys:
        for target in out_links[key]:
            adjacency[key].add(target)
            adjacency[target].add(key)

    home_key = alias_to_key.get(visit_key(artifacts.site_url))
    orphans = [url_of[k] for k in node_keys if in_degree[k] == 0 and k != home_key]
    # A page whose links are built by JavaScript delivers none in the HTML we
    # read; that is a rendering observation, not a dead end.
    dead_ends = [url_of[k] for k in node_keys if out_degree[k] == 0 and not shell[k]]
    raw_shell_pages = [url_of[k] for k in node_keys if shell[k]]

    components = _weakly_connected_components(node_keys, adjacency)
    main_component = next((c for c in components if home_key in c), max(components, key=len, default=set()))
    isolated_clusters = [sorted(url_of[k] for k in c) for c in components if c is not main_component and c]
    cluster_id_by_key = {}
    for idx, component in enumerate(components):
        for k in component:
            cluster_id_by_key[k] = idx

    nodes = {
        url_of[k]: {
            "in_degree": in_degree[k],
            "out_degree": out_degree[k],
            "is_orphan": url_of[k] in orphans,
            "is_dead_end": url_of[k] in dead_ends,
            "raw_shell": shell[k],
            "aliases": [u for u in aliases[k] if u != url_of[k]],
            "cluster_id": cluster_id_by_key.get(k, 0),
            "importance": min(1.0, in_degree[k] / max(1, len(node_keys))),
        }
        for k in node_keys
    }

    coverage = artifacts.acquisition_metadata.get("coverage", {})
    never_attempted = coverage.get("urls_never_attempted", 0) or 0
    # Pages that were fetched but whose links could not be read. Their outbound
    # links are missing from this graph, so an orphan elsewhere may simply be
    # linked from one of them.
    unread = [p.url for p in artifacts.pages
              if is_challenged(p) or p.status_code is None or (p.status_code or 0) >= 400
              or any(w in (p.warnings or ()) for w in _UNREAD_WARNINGS)]
    blocked = coverage.get("urls_blocked", 0) or 0
    link_evidence = {
        "urls_discovered": coverage.get("urls_discovered", len(node_keys)),
        "pages_read": len(node_keys),
        "urls_never_attempted": never_attempted,
        "urls_fetched_but_unread": len(unread),
        "unread_pages": sorted(unread)[:20],
        "urls_blocked": blocked,
        # The only configuration in which an absence-of-inbound-links claim covers
        # the whole site: every discovered URL was attempted, and every attempt
        # produced links we could read.
        "complete": never_attempted == 0 and not unread and blocked == 0,
    }
    crawl_scope = {
        "urls_discovered": link_evidence["urls_discovered"],
        "urls_analyzed": coverage.get("urls_analyzed", len(node_keys)),
        "urls_never_attempted": never_attempted,
        "complete": link_evidence["complete"],
    }

    return intermediate_artifact("site_graph", data={
        "nodes": nodes, "orphans": orphans, "dead_ends": dead_ends,
        "isolated_clusters": isolated_clusters, "main_cluster_size": len(main_component),
        "crawl_scope": crawl_scope, "link_evidence": link_evidence,
        "rendering_scope": {
            "raw_shell_pages": raw_shell_pages,
            "note": "Pages whose delivered HTML carries no internal links although the page can build them in "
                    "the browser. They are excluded from dead-end and navigation-absence conclusions, which are "
                    "statements about delivered HTML only.",
        },
    })
