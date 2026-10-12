"""analyze_nontext_facts.py -- key facts that exist only as a document, an image or
an embedded third-party viewer (A10).

AI fetchers extract text from the HTML they receive. A price list, menu, fee table
or spec sheet that is published only as a PDF, an image, or inside a document
viewer iframe is either skipped or cited without page context; an image-only
(scanned) PDF carries no text at all. Each rule needs two signals so ordinary
downloads and decorative images do not fire:

  facts-in-pdf     a fact-keyword document (menu.pdf, price-list.pdf, "Download
                   fee structure") is linked AND the linking page shows no
                   matching facts in text (e.g. a pricing page with no prices).
                   Range-read probes (acquire_site.py) add "image-only PDF" evidence.
  facts-in-images  on a content page, an image whose file name or alt names a fact
                   (menu, price-list, timetable ...), with little supporting text;
                   or a pricing/menu page that is mostly a large image
  facts-in-iframe  a document-viewer embed (Google Docs/Drive, Issuu, Scribd,
                   Calameo, Canva) on a page with little text of its own
"""
import re
from urllib.parse import urlsplit
from models import skill_result, make_finding
from check_helpers import content_pages
from constants import FACT_KEYWORDS
from url_keys import intent_of
from schema_rules import price_numbers

_FACT_RE = re.compile(r'(?<![a-z])(' + '|'.join(re.escape(k) for k in FACT_KEYWORDS) + r')(?![a-z])', re.I)
_PRICE_INTENTS = {'pricing', 'plans', 'price', 'menu', 'fees', 'admission', 'admissions', 'products', 'product',
                  'shop', 'store', 'collections', 'collection', 'services', 'service', 'courses', 'course'}
_VIEWERS = re.compile(r'(docs\.google\.com|drive\.google\.com|issuu\.com|scribd\.com|calameo\.com|canva\.(com|site)|'
                      r'flipsnack\.com|yumpu\.com|onedrive\.live\.com|dropbox\.com)', re.I)


def _facts_in_text(page):
    """Does the page carry facts as text? Prices, or a reasonable amount of text."""
    text = page.visible_text or ''
    return bool(price_numbers(text)) or len(text.split()) > 250


def fact_image_candidates(pages):
    """[(page, image, why)] for images that look like fact carriers (price list,
    menu, timetable) on pages with little supporting text. Shared with the agent
    brief, whose AG-04 step reads these images with the agent's own vision."""
    hits = []
    for p in pages:
        imgs = (p.features or {}).get('images_meta', ())
        words = len((p.visible_text or '').split())
        intent = intent_of(p.url) or ''
        named = [i for i in imgs if _FACT_RE.search(urlsplit(i.get('src') or '').path.rsplit('/', 1)[-1])
                 or _FACT_RE.search(i.get('alt') or '')]
        large = [i for i in imgs if (i.get('width') or 0) >= 600]
        if named and words < 400 and not price_numbers(p.visible_text or ''):
            hits.append((p, named[0], 'image named/alt-texted as a fact carrier'))
        elif intent in _PRICE_INTENTS and large and words < 150 and not price_numbers(p.visible_text or ''):
            # A product photo next to a price stated in text hides nothing; only a
            # large image on a price-type page with no price in its text does.
            hits.append((p, large[0], f'{intent} page with {words} words of text and a large image'))
    return hits


