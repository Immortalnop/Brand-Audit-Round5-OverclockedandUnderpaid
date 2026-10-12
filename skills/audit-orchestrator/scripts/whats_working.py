"""whats_working.py -- checks that ran and found nothing to fix.

A report that only lists problems cannot show that the audit looked and found
the rest in order. This section lists passed checks, each with the observation
that passed. A check is listed only when all three hold:
  - every specialist that runs it finished (status "success"), so a check that
    was skipped, timed out or failed is never shown as passed;
  - no finding, hygiene item or recommendation carries any of its check IDs, so
    the section never contradicts the rest of the report;
  - the observation it states holds on the acquisition snapshot (for example
    "all 12 pages checked have a title"). A check with nothing to look at is not
    listed.
When no content page could be analysed, only the site-level checks (robots.txt,
sitemap, llms.txt) can be listed. No requests are made.
"""
from urllib.parse import urlsplit
from check_helpers import content_pages


def _plural(n, noun):
    return f"{n} {noun}{'' if n == 1 else 's'}"


def _all(pages, test):
    return bool(pages) and all(test(p) for p in pages)


def _robots(ctx):
    r = ctx["artifacts"].robots_data
    if r.get("conservative_fail_closed") or r.get("general_disallow") is not False:
        return None
    if r.get("status") == "ok":
        return "robots.txt was read and lets crawlers fetch the start URL.", None
    if r.get("status") == "absent":
        return "The site has no robots.txt (HTTP 404), so crawlers may fetch it by default.", None
    return None


def _crawlers(ctx):
    r = ctx["artifacts"].robots_data
    directives = dict(r.get("ai_crawler_directives") or {})
    if not directives or any(v != "allow" for v in directives.values()) or r.get("ai_crawler_paths"):
        return None
    return (f"robots.txt lets all {len(directives)} search, AI search, user-fetch and training crawlers checked "
            "fetch the homepage and the key pages sampled.", None)


def _no_bot_wall(ctx):
    fetched = [p for p in ctx["artifacts"].pages if p.status_code]
    if not fetched or any(w in ("bot_challenge", "rate_limited") for p in fetched for w in p.warnings):
        return None
    return (f"None of the {_plural(len(fetched), 'page')} fetched answered with a bot challenge or rate limit.",
            len(fetched))


def _sitemap(ctx):
    s = ctx["artifacts"].sitemap_data
    if s.get("status") != "ok" or not s.get("urls"):
        return None
    return f"An XML sitemap was read; it lists {_plural(s.get('url_entries') or len(s['urls']), 'URL')}.", None


def _llms(ctx):
    llms = ctx["artifacts"].llms_txt_data
    return ("/llms.txt is published.", None) if llms.get("present") and llms.get("status") == "ok" else None


def _https(ctx):
    pages = ctx["pages"]
    if not _all(pages, lambda p: urlsplit(p.final_url or p.url).scheme == "https"):
        return None
    return f"All {_plural(len(pages), 'page')} checked were served over HTTPS.", len(pages)


def _http_status(ctx):
    fetched = [p for p in ctx["artifacts"].pages if p.status_code and "bot_challenge" not in p.warnings]
    if not fetched or any(p.status_code >= 400 for p in fetched):
        return None
    return f"None of the {_plural(len(fetched), 'page')} fetched answered with an HTTP error.", len(fetched)


def _page_test(test, sentence):
    def check(ctx):
        pages = ctx["pages"]
        return (sentence.format(n=_plural(len(pages), "page")), len(pages)) if _all(pages, test) else None
    return check


