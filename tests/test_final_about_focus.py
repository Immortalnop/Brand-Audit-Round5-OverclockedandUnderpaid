"""Corrected donor focus port through acquired immutable page observations."""
import copy
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'tests', 'skills/audit-orchestrator/scripts'):
    sys.path.insert(0, str(ROOT / rel))

from agent_evidence import build_evidence_packet, snapshot_digest
from packet_contract import fit_packet, emitted_bytes, validate_registry
from models import freeze_value
from test_precision_traps import page, snapshot, SITE


DESCRIPTION = 'Acme makes payroll software for small businesses in Leeds.'


def build(*pages, metadata=None):
    artifacts = snapshot(*pages)
    if metadata:
        artifacts = replace(artifacts, acquisition_metadata=freeze_value(metadata))
    return build_evidence_packet(artifacts, {}, {}, {}, 'audit', snapshot_digest(artifacts), 'now')


def focus(packet):
    return packet['focus']['ag01']


def test_long_navigation_does_not_displace_real_about_body():
    nav = '<nav><p>' + 'Menu item ' * 2000 + '</p></nav>'
    about = page(nav + '<h1>About</h1><p>' + DESCRIPTION + '</p>', url=SITE + '/about')
    packet = build(page('<a href="/about">About us</a><p>Home welcome.</p>'), about)
    selected = focus(packet)
    assert selected['assessable'] and selected['opening_passage'] == DESCRIPTION
    assert selected['source_kind'] == 'about_page'
    assert selected['page_ref'] == packet['pages'][1]['evidence_id']
    assert selected['opening_complete']
    for p in packet['pages']:
        assert len(p['text']) + len(p.get('focus_text', '')) <= 4000


@pytest.mark.parametrize('fragment,expected', [('team', 'Team builds payroll tools.'),
                                             ('Team', 'Uppercase Team builds invoices.'),
                                             ('t%C3%A9am', 'Accented team builds tax tools.')])
def test_exact_decoded_case_sensitive_fragment(fragment, expected):
    body = ('<section id="about"><h2>About</h2><p>Unrelated marketing slogans.</p></section>'
            '<section id="team"><h2>Team</h2><p>Team builds payroll tools.</p></section>'
            '<section id="Team"><h2>Team</h2><p>Uppercase Team builds invoices.</p></section>'
            '<section id="téam"><h2>Team</h2><p>Accented team builds tax tools.</p></section>')
    packet = build(page(f'<a href="/culture#{fragment}">About us</a><p>Home.</p>'),
                   page(body, url=SITE + '/culture'))
    assert focus(packet)['source_kind'] == 'about_section'
    assert focus(packet)['opening_passage'] == expected and focus(packet)['assessable']


def test_heading_fragment_stops_at_peer_boundary_and_keeps_child_headings():
    body = ('<h2 id="team">Our team</h2><p>Acme builds tools.</p><h3>Offering</h3>'
            '<p>Payroll for small businesses.</p><h2>Other</h2><p>Unrelated support plan.</p>')
    packet = build(page('<a href="/culture#team">About us</a>'), page(body, url=SITE + '/culture'))
    assert focus(packet)['opening_passage'] == 'Acme builds tools. Payroll for small businesses.'
    assert focus(packet)['opening_complete']


@pytest.mark.parametrize('body', ['<section id="about"><p>Wrong target.</p></section>',
                                '<section id="team"><p>First.</p></section><section id="team"><p>Second.</p></section>'])
def test_wrong_or_duplicate_fragment_never_guesses_unrelated_about(body):
    packet = build(page('<a href="/culture#team">About us</a><p>' + DESCRIPTION + '</p>'),
                   page(body, url=SITE + '/culture'))
    assert not focus(packet)['assessable'] and not focus(packet)['opening_passage']


def test_nonstandard_path_and_observed_redirect_alias_select_acquired_opening():
    home = page('<a href="/old-company">About us</a><p>Home.</p>')
    target = replace(page('<p>' + DESCRIPTION + '</p>', url=SITE + '/culture'), final_url=SITE + '/culture')
    packet = build(home, target, metadata={'url_aliases': {SITE + '/old-company': SITE + '/culture'}})
    assert focus(packet)['assessable'] and focus(packet)['opening_passage'] == DESCRIPTION
    assert SITE + '/old-company' in packet['pages'][1]['aliases']


