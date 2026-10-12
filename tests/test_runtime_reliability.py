"""Regression tests for cancellation, deadline enforcement and malformed input."""
import json,os,signal,socket,struct,subprocess,sys,threading,time
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import pytest
ROOT=Path(__file__).resolve().parents[1]
for rel in ('common','skills/audit-orchestrator/scripts','skills/crawl-render-audit/scripts'):
    sys.path.insert(0,str(ROOT/rel))
import subprocess_isolation as isolation
from constants import Limits
from transport import Transport
from instrumentation import Instrumentation
from html_features import Document
from models import make_deadline
import url_safety


def _partial_writer(target,args,kwargs,pipe):
    os.write(pipe.fileno(),struct.pack('!i',1024))
    time.sleep(20)


def test_partial_pipe_frame_cannot_defeat_timeout(monkeypatch):
    monkeypatch.setattr(isolation,'_child_entry',_partial_writer)
    start=time.monotonic()
    result=isolation.run_isolated(isolation._double,args=(2,),timeout_s=.5)
    assert result.timed_out and time.monotonic()-start<3


def test_spawn_is_used_and_large_result_is_preserved():
    assert isolation._get_context().get_start_method()=='spawn'
    from test_v6_regressions import _large_result
    result=isolation.run_isolated(_large_result,timeout_s=5)
    assert result.ok and len(result.value)==2000000


def test_stalled_dns_is_bounded(monkeypatch):
    release=threading.Event()
    def stalled(*args):release.wait(5);return []
    monkeypatch.setattr(url_safety,'DNS_LOOKUP_TIMEOUT_S',.05)
    start=time.monotonic()
    try:
        with patch.object(socket,'getaddrinfo',side_effect=stalled):
            result=url_safety.classify_url('https://dns-fixture.invalid')
        assert not result.safe and result.reason=='dns_resolution_failed'
        assert time.monotonic()-start<.5
    finally:release.set()


def test_slow_drip_headers_hit_absolute_fetch_deadline():
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen()
    stop=threading.Event()
    def serve():
        conn,_=listener.accept()
        try:
            conn.recv(4096)
            for byte in b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n':
                if stop.wait(.03):break
                conn.send(bytes([byte]))
        except OSError:pass
        finally:conn.close()
    worker=threading.Thread(target=serve,daemon=True);worker.start()
    url=f'http://127.0.0.1:{listener.getsockname()[1]}'
    limits=replace(Limits(),PER_FETCH_TIMEOUT_MS=150)
    tr=Transport(url,time.monotonic()+3,limits,Instrumentation(),True)
    start=time.monotonic()
    try:
        response,outcome=tr.get(url+'/')
        assert response is None and outcome=='timeout'
        assert time.monotonic()-start<1
    finally:stop.set();listener.close();worker.join(1)


def test_pathological_html_is_bounded():
    doc=Document()
    with pytest.raises(ValueError,match='budget'):
        doc.feed('<div>'*10000)
    assert len(doc.stack)<=256


def test_short_audit_reserves_time_for_analysis():
    limits=replace(Limits(),TOTAL_AUDIT_TIMEOUT_S=10)
    deadline=make_deadline(limits)
    assert deadline.stage_deadlines['acquisition']-deadline.started_monotonic==6

@pytest.mark.parametrize('value',['nan','inf','0','-1'])
def test_invalid_cli_timeouts_are_clean_errors(value):
    run=subprocess.run([sys.executable,str(ROOT/'skills/audit-orchestrator/scripts/run_audit.py'),'https://example.com','--timeout',value],capture_output=True,text=True,timeout=5)
    assert run.returncode==2 and 'positive finite' in run.stderr and 'Traceback' not in run.stderr

@pytest.mark.skipif(os.name!='posix',reason='POSIX terminal signal regression')
def test_real_cli_interrupt_returns_json_and_130(tmp_path):
    script=tmp_path/'cancel_fixture.py'
    script.write_text('''import sys,time,threading,os,signal
sys.path.insert(0, %r)
import run_audit

def slow(site,limits,allow_private):
    while True:time.sleep(1)

if __name__=='__main__':
    run_audit._run_audit_impl=slow
    threading.Timer(.8,lambda:os.kill(os.getpid(),signal.SIGINT)).start()
    run_audit.main(['https://example.com'])
''' % str(ROOT/'skills/audit-orchestrator/scripts'))
    result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=5)
    assert result.returncode==130,result.stderr
    assert 'Traceback' not in result.stderr
    assert '[audit] started' in result.stderr
    assert json.loads(result.stdout)['coverage']['cancelled'] is True


def test_quiet_cli_keeps_stdout_json():
    result=subprocess.run([sys.executable,str(ROOT/'skills/audit-orchestrator/scripts/run_audit.py'),'https://127.0.0.1','--quiet'],capture_output=True,text=True,timeout=5)
    assert result.returncode==0 and not result.stderr
    assert 'execution_status' in json.loads(result.stdout)
