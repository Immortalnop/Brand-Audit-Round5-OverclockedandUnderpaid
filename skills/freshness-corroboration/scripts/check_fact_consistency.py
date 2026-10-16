"""Compare explicit acquired facts for the same subject and conditions.

Markup/text comparisons need a named single entity or product, same street/day
schedule or explicit currency, complete raw text and an actual conflicting value.
Absence, unrelated support offers, multiple variants and unknown scopes do not
establish conflict. Cross-page comparisons require supported identity, language,
region and offer conditions; full supported URL sets are retained.
"""
import re
from money import markup_money, visible_money
from decimal import Decimal
from html_features import find_contact_details
from schema_values import date_value_state

from check_helpers import contact_details, eligible_pages, page_share, script_dependent
from models import make_finding, skill_result
from structured_data import LOCAL_BUSINESS_TYPES, ORGANIZATION_TYPES, iter_nodes, types_of

_PRODUCT_TYPES = frozenset({"Product", "ProductGroup", "IndividualProduct", "ProductModel"})
_NAMED_ORG_TYPES = ORGANIZATION_TYPES - LOCAL_BUSINESS_TYPES
_PRICE_TEXT = re.compile(r"(?:[$€£¥₹]|\b(?:USD|EUR|GBP|INR|JPY|AUD|CAD|Rs\.?))\s*[+-]?\d(?:[\d,.]*\d)?"
                         r"(?:[eE][+-]?\d+)?(?!\w|[.,]\d)")
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
            and not (isinstance(v, int) and v.bit_length() > 336)
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
    number = visible_money(value)
    if number is None:
        return None
    converted = float(number)
    return converted if Decimal(str(converted)) == number else None


def price_shown(price, text):
    """True when the visible text writes the price in any common way."""
    parsed = markup_money(price)
    if parsed is None:
        return False
    tokens = re.finditer(r'(?<!\w)[+-]?\d(?:[\d,.]*\d)?(?:[eE][+-]?\d+)?(?!\w|[.,]\d)', text or '')
    return any(visible_money(token.group(0)) == parsed for token in tokens)



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
    return [n for n in iter_nodes(page.jsonld_blocks) if _fact_types(n) & ORGANIZATION_TYPES]


def _fact_types(node):
    # Existing bare-type compatibility; foreign absolute namespaces cannot
    # establish a schema.org organization/product for these comparisons.
    raw = node.get('@type', ())
    raw = raw if isinstance(raw, (list, tuple)) else [raw]
    if any(isinstance(t, str) and ':' in t and not t.startswith(
            ('https://schema.org/', 'http://schema.org/')) for t in raw):
        return set()
    return types_of(node)


def _named_passages(page, name):
    return [p for p in (page.features or {}).get('opening_paragraphs') or ()
            if name and re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', p, re.I)
            and not re.search(r'\b(?:branch|department|support|holiday|seasonal|temporary|until|effective)\b', p, re.I)]


def _days(text):
    # Conservative supported day identity. Unsupported/ambiguous schedules are
    # left unassessed instead of comparing just their clock times.
    short = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4, 'sa': 5, 'su': 6}
    if re.search(r'\b(?:daily|every day)\b', text, re.I):
        return frozenset(range(7))
    normalized = re.sub(r'\b(Mon(?:day)?|Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)\b',
                        lambda m: m.group(0)[:2], text, flags=re.I)
    found = re.search(r'\b(Mo|Tu|We|Th|Fr|Sa|Su)\s*(?:-|to)\s*(Mo|Tu|We|Th|Fr|Sa|Su)\b', normalized, re.I)
    if found:
        a, b = (short[x.lower()] for x in found.groups())
        return frozenset(range(a, b + 1)) if a <= b else None
    tokens = re.findall(r'\b(?:Mo|Tu|We|Th|Fr|Sa|Su)\b', normalized, re.I)
    return frozenset(short[x.lower()] for x in tokens) if tokens else None


def _hours_days(node):
    values = _strings(node.get('openingHours'))
    if len(values) == 1:
        return _days(values[0])
    specs = node.get('openingHoursSpecification')
    specs = specs if isinstance(specs, (list, tuple)) else [specs]
    if len(specs) == 1 and hasattr(specs[0], 'get') and not any(
            key in specs[0] for key in ('validFrom', 'validThrough')):
        days = _strings(specs[0].get('dayOfWeek'))
        return _days(' '.join(value.rsplit('/', 1)[-1] for value in days))
    return None


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
            if hasattr(o, "get") and "Offer" in _fact_types(o)]


