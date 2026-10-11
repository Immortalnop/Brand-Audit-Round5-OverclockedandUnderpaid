"""One bounded acquisition. All probes, redirects and HTML share one transport."""
from urllib.parse import urljoin,urlsplit,urlunsplit
from xml.etree import ElementTree as ET
from collections import Counter
from dataclasses import replace
from time import monotonic
import json
import re
from models import PageArtifact,AuditArtifacts,freeze_value
from url_safety import classify_url,same_origin
from instrumentation import Instrumentation
from transport import Transport,USER_AGENT
from tls_context import environment_summary
from robots_policy import RobotsPolicy
from html_features import Document
from structured_data import iter_nodes,types_of,normalize_type
from non_text import image_tokens,fact_keywords,is_excluded_image,image_kind,raster_dimensions,svg_text
from pdf_text import extract_pdf_text
from llms_txt import parse_llms_txt
from auth_pages import login_page_signals

_normalize_schema_type=normalize_type
_iter_jsonld_nodes=iter_nodes

def _normalized_origin(url):
    p=urlsplit(url);return f'{p.scheme}://{p.netloc}'

def normalize_url(url,base=None):
    # As browsers do (WHATWG URL parsing): drop tab and newline characters anywhere
    # and strip leading and trailing spaces and control characters, so href="culture "
    # resolves to /culture, not /culture%20.
    url=re.sub(r'[\t\n\r]','',url or '').strip('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f ')
    if not url and not base:return None
    p=urlsplit(urljoin(base,url) if base else url)
    if p.scheme not in ('http','https') or not p.hostname:return None
    # Preserve query parameters: they may identify real content. Strip only fragments.
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',p.query,''))

def site_section(url):
    """First path segment of a URL ('/about/team' -> 'about'), '' for the root."""
    try:path=urlsplit(url).path
    except ValueError:return ''
    return next((s.lower() for s in path.split('/') if s),'')

def stratify_by_section(urls):
    """Reorder URLs round-robin across site sections, keeping each section's own
    order. A sitemap listed section by section would otherwise fill a bounded
    crawl with one section; this samples every section once before any section
    gets a second page, so the sample covers more templates."""
    groups={}
    for u in urls:groups.setdefault(site_section(u),[]).append(u)
    out=[];lanes=list(groups.values());i=0
    while lanes:
        lanes=[lane for lane in lanes if len(lane)>i]
        out.extend(lane[i] for lane in lanes);i+=1
    return out

_LISTING_INDEXES=frozenset({'blog','news','articles','press','insights','stories'})

def _classify_page_type(url,origin,jsonld_blocks,path):
    types=set().union(*(types_of(n) for n in iter_nodes(jsonld_blocks)))
    if (path or '/')=='/':return 'home'
    for names,kind in [({'SoftwareApplication','MobileApplication','WebApplication'},'software'),({'Service'},'service'),({'Product','Offer','IndividualProduct'},'product'),({'Article','BlogPosting','NewsArticle'},'article'),({'ContactPage'},'contact'),({'AboutPage'},'about')]:
        if types & names:return kind
    # The index of an editorial section (/blog/, /news) lists articles; it is not
    # one itself, so it is held to no article markup. It is not a shop category
    # either, so commerce checks leave it alone.
    if (path or '/').strip('/').lower() in _LISTING_INDEXES:return 'listing'
    for pattern,kind in [('services?','service'),('product|products|item|items|shop|store|sku','product'),('blog|news|article|articles|press|insights|stories','article'),('contact|contact-us|get-in-touch','contact'),('about|about-us|company|team|who-we-are','about'),('privacy|terms|legal|cookie|tos','legal'),('category|categories|collection|collections|catalog','category')]:
        if re.search(r'/(?:'+pattern+r')(?:/|-|$)',path,re.I):return kind
    return 'other'

