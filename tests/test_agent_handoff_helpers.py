"""Compact host setup does not bypass the regular evidence boundary."""
import copy
from pathlib import Path
import sys
import pytest
import json
import subprocess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/entity-corroboration-agent/scripts'))
from agent_handoff import prepare,pending_envelope,compact_summary,work_plan,checkpoint,terminal_summary,PENDING_REASON
from test_final_packet_contract import packet_for,assess
from run_audit import write_report
from ingest_agent_findings import EnvelopeError,validate_envelope
from packet_contract import packet_digest
from datetime import datetime,timedelta,timezone
import fetch_agent_image
from transport import Response
from subprocess_isolation import IsolatedResult


def test_prepare_saves_all_six_outcomes_once_without_changing_inputs(tmp_path):
    packet=packet_for();report,_=assess(packet)
    report.update(execution_status='completed',findings=[],recommendations=[],summary={})
    base=tmp_path/'base.json';evidence=tmp_path/'evidence.json';out=tmp_path/'outcomes.json'
    write_report(report,base);write_report(packet,evidence)
    original=(base.read_bytes(),evidence.read_bytes())
    summary=prepare(base,evidence,out)
    import json
    saved=json.loads(out.read_text())
    assert len(saved['checks'])==6 and all(c['outcome']=='not_assessed' for c in saved['checks'])
    assert summary['audit_id']==packet['audit_id']
    assert (base.read_bytes(),evidence.read_bytes())==original
    with pytest.raises(FileExistsError):prepare(base,evidence,out)


def test_prepare_rejects_stale_packet_before_writing(tmp_path):
    packet=packet_for();report,_=assess(packet)
    report.update(execution_status='completed',findings=[],recommendations=[],summary={})
    base=tmp_path/'base.json';evidence=tmp_path/'evidence.json';out=tmp_path/'outcomes.json'
    write_report(report,base)
    packet['pages'][0]['text']='Changed source'
    write_report(packet,evidence)
    with pytest.raises(EnvelopeError):prepare(base,evidence,out)
    assert not out.exists()


def test_report_clock_cannot_be_reset_independently_of_bound_packet():
    packet=packet_for()
    packet['timing']={'agent_deadline_at':'2026-10-14T12:00:00+00:00'}
    packet['packet_sha256']=packet_digest(packet)
    report,envelope=assess(packet)
    report['timing']=copy.deepcopy(packet['timing'])
    validate_envelope(envelope,report,packet)
    report['timing']['agent_deadline_at']='2026-10-14T12:30:00+00:00'
    with pytest.raises(EnvelopeError,match='timing'):validate_envelope(envelope,report,packet)


def clock_binding():
    now=datetime(2026,10,14,12,tzinfo=timezone.utc)
    packet=packet_for(media={'images':[{'url':'https://fixture.example/specs.png',
                                     'same_origin':True,'pages':['https://fixture.example/']}]})
    packet['timing']={'agent_deadline_at':(now+timedelta(seconds=112)).isoformat()}
    packet['packet_sha256']=packet_digest(packet)
    report,_=assess(packet);report['timing']=copy.deepcopy(packet['timing'])
    return report,packet,pending_envelope(report,packet,search=True),now


def test_checkpoint_exposes_real_time_and_exported_image_parents_without_assessment():
    report,packet,envelope,now=clock_binding();original=copy.deepcopy((report,packet,envelope))
    result=checkpoint(report,packet,envelope,now)
    assert result['remaining_agent_s']==112 and result['may_start_research_batch']
    assert result['checks_assessed']==[] and len(result['checks_unassessed'])==6
    assert result['ag04_eligible_images'][0]['page_evidence_ids']
    assert len(result['preflight_issues'])==6 and not result['ready_to_merge']
    assert (report,packet,envelope)==original


def test_preflight_catches_premature_deadline_and_false_image_parent_reasons():
    report,packet,envelope,now=clock_binding()
    for check in envelope['checks']:check['reason']='Required source was inaccessible; no assessment supplied.'
    envelope['checks'][2]['reason']='The agent deadline was reached before this check could run.'
    envelope['checks'][3]['reason']='No image candidate has an exported parent page association.'
    result=checkpoint(report,packet,envelope,now)
    assert any('AG-03: deadline has not expired' in v for v in result['preflight_issues'])
    assert any('AG-04: packet image_candidates' in v for v in result['preflight_issues'])
    result=checkpoint(report,packet,envelope,now+timedelta(seconds=113))
    assert result['deadline_expired'] and not result['may_start_source_inspection']
    assert not any('AG-03:' in v for v in result['preflight_issues'])


