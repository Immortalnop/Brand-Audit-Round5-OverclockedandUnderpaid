"""extract_claims.py -- heuristic, deterministic claim extraction.

Each claim is tagged with a `category` -- operational / commercial / contact /
editorial / historical / legal -- in addition to its shape-based `type`
(date/price/contact/structured). The category matters downstream (assess_freshness)
because "this date is old" means something completely different depending on what
kind of fact it is attached to: an old copyright year (legal) is normal and not a
defect, an old founding-story date (historical) is *supposed* to be old, an old
"last verified" operational date is a real freshness problem, and a stale price or
expired offer (commercial) is the highest-stakes case. Category is inferred from
the page it was found on (page_type, set during acquisition) and, for structured
facts, from which JSON-LD key produced it -- never from an analysis conclusion, so
it stays a plain classification of what the fact IS, not a verdict on it.
"""
import re
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit
from structured_data import iter_nodes, types_of
from models import intermediate_artifact
from schema_values import date_value_state, value_excerpt

# Strict ISO 8601 calendar date with an optional time and offset, the form
# schema.org expects for datePublished and dateModified. Parsed by hand so the
# behavior is identical on every supported Python version.
_ISO_DATE_RE = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?")
_COMMERCIAL_TYPES = {"Product", "IndividualProduct", "Offer", "AggregateOffer", "Service",
                     "SoftwareApplication", "MobileApplication", "WebApplication"}
_STRUCTURED_DATE_KEYS = ("datePublished", "dateModified")

_DATE_RE = re.compile(
    r"\b(19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b"
    r"|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+(19|20)\d{2}\b"
)
_PRICE_RE = re.compile(r"[$\u20ac\u00a3\u20b9]\s?\d[\d,]*(\.\d{2})?")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+\d|\(\d|\d)[\d\- \t().]{5,}\d(?!\w)")
_PHONE_LABEL = re.compile(r'\b(?:phone|telephone|tel|call|fax|mobile|whatsapp|contact)\s*:?\s*$',re.I)
_NON_PHONE_LABEL = re.compile(r'\b(?:ABN|VAT|ISBN|SKU|tax(?:\s+ID)?|registration(?:\s+number)?)\s*:?\s*$',re.I)


def phone_mentions(text):
    """Conservative visible-text numbers; explicit JSON-LD telephone is separate.

    Dates must never become high-ranked contact claims. Mask them before the
    greedy number scan so adjacent date strings cannot become one number.
    Plain digit/space identifiers require an explicit phone/contact label.
    """
    masked=list(text)
    for match in _DATE_RE.finditer(text):
        masked[match.start():match.end()]='X'*(match.end()-match.start())
    for match in _PHONE_RE.finditer(''.join(masked)):
        value=text[match.start():match.end()].strip()
        # A postal code preceding a parenthesized area code is not part of it.
        value=re.sub(r'^\d{5}(?:-\d{4})?\s+(?=\()', '',value)
        digits=re.sub(r'\D','',value)
        before=text[max(0,match.start()-40):match.start()]
        if not 7<=len(digits)<=15 or _NON_PHONE_LABEL.search(before):continue
        # Legal section ranges such as 1798.83-1798.84 are not phone numbers.
        if '.' in value and not re.fullmatch(r'(?:\+\d{1,3}[ .-])?\(?\d{1,4}\)?[ .-]\d{2,4}[ .-]\d{3,4}',value):continue
        if not any(c in value for c in '+()-') and not _PHONE_LABEL.search(before):continue
        yield value

