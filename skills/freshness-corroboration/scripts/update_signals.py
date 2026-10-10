"""update_signals.py -- page update dates declared outside the page text.

Two sources, both already collected during acquisition, so this module makes no
requests:
  - sitemap <lastmod> (W3C Datetime) for each crawled URL the sitemap lists.
  - the HTTP Last-Modified response header of each crawled page.

Neither source is trusted blindly:
  - a sitemap whose lastmod values are nearly all the same date is treated as
    generated at build time, not as a record of content changes, and is not used
    for freshness (it is reported by sitemap_lastmod_quality instead);
  - a Last-Modified value within a few minutes of the response Date header (or of
    the audit run, when Date is missing) is a timestamp generated per request by a
    dynamic page, not a content date, and is ignored;
  - unparseable values and values in the future are ignored and counted;
  - a lastmod written as "2023-07-25 15:19:07" (a space instead of "T") is not
    W3C Datetime, so it is reported as nonstandard, but its date is still used:
    the intended day is unambiguous.

Each crawled page contributes at most one claim: its most recent trusted update
date. The claim carries a category from the page type, so a pricing page not
updated in years is weighed as a commercial fact and a blog post as editorial.
"""
import re
from collections import Counter
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# W3C Datetime, the format the sitemap protocol requires for <lastmod>:
# YYYY, YYYY-MM, YYYY-MM-DD, or a full date plus hh:mm[:ss[.s]] and a zone.
_W3C_RE = re.compile(
    r"(\d{4})(?:-(\d{2})(?:-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?)?)?)?")

# Page type (set during acquisition) -> category of the page's update date. Unlike
# a date mentioned in text, an update date describes the page itself, so no page
# type is "historical": a home page untouched for years is an operational concern.
_UPDATE_CATEGORY_BY_PAGE_TYPE = {
    "product": "commercial",
    "service": "commercial",
    "software": "commercial",
    "contact": "contact",
    "legal": "legal",
    "article": "editorial",
    "about": "editorial",
}

# A sitemap is treated as stamped at build time when at least this share of at
# least _UNIFORM_MIN_ENTRIES valid lastmod values fall on one date.
_UNIFORM_MIN_ENTRIES = 5
_UNIFORM_SHARE = 0.8
# Last-Modified this close to the response time means the page was generated on
# request. The larger tolerance applies when the server sent no Date header.
_GENERATED_TOLERANCE_S = 120
_GENERATED_TOLERANCE_NO_DATE_S = 900


def parse_w3c_date(value):
    """Return the calendar date of a W3C Datetime string, or None."""
    if not isinstance(value, str):
        return None
    match = _W3C_RE.fullmatch(value.strip())
    if not match:
        return None
    year, month, day, hour, minute, second = match.groups()
    if hour is not None and (int(hour) > 23 or int(minute) > 59 or (second is not None and int(second) > 59)):
        return None
    try:
        return date(int(year), int(month or 1), int(day or 1))
    except ValueError:
        return None


