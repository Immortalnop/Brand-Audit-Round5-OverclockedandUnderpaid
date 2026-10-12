"""Shared, network-free helpers for snapshot check modules."""
import re
from urllib.parse import unquote, urlsplit
from check_catalog import calibrated_confidence, get_entry
from models import make_finding
from structured_data import iter_nodes, types_of


def eligible_pages(artifacts):
    return [p for p in artifacts.pages if p.status_code == 200 and p.features
            and p.features.get('observation_version') == 2
            and not {'non_html_content', 'response_truncated_at_byte_budget', 'html_parse_incomplete'} & set(p.warnings)]


# Page warnings meaning the delivered HTML was not read in full: a prefix can
# prove that an observed tag exists, never that the page lacks one.
PARTIAL_OBSERVATION_WARNINGS = frozenset({'response_truncated_at_byte_budget', 'html_parse_incomplete'})


def page_observation(page):
    """What one fetched page's observation can support. Keys:
      status: 'complete', 'partial', 'non_html', 'http_error' or 'fetch_failed'
      positive_facts: an observed tag, text or link is evidence (any 2xx HTML)
      local_absence: the page's own HTML was read in full, so "this page lacks X
        in its delivered HTML" holds
      link_graph: local_absence, the link list was not cut at its cap, and the
        page is not built by JavaScript, so its outgoing links are all known
      script_dependent: the raw HTML is too thin to stand for the page
      reasons: why an observation is limited (warning names, 'script_dependent')
    Unanalyzed pages (login, challenge, waiting room) never reach artifacts.pages."""
    warnings = set(page.warnings or ())
    if page.status_code is None:
        reasons = [w for w in page.warnings if w.startswith('fetch_')] or ['fetch_failed']
        return {'status': 'fetch_failed', 'positive_facts': False, 'local_absence': False, 'link_graph': False,
                'script_dependent': False, 'reasons': reasons}
    if not 200 <= page.status_code < 300:
        return {'status': 'http_error', 'positive_facts': False, 'local_absence': False, 'link_graph': False,
                'script_dependent': False, 'reasons': [f'http_{page.status_code}']}
    if 'non_html_content' in warnings:
        return {'status': 'non_html', 'positive_facts': False, 'local_absence': False, 'link_graph': False,
                'script_dependent': False, 'reasons': ['non_html_content']}
    reasons = sorted(PARTIAL_OBSERVATION_WARNINGS & warnings)
    complete = not reasons
    # A snapshot built without HTML features (no parse observation at all) has
    # no script evidence either way; an acquired page always has features.
    built = bool(page.features) and script_dependent(page)
    links_cut = 'link_list_truncated' in warnings
    if links_cut:
        reasons.append('link_list_truncated')
    if built:
        reasons.append('script_dependent')
    return {'status': 'complete' if complete else 'partial', 'positive_facts': True, 'local_absence': complete,
            'link_graph': complete and not links_cut and not built, 'script_dependent': built, 'reasons': reasons}


# Visible raw-HTML text below which a page probably builds its content with
# JavaScript. A single flat threshold would treat a contact page (legitimately
# short: an address, a phone number, a form) the same as an article page, so it
# is calibrated per page_type. Shared by analyze_rendering.py and the checks
# that must not judge a page whose content the raw HTML does not carry.
MIN_SUBSTANTIAL_CHARS = 200  # fallback for page types without a specific threshold
MIN_SUBSTANTIAL_CHARS_BY_TYPE = {
    "home": 300,
    "category": 250,
    "listing": 250,
    "product": 150,
    "article": 400,
    "contact": 80,
    "about": 200,
    "legal": 150,
    "other": MIN_SUBSTANTIAL_CHARS,
}


def substantial_threshold(page_type):
    return MIN_SUBSTANTIAL_CHARS_BY_TYPE.get(page_type, MIN_SUBSTANTIAL_CHARS)


def noscript_state(page):
    """(script_on_chars, fallback_chars, js_required) for one page.

    Text inside <noscript> is shown only when scripts do not run, so it is not
    content a script-running visitor sees. A <noscript> that only says JavaScript
    is required is not a fallback at all: it confirms the page depends on scripts.
    Real fallback text is content for crawlers that do not run scripts."""
    features = page.features or {}
    total = len((page.visible_text or "").strip())
    noscript = min(total, int(features.get("noscript_chars") or 0))
    js_required = bool(features.get("noscript_js_required"))
    fallback = 0 if js_required and noscript < 200 else noscript
    return total - noscript, fallback, js_required


def runs_scripts(page):
    """True when the page loads or embeds JavaScript, or its <noscript> says
    JavaScript is required (the page's own statement that it depends on scripts).
    A page with no script (JSON-LD and other data blocks do not count) cannot
    build content after load, so its raw HTML is the whole page. Unknown (older
    observations) counts as True."""
    features = page.features or {}
    if "external_scripts" not in features and "inline_script_bytes" not in features:
        return True
    return (bool(features.get("external_scripts")) or bool(features.get("inline_script_bytes"))
            or bool(features.get("noscript_js_required")))


