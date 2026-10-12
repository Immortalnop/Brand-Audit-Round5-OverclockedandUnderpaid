"""url_keys.py -- URL identity helpers shared by acquisition and analysis.

visit_key(): two URLs that a server almost always treats as the same page
(`/a` vs `/a/`, tracking parameters) map to one key, so the crawl never spends two
requests on one page and the site graph never splits one page into two nodes.

template_key(): pages generated from one template (`/project/requests/2.31.0/`,
`/project/requests/2.32.0/`, ...) map to one pattern, so the crawler can cap how
many near-duplicates it samples and spend its page budget on distinct page types.
"""
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING_PARAMS = re.compile(r"^(utm_[a-z]+|gclid|fbclid|msclkid|mc_cid|mc_eid|_ga|ref_src|igshid)$", re.I)


def strip_tracking(url):
    p = urlsplit(url)
    if not p.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not TRACKING_PARAMS.match(k)]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(kept), p.fragment))


def visit_key(url):
    p = urlsplit(strip_tracking(url))
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), path, p.query, ""))


_VERSION = re.compile(r"v?\d+(\.\d+)+[a-z0-9.+-]*")
_HEXID = re.compile(r"[0-9a-f]{8,}(-[0-9a-f]{4,})*")


def template_key(url):
    p = urlsplit(url)
    segs = [s for s in (p.path or "/").lower().split("/") if s]
    out = []
    for s in segs:
        if re.fullmatch(r"\d+", s):
            out.append("{n}")
        elif _VERSION.fullmatch(s):
            out.append("{ver}")
        elif _HEXID.fullmatch(s):
            out.append("{id}")
        elif len(s) > 30 or (s.count("-") >= 3 and re.search(r"\d", s)):
            out.append("{slug}")
        else:
            out.append(s)
    # The leaf of any path two or more segments deep is treated as a variable
    # (an article slug, product handle or package name): /blog/post-a and
    # /blog/post-b share one template, /blog and /pricing do not.
    if len(out) >= 2:
        out[-1] = "{leaf}"
    key = "/" + "/".join(out[:4])
    if p.query:
        key += "?" + "&".join(sorted(k for k, _ in parse_qsl(p.query)))
    return key


KEY_INTENT = re.compile(
    r"/(about|about-us|company|team|contact|contact-us|pricing|plans|price|products?|shop|store|collections?|"
    r"services?|solutions?|faqs?|help|support|docs?|documentation|blog|news|locations?|stores|menu|careers|"
    r"admissions?|courses?|programs?|fees)(?:/|$|-|\.)", re.I)


def intent_of(url):
    m = KEY_INTENT.search(urlsplit(url).path or "/")
    return m.group(1).lower() if m else None
