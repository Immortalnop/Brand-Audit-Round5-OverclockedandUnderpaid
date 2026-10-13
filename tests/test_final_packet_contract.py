"""Schema 1.1 integrity: production exports, exact bytes and supported parents."""
import copy
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'tests', 'skills/audit-orchestrator/scripts', 'skills/entity-corroboration-agent/scripts'):
    sys.path.insert(0, str(ROOT / rel))

import agent_evidence
from agent_evidence import build_evidence_packet, snapshot_digest
from packet_contract import packet_digest, emitted_bytes, emitted_json, fit_packet, validate_registry, nonready_packet
from ingest_agent_findings import validate_envelope, EnvelopeError
from models import freeze_value
from test_precision_traps import page, snapshot, SITE
from run_audit import write_report, _emit_packet


def packet_for(*pages, media=None, identity=None, facts=None):
    artifacts = snapshot(*(pages or [page('<p>Acme makes payroll software for small teams.</p>')]))
    if media:
        artifacts = replace(artifacts, media_data=freeze_value(media))
    return build_evidence_packet(artifacts, identity or {}, facts or {}, {}, 'a1', snapshot_digest(artifacts), 'now')


def assess(packet):
    report = {'audit_id': packet['audit_id'], 'snapshot_sha256': packet['snapshot_sha256'],
              'packet_sha256': packet['packet_sha256'], 'coverage': {}, 'site': SITE}
    selected = packet.get('focus', {}).get('ag01', {})
    envelope = dict(schema_version='1.1', audit_id=report['audit_id'], snapshot_sha256=report['snapshot_sha256'],
                    packet_sha256=packet['packet_sha256'], capabilities={'local_reading': True},
                    checks=[{'check': 'AG-01', 'outcome': 'pass', 'source_refs': [selected.get('page_ref', 'E001')],
                             'observation': {'passage': selected.get('opening_passage', '')}, 'reason': 'Clear opening.'}])
    return report, envelope


@pytest.mark.parametrize('field', ['text', 'title', 'claim', 'image', 'focus', 'timing'])
def test_edited_final_content_is_rejected_with_old_headers(field):
    packet = packet_for()
    report, envelope = assess(packet)
    if field in ('text', 'title'):
        packet['pages'][0][field] = 'Edited acquired content.'
    else:
        packet[field] = {'edited': True}
    with pytest.raises(EnvelopeError, match='packet_sha256'):
        validate_envelope(envelope, report, packet)


def test_whitespace_and_object_key_order_do_not_change_content_digest():
    packet = packet_for()
    reordered = json.loads(json.dumps(packet, sort_keys=True, indent=4))
    assert packet_digest(reordered) == packet['packet_sha256']
    report, envelope = assess(packet)
    assert validate_envelope(envelope, report, reordered)['checks']['AG-01']['outcome'] == 'pass'


@pytest.mark.parametrize('owner', ['report', 'envelope'])
def test_recomputed_tampered_digest_still_needs_saved_binding(owner):
    packet = packet_for()
    report, envelope = assess(packet)
    packet['pages'][0]['text'] = 'Changed facts.'
    packet['packet_sha256'] = packet_digest(packet)
    (report if owner == 'envelope' else envelope)['packet_sha256'] = packet['packet_sha256']
    with pytest.raises(EnvelopeError, match='packet_sha256'):
        validate_envelope(envelope, report, packet)


@pytest.mark.parametrize('version', ['1.0', '2.0', None])
def test_old_or_unsupported_envelope_version_is_rejected(version):
    packet = packet_for()
    report, envelope = assess(packet)
    envelope['schema_version'] = version
    with pytest.raises(EnvelopeError, match='schema_version'):
        validate_envelope(envelope, report, packet)


def test_pathological_image_identity_and_urls_are_bounded():
    packet = packet_for(media={'images': [{'url': SITE + '/price.png', 'same_origin': True,
                       'pages': [SITE + '/'], 'alt': '界' * 600000, 'keywords': ['界' * 10000] * 100}]},
                        identity={'data': {'canonical_name': '界' * 600000, 'aliases': ['A' * 10000] * 100,
                                          'same_as_urls': ['https://example.com/' + 'x' * 3000] * 100}})
    assert emitted_bytes(packet) <= agent_evidence.MAX_PACKET_BYTES
    assert len(packet['image_candidates'][0]['alt']) <= 500
    assert len(packet['identity']['name']) <= 500
    assert packet['identity']['same_as_urls'] == []
    assert packet['budget']['metadata_truncated'] > 0 and packet['budget']['metadata_omitted'] > 0
    validate_registry(packet)


