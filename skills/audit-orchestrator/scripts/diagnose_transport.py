"""Bounded robots-only diagnostics using the same verified acquisition transport."""
import json
import sys
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'common'))
from constants import Limits
from dataclasses import replace
from instrumentation import Instrumentation
from transport import Transport
from tls_context import environment_summary
from robots_policy import RobotsPolicy
from subprocess_isolation import run_isolated


def diagnose(target):
    if '://' not in target:target='https://'+target
    part=urlsplit(target);origin=f'{part.scheme}://{part.netloc}'
    url=origin+'/robots.txt'
    tr=Transport(origin,monotonic()+9,replace(Limits(),MAX_TOTAL_HTTP_REQUESTS=8),Instrumentation())
    response,status=tr.get(url,robots_exempt=True,max_bytes=512000)
    attempts=[status]
    if status in ('tls_certificate_error','tls_handshake_error','tls_protocol_error','connection_error','dns_error','timeout','failed'):
        response,status=tr.get(url,robots_exempt=True,max_bytes=512000);attempts.append(status)
    policy=None
    if status=='ok' and response.status_code in (200,404) and not response.truncated:
        try:
            text=response.content.decode('utf-8','strict') if response.status_code==200 else ''
            if text.lstrip().lower().startswith(('<html','<!doctype')):raise ValueError('HTML response')
            policy=RobotsPolicy(text)
        except (UnicodeDecodeError,ValueError):pass
    return {'url':url,'attempt_outcomes':attempts,'http_status':response.status_code if response else None,
            'environment':environment_summary(),'transport_diagnostics':tr.diagnostics,
            'crawler_policy':{agent:('allow' if policy.can_fetch(agent,target) else 'disallow')
                              for agent in ('OAI-SearchBot','GPTBot','Googlebot','PerplexityBot')} if policy else 'not_checked',
            'verification_note':'A repeat uses the same client and trust policy. It is not independent verification of a site defect.'}

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python diagnose_transport.py https://target.example')
    result=run_isolated(diagnose,args=(sys.argv[1],),timeout_s=10)
    print(json.dumps(result.value if result.ok else {'status':'diagnostic_incomplete','error':result.error},indent=2))