def test_honest_blocked_or_partial_text_outcomes_are_not_forced_to_pass():
    report,packet,envelope,now=clock_binding()
    for check in envelope['checks']:check['reason']='Source blocked with HTTP 403; no passage inspected.'
    envelope['checks'][3]['reason']='Viewed image has no readable fact; compared text is incomplete.'
    result=checkpoint(report,packet,envelope,now)
    assert result['ready_to_merge'] and result['checks_assessed']==[]


def test_preflight_detects_an_envelope_writer_that_erased_check_entries():
    report,packet,envelope,now=clock_binding()
    envelope['checks']=[]
    result=checkpoint(report,packet,envelope,now)
    assert not result['ready_to_merge']
    assert any('all six checks' in reason for reason in result['preflight_issues'])


def test_preflight_cli_refuses_placeholders_and_never_changes_saved_inputs(tmp_path):
    report,packet,envelope,_=clock_binding()
    report.update(execution_status='completed',findings=[],recommendations=[],summary={})
    paths=[tmp_path/name for name in ('base.json','packet.json','outcomes.json')]
    for data,path in zip((report,packet,envelope),paths):write_report(data,path)
    before=[p.read_bytes() for p in paths]
    script=Path(__file__).resolve().parents[1]/'skills/entity-corroboration-agent/scripts/agent_handoff.py'
    command=[sys.executable,str(script),'preflight','--report',str(paths[0]),
             '--evidence',str(paths[1]),'--outcomes',str(paths[2])]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode!=0 and 'pending reason' in result.stderr
    assert [p.read_bytes() for p in paths]==before
    for check in envelope['checks']:check['reason']='Host search/vision unavailable; no assessment performed.'
    write_report(envelope,paths[2]);before=[p.read_bytes() for p in paths]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==0 and json.loads(result.stdout)['ready_to_merge']
    assert [p.read_bytes() for p in paths]==before


def test_one_inspected_agreement_can_support_ag02_and_e_only_ag03():
    packet=packet_for(identity={'data':{'canonical_name':'Acme'}})
    report,_=assess(packet);envelope=pending_envelope(report,packet,search=True)
    query={'query':'Acme payroll software for small teams','executed_at':'2026-10-14T12:00:00Z',
           'result_count':1,'matching_result_count':1,'independent_result_count':1}
    source={'url':'https://independent.example/review','kind':'inspected_page',
            'quote':'Acme makes payroll software for small teams.',
            'authorship':'Independent Reviewer','accessed_at':'2026-10-14T12:00:05Z'}
    observation={'identity':'Acme','context':'Synthetic fixture: payroll service identity and current offering.'}
    for key in ('AG-02','AG-03'):
        record={'check':key,'outcome':'pass','reason':'One inspected independent agreement; scoped to this fixture claim.',
                'source_refs':['E001'],'queries':[query],'sources':[source],
                'observation':dict(observation)}
        if key=='AG-03':record['observation'].update(site_quote=source['quote'],
            site_claim='Acme offers payroll software for small teams.',same_entity='Same Acme payroll service.',
            independence='Independent reviewer, not an owned alias or syndicated source.')
        envelope['checks'][int(key[-2:])-1]=record
    validated=validate_envelope(envelope,report,packet)
    assert validated['checks']['AG-02']['outcome']=='pass'
    assert validated['checks']['AG-03']['outcome']=='pass'


