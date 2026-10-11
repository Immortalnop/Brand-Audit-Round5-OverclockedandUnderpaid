"""archetype_sites.py -- an offline corpus of site archetypes (Plan.md point 15).

Six small sites, each built the way that kind of site is usually built, with
known defects planted on purpose and known good practice that must not be
reported: a single-page app, an e-commerce shop, a local business, a
documentation site, a blog and a multi-language site.

Every site is served from 127.0.0.1 by serve(); nothing reaches the internet.
"HOST" in a page is replaced with the server's host and port. URLs on other
domains use the reserved .test top-level domain and are never requested.
"""
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ALLOW_ALL = "User-agent: *\nDisallow:\n"
# A date a month before the run: recent, never in the future.
RECENT = (date.today() - timedelta(days=30)).isoformat()


def _sitemap(paths):
    return ("<?xml version='1.0' encoding='UTF-8'?>"
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            + "".join(f"<url><loc>http://HOST{p}</loc></url>" for p in paths) + "</urlset>")


def _page(title, body, head="", lang="en", description=None):
    desc = f'<meta name="description" content="{description}">' if description else ""
    lang_attr = f' lang="{lang}"' if lang else ""
    return (f'<!doctype html><html{lang_attr}><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{title}</title>{desc}{head}</head><body>{body}</body></html>")


def _jsonld(text):
    return '<script type="application/ld+json">' + text + "</script>"


# ---------------------------------------------------------------------------
# 1. Single-page app. Every route is the same script shell: an empty mount
#    point, a bundle and a <noscript> that only says JavaScript is required.
#    Navigation uses hash routes. Defects: content needs JavaScript, hash
#    routing. Pages that need JavaScript must not be blamed for missing search,
#    tables or saved state, which the bundle may well build.
# ---------------------------------------------------------------------------
def _spa_shell(title):
    return _page(title, '<noscript>You need to enable JavaScript to run this app.</noscript>'
                        '<div id="root"></div><script src="/static/js/main.4f2a.js"></script>'
                        '<a href="#/pricing">Pricing</a> <a href="#/about">About</a>',
                 description="Plan team trips and share itineraries.")


SPA = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/pricing", "/about"]),
    "pages": {
        "/": _spa_shell("Tripboard"),
        "/pricing": _spa_shell("Tripboard pricing"),
        "/about": _spa_shell("About Tripboard"),
    },
    "assets": {"/static/js/main.4f2a.js": (b"document.getElementById('root').textContent='Tripboard';",
                                          "application/javascript")},
}


# ---------------------------------------------------------------------------
# 2. E-commerce shop. Server-rendered catalogue with a site search, a spec
#    table and Product markup on one product page. Defects: the second product
#    page has no Product markup and an image with no alt text. /cart is never
#    requested (sensitive route) and /login is a login page, fetched but not
#    analyzed.
# ---------------------------------------------------------------------------
_SHOP_NAV = ('<header><nav><a href="/">Home</a> <a href="/products/trail-kettle">Trail kettle</a> '
             '<a href="/products/camp-stove">Camp stove</a> <a href="/cart">Cart</a> '
             '<a href="/login">Sign in</a></nav>'
             '<form role="search" action="/search"><input type="search" name="q" aria-label="Search products">'
             '<button>Search</button></form></header>')
_SHOP_ORG = _jsonld('{"@context":"https://schema.org","@type":"Organization","name":"Ridgeway Outfitters",'
                    '"url":"http://HOST/","email":"help@ridgeway.test","telephone":"+1 555 201 3300"}')
_SHOP_COPY = ("Ridgeway Outfitters sells lightweight camping cookware tested on multi-day hikes. "
              "Every item ships within two days and comes with a two-year warranty. ")

