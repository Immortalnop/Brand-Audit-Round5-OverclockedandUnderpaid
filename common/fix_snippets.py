"""fix_snippets.py -- ready-to-paste fixes built from what the audit observed.

A finding that says "add JSON-LD" leaves the reader to write it. For the checks
whose fix is a block of markup or a file, this module writes that block from
facts the audit already holds: the brand name, the logo, the profile links the
site declares, each page's title, description and URL, and its page type.

Rules:
  - Nothing is invented. A value the audit did not observe (a price, an author,
    a publication date) is written as a REPLACE_WITH_... placeholder, and every
    placeholder is listed next to the code.
  - Every filled value names its source in filled_from, so a reviewer can check it.
  - No requests: everything comes from the acquisition snapshot and the entity
    identity artifact.
  - Output is bounded: at most a few pages per snippet.
  - The brand name comes from an Organization node on the home page that names
    the domain, or from the site-wide identity only when it is unambiguous, so a
    department's or sub-brand's markup never names the whole site.
  - og:image is never an SVG or ICO file, which social platforms do not render.

The snippet is attached as suggested_action["snippet"] with the keys format,
placement, code, filled_from, placeholders and note.
"""
import html
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

from structured_data import iter_nodes, types_of
from check_helpers import organization_contact

_PLACEHOLDER = re.compile(r"REPLACE_WITH_[A-Z_]+")
_TITLE_SEPARATOR = re.compile("\\s+(?:\\||-|\\u2013|\\u2014|:|\\u00b7|\\u2022)\\s+")
_PROFILE_HOSTS = ("twitter.com", "x.com", "facebook.com", "linkedin.com", "instagram.com", "youtube.com",
                  "tiktok.com", "pinterest.com", "github.com", "wikipedia.org", "wikidata.org", "crunchbase.com",
                  "threads.net", "mastodon.social", "bsky.app", "trustpilot.com", "g2.com", "glassdoor.com")
_SHARE_PATH = re.compile(r"/(?:sharer|share|intent|sharearticle|dialog|plugins|hashtag|search)(?:[/.?]|$)", re.I)
_TRACKING = re.compile(r"^(?:utm_[a-z_]+|gclid|fbclid|msclkid|mc_cid|mc_eid|_ga|_gl)$", re.I)
_MAX_PAGES = 3
_NOTE = ("Generated from the audited pages. Check every value against the live page, replace each "
         "REPLACE_WITH_ placeholder, and validate before publishing.")

_SCHEMA_FOR_TYPE = {
    "product": "Product", "article": "Article", "service": "Service", "software": "SoftwareApplication",
    "about": "AboutPage", "contact": "ContactPage", "category": "CollectionPage", "listing": "CollectionPage",
}


def _host(url):
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _clean_url(url):
    """The URL without its fragment and tracking parameters."""
    try:
        p = urlsplit(url)
        query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not _TRACKING.match(k)])
        return urlunsplit((p.scheme, p.netloc, p.path or "/", query, ""))
    except ValueError:
        return url


def _absolute(value, base):
    value = (value or "").strip()
    if not value or value.lower().startswith(("data:", "javascript:")):
        return None
    try:
        url = urljoin(base, value)
        return url if urlsplit(url).scheme in ("http", "https") else None
    except ValueError:
        return None


def _meta(page, key):
    values = ((page.features or {}).get("meta") or {}).get(key) or ()
    return next((v.strip() for v in values if isinstance(v, str) and v.strip()), "")


def _org_nodes(pages):
    for page in pages:
        for node in iter_nodes(page.jsonld_blocks):
            if types_of(node) & {"Organization", "Corporation", "LocalBusiness", "OnlineStore", "NGO"}:
                yield page, node


def _home(artifacts):
    pages = [p for p in artifacts.pages if p.status_code == 200 and p.features]
    return next((p for p in pages if p.page_type == "home"), pages[0] if pages else None)


def _brand_from_title(title, host):
    parts = [s.strip() for s in _TITLE_SEPARATOR.split(title or "") if s.strip()]
    if not parts:
        return ""
    core = re.sub(r"[^a-z0-9]", "", host.split(".")[0]) if host else ""
    for part in parts:
        # Only a title segment that matches the domain is trusted as the brand;
        # "Home" or a tagline must not become the Organization name.
        if _matches_host(part, core):
            return part
    return ""