def _extract_page(url,resp,fetch_ms,limits,fetch_status='ok'):
    ctype=resp.headers.get('Content-Type','') if resp else ''
    html=resp.text if resp and resp.ok and ('html' in ctype or not ctype) else ''
    doc=Document();warnings=[]
    try:doc.feed(html);doc.close()
    except (ValueError,RecursionError):warnings.append('html_parse_incomplete')
    blocks=[]
    for raw in doc.jsonld:
        try:blocks.append(json.loads(raw))
        except (ValueError,RecursionError):warnings.append('malformed_jsonld_block')
    base=getattr(resp,'final_url',url) if resp else url
    internal=[];external=[]
    for href,_ in doc.links:
        try:link=normalize_url(href,base)
        except ValueError:continue
        if not link:continue
        (internal if same_origin(link,base) else external).append(link)
    visible=' '.join(doc.text)[:limits.VISIBLE_TEXT_MAX_CHARS]
    if resp is None:warnings.append('fetch_'+fetch_status)
    if resp and resp.redirect_hops:warnings.append(f'redirected_{resp.redirect_hops}_hop(s)')
    if resp and resp.truncated:warnings.append('response_truncated_at_byte_budget')
    if resp and resp.ok and ctype and 'html' not in ctype:warnings.append('non_html_content')
    try:canonical=urljoin(base,doc.canonical) if doc.canonical else None
    except ValueError:canonical=None
    features=doc.features()
    features['visible_text_complete']=features['full_visible_chars']<=limits.VISIBLE_TEXT_MAX_CHARS
    features['html_bytes']=len(resp.content) if resp and html else 0
    features['network_duration_ms']=getattr(resp,'network_duration_ms',None) if resp else None
    features['redirect_hops']=resp.redirect_hops if resp else 0
    images=[]
    for record in features.get('image_records',())[:limits.MAX_IMAGE_RECORDS_PER_PAGE]:
        try:src=normalize_url(record['src'],base)
        except ValueError:continue
        if src:images.append({**record,'src':src})
    features['image_records']=images
    breadcrumb=next((n for n in iter_nodes(blocks) if 'BreadcrumbList' in types_of(n)),None)
    return PageArtifact(url=url,status_code=resp.status_code if resp else None,content_type=ctype,
        evidence_snippet=visible[:limits.EVIDENCE_SNIPPET_MAX_CHARS] or None,visible_text=visible,
        title=' '.join(''.join(doc.title_parts).split()) or None,
        meta_description=next(iter(doc.meta.get('description',[])),None),canonical_url=canonical,
        headings=tuple(doc.headings[:50]),internal_links=tuple(dict.fromkeys(internal))[:200],external_links=tuple(dict.fromkeys(external))[:200],
        jsonld_blocks=tuple(freeze_value(b) for b in blocks),page_type=_classify_page_type(url,_normalized_origin(url),blocks,urlsplit(url).path),
        fetch_duration_ms=fetch_ms,render_status='not_rendered',breadcrumb_visible=tuple(doc.breadcrumb[:20]),breadcrumb_schema=freeze_value(breadcrumb),
        ai_crawler_directives=freeze_value({}),warnings=tuple(warnings),features=freeze_value(features),
        response_headers=freeze_value(dict(resp.headers) if resp else {}),final_url=base)

_SITEMAP_CHUNK=65536

def _parse_sitemap(content,truncated):
    """(kind, locs, entries) from a sitemap read incrementally: kind is 'urlset' or
    'sitemapindex', locs the <loc> of every complete entry, entries the complete
    <url> elements. A sitemap cut off at the byte budget still yields every entry
    that arrived whole. Raises ET.ParseError for a document that is not a sitemap,
    is malformed (before the cut, when cut), declares a DTD or entities, or was cut
    off before its first complete entry."""
    if b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():raise ET.ParseError('DTD not allowed')
    parser=ET.XMLPullParser(events=('start','end'))
    kind=None;depth=0;locs=[];entries=[]
    def consume():
        nonlocal kind,depth
        for event,elem in parser.read_events():
            name=elem.tag.rsplit('}',1)[-1] if isinstance(elem.tag,str) else ''
            if event=='start':
                depth+=1
                if depth==1:
                    kind=name
                    if kind not in ('urlset','sitemapindex'):raise ET.ParseError('not a sitemap')
                continue
            depth-=1
            # A direct child of the root that ended is a complete entry.
            if depth==1 and name in ('url','sitemap'):
                loc=next((c.text.strip() for c in elem if isinstance(c.tag,str) and c.tag.rsplit('}',1)[-1]=='loc' and c.text),None)
                if loc:locs.append(loc)
                if name=='url':entries.append(elem)
    try:
        for start in range(0,len(content),_SITEMAP_CHUNK):
            parser.feed(content[start:start+_SITEMAP_CHUNK]);consume()
        if not truncated:parser.close();consume()
    except ET.ParseError:
        # Only a document cut off at the budget may end mid-element. Entries the
        # parser completed before the cut are still read.
        if not truncated:raise
        try:consume()
        except ET.ParseError:pass
        if kind not in ('urlset','sitemapindex'):raise
    if kind is None or (truncated and not locs):raise ET.ParseError('no sitemap entries')
    return kind,locs,entries

def _collect_lastmod(tree,origin,lastmods,url_entries,cap=200):
    """Raw <lastmod> text per <url> entry of a urlset, keyed by normalized <loc>.
    Values are kept as written; the freshness skill parses and judges them."""
    for entry in tree:
        if not isinstance(entry.tag,str) or entry.tag.rsplit('}',1)[-1]!='url':continue
        url_entries[0]+=1
        loc=lastmod=None
        for child in entry:
            name=child.tag.rsplit('}',1)[-1] if isinstance(child.tag,str) else ''
            if name=='loc' and child.text:loc=child.text.strip()
            elif name=='lastmod' and child.text:lastmod=child.text.strip()[:64]
        if not loc or not lastmod or len(lastmods)>=cap:continue
        try:key=normalize_url(loc,origin)
        except ValueError:continue
        if key:lastmods.setdefault(key,lastmod)

def _collect_sitemap_hreflang(tree,origin,out,cap=200):
    """xhtml:link rel="alternate" hreflang annotations per <url> entry, keyed by
    normalized <loc>. Kept as written; the international check judges them."""
    for entry in tree:
        if not isinstance(entry.tag,str) or entry.tag.rsplit('}',1)[-1]!='url' or len(out)>=cap:continue
        loc=None;alternates=[]
        for child in entry:
            name=child.tag.rsplit('}',1)[-1] if isinstance(child.tag,str) else ''
            if name=='loc' and child.text:loc=child.text.strip()
            elif name=='link' and child.get('rel','').strip().lower()=='alternate' and child.get('hreflang') is not None and len(alternates)<20:
                alternates.append({'hreflang':child.get('hreflang','').strip()[:40],'href':(child.get('href') or '').strip()[:500]})
        if not loc or not alternates:continue
        try:key=normalize_url(loc,origin)
        except ValueError:continue
        if key:out.setdefault(key,alternates)

