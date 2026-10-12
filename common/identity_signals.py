"""identity_signals.py -- brand-name candidates from first-party pages when no
Organization JSON-LD declares one (A7).

Each source gives a candidate name and a weight. resolve_entity_identity.py uses
these as fallbacks below Organization JSON-LD, and analyze_machine_readability.py
uses the best candidate to pre-fill proposed Organization markup.

  level 2  WebSite JSON-LD name, or og:site_name consistent on >= 2 pages  0.75
  level 3  common <title> prefix/suffix present on >= 60% of pages           0.70
  level 4  footer copyright holder                                         0.65
  level 5  registrable domain label                                        0.40
"""
import re
from collections import Counter
from urllib.parse import urlsplit
from structured_data import iter_nodes, types_of

_SPLIT = re.compile(r"\s+[|\u2013\u2014\-\u00b7:]\s+")
_COPYRIGHT = re.compile(
    r"(?:\u00a9|&copy;|\(c\)|copyright)\s*(?:\d{4}\s*(?:[-\u2013]\s*\d{2,4})?)?\s*,?\s*"
    r"([A-Z][\w&.,' -]{1,60}?)(?=\s*(?:\.|\||all rights|\u00b7|$|\d))", re.I)
_LEGAL_TAIL = re.compile(r"[,.]?\s*\b(inc|llc|ltd|limited|corp|corporation|gmbh|pvt|plc|co)\b\.?$", re.I)
_GENERIC = {"home", "homepage", "welcome", "official site", "official website", "index", "all rights reserved"}


def _clean(name):
    name = " ".join(str(name or "").split()).strip(" -|:,.")
    return name if 2 <= len(name) <= 60 and name.lower() not in _GENERIC else ""


def _norm(name):
    return re.sub(r"[^\w]+", " ", _LEGAL_TAIL.sub("", name.lower())).strip()


def candidates(pages, origin):
    """Return [(level, weight, name, source)] best first."""
    out = []
    site_names = Counter()
    for p in pages:
        for node in iter_nodes(p.jsonld_blocks):
            if "WebSite" in types_of(node) and isinstance(node.get("name"), str):
                site_names[_clean(node["name"])] += 2
        for v in ((p.features or {}).get("meta", {}) or {}).get("og:site_name", ()):
            site_names[_clean(v)] += 1
    site_names.pop("", None)
    if site_names:
        name, votes = site_names.most_common(1)[0]
        if votes >= 2:
            out.append((2, 0.75, name, "WebSite JSON-LD name / og:site_name"))
    titles = [p.title for p in pages if p.title]
    if len(titles) >= 2:
        parts = Counter()
        for t in titles:
            segs = [_clean(x) for x in _SPLIT.split(t)]
            if len(segs) >= 2:
                for seg in {segs[0], segs[-1]}:
                    if seg:
                        parts[seg] += 1
        if parts:
            name, n = parts.most_common(1)[0]
            if n >= max(2, 0.6 * len(titles)):
                out.append((3, 0.70, name, f"common title segment on {n}/{len(titles)} pages"))
    holders = Counter()
    for p in pages:
        text = ((p.features or {}).get("footer_text") or "")
        for m in _COPYRIGHT.finditer(text):
            name = _clean(m.group(1))
            if name and not re.fullmatch(r"[\d\s-]+", name):
                holders[name] += 1
    if holders:
        name, _ = holders.most_common(1)[0]
        out.append((4, 0.65, name, "footer copyright holder"))
    host = urlsplit(origin).hostname or ""
    labels = [x for x in host.split(".") if x not in ("www", "m")]
    if labels:
        label = labels[-2] if len(labels) >= 2 else labels[0]
        if label and not re.fullmatch(r"[\d.]+", label):
            out.append((5, 0.40, label, "domain label"))
    return sorted(out, key=lambda c: (c[0], -c[1]))


def best_name(pages, origin):
    found = candidates(pages, origin)
    return found[0][2] if found else ""


def agreement(name, found):
    """How many other candidate sources name the same brand."""
    key = _norm(name)
    return sum(1 for _, _, n, _ in found if _norm(n) and (_norm(n) in key or key in _norm(n)))
