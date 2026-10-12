"""access_guard.py -- tells a real page apart from a bot-protection interstitial.

Many sites put a web application firewall (WAF) or bot manager in front of their
content. To an automated client such as this audit, GPTBot or ChatGPT-User, the
firewall answers with a challenge or block page instead of the requested content.
That interstitial is not the site's content: analysing it as if it were produces
a cascade of false findings (no H1, dead ends, duplicate titles, missing
metadata). It is, however, strong evidence of a different and more serious
problem: automated readers -- including AI crawlers -- may never see the content.

classify_access() is a pure function over one HTTP response. Signatures are data,
not scattered conditionals, so new vendors can be added in one place.

The signature table has three tiers, because a bot manager being *present* is not
the same as a block page being *served*:

  interstitial  markers that appear only on a challenge or block page
                (`_cf_chl_opt`, `captcha-delivery.com`, `incapsula incident id`,
                `cf-mitigated: challenge`). These are specific enough to decide
                on their own, at any page length.
  weak          wording typical of an interstitial but possible elsewhere
                ("Just a moment...", "Access Denied", `server: cloudflare`).
                Two of them on a near-empty page, or one plus a refusing status,
                make a challenge.
  vendor        the vendor's own script, cookie or routine header, which a
                protected site serves on every ordinary page too
                (`/cdn-cgi/challenge-platform`, `challenges.cloudflare.com`
                for a Turnstile widget, `js.datadome.co`, `_Incapsula_Resource`,
                `awswaf`, `x-datadome: protected`). These NEVER classify a page
                by themselves: they only name the vendor, and only contribute
                when the server also refused the request.

That third tier is the point. A short, perfectly normal pricing page that loads
a DataDome tag used to be read as a challenge, which removed real content from
every downstream check and could raise a bot-wall finding against a site that
has no wall. A bot-manager script is not a block page.
"""
import re

# (vendor, interstitial patterns, weak patterns, vendor-presence patterns)
_SIGNATURES = (
    ("cloudflare",
     # Set only by the managed-challenge / block interstitial itself.
     (r"_cf_chl_opt", r"cf-browser-verification", r"cdn-cgi/l/chk_jschl", r"cf_chl_prog",
      r"window\._cf_chl_ctx"),
     (r"<title>\s*just a moment", r"attention required!? \| cloudflare",
      r"enable javascript and cookies to continue", r"sorry, you have been blocked",
      r"you are unable to access .{0,80}cloudflare"),
     # Served on ordinary pages of a Cloudflare site: JS Detections injects the
     # challenge-platform script, and challenges.cloudflare.com is also the
     # Turnstile widget host used on normal contact and sign-up forms.
     (r"/cdn-cgi/challenge-platform", r"challenges\.cloudflare\.com", r"\bturnstile\b")),
    ("akamai",
     (r"access denied.{0,400}reference\s*#\s*[\d.a-f]+",
      r"you don't have permission to access.{0,200}on this server"),
     (r"<title>\s*access denied\s*</title>",),
     (r"akam\.net", r"_abck=", r"ak_bmsc")),
    ("human_perimeterx",
     (r"px-captcha", r"blocked because we believe you are using automation tools",
      r"please verify you are a human.{0,120}press and hold"),
     (r"press\s*&\s*hold",),
     (r"_pxappid", r"\bperimeterx\b", r"px-cdn\.net", r"_px\d?=")),
    ("datadome",
     (r"captcha-delivery\.com", r"interstitial\.captcha-delivery", r"dd_cookie_test_"),
     (r"<title>\s*datadome\b",),
     (r"\bdatadome\b", r"js\.datadome\.co", r"datadome\.co/tags")),
    ("imperva",
     (r"incapsula incident id", r"request unsuccessful\.?\s*incident id"),
     (),
     (r"_incapsula_resource", r"incap_ses_", r"visid_incap_")),
    ("aws_waf",
     (r"captcha\.awswaf\.com", r"challenge\.awswaf\.com"),
     (),
     (r"\bawswaf\b", r"aws-waf-token")),
    ("generic",
     (r"<title>\s*client challenge\s*</title>",),
     (r"javascript is disabled in your browser", r"please enable javascript to (proceed|continue)",
      r"checking (if the site connection is secure|your browser)", r"verify (that )?you are (a )?human",
      r"<title>\s*(security check|bot verification|please wait)"),
     ()),
)

