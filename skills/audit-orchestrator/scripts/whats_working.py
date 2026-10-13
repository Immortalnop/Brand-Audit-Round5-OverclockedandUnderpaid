"""whats_working.py -- checks that ran and found nothing to fix.

A check is listed only when all three hold:
  - every skill that runs it finished (status "success"), so a check that was
    skipped, timed out or failed is never shown as passed;
  - no finding or recommendation in the report carries any of its check IDs,
    so the section never contradicts a finding;
  - the observation it states holds, measured on the acquisition snapshot
    (for example "all 12 pages checked have a title"). A check with nothing to
    look at (no page, no image, no robots.txt) is not listed.

When no page could be analyzed, only the checks that read robots.txt, the
sitemap and llms.txt can be listed. No requests are made.
"""
import re
from urllib.parse import urlsplit

from ai_crawlers import describe
from check_helpers import eligible_pages, script_dependent


def _plural(count, noun):
    return f"{count} {noun}{'' if count == 1 else 's'}"


def _all_pages(pages, test):
    return bool(pages) and all(test(p) for p in pages)


# -- Site-level checks: robots.txt, sitemap, llms.txt ------------------------

def _robots(ctx):
    robots = ctx["artifacts"].robots_data
    if robots.get("conservative_fail_closed") or robots.get("general_disallow") is not False:
        return None
    if robots.get("status") == "ok":
        return "robots.txt was read and lets crawlers fetch the start URL.", None
    if robots.get("status") == "absent":
        return "The site has no robots.txt (HTTP 404), so crawlers may fetch it by default.", None
    return None


def _ai_crawlers(ctx):
    robots = ctx["artifacts"].robots_data
    directives = dict(robots.get("ai_crawler_directives") or {})
    if not directives or any(verdict != "allow" for verdict in directives.values()):
        return None
    if any(urls for urls in (robots.get("ai_crawler_section_blocks") or {}).values()):
        return None
    return (f"robots.txt lets all {len(directives)} AI and search crawlers checked fetch the site, and closes no "
            f"discovered site section to them ({describe(directives)}).", None)


def _sitemap(ctx):
    sitemap = ctx["artifacts"].sitemap_data
    if sitemap.get("status") != "ok" or not sitemap.get("urls"):
        return None
    count = sitemap.get("url_entries") or len(sitemap["urls"])
    prefix = "at least " if sitemap.get("partial") else ""
    return f"An XML sitemap was read; it lists {prefix}{_plural(count, 'URL')}.", None


def _llms_txt(ctx):
    llms = ctx["artifacts"].llms_txt_data
    if not llms.get("present") or llms.get("structure_issues"):
        return None
    links = len(llms.get("links") or ())
    if not links:
        return None
    return f"/llms.txt is present, follows the optional artifact format and lists {_plural(links, 'link')}. Google Search ignores it; visibility gains are unmeasured.", None


# -- Page-level checks over the pages the metadata checks read ---------------

def _https(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: urlsplit(p.final_url or p.url).scheme == "https"):
        return None
    return f"All {_plural(len(pages), 'page')} checked were served over HTTPS.", len(pages)


def _no_http_errors(ctx):
    fetched = [p for p in ctx["artifacts"].pages if p.status_code]
    if not fetched or any(p.status_code >= 400 for p in fetched):
        return None
    return (f"None of the {_plural(len(fetched), 'page')} fetched answered with an HTTP error (4xx or 5xx).",
            len(fetched))


def _titles(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: (p.title or "").strip()):
        return None
    return f"All {_plural(len(pages), 'page')} checked have a document title.", len(pages)


def _descriptions(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: (p.meta_description or "").strip()):
        return None
    return f"All {_plural(len(pages), 'page')} checked have a meta description.", len(pages)


def _language(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: (p.features.get("lang") or "").strip()):
        return None
    return f"All {_plural(len(pages), 'page')} checked declare their language (html lang).", len(pages)


def _canonical(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: any((v or "").strip() for v in p.features.get("canonical_values") or ())):
        return None
    return f"All {_plural(len(pages), 'page')} checked declare a canonical URL on this site.", len(pages)