def script_dependent(page):
    """True when the page runs scripts and its raw HTML carries too little visible
    text for the page type, with no substantial <noscript> fallback: the content
    is probably built by JavaScript, so a check cannot conclude from the raw HTML
    that something is missing from the page. A short page with no script is just
    a short page."""
    if not runs_scripts(page):
        return False
    script_on, fallback, _ = noscript_state(page)
    threshold = substantial_threshold(page.page_type)
    return script_on < threshold and fallback < threshold


def split_script_dependent(pages):
    """(pages the raw HTML can judge, pages built by JavaScript)."""
    flags = [script_dependent(p) for p in pages]
    return ([p for p, built in zip(pages, flags) if not built],
            [p for p, built in zip(pages, flags) if built])


def script_dependent_warning(built, pages, checks):
    """Warning for the report when checks skipped pages built by JavaScript, so
    an unassessed page is never presented as one that passed."""
    verb = "carries" if len(pages) == 1 else "carry"
    return (f"{page_share(built, pages)} {verb} too little text in their raw HTML to judge {checks}: their "
            "content is probably built by JavaScript, so these checks did not assess them.")


def contact_details(page):
    """({emails}, {phones}) a visitor can see on one page: mailto: and tel:
    links, plus emails and labelled phone numbers written as text."""
    f = page.features or {}
    text = f.get('contact_text') or {}
    emails = {e.lower() for e in text.get('emails') or ()}
    phones = {' '.join(p.split()) for p in text.get('phones') or ()}
    for href, _ in f.get('anchors') or ():
        href = (href or '').strip()
        scheme, _, rest = href.partition(':')
        value = unquote(rest.split('?', 1)[0]).split(',')[0].strip()
        if scheme.lower() == 'mailto' and re.fullmatch(r'[^@\s]+@[^@\s]+\.[A-Za-z]{2,24}', value):
            emails.add(value.lower())
        elif scheme.lower() == 'tel' and 7 <= sum(c.isdigit() for c in value) <= 15:
            phones.add(' '.join(value.split()))
    return emails, phones


_GENERIC_MAILBOX = re.compile(r'^(?:info|contact|contactus|hello|hi|enquiries|enquiry|inquiries|inquiry|support|help'
                              r'|sales|office|admin|admissions|reception|service|customerservice|care|team|mail)@')


def organization_contact(pages, host):
    """(email, phone) most likely to be the organization's own: an email on the
    site's domain, preferring a generic mailbox (info@, contact@) and one seen on
    the home or contact page; a phone seen on the most pages, again preferring
    the home and contact pages. Either is None when nothing qualifies."""
    host = (host or '').lower()
    host = host[4:] if host.startswith('www.') else host
    email_score, phone_score, phone_text = {}, {}, {}
    for p in pages:
        weight = 3 if p.page_type in ('home', 'contact') else 1
        emails, phones = contact_details(p)
        for e in emails:
            domain = e.rsplit('@', 1)[1]
            if host and (domain == host or domain.endswith('.' + host) or host.endswith('.' + domain)):
                email_score[e] = email_score.get(e, 0) + weight + (5 if _GENERIC_MAILBOX.match(e) else 0)
        for ph in phones:
            # The same number written two ways ("+1 555 0100", "15550100") is one number.
            digits = re.sub(r'\D', '', ph)
            phone_score[digits] = phone_score.get(digits, 0) + weight
            if digits not in phone_text or (ph.startswith('+') and not phone_text[digits].startswith('+')):
                phone_text[digits] = ph
    pick = lambda scores: max(sorted(scores), key=scores.get) if scores else None
    phone = pick(phone_score)
    return pick(email_score), phone_text[phone] if phone else None


_COMMERCE_TYPES = frozenset({'Product', 'ProductGroup', 'IndividualProduct', 'ProductModel', 'Offer',
                             'AggregateOffer'})
_PRICE_TEXT = re.compile(r'(?:[$€£¥₹]|\b(?:USD|EUR|GBP|INR|AUD|CAD|Rs\.?))\s?\d[\d,]*(?:\.\d{2})?')
_BUY_TEXT = re.compile(r'\b(?:add\s+to\s+(?:cart|bag|basket|trolley|order)|buy\s+(?:it\s+)?now|shop\s+now)\b', re.I)
# A cart is a top-level path, optionally after a locale segment ("/cart",
# "/en-gb/basket"); "/payments/checkout" is a product page about checkout.
_CART_PATH = re.compile(r'^(?:/[a-z]{2}(?:[-_][a-z]{2})?)?/(?:cart|basket|bag|checkout)/?$', re.I)


