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
    r"|bot verification",
    re.I)
# On an error status a plain denial page also counts.
_DENIAL_TITLE = re.compile(r"access denied|request blocked|forbidden", re.I)

_CHALLENGE_STATUSES = frozenset({202, 403, 405, 429, 503})
# A real page has more text than an interstitial.
_THIN_PAGE_CHARS = 1000
# Markers are searched in the start of the body only; interstitials are small.
_SCAN_CHARS = 65536


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
