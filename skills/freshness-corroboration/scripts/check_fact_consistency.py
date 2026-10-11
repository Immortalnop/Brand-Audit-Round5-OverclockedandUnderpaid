"""check_fact_consistency.py -- one fact stated two ways on the site itself.

Two checks over the acquisition snapshot, with no request:

fact-markup-mismatch: structured data states a fact the visible text
contradicts. A mismatch needs both sides: the text shows a fact of the same
kind, and never the value the markup states.
  - telephone and postal code of an organization: the marked-up value appears
    on no sampled page, while the pages that carry the markup show another
    telephone or postal address (a head-office number in the markup and a store
    number on the page is fine as long as the head-office number is shown
    somewhere);
  - opening hours: no time in the markup appears in the opening hours the site
    shows;
  - price: a product page with one Offer price that the page never shows,
    while it shows other prices.
Only pages whose whole visible text was read and that do not build their text
with JavaScript are used, so a fact cut off or rendered later is never read as
missing.

fact-inconsistent-across-pages: one entity has two values for one property on
two pages: the same absolute @id, the same name for a (non-local)
organization, or the same GTIN for a product (a SKU or MPN often names a
product family whose variants are priced differently, so it is not used). Pages in different languages are compared only
with pages in the same language, since a regional page may list a regional
number or currency.
"""
import re

from check_helpers import contact_details, eligible_pages, page_share, script_dependent
from models import make_finding, skill_result
from structured_data import LOCAL_BUSINESS_TYPES, ORGANIZATION_TYPES, iter_nodes, types_of

_PRODUCT_TYPES = frozenset({"Product", "ProductGroup", "IndividualProduct", "ProductModel"})
_NAMED_ORG_TYPES = ORGANIZATION_TYPES - LOCAL_BUSINESS_TYPES
_PRICE_TEXT = re.compile(r"(?:[$\u20ac\u00a3\u00a5\u20b9]|\b(?:USD|EUR|GBP|INR|AUD|CAD|Rs\.?))\s?\d[\d,.]*\d|"
                         r"(?:[$\u20ac\u00a3\u00a5\u20b9]|\b(?:USD|EUR|GBP|INR|AUD|CAD|Rs\.?))\s?\d")
_POSTAL_TOKEN = re.compile(r"\b\d{4,6}(?:-\d{4})?\b|\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b|\b[A-Z]\d[A-Z] ?\d[A-Z]\d\b")
_HOURS_CUE = re.compile(r"\b(?:opening\s+hours|opening\s+times|business\s+hours|office\s+hours|store\s+hours"
                        r"|hours|open)\b", re.I)
_DAY_WORD = re.compile(r"\b(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\b|\bdaily\b|\bevery\s+day\b|\bweekdays?\b"
                       r"|\bweekends?\b", re.I)
_TIME_12H = re.compile(r"\b(1[0-2]|0?[1-9])(?:[:.]([0-5]\d))?\s*(a\.?\s?m\.?|p\.?\s?m\.?)(?![a-z])", re.I)
_TIME_24H = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b(?!\s*(?:a\.?\s?m|p\.?\s?m))", re.I)
_MARKUP_TIME = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)")
# How a price in each currency is written in visible text.
_CURRENCY_MARKERS = {"USD": ("$", "USD"), "EUR": ("\u20ac", "EUR"), "GBP": ("\u00a3", "GBP"),
                     "INR": ("\u20b9", "Rs", "INR"), "JPY": ("\u00a5",), "AUD": ("$", "AUD"), "CAD": ("$", "CAD")}
_MAX_EVIDENCE = 10


# -- Normalization ------------------------------------------------------------

def _strings(value):
    """String values of a property that may hold one value or a list."""
    values = value if isinstance(value, (list, tuple)) else [value]
    return [str(v).strip() for v in values if isinstance(v, (str, int, float)) and not isinstance(v, bool)
            and str(v).strip()]


def phone_key(value):
    """Last 9 digits of a phone number without its leading zeros: one key for
    '+44 20 7946 0000' and '020 7946 0000'. None below 7 digits."""
    digits = re.sub(r"\D", "", value or "").lstrip("0")
    return digits[-9:] if len(digits) >= 7 else None


def postal_key(value):
    key = re.sub(r"[\s-]", "", value or "").upper()
    return key if len(key) >= 3 else None


