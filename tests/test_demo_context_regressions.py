"""Production-path regressions for misleading template and date context."""
from datetime import datetime, timezone

from test_precision_traps import page, snapshot, SITE, LIMITS
from models import make_deadline
from agent_evidence import build_evidence_packet, snapshot_digest
from analyze_authorship import is_article, assess_page
from analyze_metadata import analyze_metadata
from analyze_experience import analyze_experience
from analyze_overlays import analyze_overlays
from extract_claims import extract_claims
from assess_freshness import assess_freshness
from analyze_context_signals import analyze_context_signals


def run(check, *pages):
    return check(snapshot(*pages), make_deadline(LIMITS))


def ids(result):
    return {f['check_id'] for f in result['findings']}


def opening(body):
    a = snapshot(page(body, url=SITE + '/about'))
    packet = build_evidence_packet(a, {}, {}, {}, 'run', snapshot_digest(a), 'now')
    return packet['focus']['ag01']


def test_main_opening_survives_custom_header_and_split_slogan():
    text = ('<announcement-bar><p>Certified company</p><p>Our impact report</p></announcement-bar>'
            '<main><p>RISE</p><p>EACH</p><p>DAY</p><h2>Our story</h2>'
            '<p>Acme Bakery makes bread and pastries for customers in Leeds.</p></main>')
    focus = opening(text)
    assert focus['assessable'] and focus['opening_complete']
    assert 'Acme Bakery' in focus['opening_passage']
    assert 'Certified' not in focus['opening_passage']
    assert focus['opening_passage'].startswith('RISE EACH DAY')


def test_genuinely_vague_short_body_is_preserved_for_agent_assessment():
    focus = opening('<main><p>Welcome here.</p><p>Dream bigger.</p></main>')
    assert focus['assessable'] and focus['opening_passage'] == 'Welcome here. Dream bigger.'


def test_inline_stylesheet_hidden_controls_do_not_hide_active_controls():
    p = page('<main><h1>Shop</h1><a href="/real"></a></main>'
             '<div class="notice" role="dialog" aria-modal="true"><a href="/cart"></a></div>'
             '<style>.notice {display:none}</style>')
    assert p.features['unnamed_control_count'] == 1
    assert p.features['unnamed_controls'][0]['href'] == '/real'
    assert 'overlay' not in ids(run(analyze_overlays, p))
    # A conditional/active override makes stylesheet visibility uncertain.
    active = page('<div class="notice active"><a href="/cart"></a></div>'
                  '<style>.notice {display:none}.notice.active {display:block}</style>')
    assert active.features['unnamed_control_count'] == 1


def test_main_outline_excludes_widget_heading_but_keeps_real_skips():
    p = page('<main><h1>Bakery</h1><h2>Our breads</h2></main><div role="dialog"><h4>Account</h4></div>')
    assert 'heading-hierarchy' not in ids(run(analyze_metadata, p))
    bad = page('<main><h1>Bakery</h1><h3>Our breads</h3><h4>Details</h4></main>')
    assert 'heading-hierarchy' in ids(run(analyze_metadata, bad))


def test_modal_role_without_open_state_is_recorded_without_arrival_claim():
    p = page('<main><h1>Shop</h1></main><div role="dialog" aria-modal="true"><p>Your cart</p></div>')
    assert p.features['modal_dialogs']
    result = run(analyze_overlays, p)
    assert 'overlay' not in ids(result)
    assert result['metrics']['overlay_visibility_unknown_pages'] == 1
    opened = page('<dialog open aria-modal="true"><p>Join us</p></dialog>')
    assert 'overlay' in ids(run(analyze_overlays, opened))


def test_press_index_and_navigation_are_not_article_or_byline():
    nav = '<nav><p>Shop by Shop Body Care Soap</p>' + '<a href="/shop">Products </a>' * 350 + '</nav>'
    index = page(nav + '<main><h1>Press</h1><p>Coverage in the media.</p></main>', url=SITE + '/pages/press')
    assert index.page_type == 'listing' and not is_article(index)
    article = page(nav + '<main><h1>Our news</h1><p>' + 'Reporting on bread. ' * 150 + '</p></main>',
                   url=SITE + '/press/new-bakery')
    assert is_article(article) and assess_page(article)[0]
    byline = page('<main><p>By Jane Doe</p><p>' + 'Reporting on bread. ' * 150 + '</p></main>',
                  url=SITE + '/press/new-bakery')
    assert not assess_page(byline)[0]


def test_publication_date_is_not_stale_offer_and_old_timestamp_is_review_only():
    year = datetime.now(timezone.utc).year - 7
    book = page(f'<main><p>Published: February 22, {year}.</p><p>Offer valid until March 1, {year}.</p></main>',
                url=SITE + '/products/book')
    a = snapshot(book)
    claims = extract_claims(a, make_deadline(LIMITS))
    dates = {c['value']: c['category'] for c in claims['data']['claims'] if c['type'] == 'date'}
    assert dates[f'February 22, {year}'] == 'historical'
    assert dates[f'March 1, {year}'] == 'commercial'
    result = assess_freshness({'data': {'facts': []}}, a, make_deadline(LIMITS), claims)
    finding, = [f for f in result['findings'] if f['check_id'].startswith('stale-dates')]
    assert finding['finding_type'] == 'proactive_improvement' and finding['severity'] == 'low'
    assert 'not establish' in finding['root_cause']


def test_descriptive_h2_orients_page_even_without_h1():
    p = page('<main><h2>About our bakery</h2><p>' + 'We bake fresh bread every morning. ' * 70 + '</p></main>',
             url=SITE + '/about')
    assert 'h1' in ids(run(analyze_experience, p))
    assert 'page-orientation' not in ids(run(analyze_experience, p))


def test_optional_location_markup_is_advice_even_with_address_and_map():
    p = page('<address>12 High Street, Leeds</address><a href="https://maps.google.com/maps?q=leeds">Map</a>')
    f, = [f for f in run(analyze_context_signals, p)['findings'] if f['check_id'] == 'location-markup-missing']
    assert f['finding_type'] == 'proactive_improvement' and f['severity'] == 'low'