# page_type (acquisition-owned) -> the category a bare date mention on that page
# most plausibly belongs to. A page type not listed here says nothing about its
# dates, so a date there is "operational" only when an operational cue sits in
# the same sentence (_OPERATIONAL_CUE); otherwise it is "unclassified", which is
# counted but never reported as stale: an old date on an essay, a news item or an
# event recap is not evidence that a current fact is out of date.
_DATE_CATEGORY_BY_PAGE_TYPE = {
    "legal": "legal",
    "article": "editorial",
    "listing": "editorial",  # a blog or news index: its dates are post dates
    "product": "commercial",
    "about": "historical",
    "home": "historical",
}
_DEFAULT_DATE_CATEGORY = "unclassified"
# Words that make a date part of a current operational fact: opening hours,
# validity and expiry, "as of" and "last updated" statements, prices and fees,
# schedules and deadlines.
_OPERATIONAL_CUE = re.compile(
    r"\b(?:opening hours|hours of operation|open(?:ing)?\s+(?:from|on|until|daily)|closed\s+(?:on|from|until)"
    r"|valid\s+(?:until|through|thru|till|from)|expir(?:es|y|ed|ation)|offer ends|sale ends|deadline"
    r"|as of|last\s+(?:updated|reviewed|verified|checked|revised)|updated\s+(?:on|:)"
    r"|effective\s+(?:from|date|as of|on)|prices?|pricing|fees?|tariffs?|timetable|schedule[sd]?"
    r"|apply by|register by|registration closes)\b", re.I)
# Path segments of archive-style sections, whose dates are history by design.
_ARCHIVE_PATH = re.compile(r"/(?:archives?|history|essays?|past[-_][\w-]+|(?:19|20)\d{2})(?:/|$)", re.I)
_SENTENCE_BREAK = re.compile(r"[.!?]\s|\n")


def _sentence_around(text, start, end):
    """The sentence holding text[start:end], bounded to 200 characters each side."""
    left = text[max(0, start - 200):start]
    breaks = list(_SENTENCE_BREAK.finditer(left))
    if breaks:
        left = left[breaks[-1].end():]
    right = text[end:end + 200]
    stop = _SENTENCE_BREAK.search(right)
    if stop:
        right = right[:stop.start() + 1]
    return left + text[start:end] + right


def _date_category(page, text, match):
    """Category of a date mention in visible text: from the page type when it
    implies one, else from an archive path or an operational cue in the sentence."""
    # The nearby label outranks the URL genre: a book's publication date is
    # immutable history, even though the book is sold on a product page.
    before = text[max(0,match.start()-100):match.start()]
    if page.page_type == 'product' and re.search(r'\b(?:published|publication date|release date|first published)\s*:?\s*$', before, re.I):
        return 'historical'
    category = _DATE_CATEGORY_BY_PAGE_TYPE.get(page.page_type)
    if category:
        return category
    try:
        path = urlsplit(page.url).path
    except (ValueError, AttributeError):
        path = ""
    if _ARCHIVE_PATH.search(path or ""):
        return "historical"
    if _OPERATIONAL_CUE.search(_sentence_around(text, match.start(), match.end())):
        return "operational"
    return _DEFAULT_DATE_CATEGORY

# JSON-LD key -> category, for structured facts (independent of page_type, since a
# priceRange or telephone means the same thing regardless of what page it's on).
_STRUCTURED_KEY_CATEGORY = {
    "priceRange": "commercial",
    "telephone": "contact",
    "address": "contact",
    "sameAs": "editorial",
    "name": "editorial",
}