SHOP = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/products/trail-kettle", "/products/camp-stove"]),
    "pages": {
        "/": _page("Ridgeway Outfitters camping cookware",
                   _SHOP_NAV + "<main><h1>Camping cookware that survives the trail</h1><p>" + _SHOP_COPY * 3
                   + '</p><p>Browse the <a href="/products/trail-kettle">trail kettle</a> or the '
                     '<a href="/products/camp-stove">camp stove</a>.</p></main>',
                   head=_SHOP_ORG, description="Lightweight camping cookware with a two-year warranty."),
        "/products/trail-kettle": _page(
            "Trail kettle 0.8 L | Ridgeway Outfitters",
            _SHOP_NAV + '<main><h1>Trail kettle 0.8 L</h1>'
            '<img src="/img/kettle.jpg" alt="Trail kettle with folding handle" width="600" height="600">'
            "<p>" + _SHOP_COPY * 2 + "</p><p>Price: $39.00</p>"
            "<table><caption>Specifications</caption><tr><th>Capacity</th><td>0.8 L</td></tr>"
            "<tr><th>Weight</th><td>210 g</td></tr><tr><th>Material</th><td>Titanium</td></tr></table></main>",
            head=_jsonld('{"@context":"https://schema.org","@type":"Product","name":"Trail kettle 0.8 L",'
                         '"image":"http://HOST/img/kettle.jpg","offers":{"@type":"Offer","price":"39.00",'
                         '"priceCurrency":"USD","availability":"https://schema.org/InStock"}}'),
            description="A 0.8 litre titanium kettle that weighs 210 g."),
        "/products/camp-stove": _page(
            "Camp stove | Ridgeway Outfitters",
            _SHOP_NAV + '<main><h1>Camp stove</h1><img src="/img/stove.jpg" width="600" height="600">'
            "<p>" + _SHOP_COPY * 2 + "</p><p>Price: $64.00</p>"
            "<table><tr><th>Output</th><td>2.6 kW</td></tr><tr><th>Weight</th><td>88 g</td></tr>"
            "<tr><th>Fuel</th><td>Butane and propane</td></tr></table></main>",
            description="A compact 2.6 kW camp stove that weighs 88 g."),
        "/login": _page("Sign in", '<main><form action="/login" method="post">'
                                           '<input name="email" type="email" aria-label="Email">'
                                           '<input name="password" type="password" aria-label="Password">'
                                           '<button>Sign in</button></form></main>'),
    },
}


# ---------------------------------------------------------------------------
# 3. Local business. A plumber whose address, phone and email are shown as
#    text and links, with a LocalBusiness block that names the business but
#    gives no address, phone or opening hours. Defects: the LocalBusiness
#    markup is incomplete and the contact details are not in markup.
# ---------------------------------------------------------------------------
_LOCAL_FOOTER = ('<footer><p>Harbour Plumbing<br>14 Quay Street<br>Portsmouth PO1 2AB</p>'
                 '<p>Call <a href="tel:+442392000111">023 9200 0111</a> or email '
                 '<a href="mailto:jobs@harbourplumbing.test">jobs@harbourplumbing.test</a></p>'
                 "<p>Open Monday to Saturday, 8am to 6pm.</p></footer>")
_LOCAL_COPY = ("Harbour Plumbing fixes leaks, boilers and blocked drains across Portsmouth and Southsea. "
               "Our engineers are Gas Safe registered and arrive within two hours for emergencies. ")
_LOCAL_BUSINESS = _jsonld('{"@context":"https://schema.org","@type":"Plumber","name":"Harbour Plumbing",'
                          '"url":"http://HOST/"}')

LOCAL = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/services", "/contact"]),
    "pages": {
        "/": _page("Harbour Plumbing, emergency plumber in Portsmouth",
                   '<header><nav><a href="/">Home</a> <a href="/services">Services</a> '
                   '<a href="/contact">Contact</a></nav></header><main><h1>Emergency plumber in Portsmouth</h1>'
                   "<p>" + _LOCAL_COPY * 3 + "</p></main>" + _LOCAL_FOOTER,
                   head=_LOCAL_BUSINESS, description="Emergency plumbing in Portsmouth, 24 hours a day."),
        "/services": _page("Plumbing services | Harbour Plumbing",
                           '<header><nav><a href="/">Home</a> <a href="/contact">Contact</a></nav></header>'
                           "<main><h1>Plumbing services</h1><ul><li>Boiler repair</li><li>Leak detection</li>"
                           "<li>Drain unblocking</li></ul><p>" + _LOCAL_COPY * 2 + "</p></main>" + _LOCAL_FOOTER,
                           description="Boiler repair, leak detection and drain unblocking."),
        "/contact": _page("Contact Harbour Plumbing",
                          '<header><nav><a href="/">Home</a> <a href="/services">Services</a></nav></header>'
                          "<main><h1>Contact us</h1><p>" + _LOCAL_COPY + "</p></main>" + _LOCAL_FOOTER,
                          description="Phone, email and address for Harbour Plumbing."),
    },
}


# ---------------------------------------------------------------------------
# 4. Documentation site. Long reference pages with a skipped heading level,
#    wall-of-text paragraphs and an llms.txt that lists a page which does not
#    exist. Good practice: a site search, TechArticle markup and llms.txt.
# ---------------------------------------------------------------------------
_DOCS_NAV = ('<header><nav><a href="/docs/">Docs home</a> <a href="/docs/getting-started">Getting started</a> '
             '<a href="/docs/api">API reference</a></nav><form role="search" action="/search">'
             '<input type="search" name="q" aria-label="Search the docs"></form></header>')
