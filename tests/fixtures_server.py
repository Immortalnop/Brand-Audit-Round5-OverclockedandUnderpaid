"""fixtures_server.py -- a tiny local HTTP server used by integration tests so they
never depend on outbound network access. Exercises: normal pages, robots.txt
variants, redirects, malformed JSON-LD, slow/timeout-inducing endpoints, JS-heavy
(CSR) pages, orphan pages, a multi-brand identity conflict, a stale-commercial-facts
product page, and a broken-navigation (sitemap-only, isolated) page cluster."""
import struct
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ROBOTS_ALLOW_ALL = "User-agent: *\nDisallow:\n"
_ROBOTS_DISALLOW_ALL = "User-agent: *\nDisallow: /\n"

_HOME = """<html><head><title>Example Brand</title>
<script type="application/ld+json">{"@type": "Organization", "name": "Example Brand",
"telephone": "+1 555-123-4567", "sameAs": ["https://twitter.com/example"]}</script>
</head><body><h1>Welcome</h1><p>Example Brand was founded 2015-01-01.</p>
<a href="/about">About</a><a href="/js-heavy">App</a><a href="/malformed">Malformed</a>
<a href="/redirect">Redirect</a><a href="/product">Product</a></body></html>"""

# Second, unrelated Organization JSON-LD block appended to the home page when
# multi_brand=True -- a genuine multi-brand-conflict case (see
# resolve_entity_identity.py), distinct from harmless legal-suffix/case noise.
_MULTI_BRAND_EXTRA_JSONLD = (
    '<script type="application/ld+json">{"@type": "Organization", '
    '"name": "Zenith Traders", "telephone": "+1 555-000-1111"}</script>'
)

# Stale commercial fact: page_type resolves to "product" via the /product path,
# so its date claims are categorized "commercial" (assess_freshness.py) -- old
# dates here should surface as a high-severity finding. Three distinct dated
# mentions (not one) so the finding's evidence sample clears the full-confidence
# threshold in step_down_severity rather than being stepped down for a thin
# sample (models.step_down_severity, threshold=0.5 of a 3-fact reference sample).
_PRODUCT = """<html><head><title>Product</title></head><body><h1>Widget</h1>
<p>Price: $49.99. Offer last updated 2019-03-01.</p>
<p>Promotion valid through 2020-06-15.</p>
<p>Stock refreshed 2021-11-20.</p></body></html>"""

# Broken-navigation pair: mutually linked to each other, but linked from nowhere
# else on the site (discovered only via sitemap.xml, never via HOME's links) --
# a weakly-connected component isolated from the main site graph
# (build_site_graph.py isolated_clusters), not just two individual orphans.
_CLUSTER_A = ('<html><head><title>Cluster A</title></head><body><h1>Cluster A</h1>'
              '<a href="/cluster-b">Next</a></body></html>')
_CLUSTER_B = ('<html><head><title>Cluster B</title></head><body><h1>Cluster B</h1>'
              '<a href="/cluster-a">Back</a></body></html>')

_ABOUT = """<html><head><title>About</title></head><body><h1>About</h1>
<p>Contact us at +1 555-987-6543.</p></body></html>"""

_MALFORMED = """<html><head><title>Bad JSON-LD</title>
<script type="application/ld+json">{not valid json,,,}</script>
</head><body><h1>Page</h1><p>Some content here.</p></body></html>"""

_JS_HEAVY = (
    '<html><head><title>App</title></head><body><div id="root"></div>'
    "<script>document.getElementById('root').innerText = "
    "'Rendered content only visible after JavaScript execution. '.repeat(20);</script>"
    "</body></html>"
)

_ORPHAN = "<html><head><title>Orphan</title></head><body><h1>Orphan</h1>" \
          "<p>Nobody links here.</p></body></html>"