def parse_price(value):
    """A price as a float: '1,299.00', '1.299,00', '49', 49.5. None when unreadable."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = re.sub(r"[^\d.,]", "", value)
    if not text or not re.search(r"\d", text):
        return None
    if "," in text and "." in text:
        decimal = "," if text.rfind(",") > text.rfind(".") else "."
        text = text.replace("." if decimal == "," else ",", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".") if re.fullmatch(r"\d+,\d{2}", text) else text.replace(",", "")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def price_shown(price, text):
    """True when the visible text writes the price in any common way."""
    whole = int(price) if price == int(price) else None
    forms = {f"{price:.2f}", f"{price:,.2f}", f"{price:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")}
    if whole is not None:
        forms |= {str(whole), f"{whole:,}", f"{whole:,}".replace(",", ".")}
    return any(re.search(r"(?<![\d.,])" + re.escape(form) + r"(?![\d]|[.,]\d)", text) for form in forms)


def _minutes(hour, minute, meridiem=None):
    hour, minute = int(hour), int(minute or 0)
    if meridiem:
        hour = hour % 12 + (12 if meridiem.lower().startswith("p") else 0)
    return hour * 60 + minute


def markup_hours(node):
    """Opening and closing times (minutes after midnight) a node states."""
    times = set()
    for text in _strings(node.get("openingHours")):
        times |= {_minutes(h, m) for h, m in _MARKUP_TIME.findall(text)}
    specs = node.get("openingHoursSpecification")
    for spec in specs if isinstance(specs, (list, tuple)) else [specs]:
        if hasattr(spec, "get"):
            for key in ("opens", "closes"):
                for text in _strings(spec.get(key)):
                    found = _MARKUP_TIME.match(text)
                    if found:
                        times.add(_minutes(*found.groups()))
    return times


def visible_hours(text):
    """Times written near an opening-hours cue and a day word."""
    times = set()
    for cue in _HOURS_CUE.finditer(text or ""):
        window = text[cue.start():cue.end() + 160]
        if not _DAY_WORD.search(window):
            continue
        times |= {_minutes(h, m, ap) for h, m, ap in _TIME_12H.findall(window)}
        times |= {_minutes(h, m) for h, m in _TIME_24H.findall(window)}
    return times


def _digit_text(text):
    """Visible text with separators inside numbers removed, so '020 7946-0000'
    reads as one run of digits."""
    return re.sub(r"(?<=\d)[\s().\-/]+(?=\d)", "", text or "")


def _addresses(page):
    f = page.features or {}
    return [a for a in list(f.get("postal_address_text") or ()) + list(f.get("address_text") or ()) if a]


def _postal_address_shown(page):
    return any(_POSTAL_TOKEN.search(a) for a in _addresses(page))


# -- Markup facts -------------------------------------------------------------

def _org_nodes(page):
    return [n for n in iter_nodes(page.jsonld_blocks) if types_of(n) & ORGANIZATION_TYPES]


def _postal_codes(node):
    codes = []
    addresses = node.get("address")
    for address in addresses if isinstance(addresses, (list, tuple)) else [addresses]:
        if hasattr(address, "get"):
            codes += _strings(address.get("postalCode"))
    return codes


def _offers(node):
    offers = node.get("offers")
    return [o for o in (offers if isinstance(offers, (list, tuple)) else [offers])
            if hasattr(o, "get") and "Offer" in types_of(o)]


def _page_prices(page):
    """Distinct (currency, price) pairs of the Offers on one page."""
    prices = set()
    for node in iter_nodes(page.jsonld_blocks):
        if "Offer" in types_of(node):
            price = parse_price(node.get("price"))
            if price:
                prices.add(((_strings(node.get("priceCurrency")) or [""])[0].upper(), price))
    return prices


# -- Check 1: markup against visible text -------------------------------------

def _readable(pages):
    return [p for p in pages if (p.features or {}).get("visible_text_complete") and not script_dependent(p)]


def markup_mismatches(pages):
    """(evidence entries, facts compared) for structured facts the visible text contradicts."""
    readable = _readable(pages)
    evidence, compared = [], 0
    site_digits = " ".join(_digit_text(p.visible_text) for p in readable)
    site_text = re.sub(r"[\s-]", "", " ".join(p.visible_text for p in readable)).upper()

    # Telephone and postal code: the value is shown nowhere, the carrying pages show others.
    phones, postals = {}, {}
    for p in readable:
        for node in _org_nodes(p):
            for value in _strings(node.get("telephone")):
                key = phone_key(value)
                if key:
                    phones.setdefault(key, (value, []))[1].append(p)
            for value in _postal_codes(node):
                key = postal_key(value)
                if key:
                    postals.setdefault(key, (value, []))[1].append(p)
    # Numbers a visitor can see or tap anywhere in the sample (tel: links included).
    site_phone_keys = {phone_key(ph) for p in readable for ph in contact_details(p)[1]}
    for key, (value, carriers) in sorted(phones.items()):
        shown = {ph for p in carriers for ph in contact_details(p)[1] if phone_key(ph)}
        if not shown:
            continue
        compared += 1
        if key not in site_digits and key not in site_phone_keys:
            urls = sorted({p.url for p in carriers})
            evidence.append({"type": "markup_text_mismatch",
                             "description": f"JSON-LD telephone {value} appears on no sampled page; the pages "
                                            f"that carry it show {', '.join(sorted(shown)[:3])}",
                             "urls": urls[:10], "fact": "telephone"})
    for key, (value, carriers) in sorted(postals.items()):
        shown = [a for p in carriers if _postal_address_shown(p) for a in _addresses(p)]
        if not shown:
            continue
        compared += 1
        if key not in site_text:
            urls = sorted({p.url for p in carriers})
            evidence.append({"type": "markup_text_mismatch",
                             "description": f"JSON-LD postal code {value} appears on no sampled page; the pages "
                                            f"that carry it show the address {shown[0][:120]}",
                             "urls": urls[:10], "fact": "postal_code"})

    # Opening hours: no marked-up time is among the times the site shows.
    stated, carriers = set(), set()
    for p in readable:
        for node in _org_nodes(p):
            times = markup_hours(node)
            if times:
                stated |= times
                carriers.add(p.url)
    # A 24-hour business marks 00:00 or 23:59, which no page writes as opening hours.
    if stated and not stated & {0, 1439}:
        shown = set().union(*(visible_hours(p.visible_text) for p in readable))
        if len(shown) >= 2:
            compared += 1
            if not stated & shown:
                fmt = lambda ts: ", ".join(f"{t // 60:02d}:{t % 60:02d}" for t in sorted(ts)[:6])
                evidence.append({"type": "markup_text_mismatch",
                                 "description": f"JSON-LD opening hours use {fmt(stated)}; the opening hours "
                                                f"shown on the site use {fmt(shown)}",
                                 "urls": sorted(carriers)[:10], "fact": "opening_hours"})

    # Price: one Offer price on a product page that the page never shows.
    for p in readable:
        if p.page_type != "product" and not any(types_of(n) & _PRODUCT_TYPES for n in iter_nodes(p.jsonld_blocks)):
            continue
        prices = _page_prices(p)
        if len(prices) != 1:
            continue  # no price, or several (variants, bundles, currencies): nothing single to compare
        (currency, price), = prices
        markers = _CURRENCY_MARKERS.get(currency)
        if not markers:
            continue  # a currency the page's price text cannot be matched against
        # Only prices in the markup's currency: a page that shows the visitor's
        # local currency (geo-pricing) is not contradicting a USD Offer.
        visible = [m.group(0) for m in _PRICE_TEXT.finditer(p.visible_text or "")
                   if any(marker in m.group(0) for marker in markers)]
        if not visible:
            continue
        compared += 1
        if not price_shown(price, p.visible_text):
            evidence.append({"type": "markup_text_mismatch",
                             "description": f"JSON-LD Offer price {price:g} {currency}".rstrip()
                                            + f"; the page shows {', '.join(dict.fromkeys(visible))[:120]} "
                                              "but never that price",
                             "urls": [p.url], "fact": "price"})
    return evidence, compared


# -- Check 2: one entity, two values ------------------------------------------

def _entity_key(node, page):
    """Identity of a structured entity across pages, or None."""
    types = types_of(node)
    node_id = node.get("@id")
    if isinstance(node_id, str) and node_id.strip().startswith(("http://", "https://")) \
            and types & (ORGANIZATION_TYPES | _PRODUCT_TYPES):
        return ("id", node_id.strip())
    if types & _PRODUCT_TYPES:
        # A GTIN names one sellable item. A SKU or MPN often names a product
        # family whose colours or sizes are priced differently, so it is no
        # identity for comparing prices.
        for prop in ("gtin", "gtin13", "gtin12", "gtin14", "gtin8"):
            values = _strings(node.get(prop))
            if values:
                return ("product", prop + ":" + values[0])
        return None
    name = (_strings(node.get("name")) or [""])[0]
    if types & _NAMED_ORG_TYPES and not types & LOCAL_BUSINESS_TYPES and name:
        return ("org", " ".join(name.lower().split()))
    return None


def _entity_facts(node):
    """[(property, comparable key, value as written)] for one node."""
    facts = []
    if types_of(node) & ORGANIZATION_TYPES:
        facts += [("telephone", phone_key(v), v) for v in _strings(node.get("telephone"))]
        facts += [("email", v.lower(), v) for v in _strings(node.get("email"))]
        facts += [("foundingDate", v[:4], v) for v in _strings(node.get("foundingDate")) if re.match(r"\d{4}", v)]
        facts += [("postalCode", postal_key(v), v) for v in _postal_codes(node)]
    if types_of(node) & _PRODUCT_TYPES:
        for offer in _offers(node):
            price = parse_price(offer.get("price"))
            if price:
                currency = (_strings(offer.get("priceCurrency")) or [""])[0].upper()
                facts.append(("price " + currency if currency else "price", f"{price:.2f}", f"{price:g}"))
    return [f for f in facts if f[1]]


def cross_page_conflicts(pages):
    """Evidence entries for an entity property with different values on two pages."""
    seen, per_page, names = {}, {}, {}
    for p in pages:
        lang = ((p.features or {}).get("lang") or "").lower()[:2]
        for node in iter_nodes(p.jsonld_blocks):
            key = _entity_key(node, p)
            if not key:
                continue
            names.setdefault(key, (_strings(node.get("name")) or [""])[0])
            for prop, value_key, written in _entity_facts(node):
                slot = seen.setdefault((key, lang, prop), {})
                slot.setdefault(value_key, (written, []))
                if p.url not in slot[value_key][1]:
                    slot[value_key][1].append(p.url)
                per_page.setdefault((key, lang, prop), {}).setdefault(p.url, set()).add(value_key)
    evidence = []
    for slot_key, values in sorted(seen.items(), key=lambda item: str(item[0])):
        (kind, ident), _, prop = slot_key
        if len(values) < 2:
            continue
        # A property one page states with several values (two telephones, one
        # product in several variants) is multi-valued, not a conflict.
        if any(len(v) > 1 for v in per_page[slot_key].values()):
            continue
        variants = sorted(values.values(), key=lambda v: (-len(v[1]), v[0]))
        pages_of = [set(v[1]) for v in variants]
        name = names.get((kind, ident)) or ident
        label = {"org": f"Organization '{name}'", "product": f"Product '{name}' ({ident})"}.get(kind, ident)
        described = "; ".join(f"'{written}' on {urls[0]}" + (f" and {len(urls) - 1} more" if len(urls) > 1 else "")
                              for written, urls in variants[:3])
        evidence.append({"type": "cross_page_fact",
                         "description": f"{label} {prop}: {described}",
                         "urls": sorted(set().union(*pages_of))[:10], "fact": prop})
    return evidence


def check_fact_consistency(artifacts, deadline):
    if deadline.expired():
        return skill_result("freshness-corroboration", status="insufficient_evidence",
                            warnings=["Fact consistency checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    findings = []
    mismatches, compared = markup_mismatches(pages)
    if mismatches:
        urls = sorted({u for e in mismatches for u in e["urls"]})
        facts = sorted({e["fact"].replace("_", " ") for e in mismatches})
        findings.append(make_finding(
            category="corroboration", finding_type="defect", severity="medium", status="suspected",
            confidence=0.65,
            title="Structured data and visible text disagree on the " + ", ".join(facts),
            root_cause="The JSON-LD states a fact that the visible pages state differently. Assistants read the "
                       "markup and the text, so they meet two answers to one question and may quote the wrong "
                       "one; visitors only see the text.",
            evidence=mismatches[:_MAX_EVIDENCE], affected_pages=urls,
            suggested_action={
                "summary": "Make the structured data and the visible text state the same value",
                "steps": ["For each fact in the evidence, find which value is current",
                          "Correct the JSON-LD or the page text so both state the current value",
                          "Generate the JSON-LD from the same source the page text uses, so they cannot drift"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Assistants and visitors get one answer for each fact",
                "verification": "Re-run the audit and confirm the facts are no longer listed",
            },
            provenance={"skill": "freshness-corroboration", "script": "check_fact_consistency.py",
                        "rule_id": "fact-markup-mismatch"},
        ))
    conflicts = cross_page_conflicts(pages)
    if conflicts:
        urls = sorted({u for e in conflicts for u in e["urls"]})
        findings.append(make_finding(
            category="corroboration", finding_type="defect", severity="medium", status="confirmed",
            confidence=0.8,
            title="The same fact has different values on " + page_share(urls, pages),
            root_cause="One organization or product is described with different values for the same property on "
                       "different pages. An assistant cannot tell which is current and may repeat either, or "
                       "trust neither.",
            evidence=conflicts[:_MAX_EVIDENCE], affected_pages=urls,
            suggested_action={
                "summary": "State each fact once and reuse it on every page",
                "steps": ["For each property in the evidence, decide which value is current",
                          "Correct the pages that state the other value",
                          "Emit organization and product markup from one shared template or data source"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Every page states the same value, so assistants repeat it with confidence",
                "verification": "Re-run the audit and confirm no property is listed with two values",
            },
            provenance={"skill": "freshness-corroboration", "script": "check_fact_consistency.py",
                        "rule_id": "fact-inconsistent-across-pages"},
        ))
    return skill_result(
        "freshness-corroboration", findings=findings,
        metrics={"facts_compared_with_text": compared, "markup_text_mismatches": len(mismatches),
                 "cross_page_conflicts": len(conflicts), "fact_consistency_pages": len(pages)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
