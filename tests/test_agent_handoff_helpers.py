"""Compact host setup does not bypass the regular evidence boundary."""
import copy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/entity-corroboration-agent/scripts'))
from agent_handoff import prepare,pending_envelope,compact_summary
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