# ---------------------------------------------------------------------------
# Clean, well-built fixture (Step 3 false-positive guard). Every page is
# server-rendered, declares lang and viewport, has a descriptive title, meta
# description, a single H1, valid JSON-LD, descriptive internal anchors, and
# terse copy with no keyword stuffing. Dates on the pricing page are refreshed to
# the near future so no stale-commercial finding fires. The whole set is mutually
# linked so there are no orphans, dead ends or isolated clusters.
# ---------------------------------------------------------------------------
_CLEAN_HEAD = (
    '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    '<meta name="description" content="{desc}"><title>{title}</title>'
)
_CLEAN_NAV = (
    '<nav><a href="/">Home</a> <a href="/about">About Northwind Analytics</a> '
    '<a href="/services">Data services</a> <a href="/pricing">Pricing plans</a></nav>'
)
_CLEAN_ORG_JSONLD = (
    '<script type="application/ld+json">{"@context":"https://schema.org",'
    '"@type":"Organization","name":"Northwind Analytics",'
    '"url":"http://HOST/","description":"Northwind Analytics builds reporting '
    'dashboards for logistics teams.","sameAs":["https://www.linkedin.com/company/northwind-analytics"]}'
    "</script>"
)


def _clean_page(title, desc, h1, body, extra_head=""):
    return (
        '<html lang="en"><head>' + _CLEAN_HEAD.format(desc=desc, title=title) + extra_head
        + "</head><body><header>" + _CLEAN_NAV + "</header><main><h1>" + h1 + "</h1>"
        + body + "</main></body></html>"
    )


_CLEAN_HOME = _clean_page(
    "Northwind Analytics", "Reporting dashboards for logistics teams.",
    "Reporting dashboards for logistics teams",
    "<p>Northwind Analytics builds reporting dashboards that help logistics teams "
    "track shipments, delivery times and freight costs in one place. Operations "
    "managers use our dashboards to spot delays early, compare carrier performance "
    "and keep spending within budget without exporting data by hand.</p>"
    "<p>Teams connect their existing shipment records and see live summaries within "
    "a day, with no engineering work required. Explore our "
    "<a href=\"/services\">data services</a> to see what each dashboard covers, or "
    "review the <a href=\"/pricing\">pricing plans</a> to find the tier that fits "
    "your team size.</p>",
    extra_head=_CLEAN_ORG_JSONLD,
)
_CLEAN_ABOUT = _clean_page(
    "About Northwind Analytics", "Who we are and what we build.",
    "About Northwind Analytics",
    "<p>Northwind Analytics is a logistics analytics company founded in 2018 and "
    "based in Chicago. We sell reporting dashboards to freight brokers, carriers "
    "and warehousing operators who need a clear daily picture of their shipments "
    "and costs.</p>"
    "<p>Our team comes from supply-chain operations and data engineering, so the "
    "product is shaped by people who have run warehouses and managed carrier "
    "contracts. You can reach us at +1 555-321-7788 or read about our "
    "<a href=\"/services\">data services</a> and current "
    "<a href=\"/pricing\">pricing plans</a>.</p>",
)
_CLEAN_SERVICES = _clean_page(
    "Data services", "Dashboards, alerts and integrations for logistics data.",
    "Data services for logistics teams",
    "<p>We offer three services that work together. Shipment dashboards show "
    "delivery status and transit times across every carrier you use. Cost alerts "
    "flag invoices and lanes that move outside their usual range so finance can "
    "review them quickly. Warehouse integrations pull inventory and dispatch "
    "records into the same reports.</p>"
    "<p>Each service is billed under a single plan described on our "
    "<a href=\"/pricing\">pricing page</a>, and every account includes setup help "
    "and access to the <a href=\"/about\">team behind the product</a>.</p>"
    '<script type="application/ld+json">{"@context":"https://schema.org",'
    '"@type":"Service","name":"Logistics reporting dashboards",'
    '"provider":{"@type":"Organization","name":"Northwind Analytics"}}</script>',
)
# Fresh commercial dates (well in the future relative to the audit) so no
# stale-commercial finding is triggered on a clean site.
_CLEAN_PRICING = _clean_page(
    "Pricing plans", "Simple monthly pricing for every team size.",
    "Pricing plans",
    "<p>Pricing is a single monthly subscription with no setup fee. The team plan "
    "costs $99 per month and covers up to ten users, all three data services and "
    "daily report refreshes. Larger operations can request a custom plan with more "
    "users and priority support.</p>"
    "<p>Prices were last reviewed 2099-01-01 and the current offer is valid through "
    "2099-12-31. Read the <a href=\"/about\">company background</a> or browse the "
    "full <a href=\"/services\">data services</a> before you choose a plan.</p>"
    '<script type="application/ld+json">{"@context":"https://schema.org",'
    '"@type":"Product","name":"Team plan","offers":{"@type":"Offer",'
    '"price":"99","priceCurrency":"USD","priceValidUntil":"2099-12-31"}}</script>',
)
_CLEAN_SITEMAP = (
    "<?xml version='1.0' encoding='UTF-8'?>"
    "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
    "<url><loc>{origin}/</loc></url><url><loc>{origin}/about</loc></url>"
    "<url><loc>{origin}/services</loc></url><url><loc>{origin}/pricing</loc></url>"
    "</urlset>"
)


