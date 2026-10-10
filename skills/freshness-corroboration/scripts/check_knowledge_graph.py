"""check_knowledge_graph.py -- is the brand tied to one knowledge-graph entity?

Knowledge graphs (Wikidata, and Wikipedia through its Wikidata sitelinks) are the
main signal assistants use to tell same-named entities apart. A brand is tied to
its entity by a two-way link: Organization sameAs on the site names the entity,
and the entity's official website (Wikidata P856) names the site.

Two layers:
  1. Deterministic, no network: does Organization markup declare a Wikidata or
     Wikipedia link at all? If not, kg-link-missing.
  2. Verification of a declared link, bounded and read-only: at most one Wikidata
     item and one Wikipedia article, fetched by plain GET from the public
     /wiki/ paths after reading each host's robots.txt (fail closed when it
     cannot be read). The item's names and official website are compared with
     the site. A conflict is kg-entity-mismatch; an item that does not name the
     site as its official website is kg-link-missing (one-way link).

Why this does not search for namesakes: robots.txt for wikidata.org and
wikipedia.org disallows their search and API endpoints (/w/api.php,
/w/rest.php, /api/, Special:Search), so a script that obeys robots.txt cannot
look a name up. Only the declared entity is verified here. Searching for
same-named entities is the agent stage's job (AG-05, kg-namesake-ambiguity),
using the agent's own web search.

The lookup can be switched off with KNOWLEDGE_GRAPH_LOOKUP=0. When it is off or
fails, the declared link is reported as unverified (a warning and metrics), never
as a defect: an unavailable third-party service says nothing about the site.
"""
import json
import os
import re
from collections.abc import Mapping
from dataclasses import replace
from time import monotonic
from urllib.parse import quote, unquote, urlsplit

from instrumentation import Instrumentation
from models import insufficient_evidence_result, make_finding, skill_result
from resolve_entity_identity import ORG_TYPES, _normalize_org_name
from robots_policy import RobotsPolicy
from structured_data import iter_nodes, types_of
from transport import USER_AGENT, Transport

WIKIDATA_ORIGIN = "https://www.wikidata.org"
LOOKUP_ENV = "KNOWLEDGE_GRAPH_LOOKUP"
_WIKIDATA_HOSTS = frozenset({"wikidata.org", "www.wikidata.org", "m.wikidata.org"})
_QID_PATH_RE = re.compile(r"/(?:wiki/(?:Special:EntityPage/)?|entity/)(Q[1-9][0-9]{0,11})/?")
_WIKIPEDIA_HOST_RE = re.compile(r"([a-z][a-z0-9-]{1,15})\.(?:m\.)?wikipedia\.org")
_ITEM_ID_RE = re.compile(rb'"wgWikibaseItemId"\s*:\s*"(Q[1-9][0-9]{0,11})"')
_NON_ARTICLE_PREFIXES = ("special:", "file:", "category:", "help:", "wikipedia:", "talk:", "user:",
                         "template:", "portal:")

# Lookup bounds: a few requests, a few MB and a few seconds at most, whatever the
# remaining audit budget is.
_LOOKUP_BUDGET_S = 15.0
_FETCH_TIMEOUT_MS = 6000
_ROBOTS_MAX_BYTES = 512_000
_ENTITY_MAX_BYTES = 2_000_000
_ARTICLE_HEAD_BYTES = 65_536
_MAX_NAMES = 300


def _host(url):
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return ""
    return host.lower().removeprefix("www.")


def _same_site(url, site_host):
    """True when url's host is the site host, or one is a subdomain of the other."""
    host = _host(url)
    if not host or not site_host:
        return False
    return host == site_host or host.endswith("." + site_host) or site_host.endswith("." + host)


def _name_matches(brand_names, entity_names):
    """Whole-word containment between any normalized brand name and entity name."""
    brand = {n for n in (_normalize_org_name(x) for x in brand_names if isinstance(x, str)) if n}
    entity = {n for n in (_normalize_org_name(x) for x in entity_names if isinstance(x, str)) if n}
    for a in brand:
        for b in entity:
            if a == b or f" {a} " in f" {b} " or f" {b} " in f" {a} ":
                return True
    return False


