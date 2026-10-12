"""Offline regression tests for the v6 fixes; no public-site requests."""
import gzip
import json
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
try:
    import pytest
    fixture = pytest.fixture
except ImportError:
    from contextlib import contextmanager
    def fixture(fn):
        return contextmanager(fn)

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'skills/audit-orchestrator/scripts', 'skills/crawl-render-audit/scripts',
            'skills/engagement-audit/scripts', 'skills/freshness-corroboration/scripts'):
    sys.path.insert(0, str(ROOT / rel))
from constants import Limits
from instrumentation import Instrumentation
from models import make_deadline, _jsonable
from acquire_site import acquire_site
from run_audit import run_audit
from robots_policy import RobotsPolicy
from transport import Transport
from structured_data import iter_nodes, types_of
from subprocess_isolation import run_isolated, _hang_forever
from corroborate_claims import _compare_claim_to_results

@fixture
def site():
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            seen.append(self.path)
            status, headers = 200, {'Content-Type': 'text/html'}
            if self.path == '/robots.txt':
                body = b'User-agent: *\nDisallow: /private\nAllow: /private/open$\n'
                headers['Content-Type'] = 'text/plain'
            elif self.path == '/sitemap.xml':
                body = b'<sitemapindex><sitemap><loc>/child.xml</loc></sitemap></sitemapindex>'
            elif self.path == '/child.xml':
                body = b'<urlset><url><loc>/about?q=1</loc></url></urlset>'
            elif self.path == '/llms.txt': body = b'<html>soft 404 landing</html>'
            elif self.path == '/jump':
                status, body = 302, b''
                headers['Location'] = '/private'
            elif self.path == '/bomb':
                body = gzip.compress(b'x' * 500000)
                headers['Content-Encoding'] = 'gzip'
            else:
                body = b'''<html lang="en"><title>Fixture</title><meta name="robots" content="noindex nosnippet">
                <meta name="viewport" content="width=device-width"><h1>Independent fixture</h1>
                <script type="application/ld+json">{"@graph":[{"@type":["https://schema.org/Organization"],"name":"Fixture"}]}</script>
                <a href="/jump">Jump</a><a href="/about?q=1">About</a><a href="/about?q=2">Other</a></html>'''
            self.send_response(status)
            for k,v in headers.items(): self.send_header(k,v)
            self.send_header('Content-Length', str(len(body))); self.end_headers()
            try: self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}', seen
    server.shutdown();server.server_close();thread.join()


def test_robots_longest_match_groups_and_wildcards():
    p = RobotsPolicy('User-agent: *\nDisallow: /private\nAllow: /private/open$\nDisallow: /*?secret=\nUser-agent: Special\nAllow: /\n')
    assert not p.can_fetch('Audit', 'https://x/private')
    assert p.can_fetch('Audit', 'https://x/private/open')
    assert not p.can_fetch('Audit', 'https://x/private/open/more')
    assert not p.can_fetch('Audit', 'https://x/page?secret=1')
    assert p.can_fetch('Special', 'https://x/private')


def test_redirect_cannot_bypass_robots(site):
    url, seen = site
    tr = Transport(url,time.monotonic()+5,Limits(),Instrumentation(),True)
    tr.robots = RobotsPolicy('User-agent: *\nDisallow: /private')
    response,status = tr.get(url+'/jump')
    assert response is None and status == 'robots_disallowed'
    assert '/private' not in seen


def test_gzip_expansion_is_bounded_and_charged(site):
    url,_=site
    tr=Transport(url,time.monotonic()+5,replace(Limits(),MAX_TOTAL_BYTES=1000),Instrumentation(),True)
    response,status=tr.get(url+'/bomb')
    assert status=='ok' and response.truncated and len(response.content)<=1000
    assert tr.bytes==1000
    assert tr.get(url+'/')[1]=='budget_exhausted'


def test_all_probes_share_request_limit(site):
    url,seen=site
    limits=replace(Limits(),MAX_TOTAL_HTTP_REQUESTS=2)
    acquire_site(url+'/',make_deadline(limits),limits,allow_private_targets=True)
    assert len(seen)==2