_SITEMAP_OK = ("<?xml version='1.0' encoding='UTF-8'?>"
               "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
               "<url><loc>{origin}/</loc></url><url><loc>{origin}/about</loc></url>"
               "</urlset>")
_SITEMAP_MALFORMED = "<urlset><url><loc>not closed"
# Per-URL <lastmod>: the home page recent ({recent} is filled with today's date),
# /about and /product years old. /product also sends a Last-Modified header from
# 2017, newer than its 2016 lastmod, so the header is the date that counts.
_SITEMAP_LASTMOD = ("<?xml version='1.0' encoding='UTF-8'?>"
                    "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
                    "<url><loc>{origin}/</loc><lastmod>{recent}</lastmod></url>"
                    "<url><loc>{origin}/about</loc><lastmod>2015-06-01</lastmod></url>"
                    "<url><loc>{origin}/product</loc><lastmod>2016-01-01T08:00:00+00:00</lastmod></url>"
                    "</urlset>")
_LASTMOD_PAGE_HEADERS = {"/product": {"Last-Modified": "Wed, 01 Mar 2017 10:00:00 GMT"}}
# Lists /cluster-a and /cluster-b so they are discovered and crawled even though
# no page other than each other links to them -- the sitemap-discovery path
# (see acquire_site.py) is what makes them reachable at all, and
# their mutual-only linking is what makes them an isolated cluster once crawled.
_SITEMAP_BROKEN_NAV = ("<?xml version='1.0' encoding='UTF-8'?>"
                       "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
                       "<url><loc>{origin}/</loc></url><url><loc>{origin}/about</loc></url>"
                       "<url><loc>{origin}/cluster-a</loc></url>"
                       "<url><loc>{origin}/cluster-b</loc></url>"
                       "</urlset>")


# ---------------------------------------------------------------------------
# Non-text media fixture (facts locked in images and PDFs). The pricing page
# states no prices in text; its prices live in an SVG and a raster image. A
# linked spec-sheet PDF states facts no HTML page states, a second PDF is a
# scanned image with no text layer, and a third PDF sits under a robots-disallowed
# path so the audit must never request it. A cross-origin image must never be
# fetched either.
# ---------------------------------------------------------------------------
def build_pdf(objects):
    """Assemble a minimal PDF from object bodies numbered 1..n."""
    out = b"%PDF-1.7\n"
    for number, body in enumerate(objects, 1):
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    return out + b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"


def pdf_stream(entries, body, compress=True):
    if compress:
        body = zlib.compress(body)
        entries += b" /Filter /FlateDecode"
    return b"<< " + entries + b" /Length %d >>\nstream\n" % len(body) + body + b"\nendstream"


def text_pdf(content):
    """One-page PDF that draws `content` (literal-string bytes) in Helvetica."""
    return build_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        pdf_stream(b"", b"BT /F1 11 Tf 72 720 Td (" + content + b") Tj ET"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ])


def image_only_pdf():
    return build_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>",
        pdf_stream(b"", b"q 612 0 0 792 0 0 cm /Im0 Do Q"),
        pdf_stream(b"/Type /XObject /Subtype /Image /Width 1 /Height 1 /BitsPerComponent 8 "
                   b"/ColorSpace /DeviceGray", b"\x00", compress=False),
    ])


def png_header(width, height):
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
            + struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00" + b"\x00" * 64)