@pytest.mark.parametrize('status,warning', [(503, 'http_503'), (None, 'fetch_timeout')])
def test_known_failed_about_never_becomes_homepage_fallback(status, warning):
    target = replace(page('', url=SITE + '/about'), status_code=status, warnings=(warning,))
    packet = build(page('<a href="/about">About us</a><p>' + DESCRIPTION + '</p>'), target)
    assert packet['about_page'] == 'known_unassessed'
    assert not focus(packet)['assessable'] and focus(packet)['source_kind'] == 'about_page'
    assert warning in ' '.join(focus(packet)['limitations'])


@pytest.mark.parametrize('reason', ['robots_disallowed', 'waiting_room', 'login_page_out_of_scope', 'max_pages_budget'])
def test_known_excluded_about_retains_actual_acquisition_reason(reason):
    packet = build(page('<a href="/about">About us</a><p>' + DESCRIPTION + '</p>'),
                   metadata={'observations': [{'requested_url': SITE + '/about', 'scope': 'excluded', 'reasons': [reason]}]})
    assert not focus(packet)['assessable'] and reason in ' '.join(focus(packet)['limitations'])


def test_sensitive_about_is_unassessed_without_exporting_secret_url():
    packet = build(page('<a href="/account?token=secret">About us</a><p>' + DESCRIPTION + '</p>'))
    assert not focus(packet)['assessable'] and focus(packet)['requested_about_url'] is None
    assert 'secret' not in str(packet)


def test_homepage_fallback_is_labeled_and_metadata_alone_cannot_make_it_assessable():
    packet = build(page('<p>' + DESCRIPTION + '</p>'))
    assert focus(packet)['assessable'] and focus(packet)['source_kind'] == 'homepage_fallback'
    packet = build(page('<h1>' + DESCRIPTION + '</h1>', '<meta name="description" content="' + DESCRIPTION + '">'))
    assert not focus(packet)['assessable'] and not focus(packet)['opening_passage']


def test_hidden_template_script_and_navigation_are_not_focused_body():
    body = ('<nav><p>Navigation slogan.</p></nav><p hidden>Hidden slogan.</p>'
            '<template><p>Template slogan.</p></template><script>Fake facts</script><p>' + DESCRIPTION + '</p>'
            '<div>' + 'Additional visible content. ' * 30 + '</div>')
    assert focus(build(page(body)))['opening_passage'] == DESCRIPTION


def test_cut_opening_is_unassessable_but_complete_opening_can_coexist_with_unrelated_partial_content():
    truncated = page('<p>' + 'Long opening ' * 200 + '</p>', url=SITE + '/about')
    assert not focus(build(truncated))['assessable']
    complete = replace(page('<p>' + DESCRIPTION + '</p><p>Software for local businesses.</p>'
                            '<div>Unrelated partial footer', url=SITE + '/about'),
                       warnings=('response_truncated_at_byte_budget',))
    assert focus(build(complete))['assessable']
    incomplete = replace(page('<p>' + DESCRIPTION + '</p>', url=SITE + '/about'),
                         warnings=('response_truncated_at_byte_budget',))
    assert not focus(build(incomplete))['assessable']


def test_focus_reference_survives_fitting_or_is_explicitly_unassessable():
    home = page('<a href="/culture">About us</a><p>' + 'Home ' * 1000 + '</p>')
    about = page('<p>' + DESCRIPTION + '</p>', url=SITE + '/culture')
    rest = [page('<p>' + 'Expendable ' * 1000 + '</p>', url=SITE + '/p/' + str(i)) for i in range(10)]
    packet = build(home, about, *rest)
    fitted = fit_packet(copy.deepcopy(packet), 7500)
    assert emitted_bytes(fitted) <= 7500
    if fitted['ready_for_assessment']:
        assert focus(fitted)['assessable']
        assert focus(fitted)['page_ref'] in {p['evidence_id'] for p in fitted['pages']}
        assert focus(fitted)['opening_passage'] == DESCRIPTION
    else:
        assert fitted['limitations']
    validate_registry(fitted)
