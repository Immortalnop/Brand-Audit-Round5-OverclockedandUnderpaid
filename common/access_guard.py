"""access_guard.py -- tells a real page apart from a bot-protection interstitial.

Many sites put a web application firewall (WAF) or bot manager in front of their
content. To an automated client such as this audit, GPTBot or ChatGPT-User, the
firewall answers with a challenge or block page instead of the requested content.
That interstitial is not the site's content: analysing it as if it were produces
a cascade of false findings (no H1, dead ends, duplicate titles, missing
metadata). It is, however, strong evidence of a different and more serious
problem: automated readers -- including AI crawlers -- may never see the content.

classify_access() is a pure function over one HTTP response. Signatures are data,
not scattered conditionals, so new vendors can be added in one place. A response
is a challenge when it matches one STRONG signal, or at least two WEAK signals on a
near-empty page. A normal article that merely mentions "Cloudflare" matches no
strong signal and is long, so it is never classified as a challenge.
"""
import re

# (vendor, strong body/header patterns, weak patterns)
_SIGNATURES = (
    ("cloudflare",
     (r"_cf_chl_opt", r"challenges\.cloudflare\.com", r"cf-browser-verification", r"/cdn-cgi/challenge-platform"),
     (r"<title>\s*just a moment", r"attention required!? \| cloudflare", r"enable javascript and cookies to continue")),
    ("akamai",
     (r"access denied.{0,400}reference\s*#\s*[\d.a-f]+",),
     (r"<title>\s*access denied\s*</title>",)),
    ("human_perimeterx",
     (r"px-captcha", r"_pxappid", r"perimeterx"),
     (r"press\s*&\s*hold",)),
    ("datadome",
     (r"captcha-delivery\.com", r"datadome"),
     ()),
    ("imperva",
     (r"_incapsula_resource", r"incapsula incident id"),
     ()),
    ("aws_waf",
     (r"awswaf", r"aws-waf-token"),
     ()),
    ("generic",
     (r"<title>\s*client challenge\s*</title>",),
     (r"javascript is disabled in your browser", r"please enable javascript to (proceed|continue)",
      r"checking (if the site connection is secure|your browser)", r"verify (that )?you are (a )?human",
      r"<title>\s*(security check|bot verification|please wait)")),
)

_HEADER_STRONG = (
    ("cloudflare", "cf-mitigated", r"challenge"),
    ("datadome", "x-datadome", r"."),
    ("aws_waf", "x-amzn-waf-action", r"challenge|captcha|block"),
)
_HEADER_WEAK = (
    ("cloudflare", "server", r"cloudflare"),
    ("akamai", "server", r"akamaighost"),
)

# A challenge interstitial is short. Above this many visible characters a page is
# treated as real content even if a weak signal appears in it.
CHALLENGE_MAX_VISIBLE_CHARS = 1500


def _header(headers, name):
    if not headers:
        return ""
    for k, v in dict(headers).items():
        if str(k).lower() == name:
            return str(v)
    return ""


def classify_access(status_code, headers, body_text, visible_chars):
    """Return {"kind": "ok"|"challenge"|"rate_limited", "vendor": str|None,
    "signals": [..]}. Pure and deterministic."""
    signals, vendor = [], None
    body = (body_text or "")[:200_000].lower()
    if status_code == 429 or (_header(headers, "retry-after") and status_code in (429, 503)):
        return {"kind": "rate_limited", "vendor": None,
                "signals": [f"HTTP {status_code}" + (" with Retry-After" if _header(headers, "retry-after") else "")]}
    strong = []
    for name, header, pattern in _HEADER_STRONG:
        value = _header(headers, header)
        if value and re.search(pattern, value, re.I):
            strong.append((name, f"header {header}: {value[:60]}"))
    for name, strong_patterns, _ in _SIGNATURES:
        for pat in strong_patterns:
            if re.search(pat, body, re.S):
                strong.append((name, f"body matches '{pat}'"))
    weak = []
    for name, header, pattern in _HEADER_WEAK:
        value = _header(headers, header)
        if value and re.search(pattern, value, re.I) and status_code in (403, 503):
            weak.append((name, f"HTTP {status_code} from server: {value[:40]}"))
    for name, _, weak_patterns in _SIGNATURES:
        for pat in weak_patterns:
            if re.search(pat, body, re.S):
                weak.append((name, f"body matches '{pat}'"))
    short = (visible_chars or 0) < CHALLENGE_MAX_VISIBLE_CHARS
    if strong and short:
        vendor = strong[0][0]
        signals = [s for _, s in strong] + [s for _, s in weak]
    elif len(weak) >= 2 and short:
        vendor = next((n for n, _ in weak if n != "generic"), weak[0][0])
        signals = [s for _, s in weak]
    elif strong and status_code in (403, 503):
        # A blocked status plus a vendor-specific marker is a challenge even on a
        # verbose block page.
        vendor = strong[0][0]
        signals = [s for _, s in strong]
    if vendor:
        signals.insert(0, f"HTTP {status_code}")
        return {"kind": "challenge", "vendor": vendor, "signals": signals[:6]}
    return {"kind": "ok", "vendor": None, "signals": []}


VENDOR_HINTS = {
    "cloudflare": "In Cloudflare, review Security > Bots (Bot Fight Mode / Super Bot Fight Mode, 'Block AI bots', AI Crawl Control) and add a WAF skip rule for verified bots and for /robots.txt, /sitemap*.xml and /llms.txt.",
    "akamai": "In Akamai Bot Manager, set the search-engine and AI-assistant bot categories to Allow or Monitor instead of Deny/Challenge.",
    "human_perimeterx": "In HUMAN Bot Defender, allowlist known good bots (search engines and AI assistants) and exempt robots/sitemap paths.",
    "datadome": "In DataDome, allow the 'search engine' and 'AI agent' good-bot categories you want to be discovered by.",
    "imperva": "In Imperva, allow the good-bot categories for search engines and AI crawlers and exempt robots/sitemap paths.",
    "aws_waf": "In AWS WAF Bot Control, allow verified bots in the search-engine and AI categories and exclude robots/sitemap paths from CAPTCHA/challenge actions.",
    "generic": "In your bot-management or WAF settings, allow verified search engine and AI crawlers and never challenge /robots.txt, /sitemap*.xml or /llms.txt.",
}
