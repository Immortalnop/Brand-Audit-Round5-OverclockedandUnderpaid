"""One bounded acquisition. All probes, redirects and HTML share one transport."""
from urllib.parse import urljoin,urlsplit,urlunsplit
from xml.etree import ElementTree as ET
from collections import Counter
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

_normalize_schema_type=normalize_type
_iter_jsonld_nodes=iter_nodes

def _normalized_origin(url):
    p=urlsplit(url);return f'{p.scheme}://{p.netloc}'

def normalize_url(url,base=None):
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

def _classify_page_type(url,origin,jsonld_blocks,path):
    types=set().union(*(types_of(n) for n in iter_nodes(jsonld_blocks)))
    if (path or '/')=='/':return 'home'
    for names,kind in [({'SoftwareApplication','MobileApplication','WebApplication'},'software'),({'Service'},'service'),({'Product','Offer','IndividualProduct'},'product'),({'Article','BlogPosting','NewsArticle'},'article'),({'ContactPage'},'contact'),({'AboutPage'},'about')]:
        if types & names:return kind
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

def _ai_crawler_directives(rp,origin,conservative):
    if conservative:return {}
    return {a:'allow' if rp.can_fetch(a,origin) else 'disallow' for a in ('OAI-SearchBot','ChatGPT-User','GPTBot','Claude-SearchBot','ClaudeBot','Googlebot','Google-Extended','PerplexityBot','CCBot')}

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