_DOCS_WALL = ("The client library wraps every endpoint of the Lumen API and handles authentication, retries, "
              "pagination and rate limits for you, so most applications never need to build a request by hand, "
              "and the same configuration object is shared by every call made from one process, which keeps "
              "connection pooling efficient and lets you set timeouts, proxies and custom headers in one place "
              "rather than repeating them for every request your application sends to the service. ") * 4
_DOCS_ORG = _jsonld('{"@context":"https://schema.org","@type":"Organization","name":"Lumen","url":"http://HOST/"}')


def _docs_article(headline):
    return _jsonld('{"@context":"https://schema.org","@type":"TechArticle","headline":"' + headline
                   + '","author":{"@type":"Organization","name":"Lumen"},"dateModified":"' + RECENT + '"}')


DOCS = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/docs/", "/docs/getting-started", "/docs/api"]),
    "llms": ("# Lumen\n\n> Developer documentation for the Lumen API.\n\n## Docs\n\n"
             "- [Getting started](/docs/getting-started): install and first request\n"
             "- [API reference](/docs/api): every endpoint\n"
             "- [Webhooks](/docs/webhooks): event delivery\n"),
    "pages": {
        "/": _page("Lumen API", _DOCS_NAV + '<main><h1>Lumen API</h1><p>Read the <a href="/docs/">documentation</a>'
                                            " to start building with the Lumen API.</p></main>",
                   head=_DOCS_ORG, description="The Lumen API for event analytics."),
        "/docs/": _page("Lumen documentation", _DOCS_NAV + "<main><h1>Documentation</h1><p>Start with "
                        '<a href="/docs/getting-started">getting started</a>, then read the '
                        '<a href="/docs/api">API reference</a>.</p></main>',
                        head=_docs_article("Lumen documentation"), description="Guides and API reference."),
        "/docs/getting-started": _page(
            "Getting started | Lumen docs",
            _DOCS_NAV + "<main><h1>Getting started</h1><h3>Install the client</h3><p>" + _DOCS_WALL
            + "</p><h3>Make your first request</h3><p>" + _DOCS_WALL + "</p>"
            '<p>Next, read the <a href="/docs/api">API reference</a>.</p></main>',
            head=_docs_article("Getting started"), description="Install the client and make a first request."),
        "/docs/api": _page(
            "API reference | Lumen docs",
            _DOCS_NAV + "<main><h1>API reference</h1><h3>Events</h3><p>" + _DOCS_WALL
            + "</p><h3>Sessions</h3><p>" + _DOCS_WALL + "</p>"
            '<p>Back to <a href="/docs/getting-started">getting started</a>.</p></main>',
            head=_docs_article("API reference"), description="Every endpoint of the Lumen API."),
    },
}


# ---------------------------------------------------------------------------
# 5. Blog. BlogPosting markup on every post, but no author anywhere, editorial
#    dates years old, "click here" links and no Open Graph tags.
# ---------------------------------------------------------------------------
_BLOG_NAV = ('<header><nav><a href="/">Home</a> <a href="/blog/">All posts</a></nav>'
             '<form role="search" action="/search"><input type="search" name="q" aria-label="Search posts">'
             "</form></header>")
_BLOG_COPY = ("Sourdough rewards patience. A starter fed at the same time each day rises predictably, "
              "and a long cold proof gives the crumb its open structure and mild sourness. ")


def _post(slug, headline, date):
    return _page(
        headline + " | Crumb Notes",
        _BLOG_NAV + "<main><article><h1>" + headline + "</h1><p>Published " + date + ". Updated " + date
        + ".</p><p>" + _BLOG_COPY * 6 + "</p><p>For the full method, "
        '<a href="/blog/">click here</a>. For the other post, <a href="/blog/' + slug + '">read more</a>.</p>'
        "</article></main>",
        head=_jsonld('{"@context":"https://schema.org","@type":"BlogPosting","headline":"' + headline
                     + '","datePublished":"' + date + '"}'),
        description=headline + ", a sourdough baking note.")


