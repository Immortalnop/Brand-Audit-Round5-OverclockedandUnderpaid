"""bot_challenge.py -- recognise bot-protection interstitials.

A site behind bot protection may answer an automated client with a challenge
page ("Just a moment...", a CAPTCHA, a JavaScript check) instead of its content.
That page says nothing about the site: analyzing it as content would produce
false findings (a thin page, a missing title, a broken page). The audit records
it as blocked_by_challenge and moves on. It never retries the challenge, never
runs its script and never changes its User-Agent to get past it.

Only shapes that an interstitial has are used:
  - a response header the protection layer sets on a challenge;
  - an error status (403, 429, 503, or 202/405 for some layers) whose body
    carries a challenge or block-page marker;
  - a 2xx page that is nearly empty (under 1,000 visible characters) and carries
    a marker that appears only on interstitials, or a challenge title beside a
    protection-layer marker.
A marker alone never makes a normal page a challenge: several protection layers
inject a script into every page they serve, so script URLs shared with normal
pages count only on error statuses.
"""
import re

# Headers a protection layer sets on a challenge response, with the values that
# mean "challenge" rather than "allowed".
_CHALLENGE_HEADERS = (
    ("cf-mitigated", re.compile(r"challenge", re.I)),
    ("x-amzn-waf-action", re.compile(r"challenge|captcha", re.I)),
)

# Markers that occur only on interstitial or block pages.
_INTERSTITIAL_ONLY = (
    ("cf_challenge", re.compile(r"cf_chl_opt|cf-chl-widget|/cdn-cgi/challenge-platform/h/[bg]/orchestrate", re.I)),
    ("captcha_delivery", re.compile(r"captcha-delivery\.com", re.I)),
    ("px_captcha", re.compile(r"px-captcha|_pxCaptcha", re.I)),
    ("sucuri_challenge", re.compile(r"sucuri_cloudproxy_js", re.I)),
    ("incident_id", re.compile(r"Incapsula incident ID", re.I)),
)

# Markers that normal pages behind the same layer may also carry (an injected
# detection script, a vendor name). They count only on an error status.
_ON_ERROR_ONLY = (
    ("challenge_platform", re.compile(r"/cdn-cgi/challenge-platform/", re.I)),
    ("incapsula", re.compile(r"_Incapsula_Resource", re.I)),
    ("aws_waf", re.compile(r"awswaf|AwsWafIntegration", re.I)),
    ("kasada", re.compile(r"KPSDK", re.I)),
    ("datadome", re.compile(r"datadome", re.I)),
    ("akamai_reference", re.compile(r"errors\.edgesuite\.net|Reference&#32;&#35;|Reference #\d", re.I)),
    ("ddos_guard", re.compile(r"ddos-guard", re.I)),
)

# Titles and headings of challenge pages.
_CHALLENGE_TITLE = re.compile(
    r"just a moment|attention required|checking your browser|verify(?:ing)? (?:that )?you are (?:a )?human"
    r"|are you a robot|human verification|pardon our interruption|one more step|ddos protection|security check"
    r"|bot verification|checking (?:your )?connection",
    re.I)
# On an error status a plain denial page also counts.
_DENIAL_TITLE = re.compile(r"access denied|request blocked|forbidden", re.I)

_CHALLENGE_STATUSES = frozenset({202, 403, 405, 429, 503})
# A real page has more text than an interstitial.
_THIN_PAGE_CHARS = 1000
# Markers are searched in the start of the body only; interstitials are small.
_SCAN_CHARS = 65536