AI_CRAWLERS=('OAI-SearchBot','ChatGPT-User','GPTBot','Claude-SearchBot','ClaudeBot','Googlebot','Google-Extended','PerplexityBot','CCBot')

def _ai_crawler_directives(rp,origin,conservative):
    if conservative:return {}
    return {a:'allow' if rp.can_fetch(a,origin) else 'disallow' for a in AI_CRAWLERS}

def _ai_crawler_section_blocks(rp,urls,conservative,cap=40):
    """{crawler: [sample URLs]} for site sections an AI crawler may not fetch while
    crawlers in general may: one sample URL per section (first path segment) of the
    URLs discovered, judged by robots.txt rules alone, with no request. Sections
    closed to every crawler are a general robots choice, not an AI-specific one."""
    if conservative:return {}
    samples={}
    for u in sorted(urls,key=lambda u:(len(u),u)):
        section=site_section(u)
        if section and section not in samples and len(samples)<cap:samples[section]=u
    out={}
    for agent in AI_CRAWLERS:
        blocked=[u for _,u in sorted(samples.items()) if rp.can_fetch('*',u) and not rp.can_fetch(agent,u)]
        if blocked:out[agent]=blocked[:10]
    return out

_SENSITIVE_ROUTE=re.compile(r'/(?:logout|signout|admin|wp-admin|checkout|cart|account)(?:/|$)',re.I)

# Media fetch outcomes that mean no request reached the server.
_NOT_REQUESTED=frozenset({'not_attempted','cross_origin_not_fetched','robots_disallowed','blocked','deadline',
                          'budget_exhausted','cross_origin_redirect_blocked'})

def _int_attr(value):
    return int(value) if isinstance(value,str) and re.fullmatch(r'[0-9]{1,6}',value.strip()) else None

def _fetch_image(tr,entry,limits):
    """Bounded GET for one same-origin image: SVG text, or raster header dimensions."""
    svg=entry['kind']=='svg'
    cap=limits.MAX_SVG_BYTES if svg else limits.MAX_IMAGE_HEADER_BYTES
    r,st=tr.get(entry['url'],max_bytes=cap,headers=None if svg else {'Range':f'bytes=0-{cap-1}'})
    if st!='ok':entry['fetch_status']=st;return st
    if not r.ok:entry['fetch_status']=f'http_{r.status_code}';return st
    ctype=r.headers.get('Content-Type','')
    entry['fetch_status']='ok';entry['content_type']=ctype.split(';')[0].strip().lower() or None
    kind=image_kind(entry['url'],ctype)
    if kind=='svg':
        entry['kind']='svg'
        status,text=('truncated','') if r.truncated else svg_text(r.content)
        entry['svg_status']=status;entry['svg_text']=text
    elif ctype.lower().startswith(('text/','application/')):
        entry['fetch_status']='not_image'
    else:
        dims=raster_dimensions(r.content)
        entry['kind']='raster'
        if dims:entry['format'],entry['width'],entry['height']=dims
        entry['bytes_total']=_total_size(r)
    return st

def _total_size(r):
    """Full file size of a response to a Range GET: the total in Content-Range, or
    Content-Length when the server ignored the range, or the body length when the
    whole file arrived. None when unknown."""
    m=re.match(r'\s*bytes\s+\d+-\d+/(\d+)',r.headers.get('Content-Range',''),re.I)
    if m:return int(m.group(1))
    if r.status_code==200:
        length=r.headers.get('Content-Length','').strip()
        if length.isdigit():return int(length)
        if not r.truncated:return len(r.content)
    return None

# Advertised like a browser, so a server that negotiates formats can answer with AVIF or WebP.
_IMAGE_ACCEPT='image/avif,image/webp,image/apng,image/*;q=0.8,*/*;q=0.5'

def _probe_image_weight(tr,entry,limits):
    """Range GET of the first bytes of one same-origin image: total size, served
    format and pixel dimensions. Pixels are never decoded."""
    cap=limits.IMAGE_WEIGHT_PROBE_BYTES
    r,st=tr.get(entry['url'],max_bytes=cap,headers={'Range':f'bytes=0-{cap-1}','Accept':_IMAGE_ACCEPT})
    entry['weight_probe']=True
    if st!='ok':entry['fetch_status']=st;return st
    if not r.ok:entry['fetch_status']=f'http_{r.status_code}';return st
    ctype=r.headers.get('Content-Type','').split(';')[0].strip().lower()
    if not ctype.startswith('image/'):entry['fetch_status']='not_image';return st
    entry['fetch_status']='ok';entry['content_type']=ctype;entry['accept_sent']=True
    if ctype=='image/svg+xml':entry['kind']='svg';return st
    entry['kind']='raster'
    dims=raster_dimensions(r.content)
    if dims:entry['format'],entry['width'],entry['height']=dims
    entry['bytes_total']=_total_size(r)
    return st

