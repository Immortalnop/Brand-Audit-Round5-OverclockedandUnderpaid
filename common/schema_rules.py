"""schema_rules.py -- what each schema.org type needs, and who needs it.

Three different claims live here and are kept apart, because reporting one as
another is how a validator loses a reader's trust:

  malformed syntax        the value cannot be read as what it claims to be: a
                          price that is not a number, a currency that is not an
                          ISO 4217 code, a date that is not ISO 8601, a URL
                          field carrying something that is not a usable web IRI.
                          These are facts about the markup, independent of any
                          consumer, and only these are reported as malformed.
  inadequate for its fact the node exists to carry a fact and cannot: an Offer
                          with no price, a BreadcrumbList with no items, an
                          Organization with no name. Still consumer-independent,
                          and reported as a missing requirement.
  consumer requirement    a named consumer wants more than the markup is
                          obliged to carry -- Google's Product rich result wants
                          an offer, review or rating; its Organization logo must
                          be an absolute URL. True, useful, and NOT a validity
                          error, so it is reported as a recommendation that
                          names the consumer and what it is for.

Two specific corrections behind that split:

  * A RELATIVE IRI reference is valid JSON-LD. JSON-LD 1.1 resolves relative
    IRIs against the document or context base IRI, so `"url": "/"` and
    `"logo": "/logo.png"` on an Organization are well-formed markup, not
    malformed values. A particular consumer may require an absolute URL; that is
    a consumer requirement, reported as one. A universal "relative is invalid"
    rule is simply wrong. (JSON-LD 1.1, 3.2 IRIs and 4.1.3 Base IRI.)
  * Type selection is deterministic. rule_for() used to iterate a Python set, so
    for a node declaring both Organization and LocalBusiness the selected rule
    changed with the process hash seed -- and with it the address and url
    requirements, and the findings, between runs of the same audit. It now walks
    an explicit precedence list and merges the requirements of every compatible
    declared type, deduplicated.
"""
import re
from datetime import date, datetime
from urllib.parse import urlsplit

