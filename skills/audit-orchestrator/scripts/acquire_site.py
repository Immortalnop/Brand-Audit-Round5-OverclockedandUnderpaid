"""One bounded acquisition. All probes, redirects and HTML share one transport.

ROBOTS_POLICY -- what each robots.txt outcome permits, and where this audit is
deliberately stricter than RFC 9309:

  ok                 parsed; its groups are obeyed for every request.
  absent (404/410)   unambiguous: no robots file, so unrestricted (RFC 2.3.1.3).
  unavailable_4xx    any other 4xx (401, 403, 405, 451 ...). RFC 2.3.1.3 would
                     permit unrestricted access; this audit records permission as
                     UNKNOWN and crawls nothing beyond the homepage diagnostic
                     below. A 401 or 403 is the server refusing this client, not
                     a statement that no robots file exists, and an audit that
                     crawls anyway is presuming a permission it was not given.
  rate_limited (429) also a 4xx by the RFC's classification, and likewise treated
                     as permission unknown here. The RFC does not mandate
                     disallow for 429; this is project policy.
  challenged         robots.txt itself is behind a bot wall: permission unknown.
  inaccessible (5xx) RFC 2.3.1.4 requires assuming complete disallow.
  timeout/malformed  permission unknown; nothing is crawled.

THE ONE EXCEPTION, stated so "fail-closed" is never claimed without it: when
permission is unknown *because the server refused or throttled us* --
unavailable_4xx, rate_limited or challenged -- exactly one robots-exempt GET of
the homepage is made, to tell "only robots.txt is refused" apart from "the whole
site is refused". There are no robots directives to violate in those cases
(none were obtained), it is a single request, and no link found on that page is
followed. robots_data['homepage_diagnostic'] records whether it was used, and
execution_summary lists it under limitations. For timeout, malformed and 5xx the
server is already failing or unparsable, so not even that request is made.
"""
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
from access_guard import classify_access
from auth_pages import login_page_signals
from url_keys import strip_tracking,visit_key,template_key,intent_of
from constants import AI_AGENTS,FACT_KEYWORDS
import heapq
from dataclasses import replace as _replace

_normalize_schema_type=normalize_type
_iter_jsonld_nodes=iter_nodes

def _normalized_origin(url):
    p=urlsplit(url);return f'{p.scheme}://{p.netloc}'