def parse_kg_links(urls):
    """Split sameAs URLs into Wikidata items, Wikipedia articles and malformed
    knowledge-graph links. Returns (wikidata, wikipedia, malformed) where
    wikidata is [(url, qid)] and wikipedia is [(url, lang, title)]."""
    wikidata, wikipedia, malformed = [], [], []
    for raw in urls:
        if not isinstance(raw, str):
            continue
        try:
            parts = urlsplit(raw.strip())
            host = (parts.hostname or "").lower()
        except ValueError:
            continue
        if parts.scheme not in ("http", "https"):
            continue
        if host in _WIKIDATA_HOSTS:
            match = _QID_PATH_RE.fullmatch(parts.path)
            if match:
                wikidata.append((raw, match.group(1)))
            else:
                malformed.append(raw)
            continue
        match = _WIKIPEDIA_HOST_RE.fullmatch(host)
        if not match or match.group(1) == "www":
            continue
        title = unquote(parts.path[6:]) if parts.path.startswith("/wiki/") else ""
        if title and not title.lower().startswith(_NON_ARTICLE_PREFIXES):
            wikipedia.append((raw, match.group(1), title))
        else:
            malformed.append(raw)
    return wikidata, wikipedia, malformed


def _organization_markup(artifacts):
    """(pages with Organization markup, names, sameAs URLs) from the crawled pages."""
    pages, names, same_as = [], [], []
    for page in artifacts.pages:
        found = False
        for node in iter_nodes(page.jsonld_blocks):
            if not isinstance(node, Mapping) or not types_of(node) & ORG_TYPES:
                continue
            found = True
            for key in ("name", "legalName", "alternateName"):
                value = node.get(key)
                names.extend(value if isinstance(value, (list, tuple)) else [value])
            value = node.get("sameAs")
            same_as.extend(value if isinstance(value, (list, tuple)) else [value])
        if found:
            pages.append(page.url)
    names = [n for n in dict.fromkeys(names) if isinstance(n, str) and n.strip()]
    same_as = [u for u in dict.fromkeys(same_as) if isinstance(u, str) and u.strip()]
    return pages, names, same_as


def _default_transport(origin, deadline_monotonic, limits):
    bounded = replace(limits, MAX_TOTAL_HTTP_REQUESTS=3,
                      MAX_TOTAL_BYTES=_ROBOTS_MAX_BYTES + _ENTITY_MAX_BYTES + _ARTICLE_HEAD_BYTES,
                      MAX_RESPONSE_BYTES=_ENTITY_MAX_BYTES,
                      PER_FETCH_TIMEOUT_MS=max(limits.PER_FETCH_TIMEOUT_MS, _FETCH_TIMEOUT_MS))
    # Never allow private targets here: these are public third-party hosts.
    return Transport(origin, deadline_monotonic, bounded, Instrumentation(), allow_private=False)


class _Lookup:
    """Robots-checked GETs to knowledge-graph hosts, one transport per origin."""

    def __init__(self, deadline_monotonic, limits, instrumentation, transport_factory):
        self.deadline = deadline_monotonic
        self.limits = limits
        self.instrumentation = instrumentation
        self.factory = transport_factory or _default_transport
        self.transports = {}
        self.robots = {}
        self.requests = []

    def _record(self, url, status, http_status=None):
        self.requests.append({"url": url, "status": status, "http_status": http_status})
        if self.instrumentation is not None and status not in ("deadline", "budget_exhausted",
                                                                "robots_disallowed", "robots_unavailable"):
            self.instrumentation.record_external_fetch(ok=status == "ok")

    def _transport(self, origin):
        if origin in self.transports:
            return self.transports[origin]
        tr = self.factory(origin, self.deadline, self.limits)
        self.transports[origin] = tr
        robots_url = origin + "/robots.txt"
        resp, status = tr.get(robots_url, robots_exempt=True, max_bytes=_ROBOTS_MAX_BYTES)
        self._record(robots_url, status, resp.status_code if resp else None)
        text = None
        if status == "ok" and resp.status_code == 404:
            text = ""
        elif status == "ok" and resp.status_code == 200 and not resp.truncated:
            try:
                text = resp.content.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None and text.lstrip().lower().startswith(("<html", "<!doctype")):
                text = None
        if text is None:
            # Fail closed: without readable robots rules nothing else is requested.
            self.robots[origin] = "unavailable"
            tr.robots = RobotsPolicy("User-agent: *\nDisallow: /")
        else:
            self.robots[origin] = "ok"
            tr.robots = RobotsPolicy(text)
            tr.delay = max(tr.delay, tr.robots.crawl_delay(USER_AGENT))
        return tr

    def get(self, url, max_bytes):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        tr = self._transport(origin)
        if self.robots.get(origin) != "ok":
            self._record(url, "robots_unavailable")
            return None, "robots_unavailable"
        resp, status = tr.get(url, max_bytes=max_bytes, headers={"Accept-Encoding": "gzip"})
        self._record(url, status, resp.status_code if resp else None)
        return resp, status


