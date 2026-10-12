"""One-pass stdlib HTML extraction. Markup observations are not rendered UX facts."""
from html.parser import HTMLParser
from urllib.parse import urlsplit
import re

_VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
_TEXT_TAGS = {'a','button','p','h1','h2','h3','h4','h5','h6','span','time'}
_JS_TYPES = ('','text/javascript','application/javascript','module')
# Class, id or itemprop tokens that mark a byline or author block.
_AUTHOR_TOKEN = re.compile(r'(?:^|[\s_-])(?:author|authors|byline|by-line|writer|contributor)(?:$|[\s_-])', re.I)
_CHROME_TAGS = ('header','nav','footer')
# <noscript> wording that only says JavaScript is required, as opposed to real
# fallback content.
_JS_REQUIRED = re.compile(r'enable\s+javascript|javascript\s+(?:is\s+)?(?:required|disabled|turned\s+off|must\s+be\s+enabled)'
                          r'|(?:requires?|need)\s+(?:to\s+enable\s+)?javascript|turn\s+on\s+javascript|without\s+javascript', re.I)
# Private Use Area code points: icon-font glyphs written into the HTML as characters.
_PUA = re.compile('[-]')
# Ligature icon fonts render a word such as "shopping_cart" as an icon.
_LIGATURE_ICON = re.compile(r'(?:^|\s)material-(?:icons|symbols)(?:-[a-z]+)?(?:$|\s)', re.I)
_ICON_CLASS = re.compile(r'(?:^|\s)(?:fa[srlbdk]?|fa-[\w-]+|glyphicon[\w-]*|icon[\w-]*|bi|bi-[\w-]+|material-(?:icons|symbols)[\w-]*|dashicons[\w-]*|ti|ti-[\w-]+)(?:$|\s)', re.I)
# Consent-management platforms and generic cookie or consent banner markup.
CONSENT_TOKEN = re.compile(r'onetrust|cookiebot|cybotcookiebot|cookie[-_]?(?:consent|banner|notice|law|bar|popup|wall)'
                           r'|gdpr|cc-window|cc-banner|didomi|qc-cmp|truste|usercentrics|osano|termly|cookieyes'
                           r'|cky-consent|iubenda|cmplz|klaro|borlabs|consent[-_]?(?:banner|manager|modal|popup|wall)', re.I)
# Question-shaped heading text: it ends with a question mark, or it opens with a
# question word followed by a verb that makes it a question ("What is", "How do",
# "Can I"). A question word alone is not enough: "How it works", "How to style",
# "What we offer" and "Who we are" are section labels, not questions.
_QUESTION_MARK = re.compile('[?？]["\'’”)\\]]*$')
_QUESTION_AUX = (r'(?:is|are|was|were|do|does|did|can|could|should|would|will|shall|may|might|must'
                 r"|has|have|had|isn'?t|aren'?t|don'?t|doesn'?t|can'?t|won'?t)")
_QUESTION_LEAD = re.compile(
    r'^(?:(?:how|what|why|when|where|who|whom|whose|which)\s+' + _QUESTION_AUX + r'\b'
    r'|how\s+(?:much|many|long|often|old|far|big|soon|fast)\b'
    r'|' + _QUESTION_AUX + r'\s+(?:i|you|we|they|it|he|she|there|this|that|these|those|my|your|our|their|the|a|an)\b)',
    re.I)


# Client-side framework signs, for telling a page a script builds from a page
# that is merely short: framework bundle paths and names, framework attributes,
# and page state serialized for a script to render. A content hash in a file
# name ("site-bundle.17bbc1da.js") is only cache busting and is not counted.
_FRAMEWORK_SCRIPT = re.compile(r'/_next/|/_nuxt/|/static/js/|/_app/immutable/|/build/_assets/'
                               r'|(?:^|[/._-])(?:react|react-dom|vue|angular|svelte|preact|ember|gatsby)'
                               r'(?:[.\-_][\w.-]*)?\.m?js(?:[?#]|$)', re.I)
_FRAMEWORK_ATTRS = ('ng-app', 'ng-version', 'data-reactroot', 'data-v-app', 'data-server-rendered',
                    'data-sveltekit-hydrate')
_STATE_SCRIPT_IDS = frozenset({'__NEXT_DATA__', '__NUXT_DATA__', '__APOLLO_STATE__', 'ng-state', 'serverApp-state'})
_STATE_GLOBAL = re.compile(r'window\.__(?:INITIAL_STATE|PRELOADED_STATE|NUXT|APOLLO_STATE|REDUX_STATE|INITIAL_DATA)__\s*=')
# A JSON string literal of at least 20 characters with no markup or URL in it.
_STATE_PROSE = re.compile(r'"((?:[^"\\<>]|\\.){20,2000})"')
# Page data serialized into an element attribute (Inertia's data-page, React
# on Rails' data-react-props and similar). Named attributes always count as page
# state; another data-* attribute counts only when it holds JSON with readable
# prose, so a large settings or tracking blob is never taken for hidden content.
_STATE_ATTRS = frozenset({'data-page', 'data-props', 'data-react-props', 'data-state', 'data-initial-state',
                          'data-server-state', 'data-hydrate', 'data-hypernova-props'})
_STATE_ATTR_NAMED_MIN = 200
_STATE_ATTR_GENERIC_MIN = 2000
_STATE_ATTR_PROSE_MIN = 200
_STATE_ATTR_MAX_INSPECTED = 5
_STATE_ATTR_MAX_CHARS = 200_000
_STATE_JSON_MAX_ITEMS = 5000
_STATE_JSON_MAX_DEPTH = 12
_STATE_TEXT_CAP = 20000


def state_prose_chars(text, cap=_STATE_TEXT_CAP):
    """(characters of readable prose, limited) in serialized page data: string
    values of four or more words. JSON is parsed when it can be and walked with a
    depth and item limit; otherwise quoted strings are matched. Nothing is
    executed. limited is True when a limit cut the walk short."""
    import json
    chars = 0
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        for m in _STATE_PROSE.finditer(text):
            if chars >= cap:
                return cap, True
            if len(m.group(1).split()) >= 4:
                chars += len(m.group(1))
        return min(chars, cap), False
    stack = [(data, 0)]
    items = 0
    while stack:
        value, depth = stack.pop()
        items += 1
        if items > _STATE_JSON_MAX_ITEMS or chars >= cap:
            return min(chars, cap), True
        if isinstance(value, str):
            if len(value.split()) >= 4:
                chars += len(value)
        elif depth >= _STATE_JSON_MAX_DEPTH:
            if isinstance(value, (dict, list)) and value:
                return min(chars, cap), True
        elif isinstance(value, dict):
            stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            stack.extend((v, depth + 1) for v in value)
    return min(chars, cap), False


# Wording that marks a form as an email subscription: on its submit control, in
# its action URL, or in the id, class or name of the form or its email field.
_SIGNUP_WORDS = re.compile(r'subscri|newsletter|sign[\s_-]?up|join\s+(?:our|the)\s+(?:list|mailing|newsletter|community)'
                           r'|mailing[\s_-]?list|e-?mail[\s_-]?(?:updates|list|alerts)|stay\s+(?:in\s+touch|updated|informed)'
                           r'|get\s+(?:updates|the\s+latest)|keep\s+me\s+(?:posted|updated)|notify\s+me|opt[\s_-]?in', re.I)


