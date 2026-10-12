"""check_entity_links.py -- do the brand's declared profile links disambiguate it?

Organization sameAs is how markup ties a brand to its official profiles and to
its knowledge-graph entity (Wikidata, and Wikipedia through it), the main signal
assistants use to tell same-named entities apart (Appendix D). Two checks, both
read from the acquisition snapshot only:

  kg-link-missing  Organization markup declares sameAs profiles, but none names
                   a Wikidata item or a Wikipedia article. Proactive, and only for
                   brands that already maintain sameAs: most small organizations
                   have no Wikidata item and do not need one.
  same-as-invalid  sameAs values that cannot be a profile: not an absolute URL,
                   the site itself, a share/intent link or a platform home page.

Whether the declared Wikidata item really is the brand, and whether namesakes
exist, needs a lookup on third-party sites. That is the agent stage's job
(AG-05), using the agent's own search tool; this script makes no request.
When the site has no Organization markup at all, identity-not-declared already
reports it and nothing is added here.
"""
import re
from collections.abc import Mapping
from urllib.parse import urlsplit, unquote

from check_helpers import profile_link_problem, site_host
from models import make_finding, skill_result
from structured_data import iter_nodes, types_of, CORE_ORGANIZATION_TYPES, ORGANIZATION_TYPES

_WIKIDATA_HOSTS = frozenset({"wikidata.org", "www.wikidata.org", "m.wikidata.org"})
_QID_PATH = re.compile(r"/(?:wiki/(?:Special:EntityPage/)?|entity/)(Q[1-9][0-9]{0,11})/?")
_WIKIPEDIA_HOST = re.compile(r"([a-z][a-z0-9-]{1,15})\.(?:m\.)?wikipedia\.org")
_NON_ARTICLE = ("special:", "file:", "category:", "help:", "wikipedia:", "talk:", "user:", "template:", "portal:")

def kg_links(urls):
    """(wikidata [(url, qid)], wikipedia [(url, lang, title)], malformed [url])."""
    wikidata, wikipedia, malformed = [], [], []
    for raw in urls:
        try:
            parts = urlsplit(raw.strip())
            host = (parts.hostname or "").lower()
        except ValueError:
            continue
        if parts.scheme not in ("http", "https"):
            continue
        if host in _WIKIDATA_HOSTS:
            m = _QID_PATH.fullmatch(parts.path)
            (wikidata.append((raw, m.group(1))) if m else malformed.append(raw))
            continue
        m = _WIKIPEDIA_HOST.fullmatch(host)
        if not m or m.group(1) == "www":
            continue
        title = unquote(parts.path[6:]) if parts.path.startswith("/wiki/") else ""
        if title and not title.lower().startswith(_NON_ARTICLE):
            wikipedia.append((raw, m.group(1), title))
        else:
            malformed.append(raw)
    return wikidata, wikipedia, malformed


def organization_markup(artifacts):
    """(pages carrying the site's Organization node, sameAs values). Organization
    subtypes count only on the home page (elsewhere they may be listings)."""
    pages, same_as = [], []
    home = artifacts.site_url.rstrip("/")
    for page in artifacts.pages:
        on_home = page.page_type == "home" or (page.final_url or page.url).rstrip("/") == home
        wanted = ORGANIZATION_TYPES if on_home else CORE_ORGANIZATION_TYPES
        found = False
        for node in iter_nodes(page.jsonld_blocks):
            if not isinstance(node, Mapping) or not types_of(node) & wanted:
                continue
            found = True
            value = node.get("sameAs")
            same_as.extend(value if isinstance(value, (list, tuple)) else [value])
        if found:
            pages.append(page.url)
    return pages, [u.strip() for u in dict.fromkeys(same_as) if isinstance(u, str) and u.strip()]


def check_entity_links(artifacts, deadline):
    org_pages, same_as = organization_markup(artifacts)
    findings = []
    if not org_pages:
        return skill_result("freshness-corroboration", findings=[],
                            metrics={"organization_pages": 0, "same_as_values": 0})
    host = site_host(artifacts.site_url)
    wikidata, wikipedia, malformed = kg_links(same_as)
    # Only suggested to a brand that already declares its profiles in sameAs: the
    # knowledge-graph link is then the missing piece of work it has started. Most
    # small organizations have no Wikidata item and do not need one.
    if same_as and not wikidata and not wikipedia:
        shown = ", ".join(same_as[:5]) if same_as else "none"
        evidence = [{"type": "organization_markup",
                     "description": f"Organization markup on {len(org_pages)} page(s) declares sameAs: {shown}; none "
                                    "names a Wikidata item or Wikipedia article", "urls": org_pages[:10]}]
        evidence += [{"type": "organization_markup",
                      "description": f"sameAs '{u}' points at Wikidata or Wikipedia but names no item or article",
                      "urls": org_pages[:1]} for u in malformed[:3]]
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.8,
            title="Organization markup does not link the brand to a knowledge-graph entity",
            root_cause="No Wikidata or Wikipedia link is declared in Organization sameAs, so nothing ties the brand "
                       "to one knowledge-graph entity.",
            evidence=evidence, affected_pages=org_pages[:10],
            suggested_action={
                "summary": "Link the brand to its Wikidata item in Organization sameAs",
                "steps": ["Find the brand's Wikidata item, or create one if the organization meets Wikidata's "
                          "notability policy (serious, public references)",
                          "Add the item URL, and the Wikipedia article if one exists, to Organization sameAs",
                          "Make sure the item lists this site as its official website (P856)"],
                "priority": "low", "effort": "medium",
                "expected_benefit": "Assistants can attribute facts to the right entity",
                "verification": "Organization sameAs contains https://www.wikidata.org/wiki/Q... for the brand"},
            provenance={"skill": "freshness-corroboration", "script": "check_entity_links.py",
                        "rule_id": "kg-link-missing"}))
    invalid = [(u, profile_link_problem(u, host)) for u in same_as]
    invalid = [(u, why) for u, why in invalid if why]
    if invalid:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="low", status="confirmed",
            confidence=0.9,
            title="Organization sameAs lists values that are not profiles",
            root_cause=f"{len(invalid)} of {len(same_as)} sameAs value(s) cannot identify an official profile.",
            evidence=[{"type": "organization_markup", "description": f"sameAs '{u[:200]}' {why}",
                       "urls": org_pages[:1]} for u, why in invalid[:8]],
            affected_pages=org_pages[:10],
            suggested_action={
                "summary": "Replace each invalid sameAs value with the brand's own profile URL",
                "steps": ["Use the full https:// URL of the brand's profile page on each platform",
                          "Remove share links, platform home pages and links back to this site"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Every declared profile identifies the brand",
                "verification": "Each sameAs value opens the brand's own profile page"},
            provenance={"skill": "freshness-corroboration", "script": "check_entity_links.py",
                        "rule_id": "same-as-invalid"}))
    return skill_result("freshness-corroboration", findings=findings,
                        metrics={"organization_pages": len(org_pages), "same_as_values": len(same_as),
                                 "kg_links": len(wikidata) + len(wikipedia), "same_as_invalid": len(invalid)})
