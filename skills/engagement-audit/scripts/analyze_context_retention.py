"""analyze_context_retention.py -- does the site keep a visitor's context?

A visitor who arrives from an AI answer already has a specific need. They stay
when the site lets them state it again quickly (search), keeps what they did
(saved or recently viewed items), and honours the link they followed (query
parameters survive). This check reads the acquisition snapshot only (no
requests):

  - site-search-missing (suggestion, suspected): a site that lists at least 50
    URLs but shows no search box on any sampled page and declares no
    SearchAction.
  - context-retention-missing (suggestion, suspected): a shop with product or
    category pages but no sign of saved state ("recently viewed", "wishlist",
    "save for later", "compare") in their HTML. Widgets that JavaScript adds
    after load usually leave a trace in the raw HTML (a mount point, a data
    attribute, a script URL or inline configuration naming a wishlist or
    recently viewed items); any such trace on a sampled page counts as saved
    state. A widget with no trace at all is still missed, so confidence is low.

Pages whose raw HTML carries too little text for their type are probably built
by JavaScript. The search and saved-state checks do not judge them, and the
report says how many were skipped. Search hints (an id, class or accessible name
starting with "search", <link rel="search">, a link to /search) count as search.
  - deep-link-params-dropped (defect, confirmed): a URL with query parameters
    that redirected to a URL without them. A visitor following a deep link to
    a filtered or preselected view lands on a generic page instead. Tracking
    parameters (utm_*, gclid and similar) are ignored.
"""
import re
from urllib.parse import urlsplit, parse_qsl
from check_helpers import (commerce_evidence, eligible_pages, page_share, split_script_dependent,
                           script_dependent_warning)
from models import make_finding, skill_result
from structured_data import iter_nodes, types_of

_LARGE_SITE_URLS = 50
_SAVED_STATE = re.compile(r"recently viewed|recently browsed|wish ?list|save for later|saved (?:items|for later)"
                          r"|favou?rites|my list|add to list|\bcompare\b|continue where you left off", re.I)
_TRACKING = re.compile(r"^(?:utm_[a-z_]+|gclid|gbraid|wbraid|fbclid|msclkid|yclid|dclid|mc_cid|mc_eid|_ga|_gl"
                       r"|ref|referrer|source|igshid|si)$", re.I)


def _site_size(artifacts, pages):
    sitemap = artifacts.sitemap_data or {}
    coverage = (artifacts.acquisition_metadata or {}).get("coverage") or {}
    return max(sitemap.get("url_entries") or 0, len(sitemap.get("urls") or ()),
               coverage.get("urls_discovered") or 0, len(pages))


def _declares_search_action(page):
    for node in iter_nodes(page.jsonld_blocks):
        action = node.get("potentialAction")
        actions = action if isinstance(action, (list, tuple)) else [action]
        if any(hasattr(a, "get") and "SearchAction" in types_of(a) for a in actions):
            return True
    return False


def _content_params(url):
    try:
        return {k for k, _ in parse_qsl(urlsplit(url).query, keep_blank_values=True) if not _TRACKING.match(k)}
    except ValueError:
        return set()


