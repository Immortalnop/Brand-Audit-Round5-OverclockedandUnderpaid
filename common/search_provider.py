"""Optional GET search adapter. No external service is required by the default audit."""
import os,json,time
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from dataclasses import replace
from transport import Transport
from constants import DEFAULT_LIMITS
from instrumentation import Instrumentation
class SearchProviderError(Exception):pass

def is_configured():return bool(os.environ.get('SEARCH_API_URL'))

def search(query,max_results,timeout_s):
    url=os.environ.get('SEARCH_API_URL')
    if not url:raise SearchProviderError('SEARCH_API_URL not configured')
    try:
        p=urlsplit(url)
        url=urlunsplit((p.scheme,p.netloc,p.path,urlencode(parse_qsl(p.query)+[('q',query),('limit',str(max_results))]),''))
        headers={}
        if os.environ.get('SEARCH_API_KEY'):headers['Authorization']='Bearer '+os.environ['SEARCH_API_KEY']
        limits=replace(DEFAULT_LIMITS,MAX_TOTAL_BYTES=512_000,MAX_TOTAL_HTTP_REQUESTS=3,PER_FETCH_TIMEOUT_MS=int(timeout_s*1000))
        tr=Transport(f'{p.scheme}://{p.netloc}',time.monotonic()+timeout_s,limits,Instrumentation())
        resp,status=tr.get(url,robots_exempt=True,headers=headers)
        if status!='ok' or not resp.ok or resp.truncated:raise SearchProviderError('Search response unavailable or incomplete')
        data=json.loads(resp.text)
        values=data.get('results',[]) if isinstance(data,dict) else data
        if not isinstance(values,list):raise SearchProviderError('Invalid search response shape')
        return [{k:str(r.get(k,'')) for k in ('title','url','snippet')} for r in values[:max_results] if isinstance(r,dict)]
    except (OSError,ValueError,TypeError) as exc:raise SearchProviderError('Search provider failed') from exc