def _fetch_article_item(lookup, lang, title):
    """('ok', qid) | ('no_item', None) | ('not_found', None) | (failure, None)."""
    path = quote(title.replace(" ", "_"), safe="()_,!'*-.~:/")
    resp, status = lookup.get(f"https://{lang}.wikipedia.org/wiki/{path}", _ARTICLE_HEAD_BYTES)
    if status != "ok":
        return status, None
    if resp.status_code == 404:
        return "not_found", None
    if not resp.ok:
        return f"http_{resp.status_code}", None
    match = _ITEM_ID_RE.search(resp.content)
    return ("ok", match.group(1).decode("ascii")) if match else ("no_item", None)


def _fetch_entity(lookup, qid):
    """('ok', entity) | ('not_found', None) | (failure, None). The entity is
    reduced to id, names and official websites."""
    resp, status = lookup.get(f"{WIKIDATA_ORIGIN}/wiki/Special:EntityData/{qid}.json", _ENTITY_MAX_BYTES)
    if status != "ok":
        return status, None
    if resp.status_code == 404:
        return "not_found", None
    if not resp.ok:
        return f"http_{resp.status_code}", None
    if resp.truncated:
        return "response_too_large", None
    try:
        data = json.loads(resp.content.decode("utf-8"))
        entity = next(iter(data["entities"].values()))
    except (ValueError, KeyError, TypeError, AttributeError, StopIteration):
        return "malformed_response", None
    if not isinstance(entity, dict) or "missing" in entity:
        return "not_found", None
    try:
        return "ok", _reduce_entity(entity, qid)
    except (AttributeError, TypeError):
        return "malformed_response", None


def _reduce_entity(entity, qid):
    """Keep only what the comparison needs. Raises AttributeError or TypeError on
    an unexpected shape, which the caller reports as a malformed response."""
    names = []
    for group in ("labels", "aliases"):
        for item in (entity.get(group) or {}).values():
            for entry in (item if isinstance(item, list) else [item]):
                if isinstance(entry, dict) and isinstance(entry.get("value"), str):
                    names.append(entry["value"])
    websites = []
    for claim in list((entity.get("claims") or {}).get("P856") or [])[:20]:
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if isinstance(value, str):
            websites.append(value)
    labels = entity.get("labels") or {}
    label = labels.get("en") or next(iter(labels.values()), {})
    return {"id": str(entity.get("id") or qid),
            "label": label.get("value") if isinstance(label.get("value"), str) else None,
            "names": list(dict.fromkeys(names))[:_MAX_NAMES], "official_websites": websites}


def _evaluate(entity, site_host, brand_names):
    if any(_same_site(w, site_host) for w in entity["official_websites"]):
        return "verified"
    if entity["official_websites"]:
        return "website_conflict"
    return "no_official_website" if _name_matches(brand_names, entity["names"]) else "name_conflict"


def _action(summary, steps, priority):
    return {"summary": summary, "steps": steps, "priority": priority, "effort": "low",
            "expected_benefit": "Assistants can tell the brand apart from same-named entities",
            "verification": "Re-run the audit after the markup or the knowledge-graph entry changes"}


