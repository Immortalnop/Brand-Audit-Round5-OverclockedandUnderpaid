"""Collect a labelled-later review set from one frozen candidate, read-only.

No scoring, tuning or fabricated host outcomes. Failed/blocked runs stay in the
manifest and denominator. Native/static capabilities are declared explicitly.
"""
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE=Path(os.environ.get('BRAND_CANDIDATE_ROOT','/tmp/brand-frozen-final')).resolve()
OUT=Path(os.environ.get('BRAND_REVIEW_OUT_DIR',str(ROOT/'verification/review-set'))).resolve()
SITES=[('commerce','https://www.adafruit.com/'),('publishing','https://www.npr.org/'),
       ('local_business','https://www.tatteredcover.com/'),('documentation','https://developer.mozilla.org/en-US/docs/Web'),
       ('education','https://www.mit.edu/'),('nonprofit','https://www.donorschoose.org/')]
def main():
 if OUT.exists() and any(OUT.iterdir()):
  raise SystemExit('refusing to overwrite a saved review batch; choose a new BRAND_REVIEW_OUT_DIR')
 OUT.mkdir(parents=True,exist_ok=True)
 release=json.loads((CANDIDATE/'RELEASE.json').read_text())
 manifest={'candidate_commit':release['commit'],'version':release['version'],
  'frozen_at':datetime.now(timezone.utc).isoformat(), 'sites':[{'category':c,'url':u} for c,u in SITES],
  'capabilities':{'native_static':True,'host_search':False,'host_vision':False,'rendering':False},
  'page_cap':6,'core_limit_s':200,'scorer_sha256':hashlib.sha256((CANDIDATE/'tests/score_benchmark.py').read_bytes()).hexdigest(),
  'scope':'Fresh review batch for this implementation, without tuning. Prior remote evaluation history is not available; independently untouched holdout status is unverified. Human labels pending.'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 runs=[];rows=[]
 for category,url in SITES:
  folder=OUT/category;folder.mkdir(exist_ok=True)
  env=os.environ.copy();env.update(BRAND_CANDIDATE_ROOT=str(CANDIDATE),BRAND_RUN_DIR=str(folder),
  OFF_SITE_LOOKUP='0',KNOWLEDGE_GRAPH_LOOKUP='0',FIELD_VITALS_LOOKUP='0',SEARCH_API_URL='',SEARCH_API_KEY='',ENABLE_RENDERING='0')
  cmd=[sys.executable,str(Path(__file__).with_name('capture_entrypoint.py')),url,'--max-pages','6','--timeout','200',
       '--out',str(folder/'base-report.json'),'--evidence-out',str(folder/'evidence.json')]
  started=datetime.now(timezone.utc).isoformat()
  print('[review set] '+category+' '+url,flush=True)
  with open(folder/'command-transcript.txt','w') as log:
   try:result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=230)
   except subprocess.TimeoutExpired:result=None
  record={'category':category,'url':url,'started_at':started,'exit_code':result.returncode if result else None}
  if (folder/'base-report.json').exists():
   report=json.loads((folder/'base-report.json').read_text());coverage=report.get('coverage') or {}
   record.update(execution_status=report['execution_status'],pages_analyzed=coverage.get('pages_analyzed',0),
     code_version=report['code_version'],audit_id=report['audit_id'],snapshot_sha256=report.get('snapshot_sha256'),
     findings=len(report['findings']),network_budget=coverage.get('network_budget'))
   for finding in report['findings']:
    rows.append({'category':category,'split':'review_pending','site':url,'finding_id':finding['id'],
     'check_ids':' '.join(finding.get('check_ids') or [finding['check_id']]),'severity':finding['severity'],
     'status':finding['status'],'confidence':finding['confidence'],'finding_type':finding['finding_type'],
     'pages':len(finding['affected_pages']),'title':finding['title'],'evidence':finding['evidence_text'][:1000],
     'label':'','note':'','support_correct':'','scope_correct':'','status_correct':'','severity_correct':'',
     'action_applicable':'','reviewer':'','human_reviewed':'','report':str((folder/'base-report.json').relative_to(ROOT))})
   subprocess.run([sys.executable,str(CANDIDATE/'common/report_markdown.py'),str(folder/'base-report.json'),str(folder/'report.md')],stdout=subprocess.DEVNULL,check=True)
  else:record['execution_status']='runner_error'
  record['hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
  runs.append(record);(OUT/'runs.json').write_text(json.dumps(runs,indent=2)+'\n')
  print('[review set] '+category+' '+record['execution_status'],flush=True)
 fields=['category','split','site','finding_id','check_ids','severity','status','confidence','finding_type','pages','title','evidence','label','note','support_correct','scope_correct','status_correct','severity_correct','action_applicable','reviewer','human_reviewed','report']
 with open(OUT/'findings-review.csv','w',newline='',encoding='utf-8') as handle:
  writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
 print(str(len(rows))+' findings ready for human review; no independent accuracy score assigned.',flush=True)


if __name__=='__main__':
 main()