def is_signup_form(form):
    """True for an email subscription form: it has an email field, signup wording
    of its own and no password field (a password makes it an account form)."""
    if not form.get('email') or form.get('password'):
        return False
    words=' '.join([form.get('action',''),form.get('attrs',''),form.get('email_attrs','')]+list(form.get('labels') or ()))
    return bool(_SIGNUP_WORDS.search(words))


def is_question_heading(text):
    """True when heading text is phrased as a question (see _QUESTION_LEAD)."""
    text = ' '.join((text or '').split())
    return bool(text) and bool(_QUESTION_MARK.search(text) or _QUESTION_LEAD.match(text))
_HEADING_TAGS = frozenset({'h1','h2','h3','h4','h5','h6'})
# Field names that site-search forms conventionally use.
_SEARCH_FIELD_NAMES = {'q','s','query','search','keyword','keywords','term','searchterm','search_query','search-term'}
# Raw-HTML hints of a search feature that JavaScript may build after load: an id,
# class or accessible name that starts with "search" (not "research"), an
# OpenSearch <link rel="search">, or a relative link to a search page.
_SEARCH_TOKEN = re.compile(r'(?<![a-z])search', re.I)
_SEARCH_PATH = re.compile(r'^/(?:[\w-]+/)?search(?:[/?#]|$)', re.I)
# Raw-HTML hints of saved-state widgets (wishlist, recently viewed, save for
# later) that JavaScript fills in after load: mount points, data attributes,
# script and stylesheet URLs, and inline script configuration.
_SAVED_STATE_HINT = re.compile(r'wish[-_ ]?list|recently[-_ ]?viewed|save[-_ ]?for[-_ ]?later|saved[-_ ]?items', re.I)
# Postal addresses written as plain text. A label such as "Address:" or "Visit us
# at" followed by text, or a street line ("12 High Street") followed by a postal
# code or a comma and a place name. Email, IP and web addresses are not postal.
_ADDRESS_LABEL = re.compile(
    r'(?<![\w@.-])(?<!e-mail )(?<!email )(?<!e-mail: )(?<!ip )(?<!web )(?<!mac )'
    r'(?:(?P<word>(?:registered |head |corporate |main |postal |mailing |office |our |business |campus |store )?address)'
    r'|(?P<phrase>registered office|head office|corporate office|visit us at|find us at))'
    r'(?P<sep>\s*[:\-]\s*|\s+)', re.I)
_ADDRESS_STOP = re.compile(r'\s(?:phone|tel|telephone|mobile|fax|e-?mail|call|hours|opening|open|follow|copyright)\b'
                           r'|[|\n•©]', re.I)
# Elements whose start or end separates blocks of text; a postal address is read
# within one block, so it never runs on into the next paragraph or list item.
_BLOCK_TAGS = frozenset({'p','div','li','ul','ol','dl','dt','dd','h1','h2','h3','h4','h5','h6','table','tr','td','th',
                         'section','article','header','footer','nav','main','aside','form','button','figure',
                         'figcaption','blockquote','pre','details','summary','body'})
_STREET_TYPES = (r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl|Court|Ct|Square|Sq'
                 r'|Parkway|Pkwy|Highway|Hwy|Terrace|Crescent|Marg|Nagar)\b')
_STREET_WORD = re.compile(r'\b' + _STREET_TYPES)
_STREET_LINE = re.compile(r'\b\d{1,5}[A-Za-z]?(?:[-/]\d{1,5})?,?[ \t]+(?:[A-Z][A-Za-z.\'-]*[ \t]+){0,4}'
                          + _STREET_TYPES + r'\.?')
_POSTAL_CODE = re.compile(r'\b\d{5}(?:-\d{4})?\b|\b[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}\b|\b[A-Z]\d[A-Z] ?\d[A-Z]\d\b'
                          r'|\b\d{3} ?\d{3}\b')
_PLACE_AFTER_COMMA = re.compile(r',\s*[A-Z][A-Za-z.\'-]+')


# Contact details written as visible text: email addresses, and phone numbers
# after a label ("Phone:", "Tel", "Call us on"). An "email" whose ending is an
# image extension is a retina file name such as logo@2x.png.
_EMAIL = re.compile(r'(?<![\w.+-])[A-Za-z0-9][\w.+-]{0,63}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.([A-Za-z]{2,24})(?![\w-])')
_IMAGE_TLD = frozenset({'png','jpg','jpeg','gif','svg','webp','avif','ico','bmp','tif','tiff'})
_PHONE_LABEL = re.compile(r'(?<![\w])(?:phone|tel|telephone|call(?: us)?(?: on| at)?|mobile|toll[- ]free|helpline|hotline)'
                          r'[ \t]*[:.]?[ \t]*(\+?\(?\d[\d \t().-]{5,22}\d)', re.I)
# Bounds on the text scanned for addresses and contact details. A page is at most
# MAX_RESPONSE_BYTES of HTML, so this keeps a pathological page from costing
# seconds while covering the whole visible text of almost every real page.
_SCAN_HEAD = 250_000
_SCAN_TAIL = 250_000


def find_contact_details(text, limit=5):
    """{'emails': [...], 'phones': [...]}: up to limit of each written as plain
    visible text. Phones count only after a label and with 7 to 15 digits."""
    emails, phones = [], []
    for m in _EMAIL.finditer(text):
        email = m.group(0).rstrip('.').lower()
        if m.group(1).lower() not in _IMAGE_TLD and email not in emails:
            emails.append(email)
            if len(emails) >= limit:
                break
    for m in _PHONE_LABEL.finditer(text):
        number = ' '.join(m.group(1).split())
        if 7 <= sum(c.isdigit() for c in number) <= 15 and number not in phones:
            phones.append(number)
            if len(phones) >= limit:
                break
    return {'emails': emails, 'phones': phones}


def _clean_address(candidate):
    """Postal-address candidate cut at the next phone, email or hours label, or
    None when it does not look like a street address: under three words, no
    digit, fewer than two words of letters, an email or web address, or none of
    a comma, a street word and a postal code."""
    stop = _ADDRESS_STOP.search(candidate)
    text = (candidate[:stop.start()] if stop else candidate).strip(' ,;:-')
    if '@' in text or re.search(r'https?:|www\.', text, re.I) or not re.search(r'\d', text):
        return None
    words = text.split()
    if len(words) < 3 or sum(bool(re.fullmatch(r'[A-Za-z][A-Za-z.\'-]{2,}', w.strip(',.'))) for w in words) < 2:
        return None
    if ',' not in text and not _STREET_WORD.search(text) and not _POSTAL_CODE.search(text):
        return None
    return text[:120]


def find_postal_addresses(text, limit=3):
    """Up to limit postal addresses written as plain text in visible page text."""
    found = []
    for m in _ADDRESS_LABEL.finditer(text):
        sep = m.group('sep')
        rest = text[m.end():m.end() + 160]
        # Without a colon or dash, "Address" must be a capitalised label followed
        # by a number or a capitalised word, so the verb ("address the issue") and
        # prose do not count.
        if m.group('word') and not sep.strip() and not (
                m.group(0)[0].isupper() and (rest[:1].isdigit() or rest[:1].isupper())):
            continue
        address = _clean_address(rest)
        if address and address not in found:
            found.append(address)
            if len(found) >= limit:
                return found
    for m in _STREET_LINE.finditer(text):
        after = text[m.end():m.end() + 100]
        postal = _POSTAL_CODE.search(after)
        if postal:
            end = m.end() + postal.end()
        elif _PLACE_AFTER_COMMA.match(after):
            end = m.end() + _PLACE_AFTER_COMMA.match(after).end()
        else:
            continue
        address = _clean_address(text[m.start():end])
        if address and not any(address in f or f in address for f in found):
            found.append(address)
            if len(found) >= limit:
                return found
    for m in _POSTAL_CODE.finditer(text):
        address = _clean_address(_comma_address(text, m) or '')
        if address and not any(address in f or f in address for f in found):
            found.append(address)
            if len(found) >= limit:
                break
    return found


