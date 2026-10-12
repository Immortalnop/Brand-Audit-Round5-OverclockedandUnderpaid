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
from structured_data import iter_nodes
from models import intermediate_artifact
from dates import extract_visible_dates
from check_helpers import is_challenged

_DATE_RE = re.compile(
    r"\b(19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b"
    r"|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+(19|20)\d{2}\b"
)
_PRICE_RE = re.compile(r"(?:[$\u20ac\u00a3\u20b9]|\bRs\.?|\bINR|\bUSD)\s?\d[\d,]*(\.\d{2})?")
_PHONE_RE = re.compile(r"\+?\d[\d\-\s\(\)]{7,}\d")

# page_type (acquisition-owned) -> the category a bare date mention on that page
# most plausibly belongs to. Not exhaustive by design -- anything not listed here
# defaults to "operational", the safest middle ground (neither dismissed like
# "historical" nor over-weighted like "commercial").
_DATE_CATEGORY_BY_PAGE_TYPE = {
    "legal": "legal",
    "article": "editorial",
    "product": "commercial",
    "about": "historical",
    "home": "historical",
}

# JSON-LD key -> category, for structured facts (independent of page_type, since a
# priceRange or telephone means the same thing regardless of what page it's on).
_STRUCTURED_KEY_CATEGORY = {
    "priceRange": "commercial",
    "telephone": "contact",
    "address": "contact",
    "sameAs": "editorial",
    "name": "editorial",
}


def extract_claims(artifacts, deadline):
    claims = []
    for page in artifacts.pages:
        if is_challenged(page):
            continue  # a bot-challenge interstitial carries no site facts (A1)
        text = page.visible_text
        # A9: a date's category comes from the words around it ("last updated",
        # "valid until", "founded" ...), not from the page type; page type is only a
        # fallback for dates with no telling context.
        fallback = _DATE_CATEGORY_BY_PAGE_TYPE.get(page.page_type, "unclassified")
        for d in extract_visible_dates(text):
            category = d["context"] if d["context"] != "unclassified" else fallback
            claims.append({"source": page.url, "subject": "date_mention", "predicate": "mentions_date",
                           "value": d["raw"], "iso": d["date"].isoformat(), "context": d["context"],
                           "type": "date", "category": category, "importance": 0.5, "confidence": 0.6})
        for m in _PRICE_RE.finditer(text):
            claims.append({"source": page.url, "subject": "price_mention", "predicate": "mentions_price",
                           "value": m.group(0), "type": "price", "category": "commercial",
                           "importance": 0.6, "confidence": 0.6})
        for m in _PHONE_RE.finditer(text):
            claims.append({"source": page.url, "subject": "contact", "predicate": "phone_number",
                           "value": m.group(0), "type": "contact", "category": "contact",
                           "importance": 0.7, "confidence": 0.5})
        for block in iter_nodes(page.jsonld_blocks):
            # jsonld_blocks on a real (acquired) PageArtifact are frozen via
            # freeze_value() into MappingProxyType, not plain dict
            # -- Mapping catches both that and plain-dict test fixtures.
            if isinstance(block, Mapping):
                for key in ("name", "address", "telephone", "sameAs", "priceRange"):
                    if key in block:
                        claims.append({"source": page.url, "subject": block.get("@type", "entity"),
                                        "predicate": key, "value": block[key], "type": "structured",
                                        "category": _STRUCTURED_KEY_CATEGORY.get(key, "operational"),
                                        "importance": 0.8, "confidence": 0.9})
    return intermediate_artifact("claims", data={"claims": claims})
