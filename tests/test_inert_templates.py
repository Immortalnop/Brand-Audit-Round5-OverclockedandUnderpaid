"""Template fragments must not supply active-page evidence or suppress it.

Use the acquisition parser and native checks, with real defects adjacent to the
inactive markup. No JavaScript execution, page re-fetch or report editing.
"""
import pytest

from test_precision_traps import page, snapshot, features, SITE, LIMITS
from html_features import Document
from models import make_deadline
from analyze_accessibility import analyze_accessibility
from analyze_metadata import analyze_metadata
from agent_evidence import build_evidence_packet, snapshot_digest


LIVE = ('<main><h1>Acme Bakery</h1><p>Acme Bakery makes fresh bread for people in Leeds.</p>'
        '<h2>Our bread</h2><h3>Ingredients</h3>'
        '<a class="live" href="/help">Help</a><button class="live">Order bread</button>'
        '<form><label for="email">Email</label><input id="email" type="email">'
        '<button>Contact us</button></form></main>')
HEAD = '<title>Acme Bakery</title><meta name="description" content="Fresh bread in Leeds.">'


@pytest.mark.parametrize('fragment', [
    '<button></button>', '<button>Buy now</button>', '<a href="/cart"></a>',
    '<a href="/cart">Cart</a>', '<input type="button">', '<input type="image" src="/buy.png">',
    '<input id="password" type="password">', '<select><option>Pick</option></select>',
    '<textarea></textarea>', '<label for="email">Inactive label</label>',
])
def test_inactive_controls_cannot_create_accessibility_or_login_evidence(fragment):
    before = page(LIVE, HEAD)
    after = page(LIVE + '<template>' + fragment + '</template>', HEAD)
    assert after.features['controls'] == before.features['controls']
    assert after.features['unnamed_control_count'] == before.features['unnamed_control_count'] == 0
    assert after.features['form_fields'] == before.features['form_fields']
    assert after.features['password_inputs'] == before.features['password_inputs'] == 0
    assert after.features['unlabeled_field_count'] == before.features['unlabeled_field_count'] == 0


@pytest.mark.parametrize('fragment', [
    '<main><h1>Inactive main</h1><p>Fake opening.</p></main>',
    '<nav><a href="/about">About us</a></nav>',
    '<h1>Inactive heading</h1><h4>Jump</h4>',
    '<form action="/login"><input type="password"><input type="email"></form>',
    '<form action="/search"><input type="search" name="q"></form>',
    '<div class="wishlist" data-reactroot></div>',
    '<img src="/inactive.png"><video src="/inactive.mp4"><track kind="captions"></video>',
    '<canvas><img src="/fallback.png" alt="Fact"></canvas><svg><text>Fake fact</text></svg>',
    '<dialog open aria-modal="true"><button></button></dialog>',
    '<div class="cookie-banner overlay-active" style="position:fixed;inset:0"></div>',
    '<ol><li>One</li><li>Two</li><li>Three</li></ol><table><tr><th>Fake</th></tr></table>',
    '<meta name="description" content="Fake description"><link rel="canonical" href="/fake">',
    '<link rel="stylesheet" href="/fake.css"><link rel="alternate" hreflang="fr" href="/fr">',
    '<script src="https://assets.example/react.js"></script>',
    '<script type="application/ld+json">{"@type":"Product","name":"Fake"}</script>',
    '<script type="application/ld+json">{broken}</script>',
    '<script id="__NEXT_DATA__" type="application/json">{"text":"Fake serialized page content"}</script>',
    '<div itemscope itemtype="https://schema.org/Product"><span itemprop="telephone">123</span></div>',
    '<style>.live {display:none}</style>',
])
def test_template_insertion_preserves_all_live_acquisition_observations(fragment):
    before = page(LIVE, HEAD)
    after = page('<template>' + fragment + '</template>' + LIVE, HEAD)
    # The response is larger; every extracted live-page observation is identical.
    actual = {k: v for k, v in after.features.items() if k != 'html_bytes'}
    expected = {k: v for k, v in before.features.items() if k != 'html_bytes'}
    assert actual == expected
    for attr in ('title', 'meta_description', 'canonical_url', 'headings', 'visible_text',
                 'internal_links', 'external_links', 'jsonld_blocks', 'page_type', 'warnings'):
        assert getattr(after, attr) == getattr(before, attr), attr


def test_inactive_label_does_not_name_a_real_unlabelled_field():
    p = page('<template><label for="live">Unused</label></template>'
             '<main><input id="live"></main>')
    assert p.features['unlabeled_field_count'] == 1


@pytest.mark.parametrize('inactive_css,live_css,expected', [
    ('.control {display:none}', '', 1),
    ('.control {display:block}', '.control {display:none}', 0),
])
def test_template_styles_neither_hide_live_controls_nor_override_live_rules(inactive_css, live_css, expected):
    p = page('<template><style>' + inactive_css + '</style></template>'
             '<style>' + live_css + '</style><main><button class="control"></button></main>')
    assert p.features['unnamed_control_count'] == expected


def test_template_closing_tags_do_not_close_live_ancestors_or_leave_internal_frames():
    p = page('<main><button>Buy <template></button></main><div><template>'
             '<button></button></template></template>bread</button>'
             '<h1>Acme Bakery</h1><p>We bake bread in Leeds.</p></main>')
    assert p.features['controls'] == 1
    assert p.features['unnamed_control_count'] == 0
    assert p.features['buttons'] == ('Buy bread',)
    assert p.features['main_region_observed'] and p.features['h1_count'] == 1
    assert p.features['body_opening']['passage'] == 'We bake bread in Leeds.'


