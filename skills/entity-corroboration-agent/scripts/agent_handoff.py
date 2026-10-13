"""Local handoff preparation and bounded summaries; never acquires a website.

Keep the large native report out of the host's time-limited research context.
The immutable report/packet still cross the ordinary envelope validation boundary.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
for rel in ('common','skills/audit-orchestrator/scripts'):
    sys.path.insert(0,str(ROOT/rel))

from agent_evidence import MAX_PACKET_BYTES
from json_boundary import read_json
from packet_contract import emitted_json
from report_markdown import read_report
from ingest_agent_findings import validate_envelope


def pending_envelope(report,packet,search=False):
    envelope={'schema_version':'1.1',**{k:packet.get(k) for k in ('audit_id','snapshot_sha256','packet_sha256')},
              'capabilities':{'local_reading':True,'search':search,'vision':False},
              'checks':[{'check':f'AG-{i:02d}','outcome':'not_assessed',
                         'reason':'Not yet assessed in this host stage.'} for i in range(1,7)]}
    validate_envelope(envelope,report,packet)
    return envelope


def compact_summary(report):
    coverage=report.get('coverage') or {}
    summary={k:report.get(k) for k in ('site','audit_id','code_version','execution_status','summary','timing')}
    summary['coverage']={k:coverage.get(k) for k in ('pages_analyzed','pages_discovered','pages_challenged',
                                                   'pages_out_of_scope','sections_analyzed','sections_discovered',
                                                   'agent_stage','agent_corroboration','capabilities')}
    summary['confidence']=report.get('confidence')
    summary['whats_working']=(report.get('whats_working') or [])[:5]
    for key in ('start_here','top_actions','quick_wins'):
        value=report.get(key)
        summary[key]=value[:3] if isinstance(value,list) else value
    summary['limitations']=[str(v)[:500] for v in (report.get('limitations') or [])[:8]]
    summary['warnings']=[str(v)[:500] for v in (report.get('warnings') or [])[:5]]
    summary['findings']=[{k:f.get(k) for k in ('id','check_id','title','finding_type','severity','status',
                                             'affected_pages','root_cause','suggested_action')}
                         | {'evidence':(f.get('evidence') or [])[:2]} for f in (report.get('findings') or [])[:2]]
    return summary


def prepare(report_path,packet_path,out,search=False):
    # Exclusive create prevents stale or concurrent writers from replacing an
    # existing handoff. No change to either input or to native report ordering.
    report=read_report(report_path)
    packet=read_json(packet_path,MAX_PACKET_BYTES)
    envelope=pending_envelope(report,packet,search)
    with open(out,'x',encoding='utf-8',newline='\n') as handle:
        handle.write(emitted_json(envelope))
    return compact_summary(report)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    init=sub.add_parser('prepare')
    init.add_argument('--report',required=True);init.add_argument('--evidence',required=True)
    init.add_argument('--out',required=True);init.add_argument('--search',action='store_true')
    summary=sub.add_parser('summary');summary.add_argument('--report',required=True)
    args=parser.parse_args(argv)
    try:
        value=prepare(args.report,args.evidence,args.out,args.search) if args.mode=='prepare' else compact_summary(read_report(args.report))
        print(json.dumps(value,ensure_ascii=True,allow_nan=False,indent=2))
    except (OSError,ValueError) as exc:parser.error(str(exc))


if __name__=='__main__':main()
