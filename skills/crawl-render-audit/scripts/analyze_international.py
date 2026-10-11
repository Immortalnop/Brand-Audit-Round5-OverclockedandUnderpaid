"""analyze_international.py -- hreflang and multi-language sites.

Assistants and search engines answer in the asker's language. On a site published
in several languages, hreflang annotations tell them which URL is which language
version; without valid, reciprocal annotations they may cite or link the wrong
version. This check reads the acquisition snapshot only (no requests):

  - hreflang-invalid (defect): annotations that search engines ignore or that
    contradict each other: a malformed code (en_US, en-UK, a country used as a
    language such as jp), a relative URL, one code pointing at two URLs, a page
    that does not list itself, a crawled alternate that does not link back, an
    alternate that answered 404 or 410, or a page whose own code disagrees with
    its html lang.
  - hreflang-missing (suggestion): crawled pages declare two or more languages
    (html lang) but no page carries an hreflang annotation.

Annotations come from <link rel="alternate" hreflang> in the HTML, the HTTP Link
header and xhtml:link entries in the sitemap. Codes are judged by shape and by a
short list of common mistakes, never by a full registry, so a rare but valid code
is never reported. Alternates that were not crawled are counted as unverified.
"""
import re
from urllib.parse import urljoin, urlsplit

from check_helpers import eligible_pages
from models import make_finding, skill_result

# Country codes often used by mistake where a language code belongs.
_COUNTRY_AS_LANGUAGE = {"jp": "ja", "cn": "zh", "dk": "da", "gr": "el", "cz": "cs", "kr": "ko",
                        "vn": "vi", "us": "en", "gb": "en"}
_SHAPE = re.compile(r"[a-z]{2,3}(?:-[a-z]{4})?(?:-(?:[a-z]{2}|[0-9]{3}))?", re.I)
_LINK_PART = re.compile(r"<([^>]*)>\s*((?:;[^,<]*)*)")


def code_problem(code):
    """Why an hreflang value is unusable, or None when it is acceptable."""
    value = (code or "").strip()
    if value.lower() == "x-default":
        return None
    if not value:
        return "the hreflang value is empty"
    if "_" in value:
        return f"'{value}' uses an underscore; hreflang codes use a hyphen, such as en-US"
    if not _SHAPE.fullmatch(value):
        return f"'{value}' is not a language code with an optional script and region, such as en or en-GB"
    parts = value.lower().split("-")
    if parts[0] in _COUNTRY_AS_LANGUAGE:
        return (f"'{parts[0]}' is a country code, not a language code "
                f"(did you mean '{_COUNTRY_AS_LANGUAGE[parts[0]]}'?)")
    region = parts[-1] if len(parts) > 1 and len(parts[-1]) != 4 else None
    if region == "uk":
        return f"'{value}' uses UK; the region code for the United Kingdom is GB"
    if region and region.isdigit():
        return f"'{value}' uses a numeric region, which Google does not support in hreflang"
    return None


def _key(url):
    """Comparison key that ignores scheme, a leading www. and a trailing slash."""
    try:
        p = urlsplit(url)
    except ValueError:
        return None
    host = (p.hostname or "").lower()
    if not host:
        return None
    host = host[4:] if host.startswith("www.") else host
    path = (p.path or "/").rstrip("/") or "/"
    return host, path, p.query


def _header(page, name):
    for k, v in (page.response_headers or {}).items():
        if k.lower() == name:
            return v
    return ""


def _annotations(page, sitemap_alts):
    """[(code, raw_href, source)] from HTML, the Link header and the sitemap."""
    out = [(a.get("hreflang", ""), a.get("href", ""), "html")
           for a in (page.features or {}).get("hreflang", ())]
    for target, params in _LINK_PART.findall(_header(page, "link")):
        if re.search(r'rel\s*=\s*"?alternate"?', params, re.I):
            m = re.search(r'hreflang\s*=\s*"?([^";,\s]+)"?', params, re.I)
            if m:
                out.append((m.group(1), target.strip(), "http_header"))
    for url in (page.url, page.final_url):
        for a in sitemap_alts.get(url, ()) if url else ():
            out.append((a.get("hreflang", ""), a.get("href", ""), "sitemap"))
    return out