def _page_prices(page):
    """Distinct (currency, price) pairs of the Offers on one page."""
    prices = set()
    for node in iter_nodes(page.jsonld_blocks):
        if "Offer" in types_of(node):
            price = markup_money(node.get("price"))
            if price is not None:
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

    site_phone_keys = {phone_key(ph) for p in readable for ph in contact_details(p)[1]}
    for p in readable:
        nodes = _org_nodes(p)
        if len(nodes) != 1:
            continue
        node = nodes[0]
        name = (_strings(node.get('name')) or [''])[0]
        passages = _named_passages(p, name)
        phones = _strings(node.get('telephone'))
        shown = {value for text in passages if re.search(re.escape(name) + r'\s*[-:]?\s*(?:main\s+)?(?:phone|tel(?:ephone)?|call)\b', text, re.I)
                 for value in find_contact_details(text)['phones']}
        if len(phones) == 1 and phone_key(phones[0]) and len({phone_key(x) for x in shown}) == 1:
            compared += 1
            key = phone_key(phones[0])
            if key not in site_digits and key not in site_phone_keys:
                evidence.append({'type': 'markup_text_mismatch', 'fact': 'telephone', 'urls': [p.url],
                    'description': f"JSON-LD telephone {phones[0]} for {name}; the acquired same-entity contact passage explicitly shows {next(iter(shown))}"})
        addresses = node.get('address')
        addresses = addresses if isinstance(addresses, (list, tuple)) else [addresses]
        if len(addresses) == 1 and hasattr(addresses[0], 'get'):
            address = addresses[0]
            codes = _strings(address.get('postalCode'))
            street = (_strings(address.get('streetAddress')) or [''])[0]
            # Street identity establishes which address is being compared. Another
            # store/address is not evidence that this postal code is wrong.
            shown = [text for text in _addresses(p) if street and street.casefold() in text.casefold()
                     and _POSTAL_TOKEN.search(text)]
            keys = {postal_key(token) for text in shown for token in _POSTAL_TOKEN.findall(text)}
            if len(codes) == 1 and postal_key(codes[0]) and len(keys) == 1:
                compared += 1
                if postal_key(codes[0]) not in keys and postal_key(codes[0]) not in site_text:
                    evidence.append({'type': 'markup_text_mismatch', 'fact': 'postal_code', 'urls': [p.url],
                        'description': f"JSON-LD postal code {codes[0]} for {street}; the acquired same-street address explicitly shows {shown[0][:160]}"})
        stated = markup_hours(node)
        days = _hours_days(node)
        matching_hours = [visible_hours(text) for text in passages if days and _days(text) == days]
        # One entity, same day schedule, one opening/closing pair. Seasonal,
        # multi-shift and 24-hour cases remain unassessed here.
        if len(stated) == 2 and not stated & {0, 1439} and len(matching_hours) == 1 and len(matching_hours[0]) == 2:
            shown = matching_hours[0]
            compared += 1
            if stated != shown:
                fmt = lambda ts: ', '.join(f'{t // 60:02d}:{t % 60:02d}' for t in sorted(ts))
                evidence.append({'type': 'markup_text_mismatch', 'fact': 'opening_hours', 'urls': [p.url],
                    'description': f"JSON-LD opening hours for {name} use {fmt(stated)}; the acquired same-entity/day passage explicitly uses {fmt(shown)}"})

    # Price needs an explicit acquired conflicting value for the same named
    # product and offer conditions. An unrelated price is never a contradiction.
    for p in readable:
        products = [n for n in iter_nodes(p.jsonld_blocks) if _fact_types(n) & _PRODUCT_TYPES]
        if len(products) != 1 or 'ProductGroup' in types_of(products[0]):
            continue
        product = products[0]
        names = _strings(product.get('name'))
        offers = _offers(product)
        if len(names) != 1 or len(offers) != 1 or any(k in offers[0] for k in
                ('priceSpecification', 'eligibleRegion', 'validFrom', 'priceValidUntil', 'itemCondition', 'eligibleQuantity')):
            continue
        price = markup_money(offers[0].get('price'))
        currency = (_strings(offers[0].get('priceCurrency')) or [''])[0].upper()
        if price is None:
            continue
        markers = _CURRENCY_MARKERS.get(currency)
        if not markers:
            continue  # a currency the page's price text cannot be matched against
        visible = []
        for passage in (p.features or {}).get('opening_paragraphs') or ():
            if names[0].casefold() not in passage.casefold() or re.search(
                    r'\b(?:support|subscription|discount|coupon|tax|variant|size|colou?r|bundle|range|from)\b|per\s+(?:month|year)', passage, re.I):
                continue
            for match in _PRICE_TEXT.finditer(passage):
                if not re.search(r'(?<!\w)' + re.escape(names[0]) +
                        r'\s*(?:costs?|price(?:\s+is)?[:]?|is\s+priced\s+at|sells\s+for|is\s+available\s+for|[:=-])\s*$',
                        passage[:match.start()], re.I):
                    continue  # Mere co-occurrence does not bind a price to this product.
                token = match.group(0)
                if any(marker in token for marker in markers):
                    # $ is ambiguous for USD/AUD/CAD: compare only if the page
                    # positively uses that ISO code or has no competing currency.
                    if currency in ('USD', 'AUD', 'CAD', 'JPY') and currency not in passage.upper():
                        continue
                    number = visible_money(token)
                    if number is not None:
                        visible.append((number, token))
        values = {number for number, _ in visible}
        if len(values) != 1:
            continue
        compared += 1
        if next(iter(values)) != price:
            evidence.append({"type": "markup_text_mismatch",
                             "description": f"JSON-LD Offer price {price:g} {currency}".rstrip()
                                            + f" for {names[0]}; the acquired same-product passage explicitly shows "
                                              f"{', '.join(dict.fromkeys(token for _,token in visible))[:120]}",
                             "urls": [p.url], "fact": "price"})
    return evidence, compared


