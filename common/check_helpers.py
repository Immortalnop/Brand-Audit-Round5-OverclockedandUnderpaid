"""Shared, network-free helpers for snapshot check modules."""
import re
from urllib.parse import unquote
from check_catalog import get_entry
from models import make_finding


def eligible_pages(artifacts):
    return [p for p in artifacts.pages if p.status_code == 200 and p.features
            and p.features.get('observation_version') == 2
            and not {'non_html_content', 'response_truncated_at_byte_budget', 'html_parse_incomplete'} & set(p.warnings)]


# Visible raw-HTML text below which a page probably builds its content with
# JavaScript. A single flat threshold would treat a contact page (legitimately
# short: an address, a phone number, a form) the same as an article page, so it
# is calibrated per page_type. Shared by analyze_rendering.py and the checks
# that must not judge a page whose content the raw HTML does not carry.
MIN_SUBSTANTIAL_CHARS = 200  # fallback for page types without a specific threshold
MIN_SUBSTANTIAL_CHARS_BY_TYPE = {
    "home": 300,
    "category": 250,
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


def script_dependent(page):
    """True when the raw HTML carries too little visible text for the page type
    and no substantial <noscript> fallback: the content is probably built by
    JavaScript, so a check cannot conclude from the raw HTML that something is
    missing from the page."""
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
        confidence=.95 if confirmed else .6, title=title,
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