_INDEX_BLOCK = re.compile(r"(?<![\w-])(?:noindex|nosnippet|none)(?![\w-])|max-snippet\s*:\s*0(?!\d)"
                          r"|max-image-preview\s*:\s*none")


def _robots_directives(page):
    """Every robots directive one page states: meta robots, meta tags named for
    a crawler (googlebot and the like) and X-Robots-Tag headers."""
    meta = page.features.get("meta") or {}
    values = [v for name, vs in meta.items() if name == "robots" or name.endswith("bot") for v in vs]
    headers = page.response_headers or {}
    values += [v for name, v in headers.items() if str(name).lower() == "x-robots-tag"]
    return " ".join(str(v) for v in values).lower()


def _indexable(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: not _INDEX_BLOCK.search(_robots_directives(p))):
        return None
    return (f"None of the {_plural(len(pages), 'page')} checked carries a noindex, nosnippet or max-snippet:0 "
            "directive (meta robots or X-Robots-Tag).", len(pages))


def _structured_data(ctx):
    pages = ctx["pages"]
    with_jsonld = [p for p in pages if p.jsonld_blocks]
    if not with_jsonld or any('malformed_jsonld_block' in p.warnings or (p.features or {}).get('jsonld_limitations')
                             for p in ctx['artifacts'].pages):
        return None
    return (f"JSON-LD structured data is on {len(with_jsonld)} of the {_plural(len(pages), 'page')} checked, "
            "and every block parsed.", len(pages))


def _raw_html(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: not script_dependent(p)):
        return None
    return (f"All {_plural(len(pages), 'page')} checked carry their text in the raw HTML, so crawlers that do "
            "not run JavaScript can read it.", len(pages))


def _h1(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: (p.features.get("h1_count") or 0) >= 1):
        return None
    return f"All {_plural(len(pages), 'page')} checked have an H1 heading.", len(pages)


def _viewport(ctx):
    pages = ctx["pages"]
    if not _all_pages(pages, lambda p: any((v or "").strip() for v in p.features.get("viewport") or ())):
        return None
    return (f"All {_plural(len(pages), 'page')} checked declare a mobile viewport, and none blocks zooming.",
            len(pages))


def _image_alt(ctx):
    pages = ctx["pages"]
    images = sum(int(p.features.get("images") or 0) for p in pages)
    missing = sum(int(p.features.get("missing_alt") or 0) for p in pages)
    if not images or missing:
        return None
    return (f"All {_plural(images, 'image')} on the pages checked carry an alt attribute, and none was flagged "
            "as a file name or placeholder.", len(pages))


def _internal_links(ctx):
    data = (ctx["results"].get("site_graph") or {}).get("data") or {}
    nodes = data.get("nodes") or {}
    if len(nodes) < 2 or data.get("dead_ends"):
        return None
    return f"Each of the {_plural(len(nodes), 'page')} crawled links to at least one other page on the site.", len(nodes)


def _metric(ctx, result, name):
    value = ((ctx["results"].get(result) or {}).get("metrics") or {}).get(name)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _offer_dates(ctx):
    found = _metric(ctx, "offer_expiry", "offer_deadlines_found")
    if not found:
        return None
    return (f"{'The' if found == 1 else 'All'} {_plural(found, 'offer end date')} found on the pages checked "
            f"{'is' if found == 1 else 'are'} still current.",
            _metric(ctx, "offer_expiry", "offer_expiry_pages_scanned") or None)


def _facts_match(ctx):
    compared = _metric(ctx, "fact_consistency", "facts_compared_with_text")
    if not compared:
        return None
    return (f"{_plural(compared, 'fact')} stated in structured data (telephone, postal code, opening hours or "
            f"price) {'matches' if compared == 1 else 'match'} what the pages show.", _metric(ctx, "fact_consistency", "fact_consistency_pages") or None)