BLOG = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/blog/", "/news/", "/blog/cold-proofing", "/blog/feeding-a-starter"]),
    "pages": {
        "/": _page("Crumb Notes, a sourdough baking blog",
                   _BLOG_NAV + "<main><h1>Crumb Notes</h1><p>" + _BLOG_COPY * 3 + '</p><p>Read '
                   '<a href="/blog/cold-proofing">cold proofing</a> and '
                   '<a href="/blog/feeding-a-starter">feeding a starter</a>.</p></main>',
                   head=_jsonld('{"@context":"https://schema.org","@type":"Organization","name":"Crumb Notes",'
                                '"url":"http://HOST/"}'),
                   description="Notes on baking sourdough at home."),
        "/blog/": _page("All posts | Crumb Notes",
                        _BLOG_NAV + '<main><h1>All posts</h1><ul><li><a href="/blog/cold-proofing">Cold proofing'
                        '</a></li><li><a href="/blog/feeding-a-starter">Feeding a starter</a></li>'
                        '<li><a href="/news/">News</a></li></ul></main>', description="Every post on Crumb Notes."),
        # A second section index: two listing pages must not look like a shop.
        "/news/": _page("News | Crumb Notes",
                        _BLOG_NAV + '<main><h1>News</h1><ul><li><a href="/blog/cold-proofing">New post on cold '
                        'proofing</a></li><li><a href="/blog/feeding-a-starter">Starter guide updated</a></li>'
                        '<li><a href="/blog/">All posts</a></li></ul></main>', description="News from Crumb Notes."),
        "/blog/cold-proofing": _post("feeding-a-starter", "Cold proofing sourdough overnight", "2014-03-02"),
        "/blog/feeding-a-starter": _post("cold-proofing", "Feeding a sourdough starter", "2013-09-15"),
    },
}


# ---------------------------------------------------------------------------
# 6. Multi-language site. English and German pages annotate each other with
#    hreflang; the French page is listed by the English page but does not link
#    back and declares no lang attribute.
# ---------------------------------------------------------------------------
_INTL_COPY = {
    "en": "Nordlicht Ferries runs daily crossings between Kiel and Gothenburg, with cabins, a restaurant "
          "and space for cars, bikes and campervans on every sailing. ",
    "de": "Nordlicht Ferries betreibt taeglich Ueberfahrten zwischen Kiel und Goeteborg, mit Kabinen, einem "
          "Restaurant und Platz fuer Autos, Fahrraeder und Wohnmobile auf jeder Fahrt. ",
    "fr": "Nordlicht Ferries assure des traversees quotidiennes entre Kiel et Goteborg, avec cabines, "
          "restaurant et places pour voitures, velos et camping-cars a chaque depart. ",
}
_INTL_ALTERNATES = ('<link rel="alternate" hreflang="en" href="http://HOST/en/">'
                    '<link rel="alternate" hreflang="de" href="http://HOST/de/">'
                    '<link rel="alternate" hreflang="fr" href="http://HOST/fr/">'
                    '<link rel="alternate" hreflang="x-default" href="http://HOST/en/">')
_INTL_ORG = _jsonld('{"@context":"https://schema.org","@type":"Organization","name":"Nordlicht Ferries",'
                    '"url":"http://HOST/en/"}')
_INTL_NAV = '<header><nav><a href="/en/">English</a> <a href="/de/">Deutsch</a> <a href="/fr/">Francais</a></nav></header>'

INTL = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/en/", "/de/", "/fr/"]),
    "pages": {
        "/": _page("Nordlicht Ferries", _INTL_NAV + '<main><h1>Nordlicht Ferries</h1><p><a href="/en/">'
                   "Continue in English</a></p></main>", head=_INTL_ORG,
                   description="Daily ferries between Kiel and Gothenburg."),
        "/en/": _page("Nordlicht Ferries, Kiel to Gothenburg", _INTL_NAV + "<main><h1>Kiel to Gothenburg</h1><p>"
                      + _INTL_COPY["en"] * 3 + "</p></main>", head=_INTL_ALTERNATES + _INTL_ORG,
                      description="Daily ferries between Kiel and Gothenburg."),
        "/de/": _page("Nordlicht Ferries, Kiel nach Goeteborg", _INTL_NAV + "<main><h1>Kiel nach Goeteborg</h1><p>"
                      + _INTL_COPY["de"] * 3 + "</p></main>", head=_INTL_ALTERNATES, lang="de",
                      description="Taegliche Faehren zwischen Kiel und Goeteborg."),
        "/fr/": _page("Nordlicht Ferries, Kiel a Goteborg", _INTL_NAV + "<main><h1>Kiel a Goteborg</h1><p>"
                      + _INTL_COPY["fr"] * 3 + "</p></main>", lang=None,
                      description="Ferries quotidiens entre Kiel et Goteborg."),
    },
}


ARCHETYPES = {"spa": SPA, "shop": SHOP, "local": LOCAL, "docs": DOCS, "blog": BLOG, "intl": INTL}


