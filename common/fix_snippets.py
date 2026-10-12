"""fix_snippets.py -- ready-to-paste fixes built from what the audit observed.

A finding that says "add an llms.txt" or "add canonical tags" leaves the reader to
write them. For the checks whose fix is a block of markup or a file, this module
writes that block from facts the audit already holds: the brand name, the logo,
the profile links the site shows, each page's title, description and URL, and
the contact details the site displays.

JSON-LD drafts for no-jsonld and the page-type gaps are built by the detector
itself (analyze_machine_readability.proposed_snippet); this module covers the
other markup fixes, so no finding carries two drafts.

Rules:
  - Nothing is invented. A value the audit did not observe is written as a
    REPLACE_WITH_... placeholder, and every placeholder is listed next to the code.
  - Every filled value names its source in filled_from.
  - No requests: everything comes from the acquisition snapshot and the entity
    identity artifact.
  - Bounded: at most a few pages per snippet.
  - og:image is never an SVG or ICO file, which social platforms do not render.

The snippet is attached as suggested_action["snippet"] with the keys format,
placement, code, filled_from, placeholders and note. Recommend-only: it is text
in the report and is never applied to the site.
"""
import html
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

from check_helpers import organization_contact, site_host, is_role_mailbox
from structured_data import iter_nodes, types_of, ORGANIZATION_TYPES

_PLACEHOLDER = re.compile(r"REPLACE_WITH_[A-Z_]+")
_PROFILE_HOSTS = ("twitter.com", "x.com", "facebook.com", "linkedin.com", "instagram.com", "youtube.com",
                  "tiktok.com", "pinterest.com", "github.com", "wikipedia.org", "wikidata.org", "crunchbase.com",
                  "threads.net", "bsky.app", "trustpilot.com", "g2.com", "glassdoor.com")
_SHARE_PATH = re.compile(r"/(?:sharer|share|intent|sharearticle|dialog|plugins|hashtag|search)(?:[/.?]|$)", re.I)
_TRACKING = re.compile(r"^(?:utm_[a-z_]+|gclid|fbclid|msclkid|mc_cid|mc_eid|_ga|_gl)$", re.I)
_MAX_PAGES = 3
_NOTE = ("Generated from the audited pages. Check every value against the live page, replace each "
         "REPLACE_WITH_ placeholder, and validate before publishing.")


def _host(url):
    try:
        return site_host(url)
    except ValueError:
        return ""


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


def _content(artifacts):
    return [p for p in artifacts.pages if p.status_code == 200 and p.features
            and not {"bot_challenge", "rate_limited", "login_page"} & set(p.warnings)]


def _home(artifacts):
    pages = _content(artifacts)
    return next((p for p in pages if p.page_type == "home"), pages[0] if pages else None)


def site_facts(artifacts, entity_identity=None):
    """Brand-level facts with the source of each one."""
    identity = (entity_identity or {}).get("data") or {}
    home = _home(artifacts)
    origin = artifacts.normalized_origin.rstrip("/")
    facts = {"url": origin + "/", "sources": {"url": "audited origin"}}
    name, source = "", ""
    if identity.get("canonical_name") and identity.get("confidence", 0) >= 0.6:
        name = str(identity["canonical_name"])
        source = ("Organization JSON-LD name" if identity.get("identity_level", 1) == 1
                  else "brand name inferred from the site (" + str((identity.get("identity_sources") or [{}])[0].get("source", "site metadata")) + ")")
    elif home is not None and _meta(home, "og:site_name"):
        name, source = _meta(home, "og:site_name"), "og:site_name on the home page"
    facts["name"] = name[:120] or "REPLACE_WITH_BRAND_NAME"
    if name:
        facts["sources"]["name"] = source

    logo = None
    for page in _content(artifacts):
        for node in iter_nodes(page.jsonld_blocks):
            if types_of(node) & ORGANIZATION_TYPES:
                value = node.get("logo")
                if hasattr(value, "get"):
                    value = value.get("url")
                logo = _absolute(value if isinstance(value, str) else "", page.final_url or page.url)
                if logo:
                    facts["sources"]["logo"] = "existing Organization logo"
                    break
        if logo:
            break
    if not logo and home is not None:
        icons = sorted((home.features or {}).get("icon_links") or (),
                       key=lambda i: ("apple-touch-icon" not in i.get("rel", ""), i.get("href", "").lower().endswith(".ico")))
        for icon in icons:
            logo = _absolute(icon.get("href"), home.final_url or home.url)
            if logo:
                facts["sources"]["logo"] = (f"<link rel=\"{icon.get('rel')}\"> on the home page "
                                            "(prefer a square logo of 112 px or more)")
                break
    facts["logo"] = logo or "REPLACE_WITH_LOGO_URL"

    same_as = [u for u in identity.get("same_as_urls") or () if isinstance(u, str)]
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


