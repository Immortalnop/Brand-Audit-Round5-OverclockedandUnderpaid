"""Local handoff preparation and bounded summaries; never acquires a website.

Keep the large native report out of the host's time-limited research context.
The immutable report/packet still cross the ordinary envelope validation boundary.
"""
import argparse
import json
import re
from datetime import datetime, timezone
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

PENDING_REASON = 'Not yet assessed in this host stage.'


def pending_envelope(report,packet,search=False):
    envelope={'schema_version':'1.1',**{k:packet.get(k) for k in ('audit_id','snapshot_sha256','packet_sha256')},
              'capabilities':{'local_reading':True,'search':search,'vision':False},
              'checks':[{'check':f'AG-{i:02d}','outcome':'not_assessed',
                         'reason':PENDING_REASON} for i in range(1,7)]}
    validate_envelope(envelope,report,packet)
    return envelope


def compact_summary(report):
    coverage=report.get('coverage') or {}
    summary={k:report.get(k) for k in ('site','audit_id','code_version','execution_status','summary','timing')}
    summary['coverage']={k:coverage.get(k) for k in ('pages_analyzed','pages_discovered','pages_challenged',
                                                   'pages_out_of_scope','sections_analyzed','sections_discovered',
                                                   'agent_stage','agent_corroboration','agent_corroboration_stage','capabilities')}
    summary['confidence']=report.get('confidence')
    summary['whats_working']=(report.get('whats_working') or [])[:5]
    for key in ('start_here','top_actions','quick_wins'):
        value=report.get(key)
        summary[key]=value[:3] if isinstance(value,list) else value
    # The report marks the starting defect on a top_actions row; it does not
    # normally have a top-level start_here field. Do not invent a starting item.
    summary['start_here']=next((row for row in coverage_rows(report,'top_actions')
                                if row.get('start_here')),None)
    summary['limitations']=[str(v)[:500] for v in (report.get('limitations') or [])[:8]]
    summary['warnings']=[str(v)[:500] for v in (report.get('warnings') or [])[:5]]
    summary['findings']=[{k:f.get(k) for k in ('id','check_id','title','finding_type','severity','status',
                                             'affected_pages','root_cause','suggested_action')}
                         | {'evidence':(f.get('evidence') or [])[:2]} for f in (report.get('findings') or [])[:2]]
    return summary


def coverage_rows(report,key):
    return [row for row in report.get(key) or [] if isinstance(row,dict)]


def work_plan(packet):
    """Expose exact packet fields, never classify or answer an AG check."""
    pages={p['evidence_id']:p for p in packet.get('pages') or []}
    images=[]
    for image in packet.get('image_candidates') or []:
        parents=[ref for ref in image.get('page_evidence_ids') or [] if ref in pages]
        if parents:
            images.append({'image_id':image['image_id'],'url':image['url'],
                           'page_evidence_ids':parents,
                           'compared_text_complete':all(pages[ref].get('observation_status')=='complete'
                                                       and not pages[ref].get('text_truncated') for ref in parents)})
    return {'ag01':(packet.get('focus') or {}).get('ag01'),
            'ag03_quote_options':{'page_refs':list(pages),
                                 'claim_refs':[c['claim_id'] for c in packet.get('claims') or []],
                                 'rule':'Use an exact substantive E passage or C value. C claims are optional; do not assess a contact/date merely to fill a slot.'},
            'ag04_eligible_images':images,
            'field_layout':'queries, sources and source_refs are siblings of observation inside each check, never nested in observation.',
            'remaining_checks':'Attempt every eligible check, sharing actual inspected sources where each contract is satisfied; one failed source does not end other checks.'}


