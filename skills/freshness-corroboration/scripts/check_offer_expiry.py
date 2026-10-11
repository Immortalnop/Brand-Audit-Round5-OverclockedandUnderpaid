"""check_offer_expiry.py -- offers whose stated end date has passed.

Two kinds of evidence, read from the acquisition snapshot with no request:
  - visible text: an offer word (offer, sale, deal, discount, coupon...) followed
    in the same sentence by a deadline in the present tense ("ends", "expires",
    "valid until", "available through") and a full date with a year;
  - structured data: an Offer's priceValidUntil or validThrough.
A deadline counts as expired only when it is more than a day before the audit
date, so time zones never make a current offer look expired. Past-tense wording
("ended", "expired") and dates without a year are never read as a live offer.
Editorial, listing and legal pages, archive paths and event pages are skipped:
an old deadline in a news story, a terms page or a past event's listing records
history, not a current offer.
"""
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit

from check_helpers import eligible_pages, page_share
from extract_claims import _ARCHIVE_PATH, _parse_iso_date, _sentence_around
from models import make_finding, skill_result
from structured_data import iter_nodes, types_of

_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
           "sept": 9, "oct": 10, "nov": 11, "dec": 12}
_MONTH_NAMES = {name: number for number, name in enumerate(
    ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
     "november", "december"), 1)}

_OFFER_WORD = (r"(?:offers?|sales?|deals?|promotions?|promos?|discounts?|coupons?|vouchers?|promo\s+codes?"
               r"|special\s+prices?|introductory\s+prices?|early[- ]bird)")
_DEADLINE = (r"(?:ends?|expires?|valid\s+(?:until|through|thru|till|to)|available\s+(?:until|through|thru|till)"
             r"|good\s+(?:until|through|thru|till)|runs\s+(?:until|through|thru|till)|lasts\s+until"
             r"|until|through|thru|till)")
# The offer word and its deadline sit in one sentence, at most 60 characters apart.
_CUE = re.compile(rf"\b{_OFFER_WORD}\b[^.!?\n]{{0,60}}?\b{_DEADLINE}\b", re.I)
_DATE = re.compile(
    r"\s*(?:on\s+|:\s*|-\s*)?(?:the\s+)?(?:(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+)?"
    r"(?:(?P<d1>\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<m1>[a-z]{3,9})\.?,?\s+(?P<y1>\d{4})"
    r"|(?P<m2>[a-z]{3,9})\.?\s+(?P<d2>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y2>\d{4})"
    r"|(?P<y3>\d{4})-(?P<mo3>\d{1,2})-(?P<d3>\d{1,2})"
    r"|(?P<a4>\d{1,2})[/.](?P<b4>\d{1,2})[/.](?P<y4>\d{4}))(?!\d)", re.I)
# Pages whose dates record history rather than a current offer.
_SKIPPED_PAGE_TYPES = frozenset({"article", "listing", "legal"})
_EVENT_TYPES = frozenset({"Event", "MusicEvent", "SportsEvent", "TheaterEvent", "BusinessEvent", "SaleEvent",
                          "EducationEvent", "ExhibitionEvent", "Festival", "FoodEvent", "SocialEvent"})
_OFFER_TYPES = frozenset({"Offer", "AggregateOffer"})
_MAX_EVIDENCE_PER_PAGE = 3


def _month(word):
    word = word.lower().rstrip(".")
    return _MONTH_NAMES.get(word) or _MONTHS.get(word)


def _valid(y, m, d):
    try:
        return date(int(y), int(m), int(d))
    except (TypeError, ValueError):
        return None


def parse_deadline(match):
    """The dates a _DATE match can mean: one for a written-out or ISO date, up
    to two for a numeric day/month or month/day date."""
    g = match.groupdict()
    if g["y1"]:
        return [d for d in [_valid(g["y1"], _month(g["m1"]), g["d1"])] if d] if _month(g["m1"]) else []
    if g["y2"]:
        return [d for d in [_valid(g["y2"], _month(g["m2"]), g["d2"])] if d] if _month(g["m2"]) else []
    if g["y3"]:
        return [d for d in [_valid(g["y3"], g["mo3"], g["d3"])] if d]
    if g["y4"]:
        options = {_valid(g["y4"], g["b4"], g["a4"]), _valid(g["y4"], g["a4"], g["b4"])}
        return sorted(d for d in options if d)
    return []