def test_terminal_summary_shows_two_findings_and_every_agent_outcome_without_reordering():
    report={'site':'https://fixture.example/','execution_status':'completed',
            'findings':[{'id':'F-001','title':'First','severity':'medium','status':'confirmed',
                         'finding_type':'defect','affected_pages':['https://fixture.example/'],
                         'provenance':{'agent_check':'AG-01'},
                         'evidence':[{'description':'Observed first evidence'}],
                         'suggested_action':{'summary':'Fix first','steps':['Name the button'],'owner_roles':['developer']}},
                        {'id':'F-002','title':'Second','severity':'low','status':'suspected',
                         'finding_type':'proactive_improvement','affected_pages':[],
                         'evidence':[{'description':'Observed second evidence'}],'suggested_action':{'summary':'Fix second'}}],
            'coverage':{'agent_stage':{'checks':{'AG-01':{'outcome':'finding','reason':'Synthetic AG finding.'},
                                               'AG-02':{'outcome':'pass','reason':'Inspected independent source.'}}}},
            'top_actions':[{'finding_id':'F-001','start_here':True,'summary':'Fix first'}]}
    original=copy.deepcopy(report);text=terminal_summary(report)
    assert all(f'AG-{i:02d}:' in text for i in range(1,7))
    assert 'AG-02: pass' in text and 'AG-04: not_assessed' in text
    assert 'AG-01: finding (F-001, medium, confirmed)' in text
    assert text.index('F-001: First')<text.index('F-002: Second')
    assert 'Observed first evidence' in text and 'Observed second evidence' in text
    assert 'Name the button' in text and 'Fix second' in text
    assert 'Starting action: F-001 Fix first' in text
    assert compact_summary(report)['start_here']['finding_id']=='F-001'
    assert report==original


def image_binding(seconds=90,url='https://fixture.example/specs.png'):
    packet=packet_for(media={'images':[{'url':url,'same_origin':True,'pages':['https://fixture.example/']}]})
    packet['timing']={'agent_deadline_at':(datetime.now(timezone.utc)+timedelta(seconds=seconds)).isoformat()}
    packet['packet_sha256']=packet_digest(packet)
    report,_=assess(packet);report['timing']=copy.deepcopy(packet['timing'])
    return report,packet


@pytest.mark.parametrize('seconds',[-10,10])
def test_image_fetch_does_not_start_without_time(monkeypatch,tmp_path,seconds):
    def refuse(*a,**k):raise AssertionError('No worker allowed')
    monkeypatch.setattr(fetch_agent_image,'run_isolated',refuse)
    report,packet=image_binding(seconds)
    with pytest.raises(ValueError,match='seconds remain'):
        fetch_agent_image.fetch_candidate(report,packet,'I001',tmp_path)
    assert not list(tmp_path.iterdir())


def test_image_fetch_rejects_cross_origin_even_with_a_bound_candidate(monkeypatch,tmp_path):
    report,packet=image_binding(url='https://elsewhere.example/specs.png')
    with pytest.raises(ValueError,match='audited origin'):
        fetch_agent_image.fetch_candidate(report,packet,'I001',tmp_path)
    assert not list(tmp_path.iterdir())


def test_image_receipt_is_one_fetch_and_never_claims_viewing(monkeypatch,tmp_path):
    report,packet=image_binding()
    data=b'a complete response supplied by the fake transport'
    calls=[]
    def fetch(*args,**kwargs):
        calls.append(kwargs)
        return IsolatedResult(True,{'status':'fetched','content':data,'format':'png','requests':2,'bytes':len(data)},False,None)
    monkeypatch.setattr(fetch_agent_image,'run_isolated',fetch)
    receipt=fetch_agent_image.fetch_candidate(report,packet,'I001',tmp_path)
    assert receipt['image_viewed'] is False and not receipt['after_agent_deadline']
    assert Path(receipt['path']).read_bytes()==data
    assert calls[0]['timeout_s']<=20
    with pytest.raises(FileExistsError):fetch_agent_image.fetch_candidate(report,packet,'I001',tmp_path)
    assert len(calls)==1


@pytest.mark.parametrize('robots,status,truncated',[
    (b'<html><title>Client Challenge</title></html>',200,False),
    (b'User-agent: *\nAllow: /',200,True),(b'Blocked',403,False),
    (b'User-agent: *\nDisallow: /',200,False)])
def test_image_transport_is_fail_closed_on_robots(monkeypatch,robots,status,truncated):
    calls=[]
    class FakeTransport:
        def __init__(self,*a,**k):self.requests=0;self.bytes=0;self.delay=0;self.robots=None
        def get(self,url,**kwargs):
            if self.robots and not self.robots.can_fetch('BrandAIReadinessAuditBot',url):return None,'robots_disallowed'
            calls.append(url);self.requests+=1
            return Response(status,{'Content-Type':'text/plain'},robots,url,truncated=truncated),'ok'
    monkeypatch.setattr(fetch_agent_image,'Transport',FakeTransport)
    receipt=fetch_agent_image._fetch('https://fixture.example','https://fixture.example/specs.png',20)
    assert receipt['status'] in ('robots_unavailable','robots_disallowed')
    assert calls==['https://fixture.example/robots.txt']