# Waiting rooms and queue pages. A site under load may answer every URL with one
# holding page ("You are now in line", "Hang Tight! Routing to checkout...")
# instead of its content. Like a challenge it says nothing about the site, so it
# is recorded as a waiting room and never analyzed as content. It is never
# retried, rendered or waited out.
#
# A page is a waiting room only when queue wording or a queue provider's marker
# comes with interstitial evidence: the page is thin, and it also has a refresh
# or script redirect, almost no links, a queue status code, or the same text as
# another holding page. Thinness, repeated HTML or a redirect alone describe an
# ordinary single-page app too, and a normal article about queue software is not
# thin. The queue wording must lead the page (title, first heading or opening
# text), not be an incidental phrase.
_QUEUE_WORDING = re.compile(
    r"waiting\s*room|virtual\s+queue|online\s+queue|you\s+are\s+(?:now\s+)?(?:in\s+(?:the\s+)?(?:queue|line)"
    r"|next\s+in\s+line)|you'?re\s+(?:now\s+)?in\s+(?:the\s+)?(?:queue|line)"
    r"|(?:your\s+)?(?:place|position)\s+in\s+(?:the\s+)?(?:queue|line)|estimated\s+wait(?:ing)?\s+time"
    r"|your\s+(?:estimated\s+)?wait\s+time|when\s+it'?s\s+your\s+turn"
    r"|(?:high|heavy|unusual)\s+(?:traffic|demand|volume)\b.{0,80}\b(?:queue|line|wait)"
    r"|routing\s+(?:you\s+)?to\s+(?:the\s+)?checkout",
    re.I | re.S)
_QUEUE_PROVIDERS = (
    ("queue_it", re.compile(r"queue-it\.net|queueit|queue-it", re.I)),
    ("cloudflare_waiting_room", re.compile(r"/cdn-cgi/waitingroom|cf-waiting-room|cf_waitingroom", re.I)),
    ("crowdhandler", re.compile(r"crowdhandler", re.I)),
    ("akamai_waiting_room", re.compile(r"akamai[-_ ]?(?:waiting[-_ ]?room|visitor[-_ ]?prioritization)", re.I)),
    ("failover_page", re.compile(r"site-?failover|site-?down-?page|waiting-?room", re.I)),
)
_META_REFRESH = re.compile(r"<meta[^>]+http-equiv\s*=\s*[\"']?refresh", re.I)
_REFRESH = re.compile(r"location(?:\.href)?\s*=(?!=)|location\.(?:replace|assign|reload)\s*\(", re.I)
_QUEUE_STATUSES = frozenset({202, 429, 503})
# Opening visible text in which queue wording counts as leading the page.
_QUEUE_LEAD_CHARS = 300


def visible_digest(visible_text):
    """Stable short digest of a page's normalized visible text (lower case,
    whitespace collapsed, first 4,000 characters), for telling repeated holding
    pages apart from pages with their own content."""
    import hashlib
    normalized = " ".join((visible_text or "").lower().split())[:4000]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# A holding page can carry more than the thin-page limit of text (a list of
# support phone numbers per country, for example) and still be a holding page.
# Above that limit it is gated only on stronger evidence: queue wording in the
# title itself, a sentence saying this page will refresh or let the visitor in,
# and either a refresh mechanism, a queue status or almost no links. An article
# about queue software has the wording at most, never the holding message.
_HOLDING_MESSAGE = re.compile(
    r"(?:this\s+page|you)\s+will\s+(?:automatically\s+)?(?:refresh|reload|be\s+(?:redirected|admitted|let\s+in"
    r"|taken|brought))|(?:bring|take|let)\s+you\s+(?:in(?:to)?|to|through)\s+(?:the\s+)?(?:web\s*)?site"
    r"|(?:do\s+not|don'?t|please\s+do\s+not)\s+(?:refresh|reload|close)\s+(?:this|the|your)\s+(?:page|window|browser)"
    r"|(?:up\s+and\s+(?:running|moving)|back\s+online)\s+shortly",
    re.I)
_LONG_HOLDING_CHARS = 6000