def _website(facts):
    return {"@type": "WebSite", "@id": facts["url"] + "#website", "name": facts["name"], "url": facts["url"],
            "publisher": {"@id": facts["url"] + "#organization"}}


def _jsonld_block(nodes):
    payload = ({"@context": "https://schema.org", "@graph": nodes} if len(nodes) > 1
               else {"@context": "https://schema.org", **nodes[0]})
    text = json.dumps(payload, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return '<script type="application/ld+json">\n' + text + "\n</script>"


def _attr(value):
    return html.escape(value or "", quote=True)


def _shareable_image(url):
    """An http(s) raster image: Facebook, LinkedIn and X do not render SVG or ICO previews."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        path = urlsplit(url).path.lower()
    except ValueError:
        return None
    return None if path.endswith((".svg", ".svgz", ".ico")) else url


def _og_values(page, facts):
    image = _shareable_image(_absolute(_meta(page, "og:image"), page.final_url or page.url)) or _shareable_image(facts["logo"])
    label = next((h for h in page.headings if h.strip()), "") or page.title or "REPLACE_WITH_PAGE_NAME"
    return {"og:title": (page.title or label)[:120],
            "og:description": (page.meta_description or "").strip()[:200] or "REPLACE_WITH_PAGE_DESCRIPTION",
            "og:image": image or "REPLACE_WITH_SHARE_IMAGE_URL",
            "og:url": _clean_url(page.final_url or page.url)}


def _llms_txt(artifacts, facts):
    pages = [p for p in _content(artifacts) if p.page_type != "legal"]
    order = {"home": 0, "about": 1, "product": 2, "service": 2, "software": 2, "category": 3, "article": 4, "contact": 5}
    pages.sort(key=lambda p: (order.get(p.page_type, 6), p.url))
    lines = [f"# {facts['name']}", "", f"> {facts['description']}", "", "## Key pages", ""]
    seen = set()
    for page in pages:
        url = _clean_url(page.final_url or page.url)
        if url in seen:
            continue
        seen.add(url)
        title = re.sub(r"[\[\]]", "", page.title or url).strip()[:100] or url
        description = " ".join((page.meta_description or "").split())[:160]
        lines.append(f"- [{title}]({url})" + (f": {description}" if description else ""))
        if len(seen) >= 12:
            break
    return "\n".join(lines) + "\n"


def build_snippet(check_id, pages, artifacts, facts):
    """The snippet for one check over its affected pages, or None."""
    home = _home(artifacts)
    home_url = (home.final_url or home.url) if home is not None else facts["url"]
    used, filled = ("url", "name", "logo", "sameAs", "description"), {}
    fmt, placement = "html", "Inside <head> of each page named in the comments"
    if check_id == "identity-not-declared":
        code = f"<!-- {home_url} -->\n" + _jsonld_block([_organization(facts), _website(facts)])
    elif check_id == "no-llms-txt":
        fmt, placement = "markdown", "Save as /llms.txt at the site root, served as text/plain"
        code = _llms_txt(artifacts, facts)
        used = ("name", "description")
        filled["key pages"] = "crawled pages, with their titles and meta descriptions"
    elif check_id in ("missing-canonical", "invalid-canonical"):
        if not pages:
            return None
        code = "\n\n".join(f"<!-- {p.final_url or p.url} -->\n<link rel=\"canonical\" "
                           f"href=\"{_attr(_clean_url(p.final_url or p.url))}\">" for p in pages[:_MAX_PAGES])
        used = ()
        filled["href"] = "each page's final URL, without fragments or tracking parameters"
    elif check_id in ("social-metadata", "social-url"):
        out = []
        for page in pages[:_MAX_PAGES]:
            values = _og_values(page, facts)
            keys = (["og:url", "og:image"] if check_id == "social-url"
                    else [k for k in values if not _meta(page, k)])
            if keys:
                out.append(f"<!-- {page.final_url or page.url} -->\n"
                           + "\n".join(f"<meta property=\"{k}\" content=\"{_attr(values[k])}\">" for k in keys))
        if not out:
            return None
        code = "\n\n".join(out)
        used = ("logo",) if facts["logo"] in code else ()
        filled["values"] = "each page's title, meta description, final URL and share image"
    elif check_id == "twitter-card":
        if not pages:
            return None
        code = "\n\n".join(
            f"<!-- {p.final_url or p.url} -->\n<meta name=\"twitter:card\" content=\""
            f"{'summary_large_image' if _meta(p, 'og:image') else 'summary'}\">" for p in pages[:_MAX_PAGES])
        used = ()
        filled["card"] = "summary_large_image when the page has an og:image, otherwise summary"
    elif check_id == "contact-markup-missing":
        emails, phones = organization_contact(_content(artifacts), _host(home_url))
        # Only a role mailbox (hello@, support@ ...) is filled in: a person's
        # address shown on a page is not the organization's contact address.
        email = next((e for e in emails if is_role_mailbox(e)), None)
        phone = phones[0] if phones else None
        org = _organization(facts)
        org["email"] = email or "REPLACE_WITH_EMAIL"
        org["telephone"] = phone or "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
        org["contactPoint"] = [{"@type": "ContactPoint", "contactType": "REPLACE_WITH_CONTACT_TYPE",
                                "email": org["email"], "telephone": org["telephone"]}]
        code = f"<!-- {home_url} -->\n" + _jsonld_block([org])
        if email:
            filled["email"] = "the role mailbox on the site's own domain shown on the most pages"
        elif emails:
            filled["email"] = ("not filled: the addresses shown (" + ", ".join(emails[:3]) + ") look personal; "
                               "use the organization's role mailbox")
        if phone:
            filled["telephone"] = "the phone number shown on the home/contact page or on the most pages"
    else:
        return None
    filled = {**{k: v for k, v in facts["sources"].items() if k in used}, **filled}
    return {"format": fmt, "placement": placement, "code": code, "filled_from": filled,
            "placeholders": sorted(set(_PLACEHOLDER.findall(code))), "note": _NOTE}


SNIPPET_CHECKS = frozenset({"identity-not-declared", "no-llms-txt", "missing-canonical", "invalid-canonical",
                            "social-metadata", "social-url", "twitter-card", "contact-markup-missing"})


def attach_fix_snippets(items, artifacts, entity_identity=None):
    """Attach a snippet to every finding whose check has a markup fix and that
    carries no detector-built draft. Never raises: a snippet is an aid, and failing
    to build one must not cost the report."""
    try:
        facts = site_facts(artifacts, entity_identity)
    except Exception:
        return
    by_url = {}
    for page in artifacts.pages:
        for url in (page.url, page.final_url):
            if url:
                by_url.setdefault(url, page)
    for item in items:
        if not isinstance(item, dict):
            continue
        action = dict(item.get("suggested_action") or {})
        if action.get("proposed_snippets") or action.get("snippet"):
            continue
        check_id = next((c for c in [item.get("check_id")] + list(item.get("check_ids") or ()) if c in SNIPPET_CHECKS),
                        None)
        if not check_id:
            continue
        pages = [by_url[u] for u in item.get("affected_pages") or () if u in by_url]
        try:
            snippet = build_snippet(check_id, pages, artifacts, facts)
        except Exception:
            snippet = None
        if snippet:
            action["snippet"] = snippet
            item["suggested_action"] = action
