"""Fetch one bound raster candidate for Claude Read; fetching is not viewing.

This optional host-stage helper uses verified TLS, pinned public DNS, the audit
User-Agent, same-origin redirects and fail-closed robots. It never fetches HTML
to fill a packet gap. Its receipt belongs to the host, not the native ledger.
"""
import argparse
from dataclasses import replace
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'common'),str(ROOT/'skills/audit-orchestrator/scripts')]
from agent_handoff import pending_envelope
from agent_evidence import MAX_PACKET_BYTES
from constants import Limits
from instrumentation import Instrumentation
from json_boundary import read_json
from non_text import raster_dimensions
from report_markdown import read_report
from robots_policy import RobotsPolicy
from subprocess_isolation import run_isolated
from transport import Transport,USER_AGENT
from url_safety import same_origin

MAX_BYTES=3*1024*1024
MAX_SECONDS=20.


def _fetch(origin,url,seconds):
    limits=replace(Limits(),MAX_TOTAL_HTTP_REQUESTS=4,MAX_TOTAL_BYTES=MAX_BYTES+512000,
                   PER_FETCH_TIMEOUT_MS=5000,MAX_FETCH_RETRIES=0)
    instrument=Instrumentation()
    tr=Transport(origin,time.monotonic()+seconds,limits,instrument)
    robots,status=tr.get(origin+'/robots.txt',robots_exempt=True,max_bytes=512000)
    text=None
    if robots is not None and status=='ok' and not robots.truncated:
        if robots.status_code in (404,410):text=''
        elif robots.status_code==200:
            try:text=robots.content.decode('utf-8-sig')
            except UnicodeDecodeError:pass
            if text is not None and ('html' in robots.headers.get('Content-Type','').lower() or '<html' in text[:1000].lower() or '<!doctype' in text[:1000].lower()):text=None
    if text is None:
        return {'status':'robots_unavailable','requests':tr.requests,'bytes':tr.bytes}
    tr.robots=RobotsPolicy(text);tr.delay=max(tr.delay,tr.robots.crawl_delay(USER_AGENT))
    response,status=tr.get(url,max_bytes=MAX_BYTES)
    result={'status':status,'requests':tr.requests,'bytes':tr.bytes,
            'http_status':response.status_code if response is not None else None}
    if response is None or status!='ok':return result
    if response.status_code!=200:return dict(result,status='http_error')
    if response.truncated:return dict(result,status='image_byte_limit')
    dimensions=raster_dimensions(response.content)
    if dimensions is None or not 0<dimensions[1]*dimensions[2]<=20_000_000:
        return dict(result,status='unsupported_or_oversized_raster')
    return dict(result,status='fetched',content=response.content,format=dimensions[0],
                dimensions=dimensions[1:],final_url=response.final_url)


def fetch_candidate(report,packet,image_id,out_dir):
    pending_envelope(report,packet)
    image=next((i for i in packet['image_candidates'] if i['image_id']==image_id),None)
    if image is None or not image.get('page_evidence_ids'):raise ValueError('Image needs an acquired, exported parent page')
    url=image['url'];parts=urlsplit(packet['audited_url'])
    origin=f'{parts.scheme}://{parts.netloc}'
    if not same_origin(url,origin):raise ValueError('Image must be on the audited origin')
    try:
        deadline=datetime.fromisoformat(packet['timing']['agent_deadline_at'])
        if deadline.tzinfo is None:raise ValueError()
    except (KeyError,TypeError,ValueError) as exc:
        raise ValueError('Image fetch needs a valid bound UTC agent deadline') from exc
    left=(deadline-datetime.now(timezone.utc)).total_seconds()
    if left<25:raise ValueError('Less than 25 seconds remain; do not start an image fetch')
    directory=Path(out_dir)
    if any((directory/(image_id+'.'+suffix)).exists() for suffix in ('png','jpeg','gif','webp')):
        raise FileExistsError('An image output already exists; use a fresh output directory')
    receipt=directory/'agent-image-fetch.json'
    record={'image_id':image_id,'url':url,'started_at':datetime.now(timezone.utc).isoformat(),
            'image_viewed':False,'status':'started','budget_s':min(MAX_SECONDS,left-5),
            'max_requests':4,'max_bytes':MAX_BYTES+512000,'ledger_scope':'separate host-stage helper'}
    # One fetch per output directory, without retries or replacing old evidence.
    with receipt.open('x',encoding='utf-8') as out:json.dump(record,out)
    try:
        result=run_isolated(_fetch,args=(origin,url,record['budget_s']),timeout_s=record['budget_s'])
        if not result.ok:
            record.update(status='error',reason=result.error,measurements_unavailable=True)
        else:
            value=dict(result.value);content=value.pop('content',None)
            record.update(value)
            if content is not None:
                path=directory/(image_id+'.'+record['format'])
                with path.open('xb') as out:out.write(content)
                record['path']=str(path.resolve())
    except OSError as exc:
        record.update(status='error',reason=str(exc),image_viewed=False)
    record['finished_at']=datetime.now(timezone.utc).isoformat()
    record['after_agent_deadline']=datetime.now(timezone.utc)>deadline
    receipt.write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('report','evidence','image-id','out-dir'):parser.add_argument('--'+flag,required=True)
    args=parser.parse_args(argv)
    try:
        record=fetch_candidate(read_report(args.report),read_json(args.evidence,MAX_PACKET_BYTES),args.image_id,args.out_dir)
        print(json.dumps(record,ensure_ascii=True,indent=2))
        return 0 if record['status']=='fetched' and not record['after_agent_deadline'] else 1
    except (OSError,ValueError,KeyError) as exc:parser.error(str(exc))


if __name__=='__main__':raise SystemExit(main())