def checkpoint(report,packet,envelope,now=None):
    """Read-only clock and evidence checks before research or final merge.

    It cannot prove host tool use or enforce a Claude tool timeout. It does
    catch initialized placeholders and deadline/parent claims contradicted by
    the bound packet and current clock, without changing evidence or outcomes.
    """
    validated=validate_envelope(envelope,report,packet)
    now=now or datetime.now(timezone.utc)
    raw_deadline=(packet.get('timing') or {}).get('agent_deadline_at')
    try:
        deadline=datetime.fromisoformat(raw_deadline.replace('Z','+00:00'))
        if deadline.tzinfo is None:raise ValueError()
    except (AttributeError,TypeError,ValueError) as exc:
        raise ValueError('A checkpoint needs the bound UTC agent deadline') from exc
    left=max(0.,(deadline-now).total_seconds())
    checks=validated['checks']
    incomplete=[key for key,row in checks.items() if row['outcome'] in ('not_assessed','error')]
    blockers=[]
    provided={str(row.get('check','')).strip().upper() for row in envelope.get('checks') or []}
    if provided!={f'AG-{i:02d}' for i in range(1,7)}:
        blockers.append('Retain exactly one explicit outcome for all six checks; do not lose entries while editing the envelope.')
    for key,row in checks.items():
        if row['reason']==PENDING_REASON:
            blockers.append(key+': replace the pending reason after an actual attempt or supported limitation.')
        elif row['outcome']=='not_assessed' and left>0 and (
                re.search(r'\bdeadline\b.{0,30}\b(?:reached|passed|expired)\b|\btime (?:ran|run) out\b',row['reason'],re.I)
                or left>=30 and re.search(r'\bdeadline\b',row['reason'],re.I)):
            blockers.append(key+': deadline has not expired; '+str(round(left,1))+' seconds remain. Continue eligible work or give the actual non-time limitation.')
    images=work_plan(packet)['ag04_eligible_images']
    image_reason=checks['AG-04']['reason']
    if checks['AG-04']['outcome']=='not_assessed' and images and re.search(
            r'(?:no|none|without).{0,100}(?:exported.{0,20}(?:parent|page)|parent.{0,20}(?:page|association))',image_reason,re.I):
        blockers.append('AG-04: packet image_candidates do have exported page_evidence_ids; use the actual image/viewing/text limit.')
    return {'checked_at':now.isoformat(),'agent_deadline_at':raw_deadline,
            'remaining_agent_s':round(left,3),'deadline_expired':now>=deadline,
            'may_start_research_batch':left>=30,'may_start_source_inspection':left>=15,
            'may_start_image_fetch':left>=25 and bool(images),
            'checks_assessed':[key for key,row in checks.items() if row['outcome'] in ('pass','finding')],
            'checks_unassessed':incomplete,'ag04_eligible_images':images,
            'preflight_issues':blockers,'ready_to_merge':not blockers}


def _line(value,limit=300):
    return ' '.join(str(value or '').split())[:limit]