def _probe_text_file(tr,url,max_bytes):
    """Presence of a plain-text companion file such as /llms-full.txt. Only the
    start is read: the file can be large, and presence and type need no more."""
    r,st=tr.get(url,max_bytes=max_bytes)
    if st!='ok':return {'present':False,'status':'blocked' if st in ('blocked','robots_disallowed','cross_origin_redirect_blocked') else 'inaccessible','fetch_status':st}
    if r.status_code in (404,410):return {'present':False,'status':'absent','http_status':r.status_code}
    if not r.ok:return {'present':False,'status':'inaccessible','http_status':r.status_code}
    head=r.text[:2048].lstrip().lower()
    html='html' in r.headers.get('Content-Type','').lower() or head.startswith(('<html','<!doctype'))
    valid=not html and len(r.text.strip())>=10 and urlsplit(r.final_url).path==urlsplit(url).path
    return {'present':valid,'status':'ok' if valid else 'malformed','bytes_read':len(r.content),'truncated':r.truncated,
            'served_html':html}

def _verify_llms_links(tr,llms,pages,origin,limits):
    """Does each page listed in llms.txt resolve? Crawled pages reuse their crawl
    result; others get a bounded, robots-checked, same-origin GET. Cross-origin
    links are listed but not requested."""
    crawled={}
    for p in pages:
        for u in (p.url,p.final_url):
            if u:crawled.setdefault(u,p.status_code)
    checks=[];fetched=0;stopped=None
    for link in llms.get('links',())[:100]:
        try:url=normalize_url(link)
        except ValueError:url=None
        item={'url':link}
        if not url:item['status']='invalid_url'
        elif not same_origin(url,origin):item['status']='cross_origin_not_checked'
        elif url in crawled:
            code=crawled[url];item.update(status='ok' if code and 200<=code<300 else 'broken' if code in (404,410) else 'unverified',http_status=code,source='crawl')
        elif tr.robots is not None and not tr.robots.can_fetch(USER_AGENT,url):item['status']='robots_disallowed'
        elif _SENSITIVE_ROUTE.search(urlsplit(url).path):item['status']='sensitive_route_not_checked'
        elif stopped or fetched>=limits.MAX_LLMS_LINK_CHECKS:item['status']=stopped or 'check_cap_reached'
        else:
            fetched+=1
            r,st=tr.get(url,max_bytes=limits.LLMS_LINK_CHECK_BYTES)
            if st in ('deadline','budget_exhausted'):stopped=st
            if st!='ok':item.update(status='unverified',fetch_status=st)
            else:item.update(status='ok' if r.ok else 'broken' if r.status_code in (404,410) else 'unverified',http_status=r.status_code,source='fetch')
        checks.append(item)
    llms['link_checks']=checks
    llms['link_summary']=dict(Counter(c['status'] for c in checks),requests=fetched)

def _probe_https(tr,origin,pages,limits,instrumentation,allow_private):
    """One GET of https://<host>/robots.txt when pages were served over plain HTTP.
    robots.txt is the one path every crawler may request, so the probe needs no
    robots permission of its own, and it is charged to the shared request and byte
    budget. Any HTTP answer over verified TLS means HTTPS is available."""
    if urlsplit(origin).scheme!='http' or not any(p.status_code==200 for p in pages):return {'status':'not_applicable'}
    if tr.requests>=limits.MAX_TOTAL_HTTP_REQUESTS or tr.bytes>=limits.MAX_TOTAL_BYTES:return {'status':'not_checked','fetch_status':'budget_exhausted'}
    host=urlsplit(origin).hostname or ''
    https_origin='https://'+(f'[{host}]' if ':' in host else host)
    probe=Transport(https_origin,tr.deadline,limits,instrumentation,allow_private)
    # Same host, so the same pacing: crawl-delay and the gap since the last request carry over.
    probe.delay=tr.delay;probe.last_request=tr.last_request
    url=https_origin+'/robots.txt'
    r,st=probe.get(url,robots_exempt=True,max_bytes=4096)
    tr.requests+=probe.requests;tr.bytes+=probe.bytes;tr.diagnostics.extend(probe.diagnostics)
    if st=='ok':return {'status':'available','url':url,'http_status':r.status_code}
    if st in ('deadline','budget_exhausted','blocked'):return {'status':'not_checked','url':url,'fetch_status':st}
    return {'status':'unavailable','url':url,'fetch_status':st}