# required / required_any: without these the node cannot carry the fact it
#   exists to carry. Consumer-independent.
# consumer_required / consumer_required_any: a named consumer wants these for a
#   particular result type. True and useful, but not a validity error, so they
#   are reported as recommendations that name the consumer.
RULES = {
    "Product": {"required": ("name",),
                # A Product node with a name and a description is well-formed
                # markup; what it is not is eligible for Google's Product rich
                # result, which wants a price, a rating or a review.
                "consumer_required_any": (("offers", "aggregateRating", "review"),),
                "consumer": "Google Product rich result",
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

# Deterministic type precedence, most specific first. A node declaring several
# types is reported under the first of these it matches, and the requirements of
# every type it matches are merged -- so the same markup always produces the same
# finding, whatever the process hash seed.
TYPE_PRECEDENCE = ("Offer", "AggregateOffer", "Product", "Event", "Article", "FAQPage",
                   "BreadcrumbList", "LocalBusiness", "Organization", "WebSite")
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


def matching_types(types):
    """Every rule type the declared types map to, in deterministic precedence
    order. A node declaring Organization and LocalBusiness matches both, always
    in that same order."""
    mapped = {ALIASES.get(t, t) for t in types}
    return [t for t in TYPE_PRECEDENCE if t in mapped and t in RULES]


def rule_for(types):
    """(primary rule type, merged rule) for a node's declared types, or
    (None, None).

    Deterministic: the primary type is the first match in TYPE_PRECEDENCE, and
    the rule is the deduplicated merge of every matched type's requirements, so
    a node declaring both Organization and LocalBusiness is held to both and
    always reports the same way. Iterating the declared-type set directly made
    this depend on the process hash seed."""
    matched = matching_types(types)
    if not matched:
        return None, None
    merged = {"required": (), "required_any": (), "consumer_required": (),
              "consumer_required_any": (), "recommended": (), "matched_types": tuple(matched)}
    consumers = []
    for t in matched:
        rule = RULES[t]
        for key in ("required", "required_any", "consumer_required", "consumer_required_any", "recommended"):
            merged[key] = merged[key] + tuple(v for v in rule.get(key, ()) if v not in merged[key])
        if rule.get("consumer"):
            consumers.append(rule["consumer"])
    merged["consumer"] = consumers[0] if consumers else None
    return matched[0], merged


def _present(node, key):
    v = node.get(key)
    return v not in (None, "", [], (), {})


def _absent(node, rule, required_key, any_key):
    out = [k for k in rule.get(required_key, ()) if not _present(node, k)]
    for alts in rule.get(any_key, ()):
        if not any(_present(node, k) for k in alts):
            out.append(" or ".join(alts))
    return out


def missing(node, rule):
    """(required, recommended) -- properties without which the node cannot carry
    its fact, and properties that would add freshness or identity signals.
    Consumer requirements are returned separately by consumer_gaps()."""
    req = _absent(node, rule, "required", "required_any")
    rec = [k for k in rule.get("recommended", ()) if not _present(node, k) and k not in req]
    return req, rec


def consumer_gaps(node, rule):
    """[(property, consumer, what it is for)] a named consumer wants and the node
    does not have. Not a validity error: reported as a recommendation."""
    consumer = rule.get("consumer") or "a rich-result consumer"
    gaps = [(prop, consumer, "eligibility for that result type")
            for prop in _absent(node, rule, "consumer_required", "consumer_required_any")]
    # Consumer requirements on values that ARE well-formed markup. Google resolves
    # a relative logo/url against the page, but requires an absolute URL for the
    # Organization logo it displays, so an absolute URL is recommended there --
    # never reported as malformed (see the module docstring).
    for key in ("url", "logo", "image"):
        v = node.get(key)
        if isinstance(v, str) and v.strip() and _is_web_iri(v) and not _absolute(v):
            gaps.append((key, "Google structured-data consumers",
                         f"a relative reference ({v[:60]}) is valid JSON-LD and resolves against the page, but an "
                         "absolute https:// URL is what they require and is unambiguous when the markup is copied "
                         "or syndicated"))
    same = node.get("sameAs")
    for v in (same if isinstance(same, (list, tuple)) else [same] if same else []):
        if isinstance(v, str) and v.strip() and _is_web_iri(v) and not _absolute(v):
            gaps.append(("sameAs", "knowledge-graph consumers",
                         f"sameAs names the brand's profile on ANOTHER site, so a relative reference ({v[:60]}) "
                         "cannot do that even though it is well-formed JSON-LD"))
    return gaps


def _absolute(v):
    try:
        p = urlsplit(str(v))
        return p.scheme in ("http", "https") and bool(p.netloc)
    except ValueError:
        return False


# A usable web IRI reference: absolute http(s), or a relative reference, which
# JSON-LD resolves against the base IRI. What is NOT usable is a value with
# whitespace or control characters in it, or a non-web scheme in a field the
# consumer will dereference as a web address.
_BAD_IRI_CHARS = re.compile(r"[\s\x00-\x1f<>\"{}|\\^`]")
_NON_WEB_SCHEME = re.compile(r"^(?!https?:)[a-z][a-z0-9+.-]*:", re.I)


def _is_web_iri(v):
    value = str(v)
    if not value.strip() or _BAD_IRI_CHARS.search(value):
        return False
    if _NON_WEB_SCHEME.match(value.strip()):
        return False  # javascript:, data:, mailto: ... in a url/logo/image field
    try:
        urlsplit(value)
    except ValueError:
        return False
    return True


def invalid_values(node):
    """[(property, value, expected)] for values that are clearly malformed -- facts
    about the markup, independent of any consumer.

    A relative IRI reference is NOT in here: JSON-LD resolves it against the
    base IRI, so it is well-formed markup. consumer_gaps() reports the
    absolute-URL preference as the named consumer requirement it is."""
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
        if isinstance(v, str) and v.strip() and not _is_web_iri(v):
            bad.append((key, v[:80], "a web address: an absolute https:// URL, or a relative reference that "
                                     "resolves against the page (not a javascript:/data:/mailto: value, and "
                                     "no spaces)"))
    same = node.get("sameAs")
    for v in (same if isinstance(same, (list, tuple)) else [same] if same else []):
        if isinstance(v, str) and v.strip() and not _is_web_iri(v):
            bad.append(("sameAs", v[:80], "a web address for the brand's profile on another site"))
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