def text_deadlines(text):
    """[(sentence, [possible dates])] for every offer deadline in visible text."""
    out = []
    for cue in _CUE.finditer(text or ""):
        found = _DATE.match(text, cue.end())
        if not found:
            continue
        dates = parse_deadline(found)
        if dates:
            sentence = " ".join(_sentence_around(text, cue.start(), found.end()).split())
            out.append((sentence[:200], dates))
    return out


def markup_deadlines(page):
    """[(property, value, date)] for Offer priceValidUntil and validThrough."""
    out = []
    for node in iter_nodes(page.jsonld_blocks):
        if not types_of(node) & _OFFER_TYPES:
            continue
        for prop in ("priceValidUntil", "validThrough"):
            value = node.get(prop)
            parsed = _parse_iso_date(value)
            if parsed:
                out.append((prop, value.strip(), parsed))
    return out


def _in_scope(page):
    if page.page_type in _SKIPPED_PAGE_TYPES:
        return False
    try:
        path = urlsplit(page.url).path or ""
    except ValueError:
        path = ""
    if _ARCHIVE_PATH.search(path):
        return False
    return not any(types_of(n) & _EVENT_TYPES for n in iter_nodes(page.jsonld_blocks))


def check_offer_expiry(artifacts, deadline, today=None):
    if deadline.expired():
        return skill_result("freshness-corroboration", status="insufficient_evidence",
                            warnings=["Offer expiry check skipped: deadline reached."])
    today = today or datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=1)
    pages = [p for p in eligible_pages(artifacts) if _in_scope(p)]
    found = 0
    expired = {}
    for page in pages:
        items = []
        for sentence, dates in text_deadlines(page.visible_text):
            found += 1
            # An ambiguous numeric date counts only when every reading is past.
            if all(d < cutoff for d in dates):
                latest = max(dates)
                items.append({"type": "expired_offer_text",
                              "description": f'Visible text: "{sentence}" (deadline {latest.isoformat()}, '
                                             f"{(today - latest).days} days before the audit)",
                              "urls": [page.url]})
        for prop, value, parsed in markup_deadlines(page):
            found += 1
            if parsed < cutoff:
                items.append({"type": "expired_offer_markup",
                              "description": f"JSON-LD Offer {prop} is {value}, "
                                             f"{(today - parsed).days} days before the audit",
                              "urls": [page.url]})
        if items:
            expired[page.url] = items
    findings = []
    if expired:
        affected = [p for p in pages if p.url in expired]
        evidence = [item for p in affected for item in expired[p.url][:_MAX_EVIDENCE_PER_PAGE]][:20]
        findings.append(make_finding(
            category="freshness", finding_type="defect", severity="medium", status="confirmed", confidence=0.8,
            title="An offer whose end date has passed is still presented on " + page_share(affected, pages),
            root_cause="These pages still present an offer with a stated end date that has passed. An assistant "
                       "that quotes the page repeats an offer that no longer applies, and a visitor who acts on "
                       "it is turned away.",
            evidence=evidence, affected_pages=[p.url for p in affected],
            suggested_action={
                "summary": "Remove expired offers, or update their terms and end dates",
                "steps": ["Remove or replace each offer listed in the evidence",
                          "Update the matching Offer priceValidUntil or validThrough in the JSON-LD",
                          "Give future promotions an end date and a step that takes them down when it passes"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Assistants and visitors see only offers that are still valid",
                "verification": "Re-run the audit and confirm no past offer deadline is listed",
            },
            provenance={"skill": "freshness-corroboration", "script": "check_offer_expiry.py",
                        "rule_id": "expired-offer"},
        ))
    return skill_result(
        "freshness-corroboration", findings=findings,
        metrics={"offer_expiry_pages_scanned": len(pages), "offer_deadlines_found": found,
                 "expired_offer_pages": len(expired), "offer_expiry_reference_date": today.isoformat()},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