def _acquire_media(tr,pages,pdf_links,origin,limits):
    """Facts locked in non-text media: bounded, same-origin, robots-checked GETs
    for the images most likely to carry facts and for linked PDFs. Runs after the
    page crawl, so it only spends request, byte and time budget the crawl left."""
    images={}
    for p in pages:
        for record in (p.features or {}).get('image_records',()):
            url=record['src'];entry=images.get(url)
            if entry is None:
                if len(images)>=400:continue
                tokens=image_tokens(url,record.get('alt'),record.get('title'))
                entry=images[url]={'url':url,'pages':[],'alt':record.get('alt'),'title':record.get('title'),
                    'width_attr':_int_attr(record.get('width')),'height_attr':_int_attr(record.get('height')),
                    'kind':image_kind(url),'keywords':list(fact_keywords(tokens)),'excluded':is_excluded_image(tokens),
                    'same_origin':same_origin(url,origin),'fetch_status':'not_attempted'}
            if p.url not in entry['pages'] and len(entry['pages'])<5:entry['pages'].append(p.url)
            if record.get('lcp'):entry['lcp']=True
            if record.get('srcset') or record.get('picture_types'):entry['responsive']=True
    candidates=[e for e in images.values() if e['keywords']]
    large_svg=[e for e in images.values() if not e['keywords'] and not e['excluded'] and e['kind']=='svg'
               and ((e['width_attr'] or 0)>=300 or (e['height_attr'] or 0)>=200)]
    for entry in candidates:
        if not entry['same_origin']:entry['fetch_status']='cross_origin_not_fetched'
    queue=[]
    for e in candidates+large_svg:
        if not e['same_origin'] or _SENSITIVE_ROUTE.search(urlsplit(e['url']).path):continue
        # Robots is checked before selection so a disallowed asset never takes a fetch slot.
        if tr.robots is not None and not tr.robots.can_fetch(USER_AGENT,e['url']):e['fetch_status']='robots_disallowed';continue
        queue.append(e)
    stopped=None
    for entry in queue[:limits.MAX_IMAGE_FETCHES]:
        if stopped:entry['fetch_status']=stopped;continue
        st=_fetch_image(tr,entry,limits)
        if st in ('deadline','budget_exhausted'):stopped=st
    # Image weight: the largest same-origin content images, likely LCP images first.
    # Images named as facts keep their own fetch above; one already read there is
    # measured from that response and never requested twice.
    def icon_sized(e):
        dims=[d for d in (e['width_attr'],e['height_attr']) if d is not None]
        return bool(dims) and (min(dims)<48 or max(dims)<100)
    weight=[e for e in images.values() if e['same_origin'] and not e['excluded'] and not e['keywords']
            and e['kind']!='svg' and not icon_sized(e) and not _SENSITIVE_ROUTE.search(urlsplit(e['url']).path)
            and (tr.robots is None or tr.robots.can_fetch(USER_AGENT,e['url']))]
    weight.sort(key=lambda e:(not e.get('lcp'),-((e['width_attr'] or 0)*(e['height_attr'] or 0)),e['url']))
    for entry in weight[:limits.MAX_IMAGE_WEIGHT_PROBES]:
        if stopped:break
        st=_probe_image_weight(tr,entry,limits)
        if st in ('deadline','budget_exhausted'):stopped=st
    pdfs=[]
    selected=0
    for url,sources in pdf_links.items():
        if selected>=limits.MAX_PDF_FETCHES or len(pdfs)>=2*limits.MAX_PDF_FETCHES:break
        if _SENSITIVE_ROUTE.search(urlsplit(url).path):continue
        doc={'url':url,'linked_from':list(sources),'fetch_status':'not_attempted','extraction':'not_attempted'}
        pdfs.append(doc)
        if tr.robots is not None and not tr.robots.can_fetch(USER_AGENT,url):doc['fetch_status']='robots_disallowed';continue
        selected+=1
        if stopped:doc['fetch_status']=stopped;continue
        r,st=tr.get(url,max_bytes=limits.MAX_PDF_BYTES)
        if st in ('deadline','budget_exhausted'):stopped=st
        if st!='ok':doc['fetch_status']=st;continue
        if not r.ok:doc['fetch_status']=f'http_{r.status_code}';continue
        doc['fetch_status']='ok';doc['bytes']=len(r.content);doc['truncated']=r.truncated
        remaining=tr.deadline-monotonic()
        if remaining<1.0:doc['extraction']='deadline';continue
        parsed=extract_pdf_text(r.content,time_budget_s=min(limits.PDF_PARSE_BUDGET_S,remaining-0.5),truncated=r.truncated)
        doc['extraction']=parsed.pop('status');doc.update(parsed)
    kept=[e for e in images.values() if e['keywords'] or e['fetch_status']!='not_attempted'][:60]
    attempted=lambda e:e['fetch_status'] not in _NOT_REQUESTED
    return {'images':kept,'pdfs':pdfs,
            'summary':{'images_observed':sum((p.features or {}).get('images',0) for p in pages),
                       'unique_image_urls':len(images),'fact_keyword_images':len(candidates),
                       'image_fetches_attempted':sum(attempted(e) for e in images.values()),
                       'images_fetched_ok':sum(e['fetch_status']=='ok' for e in images.values()),
                       'svg_text_read':sum(e.get('svg_status')=='ok' for e in images.values()),
                       'pdfs_discovered':len(pdf_links),
                       'pdfs_fetch_attempted':sum(attempted(d) for d in pdfs),
                       'pdfs_text_extracted':sum(d['extraction']=='ok' for d in pdfs),
                       'image_fetch_cap':limits.MAX_IMAGE_FETCHES,'pdf_fetch_cap':limits.MAX_PDF_FETCHES,
                       'image_weight_candidates':len(weight),
                       'image_weight_probes':sum(1 for e in images.values() if e.get('weight_probe')),
                       'image_weight_probe_cap':limits.MAX_IMAGE_WEIGHT_PROBES,
                       # Per-item outcomes so an unfetched or unread item is always explained.
                       'image_fetch_outcomes':dict(Counter(e['fetch_status'] for e in kept)),
                       'pdf_outcomes':[{'url':d['url'],'fetch_status':d['fetch_status'],'extraction':d['extraction']}
                                       for d in pdfs]}}