def normalize_url(url,base=None):
    # Browsers strip leading and trailing whitespace from an href (WHATWG URL
    # parsing), so href="/culture " is the page /culture, not a broken URL.
    url=(url or '').strip()
    p=urlsplit(urljoin(base,url) if base else url)
    if p.scheme not in ('http','https') or not p.hostname:return None
    # Preserve query parameters: they may identify real content. Strip fragments and
    # pure tracking parameters (utm_*, gclid, ...), which never identify content.
    return strip_tracking(urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',p.query,'')))

def _classify_page_type(url,origin,jsonld_blocks,path):
    types=set().union(*(types_of(n) for n in iter_nodes(jsonld_blocks)))
    if (path or '/')=='/':return 'home'
    for names,kind in [({'SoftwareApplication','MobileApplication','WebApplication'},'software'),({'Service'},'service'),({'Product','Offer','IndividualProduct'},'product'),({'Article','BlogPosting','NewsArticle'},'article'),({'ContactPage'},'contact'),({'AboutPage'},'about')]:
        if types & names:return kind
    # An editorial section index (/blog/, /news, /press) lists articles; it is not
    # one, so it is not held to Article markup. Markup above still wins.
    if re.fullmatch(r'/(?:blog|news|press|articles|insights|stories|updates)/?',path or '',re.I):return 'listing'
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
    # A bot-protection interstitial is not the site's content. It is kept in
    # the snapshot as evidence, flagged, and excluded from every content check.
    access=classify_access(resp.status_code if resp else None,resp.headers if resp else {},
                           resp.text if resp else '',features['full_visible_chars']) if resp else {'kind':'ok','vendor':None,'signals':[]}
    features['access']=access
    if access['kind']=='challenge':warnings.append('bot_challenge')
    elif access['kind']=='rate_limited':warnings.append('rate_limited')
    elif resp is not None and resp.ok:
        # A login page is public but is not content: it is kept out of the
        # analysed sample and listed in coverage (common/auth_pages.py).
        signals=login_page_signals(url,base,' '.join(''.join(doc.title_parts).split()),doc.headings,doc.heading_levels,features,blocks)
        if signals:warnings.append('login_page');features['login_signals']=signals
    features['visible_text_complete']=features['full_visible_chars']<=limits.VISIBLE_TEXT_MAX_CHARS
    features['html_bytes']=len(resp.content) if resp and html else 0
    features['network_duration_ms']=getattr(resp,'network_duration_ms',None) if resp else None
    features['redirect_hops']=resp.redirect_hops if resp else 0
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

def _ai_crawler_directives(rp,origin,conservative):
    if conservative:return {}
    return {a:'allow' if rp.can_fetch(a,origin) else 'disallow' for a,_ in AI_AGENTS}

def _ai_crawler_paths(rp,key_urls,conservative):
    """Evaluate every agent against the key URLs actually sampled (homepage,
    one URL per key intent, sitemap, llms.txt), not just '/'. Returns
    {agent: [blocked key URLs]} for agents blocked somewhere."""
    if conservative:return {}
    out={}
    for agent,_ in AI_AGENTS:
        blocked=[u for u in key_urls if not rp.can_fetch(agent,u)]
        if blocked:out[agent]=blocked
    return out

_FACT_RE=re.compile(r'(?<![a-z])('+'|'.join(re.escape(k) for k in FACT_KEYWORDS)+r')(?![a-z])',re.I)
_ASSET_RE=re.compile(r'\.(pdf|docx?|xlsx?|pptx?)(?:$|\?)',re.I)

def _probe_https(host,tr,limits,i,allow_private_targets):
    """Is HTTPS available for an http-served site? One GET of /robots.txt on the
    https origin -- the URL a crawler may always request -- so the probe never
    exempts itself from an origin whose robots.txt it has not read.

    The probe runs on its own Transport (it targets a different origin), but it
    starts from the shared request and byte counters and hands them back, so its
    request is spent OUT OF the audit's allowance rather than added beside it."""
    probe_tr=Transport('https://'+host,tr.deadline,limits,i,allow_private_targets)
    probe_tr.delay=tr.delay;probe_tr.last_request=tr.last_request  # same host: same crawl-delay courtesy
    probe_tr.requests=tr.requests;probe_tr.bytes=tr.bytes          # one shared allowance
    url='https://'+host+'/robots.txt'
    pr,pst=probe_tr.get(url,robots_exempt=True,max_bytes=8192)
    used=probe_tr.requests-tr.requests
    tr.requests=probe_tr.requests;tr.bytes=probe_tr.bytes
    return {'attempted':True,'probe_url':url,'https_available':pst=='ok',
            'status':pr.status_code if pr else None,'outcome':pst,
            'requests_used':used}


def acquire_site(site_url,deadline,limits,instrumentation=None,allow_private_targets=False,seed_urls=None):
    """seed_urls (targeted mode): audit exactly these same-origin pages plus the
    homepage, without sampling the sitemap or following links."""
    i=instrumentation or Instrumentation();i.start_memory_tracking();i.start_stage('acquisition')
    site_url=normalize_url(site_url) or site_url;origin=_normalized_origin(site_url)
    check=classify_url(site_url,allow_private=allow_private_targets)
    if not check.safe and check.reason not in ('dns_resolution_failed','dns_resolution_error'):
        i.record_safety_block(site_url,check.reason);i.end_stage('acquisition')
        return AuditArtifacts(site_url,origin,(),freeze_value({'allowed_general':False,'status':'not_checked','ai_crawler_directives':{}}),freeze_value({'present':False,'status':'not_checked'}),freeze_value({'discovered':False,'status':'not_checked','urls':[]}),freeze_value({'pages_crawled':0,'total_bytes':0,'total_requests':0}),('initial_url_blocked:'+check.reason,))
    tr=Transport(origin,min(deadline.deadline_monotonic,deadline.stage_deadlines['acquisition']),limits,i,allow_private_targets)
    warnings=[];probe_failures=[];challenged_probes=[];robots_url=urljoin(origin,'/robots.txt');resp,status=tr.get(robots_url,robots_exempt=True,max_bytes=512_000)
    robots_attempts=[status]
    retryable={'tls_certificate_error','tls_handshake_error','tls_protocol_error','connection_error','dns_error','timeout','failed'}
    if status in retryable and limits.MAX_FETCH_RETRIES>0 and monotonic()<tr.deadline:
        i.record_retry()
        resp,status=tr.get(robots_url,robots_exempt=True,max_bytes=512_000)
        robots_attempts.append(status)
    if status!='ok':probe_failures.append({'url':robots_url,'reason':'tls_certificate_error' if 'tls_certificate_error' in robots_attempts else status,'final_outcome':status,'attempt_outcomes':robots_attempts})
    elif resp.status_code not in (200,404,410):probe_failures.append({'url':robots_url,'reason':'http_error','http_status':resp.status_code})
    robots_access={'kind':'ok','vendor':None,'signals':[]}
    if status!='ok':robots_status='timeout' if status=='timeout' else 'blocked' if status=='blocked' else 'inaccessible';robots_text=None
    else:
        robots_access=classify_access(resp.status_code,resp.headers,resp.text,len(resp.text))
        if robots_access['kind']=='challenge':
            # Robots.txt itself sits behind a bot challenge. Permission is unknown,
            # so no crawl -- but one homepage request is made below to tell "only the
            # robots file is challenged" apart from "the whole site is challenged".
            robots_status='challenged';robots_text=None
        elif robots_access['kind']=='rate_limited':
            # A 429 is a 4xx, which RFC 9309 2.3.1.3 classifies as "unavailable"
            # (no restrictions). This audit does not take that permission: a
            # server actively rate-limiting us has not told us what we may crawl,
            # so permission is recorded as unknown. That is this project's policy,
            # stricter than the RFC, not an RFC requirement. One homepage request
            # below shows whether the content itself is also refused.
            robots_status='rate_limited';robots_text=None
        elif resp.status_code in (404,410):robots_status='absent';robots_text=''
        elif 400<=resp.status_code<500:
            # Any other 4xx (401, 403, 405, 451 ...). RFC 9309 2.3.1.3 would allow
            # unrestricted access here; this audit fails closed instead, because a
            # 401/403 is the server refusing *us* rather than saying "there is no
            # robots file". Deliberately stricter than the RFC; see
            # ROBOTS_POLICY below.
            robots_status='unavailable_4xx';robots_text=None
        elif resp.status_code!=200:
            # RFC 9309 2.3.1.4: a 5xx or network failure is "unreachable" and the
            # RFC itself requires assuming complete disallow.
            robots_status='inaccessible';robots_text=None
        else:
            try:
                robots_text=resp.content.decode('utf-8','strict')
                if resp.truncated or robots_text.lstrip().lower().startswith(('<html','<!doctype')):raise ValueError()
                robots_status='ok'
            except (ValueError,UnicodeDecodeError):robots_status='malformed';robots_text=None
    requests_after_robots=tr.requests
    conservative=robots_text is None
    rp=RobotsPolicy(robots_text if not conservative else 'User-agent: *\nDisallow: /')
    tr.robots=rp;tr.delay=max(tr.delay,rp.crawl_delay(USER_AGENT))
    if conservative:warnings.append(f'robots_txt_{robots_status}_conservative_crawl')
    general_disallow=None if conservative else not rp.can_fetch(USER_AGENT,site_url)
    directives=_ai_crawler_directives(rp,site_url,conservative)
    sitemap={'discovered':False,'status':'not_checked','urls':[]};llms={'present':False,'status':'not_checked'}
    # Probe failures never justify fetching blocked pages, including under blanket disallow.
    if not conservative:
        maps=list(dict.fromkeys(rp.sitemaps or [urljoin(origin,'/sitemap.xml')]))[:4];seen_maps=set();locs=[];statuses=[];lastmods={}
        url_entries=0;lastmod_entries=0
        while maps and len(seen_maps)<4:
            sm=urljoin(origin,maps.pop(0))
            if sm in seen_maps:continue
            seen_maps.add(sm);r,st=tr.get(sm,max_bytes=512_000)
            if st=='tls_certificate_error':probe_failures.append({'url':sm,'reason':st})
            if st=='ok' and classify_access(r.status_code,r.headers,r.text,len(r.text))['kind']=='challenge':
                challenged_probes.append({'url':sm,'status':r.status_code});statuses.append('challenged');continue
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
                    for entry in tree:
                        loc=lm=None
                        for child in entry:
                            name=child.tag.rsplit('}',1)[-1]
                            if name=='loc' and child.text:loc=child.text.strip()
                            elif name=='lastmod' and child.text:lm=child.text.strip()[:40]
                        if loc:url_entries+=1
                        if loc and lm:lastmod_entries+=1
                        if loc and lm and len(lastmods)<200:lastmods[loc]=lm
                statuses.append('ok')
            except ET.ParseError:statuses.append('malformed')
        sitemap={'discovered':'ok' in statuses,'status':'ok' if 'ok' in statuses else next(iter(statuses),'not_checked'),'urls':list(dict.fromkeys(locs))[:200],'lastmod':lastmods,
                 'url_entries':url_entries,'lastmod_entries':lastmod_entries}
        r,st=tr.get(urljoin(origin,'/llms.txt'),max_bytes=256_000)
        if st=='tls_certificate_error':probe_failures.append({'url':urljoin(origin,'/llms.txt'),'reason':st})
        if st=='ok' and classify_access(r.status_code,r.headers,r.text,len(r.text))['kind']=='challenge':
            challenged_probes.append({'url':urljoin(origin,'/llms.txt'),'status':r.status_code});llms={'present':False,'status':'challenged'}
        elif st!='ok':llms={'present':False,'status':'blocked' if st in ('blocked','robots_disallowed') else 'inaccessible'}
        elif r.status_code==404:llms={'present':False,'status':'absent'}
        elif not r.ok:llms={'present':False,'status':'inaccessible'}
        else:
            valid=not r.truncated and 'html' not in r.headers.get('Content-Type','').lower() and not r.text.lstrip().lower().startswith(('<html','<!doctype')) and len(r.text.strip())>=10 and urlsplit(r.final_url).path=='/llms.txt'
            llms={'present':valid,'status':'ok' if valid else 'malformed'}
    requests_after_discovery=tr.requests
    # Representative sampling. A priority frontier replaces the FIFO queue:
    # home first, then site-wide navigation/footer links, then key-intent pages,
    # then sitemap and body links -- and no URL template may take more than
    # MAX_PER_TEMPLATE pages, so one template (product versions, tag archives,
    # paginated lists) can never consume the whole page budget.
    heap=[];seq=[0];visited=set();discovered={visit_key(site_url)};pages=[];blocked=set();template_counts=Counter()
    cap=getattr(limits,'MAX_PER_TEMPLATE',3)
    def push(url,depth,source_rank):
        key=visit_key(url)
        if key in visited:return
        intent=intent_of(url)
        seq[0]+=1
        # The About page is the passage the AG-01 quotability check judges; once a
        # link to it is seen it is fetched next, ahead of the rest of the frontier.
        if intent in ('about','about-us','company','team'):source_rank=0
        heapq.heappush(heap,(1 if template_counts[template_key(url)]>=cap else 0,source_rank,0 if intent else 1,depth,url,seq[0],depth,source_rank,intent))
    push(site_url,0,0)
    sitemap_urls=[]
    for raw in sitemap['urls']:
        try:u=normalize_url(raw,origin)
        except ValueError:continue
        if u and same_origin(u,origin):sitemap_urls.append(u);discovered.add(visit_key(u))
    # Interleave sitemap URLs across first path segments so one huge section does
    # not dominate the sample.
    buckets={}
    for u in sitemap_urls:buckets.setdefault((urlsplit(u).path.strip('/').split('/') or [''])[0],[]).append(u)
    order=[];lists=[buckets[k] for k in sorted(buckets)]
    while any(lists):
        for lst in lists:
            if lst:order.append(lst.pop(0))
    targeted=[]
    for raw in seed_urls or ():
        u=normalize_url(raw,origin)
        if u and same_origin(u,origin):targeted.append(u);discovered.add(visit_key(u));push(u,0,0)
    if not targeted:
        for u in order:push(u,1,2)
    consecutive_challenges=0;challenge_stop=False
    # The single documented exception to fail-closed (see ROBOTS_POLICY): one
    # robots-exempt homepage GET when the server refused or throttled robots.txt.
    homepage_only=robots_status in ('challenged','rate_limited','unavailable_4xx')
    while heap and monotonic()<tr.deadline and len(pages)<limits.MAX_PAGES_CRAWLED:
        _,_,_,_,url,_,depth,source_rank,intent=heapq.heappop(heap)
        key=visit_key(url)
        if key in visited:i.record_deduplicated();continue
        visited.add(key)
        if depth>limits.MAX_CRAWL_DEPTH:i.record_skip('max_crawl_depth_exceeded');continue
        tkey=template_key(url)
        if template_counts[tkey]>=cap and source_rank>1 and not intent:i.record_skip('template_cap_reached');continue
        if conservative and not (homepage_only and url==site_url):i.record_skip('robots_permission_unknown');continue
        if not conservative and not rp.can_fetch(USER_AGENT,url):blocked.add(url);i.record_skip('robots_disallowed');continue
        if re.search(r'/(?:logout|signout|admin|wp-admin|checkout|cart|account)(?:/|$)',urlsplit(url).path,re.I):i.record_skip('sensitive_route');continue
        start=monotonic();r,st=tr.get(url,robots_exempt=homepage_only and url==site_url)
        for _ in range(limits.MAX_FETCH_RETRIES):
            if st not in retryable:break
            i.record_retry();r,st=tr.get(url,robots_exempt=homepage_only and url==site_url)
        if st in ('deadline','budget_exhausted'):break
        if st in ('robots_disallowed','blocked'):blocked.add(url);continue
        page=_extract_page(url,r,int((monotonic()-start)*1000),limits,st);pages.append(page)
        template_counts[tkey]+=1
        if r and r.final_url!=url:visited.add(visit_key(r.final_url))
        if {'bot_challenge','rate_limited'}&set(page.warnings):
            # Stop sampling a template that is being challenged, and stop the whole
            # crawl after a run of consecutive challenges (courtesy, no new evidence).
            template_counts[tkey]=max(template_counts[tkey],cap)
            consecutive_challenges+=1
            if consecutive_challenges>=getattr(limits,'MAX_CONSECUTIVE_CHALLENGES',3):
                challenge_stop=True;i.record_skip('access_challenge_stop');break
            continue  # never follow links found on an interstitial
        consecutive_challenges=0
        region={normalize_url(h,page.final_url or url) for h in (page.features or {}).get('region_links',())}
        for link in page.internal_links:
            if not same_origin(link,origin):continue
            if _ASSET_RE.search(link) or re.search(r'\.(png|jpg|jpeg|svg|gif|webp|mp4|css|js|zip)(?:$|\?)',link,re.I):continue
            discovered.add(visit_key(link))
            if visit_key(link) not in visited and not targeted:push(link,depth+1,1 if link in region else 3)
    if heap and not challenge_stop:i.record_skip('acquisition_limit_reached')
    requests_after_pages=tr.requests
    # Auxiliary diagnostics (the HTTPS probe and the PDF range reads) share one
    # allowance, taken OUT OF the global request budget rather than added beside
    # it: aux_left() is the binding constraint, so a diagnostic can never be the
    # request that pushes the audit past MAX_TOTAL_HTTP_REQUESTS.
    aux_cap=getattr(limits,'MAX_AUX_PROBE_REQUESTS',4)
    def aux_left():
        return min(aux_cap-(tr.requests-requests_after_pages),limits.MAX_TOTAL_HTTP_REQUESTS-tr.requests)
    # The HTTPS-availability probe for HTTP-served sites runs here, through a
    # Transport (budgeted, SSRF-checked, logged), instead of inside an analysis
    # script. It asks for /robots.txt on the https origin, not the homepage: that
    # is the one URL a crawler may always request, so the probe needs no robots
    # exemption on an origin whose permissions it has not read, and a completed
    # TLS handshake plus HTTP response already answers "is HTTPS available?".
    https_probe={'attempted':False}
    home_page=next((p for p in pages if p.url==site_url),None)
    if home_page and urlsplit(home_page.final_url or home_page.url).scheme=='http' and monotonic()<tr.deadline:
        host=urlsplit(home_page.final_url or home_page.url).netloc
        if aux_left()>=1:
            https_probe=_probe_https(host,tr,limits,i,allow_private_targets)
        else:
            https_probe={'attempted':False,'skipped':'request_allowance_exhausted'}
            i.record_skip('https_probe_request_allowance_exhausted')
    # Record document links (PDF/Office) instead of silently dropping them, and
    # range-read up to MAX_ASSET_PROBES key-fact PDFs to see if they carry a text layer.
    asset_links=[];seen_assets=set()
    for p in pages:
        if {'bot_challenge','rate_limited'}&set(p.warnings):continue
        for href,text in (p.features or {}).get('anchors',()):
            link=normalize_url(href,p.final_url or p.url) if href else None
            if not link or not same_origin(link,origin) or not _ASSET_RE.search(link) or link in seen_assets:continue
            seen_assets.add(link)
            asset_links.append({'url':link,'anchor':(text or '')[:120],'linked_from':p.url,
                                'fact_keyword':bool(_FACT_RE.search(link.rsplit('/',1)[-1]) or _FACT_RE.search(text or ''))})
    asset_probes=[]
    for a in [a for a in asset_links if a['fact_keyword'] and a['url'].lower().split('?')[0].endswith('.pdf')][:getattr(limits,'MAX_ASSET_PROBES',3)]:
        if monotonic()>=tr.deadline or conservative or aux_left()<1:break
        if not rp.can_fetch(USER_AGENT,a['url']):continue
        ar,ast=tr.get(a['url'],max_bytes=getattr(limits,'ASSET_PROBE_BYTES',65536))
        if ast!='ok' or not ar:asset_probes.append({'url':a['url'],'outcome':ast});continue
        asset_probes.append({'url':a['url'],'outcome':'ok','status':ar.status_code,'content_type':ar.headers.get('Content-Type',''),
                             'text_layer':(b'/Font' in ar.content) if ar.content.startswith(b'%PDF') else None})
    key_urls=[site_url]+[p.url for p in pages if intent_of(p.url)][:12]+[urljoin(origin,'/llms.txt')]+sitemap_urls[:1]
    ai_paths=_ai_crawler_paths(rp,list(dict.fromkeys(key_urls)),conservative)
    challenged=[p for p in pages if {'bot_challenge','rate_limited'}&set(p.warnings)]
    login=[p for p in pages if 'login_page' in p.warnings]
    if any(p.url==site_url for p in login):warnings.append('start_url_is_login_page')
    ok=[p for p in pages if p.status_code and 200<=p.status_code<300 and p not in challenged];analyzed=[p for p in ok if p not in login and (p.visible_text or p.jsonld_blocks or (p.features or {}).get('scripts'))]
    timed=[p for p in pages if 'fetch_timeout' in p.warnings]
    cov={'urls_discovered':len(discovered),'urls_fetched_attempted':len(pages),'urls_fetched_ok':len(ok),'urls_fetched_error':sum(bool(p.status_code and p.status_code>=400) for p in pages),
         'urls_blocked':len(blocked),'urls_timed_out':len(timed),'urls_failed_other':sum(p.status_code is None and p not in timed for p in pages),
         'urls_analyzed':len(analyzed),'urls_never_attempted':max(0,len(discovered)-len(pages)),'skip_reason_counts':dict(Counter(i.pages_skipped_reasons)),
         'urls_challenged':len(challenged),'templates_sampled':len({template_key(p.url) for p in analyzed}),
         'pages_per_template':dict(Counter(template_key(p.url) for p in analyzed).most_common(10)),
         'key_intents_found':sorted({intent_of(p.url) for p in analyzed if intent_of(p.url)}),
         'asset_links_found':len(asset_links),'challenge_stop':challenge_stop,
         'urls_out_of_scope':len(login),
         'out_of_scope_pages':[{'url':p.url,'reason':'login_page','signals':list((p.features or {}).get('login_signals',()))} for p in login][:20]}
    # Where every request of the shared allowance went. Robots reads, sitemap and
    # llms.txt probes, page fetches, redirect hops, retries and the auxiliary
    # diagnostics are all inside this one total -- no stage keeps a private
    # budget, so the numbers add up to total_requests by construction.
    accounting={'allowance':limits.MAX_TOTAL_HTTP_REQUESTS,'total':tr.requests,
                'robots':requests_after_robots,
                'sitemap_and_llms':requests_after_discovery-requests_after_robots,
                'pages':requests_after_pages-requests_after_discovery,
                'auxiliary_probes':tr.requests-requests_after_pages,
                'auxiliary_allowance':aux_cap,
                'redirect_hops_followed':i.redirects_followed,'retries':i.requests_retried,
                'remaining':max(0,limits.MAX_TOTAL_HTTP_REQUESTS-tr.requests)}
    i.end_stage('acquisition')
    return AuditArtifacts(site_url,origin,tuple(pages),freeze_value({'allowed_general':robots_status in ('ok','absent'),'status':robots_status,'conservative_fail_closed':conservative,
        # The one documented exception to fail-closed, so no reader has to infer it.
        'homepage_diagnostic':bool(conservative and homepage_only and any(p.url==site_url for p in pages)),
        'homepage_diagnostic_allowed':bool(conservative and homepage_only),
        'general_disallow':general_disallow,'ai_crawler_directives':directives,'ai_crawler_paths':ai_paths,'fetch_outcome':status,'attempt_outcomes':robots_attempts,
        'access':robots_access,'http_status':resp.status_code if resp else None}),
        freeze_value(llms),freeze_value(sitemap),freeze_value({'transport_diagnostics':tr.diagnostics,'transport_environment':environment_summary(),'probe_failures':probe_failures,'challenged_probes':challenged_probes,'https_probe':https_probe,
        'asset_links':asset_links[:60],'asset_probes':asset_probes,'pages_crawled':len(pages),'total_bytes':tr.bytes,'total_requests':tr.requests,
        'request_accounting':accounting,'coverage':cov}),tuple(warnings))