def _link_missing_finding(org_pages, same_as, malformed, severity, ambiguity_type):
    shown = ", ".join(same_as[:5]) if same_as else "none"
    evidence = [{"type": "organization_markup",
                 "description": f"Organization markup on {len(org_pages)} page(s) declares sameAs: {shown}; "
                                f"none names a Wikidata item or Wikipedia article",
                 "urls": org_pages[:10]}]
    for url in malformed[:3]:
        evidence.append({"type": "organization_markup",
                         "description": f"sameAs '{url}' points at Wikidata or Wikipedia but names no item "
                                        f"or article"})
    if ambiguity_type:
        evidence.append({"type": "entity_identity",
                         "description": f"Identity resolution already found on-site ambiguity "
                                        f"({ambiguity_type}), which a knowledge-graph link would settle"})
    return make_finding(
        category="ai_discoverability", finding_type="proactive_improvement", severity=severity,
        status="confirmed", confidence=0.8,
        title="Organization markup does not link the brand to a knowledge-graph entity",
        root_cause="No Wikidata or Wikipedia link is declared, so nothing ties the brand to one "
                   "knowledge-graph entity",
        evidence=evidence, affected_pages=org_pages[:10],
        suggested_action=_action(
            "Link the brand to its Wikidata item in Organization sameAs",
            ["Find the brand's Wikidata item, or create one if the organization meets Wikidata's "
             "notability policy (public, serious references)",
             "Add the item URL (and the Wikipedia article, if one exists) to Organization sameAs",
             "Make sure the item lists this site as its official website (P856)"],
            severity),
        provenance={"skill": "freshness-corroboration", "script": "check_knowledge_graph.py",
                    "rule_id": "kg-link-missing"},
    )


def _one_way_finding(org_pages, entity, link):
    return make_finding(
        category="ai_discoverability", finding_type="proactive_improvement", severity="low",
        status="confirmed", confidence=0.8,
        title="The brand's Wikidata item does not name the site as its official website",
        root_cause="The knowledge-graph link runs one way only: the site names the entity, but the "
                   "entity does not name the site",
        evidence=[{"type": "knowledge_graph",
                   "description": f"Wikidata {entity['id']} ({entity['label'] or 'no label'}), declared "
                                  f"by sameAs {link}, has no official website (P856)",
                   "urls": org_pages[:10]}],
        affected_pages=org_pages[:10],
        suggested_action=_action(
            "Add this site as the official website (P856) of the brand's Wikidata item",
            ["Edit the Wikidata item and add the site URL under official website (P856)",
             "Cite a reference for the statement where possible"],
            "low"),
        provenance={"skill": "freshness-corroboration", "script": "check_knowledge_graph.py",
                    "rule_id": "kg-link-missing"},
    )


def _mismatch_finding(org_pages, problems, confirmed):
    return make_finding(
        category="ai_discoverability", finding_type="defect", severity="medium",
        status="confirmed" if confirmed else "suspected", confidence=0.85 if confirmed else 0.6,
        title="The declared knowledge-graph entity does not match the brand",
        root_cause="Organization sameAs points at a knowledge-graph entry that is missing or describes "
                   "a different organization",
        evidence=[{"type": "knowledge_graph", "description": p, "urls": org_pages[:10]} for p in problems],
        affected_pages=org_pages[:10],
        suggested_action=_action(
            "Point Organization sameAs at the brand's own knowledge-graph entity",
            ["Check that each Wikidata and Wikipedia link in sameAs is the brand's own entry",
             "Replace links to a namesake or to a deleted entry",
             "Where the entry is the brand's own, correct its name or official website (P856)"],
            "medium"),
        provenance={"skill": "freshness-corroboration", "script": "check_knowledge_graph.py",
                    "rule_id": "kg-entity-mismatch"},
    )