def _comma_address(text, postal):
    """An address written as three or more short comma-separated parts that
    each start with a capital letter or a digit and end in a postal code
    ("Sector 62, Noida, Uttar Pradesh 201301"), or None. A part before the
    last must hold a number or a street word, or the last must be a US state
    and ZIP code, so a list of names followed by a number does not count."""
    window = text[max(0, postal.start() - 140):postal.end()]
    window = re.split(r'\.\s|[|:;\n•©]', window)[-1]
    kept = []
    for part in reversed(window.split(',')):
        part = part.strip()
        if not part or not (part[0].isupper() or part[0].isdigit()) or len(part.split()) > 6:
            break
        kept.append(part)
    if len(kept) < 3:
        return None
    kept.reverse()
    if not (any(re.search(r'\d', p) or _STREET_WORD.search(p) for p in kept[:-1])
            or re.search(r'\b[A-Z]{2} \d{5}(?:-\d{4})?$', kept[-1])):
        return None
    return ', '.join(kept)
_SCROLL_LOCK_CLASS =re.compile(r'(?:^|\s)(?:modal-open|no-scroll|noscroll|overflow-hidden|scroll-lock|disable-scroll|is-locked)(?:$|\s)', re.I)
_NAMED_COLORS = {'black':(0,0,0),'white':(255,255,255),'red':(255,0,0),'green':(0,128,0),'blue':(0,0,255),
                 'gray':(128,128,128),'grey':(128,128,128),'silver':(192,192,192),'yellow':(255,255,0),
                 'orange':(255,165,0),'navy':(0,0,128),'maroon':(128,0,0),'purple':(128,0,128),'teal':(0,128,128),
                 'olive':(128,128,0),'lime':(0,255,0),'aqua':(0,255,255),'cyan':(0,255,255),'fuchsia':(255,0,255),
                 'magenta':(255,0,255),'lightgray':(211,211,211),'lightgrey':(211,211,211),'darkgray':(169,169,169),
                 'darkgrey':(169,169,169),'gainsboro':(220,220,220),'whitesmoke':(245,245,245)}


def _style_value(style, prop):
    """Last declared value of one CSS property in an inline style, or None."""
    found = None
    for m in re.finditer(r'(?:^|;)\s*' + prop + r'\s*:\s*([^;]+)', style or '', re.I):
        found = m.group(1).strip().lower().replace('!important', '').strip()
    return found


def parse_color(value):
    """(r, g, b) for an opaque CSS colour, or None for anything else (alpha below
    1, variables, gradients, keywords such as inherit or transparent)."""
    if not value:
        return None
    v = value.strip().lower()
    if v in _NAMED_COLORS:
        return _NAMED_COLORS[v]
    m = re.fullmatch(r'#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})', v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            if len(h) == 4 and h[3] != 'f':
                return None
            return tuple(int(c * 2, 16) for c in h[:3])
        if len(h) == 8 and h[6:] != 'ff':
            return None
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r'rgba?\(\s*([^)]*)\)', v)
    if not m:
        return None
    parts = [p for p in re.split(r'[\s,/]+', m.group(1)) if p]
    if len(parts) not in (3, 4):
        return None
    if len(parts) == 4:
        alpha = parts[3]
        try:
            a = float(alpha[:-1]) / 100 if alpha.endswith('%') else float(alpha)
        except ValueError:
            return None
        if a < 1:
            return None
    rgb = []
    for p in parts[:3]:
        try:
            n = float(p[:-1]) * 2.55 if p.endswith('%') else float(p)
        except ValueError:
            return None
        if not 0 <= n <= 255:
            return None
        rgb.append(round(n))
    return tuple(rgb)


def _background_color(style):
    """Opaque background colour from background-color or a plain background
    shorthand; None when an image or gradient may sit behind the text."""
    value = _style_value(style, 'background-color')
    if value is None:
        value = _style_value(style, 'background')
        if value is None or 'url(' in value or 'gradient' in value:
            return None
        for token in re.findall(r'#[0-9a-f]+|rgba?\([^)]*\)|[a-z]+', value):
            color = parse_color(token)
            if color:
                return color
        return None
    if 'url(' in value or 'gradient' in value:
        return None
    return parse_color(value)


def contrast_ratio(fg, bg):
    """WCAG 2 contrast ratio between two sRGB colours."""
    def lum(c):
        ch = [x / 255 for x in c]
        ch = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in ch]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _px(value):
    """CSS length in px for px or pt values, else None."""
    m = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(px|pt)', (value or '').strip().lower())
    if not m:
        return None
    n = float(m.group(1))
    return n * 4 / 3 if m.group(2) == 'pt' else n


def _large_text(style, tag):
    """WCAG large text: at least 24px, or at least 18.66px and bold."""
    size = _px(_style_value(style, 'font-size') or '')
    if size is None:
        size = {'h1': 32.0, 'h2': 24.0}.get(tag)
    if size is None:
        return False
    weight = _style_value(style, 'font-weight') or ''
    bold = weight in ('bold', 'bolder') or (weight.isdigit() and int(weight) >= 700) or tag in ('b', 'strong', 'h1', 'h2', 'h3')
    return size >= 24 or (bold and size >= 18.66)

def _positive_int(value):
    return bool(re.fullmatch(r'[0-9]{1,9}', value or '')) and int(value) > 0