def _matches_host(text, core):
    """True when text names the domain: 'Acme Widgets' for acme.com, or by its
    initials, 'Shiv Nadar University' for snu.edu.in."""
    compact = re.sub(r"[^a-z0-9]", "", (text or "").lower())
    if not core or len(compact) < 3:
        return False
    if core in compact or compact in core:
        return True
    initials = "".join(w[0] for w in re.findall(r"[a-z0-9]+", (text or "").lower()))
    return len(core) >= 2 and initials == core


def site_facts(artifacts, entity_identity=None):
    """Brand-level facts with the source of each one."""
    identity = (entity_identity or {}).get("data") or {}
    home = _home(artifacts)
    origin = artifacts.normalized_origin.rstrip("/")
    host = _host(origin)
    facts = {"url": origin + "/", "sources": {"url": "audited origin"}}

    name, source = "", ""
    core = re.sub(r"[^a-z0-9]", "", host.split(".")[0]) if host else ""
    # An Organization node on the home page that names the domain is the brand.
    # The site-wide identity is trusted only when it is unambiguous: a site with
    # department or sub-brand Organization nodes must not lend one of them its name.
    home_org = next((str(n["name"]) for p, n in _org_nodes([home] if home is not None else [])
                     if isinstance(n.get("name"), str) and _matches_host(n["name"], core)), "")
    if home_org:
        name, source = home_org, "Organization JSON-LD on the home page"
    elif identity.get("canonical_name") and identity.get("confidence", 0) >= 0.85 \
            and identity["canonical_name"] != artifacts.normalized_origin:
        name, source = str(identity["canonical_name"]), "Organization JSON-LD name"
    elif home is not None and _meta(home, "og:site_name"):
        name, source = _meta(home, "og:site_name"), "og:site_name on the home page"
    elif home is not None and _meta(home, "application-name"):
        name, source = _meta(home, "application-name"), "application-name on the home page"
    elif home is not None and _brand_from_title(home.title, host):
        name, source = _brand_from_title(home.title, host), "home page title"
    facts["name"] = name[:120] or "REPLACE_WITH_BRAND_NAME"
    if name:
        facts["sources"]["name"] = source

    logo = None
    for page, node in _org_nodes(artifacts.pages):
        value = node.get("logo")
        if hasattr(value, "get"):
            value = value.get("url")
        logo = _absolute(value if isinstance(value, str) else "", page.final_url or page.url)
        if logo:
            facts["sources"]["logo"] = "existing Organization logo"
            break
    if not logo and home is not None:
        icons = list((home.features or {}).get("icon_links") or ())
        icons.sort(key=lambda i: ("apple-touch-icon" not in i.get("rel", ""), i.get("href", "").lower().endswith(".ico")))
        for icon in icons:
            logo = _absolute(icon.get("href"), home.final_url or home.url)
            if logo:
                facts["sources"]["logo"] = f"<link rel=\"{icon.get('rel')}\"> on the home page (prefer a square logo of 112 px or more)"
                break
    facts["logo"] = logo or "REPLACE_WITH_LOGO_URL"

    trusted = identity.get("confidence", 0) >= 0.85
    same_as = [u for u in identity.get("same_as_urls") or () if isinstance(u, str)] if trusted else []
    if same_as:
        facts["sources"]["sameAs"] = "existing Organization sameAs"
    elif home is not None:
        for link in home.external_links:
            h = _host(link)
            try:
                path = urlsplit(link).path
            except ValueError:
                continue
            if any(h == d or h.endswith("." + d) for d in _PROFILE_HOSTS) and path.strip("/") \
                    and not _SHARE_PATH.search(path) and link not in same_as:
                same_as.append(link)
        if same_as:
            facts["sources"]["sameAs"] = "profile links on the home page"
    facts["same_as"] = same_as[:10]

    description = (home.meta_description or "").strip() if home is not None else ""
    facts["description"] = description[:300] or "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION"
    if description:
        facts["sources"]["description"] = "home page meta description"
    return facts


def _organization(facts):
    node = {"@type": "Organization", "@id": facts["url"] + "#organization", "name": facts["name"],
            "url": facts["url"], "logo": facts["logo"], "description": facts["description"]}
    if facts["same_as"]:
        node["sameAs"] = facts["same_as"]
    return node


