"""Local verified-TLS regression tests. Fixture keys are public test data only."""
import json,socket,ssl,sys,threading,time
from dataclasses import replace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
ROOT=Path(__file__).resolve().parents[1]
for rel in ('common','skills/audit-orchestrator/scripts','skills/crawl-render-audit/scripts'):
    sys.path.insert(0,str(ROOT/rel))
from transport import Transport
from tls_context import create_context,environment_summary
from constants import Limits
from instrumentation import Instrumentation
from acquire_site import acquire_site
from models import make_deadline
from analyze_directives import analyze_directives
from check_ai_crawler_access import check_ai_crawler_access
from run_audit import run_audit

@pytest.fixture
def server(monkeypatch):
    # Fixture binds IPv4 only; constrain its DNS result rather than depending on host IPv6 setup.
    import ipaddress,url_safety
    original=url_safety._resolve
    monkeypatch.setattr(url_safety,'_resolve',lambda host:[ipaddress.ip_address('127.0.0.1')] if host=='localhost' else original(host))
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            seen.append(self.path)
            body=b'User-agent: *\nAllow: /\nUser-agent: OAI-SearchBot\nDisallow: /\n' if self.path=='/robots.txt' else b'<html lang="en"><title>Fixture</title><h1>Fixture</h1></html>'
            self.send_response(503 if self.path=='/http-error' else 200);self.send_header('Content-Type','text/plain' if self.path=='/robots.txt' else 'text/html')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(ROOT/'tests/tls-fixtures/server.pem'),str(ROOT/'tests/tls-fixtures/server-key.pem'))
    srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
    thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
    yield f'https://localhost:{srv.server_port}',seen
    srv.shutdown();srv.server_close();thread.join()

def transport(url):return Transport(url,time.monotonic()+8,Limits(),Instrumentation(),True)
def trust(monkeypatch):monkeypatch.setenv('AUDIT_CA_BUNDLE',str(ROOT/'tests/tls-fixtures/ca.pem'))

def test_exact_certificate_error(server,monkeypatch):
    monkeypatch.delenv('AUDIT_CA_BUNDLE',raising=False)
    url,seen=server;tr=transport(url)
    assert tr.get(url+'/robots.txt',robots_exempt=True)[1]=='tls_certificate_error'
    d=tr.diagnostics[-1]
    assert not seen and d['verify_code'] and d['verify_message'] and d['phase']=='tls_handshake'

def test_approved_ca_recovers_crawler_rule(server,monkeypatch):
    trust(monkeypatch);url,seen=server;ctx=create_context()
    assert ctx.check_hostname and ctx.verify_mode==ssl.CERT_REQUIRED
    a=acquire_site(url+'/',make_deadline(Limits()),Limits(),allow_private_targets=True)
    assert a.robots_data['status']=='ok' and seen[0]=='/robots.txt'
    assert any(f['check_id']=='ai-crawler-blocked' for f in check_ai_crawler_access(a,make_deadline(Limits()))['findings'])
    assert not any(f['check_id']=='tls-health' for f in analyze_directives(a,make_deadline(Limits()))['findings'])

def test_wrong_hostname_still_fails(server,monkeypatch):
    trust(monkeypatch);url,_=server;url=url.replace('localhost','127.0.0.1');tr=transport(url)
    assert tr.get(url+'/robots.txt',robots_exempt=True)[1]=='tls_certificate_error'
    assert 'mismatch' in tr.diagnostics[-1]['verify_message'].lower()

def test_verified_retry_recovers(server,monkeypatch):
    trust(monkeypatch);url,_=server;trusted=create_context();contexts=iter([ssl.create_default_context(),trusted])
    with patch('transport.create_context',side_effect=lambda:next(contexts,trusted)):
        a=acquire_site(url+'/',make_deadline(Limits()),Limits(),allow_private_targets=True)
    assert tuple(a.robots_data['attempt_outcomes'])==('tls_certificate_error','ok')
    assert not a.acquisition_metadata['probe_failures']
    assert a.acquisition_metadata['transport_diagnostics'][0]['verify_code']