# ---------------------------------------------------------------------------
# Precision traps (tests/test_precision_traps.py). Each site is built from page
# shapes that commonly trip a heuristic on real sites: the traps must not be
# reported, while the real defects planted next to them must be. The shapes are
# generic (a news homepage, a splash page, a store with a footer), never copies
# of any real site.
# ---------------------------------------------------------------------------

# 7. News publisher. Headline teasers phrased as questions link to other pages;
#    an article quotes a gallery's street address; audio is filed under
#    /category/ with nothing for sale; an archive essay carries a 1998 date; a
#    navigation link has a trailing space in its href; the brand name recurs on
#    the home page. One FAQ page has real answered questions without FAQPage
#    markup and one filler answer: those two must still be reported.
_NEWS_ORG = _jsonld('{"@context":"https://schema.org","@type":"NewsMediaOrganization","name":"Daybreak Post",'
                    '"url":"http://HOST/"}')
_NEWS_NAV = ('<header><nav><a href="/">Daybreak Post</a> <a href="/culture ">Culture</a> '
             '<a href="/category/audio">Audio</a> <a href="/category/podcasts">Podcasts</a> '
             '<a href="/faq">Help</a> <a href="/archive/1998-essay">From the archive</a></nav>'
             '<form role="search" action="/search"><input type="search" name="q" aria-label="Search"></form></header>')
_NEWS_COPY = ("Reporters cover city hall, schools, transport and the arts every day, and readers send tips "
              "that shape what the newsroom investigates next. ")


def _news_article(headline, body):
    return _page(headline + " | Daybreak Post",
                 _NEWS_NAV + "<main><article><h1>" + headline + "</h1><p>By Lena Marsh, " + RECENT + "</p>"
                 + body + "</article></main>",
                 head=_jsonld('{"@context":"https://schema.org","@type":"NewsArticle","headline":"' + headline
                              + '","datePublished":"' + RECENT + '","author":{"@type":"Person","name":"Lena Marsh",'
                              '"url":"http://HOST/authors/lena-marsh","jobTitle":"Arts editor"}}') + _NEWS_ORG,
                 description=headline + ".")


NEWS = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/world/coffee-study", "/culture/gallery-review", "/culture", "/category/audio",
                         "/category/podcasts", "/archive/1998-essay", "/faq"]),
    "pages": {
        "/": _page("Daybreak Post, news for the valley",
                   _NEWS_NAV + "<main><h1>Daybreak Post</h1>"
                   '<article><a href="/world/coffee-study"><h2>Is coffee good for your heart?</h2></a>'
                   "<p>A ten-year study of 4,000 adults reports a modest benefit.</p></article>"
                   '<article><h3><a href="/culture/gallery-review">Why are gallery tickets so expensive?</a></h3>'
                   "<p>Curators explain the costs behind the new season.</p></article>"
                   '<article><h3><a href="/category/podcasts">What happens when the river floods?</a></h3>'
                   "<p>Our podcast follows the emergency crews.</p></article>"
                   "<p>" + ("Daybreak Post reporters bring Daybreak readers the Daybreak morning briefing. "
                            "The Daybreak newsroom publishes Daybreak Post stories daily. ") * 12
                   + _NEWS_COPY * 4 + "</p></main>",
                   head=_NEWS_ORG, description="Local news, culture and podcasts from the valley."),
        "/world/coffee-study": _news_article(
            "Coffee drinkers show a modest heart benefit in a ten-year study",
            "<p>" + _NEWS_COPY * 6 + "</p>"),
        "/culture/gallery-review": _news_article(
            "A bold season opens at the Halcyon Gallery",
            "<p>" + _NEWS_COPY * 4 + "</p><p>The exhibition runs at the Halcyon Gallery, 56 Brewer Street, "
            "London W1F 9TE, until the end of June.</p>"),
        "/culture": _page("Culture | Daybreak Post",
                          _NEWS_NAV + '<main><h1>Culture</h1><ul><li><a href="/culture/gallery-review">A bold season '
                          'opens at the Halcyon Gallery</a></li><li><a href="/">Front page</a></li></ul></main>',
                          head=_NEWS_ORG, description="Arts and culture coverage."),
        "/category/audio": _page("Audio | Daybreak Post",
                                 _NEWS_NAV + "<main><h1>Audio</h1><p>" + _NEWS_COPY * 3 + '</p><ul><li><a href='
                                 '"/category/podcasts">Podcasts</a></li><li><a href="/">Front page</a></li></ul></main>',
                                 head=_NEWS_ORG, description="Audio reports from the newsroom."),
        "/category/podcasts": _page("Podcasts | Daybreak Post",
                                    _NEWS_NAV + "<main><h1>Podcasts</h1><p>" + _NEWS_COPY * 3 + '</p><ul><li><a href='
                                    '"/category/audio">Audio</a></li><li><a href="/">Front page</a></li></ul></main>',
                                    head=_NEWS_ORG, description="Weekly podcasts from the newsroom."),
        "/archive/1998-essay": _page("Why the valley needs a newspaper | Daybreak Post archive",
                                     _NEWS_NAV + "<main><h1>Why the valley needs a newspaper</h1><p>First "
                                     "published Feb 6, 1998.</p><p>" + _NEWS_COPY * 5 + "</p></main>",
                                     head=_NEWS_ORG, description="An essay from the first year of the paper."),
        "/faq": _page("Help and questions | Daybreak Post",
                      _NEWS_NAV + "<main><h1>Help</h1>"
                      "<h2>How do I subscribe to the print edition?</h2><p>Call the circulation desk or fill in the "
                      "form on the subscriptions page.</p>"
                      "<h2>Can I read stories without an account?</h2><p>Yes, ten stories a month are free.</p>"
                      "<h2>How do I send the newsroom a tip?</h2><p>Great question. There are many ways to reach us "
                      "and we read everything.</p>"
                      "<p>" + _NEWS_COPY * 2 + "</p></main>",
                      head=_NEWS_ORG, description="Answers to common reader questions."),
    },
}


