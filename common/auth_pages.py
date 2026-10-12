"""auth_pages.py -- tells login and sign-in pages apart from public content.

The audit never signs in. A login page is public and readable, but judging it as
content produces false findings ("no JSON-LD", "no H1", "dead end"), so it is kept
out of the analysed sample and listed in coverage with its reasons instead.

Skipping a useful page costs more than auditing a login page, so ALL of these
must hold before a page is out of scope:
  1. it shows a visible password input;
  2. it is short: at most MAX_LOGIN_PAGE_CHARS characters of visible text, so a
     page with real copy next to a login box is always audited;
  3. it carries no entity structured data (Organization, Product, Article ...);
     page boilerplate such as WebPage or BreadcrumbList does not count;
  4. it shows one login signal: an auth path segment matched whole (/login,
     /wp-login.php, /sign-in; /author/ never matches), or a title or H1 that
     names logging in.
A home page with a login box in its header therefore stays in scope.
"""
import re
from urllib.parse import unquote, urlsplit

from structured_data import iter_nodes, types_of

MAX_LOGIN_PAGE_CHARS = 1500
_AUTH_SEGMENTS = frozenset({"login", "log-in", "log_in", "logon", "signin", "sign-in", "sign_in", "auth",
                            "sso", "oauth", "wp-login", "account-login", "session", "sessions"})
_SERVER_EXT = re.compile(r"\.(?:php|aspx?|jsp|html?|cfm|do|action)$")
_LOGIN_WORDS = re.compile(r"\b(?:log\s*-?\s*in|sign\s*-?\s*in|log\s*-?\s*on|anmelden|einloggen|connexion|"
                          r"iniciar\s+sesi[oó]n|accedi|inloggen)\b", re.I)
_BOILERPLATE = frozenset({"WebPage", "WebSite", "BreadcrumbList", "ListItem", "SearchAction", "EntryPoint",
                          "ReadAction", "PropertyValueSpecification", "SiteNavigationElement", "WebPageElement"})


def auth_path_segment(url):
    try:
        path = urlsplit(url or "").path
    except ValueError:
        return None
    for raw in path.split("/"):
        seg = _SERVER_EXT.sub("", unquote(raw).strip().lower())
        if seg in _AUTH_SEGMENTS:
            return seg
    return None


def login_page_signals(url, final_url, title, headings, heading_levels, features, jsonld_blocks=()):
    """The signals that make a fetched page a login page, or [] when it is in scope."""
    f = features or {}
    if not f.get("password_inputs"):
        return []
    visible = f.get("full_visible_chars")
    if not isinstance(visible, int) or visible > MAX_LOGIN_PAGE_CHARS:
        return []
    entity = {t for n in iter_nodes(list(jsonld_blocks or ())) for t in types_of(n)} - _BOILERPLATE
    if entity or set(f.get("microdata_types") or ()) - _BOILERPLATE:
        return []
    signals = ["password_input", "short_page"]
    seg = auth_path_segment(final_url) or auth_path_segment(url)
    if seg:
        signals.append("auth_path:" + seg)
    if title and _LOGIN_WORDS.search(title):
        signals.append("login_title")
    h1s = [h for h, lvl in zip(headings or (), heading_levels or ()) if lvl == 1]
    if any(_LOGIN_WORDS.search(h or "") for h in h1s):
        signals.append("login_h1")
    return signals if len(signals) > 2 else []