def _parse_iso_date(value):
    if not isinstance(value, str):
        return None
    match = _ISO_DATE_RE.fullmatch(value.strip())
    if not match or date_value_state(value.strip()) != 'valid':
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def structured_date_claims(pages, today=None):
    """Explicit publication and update dates declared in JSON-LD.

    Returns (claims, issues). Each JSON-LD node contributes at most one claim: its
    most recent valid date, so an old datePublished followed by a recent
    dateModified reads as recently updated, never as stale. `issues` lists values
    that are not ISO 8601 dates, dates in the future, and a dateModified earlier
    than the datePublished of the same node.

    These claims are deliberately not added to the claims artifact: the
    important-facts ranking keeps only the top-ranked claims for corroboration,
    and site-wide date claims would displace prices and contact facts there.
    assess_freshness reads them directly instead."""
    today = today or datetime.now(timezone.utc).date()
    claims, issues = [], []
    for page in pages:
        for node in iter_nodes(page.jsonld_blocks):
            if not isinstance(node, Mapping):
                continue
            types = types_of(node)
            subject = sorted(types)[0] if types else "entity"
            parsed = {}
            for key in _STRUCTURED_DATE_KEYS:
                if key not in node:
                    continue
                values = node[key] if isinstance(node[key], (list, tuple)) else [node[key]]
                for raw in values[:3]:
                    shown = value_excerpt(raw).strip()[:80]
                    parsed_date = _parse_iso_date(raw)
                    if parsed_date is None:
                        issues.append({"source": page.url, "subject": subject, "field": key,
                                       "value": shown, "issue": "invalid_calendar" if date_value_state(raw) == 'invalid' else "unsupported_format"})
                    elif parsed_date > today + timedelta(days=1):
                        issues.append({"source": page.url, "subject": subject, "field": key,
                                       "value": shown, "issue": "future"})
                    elif key not in parsed or parsed_date > parsed[key][0]:
                        parsed[key] = (parsed_date, shown)
            if not parsed:
                continue
            if "datePublished" in parsed and "dateModified" in parsed \
                    and parsed["dateModified"][0] < parsed["datePublished"][0]:
                issues.append({"source": page.url, "subject": subject, "field": "dateModified",
                               "value": parsed["dateModified"][1],
                               "issue": "modified_before_published",
                               "published": parsed["datePublished"][1]})
            # Latest date wins; on a tie the declared modification date is reported.
            key = max(parsed, key=lambda k: (parsed[k][0], k == "dateModified"))
            latest, shown = parsed[key]
            if key == 'datePublished' and types & (_COMMERCIAL_TYPES | {'Book'}):
                category = 'historical'
            elif types & _COMMERCIAL_TYPES:
                category = "commercial"
            elif page.page_type == "legal":
                category = "legal"
            else:
                category = "editorial"
            claims.append({"source": page.url, "subject": subject, "predicate": key,
                           "value": shown, "iso_date": latest.isoformat(), "type": "date",
                           "category": category, "origin": "jsonld",
                           "importance": 0.5, "confidence": 0.9})
    return claims, issues


def extract_claims(artifacts, deadline):
    claims = []
    for page in artifacts.pages:
        text = page.visible_text or ""
        for m in _DATE_RE.finditer(text):
            claims.append({"source": page.url, "subject": "date_mention", "predicate": "mentions_date",
                           "value": m.group(0), "type": "date", "category": _date_category(page, text, m),
                           "importance": 0.5, "confidence": 0.6})
        for m in _PRICE_RE.finditer(text):
            claims.append({"source": page.url, "subject": "price_mention", "predicate": "mentions_price",
                           "value": m.group(0), "type": "price", "category": "commercial",
                           "importance": 0.6, "confidence": 0.6})
        for phone in phone_mentions(text):
            claims.append({"source": page.url, "subject": "contact", "predicate": "phone_number",
                           "value": phone, "type": "contact", "category": "contact",
                           "importance": 0.7, "confidence": 0.5})
        for block in iter_nodes(page.jsonld_blocks):
            # jsonld_blocks on a real (acquired) PageArtifact are frozen via
            # freeze_value() into MappingProxyType, not plain dict
            # -- Mapping catches both that and plain-dict test fixtures.
            if isinstance(block, Mapping):
                keys=["name", "address", "telephone", "sameAs", "priceRange"]
                if types_of(block) & (_COMMERCIAL_TYPES | {'Organization','Corporation','Brand','Book'}):
                    keys.append('description')
                for key in keys:
                    if key in block:
                        subject=' / '.join(sorted(types_of(block))) or 'entity'
                        if key=='description' and not isinstance(block[key],str):continue
                        claims.append({"source": page.url, "subject": subject,
                                        "predicate": key, "value": block[key], "type": "structured",
                                        "category": _STRUCTURED_KEY_CATEGORY.get(key, "operational"),
                                        "importance": 0.8, "confidence": 0.9})
    return intermediate_artifact("claims", data={"claims": claims})
