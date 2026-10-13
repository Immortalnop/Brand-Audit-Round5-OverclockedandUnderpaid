"""Semantic counterexamples and genuine acquired positive controls for AG checks."""
import copy
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'tests', 'skills/entity-corroboration-agent/scripts', 'skills/audit-orchestrator/scripts'):
    sys.path.insert(0, str(ROOT / rel))

from agent_evidence import build_evidence_packet, snapshot_digest
from ingest_agent_findings import validate_envelope, EnvelopeError
from packet_contract import packet_digest
from models import freeze_value
from test_precision_traps import page, snapshot, SITE


def setup(*pages, media=None, facts=None):
    artifacts = snapshot(*(pages or [page('<p>Acme makes payroll software for small teams.</p>')]))
    if media:
        artifacts = replace(artifacts, media_data=freeze_value(media))
    packet = build_evidence_packet(artifacts, {'data': {'canonical_name': 'Acme', 'same_as_urls': ['https://profile.example/acme']}},
                                   facts or {}, {}, 'a1', snapshot_digest(artifacts), 'now')
    report = {'audit_id': 'a1', 'snapshot_sha256': packet['snapshot_sha256'], 'packet_sha256': packet['packet_sha256'],
              'site': SITE, 'coverage': {'audited_url': SITE}}
    envelope = {'schema_version': '1.1', 'audit_id': 'a1', 'snapshot_sha256': packet['snapshot_sha256'],
                'packet_sha256': packet['packet_sha256'], 'capabilities': {'local_reading': True, 'search': True, 'vision': True},
                'checks': []}
    return report, packet, envelope


def query(platform='', matching=0):
    return {'query': '"Acme" payroll ' + platform, 'platform': platform, 'result_count': matching,
            'matching_result_count': matching, 'independent_result_count': matching, 'executed_at': '2026-10-13'}


def ag03(packet):
    quote = packet['pages'][0]['focus_text']
    return {'check': 'AG-03', 'outcome': 'finding', 'source_refs': ['E001'], 'queries': [query()],
            'reason': 'Current category differs materially.',
            'sources': [{'url': 'https://news.example/acme', 'kind': 'inspected_page', 'authorship': 'News editor',
                         'quote': 'Acme is an accounting practice for local businesses.'},
                        {'url': 'https://directory.example/acme', 'kind': 'inspected_page', 'authorship': 'Directory researcher',
                         'quote': 'Acme provides bookkeeping services.'}],
            'observation': {'identity': 'Acme payroll', 'site_claim': 'Acme makes payroll software.', 'site_quote': quote,
                            'same_entity': 'Same company, domain and local office.', 'context': 'Current offering, October 2026.',
                            'independence': 'Different independently maintained sources, no syndication.',
                            'conflict_explanation': 'Software product versus accounting service category.', 'material': True}}


def validate(entry, state):
    report, packet, envelope = state
    envelope = copy.deepcopy(envelope)
    envelope['checks'] = [entry]
    return validate_envelope(envelope, report, packet)


def test_actual_acquired_conflict_is_high_and_scoped_to_support():
    state = setup()
    result = validate(ag03(state[1]), state)
    finding = result['findings'][0]
    assert finding['severity'] == 'high' and finding['status'] == 'confirmed'
    assert finding['affected_pages'] == [SITE + '/']


@pytest.mark.parametrize('quote', ['Acme builds nuclear submarines.', 'Acme does not make payroll software.',
                                  'Acme makes payroll software for large enterprises.'])
def test_invented_or_materially_changed_quote_cannot_borrow_valid_reference(quote):
    state = setup()
    entry = ag03(state[1]);entry['observation']['site_quote'] = quote
    with pytest.raises(EnvelopeError, match='site_quote is not bound'):
        validate(entry, state)


def test_agreeing_sources_do_not_become_confirmed_conflict():
    state = setup();entry = ag03(state[1])
    for source in entry['sources']:
        source['quote'] = entry['observation']['site_quote']
    with pytest.raises(EnvelopeError, match='merely agree'):
        validate(entry, state)


def test_own_origin_is_not_independent_and_syndicated_authorship_cannot_earn_high():
    state = setup();entry = ag03(state[1]);entry['sources'][0]['url'] = SITE + '/news'
    with pytest.raises(EnvelopeError, match='not independent'):
        validate(entry, state)
    entry = ag03(state[1])
    entry['sources'][1]['authorship'] = entry['sources'][0]['authorship']
    result = validate(entry, state)
    assert result['findings'][0]['severity'] == 'medium' and result['findings'][0]['status'] == 'suspected'


def test_affected_url_can_narrow_but_not_expand_acquired_quote_support():
    state = setup(page('<p>Acme makes payroll software for small teams.</p>'), page('<p>Unrelated.</p>', url=SITE + '/other'))
    entry = ag03(state[1]);entry['affected_pages'] = [SITE + '/not-acquired']
    with pytest.raises(EnvelopeError, match='cannot expand'):
        validate(entry, state)
    entry['affected_pages'] = [SITE + '/other']
    with pytest.raises(EnvelopeError, match='cannot expand'):
        validate(entry, state)
    entry['affected_pages'] = [SITE + '/']
    assert validate(entry, state)['findings'][0]['affected_pages'] == [SITE + '/']