# Seconds the acquisition stage must still have left to re-anchor on a new origin.
_REANCHOR_MIN_S=20.0

def acquire_site(site_url,deadline,limits,instrumentation=None,allow_private_targets=False):
    """One bounded acquisition of the site at site_url.

    When the start URL (or robots.txt) answers with a redirect to another origin
    (example.so to example.com, http to https) and no page could be analyzed, the
    audit re-anchors once on the redirect target: it validates the target against
    the SSRF policy, reads that origin's own robots.txt and audits that origin only.
    The report records both URLs. Redirects to other origins met during the crawl
    are never followed."""
    i=instrumentation or Instrumentation();i.start_memory_tracking();i.start_stage('acquisition')
    artifacts,moved=_acquire_origin(site_url,deadline,limits,i,allow_private_targets)
    target,reason=_reanchor_target(artifacts,moved,deadline,allow_private_targets)
    if target:
        artifacts,_=_acquire_origin(target,deadline,limits,i,allow_private_targets,
                                    start_redirect=dict(moved,requested_url=artifacts.site_url,audited_url=target))
    elif reason:
        artifacts=replace(artifacts,warnings=artifacts.warnings+(reason,))
    i.end_stage('acquisition')
    return artifacts

def _reanchor_target(artifacts,moved,deadline,allow_private):
    """(target URL, None) when the audit should move to the origin the start URL
    redirected to; (None, warning) when it redirected but cannot move; (None, None)
    when there was no such redirect or the first origin was audited."""
    if not moved:return None,None
    coverage=(artifacts.acquisition_metadata or {}).get('coverage') or {}
    if coverage.get('urls_analyzed'):return None,None
    target=normalize_url(moved.get('to') or '')
    if not target or same_origin(target,artifacts.normalized_origin):return None,None
    note=(f"The start URL {artifacts.site_url} redirects to another site, {target}; ")
    # The target must resolve and pass the SSRF policy now; an unresolvable target
    # is reported, never retried.
    check=classify_url(target,allow_private=allow_private)
    if check.reason in ('dns_resolution_failed','dns_resolution_error'):
        return None,note+'that address could not be resolved, so it was not audited.'
    if not check.safe:
        return None,note+'that address is not allowed by the safety policy, so it was not audited.'
    left=min(deadline.deadline_monotonic,deadline.stage_deadlines['acquisition'])-monotonic()
    if left<_REANCHOR_MIN_S:
        return None,note+'too little time was left to audit it. Run the audit on that URL.'
    return target,None

