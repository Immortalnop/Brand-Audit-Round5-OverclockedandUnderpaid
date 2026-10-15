"""Offline verification of replay commands, not an executed Claude assessment."""
from pathlib import Path
import contextlib
import copy
import hashlib
import http.client
import io
import json
import shutil
import socket
import sys

REPO = Path(__file__).resolve().parents[2]
PACKAGE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(exist_ok=True)
sys.dont_write_bytecode = True
for rel in ('common', 'skills/audit-orchestrator/scripts', 'skills/entity-corroboration-agent/scripts'):
    sys.path.insert(0, str(PACKAGE/rel))
import run_audit
import report_markdown

attempts = []
def no_network(*args, **kwargs):
    attempts.append('network operation')
    raise AssertionError('Offline merge/render attempted a network operation')
socket.create_connection = no_network
socket.socket.connect = no_network
http.client.HTTPConnection.request = no_network

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def command(module, args):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            result = module.main(args)
        except SystemExit as exc:
            result = exc.code
    return {'exit_code': result, 'stdout': stdout.getvalue(), 'stderr': stderr.getvalue()}

results = {}
for slug in ('bare', 'python'):
    src = REPO/'verification/replay-manifest'/('live-'+slug)
    base, packet = src/'base-report.json', src/'evidence.json'
    original = {'base': sha(base), 'packet': sha(packet)}
    p = json.loads(packet.read_text())
    checks = [{'check': f'AG-{i:02}', 'outcome': 'not_assessed',
               'reason': 'Offline contract probe: no fresh host assessment claimed.'} for i in range(1, 7)]
    if slug == 'python':
        focus = p['focus']['ag01']
        assert focus['assessable'] and focus['opening_complete']
        checks[0] = {'check': 'AG-01', 'outcome': 'pass', 'source_refs': [focus['page_ref']],
                     'observation': {'passage': focus['opening_passage']},
                     'reason': 'Offline schema/command probe only; not a timely Claude or accuracy result.'}
    envelope = {'schema_version': '1.1', **{key: p[key] for key in ('audit_id', 'snapshot_sha256', 'packet_sha256')},
                'capabilities': {'local_reading': True, 'search': False, 'vision': False}, 'checks': checks}
    env_path, final, markdown = OUT/(slug+'-outcomes.json'), OUT/(slug+'-final.json'), OUT/(slug+'-final.md')
    env_path.write_text(json.dumps(envelope, indent=2)+'\n', encoding='utf-8')
    args = ['--from-report', str(base), '--agent-findings', str(env_path), '--evidence', str(packet), '--out', str(final)]
    merged = command(run_audit, args)
    assert merged['exit_code'] == 0, merged
    rendered = command(report_markdown, [str(final), str(markdown)])
    assert rendered['exit_code'] == 0 and markdown.read_text(), rendered
    report = json.loads(final.read_text())
    assert report['coverage']['agent_stage']['assessed_count'] == (1 if slug == 'python' else 0)
    assert report['findings'] == json.loads(base.read_text())['findings']
    assert original == {'base': sha(base), 'packet': sha(packet)}
    results[slug+'_ready_merge_render'] = {'passed': True, 'assessed_count': report['coverage']['agent_stage']['assessed_count'],
                                          'original_findings_unchanged': True, 'base_packet_unchanged': True,
                                          'scope': 'Offline command/contract probe; no new host judgment/execution claim'}
    if slug == 'python':
        changed = copy.deepcopy(p)
        changed['identity']['name'] += ' altered'
        altered = OUT/'altered-packet.json'
        altered.write_text(json.dumps(changed)+'\n')
        sentinel = OUT/'rejection-output.json'
        sentinel.write_text('preserve this existing file\n')
        prior = sha(sentinel)
        rejected = command(run_audit, ['--from-report', str(base), '--agent-findings', str(env_path),
                                      '--evidence', str(altered), '--out', str(sentinel)])
        assert rejected['exit_code'] == 2 and sha(sentinel) == prior, rejected
        results['altered_packet_rejection'] = {'passed': True, 'exit_code': 2, 'existing_output_preserved': True,
                                               'diagnostic': rejected['stderr'][-1500:]}
    else:
        unsupported = copy.deepcopy(envelope)
        unsupported['checks'][0] = {'check': 'AG-01', 'outcome': 'pass', 'source_refs': ['E001'],
                                    'observation': {'passage': 'invented opening'}, 'reason': 'unsupported probe'}
        bad = OUT/'unsupported-opening.json'
        bad.write_text(json.dumps(unsupported)+'\n')
        bad_final = OUT/'unsupported-opening-final.json'
        rejected = command(run_audit, ['--from-report', str(base), '--agent-findings', str(bad),
                                      '--evidence', str(packet), '--out', str(bad_final)])
        assert rejected['exit_code'] == 2 and not bad_final.exists(), rejected
        results['unassessable_opening_rejection'] = {'passed': True, 'exit_code': 2,
                                                    'no_final_output': True, 'diagnostic': rejected['stderr'][-1500:]}

nonready = REPO/'verification/review-set/publishing'
assert json.loads((nonready/'evidence.json').read_text())['ready_for_assessment'] is False
fallback = OUT/'nonready-final.json'
shutil.copyfile(nonready/'base-report.json', fallback)
rendered = command(report_markdown, [str(fallback), str(OUT/'nonready-final.md')])
assert rendered['exit_code'] == 0 and sha(fallback) == sha(nonready/'base-report.json')
results['nonready_unchanged_base_fallback'] = {'passed': True, 'byte_identical': True,
                                             'renderer_exit_code': rendered['exit_code'],
                                             'source': 'verification/review-set/publishing (dated saved evidence)'}
assert attempts == [], attempts
record = {'scope': 'Offline production CLI/renderer checks against the supplied extracted package. '
                   'The illustrative AG-01 pass tests field binding only, not its truth or a Claude run.',
          'package_directory': str(PACKAGE), 'network_attempts': len(attempts), 'checks': results}
(REPO/'verification/replay-manifest/offline-contract-checks.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps({'network_attempts': len(attempts), 'checks_passed': list(results)}))