# Headers that only a challenge or block response carries.
_HEADER_INTERSTITIAL = (
    ("cloudflare", "cf-mitigated", r"challenge"),
    ("aws_waf", "x-amzn-waf-action", r"challenge|captcha|block"),
    ("datadome", "x-datadome", r"blocked|captcha|challenge|hardblock"),
)
# Headers that need a refusing status before they mean anything.
_HEADER_WEAK = (
    ("cloudflare", "server", r"cloudflare"),
    ("akamai", "server", r"akamaighost"),
)
# Headers a protected site sets on every ordinary response.
_HEADER_VENDOR = (
    ("datadome", "x-datadome", r"."),
    ("imperva", "x-iinfo", r"."),
    ("imperva", "x-cdn", r"incapsula"),
)

# Statuses that mean the server refused to serve the request. Only with one of
# these can a vendor's mere presence contribute to a challenge classification.
REFUSING_STATUSES = frozenset({401, 403, 405, 406, 429, 503})

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


def _header_hits(headers, table, status_filter=None):
    out = []
    for name, header, pattern in table:
        value = _header(headers, header)
        if value and re.search(pattern, value, re.I) and (status_filter is None or status_filter):
            out.append((name, f"header {header}: {value[:60]}"))
    return out


def classify_access(status_code, headers, body_text, visible_chars):
    """Return {"kind": "ok"|"challenge"|"rate_limited", "vendor": str|None,
    "signals": [..]}. Pure and deterministic."""
    body = (body_text or "")[:200_000].lower()
    if status_code == 429 or (_header(headers, "retry-after") and status_code in (429, 503)):
        return {"kind": "rate_limited", "vendor": None,
                "signals": [f"HTTP {status_code}" + (" with Retry-After" if _header(headers, "retry-after") else "")]}

    refused = status_code in REFUSING_STATUSES
    short = (visible_chars or 0) < CHALLENGE_MAX_VISIBLE_CHARS

    interstitial = _header_hits(headers, _HEADER_INTERSTITIAL)
    weak = _header_hits(headers, _HEADER_WEAK, status_filter=refused)
    vendor_present = _header_hits(headers, _HEADER_VENDOR)
    for name, inter_patterns, weak_patterns, vendor_patterns in _SIGNATURES:
        for pat in inter_patterns:
            if re.search(pat, body, re.S):
                interstitial.append((name, f"interstitial marker '{pat}'"))
        for pat in weak_patterns:
            if re.search(pat, body, re.S):
                weak.append((name, f"body matches '{pat}'"))
        for pat in vendor_patterns:
            if re.search(pat, body, re.S):
                vendor_present.append((name, f"{name} script or cookie present ('{pat}')"))

    # An interstitial marker is specific to a challenge page, so it decides on
    # its own. Everything below it needs the page to be near-empty, and the
    # vendor-presence tier additionally needs the server to have refused.
    if interstitial:
        hits = interstitial + weak
    elif len(weak) >= 2 and short:
        hits = weak
    elif weak and short and refused:
        hits = weak
    elif vendor_present and short and refused:
        # No interstitial marker, but the request was refused on a page served
        # behind a bot manager: an access problem, stated as exactly that.
        hits = vendor_present
    else:
        return {"kind": "ok", "vendor": None, "signals": []}

    vendor = next((n for n, _ in hits if n != "generic"), hits[0][0])
    signals = [f"HTTP {status_code}"] + [s for _, s in hits]
    if not interstitial:
        signals.append("no vendor-specific interstitial marker was present; "
                       "classified from the refusing status and the signals above")
    return {"kind": "challenge", "vendor": vendor, "signals": signals[:7]}


VENDOR_HINTS = {
    "cloudflare": "In Cloudflare, review Security > Bots (Bot Fight Mode / Super Bot Fight Mode, 'Block AI bots', AI Crawl Control) and add a WAF skip rule for verified bots and for /robots.txt, /sitemap*.xml and /llms.txt.",
    "akamai": "In Akamai Bot Manager, set the search-engine and AI-assistant bot categories to Allow or Monitor instead of Deny/Challenge.",
    "human_perimeterx": "In HUMAN Bot Defender, allowlist known good bots (search engines and AI assistants) and exempt robots/sitemap paths.",
    "datadome": "In DataDome, allow the 'search engine' and 'AI agent' good-bot categories you want to be discovered by.",
    "imperva": "In Imperva, allow the good-bot categories for search engines and AI crawlers and exempt robots/sitemap paths.",
    "aws_waf": "In AWS WAF Bot Control, allow verified bots in the search-engine and AI categories and exclude robots/sitemap paths from CAPTCHA/challenge actions.",
    "generic": "In your bot-management or WAF settings, allow verified search engine and AI crawlers and never challenge /robots.txt, /sitemap*.xml or /llms.txt.",
}