# (key, title, skills that run the check, check IDs that contradict it,
#  test, site level). Skills are the result names run_audit.py schedules.
CHECKS = (
    ("robots-txt", "robots.txt allows crawling", ("crawlability",),
     ("robots-block", "robots-unreachable"), _robots, True),
    ("ai-crawler-access", "AI and search crawlers may fetch the site", ("ai_crawler_access",),
     ("ai-crawler-blocked", "ai-crawler-section-blocked", "ai-crawler-unchecked"), _ai_crawlers, True),
    ("sitemap", "An XML sitemap is available", ("performance",),
     ("sitemap-unavailable",), _sitemap, True),
    ("llms-txt", "llms.txt is present and well formed", ("llms_txt",),
     ("no-llms-txt", "llms-txt-invalid", "llms-txt-broken-links", "llms-txt-unchecked"), _llms_txt, True),
    ("https", "Pages are served over HTTPS", ("metadata", "directives"),
     ("http-transport", "tls-health"), _https, False),
    ("http-status", "Fetched pages load without HTTP errors", ("crawlability",),
     ("broken-pages",), _no_http_errors, False),
    ("titles", "Every page has a title", ("metadata",),
     ("missing-title",), _titles, False),
    ("meta-descriptions", "Every page has a meta description", ("metadata",),
     ("missing-description",), _descriptions, False),
    ("language", "Every page declares its language", ("metadata",),
     ("missing-language",), _language, False),
    ("canonical", "Every page declares a canonical URL", ("metadata",),
     ("missing-canonical", "invalid-canonical", "cross-origin-canonical"), _canonical, False),
    ("indexable", "Pages are open to indexing and snippets", ("directives",),
     ("noindex", "nosnippet", "snippet-suppression"), _indexable, False),
    ("structured-data", "Structured data parses cleanly", ("machine_readability",),
     ("no-jsonld", "malformed-jsonld"), _structured_data, False),
    ("raw-html", "Content is in the raw HTML", ("rendering", "engagement"),
     ("render-gap", "render-gap-unconfirmed", "hash-routing"), _raw_html, False),
    ("h1", "Every page has an H1 heading", ("engagement",),
     ("h1", "no-headings", "page-orientation", "homepage-orientation"), _h1, False),
    ("viewport", "Mobile viewport is declared and zoom is allowed", ("engagement",),
     ("viewport", "zoom"), _viewport, False),
    ("image-alt", "Images carry alt attributes", ("engagement", "image_context", "media_text"),
     ("missing-alt", "image-context-missing", "alt-text-quality"), _image_alt, False),
    ("internal-links", "Every page links onward", ("site_graph", "engagement"),
     ("dead-ends", "no-internal-navigation"), _internal_links, False),
    ("offer-dates", "Offers shown are still current", ("offer_expiry",),
     ("expired-offer",), _offer_dates, False),
    ("fact-consistency", "Structured data agrees with the visible text", ("fact_consistency",),
     ("fact-markup-mismatch", "fact-inconsistent-across-pages"), _facts_match, False),
)


def reported_check_ids(items):
    """Every check ID that a finding or recommendation carries."""
    ids = set()
    for item in items:
        if isinstance(item, dict):
            if item.get("check_id"):
                ids.add(item["check_id"])
            ids.update(item.get("check_ids") or ())
    return ids


def whats_working(artifacts, results, findings, recommendations, pages_analyzed):
    """[{id, check, title, check_ids, evidence, pages_checked}] for the checks
    that ran and passed, in a fixed order. results maps a skill result name
    (as scheduled in run_audit.py) to its result."""
    flagged = reported_check_ids(list(findings) + list(recommendations))
    ctx = {"artifacts": artifacts, "results": results, "pages": eligible_pages(artifacts) if pages_analyzed else []}
    out = []
    for key, title, skills, check_ids, test, site_level in CHECKS:
        if not pages_analyzed and not site_level:
            continue
        if any((results.get(name) or {}).get("status") != "success" for name in skills):
            continue
        if flagged & set(check_ids):
            continue
        try:
            passed = test(ctx)
        except Exception:
            # A check that cannot be evaluated is never reported as passed.
            passed = None
        if not passed:
            continue
        evidence, pages_checked = passed
        out.append({"id": f"W-{len(out) + 1:03d}", "check": key, "title": title,
                    "check_ids": sorted(check_ids), "evidence": evidence, "pages_checked": pages_checked})
    return out