def analyze_nontext_facts(artifacts, deadline):
    pages = {p.url: p for p in content_pages(artifacts)}
    assets = list(artifacts.acquisition_metadata.get('asset_links', ()))
    probes = {a['url']: a for a in artifacts.acquisition_metadata.get('asset_probes', ())}
    findings = []

    pdf_hits = []
    for a in assets:
        page = pages.get(a['linked_from'])
        if not a.get('fact_keyword') or page is None:
            continue
        intent = intent_of(page.url) or ''
        probe = probes.get(a['url'], {})
        image_only = probe.get('text_layer') is False
        if image_only or not _facts_in_text(page):
            pdf_hits.append((a, page, intent, image_only))
    if pdf_hits:
        key = any(intent in _PRICE_INTENTS or page.page_type in ('product', 'home') for _, page, intent, _ in pdf_hits)
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='high' if key else 'medium',
            status='confirmed' if any(io for *_, io in pdf_hits) else 'suspected', confidence=0.75,
            title='Key facts are published only as linked documents',
            root_cause='Fact documents (prices, menus, fees, specifications) are linked from pages that do not state '
                       'those facts as text, so AI fetchers reading the page find nothing to quote',
            evidence=[{'type': 'non_text_fact',
                       'description': f"'{a['anchor'] or a['url'].rsplit('/', 1)[-1]}' -> {a['url']} linked from a page with "
                                      + ('no prices in text' if not price_numbers(page.visible_text or '') else 'little text')
                                      + ('; range read shows an image-only PDF (no text layer)' if io else ''),
                       'urls': [page.url, a['url']]} for a, page, _, io in pdf_hits[:6]],
            affected_pages=sorted({page.url for _, page, _, _ in pdf_hits}),
            suggested_action={
                'summary': 'Publish the document facts as HTML text on the linking page',
                'steps': ['Copy the key facts (prices, items, fees, specs) into an HTML table or list on the page',
                          'Keep the document as an optional download below the text',
                          'For image-only PDFs, at minimum provide a text version'],
                'priority': 'high' if key else 'medium', 'effort': 'medium',
                'expected_benefit': 'The facts become readable and quotable from the page itself',
                'verification': 'The raw HTML of the page contains the facts'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_nontext_facts.py', 'rule_id': 'facts-in-pdf'}))

    img_hits = fact_image_candidates(pages.values())
    if img_hits:
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='medium', status='suspected',
            confidence=0.65, title='Key facts appear to be carried inside images',
            root_cause='Images that look like fact carriers (price lists, menus, timetables) sit on pages with little '
                       'supporting text; their content is pixels to a text extractor',
            evidence=[{'type': 'non_text_fact',
                       'description': f"{why}: {img.get('src') or '(inline)'} (alt: {img.get('alt')!r})",
                       'urls': [p.url]} for p, img, why in img_hits[:6]],
            affected_pages=[p.url for p, _, _ in img_hits],
            suggested_action={
                'summary': 'State the image facts as HTML text next to the image',
                'steps': ['Publish the same content as an HTML table or list',
                          'Give the image alt text that states what it shows'],
                'priority': 'medium', 'effort': 'low',
                'expected_benefit': 'Facts exist as extractable text',
                'verification': 'The facts appear in the raw HTML text of the page'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_nontext_facts.py', 'rule_id': 'facts-in-images'}))

    frame_hits = [(p, src) for p in pages.values() for src in (p.features or {}).get('iframes', ())
                  if _VIEWERS.search(src) and len((p.visible_text or '').split()) < 250]
    if frame_hits:
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='medium', status='suspected',
            confidence=0.65, title='Key content is embedded through a document-viewer iframe',
            root_cause='Pages with little text of their own embed a third-party document viewer; the embedded '
                       'content belongs to another origin and is not read as part of the page',
            evidence=[{'type': 'non_text_fact', 'description': f'iframe src: {src[:150]}', 'urls': [p.url]}
                      for p, src in frame_hits[:6]],
            affected_pages=sorted({p.url for p, _ in frame_hits}),
            suggested_action={
                'summary': 'Render the embedded content as HTML on the page',
                'steps': ['Publish the key facts from the embedded document as page text',
                          'Keep the viewer only as an enhancement'],
                'priority': 'medium', 'effort': 'medium',
                'expected_benefit': 'The facts belong to the page crawlers read',
                'verification': 'The raw HTML contains the facts without the iframe'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_nontext_facts.py', 'rule_id': 'facts-in-iframe'}))

    return skill_result('crawl-render-audit', findings=findings,
                        metrics={'asset_links': len(assets), 'asset_probes': len(probes),
                                 'pdf_fact_hits': len(pdf_hits), 'image_fact_hits': len(img_hits),
                                 'iframe_fact_hits': len(frame_hits)})