def test_sitemap_index_relative_children_and_queries(site):
    url,seen=site
    limits=Limits()
    a=acquire_site(url+'/',make_deadline(limits),limits,allow_private_targets=True)
    assert '/child.xml' in seen
    assert {url+'/about?q=1',url+'/about?q=2'} <= {p.url for p in a.pages}
    assert a.llms_txt_data['status']=='malformed'
    assert '/private' not in seen


def test_nested_type_arrays_and_full_schema_uris():
    nodes=list(iter_nodes({'@graph':[{'@type':['https://schema.org/Organization'], 'subjectOf':{'@type':'Article'}}]}))
    assert {'Organization','Article'} == set().union(*(types_of(n) for n in nodes))


def test_complete_report_survives_process_boundary_and_is_json(site):
    url,_=site
    r=run_audit(url+'/',allow_private_targets=True)
    json.dumps(r,allow_nan=False)
    assert r['coverage']['pages_analyzed']>0
    assert {'noindex','nosnippet'} <= {p['rule_id'] for f in r['findings'] for p in f['provenance']['contributing_skills']}
    assert not any('Dropped' in w for w in r['warnings'])
    assert r['recommendations'] and r['top_actions']


def _large_result(): return 'x'*2000000


def test_process_large_result_does_not_deadlock():
    r=run_isolated(_large_result,timeout_s=3)
    assert r.ok and len(r.value)==2000000


def test_hung_worker_is_terminated():
    start=time.monotonic();r=run_isolated(_hang_forever,timeout_s=.1)
    assert r.timed_out and time.monotonic()-start<2


def test_numeric_match_cannot_join_unrelated_numbers():
    outcome,_=_compare_claim_to_results({'type':'price','value':'$1234'},[
        {'title':'12 items','snippet':'34 reviews','url':'https://independent.example'}])
    assert outcome=='not_found'


def test_marketplace_frontmatter():
    import yaml
    manifest=json.loads((ROOT/'marketplace.json').read_text())
    assert len(manifest['skills'])==5
    assert sum(bool(s.get('entrypoint')) for s in manifest['skills'])==1
    for skill in manifest['skills']:
        path=ROOT/skill['path'];front=yaml.safe_load((path/'SKILL.md').read_text().split('---',2)[1])
        assert front['name']==path.name and isinstance(front['description'],str)
        assert isinstance(front.get('allowed-tools'),str)


if __name__ == '__main__':
    test_robots_longest_match_groups_and_wildcards()
    print("PASS: test_robots_longest_match_groups_and_wildcards")
    test_nested_type_arrays_and_full_schema_uris()
    print("PASS: test_nested_type_arrays_and_full_schema_uris")
    test_process_large_result_does_not_deadlock()
    print("PASS: test_process_large_result_does_not_deadlock")
    test_hung_worker_is_terminated()
    print("PASS: test_hung_worker_is_terminated")
    test_numeric_match_cannot_join_unrelated_numbers()
    print("PASS: test_numeric_match_cannot_join_unrelated_numbers")
    test_marketplace_frontmatter()
    print("PASS: test_marketplace_frontmatter")

    with site() as s:
        test_redirect_cannot_bypass_robots(s)
        print("PASS: test_redirect_cannot_bypass_robots")
    with site() as s:
        test_gzip_expansion_is_bounded_and_charged(s)
        print("PASS: test_gzip_expansion_is_bounded_and_charged")
    with site() as s:
        test_all_probes_share_request_limit(s)
        print("PASS: test_all_probes_share_request_limit")
    with site() as s:
        test_sitemap_index_relative_children_and_queries(s)
        print("PASS: test_sitemap_index_relative_children_and_queries")
    with site() as s:
        test_complete_report_survives_process_boundary_and_is_json(s)
        print("PASS: test_complete_report_survives_process_boundary_and_is_json")
    print("All v6 regression tests passed!")