def test_structured_claim_requires_matching_subject_and_predicate():
    state = setup(facts={'data': {'facts': [{'source': SITE + '/', 'subject': 'Acme', 'predicate': 'offering', 'value': 'payroll software'}]}})
    entry = ag03(state[1]);entry['source_refs'] = ['C001'];entry['observation']['site_quote'] = 'payroll software'
    entry['observation'].update(subject='Unrelated entity', predicate='offering')
    with pytest.raises(EnvelopeError, match='subject/predicate'):
        validate(entry, state)
    entry['observation']['subject'] = 'Acme'
    assert validate(entry, state)['findings'][0]['affected_pages'] == [SITE + '/']


def test_ag01_cannot_assess_home_when_about_is_selected_for_pass_or_finding():
    state = setup(page('<a href="/about">About us</a><p>Acme home.</p>'), page('<p>Acme about.</p>', url=SITE + '/about'))
    for outcome in ('pass', 'finding'):
        entry = {'check': 'AG-01', 'outcome': outcome, 'source_refs': ['E001'], 'reason': 'Home assessed.',
                 'observation': {'passage': 'Acme home.', 'unanswered': ['category']}}
        with pytest.raises(EnvelopeError, match='selected focused'):
            validate(entry, state)


def test_failed_about_keeps_not_assessed_even_when_home_is_concrete():
    failed = replace(page('', url=SITE + '/about'), status_code=503)
    state = setup(page('<a href="/about">About us</a><p>Acme makes payroll software.</p>'), failed)
    entry = {'check': 'AG-01', 'outcome': 'pass', 'source_refs': ['E001'], 'reason': 'Home is concrete.',
             'observation': {'passage': 'Acme makes payroll software.'}}
    with pytest.raises(EnvelopeError, match='not assessable'):
        validate(entry, state)
    entry.update(outcome='not_assessed', reason='Known About returned 503.')
    assert validate(entry, state)['checks']['AG-01']['outcome'] == 'not_assessed'


def image_state():
    return setup(media={'images': [{'url': SITE + '/price.png', 'same_origin': True, 'alt': 'Price list',
                                   'pages': [SITE + '/', SITE + '/unexported']} ]})


def ag04():
    return {'check': 'AG-04', 'outcome': 'finding', 'source_refs': ['I001', 'E001'], 'reason': 'Price drawn in pixels.',
            'observation': {'image_viewed': True, 'transcription': 'Basic $19', 'compared_page_refs': ['E001'],
                            'text_comparison': 'The delivered text does not state this price.',
                            'comparison_scope': 'raw_html_text', 'markup_limitation': 'Markup comparison not available.'}}


def test_unexported_image_page_cannot_inherit_confirmation():
    state = image_state();entry = ag04()
    result = validate(entry, state)
    assert result['findings'][0]['affected_pages'] == [SITE + '/']
    assert result['findings'][0]['status'] == 'suspected'
    entry['affected_pages'] = [SITE + '/unexported']
    with pytest.raises(EnvelopeError, match='cannot expand'):
        validate(entry, state)


@pytest.mark.parametrize('change', ['no_view', 'no_compared', 'wrong_provenance', 'no_markup_limit'])
def test_image_filename_alt_and_unscoped_comparison_are_not_vision(change):
    state = image_state();entry = ag04()
    if change == 'no_view':entry['observation']['image_viewed'] = False
    elif change == 'no_compared':entry['observation']['compared_page_refs'] = []
    elif change == 'wrong_provenance':entry['observation']['comparison_scope'] = 'rendered_text'
    else:entry['observation'].pop('markup_limitation')
    with pytest.raises(EnvelopeError):
        validate(entry, state)


def test_ag06_missing_platforms_cannot_exceed_actual_zero_matching_queries():
    state = setup()
    entry = {'check': 'AG-06', 'outcome': 'finding', 'reason': 'No platform profile found.', 'queries': [query('G2')],
             'observation': {'identity': 'Acme', 'context': 'October 2026 brand/category search.',
                             'business_applicability': 'B2B payroll software.', 'platforms_missing': ['G2', 'Yelp']}}
    with pytest.raises(EnvelopeError, match='subset of queried'):
        validate(entry, state)
    entry['observation']['platforms_missing'] = ['G2']
    finding = validate(entry, state)['findings'][0]
    assert finding['severity'] == 'low' and finding['affected_pages'] == []


def test_ag05_sameas_is_not_automatically_a_competing_entity():
    state = setup()
    entry = {'check': 'AG-05', 'outcome': 'finding', 'reason': 'Namesake found.', 'queries': [query()], 'source_refs': ['E001'],
             'sources': [{'url': 'https://profile.example/acme', 'kind': 'inspected_page', 'quote': 'Acme payroll software'}],
             'observation': {'identity': 'Acme', 'context': 'October 2026 entity search.',
                             'competing_entities': [{'name': 'Acme', 'url': 'https://profile.example/acme',
                                                     'distinguishing': 'Payroll software profile'}]}}
    with pytest.raises(EnvelopeError, match='not a competing'):
        validate(entry, state)


def test_search_pass_needs_relevant_queries_and_actual_matching_outcomes():
    state = setup()
    entry = {'check': 'AG-02', 'outcome': 'pass', 'reason': 'Checked.', 'queries': [query()],
             'observation': {'identity': 'Acme', 'context': 'October 2026 search.'}}
    with pytest.raises(EnvelopeError, match='independent matching mention'):
        validate(entry, state)
    entry['queries'][0] = query(matching=1)
    entry['queries'][0]['query'] = 'Unrelated company'
    with pytest.raises(EnvelopeError, match='not relevant'):
        validate(entry, state)