def _long_holding_page(status, body, title, visible, internal_links):
    if len(visible) >= _LONG_HOLDING_CHARS or not _QUEUE_WORDING.search(title or ""):
        return []
    if not _HOLDING_MESSAGE.search(visible[:_LONG_HOLDING_CHARS]):
        return []
    corroboration = []
    if _META_REFRESH.search(body):
        corroboration.append("meta_refresh")
    elif _REFRESH.search(body):
        corroboration.append("script_redirect")
    if internal_links <= 2:
        corroboration.append("few_links")
    if status in _QUEUE_STATUSES:
        corroboration.append(f"status_{status}")
    if not corroboration:
        return []
    return ["queue_wording", "holding_message"] + corroboration


def waiting_room_signals(status, body_text, title=None, headings=(), visible_text="", internal_links=0,
                         seen_digests=()):
    """Names of the waiting-room signals a response shows; empty for a normal page.
    seen_digests holds visible_digest values of holding pages already met."""
    visible = " ".join((visible_text or "").split())
    body = (body_text or "")[:_SCAN_CHARS]
    if len(visible) >= _THIN_PAGE_CHARS:
        return _long_holding_page(status, body, title, visible, internal_links)
    lead = " ".join([title or ""] + [h or "" for h in list(headings)[:2]] + [visible[:_QUEUE_LEAD_CHARS]])
    wording = bool(_QUEUE_WORDING.search(lead))
    providers = [name for name, pattern in _QUEUE_PROVIDERS if pattern.search(body)]
    if not wording and not providers:
        return []
    corroboration = []
    if _META_REFRESH.search(body):
        corroboration.append("meta_refresh")
    elif _REFRESH.search(body):
        corroboration.append("script_redirect")
    if internal_links <= 2:
        corroboration.append("few_links")
    if status in _QUEUE_STATUSES:
        corroboration.append(f"status_{status}")
    if visible and visible_digest(visible) in set(seen_digests or ()):
        corroboration.append("repeated_holding_page")
    # A provider's script without queue wording is injected into normal pages
    # too (a thin app shell has few links and inline redirects as well), so it
    # needs evidence a normal page does not have.
    strong = {"meta_refresh", "repeated_holding_page"} | {f"status_{s}" for s in _QUEUE_STATUSES}
    if not corroboration or (not wording and not strong & set(corroboration)):
        return []
    return (["queue_wording"] if wording else []) + ["provider:" + name for name in providers] + corroboration


def challenge_signals(status, headers, body_text, title=None, visible_chars=None):
    """Names of the challenge signals a response shows; empty for a normal
    response. status is the HTTP status, headers a mapping, body_text the decoded
    body, title the page title and visible_chars the visible-text length (both
    optional; without visible_chars a 2xx page is judged by markers alone only
    when its body is small)."""
    signals = []
    lowered = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    for name, pattern in _CHALLENGE_HEADERS:
        if pattern.search(lowered.get(name, "")):
            signals.append("header:" + name)
    if signals:
        return signals
    body = (body_text or "")[:_SCAN_CHARS]
    title = title or ""
    if status in _CHALLENGE_STATUSES:
        signals += [name for name, pattern in _INTERSTITIAL_ONLY + _ON_ERROR_ONLY if pattern.search(body)]
        if _CHALLENGE_TITLE.search(title):
            signals.append("challenge_title")
        elif _DENIAL_TITLE.search(title) and signals:
            signals.append("denial_title")
        return signals
    if status is None or not 200 <= status < 300:
        return []
    thin = visible_chars < _THIN_PAGE_CHARS if visible_chars is not None else len(body_text or "") < 20000
    if not thin:
        return []
    signals += [name for name, pattern in _INTERSTITIAL_ONLY if pattern.search(body)]
    # A challenge title on a short 2xx page counts only beside a protection
    # marker: a real short page may be titled "Security check".
    if _CHALLENGE_TITLE.search(title) and (signals or any(p.search(body) for _, p in _ON_ERROR_ONLY)):
        signals.append("challenge_title")
    return signals
