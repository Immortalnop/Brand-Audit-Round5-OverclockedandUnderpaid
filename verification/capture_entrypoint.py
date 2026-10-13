"""Verification instrumentation around the existing entrypoint; no extra crawl.

Records actual HTTPConnection.request calls and the acquired observations in
spawned workers. Request headers/cookies/provider credentials are not logged.
Product code, safety gates, deadlines and the immutable artifacts are untouched.
"""
import http.client
import json
import os
import sys
import time
from pathlib import Path

CANDIDATE = Path(os.environ['BRAND_CANDIDATE_ROOT']).resolve()
RUN = Path(os.environ['BRAND_RUN_DIR']).resolve()
RUN.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CANDIDATE/'common'))
sys.path.insert(0, str(CANDIDATE/'skills/audit-orchestrator/scripts'))
import run_audit
from models import _jsonable
from json_boundary import atomic_write_text

_original_request = http.client.HTTPConnection.request

def _record_request(self, method, url, *args, **kwargs):
    result = _original_request(self, method, url, *args, **kwargs)
    record = {'method':method, 'host':self.host, 'port':self.port, 'path':url,
              'at_unix':time.time(), 'pid':os.getpid()}
    with open(RUN/'requests.jsonl', 'a', encoding='utf-8') as handle:
        handle.write(json.dumps(record,ensure_ascii=False)+'\n')
    return result

http.client.HTTPConnection.request = _record_request
_original_acquire = run_audit.acquire_site

def _record_acquire(*args, **kwargs):
    artifacts = _original_acquire(*args, **kwargs)
    data = _jsonable(artifacts)
    for page in data.get('pages', []):
        page['response_headers'] = {k:v for k,v in (page.get('response_headers') or {}).items()
                                    if k.lower() not in ('set-cookie','cookie','authorization','proxy-authorization')}
    atomic_write_text(RUN/'acquisition.json',json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    with open(RUN/'acquisition-calls.jsonl','a',encoding='utf-8') as handle:
        handle.write(json.dumps({'at_unix':time.time(),'pid':os.getpid(),'pages':len(data.get('pages',[]))})+'\n')
    return artifacts

run_audit.acquire_site = _record_acquire
if __name__ == '__main__':
    started = time.monotonic()
    result = run_audit.main(sys.argv[1:])
    atomic_write_text(RUN/'entrypoint.json',json.dumps({'exit_code':result,'entrypoint_elapsed_s':time.monotonic()-started,
                      'command_arguments':sys.argv[1:],'instrumentation':'client requests after send; observation snapshot excludes cookies/auth headers'})+'\n')
    sys.exit(result)