def _page_problems(page, annotations, by_key, all_annotations):
    base = page.final_url or page.url
    self_keys = {k for k in (_key(page.url), _key(page.final_url), _key(page.canonical_url or "")) if k}
    problems, severe = [], False
    targets, self_codes, unverified = {}, [], 0
    for code, raw, source in annotations:
        bad = code_problem(code)
        if bad:
            problems.append(bad + f" ({source})")
            severe = True
        if not re.match(r"https?://", raw or "", re.I):
            problems.append(f"'{raw or '(empty)'}' for {code} is not a full URL; hreflang needs absolute URLs ({source})")
        try:
            target = urljoin(base, raw or "")
        except ValueError:
            continue
        tkey = _key(target)
        if tkey is None:
            continue
        code_l = (code or "").strip().lower()
        if code_l in targets and targets[code_l] != tkey:
            problems.append(f"'{code}' points at two different URLs")
            severe = True
        targets.setdefault(code_l, tkey)
        if tkey in self_keys:
            self_codes.append(code_l)
            continue
        other = by_key.get(tkey)
        if other is None or (other.status_code == 200 and other.url not in all_annotations):
            unverified += 1
        elif other.status_code in (404, 410):
            problems.append(f"the {code} alternate {target} answered HTTP {other.status_code}")
            severe = True
        elif other.status_code == 200:
            back = {_key(urljoin(other.final_url or other.url, r or "")) for _, r, _ in all_annotations.get(other.url, ())}
            if not back & self_keys:
                problems.append(f"the {code} alternate {target} does not link back to this page")
                severe = True
    if annotations and not self_codes:
        problems.append("the page does not list itself among its hreflang alternates")
    lang = ((page.features or {}).get("lang") or "").strip().lower().split("-")[0]
    named = [c.split("-")[0] for c in self_codes if c != "x-default"]
    if lang and named and lang not in named:
        problems.append(f"its own hreflang code ({', '.join(sorted(set(named)))}) differs from html lang '{lang}'")
    return list(dict.fromkeys(problems)), severe, unverified


def analyze_international(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["hreflang checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    sitemap_alts = (artifacts.sitemap_data or {}).get("hreflang") or {}
    by_key = {}
    for p in artifacts.pages:
        for u in (p.url, p.final_url):
            k = _key(u) if u else None
            if k:
                by_key.setdefault(k, p)
    annotations = {p.url: _annotations(p, sitemap_alts) for p in pages}
    findings, flagged, unverified_total, any_severe = [], [], 0, False
    for p in pages:
        if not annotations[p.url]:
            continue
        problems, severe, unverified = _page_problems(p, annotations[p.url], by_key, annotations)
        unverified_total += unverified
        if problems:
            flagged.append((p, problems))
            any_severe = any_severe or severe
    if flagged:
        severity = "medium" if any_severe else "low"
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity=severity,
            status="confirmed", confidence=0.85,
            title="hreflang annotations are invalid or not reciprocal",
            root_cause="Search engines ignore hreflang codes that are malformed, relative or not confirmed by a "
                       "return link, so assistants and search results may show the wrong language version",
            affected_pages=[p.url for p, _ in flagged],
            evidence=[{"type": "hreflang", "description": "; ".join(problems[:5]), "urls": [p.url]}
                      for p, problems in flagged[:10]],
            suggested_action={
                "summary": "Fix the hreflang annotations so every language version lists all versions, itself included",
                "steps": ["Use codes of the form language or language-REGION, for example en, en-GB, pt-BR",
                          "Use absolute URLs in every hreflang annotation",
                          "List every language version, including the page itself, on each version",
                          "Make each alternate page link back with the same set of annotations"],
                "priority": severity, "effort": "medium",
                "expected_benefit": "Each language version is served and cited to speakers of that language",
                "verification": "Re-run the audit and confirm no hreflang problem is listed"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_international.py",
                        "rule_id": "hreflang-invalid"},
        ))
    langs = {}
    for p in pages:
        lang = ((p.features or {}).get("lang") or "").strip().lower().split("-")[0]
        if re.fullmatch(r"[a-z]{2,3}", lang):
            langs.setdefault(lang, []).append(p.url)
    has_any = any(annotations.values())
    if len(langs) >= 2 and not has_any:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.6,
            title="Pages in several languages carry no hreflang annotations",
            root_cause="Without hreflang, search engines and assistants must guess which language version to "
                       "show, and may cite a version the reader cannot read",
            affected_pages=[u for urls in langs.values() for u in urls[:3]],
            evidence=[{"type": "hreflang",
                       "description": f"html lang '{lang}' on {len(urls)} crawled page(s); no hreflang in HTML, "
                                      "Link headers or the sitemap",
                       "urls": urls[:5]} for lang, urls in sorted(langs.items())[:6]],
            suggested_action={
                "summary": "Add hreflang annotations that link each page to its other language versions",
                "steps": ["Add <link rel=\"alternate\" hreflang=\"...\" href=\"...\"> for every language version "
                          "of each page, including the page itself",
                          "Add an x-default alternate for the language picker or default page"],
                "priority": "low", "effort": "medium",
                "expected_benefit": "Readers are sent to and quoted from the version in their language",
                "verification": "Re-run the audit and confirm the annotations are found and valid"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_international.py",
                        "rule_id": "hreflang-missing"},
        ))
    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"hreflang_pages": sum(1 for v in annotations.values() if v),
                 "hreflang_annotations": sum(len(v) for v in annotations.values()),
                 "hreflang_sitemap_entries": len(sitemap_alts),
                 "hreflang_alternates_unverified": unverified_total,
                 "html_languages": sorted(langs)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