def test_persistent_failure_is_not_site_defect_or_robot_block(server,monkeypatch):
    monkeypatch.delenv('AUDIT_CA_BUNDLE',raising=False);url,seen=server
    r=run_audit(url+'/',allow_private_targets=True)
    assert not seen and r['execution_status']=='degraded'
    assert r['coverage']['pages_blocked']==0 and r['coverage']['robots_permission']=='unknown'
    assert r['coverage']['skip_reason_counts']['robots_permission_unknown']==1
    tls=[f for f in r['findings'] if f['check_id']=='tls-health']
    assert tls and all(f['severity']=='low' and f['status']=='insufficient_evidence' and f['finding_type']=='proactive_improvement' for f in tls)
    assert r['coverage']['robots_attempt_outcomes'][0]=='tls_certificate_error'
    assert len(r['coverage']['robots_attempt_outcomes'])==2
    json.dumps(r,allow_nan=False)

@pytest.mark.parametrize('error,expected',[(ssl.SSLError(1,'WRONG_VERSION_NUMBER'),'tls_handshake_error'),(socket.timeout('slow'),'timeout')])
def test_failure_categories(error,expected):
    tr=transport('https://example.test')
    def fail(*a,**kw):raise error
    ctx=SimpleNamespace(wrap_socket=fail,check_hostname=True,verify_mode=ssl.CERT_REQUIRED,verify_flags=0,cert_store_stats=lambda:{'x509_ca':1});sock=SimpleNamespace(settimeout=lambda t:None,close=lambda:None)
    with patch('transport.classify_url',return_value=SimpleNamespace(safe=True,addresses=('93.184.216.34',))),patch('transport.create_context',return_value=ctx),patch('transport.socket.create_connection',return_value=sock):
        assert tr.get('https://example.test/')[1]==expected
    assert tr.diagnostics[-1]['category']==expected

def test_dns_is_not_safety_or_tls_failure():
    tr=transport('https://example.test')
    with patch('transport.classify_url',return_value=SimpleNamespace(safe=False,reason='dns_resolution_failed')):
        assert tr.get('https://example.test/')[1]=='dns_error'
    assert tr.diagnostics[-1]['category']=='dns_error'

def test_invalid_ca_configuration(monkeypatch):
    monkeypatch.setenv('AUDIT_CA_BUNDLE','/nonexistent/ca.pem');tr=transport('https://example.test')
    with patch('transport.classify_url',return_value=SimpleNamespace(safe=True,addresses=('93.184.216.34',))),patch('transport.socket.create_connection') as connect:
        assert tr.get('https://example.test/')[1]=='tls_configuration_error'
    connect.assert_not_called()

def test_retry_respects_request_budget(server,monkeypatch):
    monkeypatch.delenv('AUDIT_CA_BUNDLE',raising=False);url,seen=server;limits=replace(Limits(),MAX_TOTAL_HTTP_REQUESTS=1)
    a=acquire_site(url+'/',make_deadline(limits),limits,allow_private_targets=True)
    assert a.acquisition_metadata['total_requests']==1 and not seen and a.robots_data['conservative_fail_closed']

def test_proxy_context_does_not_leak_credentials(monkeypatch):
    monkeypatch.setenv('HTTPS_PROXY','http://secret:password@proxy.example:8080')
    data=environment_summary()
    assert data['proxy_environment_present'] and 'password' not in json.dumps(data)
    assert data['connection_route']=='direct_validated_ip'


def test_http_error_remains_a_response_not_tls_failure(server,monkeypatch):
    trust(monkeypatch);url,_=server;tr=transport(url)
    response,status=tr.get(url+'/http-error')
    assert status=='ok' and response.status_code==503
    assert tr.diagnostics[-1]['category']=='http_error' and tr.diagnostics[-1]['http_status']==503


def test_retry_rotates_only_validated_addresses():
    tr=transport('https://example.test');addresses=('93.184.216.34','93.184.216.35')
    with patch('transport.classify_url',return_value=SimpleNamespace(safe=True,addresses=addresses)),patch('transport.socket.create_connection',side_effect=ConnectionRefusedError('refused')) as connect:
        assert tr.get('https://example.test/')[1]=='connection_error'
        assert tr.get('https://example.test/')[1]=='connection_error'
    assert [call.args[0][0] for call in connect.call_args_list]==list(addresses)