# -- Check 2: one entity, two values ------------------------------------------

def _entity_key(node, page):
    """Identity of a structured entity across pages, or None."""
    types = _fact_types(node)
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
    if _fact_types(node) & ORGANIZATION_TYPES:
        facts += [("telephone", phone_key(v), v) for v in _strings(node.get("telephone"))]
        facts += [("email", v.lower(), v) for v in _strings(node.get("email"))]
        facts += [("foundingDate", v[:4], v) for v in _strings(node.get("foundingDate")) if date_value_state(v) == "valid"]
        facts += [("postalCode", postal_key(v), v) for v in _postal_codes(node)]
    if _fact_types(node) & _PRODUCT_TYPES and 'ProductGroup' not in _fact_types(node) and len(_offers(node)) == 1:
        for offer in _offers(node):
            price = markup_money(offer.get("price"))
            if price is not None:
                currency = (_strings(offer.get("priceCurrency")) or [""])[0].upper()
                conditions = tuple((key, str(offer.get(key, ''))) for key in
                    ('@id', 'sku', 'itemCondition', 'eligibleRegion', 'validFrom', 'priceValidUntil',
                     'availabilityStarts', 'availabilityEnds', 'eligibleQuantity', 'priceSpecification'))
                variant = tuple((key, str(node.get(key, ''))) for key in ('color', 'size', 'model'))
                facts.append((("price " + currency if currency else "price", conditions, variant),
                              price, f"{price:g}"))
    return [f for f in facts if f[1] is not None]


def cross_page_conflicts(pages):
    """Evidence entries for an entity property with different values on two pages."""
    seen, per_page, names = {}, {}, {}
    for p in pages:
        lang = ((p.features or {}).get("lang") or "").lower()
        for node in iter_nodes(p.jsonld_blocks):
            key = _entity_key(node, p)
            if not key:
                continue
            names.setdefault(key, (_strings(node.get("name")) or [""])[0])
            address = node.get('address')
            region = tuple(str(address.get(k, '')) for k in ('addressCountry', 'addressLocality', 'streetAddress')) if hasattr(address, 'get') else str(address or '')
            for prop, value_key, written in _entity_facts(node):
                temporal = tuple(str(node.get(k, '')) for k in ('validFrom', 'validThrough', 'startDate', 'endDate', 'datePublished', 'dateModified'))
                slot = seen.setdefault((key, lang, str(node.get('areaServed', '')), region, temporal, prop), {})
                slot.setdefault(value_key, (written, []))
                if p.url not in slot[value_key][1]:
                    slot[value_key][1].append(p.url)
                per_page.setdefault((key, lang, str(node.get('areaServed', '')), region, temporal, prop), {}).setdefault(p.url, set()).add(value_key)
    evidence = []
    for slot_key, values in sorted(seen.items(), key=lambda item: str(item[0])):
        (kind, ident), _, _, _, _, prop = slot_key
        prop_label = prop[0] if isinstance(prop, tuple) else prop
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
                         "description": f"{label} {prop_label}: {described}",
                         "urls": sorted(set().union(*pages_of)), "fact": prop_label})
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
