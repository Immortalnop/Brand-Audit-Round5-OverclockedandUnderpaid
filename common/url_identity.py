"""url_identity.py -- one shared notion of "the same page" for URL comparisons.

A page URL is identified by its host (lower case, without a leading www.), its
path without a trailing slash, and its query string. The fragment never reaches
the server, so it is dropped. The query is kept: /product?id=red and
/product?id=blue can be different pages, and stripping every query would merge
them. Two URLs with different queries are treated as one page only on evidence:
a redirect that took both to one final URL (an alias recorded by acquisition),
which callers pass in as `aliases`.

Canonical declarations and hreflang alternates are identity hints, not proof that
two URLs serve the same content and controls; callers that suppress something on
such a hint record the reason (see analyze_experience.shared_title_pages).
"""
from urllib.parse import urlsplit


def page_identity(url):
    """(host, path, query) for a page URL, or None when it cannot be parsed."""
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


def alias_identities(aliases):
    """{identity of a requested URL: identity of its final URL} from acquisition's
    requested-to-final alias map (url_aliases). Entries that cannot be parsed are
    skipped."""
    out = {}
    for requested, final in (aliases or {}).items():
        source, target = page_identity(requested), page_identity(final)
        if source is not None and target is not None and source != target:
            out[source] = target
    return out


def resolve_identity(url, alias_map=None):
    """Identity of url after following a recorded redirect alias, if any."""
    key = page_identity(url)
    if key is None or not alias_map:
        return key
    return alias_map.get(key, key)