@pytest.mark.parametrize('tag', ['script', 'style', 'textarea', 'title', 'xmp', 'iframe', 'noembed', 'noframes'])
@pytest.mark.parametrize('text', ['<template>', '</template>', '<template></template>'])
def test_template_strings_inside_raw_text_do_not_change_template_depth(tag, text):
    p = page('<template><' + tag + '>' + text + '</' + tag + '></template>' + LIVE, HEAD)
    assert p.features['h1_count'] == 1 and p.features['controls'] == 3
    assert p.features['body_opening']['passage'].startswith('Acme Bakery makes fresh bread')


def test_comments_and_escaped_template_text_do_not_hide_live_controls():
    f = features('<!-- <template> --><main><p>&lt;template&gt;</p><button></button></main>')
    assert f['controls'] == f['unnamed_control_count'] == 1
    assert '<template>' in f['body_text']


def test_self_closing_template_syntax_does_not_activate_its_contents():
    # In HTML, the slash does not close a non-void template element.
    p = page('<template/><button></button></template>' + LIVE)
    assert p.features['controls'] == 3 and p.features['unnamed_control_count'] == 0


def test_unclosed_template_cannot_promote_its_tail_to_live_evidence():
    p = page(LIVE + '<template><button></button><h1>Fake</h1><img src="/fake.png">')
    assert p.features['controls'] == 3 and p.features['unnamed_control_count'] == 0
    assert p.features['h1_count'] == 1 and p.features['images'] == 0


def test_template_at_fragment_boundary_does_not_reset_ag01_opening():
    p = page('<p>Acme Bakery bakes bread for people in Leeds.</p>'
             '<template><main><p>Fake company offering.</p></main></template>', url=SITE + '/about')
    artifacts = snapshot(p)
    packet = build_evidence_packet(artifacts, {}, {}, {}, 'audit', snapshot_digest(artifacts), 'now')
    assert packet['focus']['ag01']['assessable']
    assert packet['focus']['ag01']['opening_passage'] == 'Acme Bakery bakes bread for people in Leeds.'
    assert not p.features['main_region_observed']


def test_real_accessibility_and_outline_defects_remain_in_native_checks():
    p = page('<main><h1>Shop</h1><h3>Our bread</h3><h4>Ingredients</h4><button></button><input id="live"></main>'
             '<template><h2>Inactive intervening level</h2><button>Unused</button></template>')
    accessibility = analyze_accessibility(snapshot(p), make_deadline(LIMITS))
    check_ids = {f['check_id'] for f in accessibility['findings']}
    assert 'control-name-missing' in check_ids
    assert 'form-label-missing' in check_ids
    metadata = analyze_metadata(snapshot(p), make_deadline(LIMITS))
    assert 'heading-hierarchy' in {f['check_id'] for f in metadata['findings']}


def test_inactive_accessibility_and_outline_defects_do_not_reach_native_checks():
    p = page(LIVE + '<template><h6>Wrong level</h6><button></button><input></template>')
    accessibility = analyze_accessibility(snapshot(p), make_deadline(LIMITS))
    assert not {'control-name-missing', 'form-label-missing'} & {f['check_id'] for f in accessibility['findings']}
    metadata = analyze_metadata(snapshot(p), make_deadline(LIMITS))
    assert 'heading-hierarchy' not in {f['check_id'] for f in metadata['findings']}


@pytest.mark.parametrize('markup', ['<template>' * 300, '<template>' + '<button></button>' * 100001])
def test_ignored_template_markup_still_respects_structural_budgets(markup):
    doc = Document()
    with pytest.raises(ValueError, match='budget'):
        doc.feed(markup)


def test_template_state_survives_chunked_feed():
    doc = Document()
    for chunk in ('<temp', 'late><button>Unused</button><template>', '<button></button>',
                  '</template></template><main><button></button></main>'):
        doc.feed(chunk)
    doc.close()
    assert doc.features()['controls'] == doc.features()['unnamed_control_count'] == 1


def test_template_css_scope_survives_chunked_feed():
    doc = Document()
    for chunk in ('<template>', '<style>.live {display:none}</style>', '</template>',
                  '<main><button class="live"></button></main>'):
        doc.feed(chunk)
    doc.close()
    assert doc.features()['controls'] == doc.features()['unnamed_control_count'] == 1


def test_native_pipeline_ignores_template_links_assets_and_defects_but_retains_real_ones():
    from test_round5_release import _site, _audit
    site = _site(h1_on_services=True)
    inactive = ('<template><main><h6>Unused</h6><button></button><input type="password">'
                '<a href="/inert-only">Inactive destination</a><img src="/inert-image.png">'
                '<meta name="description" content="Unused"><script type="application/ld+json">'
                '{broken}</script></main></template>')
    site['pages'] = {path: html.replace('</body>', inactive + '</body>')
                     for path, html in site['pages'].items()}
    site['pages']['/'] = site['pages']['/'].replace('</main>', '<button></button><input id="real"></main>')
    base, stop, seen, report, packet = _audit(site)
    try:
        assert report['execution_status'] == 'completed'
        assert report['coverage']['pages_analyzed'] == 3
        assert not any('/inert-' in path for _, path in seen)
        assert packet['focus']['ag01']['opening_passage'].startswith('Acme is a bicycle repair shop')
        findings = {f['check_id']: f for f in report['findings']}
        for rule in ('control-name-missing', 'form-label-missing'):
            assert findings[rule]['affected_pages'] == [base + '/']
        assert not {'heading-hierarchy', 'malformed-jsonld', 'alt-text', 'image-weight',
                    'render-gap', 'render-gap-unconfirmed'} & findings.keys()
    finally:
        stop()