def _acquire_origin(site_url,deadline,limits,i,allow_private_targets,start_redirect=None):
    """Acquisition of one origin: (AuditArtifacts, moved), where moved describes a
    redirect of the start URL or robots.txt to another origin ({'from','to',
    'http_status','via'}), or is None."""
    site_url=normalize_url(site_url) or site_url;origin=_normalized_origin(site_url)
    check=classify_url(site_url,allow_private=allow_private_targets)
    if not check.safe and check.reason not in ('dns_resolution_failed','dns_resolution_error'):
        i.record_safety_block(site_url,check.reason)
        return AuditArtifacts(site_url,origin,(),freeze_value({'allowed_general':False,'status':'not_checked','ai_crawler_directives':{}}),freeze_value({'present':False,'status':'not_checked'}),freeze_value({'discovered':False,'status':'not_checked','urls':[]}),freeze_value({'pages_crawled':0,'total_bytes':0,'total_requests':0}),('initial_url_blocked:'+check.reason,)),None
    tr=Transport(origin,min(deadline.deadline_monotonic,deadline.stage_deadlines['acquisition']),limits,i,allow_private_targets)
    warnings=[];probe_failures=[];moved=None
    if start_redirect:
        warnings.append(f"The start URL {start_redirect['requested_url']} redirects to another site "
                        f"({start_redirect['audited_url']}); that site was audited instead, after reading its own "
                        f"robots.txt.")
    robots_url=urljoin(origin,'/robots.txt');resp,status=tr.get(robots_url,robots_exempt=True,max_bytes=512_000)
    if status=='cross_origin_redirect_blocked' and tr.last_cross_origin_redirect:
        # The whole host moved: robots.txt itself redirects. The start URL's path is
        # kept on the new origin.
        dest=urlsplit(tr.last_cross_origin_redirect['to']);start=urlsplit(site_url)
        if dest.scheme in ('http','https') and dest.netloc:
            moved={'from':site_url,'to':urlunsplit((dest.scheme,dest.netloc,start.path or '/',start.query,'')),
                   'http_status':tr.last_cross_origin_redirect.get('http_status'),'via':'robots_txt'}
    robots_attempts=[status]
    retryable={'tls_certificate_error','tls_handshake_error','tls_protocol_error','connection_error','dns_error','timeout','failed'}
    if status in retryable and limits.MAX_FETCH_RETRIES>0 and monotonic()<tr.deadline:
        i.record_retry()
        resp,status=tr.get(robots_url,robots_exempt=True,max_bytes=512_000)
        robots_attempts.append(status)
    if status!='ok':probe_failures.append({'url':robots_url,'reason':'tls_certificate_error' if 'tls_certificate_error' in robots_attempts else status,'final_outcome':status,'attempt_outcomes':robots_attempts})
    elif resp.status_code not in (200,404):probe_failures.append({'url':robots_url,'reason':'http_error','http_status':resp.status_code})
    if status!='ok':robots_status='timeout' if status=='timeout' else 'blocked' if status=='blocked' else 'inaccessible';robots_text=None
    elif resp.status_code==404:robots_status='absent';robots_text=''
    elif resp.status_code!=200:robots_status='inaccessible';robots_text=None
    else:
        try:
            robots_text=resp.content.decode('utf-8','strict')
            if resp.truncated or robots_text.lstrip().lower().startswith(('<html','<!doctype')):raise ValueError()
            robots_status='ok'
        except (ValueError,UnicodeDecodeError):robots_status='malformed';robots_text=None
    conservative=robots_text is None
    rp=RobotsPolicy(robots_text if not conservative else 'User-agent: *\nDisallow: /')
    tr.robots=rp;tr.delay=max(tr.delay,rp.crawl_delay(USER_AGENT))
    if conservative:warnings.append(f'robots_txt_{robots_status}_conservative_crawl')
    general_disallow=None if conservative else not rp.can_fetch(USER_AGENT,site_url)
    directives=_ai_crawler_directives(rp,site_url,conservative)
    sitemap={'discovered':False,'status':'not_checked','urls':[]};llms={'present':False,'status':'not_checked'}
    # Probe failures never justify fetching blocked pages, including under blanket disallow.
    if not conservative:
        maps=list(dict.fromkeys(rp.sitemaps or [urljoin(origin,'/sitemap.xml')]))[:4];seen_maps=set();locs=[];statuses=[]
        lastmods={};url_entries=[0];sitemap_hreflang={};checked=[];partial=[]
        while maps and len(seen_maps)<4:
            sm=urljoin(origin,maps.pop(0))
            if sm in seen_maps:continue
            seen_maps.add(sm);r,st=tr.get(sm,max_bytes=512_000)
            if st=='tls_certificate_error':probe_failures.append({'url':sm,'reason':st})
            if st!='ok':outcome='blocked' if st in ('robots_disallowed','blocked','cross_origin_redirect_blocked') else 'inaccessible'
            elif r.status_code==404:outcome='absent'
            elif not r.ok:outcome='inaccessible'
            else:
                # A gzipped sitemap is decompressed by the transport, within the same byte cap.
                try:
                    kind,found,entries=_parse_sitemap(r.content,r.truncated)
                    if kind=='sitemapindex':maps.extend(found[:4-len(seen_maps)])
                    else:
                        locs.extend(found[:200-len(locs)])
                        _collect_lastmod(entries,origin,lastmods,url_entries)
                        _collect_sitemap_hreflang(entries,origin,sitemap_hreflang)
                    outcome='ok'
                    # Larger than the read budget: every complete entry read is used,
                    # and the sitemap is not reported as malformed.
                    if r.truncated:partial.append(sm)
                except ET.ParseError:outcome='malformed'
            statuses.append(outcome)
            if len(checked)<8:checked.append({'url':sm,'status':outcome,'truncated':bool(r and st=='ok' and r.truncated)})
        sitemap={'discovered':'ok' in statuses,'status':'ok' if 'ok' in statuses else next(iter(statuses),'not_checked'),'urls':list(dict.fromkeys(locs))[:200],
                 'url_entries':url_entries[0],'lastmod':lastmods,'hreflang':sitemap_hreflang,'checked':checked,
                 'partial':partial}
        r,st=tr.get(urljoin(origin,'/llms.txt'),max_bytes=256_000)
        if st=='tls_certificate_error':probe_failures.append({'url':urljoin(origin,'/llms.txt'),'reason':st})
        if st!='ok':llms={'present':False,'status':'blocked' if st in ('blocked','robots_disallowed') else 'inaccessible'}
        elif r.status_code==404:llms={'present':False,'status':'absent'}
        elif not r.ok:llms={'present':False,'status':'inaccessible'}
        else:
            valid=not r.truncated and 'html' not in r.headers.get('Content-Type','').lower() and not r.text.lstrip().lower().startswith(('<html','<!doctype')) and len(r.text.strip())>=10 and urlsplit(r.final_url).path=='/llms.txt'
            llms={'present':valid,'status':'ok' if valid else 'malformed'}
            if valid:llms.update(parse_llms_txt(r.text,r.final_url))
        llms['full']=_probe_text_file(tr,urljoin(origin,'/llms-full.txt'),limits.LLMS_FULL_PROBE_BYTES)
    queue=[(site_url,0)];visited=set();discovered={site_url};pages=[];blocked=set();pdf_links={}
    # Login pages: fetched (a public, read-only GET) but kept out of the analyzed
    # sample, with the reason listed in coverage.
    login_pages=[];out_of_scope=[]
    sitemap_urls=[]
    for raw in sitemap['urls']:
        try:u=normalize_url(raw,origin)
        except ValueError:continue
        if u and same_origin(u,origin) and u not in discovered:sitemap_urls.append(u);discovered.add(u)
    queue.extend((u,1) for u in stratify_by_section(sitemap_urls))
    # Login pages count toward the page cap, so the number of page fetches, and
    # with it the run time, never grows.
    while queue and monotonic()<tr.deadline and len(pages)+len(login_pages)<limits.MAX_PAGES_CRAWLED:
        url,depth=queue.pop(0)
        if url in visited:i.record_deduplicated();continue
        visited.add(url)
        if depth>limits.MAX_CRAWL_DEPTH:i.record_skip('max_crawl_depth_exceeded');continue
        if conservative:i.record_skip('robots_permission_unknown');continue
        if not rp.can_fetch(USER_AGENT,url):blocked.add(url);i.record_skip('robots_disallowed');continue
        if _SENSITIVE_ROUTE.search(urlsplit(url).path):i.record_skip('sensitive_route');continue
        tr.last_cross_origin_redirect=None
        start=monotonic();r,st=tr.get(url)
        for _ in range(limits.MAX_FETCH_RETRIES):
            if st not in retryable:break
            i.record_retry();r,st=tr.get(url)
        if url==site_url and st=='cross_origin_redirect_blocked' and tr.last_cross_origin_redirect and not moved:
            moved=dict(tr.last_cross_origin_redirect,via='start_url')
        if st in ('deadline','budget_exhausted'):break
        if st in ('robots_disallowed','blocked'):blocked.add(url);continue
        page=_extract_page(url,r,int((monotonic()-start)*1000),limits,st)
        signals=login_page_signals(url,page.final_url,page.title,page.headings,page.features,page.jsonld_blocks) if page.status_code and 200<=page.status_code<300 else []
        if signals:
            login_pages.append(page);i.record_skip('login_page_out_of_scope')
            if len(out_of_scope)<20:
                out_of_scope.append({'url':url,'final_url':page.final_url,'reason':'login_page','signals':signals})
            if url==site_url:
                warnings.append(f'The start URL {url} is a login page ({", ".join(signals)}); it was left out of the '
                                f'audit, which never signs in. Audit a public page such as the home page instead.')
        else:pages.append(page)
        # Real final URLs resolve relative links; fragments are canonicalized before queueing.
        if r and r.final_url!=url:visited.add(r.final_url)
        links=sorted(page.internal_links,key=lambda u:(not bool(re.search(r'/(about|contact|product|pricing|blog|docs)',u)),u))
        for link in links:
            if not same_origin(link,origin):continue
            if re.search(r'\.pdf(?:$|\?)',link,re.I):
                sources=pdf_links.setdefault(link,[])
                if page.url not in sources and len(sources)<5:sources.append(page.url)
                continue
            if re.search(r'\.(pdf|zip|png|jpg|jpeg|svg|gif|mp4|css|js)(?:$|\?)',link,re.I):continue
            discovered.add(link)
            if link not in visited:queue.append((link,depth+1))
    if queue:i.record_skip('acquisition_limit_reached')
    # Every fetched page, login pages included: they answered a request.
    fetched=pages+login_pages
    https_probe=_probe_https(tr,origin,fetched,limits,i,allow_private_targets)
    if llms.get('links'):_verify_llms_links(tr,llms,fetched,origin,limits)
    media=_acquire_media(tr,pages,pdf_links,origin,limits)
    ok=[p for p in pages if p.status_code and 200<=p.status_code<300];analyzed=[p for p in ok if p.visible_text or p.jsonld_blocks or (p.features or {}).get('scripts')]
    timed=[p for p in fetched if 'fetch_timeout' in p.warnings]
    cov={'urls_discovered':len(discovered),'urls_fetched_attempted':len(fetched),'urls_fetched_ok':len(ok)+len(login_pages),'urls_fetched_error':sum(bool(p.status_code and p.status_code>=400) for p in fetched),
         'urls_blocked':len(blocked),'urls_timed_out':len(timed),'urls_failed_other':sum(p.status_code is None and p not in timed for p in fetched),
         'urls_out_of_scope':len(login_pages),'out_of_scope_pages':out_of_scope,
         'start_url_out_of_scope':any(p.url==site_url for p in login_pages),
         'urls_analyzed':len(analyzed),'urls_never_attempted':max(0,len(discovered)-len(fetched)),'skip_reason_counts':dict(Counter(i.pages_skipped_reasons)),
         # Representativeness of the sample: site sections (first path segment)
         # discovered versus sections with at least one analyzed page.
         'sections_discovered':len({site_section(u) for u in discovered}),
         'sections_analyzed':len({site_section(p.final_url or p.url) for p in analyzed}),
         'page_types_analyzed':sorted({p.page_type for p in analyzed if p.page_type})}
    section_blocks=_ai_crawler_section_blocks(rp,discovered,conservative)
    metadata={'transport_diagnostics':tr.diagnostics,'transport_environment':environment_summary(),'probe_failures':probe_failures,'https_probe':https_probe,'pages_crawled':len(pages),'total_bytes':tr.bytes,'total_requests':tr.requests,'coverage':cov}
    if start_redirect:metadata['start_redirect']=start_redirect
    return AuditArtifacts(site_url,origin,tuple(pages),freeze_value({'allowed_general':robots_status in ('ok','absent'),'status':robots_status,'conservative_fail_closed':conservative,'general_disallow':general_disallow,'ai_crawler_directives':directives,'ai_crawler_section_blocks':section_blocks,'fetch_outcome':status,'attempt_outcomes':robots_attempts}),
        freeze_value(llms),freeze_value(sitemap),freeze_value(metadata),tuple(warnings),
        media_data=freeze_value(media)),moved