_MEDIA_ROBOTS = "User-agent: *\nDisallow: /private/\n"
_MEDIA_HOME = """<html lang="en"><head><title>Media Brand</title></head><body><h1>Media Brand</h1>
<p>Media Brand sells industrial heaters to workshops.</p>
<img src="/img/logo.svg" width="400" height="120" alt="Media Brand">
<a href="/pricing">Pricing</a> <a href="/docs/specs.pdf">Spec sheet</a>
<a href="/docs/scan.pdf">Scanned brochure</a> <a href="/private/secret.pdf">Internal</a>
</body></html>"""
_MEDIA_PRICING = """<html lang="en"><head><title>Pricing</title></head><body><h1>Pricing</h1>
<p>See our plans in the table below.</p>
<img src="/img/rates.svg" width="600" height="400">
<img src="/img/price-list.png" alt="Price list">
<img src="https://cdn.example.test/menu.jpg" alt="Menu">
<a href="/">Home</a></body></html>"""
_MEDIA_RATES_SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">'
                    b'<text x="10" y="20">Basic <tspan>$19.99</tspan> per month</text>'
                    b'<text x="10" y="40">Pro $49.99 per month</text></svg>')
_MEDIA_LOGO_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><text>Media Brand</text></svg>'
_MEDIA_SPECS_PDF = text_pdf(b"Model H500 output 4500 W weight 12.5 kg price $1,299.00 call +1 555-222-3333")
_MEDIA_SCAN_PDF = image_only_pdf()
_MEDIA_PNG = png_header(1200, 900)


