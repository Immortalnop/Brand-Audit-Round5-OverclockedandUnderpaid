"""Actual host rehearsal over a controlled public-page fixture.

Uses the existing test-only allow_private_targets API for loopback; production
CLI safety remains unchanged. The server records actual requests independently.
"""
import functools
import json
import os
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=Path(os.environ.get('BRAND_CANDIDATE_ROOT',str(ROOT))).resolve()
RUN=Path(os.environ.get('BRAND_RUN_DIR',str(ROOT/'verification/rehearsals/failed-about'))).resolve()
os.environ.update(BRAND_CANDIDATE_ROOT=str(CANDIDATE),BRAND_RUN_DIR=str(RUN),OFF_SITE_LOOKUP='0',KNOWLEDGE_GRAPH_LOOKUP='0',FIELD_VITALS_LOOKUP='0',ENABLE_RENDERING='0',SEARCH_API_URL='',SEARCH_API_KEY='')
sys.path.insert(0,str(ROOT/'verification'))
from capture_entrypoint import run_audit
sys.path.insert(0,str(CANDIDATE/'tests'))
from archetype_sites import serve,ALLOW_ALL
from models import _jsonable

if __name__=='__main__':
 RUN.mkdir(parents=True,exist_ok=True)
 page='<html lang="en"><head><title>Acme</title></head><body><a href="/about">About us</a><main><h1>Acme</h1><p>Acme makes payroll software for small businesses.</p><p>'+('Plain useful source content. '*30)+'</p></main></body></html>'
 base,stop,seen=serve({'robots':ALLOW_ALL,'pages':{'/':page},'responses':{'/about':(503,'Service unavailable','text/html',())}})
 original=run_audit.run_audit_with_evidence
 run_audit.run_audit_with_evidence=functools.partial(original,allow_private_targets=True)
 started=time.time()
 arguments=[base+'/','--timeout','60','--max-pages','3','--out',str(RUN/'base-report.json'),'--evidence-out',str(RUN/'evidence.json')]
 try:
  result=run_audit.main(arguments)
  (RUN/'server-requests.json').write_text(json.dumps(seen,indent=2)+'\n')
  (RUN/'entrypoint-core.json').write_text(json.dumps({'exit_code':result,'started_at_unix':started,'finished_at_unix':time.time(),'command_arguments':arguments,'test_only_allow_private_targets':True},indent=2)+'\n')
 finally:stop()
 sys.exit(result)