# 8. Splash page and nonprofit. The home page is a short chooser between two
#    campuses that runs an analytics script; a Markdown file for agents is
#    listed in the sitemap; the contact form has an email field; a page title
#    uses "Alternative" as an adjective; the home page asks for donations. None
#    of these is a defect to report, except that the splash page is listed as
#    unconfirmed.
_TRUST_ORG = _jsonld('{"@context":"https://schema.org","@type":"Organization","name":"Northfield Learning Trust",'
                     '"url":"http://HOST/"}')
_TRUST_NAV = ('<header><nav><a href="/home/">Home</a> <a href="/contact">Contact</a> '
              '<a href="/visit/alternatives">Getting here</a> <a href="/donate">Donate</a></nav></header>')
_TRUST_COPY = ("Northfield Learning Trust runs free evening classes in reading, numeracy and computing for adults "
               "across the county, taught by volunteers in libraries and community halls. ")

SPLASH = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/home/", "/contact", "/visit/alternatives", "/agents.md"]),
    "pages": {
        "/": _page("Northfield Learning Trust",
                   "<h1>Welcome</h1>"
                   '<a href="/home/">North campus</a> <a href="https://south.northfield.test/">South campus</a>'
                   '<script src="/js/analytics.js"></script>',
                   head=_TRUST_ORG, description="Choose a campus."),
        "/home/": _page("Northfield Learning Trust, free adult classes",
                        _TRUST_NAV + "<main><h1>Free evening classes for adults</h1>"
                        "<h2>How it works</h2><p>" + _TRUST_COPY * 2 + "</p>"
                        "<h2>What we offer</h2><p>" + _TRUST_COPY * 2 + "</p>"
                        '<p>See <a href="/contact">how to reach us</a> or <a href="/donate">donate</a>.</p></main>',
                        head=_TRUST_ORG, description="Free evening classes in reading, numeracy and computing."),
        "/contact": _page("Contact Northfield Learning Trust",
                          _TRUST_NAV + "<main><h1>Contact us</h1><p>" + _TRUST_COPY + "</p>"
                          '<form action="/contact/send" method="post"><label>Email <input type="email" name="email">'
                          '</label><label>Message <textarea name="message"></textarea></label>'
                          "<button>Send</button></form></main>",
                          head=_TRUST_ORG, description="Write to the trust."),
        "/donate": _page("Donate to Northfield Learning Trust",
                         _TRUST_NAV + "<main><h1>Support free classes</h1><p>" + _TRUST_COPY * 2 + "</p></main>",
                         head=_TRUST_ORG, description="Gifts fund free classes."),
        "/visit/alternatives": _page("Alternative routes to the north campus",
                                     _TRUST_NAV + "<main><h1>Alternative routes to the north campus</h1><p>"
                                     + _TRUST_COPY * 2 + "</p><p>Take the number 12 bus or walk along the canal "
                                     "path from the station.</p></main>",
                                     description="Bus, train and walking routes."),
    },
    "assets": {"/agents.md": (b"# Northfield Learning Trust\n\nFree evening classes for adults.\n",
                              "text/markdown; charset=utf-8"),
               "/js/analytics.js": (b"window.analytics=[];", "application/javascript")},
}