def _path_of(href):
    try:
        return urlsplit((href or '').strip()).path or ''
    except ValueError:
        return ''


def commerce_evidence(page):
    """What on one page shows that it sells something: Product or Offer markup,
    a price, a buy or add-to-cart control, or a link to a cart. '' when nothing."""
    f = page.features or {}
    if any(types_of(n) & _COMMERCE_TYPES for n in iter_nodes(page.jsonld_blocks)) \
            or set(f.get('microdata_types') or ()) & _COMMERCE_TYPES:
        return 'product_markup'
    if _PRICE_TEXT.search(page.visible_text or ''):
        return 'price'
    controls = list(f.get('buttons') or ()) + [t for _, t in (f.get('anchors') or ())]
    if any(_BUY_TEXT.search(t or '') for t in controls):
        return 'buy_control'
    if any(_CART_PATH.search(_path_of(h)) for h, _ in (f.get('anchors') or ())):
        return 'cart_link'
    return ''


# Organization types and wording that show a site does not sell to consumers:
# news publishers and nonprofits (public bodies are recognized separately by
# their types and host names in check_off_site_profiles.py).
_PUBLISHER_TYPES = frozenset({'NewsMediaOrganization', 'NewsArticle', 'ReportageNewsArticle', 'AnalysisNewsArticle',
                              'OpinionNewsArticle', 'BackgroundNewsArticle', 'ReviewNewsArticle', 'LiveBlogPosting'})
_NONPROFIT_TYPES = frozenset({'NGO', 'NonprofitType', 'FundingScheme'})
_DONATE = re.compile(r'^(?:donate|donations?|give|make\s+a\s+(?:gift|donation)|support\s+us)\b', re.I)
_DONATE_PATH = re.compile(r'/(?:donate|donations?|give|support-us)(?:[/?#]|$)', re.I)


def site_kind(pages):
    """'publisher', 'nonprofit' or 'unknown' from positive evidence on the sampled
    pages: news markup marks a publisher; nonprofit markup, or a donation link on
    a site with no commerce evidence, marks a nonprofit. 'unknown' never
    excludes a check."""
    types = set()
    nonprofit_status = False
    for p in pages:
        for node in iter_nodes(p.jsonld_blocks):
            types |= types_of(node)
            nonprofit_status = nonprofit_status or bool(hasattr(node, 'get') and node.get('nonprofitStatus'))
    if types & _PUBLISHER_TYPES:
        return 'publisher'
    if types & _NONPROFIT_TYPES or nonprofit_status:
        return 'nonprofit'
    # A price alone counts only on a shop page: a salary on a jobs page or a fee
    # in an article does not make a site a shop.
    for p in pages:
        found = commerce_evidence(p)
        if found and (found != 'price' or p.page_type in ('product', 'category')):
            return 'unknown'
    # A donation link on the home page, or in navigation repeated on two or more
    # pages (the home page may be a splash page with no navigation).
    asks = [p for p in pages
            if any(_DONATE.match((t or '').strip()) or _DONATE_PATH.search(h or '')
                   for h, t in (p.features or {}).get('anchors') or ())]
    if any(p.page_type == 'home' for p in asks) or len(asks) >= 2:
        return 'nonprofit'
    return 'unknown'


def page_share(selected, population, noun='sampled page'):
    """'3/5 sampled pages': how many of the checked pages a gap affects, so a title
    states the concrete gap rather than asking the reader to review something.
    selected is the affected pages or their count."""
    count = selected if isinstance(selected, int) else len(selected)
    total = len(population)
    return f"{count}/{total} {noun}{'' if total == 1 else 's'}"


def observation(check_id, title, pages, details, *, skill='crawl-render-audit',
                script='analyze_metadata.py', severity='low', confirmed=False):
    """Absence-based heuristics default to suspected, low-priority opportunities."""
    entry = get_entry(check_id)
    return make_finding(
        category='ai_discoverability', finding_type='defect' if confirmed else 'proactive_improvement',
        severity=severity, status='confirmed' if confirmed else 'suspected',
        confidence=.95 if confirmed else calibrated_confidence(check_id, .6), title=title,
        root_cause=entry['mechanism'],
        affected_pages=[p.url for p in pages],
        evidence=[{'type':'snapshot_observation', 'description':details[p.url], 'urls':[p.url]}
                  for p in pages[:10]],
        suggested_action={'summary':entry['implementation_detail'],
                          'steps':[entry['implementation_detail']], 'priority':severity,
                          'effort':'medium' if check_id in ('http-transport','heavy-html','fetch-latency') else 'low',
                          'expected_benefit':entry['expected_outcome'],
                          'verification':'Repeat the affected observation and verify the intended behavior.'},
        provenance={'skill':skill, 'script':script, 'rule_id':check_id})