def _page_label(page):
    heading = next((h for h in page.headings if h.strip()), "")
    return (heading or page.title or "REPLACE_WITH_PAGE_NAME").strip()[:150]


def _page_node(page, facts):
    """A schema.org node for one page, by its classified page type."""
    url = _clean_url(page.final_url or page.url)
    kind = _SCHEMA_FOR_TYPE.get(page.page_type, "WebPage")
    label = _page_label(page)
    description = (page.meta_description or "").strip()[:300] or "REPLACE_WITH_PAGE_DESCRIPTION"
    org_ref = {"@id": facts["url"] + "#organization"}
    node = {"@type": kind, "url": url}
    if kind == "Product":
        node.update(name=label, description=description, brand=org_ref,
                    image=_lead_image(page) or "REPLACE_WITH_PRODUCT_IMAGE_URL",
                    offers={"@type": "Offer", "price": "REPLACE_WITH_PRICE",
                            "priceCurrency": "REPLACE_WITH_CURRENCY_CODE",
                            "availability": "https://schema.org/InStock", "url": url})
    elif kind == "Article":
        node.update(headline=label[:110], description=description,
                    image=_lead_image(page) or "REPLACE_WITH_ARTICLE_IMAGE_URL",
                    author={"@type": "Person", "name": "REPLACE_WITH_AUTHOR_NAME", "url": "REPLACE_WITH_AUTHOR_PAGE_URL"},
                    datePublished="REPLACE_WITH_ISO_DATE", dateModified="REPLACE_WITH_ISO_DATE", publisher=org_ref)
    elif kind == "Service":
        node.update(name=label, description=description, provider=org_ref,
                    areaServed="REPLACE_WITH_AREA_SERVED")
    elif kind == "SoftwareApplication":
        node.update(name=label, description=description, publisher=org_ref,
                    applicationCategory="REPLACE_WITH_APPLICATION_CATEGORY",
                    operatingSystem="REPLACE_WITH_OPERATING_SYSTEM",
                    offers={"@type": "Offer", "price": "REPLACE_WITH_PRICE",
                            "priceCurrency": "REPLACE_WITH_CURRENCY_CODE"})
    else:
        node.update(name=label, description=description, about=org_ref)
    return node


def _lead_image(page):
    image = (page.features or {}).get("lcp_image") or {}
    return _absolute(image.get("src") or _meta(page, "og:image"), page.final_url or page.url)