def _indexable(ctx):
    import re
    block = re.compile(r"(?<![\w-])(?:noindex|nosnippet|none)(?![\w-])|max-snippet\s*:\s*0(?!\d)")
    def directives(p):
        meta = (p.features or {}).get("meta") or {}
        values = [v for k, vs in meta.items() if k == "robots" or k.endswith("bot") for v in vs]
        values += [str(v) for k, v in dict(p.response_headers or {}).items() if str(k).lower() == "x-robots-tag"]
        return " ".join(values).lower()
    pages = ctx["pages"]
    if not _all(pages, lambda p: not block.search(directives(p))):
        return None
    return (f"None of the {_plural(len(pages), 'page')} checked carries noindex, nosnippet or max-snippet:0 "
            "(meta robots or X-Robots-Tag).", len(pages))


def _structured(ctx):
    pages = ctx["pages"]
    with_jsonld = [p for p in pages if p.jsonld_blocks]
    if not with_jsonld or any("malformed_jsonld_block" in p.warnings for p in ctx["artifacts"].pages):
        return None
    return (f"JSON-LD is present on {len(with_jsonld)} of the {_plural(len(pages), 'page')} checked, and every "
            "block parsed and carried its required properties.", len(pages))


def _raw_html(ctx):
    pages = ctx["pages"]
    ok = _all(pages, lambda p: (p.features or {}).get("full_visible_chars", 0) >= 200
              and not (p.features or {}).get("spa_mount_empty"))
    if not ok:
        return None
    return (f"All {_plural(len(pages), 'page')} checked carry their text in the server HTML, so crawlers that do "
            "not run JavaScript can read it.", len(pages))


def _images(ctx):
    pages = ctx["pages"]
    images = sum(int((p.features or {}).get("images") or 0) for p in pages)
    if not images or any((p.features or {}).get("missing_alt") for p in pages):
        return None
    return f"All {_plural(images, 'image')} on the pages checked carry an alt attribute.", len(pages)


def _links(ctx):
    data = (ctx["results"].get("site_graph") or {}).get("data") or {}
    nodes = data.get("nodes") or {}
    if len(nodes) < 2 or data.get("dead_ends"):
        return None
    return f"Each of the {_plural(len(nodes), 'page')} crawled links to at least one other page on the site.", len(nodes)


def _identity(ctx):
    data = (ctx["results"].get("entity_identity") or {}).get("data") or {}
    if data.get("identity_level", 1) != 1 or not data.get("canonical_name") or data.get("ambiguity_type"):
        return None
    return f"Organization markup declares the brand as '{data['canonical_name']}' with no conflicting name.", None


def _dates(ctx):
    m = (ctx["results"].get("freshness") or {}).get("metrics") or {}
    if not m.get("date_signals_found") or m.get("expired_items") or m.get("date_contradictions"):
        return None
    return (f"{_plural(m['date_signals_found'], 'date')} found on the pages checked: no expired offer and no "
            "contradiction between visible, markup and sitemap dates.", None)