def test_fitter_removes_dropped_claim_and_image_and_identity_references():
    pages = [page('<p>' + '界 ' * 3000 + '</p>', url=f'{SITE}/{i}') for i in range(8)]
    packet = packet_for(*pages, media={'images': [{'url': SITE + '/price.png', 'same_origin': True,
                                                 'pages': [f'{SITE}/7'], 'alt': 'price'}]},
                        identity={'data': {'canonical_name': '界'}},
                        facts={'data': {'facts': [{'source': f'{SITE}/7', 'value': '界', 'predicate': 'name'}]}})
    shrunk = fit_packet(packet, 7000)
    assert emitted_bytes(shrunk) <= 7000
    refs = {p['evidence_id'] for p in shrunk['pages']}
    assert not any(c['page_evidence_id'] not in refs for c in shrunk['claims'])
    assert all(set(i['page_evidence_ids']) <= refs for i in shrunk['image_candidates'])
    assert set(shrunk['identity']['source_refs']) <= refs
    assert shrunk['budget']['pages_selected'] == len(shrunk['pages'])
    assert 'packet_bytes' not in shrunk['budget']
    validate_registry(shrunk)


def test_fitter_matches_exact_writer_bytes_including_digest_and_newline(tmp_path):
    packet = packet_for(page('<p>' + '界😀 ' * 3000 + '</p>'))
    path = tmp_path / 'packet.json'
    write_report(packet, path)
    assert path.read_bytes() == emitted_json(packet).encode('utf-8')
    assert len(path.read_bytes()) == emitted_bytes(packet)
    assert packet['packet_sha256'] == packet_digest(packet)
    limit = emitted_bytes(packet)
    assert emitted_bytes(fit_packet(copy.deepcopy(packet), limit)) <= limit
    assert emitted_bytes(fit_packet(copy.deepcopy(packet), limit - 1)) <= limit - 1


def test_nonready_current_marker_replaces_stale_ready_export(tmp_path, capsys):
    path = tmp_path / 'packet.json'
    path.write_text(json.dumps(packet_for()))
    marker = nonready_packet('current-audit', None, 'Worker cancelled before evidence acquisition.', SITE)
    assert _emit_packet(marker, path)
    written = json.loads(path.read_text())
    assert written['audit_id'] == 'current-audit' and written['ready_for_assessment'] is False
    assert 'cancelled' in capsys.readouterr().err
    report, envelope = assess(written)
    with pytest.raises(EnvelopeError):
        validate_envelope(envelope, report, written)


def test_packet_write_failure_preserves_core_report_and_records_reason(tmp_path, monkeypatch):
    import run_audit
    report = {'coverage': {}, 'findings': []}
    monkeypatch.setattr(run_audit, 'write_report', lambda *args: (_ for _ in ()).throw(OSError('disk full')))
    assert not _emit_packet(packet_for(), tmp_path / 'packet.json', report)
    assert report['coverage']['evidence_packet_write_failed'] is True
    assert report['findings'] == [] and 'disk full' in report['warnings'][0]


@pytest.mark.parametrize('mutation', ['parent', 'source', 'image', 'identity'])
def test_registry_rejects_dangling_or_unrelated_support(mutation):
    packet = packet_for(facts={'data': {'facts': [{'source': SITE + '/', 'value': 'Acme'}]}})
    if mutation == 'parent':
        packet['claims'][0]['page_evidence_id'] = 'E999'
    elif mutation == 'source':
        packet['claims'][0]['source_url'] = SITE + '/unobserved'
    elif mutation == 'image':
        packet['image_candidates'] = [{'image_id': 'I001', 'page_evidence_ids': ['E999'], 'pages': [SITE]}]
    else:
        packet['identity']['source_refs'] = ['E999']
    with pytest.raises(ValueError):
        validate_registry(packet)