def analyze_context_retention(artifacts, deadline):
    if deadline.expired():
        return skill_result("engagement-audit", status="insufficient_evidence",
                            warnings=["Context-retention checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    judged, built = split_script_dependent(pages)
    findings = []

    size = _site_size(artifacts, pages)
    has_search = any((p.features or {}).get("search") or (p.features or {}).get("search_form")
                     or (p.features or {}).get("search_hint") or _declares_search_action(p) for p in pages)
    if judged and size >= _LARGE_SITE_URLS and not has_search:
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low", status="suspected",
            confidence=0.6,
            title=f"No site search on {page_share(judged, judged)} of a site with {size} URLs",
            root_cause="A visitor who arrives from an AI answer with a follow-up need must browse menus to find "
                       "it when a large site offers no search box, and many leave instead",
            affected_pages=[judged[0].url],
            evidence=[{"type": "site_search",
                       "description": f"No search input, role=\"search\" form or SearchAction on {len(judged)} sampled "
                                      f"pages; the sitemap and crawl list {size} URLs",
                       "urls": [judged[0].url]}],
            suggested_action={
                "summary": "Add a site search box to the header of every page",
                "steps": ["Add a <form role=\"search\"> with a labelled search input to the shared header",
                          "Make results pages reachable by URL (for example /search?q=term) so they can be linked",
                          "Declare the search URL as a WebSite SearchAction in JSON-LD"],
                "priority": "low", "effort": "medium",
                "expected_benefit": "Visitors can restate their need in one step instead of leaving",
                "verification": "Re-run the audit and confirm a search form is detected"},
            provenance={"skill": "engagement-audit", "script": "analyze_context_retention.py",
                        "rule_id": "site-search-missing"},
        ))

    # A /category/ or /product path alone does not make a shop (a news site files
    # audio by category); the sampled product and category pages must show
    # something for sale: Product or Offer markup, a price or a buy control.
    shop = [p for p in judged if p.page_type in ("product", "category")]
    if not any(commerce_evidence(p) for p in shop):
        shop = []
    def saved_state(p):
        f = p.features or {}
        texts = [p.visible_text] + list(f.get("buttons") or ()) + [t for _, t in (f.get("anchors") or ())]
        return any(_SAVED_STATE.search(t or "") for t in texts)
    hints = sorted({h for p in pages for h in ((p.features or {}).get("saved_state_hints") or ())})
    if len(shop) >= 2 and not hints and not any(saved_state(p) for p in shop):
        findings.append(make_finding(
            category="engagement", finding_type="proactive_improvement", severity="low", status="suspected",
            confidence=0.4,
            title=f"No saved or recently viewed items on {page_share(shop, shop, 'product page')}",
            root_cause="Returning visitors pick up where they left off only if the site keeps their state; "
                       "without saved or recently viewed items, each visit starts from zero",
            affected_pages=[p.url for p in shop],
            evidence=[{"type": "saved_state",
                       "description": "No wishlist, save-for-later, compare or recently viewed control in the HTML, "
                                      "and no mount point, data attribute or script for one. A widget that "
                                      "JavaScript adds without any trace in the raw HTML would be missed",
                       "urls": [p.url for p in shop[:10]]}],
            suggested_action={
                "summary": "Let visitors save items and see what they viewed recently",
                "steps": ["Add a save-for-later or wishlist control to product pages",
                          "Show recently viewed items on product and category pages",
                          "Keep the saved list across visits without requiring an account"],
                "priority": "low", "effort": "medium",
                "expected_benefit": "Returning visitors resume their task instead of searching again",
                "verification": "Open a product page in a browser and confirm the control is present"},
            provenance={"skill": "engagement-audit", "script": "analyze_context_retention.py",
                        "rule_id": "context-retention-missing"},
        ))

    dropped = []
    for p in artifacts.pages:
        if p.status_code != 200 or not p.final_url or p.final_url == p.url:
            continue
        lost = sorted(_content_params(p.url) - _content_params(p.final_url))
        if lost:
            dropped.append((p, lost))
    if dropped:
        findings.append(make_finding(
            category="engagement", finding_type="defect", severity="low", status="confirmed", confidence=0.85,
            title=f"Redirects drop query parameters on {len(dropped)} deep link(s)",
            root_cause="A link that preselects a filter, variant or tab sends the visitor to a generic page when "
                       "a redirect strips its query parameters, so the context the link carried is lost",
            affected_pages=[p.url for p, _ in dropped],
            evidence=[{"type": "redirect_params",
                       "description": f"{p.url} redirected to {p.final_url}, dropping: {', '.join(lost[:5])}",
                       "urls": [p.url]} for p, lost in dropped[:10]],
            suggested_action={
                "summary": "Carry query parameters through redirects",
                "steps": ["Change each listed redirect rule to append the original query string to the target",
                          "Link directly to the final URL, with its parameters, from navigation and sitemaps"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Deep links land visitors on the exact view they were promised",
                "verification": "Request each listed URL and confirm the final URL keeps its parameters"},
            provenance={"skill": "engagement-audit", "script": "analyze_context_retention.py",
                        "rule_id": "deep-link-params-dropped"},
        ))

    warnings = [script_dependent_warning(built, pages, "site search and saved items")] if built else []
    return skill_result(
        "engagement-audit", findings=findings, warnings=warnings,
        metrics={"context_retention_pages_analyzed": len(pages), "context_retention_site_urls": size,
                 "context_retention_script_dependent_pages": len(built),
                 "context_retention_saved_state_hints": hints,
                 "context_retention_search_present": has_search, "context_retention_shop_pages": len(shop),
                 "context_retention_query_urls": sum(bool(urlsplit(p.url).query) for p in artifacts.pages)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
