"""auth_pages.py -- tells login and sign-in pages apart from public content.

The audit never signs in, and the handout bans actions in authenticated areas.
A login page is still public and readable, but auditing it produces false
positives ("no JSON-LD on a login page"), so the crawl keeps it out of the
analyzed sample and lists it in coverage with the reason instead.

Skipping a useful page costs more than auditing a login page, so every one of
these must hold before a page is out of scope:
  1. it shows a visible password input;
  2. it is short: at most MAX_LOGIN_PAGE_CHARS characters of visible text, so a
     page with real copy next to its login form is always audited;
  3. it carries no structured data beyond page boilerplate (WebPage, WebSite,
     BreadcrumbList and the like): Organization, Product, Article or any other
     entity markup is evidence the audit uses, so such a page is kept;
  4. and one login signal:
     - an auth path: a path segment that is exactly an auth word (/login,
       /user/login, /wp-login.php, /sign-in). Segments are compared whole, so
       /author/ or /blog/login-tips never match;
     - the page title or an H1 names logging in ("Sign in", "Log in to Acme");
     - a login form (a password form whose action, id, class, name or submit
       label names logging in) outside the header, nav and footer.
A home page with a small login box in its header therefore stays in scope.
"""
import re
from urllib.parse import unquote, urlsplit

from structured_data import iter_nodes, types_of

# Whole path segments, compared after lower-casing and dropping a server-side
# file extension (wp-login.php -> wp-login).
_AUTH_SEGMENTS = frozenset({
    "login", "log-in", "log_in", "logon", "log-on", "signin", "sign-in", "sign_in",
    "auth", "authenticate", "authentication", "sso", "cas", "oauth", "oauth2", "saml",
    "wp-login", "register", "signup", "sign-up", "sign_up",
})
_SERVER_EXTENSION = re.compile(r"\.(?:php|aspx?|jsp|html?|cfm|do|action)$")

# Words that name logging in, in titles, headings and submit labels. Matched on
# word boundaries so "blogin" or "designing" never match.
_LOGIN_WORDS = re.compile(
    r"\b(?:log\s*-?\s*in|sign\s*-?\s*in|log\s*-?\s*on|sign\s*-?\s*on|anmelden|einloggen|"
    r"connexion|se\s+connecter|iniciar\s+sesi[oó]n|accedi|inloggen|logowanie)\b"
    r"|ログイン|登录|登入|로그인",
    re.I,
)
# Login tokens inside a form's id, class or name ("loginform", "signin-form").
_LOGIN_ATTR = re.compile(r"log[-_]?in|sign[-_]?in|log[-_]?on", re.I)

# A page with more visible text than this (nav and footer included) has real
# copy next to its login form and is always audited.
MAX_LOGIN_PAGE_CHARS = 1500

# Structured data that describes the page itself rather than any entity. Any
# other type (Organization, Product, Article, Event, FAQPage...) keeps the page.
_BOILERPLATE_TYPES = frozenset({
    "WebPage", "WebSite", "BreadcrumbList", "ListItem", "SearchAction", "EntryPoint",
    "ReadAction", "PropertyValueSpecification", "SiteNavigationElement", "WPHeader",
    "WPFooter", "WPSideBar", "WebPageElement",
})


def entity_markup_types(jsonld_blocks=(), microdata_types=()):
    """Structured-data types on a page that name an entity, not page boilerplate."""
    found = set()
    for node in iter_nodes(list(jsonld_blocks or ())):
        if hasattr(node, "get"):
            found |= types_of(node)
    found |= {t for t in microdata_types or () if isinstance(t, str)}
    return sorted(t for t in found if t and t not in _BOILERPLATE_TYPES)


def auth_path_segment(url):
    """The first path segment of url that is an auth word, or None."""
    try:
        path = urlsplit(url or "").path
    except ValueError:
        return None
    for raw in path.split("/"):
        segment = _SERVER_EXTENSION.sub("", unquote(raw).strip().lower())
        if segment in _AUTH_SEGMENTS:
            return segment
    return None


def names_login(text):
    return bool(text) and _LOGIN_WORDS.search(text) is not None


def is_login_form(form):
    """True when a password form's action, attributes or submit labels name logging in."""
    if auth_path_segment(form.get("action") or ""):
        return True
    if _LOGIN_ATTR.search(form.get("attrs") or ""):
        return True
    return any(names_login(label) for label in form.get("labels") or ())


def _h1_texts(headings, levels):
    return [h for h, level in zip(headings or (), levels or ()) if level == 1]


def login_page_signals(url, final_url, title, headings, features, jsonld_blocks=()):
    """The signals that make a fetched page a login page, or [] when it is in scope.

    url is the requested URL and final_url the URL after redirects; headings and
    features come from html_features.Document, jsonld_blocks are the page's parsed
    JSON-LD. Any doubt keeps the page in scope."""
    features = features or {}
    if not features.get("password_inputs"):
        return []
    visible = features.get("full_visible_chars")
    if not isinstance(visible, int) or visible > MAX_LOGIN_PAGE_CHARS:
        return []
    if entity_markup_types(jsonld_blocks, features.get("microdata_types")):
        return []
    signals = ["password_input", "short_page"]
    segment = auth_path_segment(final_url) or auth_path_segment(url)
    if segment:
        signals.append("auth_path:" + segment)
    if names_login(title) or any(names_login(h) for h in _h1_texts(headings, features.get("heading_levels"))):
        signals.append("login_title")
    login_forms = [f for f in features.get("password_forms") or () if is_login_form(f)]
    if login_forms:
        signals.append("login_form")
    main_form = any(not f.get("in_chrome") for f in login_forms)
    if main_form:
        signals.append("login_form_is_main_content")
    if segment or "login_title" in signals or main_form:
        return signals
    return []
