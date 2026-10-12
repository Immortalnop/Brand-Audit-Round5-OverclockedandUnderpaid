"""Measured retrieval and static loading hints; no browser timings or new fetches."""
from statistics import median
from check_helpers import eligible_pages, observation
from models import skill_result

CHECK_IDS = frozenset({'heavy-html','markup-ratio','blocking-scripts','image-sizing','fetch-latency','sitemap-unavailable'})


def analyze_performance(artifacts, deadline):
    pages=eligible_pages(artifacts)
    out=[]
    if deadline.expired():
        return skill_result('crawl-render-audit',status='insufficient_evidence',warnings=['Performance checks skipped: deadline reached.'])
    def emit(rid,title,selected,detail):
        if selected:
            out.append(observation(rid,title,selected,{p.url:detail(p) for p in selected},script='analyze_performance.py'))
    # Retain positive size evidence from byte-capped pages, but never infer absence.
    sized=[p for p in artifacts.pages if p.status_code==200 and p.features
           and p.features.get('observation_version')==2 and 'non_html_content' not in p.warnings]
    emit('heavy-html','Review large HTML response bodies',
         [p for p in sized if p.features.get('html_bytes',0)>400000 or 'response_truncated_at_byte_budget' in p.warnings],
         lambda p:f"Retained {p.features.get('html_bytes',0)} HTML body bytes; truncated: {'response_truncated_at_byte_budget' in p.warnings}. Asset transfer sizes were not measured.")
    emit('markup-ratio','Review HTML overhead relative to visible text',
         [p for p in pages if p.features.get('html_bytes',0)>30000 and p.features.get('full_visible_chars',0)>=400
          and p.features.get('full_visible_bytes',0)/p.features['html_bytes']<.08],
         lambda p:f"Visible text represents {p.features.get('full_visible_bytes',0)/p.features['html_bytes']:.1%} of decoded HTML body bytes. This is not a ranking metric.")
    emit('blocking-scripts','Review synchronous external head scripts',
         [p for p in pages if p.features.get('head_blocking_scripts',0)>=6],
         lambda p:f"Observed {p.features['head_blocking_scripts']} classic external head scripts without async/defer. First paint and execution costs were not measured.")
    emit('image-sizing','Review image space reservation and loading strategy',
         [p for p in pages if p.features['images']>=10 and p.features['images_missing_dims']/p.features['images']>.7 and not p.features['images_lazy']],
         lambda p:f"{p.features['images_missing_dims']}/{p.features['images']} images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.")
    timed=[p for p in pages if isinstance(p.features.get('network_duration_ms'),(int,float))]
    if timed and median(p.features['network_duration_ms'] for p in timed)>3000:
        emit('fetch-latency','Review slow sampled HTML retrieval',
             [p for p in timed if p.features['network_duration_ms']>3000],
             lambda p:f"Measured connection and response duration: {p.features['network_duration_ms']} ms, excluding pacing and earlier retries. This is not TTFB or a browser performance score.")
    # Never report a missing sitemap when permission or connectivity was unknown.
    if pages and artifacts.sitemap_data.get('status') in ('absent','malformed'):
        emit('sitemap-unavailable','Review the sampled sitemap endpoint',[pages[0]],
             lambda p:'Sitemap probe status: '+artifacts.sitemap_data['status']+'. No additional sitemap discovery was attempted by this check.')
    return skill_result('crawl-render-audit',findings=out,metrics={'performance_pages_analyzed':len(pages),
        'network_timing_pages':len(timed),'browser_performance_measured':False},
        coverage={'pages_analyzed':len(pages),'pages_skipped':len(artifacts.pages)-len(pages)})
