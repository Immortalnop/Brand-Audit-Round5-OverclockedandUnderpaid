"""Shared, network-free helpers for snapshot check modules."""
import re
from collections import Counter, defaultdict
from check_catalog import get_entry, meta_for
from models import make_finding

# Pages whose body is not the site's real content are never analysed for content
# defects. bot_challenge / rate_limited are firewall interstitials; the others
# are incomplete or non-HTML responses.
EXCLUDED_WARNINGS = frozenset({'non_html_content', 'response_truncated_at_byte_budget',
                               'html_parse_incomplete', 'bot_challenge', 'rate_limited', 'login_page'})


def is_challenged(page):
    return bool({'bot_challenge', 'rate_limited'} & set(page.warnings or ()))


def content_pages(artifacts, require_features=True):
    """The single definition of 'a page whose content we can judge': HTTP 200,
    parsed, complete, and not a bot-protection interstitial."""
    return [p for p in artifacts.pages if p.status_code == 200
            and (not require_features or (p.features and p.features.get('observation_version') == 2))
            and not EXCLUDED_WARNINGS & set(p.warnings)]


def meta_value(page, key):
    """The first non-empty value of a meta tag on a page, or ''."""
    values = ((page.features or {}).get('meta') or {}).get(key) or ()
    return next((v.strip() for v in values if isinstance(v, str) and v.strip()), '')


def grouped_evidence(pages, details, evidence_type='snapshot_observation', limit=10):
    """One evidence line per distinct observation ('40 page(s): ...'), not one
    identical line per page."""
    by_detail = defaultdict(list)
    for p in pages:
        by_detail[details[p.url]].append(p.url)
    ordered = sorted(by_detail.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return [{'type': evidence_type,
             'description': (f'{len(urls)} page(s): {d}' if len(urls) > 1 else d),
             'urls': urls[:10]} for d, urls in ordered][:limit]


def numbered(steps):
    """Render action steps as one readable sentence: '1) ...; 2) ...'."""
    steps = [str(s).strip().rstrip('.') for s in steps if str(s).strip()]
    if len(steps) == 1:
        return steps[0] + '.'
    return '; '.join(f'{i}) {s}' for i, s in enumerate(steps, 1)) + '.'


def observation(check_id, title, pages, details, *, skill='crawl-render-audit',
                script='analyze_metadata.py', severity='low', confirmed=False, category=None,
                assessed=None, assessed_templates=None):
    """Absence-based heuristics default to suspected, low-priority opportunities.

    assessed is how many pages this check was actually able to judge -- the
    denominator behind an absence claim. common/scoring.py uses it instead of the
    whole content sample when it is supplied, so a check that looked at one About
    page does not borrow the sample strength of twenty unrelated pages."""
    entry = get_entry(check_id)
    category = category or meta_for(check_id).get('category') or 'ai_discoverability'
    finding = make_finding(
        category=category, finding_type='defect' if confirmed else 'proactive_improvement',
        severity=severity, status='confirmed' if confirmed else 'suspected',
        confidence=.95 if confirmed else .6, title=title,
        # What was observed (root cause) is stated separately from why it matters
        # (the catalog mechanism, added by enrich_finding).
        root_cause=f"{title} on {len(pages)} sampled page(s); e.g. {details[pages[0].url]}",
        affected_pages=[p.url for p in pages],
        evidence=grouped_evidence(pages, details),
        suggested_action={'summary':entry['implementation_detail'],
                          'steps':[entry['implementation_detail']], 'priority':severity,
                          'effort':'medium' if check_id in ('http-transport','heavy-html','fetch-latency') else 'low',
                          'expected_benefit':entry['expected_outcome'],
                          'verification':'Repeat the affected observation and verify the intended behavior.'},
        provenance={'skill':skill, 'script':script, 'rule_id':check_id})
    if assessed is not None:
        finding['assessed_pages'] = int(assessed)
    if assessed_templates is not None:
        finding['assessed_templates'] = int(assessed_templates)
    return finding


# The site's own contact details (contact-markup-missing and its snippet). A
# third-party address quoted in user content (a README, a forum post) never counts.
_CONTACT_PAGE_TYPES = ("home", "contact", "about")
_ROLE_MAILBOXES = frozenset({"hello", "hi", "info", "contact", "support", "help", "sales", "enquiries", "inquiries",
                             "office", "team", "press", "media", "customerservice", "service", "care", "admin",
                             "bookings", "reservations", "orders", "jobs", "careers"})


def site_host(url):
    from urllib.parse import urlsplit
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


# A share widget, a platform home page or a link back to the site itself is not
# a profile of the brand on another platform.
_SHARE_PATH = re.compile(r"/(?:sharer|share|intent|sharearticle|dialog|plugins|hashtag|search)(?:[/.?]|$)", re.I)


def profile_link_problem(url, host_of_site):
    """Why a URL cannot be the brand's profile on another platform, or None."""
    from urllib.parse import urlsplit
    try:
        parts = urlsplit((url or "").strip())
        host = (parts.hostname or "").lower()
    except ValueError:
        return "is not a valid web address"
    if parts.scheme not in ("http", "https") or not host:
        return "is not an absolute http(s) web address"
    host = host[4:] if host.startswith("www.") else host
    if host_of_site and (host == host_of_site or host.endswith("." + host_of_site)):
        return "points back at the site itself, not at a profile on another platform"
    if _SHARE_PATH.search(parts.path):
        return "is a share or widget link, not a profile"
    if parts.path.strip("/") == "" and not parts.query:
        return "points at the platform home page, not at a profile"
    return None


def own_email(address, site_host):
    domain = address.rsplit("@", 1)[-1].lower()
    local = address.split("@", 1)[0].lower()
    if local.replace("-", "").replace("_", "") in ("noreply", "donotreply"):
        return False
    return bool(site_host) and (domain == site_host or domain.endswith("." + site_host)
                                or site_host.endswith("." + domain))


def is_role_mailbox(address):
    return address.split("@", 1)[0].lower() in _ROLE_MAILBOXES


def organization_contact(pages, site_host):
    """(emails, phones) the site itself shows, most frequent first."""
    emails, phones, phone_pages = Counter(), Counter(), {}
    for p in pages:
        f = p.features or {}
        for e in f.get("contact_emails") or ():
            if own_email(e, site_host):
                emails[e] += 1
        for n in f.get("contact_phones") or ():
            phones[n] += 1
            phone_pages.setdefault(n, set()).add(p.page_type)
    kept_phones = [n for n, c in phones.most_common() if c >= 2 or phone_pages[n] & set(_CONTACT_PAGE_TYPES)]
    # A role mailbox (hello@, support@ ...) is the organization's address; a
    # person's address shown on a page is not, so role mailboxes come first.
    ranked = sorted(emails.items(), key=lambda kv: (kv[0].split("@", 1)[0] not in _ROLE_MAILBOXES, -kv[1], kv[0]))
    return [e for e, _ in ranked], kept_phones