# 9. Store with consumer segments. Navigation names Men, Women and Kids; a
#    product gallery repeats one descriptive alt text on four views of the same
#    shoe. Defects that must still be found: a footer newsletter signup (the
#    email-summary suggestion), a footer address with no location markup, and no
#    saved or recently viewed items on product pages.
_STORE_NAV = ('<header><nav><a href="/">Home</a> <a href="/collections/men">Men</a> '
              '<a href="/collections/women">Women</a> <a href="/collections/kids">Kids</a></nav>'
              '<form role="search" action="/search"><input type="search" name="q" aria-label="Search"></form></header>')
_STORE_FOOTER = ('<footer><p>Fellwalk Shoes, 12 Harbour Road, Bristol BS1 5TT</p>'
                 '<form action="/newsletter/subscribe" method="post"><input type="email" name="email" '
                 'aria-label="Email address"><button>Subscribe</button></form></footer>')
_STORE_ORG = _jsonld('{"@context":"https://schema.org","@type":"Organization","name":"Fellwalk Shoes",'
                     '"url":"http://HOST/"}')
_STORE_COPY = ("Fellwalk Shoes makes wool walking shoes that dry fast, breathe on warm days and keep feet warm on cold "
               "ones, with soles made from natural rubber. ")


def _shoe(name, slug):
    gallery = "".join(f'<img src="/img/{slug}-{view}.jpg" alt="{name} walking shoe in grey wool" width="800" '
                      f'height="800">' for view in ("side", "top", "back", "sole"))
    return _page(name + " | Fellwalk Shoes",
                 _STORE_NAV + "<main><h1>" + name + "</h1>" + gallery + "<p>" + _STORE_COPY * 2
                 + "</p><p>Price: $120.00</p><button>Add to cart</button>"
                 "<table><tr><th>Weight</th><td>280 g</td></tr><tr><th>Upper</th><td>Merino wool</td></tr></table>"
                 "</main>" + _STORE_FOOTER,
                 head=_jsonld('{"@context":"https://schema.org","@type":"Product","name":"' + name + '",'
                              '"offers":{"@type":"Offer","price":"120.00","priceCurrency":"USD"}}') + _STORE_ORG,
                 description=name + ", a wool walking shoe.")


STORE = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/products/ridge-runner", "/products/valley-walker", "/collections/men"]),
    "pages": {
        "/": _page("Fellwalk Shoes, wool walking shoes",
                   _STORE_NAV + "<main><h1>Wool walking shoes</h1><p>" + _STORE_COPY * 3 + '</p><p>Shop the '
                   '<a href="/products/ridge-runner">Ridge Runner</a> or the <a href="/products/valley-walker">Valley '
                   "Walker</a>.</p></main>" + _STORE_FOOTER,
                   head=_STORE_ORG, description="Wool walking shoes for men, women and kids."),
        "/products/ridge-runner": _shoe("Ridge Runner", "ridge"),
        "/products/valley-walker": _shoe("Valley Walker", "valley"),
        "/collections/men": _page("Men's shoes | Fellwalk Shoes",
                                  _STORE_NAV + "<main><h1>Men's shoes</h1><p>" + _STORE_COPY * 2 + '</p><ul><li><a '
                                  'href="/products/ridge-runner">Ridge Runner</a></li><li><a href="/products/'
                                  'valley-walker">Valley Walker</a></li></ul></main>' + _STORE_FOOTER,
                                  head=_STORE_ORG, description="Wool walking shoes for men."),
        "/collections/women": _page("Women's shoes | Fellwalk Shoes",
                                    _STORE_NAV + "<main><h1>Women's shoes</h1><p>" + _STORE_COPY * 2 + '</p><ul><li><a '
                                    'href="/products/valley-walker">Valley Walker</a></li></ul></main>' + _STORE_FOOTER,
                                    head=_STORE_ORG, description="Wool walking shoes for women."),
        "/collections/kids": _page("Kids' shoes | Fellwalk Shoes",
                                   _STORE_NAV + "<main><h1>Kids' shoes</h1><p>" + _STORE_COPY * 2 + '</p><ul><li><a '
                                   'href="/products/ridge-runner">Ridge Runner</a></li></ul></main>' + _STORE_FOOTER,
                                   head=_STORE_ORG, description="Wool walking shoes for kids."),
    },
}

TRAPS = {"news": NEWS, "splash": SPLASH, "store": STORE}


# ---------------------------------------------------------------------------
# Robustness sites (tests/test_robustness.py). Each reproduces a way a real
# acquisition goes wrong: the audit must still return a valid, honest report.
# ---------------------------------------------------------------------------