def parse_http_date(value):
    """Return an aware UTC datetime for an HTTP date header value, or None."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = parsedate_to_datetime(value.strip())
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _header(headers, name):
    """Case-insensitive header lookup; servers send any capitalization."""
    if not isinstance(headers, Mapping):
        return None
    wanted = name.lower()
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == wanted:
            return value if isinstance(value, str) else None
    return None


def parse_lastmod(value):
    """(date, standard) for a sitemap lastmod value: strict W3C Datetime first,
    then the common "YYYY-MM-DD hh:mm[:ss]" form, which is accepted as a date but
    marked nonstandard. (None, False) when neither parses."""
    parsed = parse_w3c_date(value)
    if parsed is not None:
        return parsed, True
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}.*", value.strip()):
        parsed = parse_w3c_date(value.strip().replace(" ", "T", 1))
        if parsed is not None:
            return parsed, False
    return None, False


def sitemap_lastmod_quality(sitemap_data, today=None):
    """Judge the sitemap's lastmod values as a whole.

    Returns a dict: url_entries, with_lastmod, valid (url -> date), invalid
    (list of {url, value, issue}; issue is unparseable, future or nonstandard,
    and nonstandard values are also in valid), uniform (None or {date, count,
    of}) and trusted (whether valid values may be used as update dates)."""
    today = today or datetime.now(timezone.utc).date()
    raw = sitemap_data.get("lastmod") if isinstance(sitemap_data, Mapping) else None
    raw = raw if isinstance(raw, Mapping) else {}
    valid, invalid = {}, []
    for url, value in raw.items():
        parsed, standard = parse_lastmod(value)
        if parsed is None:
            invalid.append({"url": url, "value": str(value)[:64], "issue": "unparseable"})
        elif parsed > today + timedelta(days=1):
            invalid.append({"url": url, "value": str(value)[:64], "issue": "future"})
        else:
            valid[url] = parsed
            if not standard:
                invalid.append({"url": url, "value": str(value)[:64], "issue": "nonstandard"})
    uniform = None
    if len(valid) >= _UNIFORM_MIN_ENTRIES:
        top, count = Counter(valid.values()).most_common(1)[0]
        if count / len(valid) >= _UNIFORM_SHARE:
            uniform = {"date": top.isoformat(), "count": count, "of": len(valid)}
    entries = sitemap_data.get("url_entries", 0) if isinstance(sitemap_data, Mapping) else 0
    return {"url_entries": entries if isinstance(entries, int) else 0, "with_lastmod": len(raw),
            "valid": valid, "invalid": invalid, "uniform": uniform, "trusted": uniform is None}


def _last_modified(page, now):
    """(status, date, raw) for one page's Last-Modified header."""
    raw = _header(page.response_headers, "Last-Modified")
    if raw is None:
        return "absent", None, None
    modified = parse_http_date(raw)
    if modified is None:
        return "unparseable", None, raw
    served = parse_http_date(_header(page.response_headers, "Date"))
    reference, tolerance = (served, _GENERATED_TOLERANCE_S) if served else (now, _GENERATED_TOLERANCE_NO_DATE_S)
    if modified > reference + timedelta(days=1):
        return "future", None, raw
    if abs((reference - modified).total_seconds()) <= tolerance:
        return "generated_per_request", None, raw
    return "ok", modified.date(), raw


def page_update_claims(pages, sitemap_data, now=None):
    """Return (claims, metrics, quality). One claim per successfully fetched page:
    the most recent trusted update date from sitemap lastmod or Last-Modified.
    `quality` is the sitemap_lastmod_quality result, reused for its finding."""
    now = now or datetime.now(timezone.utc)
    quality = sitemap_lastmod_quality(sitemap_data, now.date())
    lastmod = quality["valid"] if quality["trusted"] else {}
    header_status = Counter()
    claims, seen = [], set()
    for page in pages:
        if not (page.status_code and 200 <= page.status_code < 300) or page.url in seen:
            continue
        seen.add(page.url)
        signals = []
        for key in dict.fromkeys((page.url, page.final_url or page.url)):
            if key in lastmod:
                signals.append((lastmod[key], "sitemap lastmod", lastmod[key].isoformat()))
                break
        status, modified, raw = _last_modified(page, now)
        header_status[status] += 1
        if modified is not None:
            signals.append((modified, "HTTP Last-Modified", raw))
        if not signals:
            continue
        latest, predicate, shown = max(signals, key=lambda s: s[0])
        claims.append({"source": page.url, "subject": "page", "predicate": predicate,
                       "value": shown, "iso_date": latest.isoformat(), "type": "date",
                       "category": _UPDATE_CATEGORY_BY_PAGE_TYPE.get(page.page_type, "operational"),
                       "origin": "update_signal", "importance": 0.5, "confidence": 0.7})
    metrics = {
        "sitemap_lastmod_entries": quality["with_lastmod"],
        "sitemap_lastmod_trusted": quality["trusted"] and bool(quality["valid"]),
        "sitemap_lastmod_invalid": len(quality["invalid"]),
        "sitemap_lastmod_uniform": quality["uniform"],
        "update_dates_from_sitemap_lastmod": sum(c["predicate"] == "sitemap lastmod" for c in claims),
        "update_dates_from_last_modified": sum(c["predicate"] == "HTTP Last-Modified" for c in claims),
        "last_modified_header": dict(header_status),
        "pages_with_update_date": len(claims),
    }
    return claims, metrics, quality
