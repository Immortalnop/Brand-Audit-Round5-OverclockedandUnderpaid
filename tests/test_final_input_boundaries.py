"""Master plan phase 1: adversarial boundaries and genuine usable controls."""
import copy
import io
import json
import sys
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'skills/audit-orchestrator/scripts', 'skills/entity-corroboration-agent/scripts',
            'skills/freshness-corroboration/scripts', 'skills/crawl-render-audit/scripts', 'tests'):
    sys.path.insert(0, str(ROOT / rel))

from json_boundary import read_json, loads, JSONLimitError, JSONAmbiguityError, JSONSyntaxError
from report_markdown import read_report, render
from ingest_agent_findings import read_agent_input, validate_envelope, AgentFindingsError, EnvelopeError
from agent_evidence import evidence_ids
from run_audit import write_report
from check_fact_consistency import parse_price, check_fact_consistency, price_shown
from money import markup_money, visible_money
from models import freeze_value, make_deadline
from test_precision_traps import page, snapshot, LIMITS, SITE


def binding():
    report = {'audit_id': 'a1', 'snapshot_sha256': 's1', 'site': SITE, 'coverage': {}}
    packet = dict(report, pages=[{'evidence_id': 'E001', 'text': 'Acme builds payroll software.',
                                  'requested_url': SITE, 'final_url': SITE, 'observation_status': 'complete'}],
                  claims=[], image_candidates=[])
    envelope = {'schema_version': '1.0', 'audit_id': 'a1', 'snapshot_sha256': 's1',
                'capabilities': {'local_reading': True},
                'checks': [{'check': 'AG-01', 'outcome': 'finding', 'source_refs': ['E001'],
                            'reason': 'The opening does not identify its audience.',
                            'observation': {'passage': 'Acme builds payroll software.', 'unanswered': ['who']}}]}
    return report, packet, envelope


@pytest.mark.parametrize('raw', ['{"checks":[],"checks":[]}', '{"x":NaN}', '{"x":Infinity}',
                                '{"x":-Infinity}', '{"x":1e999}', '[' * 1000 + '0' + ']' * 1000])
def test_agent_file_bad_json_is_bounded_public_error(tmp_path, raw):
    path = tmp_path / 'outcomes.json'
    path.write_text(raw)
    with pytest.raises(AgentFindingsError) as caught:
        read_agent_input(path)
    assert len(str(caught.value)) < 600


@pytest.mark.parametrize('encoding', ['utf-8', 'utf-8-sig', 'utf-16'])
def test_valid_agent_and_report_encodings_remain_supported(tmp_path, encoding):
    _, _, envelope = binding()
    path = tmp_path / 'input.json'
    path.write_bytes(json.dumps(envelope).encode(encoding))
    assert read_agent_input(path) == envelope
    path.write_bytes(json.dumps({'site': SITE, 'findings': []}).encode(encoding))
    assert read_report(path)['site'] == SITE


def test_bounded_reader_does_not_trust_stat_or_read_to_eof(monkeypatch):
    calls = []
    class Stream(io.BytesIO):
        def read(self, count=-1):
            calls.append(count)
            return super().read(count)
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: Stream(b'x' * 100))
    with pytest.raises(JSONLimitError):
        read_json('changing-file', 20)
    assert calls == [21]


@pytest.mark.parametrize('raw', [b'\xff', b'\xff\xfe{', b'"\\ud800"'])
def test_invalid_encoding_and_surrogates_are_controlled(tmp_path, raw):
    path = tmp_path / 'input.json'
    path.write_bytes(raw)
    with pytest.raises((UnicodeDecodeError, ValueError)):
        read_report(path)


@pytest.mark.parametrize('field,value', [('unanswered', [{}]), ('unanswered', [True]),
                                        ('passage', {}), ('material', 'true'), ('competing_entities', [{}]),
                                        ('platforms_missing', [None])])
def test_nested_envelope_types_fail_before_hashing(field, value):
    report, packet, envelope = binding()
    envelope['checks'][0]['observation'][field] = value
    # competing entities with absent fields get caught by the per-check validator
    # for its applicable check, rather than being stringified into facts.
    if field == 'competing_entities':
        envelope['checks'][0]['check'] = 'AG-05'
        envelope['capabilities']['search'] = True
    with pytest.raises(EnvelopeError):
        validate_envelope(envelope, report, packet)


@pytest.mark.parametrize('field,value', [('check', {}), ('outcome', []), ('sources', [{'kind': {}}]),
                                        ('queries', [{'query': 'Acme', 'result_count': True}]),
                                        ('affected_pages', [{}]), ('source_refs', [{}]),
                                        ('confidence', True), ('confidence', float('nan'))])
def test_envelope_malformed_members_raise_envelope_error(field, value):
    report, packet, envelope = binding()
    envelope['checks'][0][field] = value
    before = copy.deepcopy(report)
    with pytest.raises(EnvelopeError):
        validate_envelope(envelope, report, packet)
    assert report == before


def test_valid_typed_local_assessment_still_works():
    report, packet, envelope = binding()
    result = validate_envelope(envelope, report, packet)
    assert result['findings'][0]['status'] == 'suspected'