# A bot-protection interstitial: a challenge title, a challenge script and a
# noscript notice, with no content of the site.
CHALLENGE_PAGE = ('<!DOCTYPE html><html lang="en"><head><title>Just a moment...</title></head><body>'
                  '<noscript>Enable JavaScript and cookies to continue</noscript>'
                  '<script>window._cf_chl_opt={cvId:"3",cType:"managed"};</script></body></html>')

_GUARD_PATHS = ("/", "/about", "/pricing", "/blog/", "/contact")

# 10. A site behind bot protection: every page answers 403 with a challenge. The
#     audit must stop after a couple of challenges, analyze nothing, and say why.
GUARDED = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(_GUARD_PATHS),
    "pages": {},
    "responses": {p: (403, CHALLENGE_PAGE, "text/html; charset=utf-8") for p in _GUARD_PATHS},
}

_MIXED_NAV = ('<header><nav><a href="/">Home</a> <a href="/guides">Guides</a> <a href="/members">Members</a>'
              '</nav></header>')
_MIXED_COPY = ("Cedar Row Studio teaches pottery to beginners in small evening groups, with clay, glazes and two "
               "firings included in every course. ")

# 11. One section behind a challenge (503 with a challenge script); the rest is
#     public. The challenged page is skipped, never reported as broken.
MIXED_GUARD = {
    "robots": ALLOW_ALL,
    "sitemap": _sitemap(["/", "/guides", "/members"]),
    "pages": {
        "/": _page("Cedar Row Studio, pottery classes",
                   _MIXED_NAV + "<main><h1>Pottery classes for beginners</h1><p>" + _MIXED_COPY * 3 + "</p></main>",
                   description="Evening pottery classes for beginners."),
        "/guides": _page("Glazing guide | Cedar Row Studio",
                         _MIXED_NAV + "<main><h1>A beginner's glazing guide</h1><p>" + _MIXED_COPY * 3
                         + "</p></main>", description="How glazes behave in the kiln."),
    },
    "responses": {"/members": (503, CHALLENGE_PAGE, "text/html; charset=utf-8")},
}

# 12. A page in windows-1252 whose only declaration is <meta charset>; the HTTP
#     header names no charset. Curly quotes and accented letters must survive.
_LEGACY_TEXT = ("\u201cCaf\u00e9 cr\u00e8me\u201d is what we\u2019re known for: Rue Barr\u00e9 roasts its own "
                "beans and bakes p\u00e2tisserie every morning. ")
LEGACY_ENCODING = {
    "robots": ALLOW_ALL,
    "pages": {},
    "responses": {"/": (200, ('<!doctype html><html lang="fr"><head><meta charset="windows-1252">'
                              "<title>Caf\u00e9 Rue Barr\u00e9</title></head><body><h1>Caf\u00e9 Rue Barr\u00e9</h1>"
                              "<p>" + _LEGACY_TEXT * 4 + "</p></body></html>").encode("cp1252"),
                        "text/html")},
}

ROBUSTNESS = {"guarded": GUARDED, "mixed_guard": MIXED_GUARD, "legacy_encoding": LEGACY_ENCODING}


def serve(site):
    """Serve one archetype on 127.0.0.1. Returns (base_url, stop, requests), where
    requests lists (method, path) for every request the server received."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _reply(self, status, body, ctype, headers=()):
            data = body if isinstance(body, bytes) else body.replace("HOST", self.headers.get("Host", "")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            for name, value in headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            seen.append((self.command, self.path))
            path = self.path.split("?")[0]
            # Exact responses (status, body, content type[, headers]) win over
            # everything else, robots.txt included.
            if path in site.get("responses", {}):
                return self._reply(*site["responses"][path])
            if path == "/robots.txt":
                return self._reply(200, site.get("robots", ALLOW_ALL), "text/plain")
            if path == "/sitemap.xml" and site.get("sitemap"):
                return self._reply(200, site["sitemap"], "application/xml")
            if path == "/llms.txt" and site.get("llms"):
                return self._reply(200, site["llms"], "text/plain")
            if path in site["pages"]:
                return self._reply(200, site["pages"][path], "text/html; charset=utf-8")
            if path in site.get("assets", {}):
                body, ctype = site["assets"][path]
                return self._reply(200, body, ctype)
            return self._reply(404, "<html><body><h1>Not found</h1></body></html>", "text/html")

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    def stop():
        httpd.shutdown()
        httpd.server_close()
    return f"http://127.0.0.1:{httpd.server_address[1]}", stop, seen