def acquire_site(site_url,deadline,limits,instrumentation=None,allow_private_targets=False):
    i=instrumentation or Instrumentation();i.start_memory_tracking();i.start_stage('acquisition')
    site_url=normalize_url(site_url) or site_url;origin=_normalized_origin(site_url)
    check=classify_url(site_url,allow_private=allow_private_targets)
    if not check.safe and check.reason not in ('dns_resolution_failed','dns_resolution_error'):
        i.record_safety_block(site_url,check.reason);i.end_stage('acquisition')
        return AuditArtifacts(site_url,origin,(),freeze_value({'allowed_general':False,'status':'not_checked','ai_crawler_directives':{}}),freeze_value({'present':False,'status':'not_checked'}),freeze_value({'discovered':False,'status':'not_checked','urls':[]}),freeze_value({'pages_crawled':0,'total_bytes':0,'total_requests':0}),('initial_url_blocked:'+check.reason,))
    tr=Transport(origin,min(deadline.deadline_monotonic,deadline.stage_deadlines['acquisition']),limits,i,allow_private_targets)
    warnings=[];probe_failures=[];robots_url=urljoin(origin,'/robots.txt');resp,status=tr.get(robots_url,robots_exempt=True,max_bytes=512_000)
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
        lastmods={};url_entries=[0];sitemap_hreflang={}
        while maps and len(seen_maps)<4:
            sm=urljoin(origin,maps.pop(0))
            if sm in seen_maps:continue
            seen_maps.add(sm);r,st=tr.get(sm,max_bytes=512_000)
            if st=='tls_certificate_error':probe_failures.append({'url':sm,'reason':st})
            if st!='ok':statuses.append('blocked' if st in ('robots_disallowed','blocked','cross_origin_redirect_blocked') else 'inaccessible');continue
            if r.status_code==404:statuses.append('absent');continue
            if not r.ok:statuses.append('inaccessible');continue
            try:
                if r.truncated or b'<!DOCTYPE' in r.content.upper() or b'<!ENTITY' in r.content.upper():raise ET.ParseError()
                tree=ET.fromstring(r.content);kind=tree.tag.rsplit('}',1)[-1]
                if kind not in ('urlset','sitemapindex'):raise ET.ParseError()
                found=[e.text.strip() for e in tree.iter() if e.tag.rsplit('}',1)[-1]=='loc' and e.text]
                if kind=='sitemapindex':maps.extend(found[:4-len(seen_maps)])
                else:
                    locs.extend(found[:200-len(locs)])
                    _collect_lastmod(tree,origin,lastmods,url_entries)
                    _collect_sitemap_hreflang(tree,origin,sitemap_hreflang)
                statuses.append('ok')
            except ET.ParseError:statuses.append('malformed')
        sitemap={'discovered':'ok' in statuses,'status':'ok' if 'ok' in statuses else next(iter(statuses),'not_checked'),'urls':list(dict.fromkeys(locs))[:200],
                 'url_entries':url_entries[0],'lastmod':lastmods,'hreflang':sitemap_hreflang}
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
    sitemap_urls=[]
    for raw in sitemap['urls']:
        try:u=normalize_url(raw,origin)
        except ValueError:continue
        if u and same_origin(u,origin) and u not in discovered:sitemap_urls.append(u);discovered.add(u)
    queue.extend((u,1) for u in stratify_by_section(sitemap_urls))
    while queue and monotonic()<tr.deadline and len(pages)<limits.MAX_PAGES_CRAWLED:
        url,depth=queue.pop(0)
        if url in visited:i.record_deduplicated();continue
        visited.add(url)
        if depth>limits.MAX_CRAWL_DEPTH:i.record_skip('max_crawl_depth_exceeded');continue
        if conservative:i.record_skip('robots_permission_unknown');continue
        if not rp.can_fetch(USER_AGENT,url):blocked.add(url);i.record_skip('robots_disallowed');continue
        if _SENSITIVE_ROUTE.search(urlsplit(url).path):i.record_skip('sensitive_route');continue
        start=monotonic();r,st=tr.get(url)
        for _ in range(limits.MAX_FETCH_RETRIES):
            if st not in retryable:break
            i.record_retry();r,st=tr.get(url)
        if st in ('deadline','budget_exhausted'):break
        if st in ('robots_disallowed','blocked'):blocked.add(url);continue
        page=_extract_page(url,r,int((monotonic()-start)*1000),limits,st);pages.append(page)
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
    https_probe=_probe_https(tr,origin,pages,limits,i,allow_private_targets)
    if llms.get('links'):_verify_llms_links(tr,llms,pages,origin,limits)
    media=_acquire_media(tr,pages,pdf_links,origin,limits)
    ok=[p for p in pages if p.status_code and 200<=p.status_code<300];analyzed=[p for p in ok if p.visible_text or p.jsonld_blocks or (p.features or {}).get('scripts')]
    timed=[p for p in pages if 'fetch_timeout' in p.warnings]
    cov={'urls_discovered':len(discovered),'urls_fetched_attempted':len(pages),'urls_fetched_ok':len(ok),'urls_fetched_error':sum(bool(p.status_code and p.status_code>=400) for p in pages),
         'urls_blocked':len(blocked),'urls_timed_out':len(timed),'urls_failed_other':sum(p.status_code is None and p not in timed for p in pages),
         'urls_analyzed':len(analyzed),'urls_never_attempted':max(0,len(discovered)-len(pages)),'skip_reason_counts':dict(Counter(i.pages_skipped_reasons)),
         # Representativeness of the sample: site sections (first path segment)
         # discovered versus sections with at least one analyzed page.
         'sections_discovered':len({site_section(u) for u in discovered}),
         'sections_analyzed':len({site_section(p.final_url or p.url) for p in analyzed}),
         'page_types_analyzed':sorted({p.page_type for p in analyzed if p.page_type})}
    i.end_stage('acquisition')
    return AuditArtifacts(site_url,origin,tuple(pages),freeze_value({'allowed_general':robots_status in ('ok','absent'),'status':robots_status,'conservative_fail_closed':conservative,'general_disallow':general_disallow,'ai_crawler_directives':directives,'fetch_outcome':status,'attempt_outcomes':robots_attempts}),
        freeze_value(llms),freeze_value(sitemap),freeze_value({'transport_diagnostics':tr.diagnostics,'transport_environment':environment_summary(),'probe_failures':probe_failures,'https_probe':https_probe,'pages_crawled':len(pages),'total_bytes':tr.bytes,'total_requests':tr.requests,'coverage':cov}),tuple(warnings),
        media_data=freeze_value(media))
