"""schema_rules.py -- what each schema.org type needs to be useful.

Required properties are the ones consumers need to use the node at all (an Offer
with no price is not an offer); recommended properties carry freshness and
identity signals. The table is data so it can be reviewed and extended in one
place. Value validators are deliberately conservative: they only flag values that
are unambiguously malformed.
"""
import re
from datetime import date, datetime
from urllib.parse import urlsplit

RULES = {
    "Product": {"required": ("name",), "required_any": (("offers", "aggregateRating", "review"),),
                "recommended": ("image", "description", "brand", "sku", "offers")},
    "Offer": {"required_any": (("price", "priceSpecification", "lowPrice"),), "required": ("priceCurrency",),
              "recommended": ("availability", "url", "priceValidUntil")},
    "AggregateOffer": {"required": ("lowPrice", "priceCurrency"), "recommended": ("highPrice", "offerCount")},
    "Organization": {"required": ("name",), "required_any": (("url", "@id"),), "recommended": ("logo", "sameAs")},
    "LocalBusiness": {"required": ("name", "address"), "recommended": ("telephone", "openingHoursSpecification", "geo", "url")},
    # Google lists no required Article properties; dates are recommended. Their
    # absence is reported once by missing-article-dates (freshness), not here.
    "Article": {"required": ("headline",),
                "recommended": ("datePublished", "dateModified", "author", "image")},
    "FAQPage": {"required": ("mainEntity",), "recommended": ()},
    "WebSite": {"required": ("name",), "required_any": (("url", "@id"),), "recommended": ()},
    "BreadcrumbList": {"required": ("itemListElement",), "recommended": ()},
    "Event": {"required": ("name", "startDate"), "recommended": ("location", "endDate", "offers")},
}
ALIASES = {"BlogPosting": "Article", "NewsArticle": "Article", "TechArticle": "Article",
           "Store": "LocalBusiness", "Restaurant": "LocalBusiness", "OnlineStore": "Organization",
           "Corporation": "Organization", "EducationalOrganization": "Organization",
           "NGO": "Organization", "IndividualProduct": "Product", "ProductGroup": "Product"}
# Organization subtypes are validated as their parent: LocalBusiness subtypes need
# an address, every other Organization subtype a name and url.
from structured_data import LOCAL_BUSINESS_TYPES, ORGANIZATION_TYPES  # noqa: E402
for _t in LOCAL_BUSINESS_TYPES:
    ALIASES.setdefault(_t, "LocalBusiness")
for _t in ORGANIZATION_TYPES - LOCAL_BUSINESS_TYPES:
    ALIASES.setdefault(_t, "Organization")
# Properties that matter enough to keep in the core report when missing.
CORE_RECOMMENDED = {"dateModified", "sameAs", "offers", "availability"}

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ][\d:.]+(Z|[+-]\d{2}:?\d{2})?)?$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_PRICE = re.compile(r"^\d+(\.\d+)?$")


def rule_for(types):
    for t in types:
        t = ALIASES.get(t, t)
        if t in RULES:
            return t, RULES[t]
    return None, None


def _present(node, key):
    v = node.get(key)
    return v not in (None, "", [], (), {})


def missing(node, rule):
    req = [k for k in rule.get("required", ()) if not _present(node, k)]
    for alts in rule.get("required_any", ()):
        if not any(_present(node, k) for k in alts):
            req.append(" or ".join(alts))
    rec = [k for k in rule.get("recommended", ()) if not _present(node, k) and k not in req]
    return req, rec


def _absolute(v):
    try:
        p = urlsplit(str(v))
        return p.scheme in ("http", "https") and bool(p.netloc)
    except ValueError:
        return False


def invalid_values(node):
    """[(property, value, expected)] for values that are clearly malformed."""
    bad = []
    for key in ("price", "lowPrice", "highPrice"):
        v = node.get(key)
        if v not in (None, "") and not isinstance(v, (int, float)):
            sv = str(v).strip()
            if not _PRICE.match(sv):
                bad.append((key, sv[:40], "a plain number such as 1299.00 (no currency symbol or thousands separator)"))
    cur = node.get("priceCurrency")
    if cur not in (None, "") and not _CURRENCY.match(str(cur).strip()):
        bad.append(("priceCurrency", str(cur)[:20], "an ISO 4217 code such as INR or USD"))
    for key in ("datePublished", "dateModified", "priceValidUntil", "validThrough", "startDate", "endDate"):
        v = node.get(key)
        if isinstance(v, str) and v.strip() and not _ISO_DATE.match(v.strip()):
            bad.append((key, v[:40], "an ISO 8601 date such as 2026-10-12"))
    for key in ("url", "logo", "image"):
        v = node.get(key)
        if isinstance(v, str) and v.strip() and not _absolute(v):
            bad.append((key, v[:80], "an absolute https:// URL"))
    same = node.get("sameAs")
    for v in (same if isinstance(same, (list, tuple)) else [same] if same else []):
        if isinstance(v, str) and not _absolute(v):
            bad.append(("sameAs", v[:80], "an absolute https:// profile URL"))
    return bad


def price_numbers(text):
    """Numbers that look like prices in visible text, normalised (1,299.00 -> 1299)."""
    out = set()
    for m in re.finditer(r"(?:[$\u20ac\u00a3\u20b9]|rs\.?|inr|usd|eur|gbp)\s?(\d[\d,]*(?:\.\d{1,2})?)", text, re.I):
        out.add(_norm_number(m.group(1)))
    for m in re.finditer(r"(\d[\d,]*(?:\.\d{1,2})?)\s?(?:[$\u20ac\u00a3\u20b9]|inr|usd|eur|/-)", text, re.I):
        out.add(_norm_number(m.group(1)))
    return {n for n in out if n}


def _norm_number(s):
    try:
        v = float(str(s).replace(",", ""))
    except ValueError:
        return None
    return str(int(v)) if v == int(v) else f"{v:.2f}"


def norm_price(v):
    return _norm_number(str(v).strip()) if v not in (None, "") else None