def check_knowledge_graph(artifacts, identity, deadline, limits, instrumentation=None,
                          transport_factory=None):
    org_pages, brand_names, same_as = _organization_markup(artifacts)
    if not org_pages:
        return insufficient_evidence_result(
            "freshness-corroboration",
            "No Organization markup on the crawled pages; the knowledge-graph link was not assessed.",
            metrics={"lookup": "not_applicable", "organization_pages": 0})
    identity_data = identity.get("data", {}) if isinstance(identity, Mapping) else {}
    if isinstance(identity_data.get("canonical_name"), str):
        brand_names = [identity_data["canonical_name"]] + brand_names
    wikidata, wikipedia, malformed = parse_kg_links(same_as)
    metrics = {"organization_pages": len(org_pages),
               "declared_wikidata": [q for _, q in wikidata][:5],
               "declared_wikipedia": [u for u, _, _ in wikipedia][:5],
               "malformed_links": len(malformed), "lookup": "not_needed", "requests": []}

    if not wikidata and not wikipedia:
        ambiguity = identity_data.get("ambiguity_type")
        severity = "medium" if ambiguity in ("multi_brand_conflict", "conflicting_sameas") else "low"
        return skill_result("freshness-corroboration", metrics=metrics, findings=[
            _link_missing_finding(org_pages, same_as, malformed, severity, ambiguity)])

    if os.environ.get(LOOKUP_ENV) == "0":
        metrics["lookup"] = "disabled"
        return skill_result("freshness-corroboration", metrics=metrics, warnings=[
            f"Knowledge-graph lookup disabled ({LOOKUP_ENV}=0); the declared entity was not verified."])

    now = monotonic()
    end = now + _LOOKUP_BUDGET_S
    if deadline is not None:
        end = min(end, deadline.deadline_monotonic)
    lookup = _Lookup(end, limits, instrumentation, transport_factory)
    problems, confirmed, failures = [], False, []
    qid, link = (wikidata[0][1], wikidata[0][0]) if wikidata else (None, None)

    if wikipedia:
        article_url, lang, title = wikipedia[0]
        status, article_qid = _fetch_article_item(lookup, lang, title)
        if status == "not_found":
            problems.append(f"sameAs {article_url} names a Wikipedia article that does not exist (HTTP 404)")
            confirmed = True
        elif status == "ok" and qid and article_qid != qid:
            problems.append(f"sameAs names Wikidata {qid}, but the declared Wikipedia article "
                            f"{article_url} belongs to {article_qid}")
            confirmed = True
        elif status == "ok" and not qid:
            qid, link = article_qid, article_url
        elif status not in ("ok", "no_item"):
            failures.append(f"Wikipedia article: {status}")

    entity = None
    if qid:
        status, entity = _fetch_entity(lookup, qid)
        if status == "not_found":
            problems.append(f"sameAs {link} names Wikidata {qid}, which does not exist or was deleted")
            confirmed = True
        elif status != "ok":
            failures.append(f"Wikidata {qid}: {status}")

    findings, verdict = [], None
    site_host = _host(artifacts.site_url) or _host(artifacts.normalized_origin)
    if entity is not None:
        verdict = _evaluate(entity, site_host, brand_names)
        metrics["entity"] = {"id": entity["id"], "label": entity["label"],
                             "official_websites": entity["official_websites"][:5]}
        if verdict == "website_conflict":
            problems.append(f"Wikidata {entity['id']} ({entity['label'] or 'no label'}) gives its official "
                            f"website as {', '.join(entity['official_websites'][:3])}, not {site_host}")
            confirmed = True
        elif verdict == "name_conflict":
            problems.append(f"Wikidata {entity['id']} is named {entity['label'] or 'with no label'}, which "
                            f"matches none of the brand names on the site, and lists no official website")
        elif verdict == "no_official_website":
            findings.append(_one_way_finding(org_pages, entity, link))
    if problems:
        findings.append(_mismatch_finding(org_pages, problems, confirmed))

    metrics["verdict"] = verdict
    metrics["requests"] = lookup.requests
    metrics["robots"] = dict(lookup.robots)
    metrics["lookup"] = "completed" if not failures else "incomplete"
    warnings = []
    if failures:
        metrics["lookup_failures"] = failures
        warnings.append("Knowledge-graph lookup incomplete (" + "; ".join(failures) + "); the declared "
                        "entity was not fully verified (not checked, not a site defect).")
    return skill_result("freshness-corroboration", findings=findings, metrics=metrics, warnings=warnings)