class FixtureHandler(BaseHTTPRequestHandler):
    server_version = "FixtureHTTP/1.0"
    robots_body = _ROBOTS_ALLOW_ALL
    robots_mode = "ok"  # "ok" | "absent" | "malformed" | "timeout" | "error"
    slow_delay_s = 0.0
    sitemap_mode = "absent"  # "absent" | "ok" | "malformed" | "broken_nav" | "lastmod"
    llms_txt_mode = "absent"  # "absent" | "ok"
    big_body_bytes = 0  # if >0, /big serves this many bytes
    multi_brand = False  # if True, home page carries a second, unrelated Organization block
    clean = False  # if True, serve the well-built site (Step 3 false-positive guard)
    media = False  # if True, serve the non-text media site (images and PDFs)
    requests_seen = None  # optional per-server list of request paths, set by start_server

    def log_message(self, fmt, *args):  # silence test output
        pass

    def _send(self, status, body, headers=None):
        self.send_response(status)
        headers = dict(headers or {"Content-Type": "text/html"})
        if status == 200 and self.sitemap_mode == "lastmod":
            headers.update(_LASTMOD_PAGE_HEADERS.get(self.path, {}))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.wfile.write(body)

    def do_GET(self):
        path = self.path
        if self.requests_seen is not None:
            self.requests_seen.append(path)
        origin = f"http://{self.headers.get('Host', '127.0.0.1')}"
        if self.media:
            routes = {
                "/robots.txt": (_MEDIA_ROBOTS, "text/plain"),
                "/": (_MEDIA_HOME, "text/html"),
                "/pricing": (_MEDIA_PRICING, "text/html"),
                "/img/rates.svg": (_MEDIA_RATES_SVG, "image/svg+xml"),
                "/img/logo.svg": (_MEDIA_LOGO_SVG, "image/svg+xml"),
                "/img/price-list.png": (_MEDIA_PNG, "image/png"),
                "/docs/specs.pdf": (_MEDIA_SPECS_PDF, "application/pdf"),
                "/docs/scan.pdf": (_MEDIA_SCAN_PDF, "application/pdf"),
                "/private/secret.pdf": (_MEDIA_SPECS_PDF, "application/pdf"),
            }
            if path in routes:
                body, ctype = routes[path]
                self._send(200, body, {"Content-Type": ctype})
            else:
                self._send(404, "<html><body>not found</body></html>")
            return
        if self.clean:
            if path == "/robots.txt":
                self._send(200, self.robots_body, {"Content-Type": "text/plain"})
                return
            if path == "/sitemap.xml":
                self._send(200, _CLEAN_SITEMAP.format(origin=origin), {"Content-Type": "application/xml"})
                return
            if path == "/llms.txt":
                self._send(404, "not found")
                return
            clean_pages = {"/": _CLEAN_HOME, "/about": _CLEAN_ABOUT,
                           "/services": _CLEAN_SERVICES, "/pricing": _CLEAN_PRICING}
            if path in clean_pages:
                self._send(200, clean_pages[path].replace("HOST", self.headers.get("Host", "127.0.0.1")))
                return
            self._send(404, "<html><body>not found</body></html>")
            return
        if path == "/robots.txt":
            if self.robots_mode == "absent":
                self._send(404, "not found")
            elif self.robots_mode == "malformed":
                self._send(200, b"\xff\xfe\x00not valid utf-8 \x80\x81", {"Content-Type": "text/plain"})
            elif self.robots_mode == "timeout":
                time.sleep(self.slow_delay_s or 2.0)
                self._send(200, self.robots_body, {"Content-Type": "text/plain"})
            elif self.robots_mode == "error":
                self._send(500, "error", {"Content-Type": "text/plain"})
            else:
                self._send(200, self.robots_body, {"Content-Type": "text/plain"})
        elif path == "/sitemap.xml":
            if self.sitemap_mode == "ok":
                self._send(200, _SITEMAP_OK.format(origin=origin), {"Content-Type": "application/xml"})
            elif self.sitemap_mode == "lastmod":
                recent = time.strftime("%Y-%m-%d", time.gmtime())
                self._send(200, _SITEMAP_LASTMOD.format(origin=origin, recent=recent),
                           {"Content-Type": "application/xml"})
            elif self.sitemap_mode == "broken_nav":
                self._send(200, _SITEMAP_BROKEN_NAV.format(origin=origin), {"Content-Type": "application/xml"})
            elif self.sitemap_mode == "malformed":
                self._send(200, _SITEMAP_MALFORMED, {"Content-Type": "application/xml"})
            else:
                self._send(404, "not found")
        elif path == "/llms.txt":
            if self.llms_txt_mode == "ok":
                self._send(200, "# Example Brand\n", {"Content-Type": "text/plain"})
            else:
                self._send(404, "not found")
        elif path == "/":
            home = _HOME
            if self.multi_brand:
                home = home.replace("</head>", _MULTI_BRAND_EXTRA_JSONLD + "</head>")
            self._send(200, home)
        elif path == "/about":
            self._send(200, _ABOUT)
        elif path == "/malformed":
            self._send(200, _MALFORMED)
        elif path == "/js-heavy":
            self._send(200, _JS_HEAVY)
        elif path == "/orphan":
            self._send(200, _ORPHAN)
        elif path == "/product":
            self._send(200, _PRODUCT)
        elif path == "/cluster-a":
            self._send(200, _CLUSTER_A)
        elif path == "/cluster-b":
            self._send(200, _CLUSTER_B)
        elif path == "/redirect":
            self._send(301, "", {"Location": "/about", "Content-Type": "text/html"})
        elif path == "/redirect-external":
            self._send(302, "", {"Location": "http://example.invalid.test/elsewhere",
                                  "Content-Type": "text/html"})
        elif path == "/big":
            self._send(200, b"x" * self.big_body_bytes, {"Content-Type": "application/octet-stream"})
        elif path == "/slow":
            time.sleep(self.slow_delay_s)
            self._send(200, "<html><body>slow</body></html>")
        elif path == "/error":
            self._send(500, "<html><body>error</body></html>")
        else:
            self._send(404, "<html><body>not found</body></html>")


def start_server(robots_body: str = _ROBOTS_ALLOW_ALL, slow_delay_s: float = 0.0,
                  robots_mode: str = "ok", sitemap_mode: str = "absent",
                  llms_txt_mode: str = "absent", big_body_bytes: int = 0,
                  multi_brand: bool = False, clean: bool = False, media: bool = False,
                  requests_seen: list = None):
    """Starts a background server on 127.0.0.1 with an OS-assigned port. Returns
    (base_url, shutdown_fn). Pass a list as requests_seen to record every path
    the server is asked for."""
    handler = type("BoundFixtureHandler", (FixtureHandler,), {
        "robots_body": robots_body, "slow_delay_s": slow_delay_s, "robots_mode": robots_mode,
        "sitemap_mode": sitemap_mode, "llms_txt_mode": llms_txt_mode, "big_body_bytes": big_body_bytes,
        "multi_brand": multi_brand, "clean": clean, "media": media,
        "requests_seen": requests_seen,
    })
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]

    def shutdown():
        httpd.shutdown()
        httpd.server_close()

    return f"http://127.0.0.1:{port}", shutdown