# (key, title, specialists that run it, check IDs that contradict it, test, site level)
CHECKS = (
    ("robots-txt", "robots.txt allows crawling", ("crawlability",),
     ("robots-block", "robots-unreachable", "robots-rate-limited", "bot-challenge-robots"), _robots, True),
    ("crawler-access", "Search and AI crawlers may fetch the site", ("ai_crawler_access",),
     ("search-crawler-blocked", "ai-crawler-blocked", "user-fetch-blocked", "training-crawler-blocked",
      "ai-crawler-unchecked"), _crawlers, True),
    ("bot-access", "Automated clients receive the real content", ("access",),
     ("bot-challenge-sitewide", "bot-challenge-rate", "bot-challenge-robots", "robots-rate-limited"), _no_bot_wall, True),
    ("sitemap", "An XML sitemap is available", ("performance",), ("sitemap-unavailable",), _sitemap, True),
    ("llms-txt", "llms.txt is published", ("llms_txt",), ("no-llms-txt", "llms-txt-unchecked"), _llms, True),
    ("https", "Pages are served over HTTPS", ("metadata", "directives"), ("http-transport", "tls-health"), _https, False),
    ("http-status", "Fetched pages load without HTTP errors", ("crawlability",), ("broken-pages",), _http_status, False),
    ("titles", "Every page has a title", ("metadata",), ("missing-title",),
     _page_test(lambda p: (p.title or "").strip(), "All {n} checked have a document title."), False),
    ("descriptions", "Every page has a meta description", ("metadata",), ("missing-description",),
     _page_test(lambda p: (p.meta_description or "").strip(), "All {n} checked have a meta description."), False),
    ("language", "Every page declares its language", ("metadata",), ("missing-language",),
     _page_test(lambda p: ((p.features or {}).get("lang") or "").strip(), "All {n} checked declare their language (html lang)."), False),
    ("canonical", "Every page declares a canonical URL", ("metadata",),
     ("missing-canonical", "invalid-canonical", "cross-origin-canonical"),
     _page_test(lambda p: any((v or "").strip() for v in (p.features or {}).get("canonical_values") or ()),
                "All {n} checked declare a canonical URL."), False),
    ("indexable", "Pages are open to indexing and snippets", ("directives",),
     ("noindex", "nosnippet", "snippet-suppression"), _indexable, False),
    ("structured-data", "Structured data parses and is complete", ("machine_readability", "structured_data_validity"),
     ("no-jsonld", "malformed-jsonld", "schema-missing-required", "schema-invalid-value"), _structured, False),
    ("raw-html", "Content is in the server HTML", ("rendering",),
     ("render-gap", "render-gap-unconfirmed", "hash-routing"), _raw_html, False),
    ("h1", "Every page has an H1 heading", ("engagement",),
     ("h1", "no-headings", "page-orientation", "homepage-orientation"),
     _page_test(lambda p: ((p.features or {}).get("h1_count") or 0) >= 1, "All {n} checked have an H1 heading."), False),
    ("viewport", "Mobile viewport is declared and zoom is allowed", ("engagement",), ("viewport", "zoom"),
     _page_test(lambda p: any((v or "").strip() for v in (p.features or {}).get("viewport") or ()),
                "All {n} checked declare a mobile viewport, and none blocks zooming."), False),
    ("image-alt", "Images carry alt attributes", ("engagement",), ("missing-alt",), _images, False),
    ("internal-links", "Every page links onward", ("site_graph", "engagement"),
     ("dead-ends", "no-internal-navigation", "internal-discoverability"), _links, False),
    ("identity", "The brand identity is declared", ("entity_identity", "answer_content"),
     ("identity-not-declared", "page-type-schema-gap:home"), _identity, False),
    ("dates", "Dates are current and consistent", ("freshness",),
     ("expired-offer", "date-contradiction", "stale-update-claim"), _dates, False),
)


def reported_check_ids(items):
    ids = set()
    for item in items:
        if isinstance(item, dict):
            if item.get("check_id"):
                ids.add(item["check_id"])
            ids.update(item.get("check_ids") or ())
    return ids


def whats_working(artifacts, results, reported_items):
    """[{id, check, title, check_ids, evidence, pages_checked}] in a fixed order.
    results maps the specialist names scheduled by run_audit.py to their results;
    reported_items is every finding, hygiene item and recommendation."""
    flagged = reported_check_ids(reported_items)
    pages = content_pages(artifacts, require_features=False)
    ctx = {"artifacts": artifacts, "results": results, "pages": pages}
    out = []
    for key, title, skills, check_ids, test, site_level in CHECKS:
        if not pages and not site_level:
            continue
        if any((results.get(name) or {}).get("status") != "success" for name in skills):
            continue
        if flagged & set(check_ids):
            continue
        try:
            passed = test(ctx)
        except Exception:
            passed = None  # a check that cannot be evaluated is never shown as passed
        if not passed:
            continue
        evidence, pages_checked = passed
        out.append({"id": f"W-{len(out) + 1:03d}", "check": key, "title": title, "check_ids": sorted(check_ids),
                    "evidence": evidence, "pages_checked": pages_checked})
    return out
