"""Technical SEO and social preview observations over the one acquisition snapshot.

No new requests: the HTTPS-availability probe for HTTP-served sites is made by
acquire_site.py through the shared Transport and read here from
acquisition_metadata['https_probe']. Missing hints are opportunities, not proof
of ranking failure.
Canonical and preview URLs are examined as strings and are never dereferenced.
"""
import re
from urllib.parse import urlsplit, urljoin
from check_helpers import content_pages, observation
from models import skill_result
from url_safety import same_origin

CHECK_IDS = frozenset({'http-transport','redirect-chain','missing-title','missing-description',
    'missing-canonical','invalid-canonical','cross-origin-canonical','missing-language',
    'missing-landmarks','heading-hierarchy','social-metadata','social-url','twitter-card','title-length'})


def valid_http_url(value):
    try:
        p = urlsplit(value)
        return (p.scheme in ('http','https') and bool(p.hostname) and not p.username and not p.password
                and (p.port is None or 0 < p.port < 65536)
                and not any(c.isspace() or ord(c)<32 for c in value))
    except ValueError:
        return False


def analyze_metadata(artifacts, deadline):
    pages = content_pages(artifacts)
    out = []
    def emit(rid,title,selected,detail,**kw):
        if selected:
            out.append(observation(rid,title,selected,{p.url:detail(p) for p in selected},**kw))
    if deadline.expired():
        return skill_result('crawl-render-audit', status='insufficient_evidence', warnings=['Metadata checks skipped: deadline reached.'])
    http_pages = [p for p in pages if urlsplit(p.final_url or p.url).scheme=='http']
    if http_pages:
        host = urlsplit(http_pages[0].final_url or http_pages[0].url).hostname
        probe = artifacts.acquisition_metadata.get('https_probe') or {}
        https_ok = bool(probe.get('https_available'))
        status_detail = f"status {probe.get('status')}" if probe.get('status') else None
        if https_ok:
            emit('http-transport','HTTPS is available but not enforced (missing HTTP to HTTPS redirect)',
                 http_pages,
                 lambda p:f"HTTPS connection to https://{host}/ succeeded ({status_detail}), but page was retrieved over unencrypted HTTP: {p.final_url or p.url}",
                 confirmed=True,severity='high')
        else:
            emit('http-transport','Sampled content was retrieved over HTTP',
                 http_pages,
                 lambda p:'Retrieved URL: '+(p.final_url or p.url),confirmed=True,severity='high')
    emit('redirect-chain','Sampled URLs require multiple redirects',
         [p for p in pages if p.features.get('redirect_hops',0)>2],
         lambda p:f"Observed {p.features['redirect_hops']} hops; final URL: {p.final_url}",confirmed=True,severity='medium')
    emit('missing-title','Pages lack a document title',[p for p in pages if not (p.title or '').strip()],
         lambda p:'No nonempty title was parsed from the complete HTML response.',confirmed=True,severity='medium')
    emit('missing-description','Review missing page descriptions',[p for p in pages if not (p.meta_description or '').strip()],
         lambda p:'No nonempty meta description was observed; a search engine can still extract a summary.')
    emit('missing-language','Pages omit an explicit document language',[p for p in pages if not (p.features.get('lang') or '').strip()],
         lambda p:'The html lang attribute is absent or empty.',confirmed=True,severity='low')
    emit('missing-landmarks','Review primary content landmarks',
         [p for p in pages if len(p.visible_text.split())>=100 and not p.features.get('landmarks')],
         lambda p:'No main or article landmark observed on a page with substantial text.')
    emit('heading-hierarchy','Review skipped heading levels',
         [p for p in pages if len(p.features['heading_levels'])>=3 and any(b>a+1 for a,b in zip(p.features['heading_levels'],p.features['heading_levels'][1:]))],
         lambda p:'Observed heading levels: '+str(list(p.features['heading_levels'][:20])))
    emit('title-length','Review unusually short or long titles',
         [p for p in pages if p.title and not 15<=len(p.title)<=70],
         lambda p:f'Title has {len(p.title)} characters: {p.title[:100]}. Display width was not measured.')
    missing,invalid,external=[],[],[]
    canon_details={}
    for p in pages:
        values=p.features.get('canonical_values',())
        if not values:missing.append(p);continue
        try:resolved=[urljoin(p.final_url or p.url,v) for v in values]
        except ValueError:
            invalid.append(p);canon_details[p.url]='Malformed canonical declaration: '+str(list(values))[:500]
            continue
        if any(not v.strip() for v in values) or len(set(resolved))>1 or any(not valid_http_url(v) or urlsplit(v).fragment for v in resolved):
            invalid.append(p);canon_details[p.url]='Declared canonical values: '+str(list(values))[:500]
        elif resolved and not same_origin(resolved[0],p.final_url or p.url):
            external.append(p);canon_details[p.url]='External canonical hint: '+resolved[0]
    emit('missing-canonical','Review preferred URL declarations',missing,
         lambda p:'No rel=canonical declaration observed. Duplicate content was not established.')
    emit('invalid-canonical','Canonical declarations are unusable or conflicting',invalid,
         lambda p:canon_details[p.url],confirmed=True,severity='medium')
    emit('cross-origin-canonical','Review external canonical targets',external,lambda p:canon_details[p.url])
    shareable=[p for p in pages if p.page_type not in ('legal',)]
    og_required=('og:title','og:description','og:image','og:url')
    emit('social-metadata','Review incomplete Open Graph preview metadata',
         [p for p in shareable if any(not any(v.strip() for v in p.features['meta'].get(k,())) for k in og_required)],
         lambda p:'Missing nonempty fields: '+', '.join(k for k in og_required if not any(v.strip() for v in p.features['meta'].get(k,()))))
    emit('social-url','Open Graph URL fields need review',
         [p for p in shareable if any(not valid_http_url(v) for k in ('og:image','og:url') for v in p.features['meta'].get(k,()))],
         lambda p:'One or more og:image or og:url values are not absolute HTTP(S) URLs. Assets were not fetched.')
    emit('twitter-card','Review Twitter Card declarations',
         [p for p in shareable if not any(v.strip().lower() in ('summary','summary_large_image','app','player') for v in p.features['meta'].get('twitter:card',()))],
         lambda p:'No supported nonempty twitter:card declaration observed. Platform fallback was not tested.')
    return skill_result('crawl-render-audit', findings=out, metrics={'metadata_pages_analyzed':len(pages)},
                        coverage={'pages_analyzed':len(pages),'pages_skipped':len(artifacts.pages)-len(pages)})