@pytest.mark.parametrize('record', [{'evidence_id': {}}, {'evidence_id': 'E001', 'text': []},
                                   {'evidence_id': 'E001', 'text_truncated': 1}])
def test_packet_registry_rejects_malformed_members(record):
    with pytest.raises(ValueError):
        evidence_ids({'pages': [record]})


def test_duplicate_packet_ids_are_not_last_write_wins():
    with pytest.raises(ValueError, match='duplicate evidence ID'):
        evidence_ids({'pages': [{'evidence_id': 'E001'}, {'evidence_id': 'E001'}]})


@pytest.mark.parametrize('value', [{'coverage': []}, {'findings': [{}], 'recommendations': ['x']},
                                  {'findings': [{'severity': []}]}, {'findings': [{'confidence': True}]},
                                  {'coverage': {'pages_analyzed': True}}, {'limitations': [{}]}])
def test_renderer_rejects_wrong_semantic_shapes_normally(value):
    with pytest.raises(ValueError):
        render(value)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), object()])
def test_json_writer_rejection_preserves_existing_destination(tmp_path, value):
    path = tmp_path / 'report.json'
    path.write_text('saved base')
    with pytest.raises(ValueError):
        write_report({'bad': value}, path)
    assert path.read_text() == 'saved base'
    assert not list(tmp_path.glob('.report-*.tmp'))


@pytest.mark.parametrize('number,state', [('NaN', 'malformed'), ('Infinity', 'malformed'),
                                        ('1e999', 'unsupported'), ('true', 'usable')])
def test_jsonld_numeric_states_and_unaffected_block_survive(number, state):
    html = ('<script type="application/ld+json">{"@type":"Offer","price":' + number + '}</script>'
            '<script type="application/ld+json">{"@type":"Organization","name":"Acme"}</script>')
    acquired = page('<p>Acme sells software for small teams.</p>', html)
    assert any(block.get('name') == 'Acme' for block in acquired.jsonld_blocks)
    if state == 'malformed':
        assert 'malformed_jsonld_block' in acquired.warnings
    elif state == 'unsupported':
        assert 'jsonld_unsupported_block' in acquired.warnings
        assert not acquired.features['jsonld_errors']
    else:
        assert len(acquired.jsonld_blocks) == 2
    check_fact_consistency(snapshot(acquired), make_deadline(LIMITS))


def test_duplicate_jsonld_keys_are_ambiguity_and_other_blocks_survive():
    acquired = page('<p>Acme sells software.</p>', '<script type="application/ld+json">'
                    '{"@type":"Offer","price":49,"price":9}</script>')
    assert acquired.features['jsonld_extraction_state'] == 'ambiguous'
    assert not acquired.features['jsonld_errors']


@pytest.mark.parametrize('value', [float('nan'), float('inf'), float('-inf'), True, 'price123oops', '1e999'])
def test_money_rejects_unsupported_values_without_manufacturing_price(value):
    assert parse_price(value) is None
    assert markup_money(value) is None
    acquired = page('<p>Widget $9.</p>', url=SITE + '/product')
    acquired = replace(acquired, jsonld_blocks=freeze_value([{'@type': 'Product', 'name': 'Widget',
                                 'offers': {'@type': 'Offer', 'price': value, 'priceCurrency': 'USD'}}]))
    result = check_fact_consistency(snapshot(acquired), make_deadline(LIMITS))
    assert not result['findings']


@pytest.mark.parametrize('raw,expected', [('-49', -49), ('1e3', 1000), ('0', 0), (49.5, 49.5)])
def test_money_preserves_signed_exponent_zero_and_decimal_meaning(raw, expected):
    assert markup_money(raw) == expected
    assert parse_price(raw) == expected


def test_markup_and_visible_money_have_distinct_grammars():
    assert markup_money('1,299.00') is None
    assert visible_money('$1,299.00') == 1299
    assert visible_money('1.299,00 EUR') == 1299
    assert visible_money('9,9') is None
    assert not price_shown(float('nan'), 'NaN $9')


def test_duplicate_saved_finding_ids_are_rejected():
    with pytest.raises(ValueError, match='duplicate findings ID'):
        render({'findings': [{'id': 'F-001'}, {'id': 'F-001'}]})


def test_malformed_cli_merge_is_atomic_without_traceback(tmp_path):
    report, packet, envelope = binding()
    report.update(findings=[], recommendations=[])
    report['coverage']['pages_analyzed'] = 1
    envelope['checks'][0]['observation']['unanswered'] = [{}]
    paths = [tmp_path / name for name in ('base.json', 'packet.json', 'outcomes.json')]
    for path, value in zip(paths, (report, packet, envelope)):
        path.write_text(json.dumps(value))
    before = [path.read_bytes() for path in paths]
    output = tmp_path / 'final.json'
    output.write_text('previous output')
    result = subprocess.run([sys.executable, str(ROOT / 'skills/audit-orchestrator/scripts/run_audit.py'),
                             '--from-report', str(paths[0]), '--agent-findings', str(paths[2]),
                             '--evidence', str(paths[1]), '--out', str(output)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'unanswered must be a bounded list of strings' in result.stderr
    assert 'Traceback' not in result.stderr
    assert output.read_text() == 'previous output'
    assert [path.read_bytes() for path in paths] == before