def _jsonld_block(nodes):
    payload = {"@context": "https://schema.org", "@graph": nodes} if len(nodes) > 1 else \
        {"@context": "https://schema.org", **nodes[0]}
    text = json.dumps(payload, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return '<script type="application/ld+json">\n' + text + "\n</script>"


def _website(facts):
    return {"@type": "WebSite", "@id": facts["url"] + "#website", "name": facts["name"], "url": facts["url"],
            "publisher": {"@id": facts["url"] + "#organization"}}


def _jsonld_for_pages(pages, facts, home_url):
    """One block per distinct page type among pages, plus the site-wide nodes."""
    blocks, seen = [], set()
    site_nodes = [_organization(facts), _website(facts)]
    blocks.append(("Home page " + home_url, _jsonld_block(site_nodes)))
    for page in pages:
        if page.page_type == "home" or page.page_type in seen or len(blocks) > _MAX_PAGES:
            continue
        seen.add(page.page_type)
        blocks.append(((page.page_type or "page").capitalize() + " page " + (page.final_url or page.url),
                       _jsonld_block([_page_node(page, facts)])))
    return blocks


def _attr(value):
    return html.escape(value or "", quote=True)


def _canonical_lines(pages):
    return [f"<!-- {p.final_url or p.url} -->\n<link rel=\"canonical\" href=\"{_attr(_clean_url(p.final_url or p.url))}\">"
            for p in pages[:_MAX_PAGES]]


def _shareable_image(url):
    """A URL usable as og:image: an http(s) raster image. Facebook, LinkedIn and X
    do not render SVG previews."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        path = urlsplit(url).path.lower()
    except ValueError:
        return None
    return None if path.endswith((".svg", ".svgz", ".ico")) else url


def _og_values(page, facts):
    image = _shareable_image(_lead_image(page)) or _shareable_image(facts["logo"])
    return {
        "og:title": (page.title or _page_label(page))[:120],
        "og:description": (page.meta_description or "").strip()[:200] or "REPLACE_WITH_PAGE_DESCRIPTION",
        "og:image": image or "REPLACE_WITH_SHARE_IMAGE_URL",
        "og:url": _clean_url(page.final_url or page.url),
        "og:type": "article" if page.page_type == "article" else "website",
        "og:site_name": facts["name"],
    }


def _og_lines(pages, facts, only_missing=True, keys=None):
    out = []
    for page in pages[:_MAX_PAGES]:
        values = _og_values(page, facts)
        wanted = keys or [k for k in ("og:title", "og:description", "og:image", "og:url")
                          if not only_missing or not _meta(page, k)]
        if not wanted:
            continue
        lines = [f"<meta property=\"{k}\" content=\"{_attr(values[k])}\">" for k in wanted]
        out.append(f"<!-- {page.final_url or page.url} -->\n" + "\n".join(lines))
    return out


def _twitter_lines(pages, facts):
    out = []
    for page in pages[:_MAX_PAGES]:
        card = "summary_large_image" if _shareable_image(_lead_image(page)) or _meta(page, "og:image") else "summary"
        out.append(f"<!-- {page.final_url or page.url} -->\n<meta name=\"twitter:card\" content=\"{card}\">")
    return out


def _llms_txt(artifacts, facts):
    pages = [p for p in artifacts.pages if p.status_code == 200 and p.features and p.page_type != "legal"]
    order = {"home": 0, "about": 1, "product": 2, "service": 2, "software": 2, "category": 3, "listing": 3,
             "article": 4, "contact": 5}
    pages.sort(key=lambda p: (order.get(p.page_type, 6), p.url))
    lines = [f"# {facts['name']}", "", f"> {facts['description']}", "", "## Key pages", ""]
    seen = set()
    for page in pages:
        url = _clean_url(page.final_url or page.url)
        if url in seen:
            continue
        seen.add(url)
        title = re.sub(r"[\[\]]", "", page.title or _page_label(page)).strip()[:100] or url
        description = " ".join((page.meta_description or "").split())[:160]
        lines.append(f"- [{title}]({url})" + (f": {description}" if description else ""))
        if len(seen) >= 12:
            break
    return "\n".join(lines) + "\n"


def _location_block(pages, facts):
    address = next((t for p in pages for t in (p.features or {}).get("address_text") or ()
                    if re.search(r"\d", t)), "") or next(
        (t for p in pages for t in (p.features or {}).get("postal_address_text") or ()), "")
    org = _organization(facts)
    org["address"] = address or "REPLACE_WITH_STREET_ADDRESS"
    org["geo"] = {"@type": "GeoCoordinates", "latitude": "REPLACE_WITH_LATITUDE", "longitude": "REPLACE_WITH_LONGITUDE"}
    org["areaServed"] = "REPLACE_WITH_AREA_SERVED"
    return _jsonld_block([org]), bool(address)


def build_snippet(check_id, pages, artifacts, facts):
    """The snippet for one check over its affected pages, or None when the check
    has no markup fix or no page to build from."""
    home = _home(artifacts)
    home_url = (home.final_url or home.url) if home is not None else facts["url"]
    # Brand facts each snippet draws on; only their sources are listed in filled_from.
    used = ("url", "name", "logo", "sameAs", "description")
    filled = {}
    fmt, placement = "html", "Inside <head> of each page named in the comments"
    if check_id == "no-jsonld":
        blocks = _jsonld_for_pages(pages or ([home] if home else []), facts, home_url)
        code = "\n\n".join(f"<!-- {where} -->\n{block}" for where, block in blocks)
        filled["page fields"] = "each page's H1 or title, meta description and URL"
    elif check_id.startswith("page-type-schema-gap:"):
        kind = check_id.split(":", 1)[1]
        if kind == "home":
            code = f"<!-- {home_url} -->\n" + _jsonld_block([_organization(facts), _website(facts)])
        else:
            target = next((p for p in pages if p.page_type == kind), pages[0] if pages else None)
            if target is None:
                return None
            code = f"<!-- {target.final_url or target.url} -->\n" + _jsonld_block([_page_node(target, facts)])
            used = ("url",)
            filled["page fields"] = "the page's H1 or title, meta description and URL"
    elif check_id in ("no-llms-txt", "llms-txt-invalid"):
        fmt, placement = "markdown", "Save as /llms.txt at the site root, served as text/plain"
        code = _llms_txt(artifacts, facts)
        used = ("name", "description")
        filled["key pages"] = "crawled pages, with their titles and meta descriptions"
    elif check_id in ("missing-canonical", "invalid-canonical"):
        if not pages:
            return None
        code = "\n\n".join(_canonical_lines(pages))
        used = ()
        filled["href"] = "each page's final URL, without fragments or tracking parameters"
    elif check_id in ("social-metadata", "social-url"):
        if check_id == "social-metadata":
            lines = _og_lines(pages, facts)
            filled["values"] = "each page's title, meta description, final URL and lead image"
        else:
            lines = _og_lines(pages, facts, only_missing=False, keys=["og:url", "og:image"])
            filled["values"] = "each page's final URL and lead image, as full URLs"
        if not lines:
            return None
        code = "\n\n".join(lines)
        used = ("logo",) if facts["logo"] in code else ()
    elif check_id == "twitter-card":
        if not pages:
            return None
        code = "\n\n".join(_twitter_lines(pages, facts))
        used = ()
        filled["card"] = "summary_large_image when the page has a lead image, otherwise summary"
    elif check_id == "location-markup-missing":
        block, found = _location_block(pages, facts)
        code = f"<!-- {home_url} -->\n" + block
        if found:
            filled["address"] = "the address shown on the page"
    elif check_id == "contact-markup-missing":
        email, phone = organization_contact(pages, _host(home_url))
        org = _organization(facts)
        org["email"] = email or "REPLACE_WITH_EMAIL"
        org["telephone"] = phone or "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
        org["contactPoint"] = [{"@type": "ContactPoint", "contactType": "REPLACE_WITH_CONTACT_TYPE",
                                "email": org["email"], "telephone": org["telephone"]}]
        code = f"<!-- {home_url} -->\n" + _jsonld_block([org])
        if email:
            filled["email"] = "the most used email on the site's own domain"
        if phone:
            filled["telephone"] = "the phone number shown on the most pages"
    else:
        return None
    filled = {**{k: v for k, v in facts["sources"].items() if k in used}, **filled}
    placeholders = sorted(set(_PLACEHOLDER.findall(code)))
    return {"format": fmt, "placement": placement, "code": code, "filled_from": filled,
            "placeholders": placeholders, "note": _NOTE}


SNIPPET_CHECKS = frozenset({"no-jsonld", "no-llms-txt", "llms-txt-invalid", "missing-canonical",
                            "invalid-canonical", "social-metadata", "social-url", "twitter-card",
                            "location-markup-missing", "contact-markup-missing"})


def _wants_snippet(check_id):
    return check_id in SNIPPET_CHECKS or (check_id or "").startswith("page-type-schema-gap:")


def attach_fix_snippets(findings, recommendations, artifacts, entity_identity=None):
    """Attach a snippet to every finding and recommendation whose check has a
    markup fix. A recommendation that points at a finding gets none: the finding
    it names carries the snippet. Never raises: a snippet is an aid, and a failure to build one must not cost
    the report."""
    try:
        facts = site_facts(artifacts, entity_identity)
    except Exception:
        return
    by_url = {}
    for page in artifacts.pages:
        for url in (page.url, page.final_url):
            if url:
                by_url.setdefault(url, page)
    pages_of = {f.get("id"): list(f.get("affected_pages") or ()) for f in findings}
    for item in list(findings) + list(recommendations):
        if not isinstance(item, dict) or "finding_id" in item:
            # A recommendation that points at a finding: the snippet goes on
            # the finding it names, not on a copy.
            continue
        check_id = item.get("check_id")
        if not _wants_snippet(check_id):
            check_id = next((c for c in item.get("check_ids") or () if _wants_snippet(c)), None)
        if not check_id:
            continue
        urls = list(item.get("affected_pages") or ()) or pages_of.get((item.get("provenance") or {}).get("finding_id"), [])
        pages = [by_url[u] for u in urls if u in by_url]
        try:
            snippet = build_snippet(check_id, pages, artifacts, facts)
        except Exception:
            snippet = None
        if snippet:
            action = dict(item.get("suggested_action") or {})
            action["snippet"] = snippet
            item["suggested_action"] = action