def _sized(a):
    """True when markup reserves space: width and height attributes, or an inline
    style that sets a height or an aspect ratio."""
    if _positive_int(a.get('width','')) and _positive_int(a.get('height','')):
        return True
    return bool(re.search(r'(?:^|;|\s)(?:aspect-ratio|height)\s*:', a.get('style',''), re.I))

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.node_count=0
        self.stack=[];self.text=[];self.title_parts=[];self.meta={};self.canonical=None
        self.links=[];self.headings=[];self.heading_levels=[];self.paragraphs=[];self.jsonld=[]
        self.breadcrumb=[];self.scripts=0;self.spa=False;self.has_nav=False;self.lang=None
        self.images=0;self.missing_alt=0;self.forms=0;self.email_capture=False;self.search=False
        self.buttons=[];self.media=0;self.details=0;self.overlay=False;self.microdata=False
        self.landmarks=set();self.head_blocking_scripts=0;self.images_missing_dims=0;self.images_lazy=0
        self.canonicals=[];self.paragraph_text=[];self.image_records=[]
        # Text alternatives for media, authorship, list structure and loading hints.
        self.media_records=[];self.bylines=[];self.author_links=[];self.microdata_types=[]
        self.ordered_lists=0;self.max_ordered_list_items=0
        self.lcp_image=None;self.blocking_stylesheets=0;self.preload_images=0
        self.script_hosts=set();self.external_scripts=0;self.inline_script_bytes=0;self.embeds_missing_dims=0
        # Language alternates, noscript fallback, text drawn in graphics, accessibility
        # and overlay observations. All are bounded lists or counters.
        self.hreflang=[];self.noscript_parts=[];self.inline_svg_parts=[];self.canvases=[]
        self.pua_chars=0;self.pua_samples=[];self.icon_ligatures=[]
        self.controls=0;self.unnamed_controls=[];self.unnamed_control_count=0
        self.form_fields=[];self.label_for=set()
        self.contrast_checked=0;self.contrast_issues=[];self.small_targets=[]
        self.consent_markup=[];self.modal_dialogs=[];self.scroll_lock=False;self.fullscreen_fixed=0
        self._noscript_len=0;self._svg_len=0
        self._script=None
        # Answer formats (tables, lists, question headings with the text that follows
        # them), location and site-search observations, and icon links for the logo.
        self.tables=[];self.definition_lists=0;self.unordered_lists=0
        self.question_answers=[];self._qa=None
        # Text or aria-label of links to other pages, lowercased, so a heading that
        # repeats one (a news card whose link is an empty overlay labelled with the
        # headline) can be told apart from a question the page answers.
        self.link_labels=[]
        # Question-shaped H2/H3 headings this page answers, and headings that are
        # links to other pages (not counted as questions).
        self.question_heading_count=0;self.linked_question_headings=0;self.linked_headings=0
        self.address_text=[];self.icon_links=[];self.search_form=False
        # Hints of features that JavaScript builds after load: a search box, and
        # saved-state widgets such as a wishlist or recently viewed items.
        self.search_hint=False;self.saved_state_hints=[]
        # Visible text with a newline between blocks, for the postal-address scan.
        self.flow=[]
        # Microdata or RDFa that states a telephone, email or contactPoint.
        self.contact_markup=False
        # Visible password inputs and the forms that hold them, for telling login
        # pages apart from public content (common/auth_pages.py).
        self.password_inputs=0;self.password_forms=[]
        # Every visible form (bounded), for telling a newsletter signup apart from
        # contact, search and login forms that also hold an email field.
        self.form_records=[]
        # Signs that a client-side framework builds the page: framework attributes
        # or bundle names, and page data serialized for a script to render.
        self.framework_hint=False;self.state_blob=False;self.state_text_chars=0
        # Where page state was found ('script#__NEXT_DATA__', 'attr:data-page'),
        # how many state attributes were inspected, and whether a bound cut it short.
        self.state_sources=[];self.state_attrs_inspected=0;self.state_extraction_limited=False
        # Scripts that run: external or inline JavaScript. JSON-LD and other data
        # blocks are not counted.
        self.executable_scripts=0
    def _add_state_source(self,label):
        if label not in self.state_sources and len(self.state_sources)<5:self.state_sources.append(label)
    def _observe_state_attrs(self,a):
        """Page data serialized into data-* attributes. Bounded: at most
        _STATE_ATTR_MAX_INSPECTED attributes per page, each read up to
        _STATE_ATTR_MAX_CHARS characters."""
        for name,value in a.items():
            if not name.startswith('data-') or self.state_text_chars>=_STATE_TEXT_CAP:continue
            named=name in _STATE_ATTRS
            if named:
                if len(value)<_STATE_ATTR_NAMED_MIN:continue
            elif len(value)<_STATE_ATTR_GENERIC_MIN or not value.lstrip().startswith(('{','[')):continue
            if self.state_attrs_inspected>=_STATE_ATTR_MAX_INSPECTED:
                self.state_extraction_limited=True;return
            self.state_attrs_inspected+=1
            if len(value)>_STATE_ATTR_MAX_CHARS:self.state_extraction_limited=True
            prose,limited=state_prose_chars(value[:_STATE_ATTR_MAX_CHARS],_STATE_TEXT_CAP-self.state_text_chars)
            if limited:self.state_extraction_limited=True
            if named or prose>=_STATE_ATTR_PROSE_MIN:
                self.state_blob=True;self._add_state_source('attr:'+name[:40])
                self.state_text_chars=min(_STATE_TEXT_CAP,self.state_text_chars+prose)
    def _observe_auth(self,tag,a,frame):
        """Visible password inputs, and for each form that holds one: its action,
        its id, class and name, its submit labels and whether it sits in the page
        chrome (header, nav or footer). Runs after the frame is pushed."""
        if tag=='form':
            frame['form']={'action':a.get('action','').strip()[:300],
                           'attrs':' '.join(a.get(k,'') for k in ('id','class','name')).strip()[:200],
                           'labels':[],'in_chrome':any(f['tag'] in _CHROME_TAGS for f in self.stack[:-1])}
            if not frame['hidden'] and len(self.form_records)<20:self.form_records.append(frame['form'])
            return
        if tag!='input' or frame['hidden']:return
        kind=(a.get('type') or 'text').strip().lower()
        owner=self._open('form')
        form=owner.get('form') if owner is not None else None
        if kind=='email' and form is not None:
            form['email']=True
            # The email field's own name, id, placeholder and label say what it is for.
            words=' '.join(a.get(k,'') for k in ('name','id','placeholder','aria-label')).strip()
            if words:form['email_attrs']=(form.get('email_attrs','')+' '+words)[:300]
        if kind=='password':
            self.password_inputs+=1
            # Recorded when the password input is seen, so a form whose end tag
            # never arrives is still kept.
            if form is not None and not form.get('password'):
                form['password']=True
                if len(self.password_forms)<5:self.password_forms.append(form)
        elif kind in ('submit','image') and form is not None and len(form['labels'])<10:
            label=(a.get('value') or a.get('alt') or a.get('aria-label') or '').strip()
            if label:form['labels'].append(label[:80])
    def _block_break(self):
        if self.flow and self.flow[-1]!='\n':self.flow.append('\n')
    def _links_elsewhere(self,heading):
        """True when a link to another page carries this heading's text as its own
        text or aria-label: the heading is a teaser for that page. A label of at
        least 15 characters inside the heading counts, so a kicker joined to the
        headline ("FashionThe industry...") still matches."""
        text=' '.join((heading or '').lower().split())
        return bool(text) and any(label in text for label in self.link_labels)
    def _add_saved_state_hint(self,text):
        if len(self.saved_state_hints)>=5:return
        m=_SAVED_STATE_HINT.search(text or '')
        if m:
            hint=re.sub(r'[-_ ]','',m.group(0).lower())
            if hint not in self.saved_state_hints:self.saved_state_hints.append(hint)
    def _observe_hints(self,tag,a,rel):
        """Search and saved-state hints, read from hidden elements too: a widget
        that JavaScript opens or fills in later often starts out hidden."""
        idcls=a.get('id','')+' '+a.get('class','')
        href=a.get('href','').strip()
        if not self.search_hint and (
                (tag=='link' and 'search' in rel) or _SEARCH_TOKEN.search(idcls)
                or _SEARCH_TOKEN.search(a.get('aria-label','')) or (tag=='a' and _SEARCH_PATH.search(href))):
            self.search_hint=True
        sources=[idcls]+[k for k in a if k.startswith('data-')]
        if tag=='script':sources.append(a.get('src',''))
        if tag in ('a','link'):sources.append(href)
        self._add_saved_state_hint(' '.join(sources))
    def _open(self,*tags):
        """Innermost open frame whose tag is one of tags, or None."""
        return next((f for f in reversed(self.stack) if f['tag'] in tags),None)
    def _observe_start(self,tag,a,frame,rel):
        """Observations for language alternates, picture sources, text drawn in
        graphics, accessible names, form labels, inline contrast, target sizes and
        overlays. Runs after the frame is pushed, so frame is the current element."""
        style=a.get('style','');cls=a.get('class','')
        if tag=='link' and 'alternate' in rel and 'hreflang' in a and len(self.hreflang)<60:
            self.hreflang.append({'hreflang':a.get('hreflang','').strip()[:40],'href':a.get('href','').strip()[:500]})
        if tag=='picture':frame['source_types']=[]
        if tag=='source':
            picture=self._open('picture')
            if picture is not None and 'source_types' in picture and len(picture['source_types'])<10:
                kind=(a.get('type') or '').strip().lower()
                if not kind:
                    first=(a.get('srcset') or '').split(',')[0].strip().split(' ')[0].split('?')[0].lower()
                    kind=next((t for ext,t in (('.avif','image/avif'),('.webp','image/webp'),('.jxl','image/jxl')) if first.endswith(ext)),'')
                picture['source_types'].append(kind or 'unspecified')
        if tag=='label' and a.get('for','').strip() and len(self.label_for)<500:self.label_for.add(a['for'].strip())
        if frame['hidden']:return
        named=bool((a.get('aria-label') or a.get('aria-labelledby') or '').strip())
        if tag=='figcaption':frame['collect']=True
        if tag=='canvas':
            frame['collect']=True
            if len(self.canvases)<20:
                frame['canvas']={'width':a.get('width') or None,'height':a.get('height') or None,
                                 'label':named or bool(a.get('title','').strip()),'role':a.get('role','').lower() or None,
                                 'fallback_chars':0,'fallback_alt':False}
                self.canvases.append(frame['canvas'])
        if _LIGATURE_ICON.search(cls):frame['collect']=True;frame['ligature']=True
        if (tag=='a' and 'href' in a) or tag=='button':
            self.controls+=1
            frame['control']={'tag':tag,'named':named or bool(a.get('title','').strip()),
                              'icon':bool(_ICON_CLASS.search(cls)),'href':a.get('href','')[:200] if tag=='a' else None}
        else:
            owner=self._open('a','button')
            if owner is not None and owner is not frame and 'control' in owner:
                if tag in ('svg','img','i') or _ICON_CLASS.search(cls):owner['control']['icon']=True
                if named or (tag=='img' and a.get('alt','').strip()):owner['control']['named']=True
        if tag=='input':
            kind=(a.get('type') or 'text').strip().lower()
            if kind in ('button','image'):
                self.controls+=1
                label=a.get('value','') if kind=='button' else a.get('alt','')
                if not (named or label.strip() or a.get('title','').strip()):
                    self.unnamed_control_count+=1
                    if len(self.unnamed_controls)<20:self.unnamed_controls.append({'tag':'input','href':None,'icon':kind=='image','type':kind})
        else:
            kind=tag
        if tag in ('input','select','textarea') and kind not in ('hidden','submit','reset','button','image') and len(self.form_fields)<60:
            self.form_fields.append({'tag':tag,'type':kind,'id':a.get('id','').strip()[:80],'name':a.get('name','').strip()[:80],
                                     'labelled':named or bool(a.get('title','').strip()) or self._open('label') is not None,
                                     'placeholder':bool(a.get('placeholder','').strip())})
        if (tag in ('a','button') or (tag=='input' and kind in ('submit','button','image','reset'))) and len(self.small_targets)<20:
            width=_px(_style_value(style,'width') or '');height=_px(_style_value(style,'height') or '')
            if tag=='input' and kind=='image':
                width=width if width is not None else _px((a.get('width') or '')+'px');height=height if height is not None else _px((a.get('height') or '')+'px')
            if width is not None and height is not None and min(width,height)<24:
                self.small_targets.append({'tag':tag,'width':round(width,1),'height':round(height,1),'href':a.get('href','')[:200] or None})
        if style and tag not in _VOID:
            fg=parse_color(_style_value(style,'color'))
            bg=_background_color(style) if fg else None
            if fg and bg:
                frame['collect']=True
                frame['contrast']=(fg,bg,contrast_ratio(fg,bg),_large_text(style,tag))
        idcls=a.get('id','')+' '+cls
        consent=CONSENT_TOKEN.search(idcls)
        if consent and len(self.consent_markup)<8 and consent.group(0).lower() not in self.consent_markup:
            self.consent_markup.append(consent.group(0).lower())
        if (a.get('role','').lower() in ('dialog','alertdialog') or (tag=='dialog' and 'open' in a)) and len(self.modal_dialogs)<5:
            frame['collect']=True
            frame['dialog']={'tag':tag,'modal':a.get('aria-modal','').strip().lower()=='true','consent':bool(consent),'text':''}
            self.modal_dialogs.append(frame['dialog'])
        if tag in ('html','body'):
            overflow=(_style_value(style,'overflow') or '')+' '+(_style_value(style,'overflow-y') or '')
            if 'hidden' in overflow or _SCROLL_LOCK_CLASS.search(cls):self.scroll_lock=True
        if (_style_value(style,'position') or '')=='fixed':
            zero=lambda v:v is not None and re.fullmatch(r'0(?:px|%)?',v) is not None
            full=lambda v:v in ('100%','100vw','100vh','100dvh','100svh','100lvh')
            inset=_style_value(style,'inset')
            if (inset is not None and all(zero(p) for p in inset.split())) or (
                    zero(_style_value(style,'top')) and zero(_style_value(style,'left'))
                    and (zero(_style_value(style,'right')) or full(_style_value(style,'width')))
                    and (zero(_style_value(style,'bottom')) or full(_style_value(style,'height')))):
                self.fullscreen_fixed+=1
    def _observe_structure(self,tag,a,frame,rel):
        """Tables, lists, address blocks, icon links and site-search forms. A new
        heading ends the text collected as the answer to a question heading."""
        if re.fullmatch('h[1-6]',tag):
            # A question answered by its own subheadings (an H3 under an H2) is
            # structured, not unanswered; record the level that closed it.
            if self._qa is not None and not self._qa['parts']:self._qa['next_level']=int(tag[1])
            self._qa=None
        if tag=='link' and ('icon' in rel or 'apple-touch-icon' in rel) and a.get('href','').strip() and len(self.icon_links)<6:
            self.icon_links.append({'rel':' '.join(rel)[:40],'href':a['href'].strip()[:500],'sizes':a.get('sizes','').strip()[:20] or None})
        if frame['hidden']:return
        if a.get('role','').lower()=='search':self.search_form=True
        if tag=='form' and re.search(r'search|/s(?:$|[/?])|[?&]q=',a.get('action',''),re.I):self.search_form=True
        if tag=='input' and (a.get('type') or 'text').strip().lower() in ('text','search') and (
                a.get('name','').strip().lower() in _SEARCH_FIELD_NAMES or 'search' in a.get('placeholder','').lower()):
            self.search_form=True
        if tag=='address':frame['collect']=True
        if tag=='dl':self.definition_lists+=1
        if tag=='table':
            frame['table']={'rows':0,'max_cols':0,'header_cells':0,'caption':False,
                            'layout':a.get('role','').strip().lower() in ('presentation','none')}
        elif tag=='caption':
            table=self._open('table')
            if table is not None and 'table' in table:table['table']['caption']=True
        elif tag=='tr':
            table=self._open('table')
            if table is not None and 'table' in table:table['table']['rows']+=1;frame['cells']=0
        elif tag in ('td','th'):
            # Counted as cells open, because HTML lets </td> and </tr> be omitted.
            row=self._open('tr');table=self._open('table')
            if table is not None and 'table' in table:
                if row is not None and 'cells' in row:
                    row['cells']+=1
                    table['table']['max_cols']=max(table['table']['max_cols'],row['cells'])
                if tag=='th':table['table']['header_cells']+=1
    def handle_starttag(self,tag,attrs):
        self.node_count+=1
        if len(self.stack)>=256 or self.node_count>100000:
            raise ValueError("HTML structural parsing budget reached")
        a={k:(v or '') for k,v in attrs};hidden=('hidden' in a or a.get('aria-hidden','').lower()=='true' or bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',a.get('style',''),re.I)))
        frame={'tag':tag,'a':a,'text':[],'hidden':hidden or any(x['hidden'] for x in self.stack)}
        in_head=any(f['tag']=='head' for f in self.stack)
        rel=a.get('rel','').lower().split()
        authorish=('author' in rel or _AUTHOR_TOKEN.search(a.get('itemprop',''))
                   or _AUTHOR_TOKEN.search(a.get('class','')) or _AUTHOR_TOKEN.search(a.get('id','')))
        if authorish and not frame['hidden']:
            if tag in ('a','link') and 'author' in rel and a.get('href') and len(self.author_links)<10:
                self.author_links.append(a['href'][:300])
            if tag=='meta' and a.get('content') and len(self.bylines)<10:
                self.bylines.append(' '.join(a['content'].split())[:160])
            frame['capture']=True
        if tag not in _VOID:self.stack.append(frame)
        # A line break separates words ("12 High Street<br>Springfield"); without
        # this the element's collected text would join them.
        if tag=='br':
            for f in self.stack:f['text'].append(' ')
        self._observe_start(tag,a,frame,rel)
        self._observe_structure(tag,a,frame,rel)
        self._observe_hints(tag,a,rel)
        self._observe_auth(tag,a,frame)
        if tag in _BLOCK_TAGS:self._block_break()
        if not self.contact_markup and re.search(r'(?:^|[\s:/#])(?:telephone|email|contactpoint)(?:$|\s)',
                                                 (a.get('itemprop','')+' '+a.get('property','')).lower()):
            self.contact_markup=True
        if tag in ('main','article') and not frame['hidden']:self.landmarks.add(tag)
        if tag=='script' and a.get('src') and in_head:
            if a.get('type','').lower() in ('','text/javascript','application/javascript') and 'async' not in a and 'defer' not in a:
                self.head_blocking_scripts+=1
        if tag=='link' and 'canonical' in rel:self.canonicals.append(a.get('href',''))
        if tag=='link' and in_head and 'stylesheet' in rel and 'alternate' not in rel and 'disabled' not in a \
                and a.get('media','').strip().lower() not in ('print','not all'):
            self.blocking_stylesheets+=1
        if tag=='link' and 'preload' in rel and a.get('as','').lower()=='image':self.preload_images+=1
        if tag=='html':self.lang=a.get('lang')
        if tag=='meta':self.meta.setdefault((a.get('name') or a.get('property') or '').lower(),[]).append(a.get('content',''))
        if tag=='link' and 'canonical' in rel:self.canonical=a.get('href')
        if tag=='script':
            self.scripts+=1;self._script={'type':a.get('type','').lower(),'parts':[],'src':bool(a.get('src')),
                                          'id':a.get('id','').strip()}
            if a.get('src') and self._script['type'] in _JS_TYPES:
                self.external_scripts+=1;self.executable_scripts+=1
                src=a['src'].strip()
                if not self.framework_hint and _FRAMEWORK_SCRIPT.search(src):self.framework_hint=True
                if src.startswith(('http://','https://','//')) and len(self.script_hosts)<60:
                    try:host=(urlsplit(src if not src.startswith('//') else 'https:'+src).hostname or '').lower()
                    except ValueError:host=''
                    if host:self.script_hosts.add(host)
        if tag=='nav' or a.get('role')=='navigation':self.has_nav=True
        if a.get('id','').lower() in {'root','app','__next','___gatsby','app-root'}:self.spa=True
        if not self.framework_hint and (tag in ('app-root',) or any(k in a for k in _FRAMEWORK_ATTRS)):
            self.framework_hint=True
        self._observe_state_attrs(a)
        if 'itemscope' in a or 'typeof' in a:self.microdata=True
        if a.get('itemtype') and len(self.microdata_types)<30:
            for value in a['itemtype'].split()[:5]:
                name=value.rstrip('/').rsplit('/',1)[-1].rsplit('#',1)[-1]
                if name and name not in self.microdata_types:self.microdata_types.append(name[:80])
        if tag=='img':
            self.images+=1
            if not (re.fullmatch(r'[0-9]{1,9}',a.get('width','')) and int(a['width'])>0 and re.fullmatch(r'[0-9]{1,9}',a.get('height','')) and int(a['height'])>0):self.images_missing_dims+=1
            if a.get('loading','').lower()=='lazy':self.images_lazy+=1
            # An image inside <noscript> is a fallback for visitors without script
            # (usually a tracking pixel or a copy of a lazy-loaded image), not content.
            in_noscript=any(f['tag']=='noscript' for f in self.stack)
            # alt="" is valid for decorative images; only missing attributes count.
            if 'alt' not in a and a.get('role') not in ('presentation','none') and not in_noscript:self.missing_alt+=1
            # Bounded per-page record of visible images for the non-text media checks.
            src=(a.get('src') or a.get('data-src') or a.get('data-lazy-src') or a.get('srcset','').split(',')[0].strip().split(' ')[0]).strip()
            record=None
            if src and not src.lower().startswith('data:') and not frame['hidden'] and not in_noscript and len(self.image_records)<60:
                record={'src':src,'alt':a['alt'] if 'alt' in a else None,'title':a.get('title') or None,
                        'width':a.get('width') or None,'height':a.get('height') or None,
                        'role':a.get('role','').lower() or None}
                self.image_records.append(record)
            # Likely largest-paint image: the first visible content image outside the
            # page chrome that its own attributes do not declare tiny.
            small=any(_positive_int(a.get(k,'')) and int(a[k])<100 for k in ('width','height'))
            if (self.lcp_image is None and src and not frame['hidden'] and not in_head and not small
                    and not any(f['tag'] in _CHROME_TAGS for f in self.stack)):
                self.lcp_image={'src':src[:300],'loading':a.get('loading','').lower() or None,
                                'fetchpriority':a.get('fetchpriority','').lower() or None,
                                'width':a.get('width') or None,'height':a.get('height') or None,
                                'image_index':self.images}
                if record is not None:record['lcp']=True
            if record is not None:
                # Context for the image: responsive variants, its figure caption and the
                # text of a link around it. Captions and link text are filled in when the
                # enclosing element closes.
                record['srcset']=bool((a.get('srcset') or a.get('data-srcset') or '').strip())
                record['aria_label']=bool((a.get('aria-label') or a.get('aria-labelledby') or '').strip())
                record['in_main']=any(f['tag'] in ('main','article') for f in self.stack)
                record['in_chrome']=any(f['tag'] in _CHROME_TAGS for f in self.stack)
                picture=self._open('picture')
                if picture is not None:
                    record['picture_types']=list(picture.get('source_types',()))
                for owner in (self._open('figure'),self._open('a')):
                    if owner is not None and len(owner.setdefault('images',[]))<20:owner['images'].append(record)
            canvas=self._open('canvas')
            if canvas is not None and 'canvas' in canvas and a.get('alt','').strip():canvas['canvas']['fallback_alt']=True
        if tag=='form':self.forms+=1
        if tag=='input':
            self.email_capture |= a.get('type','').lower()=='email'
            self.search |= a.get('type','').lower()=='search'
            if a.get('type','').lower()=='submit':self.buttons.append(a.get('value',''))
        if tag in ('video','audio','iframe'):self.media+=1
        if tag in ('video','audio','iframe','embed','object') and len(self.media_records)<30:
            record={'tag':tag,'src':(a.get('src') or a.get('data-src') or a.get('data') or '').strip()[:500] or None,
                    'title':(a.get('title') or a.get('aria-label') or '').strip()[:200] or None,
                    'hidden':frame['hidden'],'sized':_sized(a),'tracks':[],
                    # A video that plays muted by itself with no controls is a moving
                    # background, not something a visitor watches or listens to.
                    'decorative':tag=='video' and 'autoplay' in a and 'muted' in a and 'controls' not in a}
            self.media_records.append(record)
            if tag in ('video','audio'):frame['media']=record
            if tag in ('video','iframe','embed','object') and not record['sized'] and not frame['hidden']:
                self.embeds_missing_dims+=1
        if tag in ('source','track'):
            owner=self._open('video','audio')
            if owner is not None and 'media' in owner:
                if tag=='source' and not owner['media']['src'] and a.get('src'):owner['media']['src']=a['src'].strip()[:500]
                if tag=='track' and len(owner['media']['tracks'])<10:
                    kind=a.get('kind','').strip().lower()
                    # Per the HTML spec a missing or unknown kind means subtitles.
                    owner['media']['tracks'].append(kind if kind in ('captions','subtitles','descriptions','chapters','metadata') else 'subtitles')
        if tag=='li':
            owner=self._open('ol','ul')
            if owner is not None:owner['items']=owner.get('items',0)+1
        if tag=='details':self.details+=1
        if not frame['hidden'] and re.search(r'newsletter-popup|modal-backdrop|interstitial|overlay-active',a.get('class',''),re.I):self.overlay=True
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in _VOID:self.handle_endtag(tag)
    def handle_data(self,data):
        tags={f['tag'] for f in self.stack}
        if 'script' in tags:
            if self._script:self._script['parts'].append(data)
            return
        if 'style' in tags or 'template' in tags:return
        if 'title' in tags:
            if 'svg' not in tags:self.title_parts.append(data);return
            # An SVG <title> names the graphic. It is neither the document title nor
            # visible text, but it does name a link or button the graphic sits in.
            if data.strip() and not any(f['hidden'] for f in self.stack):
                owner=self._open('a','button')
                if owner is not None and 'control' in owner:owner['control']['named']=True
            return
        if any(f['hidden'] for f in self.stack):return
        stripped=data.strip()
        if stripped:
            self.text.append(stripped);self.flow.append(stripped)
            qa=self._qa
            if qa is not None and qa['chars']<600 and not tags & _HEADING_TAGS:
                # Where the text after the heading starts: a table or list holds
                # items, not a sentence, so its length says nothing about an answer.
                if not qa['parts']:qa['starts_in']='table' if tags & {'td','th'} else 'list' if tags & {'li','dt','dd'} else 'text'
                qa['parts'].append(stripped);qa['chars']+=len(stripped)+1
            if 'noscript' in tags and self._noscript_len<8000:
                self.noscript_parts.append(stripped);self._noscript_len+=len(stripped)+1
            if 'svg' in tags and tags & {'text','tspan','textpath'} and self._svg_len<8000:
                self.inline_svg_parts.append(stripped);self._svg_len+=len(stripped)+1
            glyphs=len(_PUA.findall(stripped))
            if glyphs:
                self.pua_chars+=glyphs
                if len(self.pua_samples)<5 and self.stack:
                    top=self.stack[-1]
                    self.pua_samples.append('<'+top['tag']+(' class="'+top['a'].get('class','')[:60]+'"' if top['a'].get('class') else '')+'>')
        for f in self.stack:
            if f['tag'] in _TEXT_TAGS or f.get('capture') or f.get('collect'):f['text'].append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self._script:
            if self._script['type']=='application/ld+json':self.jsonld.append(''.join(self._script['parts']))
            elif not self._script['src'] and self._script['type'] in _JS_TYPES:
                inline=sum(len(part) for part in self._script['parts'])
                self.inline_script_bytes+=inline
                if inline:self.executable_scripts+=1
            if not self._script['src'] and self._script['type'] in _JS_TYPES+('application/json',):
                self._add_saved_state_hint(''.join(self._script['parts'])[:100000])
            if not self._script['src'] and self._script['type']!='application/ld+json' and self.state_text_chars<20000:
                body=''.join(self._script['parts'])
                # Page data serialized for a script to render: a framework state
                # object, or a large JSON data block.
                if (self._script['id'] in _STATE_SCRIPT_IDS or _STATE_GLOBAL.search(body[:200000])
                        or (self._script['type']=='application/json' and len(body)>=2000)):
                    self.state_blob=True
                    self._add_state_source('script#'+self._script['id'][:40] if self._script['id']
                                           else 'script:'+(self._script['type'] or 'inline'))
                    if len(body)>200000:self.state_extraction_limited=True
                    # Prose inside it: string values of four or more words, the text a
                    # script will put on the page.
                    for m in _STATE_PROSE.finditer(body[:200000]):
                        if self.state_text_chars>=20000:self.state_extraction_limited=True;break
                        if len(m.group(1).split())>=4:self.state_text_chars+=len(m.group(1))
            self._script=None
        if tag in _BLOCK_TAGS:self._block_break()
        idx=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i]['tag']==tag),None)
        if idx is None:return
        frame=self.stack[idx];text=' '.join(''.join(frame['text']).split());a=frame['a']
        if tag=='ol' and frame.get('items',0)>=3:
            self.ordered_lists+=1;self.max_ordered_list_items=max(self.max_ordered_list_items,frame['items'])
        if tag=='ul' and frame.get('items',0)>=3 and not frame['hidden']:self.unordered_lists+=1
        if tag=='table' and 'table' in frame and not frame['hidden'] and len(self.tables)<20:
            self.tables.append(frame['table'])
        if tag=='address' and text and not frame['hidden'] and len(self.address_text)<5:
            self.address_text.append(text[:200])
        if not frame['hidden']:
            if tag=='a' and a.get('href'):
                self.links.append((a['href'],text))
                label=' '.join((a.get('aria-label') or text).lower().split())
                if not a['href'].strip().startswith('#') and len(label)>=15 and len(self.link_labels)<400:
                    self.link_labels.append(label)
                # Link text inside a heading, so a heading that is a link to another
                # page (a headline teaser on a news or listing page) can be told apart.
                heading=next((f for f in reversed(self.stack[:idx]) if f['tag'] in _HEADING_TAGS),None)
                if heading is not None:heading['link_chars']=heading.get('link_chars',0)+len(text)
            if re.fullmatch('h[1-6]',tag):
                self.headings.append(text);self.heading_levels.append(int(tag[1]))
                # A heading inside a link, or one whose text is mostly a link, names
                # another page; it is not a question this page answers.
                linked=(any(f['tag']=='a' and f['a'].get('href') for f in self.stack[:idx])
                        or (bool(text) and frame.get('link_chars',0)>=0.6*len(text)))
                if linked:self.linked_headings+=1
                # Collect the text after a question-shaped H2 or H3 until the next heading.
                if tag in ('h2','h3') and is_question_heading(text):
                    if linked:self.linked_question_headings+=1
                    else:
                        self.question_heading_count+=1
                        if len(self.question_answers)<20:
                            self._qa={'question':text[:200],'parts':[],'chars':0,'level':int(tag[1]),'next_level':None}
                            self.question_answers.append(self._qa)
            if tag=='p':
                self.paragraphs.append(len(text))
                if len(self.paragraph_text)<12:self.paragraph_text.append(text[:600])
            if tag=='button':
                self.buttons.append(text)
                owner=self._open('form')
                if owner is not None and 'form' in owner and len(owner['form']['labels'])<10:
                    label=text or (a.get('aria-label') or a.get('value') or '').strip()
                    if label:owner['form']['labels'].append(label[:80])
            if tag in ('a','span') and any('breadcrumb' in str(f['a']).lower() for f in self.stack):self.breadcrumb.append(text)
            if frame.get('capture') and text and len(self.bylines)<10:self.bylines.append(text[:160])
            control=frame.get('control')
            if control and not text and not control['named']:
                self.unnamed_control_count+=1
                if len(self.unnamed_controls)<20:
                    self.unnamed_controls.append({'tag':control['tag'],'href':control['href'],'icon':control['icon']})
            if 'contrast' in frame and text:
                fg,bg,ratio,large=frame['contrast'];required=3.0 if large else 4.5
                self.contrast_checked+=1
                if ratio<required and len(self.contrast_issues)<20:
                    self.contrast_issues.append({'text':text[:60],'ratio':round(ratio,2),'required':required,
                                                 'color':'#%02x%02x%02x'%fg,'background':'#%02x%02x%02x'%bg})
            if frame.get('ligature') and text and len(self.icon_ligatures)<20:self.icon_ligatures.append(text[:40])
            if 'dialog' in frame:frame['dialog']['text']=text[:300]
            if tag=='figcaption' and text:
                figure=next((f for f in reversed(self.stack[:idx]) if f['tag']=='figure'),None)
                if figure is not None:figure['caption']=text[:200]
        if 'canvas' in frame:frame['canvas']['fallback_chars']=len(text)
        if tag=='figure':
            for record in frame.get('images',()):record['caption']=frame.get('caption')
        if tag=='a':
            for record in frame.get('images',()):record['link_text']=text[:120]
        del self.stack[idx:]
    def features(self):
        return {'observation_version':2, 'landmarks':sorted(self.landmarks),
                'head_blocking_scripts':self.head_blocking_scripts,'images_missing_dims':self.images_missing_dims,
                'images_lazy':self.images_lazy,'canonical_values':self.canonicals[:20],
                'opening_paragraphs':self.paragraph_text,
                'full_visible_chars':len(' '.join(self.text)),
                'full_visible_bytes':len(' '.join(self.text).encode('utf-8')),
                'question_headings':self.question_heading_count,
                'linked_question_headings':self.linked_question_headings,
                'linked_headings':self.linked_headings,
                'viewport':self.meta.get('viewport',[]),'lang':self.lang,'has_nav':self.has_nav,
                'h1_count':self.heading_levels.count(1),'subheadings':sum(x>1 for x in self.heading_levels),
                'heading_levels':self.heading_levels[:200],'paragraph_lengths':self.paragraphs[:400],
                'buttons':self.buttons[:50],'anchors':self.links[:200],'scripts':self.scripts,'spa_mount':self.spa,
                'images':self.images,'missing_alt':self.missing_alt,'forms':self.forms,'email_capture':self.email_capture,
                'search':self.search,'media':self.media,'details':self.details,'overlay_pattern':self.overlay,
                'alternative_structured_markup':self.microdata,'meta':self.meta,
                'image_records':self.image_records,
                'media_records':self.media_records,'bylines':self.bylines,'author_links':self.author_links,
                'microdata_types':self.microdata_types,'ordered_lists':self.ordered_lists,
                'max_ordered_list_items':self.max_ordered_list_items,'lcp_image':self.lcp_image,
                'blocking_stylesheets':self.blocking_stylesheets,'preload_images':self.preload_images,
                'script_hosts':sorted(self.script_hosts),'external_scripts':self.external_scripts,
                'inline_script_bytes':self.inline_script_bytes,'embeds_missing_dims':self.embeds_missing_dims,
                'password_inputs':self.password_inputs,
                'signup_forms':sum(1 for f in self.form_records if is_signup_form(f)),
                'framework_hint':self.framework_hint,'state_blob':self.state_blob,
                'state_text_chars':self.state_text_chars,'state_sources':self.state_sources,
                'state_extraction_limited':self.state_extraction_limited,
                'executable_scripts':self.executable_scripts,
                'password_forms':[{k:(list(v) if k=='labels' else v) for k,v in f.items() if k!='password'}
                                  for f in self.password_forms],
                **self._extended_features()}
    def _extended_features(self):
        noscript=' '.join(self.noscript_parts)
        unlabeled=[f for f in self.form_fields if not f['labelled'] and not (f['id'] and f['id'] in self.label_for)]
        return {'hreflang':self.hreflang,
                'noscript_chars':len(noscript),'noscript_js_required':bool(_JS_REQUIRED.search(noscript)),
                'noscript_sample':noscript[:200],
                'inline_svg_text':' '.join(self.inline_svg_parts)[:4000],'canvases':self.canvases,
                'pua_chars':self.pua_chars,'pua_samples':self.pua_samples,'icon_ligatures':self.icon_ligatures,
                'controls':self.controls,'unnamed_control_count':self.unnamed_control_count,
                'unnamed_controls':self.unnamed_controls,'form_fields':len(self.form_fields),
                'unlabeled_fields':[{k:f[k] for k in ('tag','type','id','name')} for f in unlabeled if not f['placeholder']][:20],
                'unlabeled_field_count':sum(1 for f in unlabeled if not f['placeholder']),
                'placeholder_only_fields':sum(1 for f in unlabeled if f['placeholder']),
                'contrast_checked':self.contrast_checked,'contrast_issues':self.contrast_issues,
                'small_targets':self.small_targets,'consent_markup':self.consent_markup,
                'modal_dialogs':self.modal_dialogs,'scroll_lock':self.scroll_lock,'fullscreen_fixed':self.fullscreen_fixed,
                'tables':self.tables,'definition_lists':self.definition_lists,'unordered_lists':self.unordered_lists,
                'question_answers':[{'question':q['question'],'answer':' '.join(q['parts'])[:600],
                                     'answered_by_subheadings':bool(q['next_level'] and q['next_level']>q['level']),
                                     'teaser':self._links_elsewhere(q['question']),
                                     'starts_in':q.get('starts_in')}
                                    for q in self.question_answers],
                'address_text':self.address_text,'icon_links':self.icon_links,'search_form':self.search_form,
                **self._text_scans(),'running_text':self._running_text(),
                'search_hint':self.search_hint,'saved_state_hints':self.saved_state_hints,
                'contact_markup':self.contact_markup}
    def _text_scans(self):
        """Addresses and contact details written as plain text, read from the
        start and the end (the footer) of very long pages so the scan stays
        bounded."""
        text=' '.join(self.flow)
        if len(text)>_SCAN_HEAD+_SCAN_TAIL:text=text[:_SCAN_HEAD]+' \n '+text[-_SCAN_TAIL:]
        return {'postal_address_text':find_postal_addresses(text),'contact_text':find_contact_details(text)}
    def _running_text(self):
        """Blocks of at least 12 words, joined, at most 20,000 characters: the
        sentences of the page, without the labels, list items and link captions
        that repeat a word by design."""
        out=[];size=0
        for block in ' '.join(self.flow).split('\n'):
            words=block.split()
            if len(words)>=12:
                out.append(' '.join(words));size+=len(out[-1])+1
                if size>=20000:break
        return ' '.join(out)[:20000]