def terminal_summary(report):
    """A fixed, evidence-based reply scaffold; no new ranking or assessment."""
    c=report.get('coverage') or {}; counts=report.get('summary') or {}
    stage=c.get('agent_stage') or {}; checks=stage.get('checks') or {}
    lines=[f"Audit of {_line(report.get('site'))}: {_line(report.get('execution_status'))}.",
           'Findings: '+', '.join(f'{counts.get(k,0)} {k}' for k in ('critical','high','medium','low'))+
           f"; {counts.get('total_findings',0)} total, {counts.get('total_recommendations',0)} recommendations.",
           f"Coverage: {c.get('pages_analyzed','unknown')}/{c.get('pages_discovered','unknown')} pages; "
           f"{c.get('pages_challenged',0)} challenged, {c.get('pages_out_of_scope',0)} out of scope.",
           f"Version: {_line(report.get('code_version'))}; audit ID: {_line(report.get('audit_id'))}.",
           '', 'Agent checks (unassessed checks are audit limits, not website defects):']
    for i in range(1,7):
        key=f'AG-{i:02d}';row=checks.get(key) or {}
        linked=[f for f in report.get('findings') or [] if f.get('check_id')==key
                or key in (f.get('check_ids') or []) or (f.get('provenance') or {}).get('agent_check')==key
                or any(p.get('agent_check')==key for p in (f.get('provenance') or {}).get('contributing_skills') or [])]
        finding_info=' ('+', '.join(f"{f.get('id')}, {f.get('severity')}, {f.get('status')}" for f in linked)+')' if row.get('outcome')=='finding' and linked else ''
        if row.get('outcome')=='finding' and not linked:
            finding_info=' ('+str(row.get('severity','unknown severity'))+', '+str(row.get('status','unknown status'))+')'
        lines.append(f"- {key}: {row.get('outcome','not_assessed')}{finding_info}; {_line(row.get('reason') or 'No agent assessment was supplied.',240)}")
    lines+=['','First two findings, in the report\'s priority order:']
    for f in (report.get('findings') or [])[:2]:
        urls=f.get('affected_pages') or [];action=f.get('suggested_action') or {}
        lines.append(f"- {f.get('id')}: {_line(f.get('title'))} ({f.get('severity')}, {f.get('status')}, {f.get('finding_type')}; {len(urls)} affected pages).")
        evidence=next((e.get('description') for e in f.get('evidence') or [] if isinstance(e,dict) and e.get('description')),f.get('evidence_text'))
        lines.append('  Evidence: '+_line(evidence,450))
        if urls:lines.append('  Example page: '+_line(urls[0]))
        lines.append('  Fix: '+_line(action.get('summary')))
        for step in (action.get('steps') or [])[:2]:lines.append('  - '+_line(step,220))
        if action.get('owner_roles'):lines.append('  Suggested roles: '+', '.join(action['owner_roles']))
    if not report.get('findings'):lines.append('- No findings were reported.')
    start=next((r for r in coverage_rows(report,'top_actions') if r.get('start_here')),None)
    lines+=['','Starting action: '+(_line(start.get('finding_id'))+' '+_line(start.get('summary')) if start else 'No confirmed defect is marked start_here.')]
    for row in coverage_rows(report,'top_actions')[:2]:lines.append('Top defect action: '+_line(row.get('finding_id'))+' '+_line(row.get('summary')))
    for row in coverage_rows(report,'quick_wins')[:2]:lines.append('Quick win: '+_line(row.get('id'))+' '+_line(row.get('summary')))
    limits=report.get('limitations') or []
    if limits:lines+=['','Relevant limits:']+['- '+_line(v,240) for v in limits[:4]]
    measured=(c.get('agent_corroboration') or {}).get('workflow_timing') or {}
    if measured:lines.append(f"Measured through merge: {measured.get('workflow_elapsed_s')} s; rendering and the final reply are additional.")
    lines+=['','Files: final-report.json, final-report.md, base-report.json, evidence.json, agent-outcomes.json, agent-stage-notes.md.',
            'The complete report retains every finding and recommendation. This is a bounded sample; it does not predict rankings or business gains.']
    return '\n'.join(lines)


def prepare(report_path,packet_path,out,search=False):
    # Exclusive create prevents stale or concurrent writers from replacing an
    # existing handoff. No change to either input or to native report ordering.
    report=read_report(report_path)
    packet=read_json(packet_path,MAX_PACKET_BYTES)
    envelope=pending_envelope(report,packet,search)
    with open(out,'x',encoding='utf-8',newline='\n') as handle:
        handle.write(emitted_json(envelope))
    summary=compact_summary(report)
    summary['agent_work_plan']=work_plan(packet)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    init=sub.add_parser('prepare')
    init.add_argument('--report',required=True);init.add_argument('--evidence',required=True)
    init.add_argument('--out',required=True);init.add_argument('--search',action='store_true')
    summary=sub.add_parser('summary');summary.add_argument('--report',required=True)
    terminal=sub.add_parser('terminal');terminal.add_argument('--report',required=True)
    for mode in ('status','preflight'):
        command=sub.add_parser(mode)
        command.add_argument('--report',required=True);command.add_argument('--evidence',required=True)
        command.add_argument('--outcomes',required=True)
    args=parser.parse_args(argv)
    try:
        if args.mode=='terminal':
            print(terminal_summary(read_report(args.report)));return
        if args.mode in ('status','preflight'):
            value=checkpoint(read_report(args.report),read_json(args.evidence,MAX_PACKET_BYTES),read_json(args.outcomes,MAX_PACKET_BYTES))
            if args.mode=='preflight' and value['preflight_issues']:
                raise ValueError('; '.join(value['preflight_issues']))
        else:
            value=prepare(args.report,args.evidence,args.out,args.search) if args.mode=='prepare' else compact_summary(read_report(args.report))
        print(json.dumps(value,ensure_ascii=True,allow_nan=False,indent=2))
    except (OSError,ValueError) as exc:parser.error(str(exc))


if __name__=='__main__':main()
