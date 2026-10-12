"""Engine regression tests: a positive and a negative case for each correctness
fix in the scoring, merging, acquisition and reporting path. Offline, against the
local fixture server or synthetic page artifacts."""
import ast
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'skills/audit-orchestrator/scripts', 'skills/crawl-render-audit/scripts',
            'skills/freshness-corroboration/scripts', 'skills/engagement-audit/scripts',
            'skills/entity-corroboration-agent/scripts', 'tests'):
    sys.path.insert(0, str(ROOT / rel))

from access_guard import classify_access
from url_keys import template_key, visit_key, strip_tracking
from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline, make_finding
from transport import Response
from acquire_site import _extract_page, acquire_site
from fixtures_server import start_server
from check_catalog import CATALOG, meta_for
from scoring import ScoringContext, apply_scoring, priority_consistent, sample_strength
from merge_findings import merge_findings
from models import skill_result
from dates import extract_visible_dates, copyright_years
from schema_rules import invalid_values, price_numbers

LIMITS = Limits()
CF_BODY = ('<!DOCTYPE html><html><head><title>Just a moment...</title></head><body>'
           '<noscript>Enable JavaScript and cookies to continue</noscript>'
           '<script>window._cf_chl_opt={cZone:"x"}</script></body></html>')
PYPI_BODY = ('<html><head><title>Client Challenge</title></head><body>JavaScript is disabled in your browser. '
             'Please enable JavaScript to proceed.</body></html>')


def page(html, url='https://shop.example/', headers=None, status=200):
    r = Response(status, {'Content-Type': 'text/html', **(headers or {})}, html.encode(), url)
    r.network_duration_ms = 50
    return _extract_page(url, r, 50, LIMITS)


def snapshot(pages, robots=None, meta=None, sitemap=None):
    return AuditArtifacts('https://shop.example/', 'https://shop.example', tuple(pages),
                          freeze_value(robots or {'status': 'ok', 'ai_crawler_directives': {}}),
                          freeze_value({'present': False, 'status': 'absent'}),
                          freeze_value(sitemap or {'status': 'ok', 'urls': [], 'lastmod': {}}),
                          freeze_value(meta or {'coverage': {}}), ())


# ----------------------------------------------------------------
def test_challenge_pages_are_classified():
    assert classify_access(403, {'cf-mitigated': 'challenge'}, CF_BODY, 40)['kind'] == 'challenge'
    assert classify_access(200, {}, PYPI_BODY, 90)['vendor'] == 'generic'
    assert classify_access(429, {'Retry-After': '30'}, '', 0)['kind'] == 'rate_limited'


def test_article_mentioning_cloudflare_is_not_a_challenge():
    body = '<html><title>Our CDN</title><body>' + ('We moved to Cloudflare and challenges.cloudflare.com '
                                                   'docs helped. ' * 60) + '</body></html>'
    assert classify_access(200, {'server': 'cloudflare'}, body, 5000)['kind'] == 'ok'


def test_challenge_pages_excluded_from_content_checks():
    from analyze_experience import analyze_experience
    from build_site_graph import build_site_graph
    pages = [page(PYPI_BODY, f'https://shop.example/p/{i}/') for i in range(5)]
    assert all('bot_challenge' in p.warnings for p in pages)
    a = snapshot(pages)
    findings = analyze_experience(a, make_deadline(LIMITS))['findings']
    assert not any(set(f['affected_pages']) & {p.url for p in pages} for f in findings)
    graph = build_site_graph(a, make_deadline(LIMITS))['data']
    assert graph['dead_ends'] == [] and graph['nodes'] == {}


# ----------------------------------------------------------------
def test_robots_403_is_permission_unknown_not_permission_granted():
    """RFC 9309 2.3.1.3 would read a 4xx robots.txt as "no restrictions". This
    audit is deliberately stricter: a 401/403 is the server refusing this client,
    not a statement that no robots file exists, so permission is unknown and only
    the one documented homepage diagnostic is fetched (acquire_site ROBOTS_POLICY)."""
    url, stop = start_server(routes={'/robots.txt': (403, 'Forbidden', {'Content-Type': 'text/plain'})})
    try:
        a = acquire_site(url + '/', make_deadline(LIMITS), LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert a.robots_data['status'] == 'unavailable_4xx'
    assert a.robots_data['conservative_fail_closed'] is True
    assert a.robots_data['allowed_general'] is False
    assert [p.url for p in a.pages] == [url + '/']
    assert a.robots_data['homepage_diagnostic'] is True


def test_robots_404_is_the_only_4xx_that_grants_permission():
    url, stop = start_server(robots_mode='absent')
    try:
        a = acquire_site(url + '/', make_deadline(LIMITS), LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert a.robots_data['status'] == 'absent' and not a.robots_data['conservative_fail_closed']
    assert a.robots_data['homepage_diagnostic'] is False
    assert len(a.pages) > 1


def test_challenged_robots_fetches_homepage_only_and_reports_wall():
    from analyze_access import analyze_access
    routes = {'/robots.txt': (403, CF_BODY, {'Content-Type': 'text/html', 'cf-mitigated': 'challenge'}),
              '/': (403, CF_BODY, {'Content-Type': 'text/html', 'cf-mitigated': 'challenge'})}
    url, stop = start_server(routes=routes)
    try:
        a = acquire_site(url + '/', make_deadline(LIMITS), LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert a.robots_data['status'] == 'challenged'
    assert [p.url for p in a.pages] == [url + '/']
    ids = {f['check_id'] for f in analyze_access(a, make_deadline(LIMITS))['findings']}
    assert {'bot-challenge-robots', 'bot-challenge-sitewide'} <= ids


def test_robots_5xx_fails_closed():
    url, stop = start_server(robots_mode='error')
    try:
        a = acquire_site(url + '/', make_deadline(LIMITS), LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert a.robots_data['conservative_fail_closed'] and a.pages == ()


def test_rate_challenge_after_some_pages():
    from analyze_access import analyze_access
    pages = [page('<html><h1>Hi</h1>' + 'text ' * 200, f'https://shop.example/a{i}') for i in range(3)]
    pages += [page(PYPI_BODY, 'https://shop.example/b')]
    ids = {f['check_id'] for f in analyze_access(snapshot(pages), make_deadline(LIMITS))['findings']}
    assert ids == {'bot-challenge-rate'}


def test_no_wall_no_finding():
    from analyze_access import analyze_access
    pages = [page('<html><h1>Hi</h1>' + 'text ' * 200)]
    assert analyze_access(snapshot(pages), make_deadline(LIMITS))['findings'] == []


# ----------------------------------------------------------------
def test_finalize_merges_agent_findings_idempotently(tmp_path):
    import run_audit
    from finalize_report import finalize
    url, stop = start_server(clean=True)
    try:
        report = run_audit.run_audit(url + '/', LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert report['agent_stage']['status'] == 'not_supplied'
    assert report['agent_stage']['brief']['brand_name'] == 'Northwind Analytics'
    ag = tmp_path / 'ag.json'
    # An AG-03 contradiction has to cite the independent source it was seen in
    # (ingest_agent_findings._AG_RULES), or it is capped at suspected.
    ag.write_text(json.dumps({'site': url + '/', 'search': {'available': True, 'queries_run': 3},
                              'checks': {'AG-03': 'fail'},
                              'findings': [{'check': 'AG-03', 'status': 'confirmed', 'severity': 'high',
                                            'evidence': [{'description': 'Two directories list it as a freight '
                                                                         'broker; the site says analytics.',
                                                          'urls': ['https://dir.example/northwind']}]}]}))
    once = finalize(report, str(ag))
    twice = finalize(once, str(ag))
    ids = lambda r: [(f['id'], f['check_id'], f['severity']) for f in r['findings']]
    assert ids(once) == ids(twice)
    assert once['agent_stage']['status'] == 'ingested'
    assert any(f['check_id'] == 'independent-contradiction' and f['severity'] == 'high' for f in once['findings'])
    empty = tmp_path / 'empty.json'
    empty.write_text('[]')
    # A bare empty array cannot claim the checks passed, so it is empty_unspecified.
    assert finalize(report, str(empty))['agent_stage']['status'] == 'empty_unspecified'
    assessed = tmp_path / 'assessed.json'
    assessed.write_text(json.dumps({'findings': [], 'checks': {c: 'pass' for c in
                                                               ('AG-01', 'AG-02', 'AG-03', 'AG-04', 'AG-05', 'AG-06')}}))
    assert finalize(report, str(assessed))['agent_stage']['status'] == 'assessed_no_findings'
    assert finalize(report, str(tmp_path / 'missing.json'))['agent_stage']['status'] == 'not_supplied'


# ----------------------------------------------------------------
def _f(check, severity, pages, confidence=0.9, status='confirmed', effort='low'):
    f = make_finding(category='ai_discoverability', finding_type='defect', severity=severity, status=status,
                     confidence=confidence, title=check, root_cause=check,
                     evidence=[{'type': 'x', 'description': check, 'urls': pages}],
                     suggested_action={'summary': 's', 'steps': ['a'], 'priority': 'low', 'effort': effort,
                                       'expected_benefit': 'b', 'verification': 'v'},
                     provenance={'rule_id': check}, affected_pages=pages)
    return f


def test_large_site_does_not_lower_severity_and_absence_uses_sample_strength():
    ctx = ScoringContext(40, 8, {}, 'https://shop.example/')
    f = apply_scoring(_f('no-jsonld', 'high', [f'https://shop.example/{i}' for i in range(40)], 0.85), ctx)
    assert f['severity'] == 'high' and f['confidence'] == 0.85
    thin = apply_scoring(_f('no-jsonld', 'high', ['https://shop.example/a'], 0.85), ScoringContext(2, 1, {}, None))
    assert thin['confidence'] < 0.5 and thin['severity_rationale']['sample_strength'] == sample_strength(2, 1)


def test_single_non_key_page_steps_down_but_access_checks_do_not():
    ctx = ScoringContext(20, 5, {'https://shop.example/x': 'other'}, 'https://shop.example/')
    f = apply_scoring(_f('missing-title', 'medium', ['https://shop.example/x']), ctx)
    assert f['severity'] == 'low'
    g = apply_scoring(_f('search-crawler-blocked', 'critical', ['https://shop.example/x']), ctx)
    assert g['severity'] == 'critical'


def test_scoring_is_idempotent_and_priority_follows_severity():
    ctx = ScoringContext(20, 5, {'https://shop.example/x': 'other'}, 'https://shop.example/')
    f = apply_scoring(_f('missing-title', 'medium', ['https://shop.example/x']), ctx)
    once = (f['severity'], f['confidence'], f['priority_score'])
    apply_scoring(f, ctx)
    assert (f['severity'], f['confidence'], f['priority_score']) == once
    assert priority_consistent(f) and f['suggested_action']['priority'] == f['severity']


# ----------------------------------------------------------------
def test_identity_falls_back_to_first_party_naming():
    from resolve_entity_identity import resolve_entity_identity
    pages = [page(f'<html><head><title>{t} | Acme Tools</title></head><body><h1>{t}</h1>'
                  '<footer>© 2025 Acme Tools Pvt Ltd</footer></body></html>', f'https://shop.example/{t}')
             for t in ('Hammers', 'Drills', 'Saws')]
    data = resolve_entity_identity(snapshot(pages), make_deadline(LIMITS))['data']
    assert data['canonical_name'] == 'Acme Tools'
    assert 0.7 <= data['confidence'] < 0.85 and data['declared'] is False


# ----------------------------------------------------------------
def test_template_keys_and_visit_keys():
    assert template_key('https://x/project/requests/2.31.0/') == template_key('https://x/project/requests/0.1/')
    assert template_key('https://x/blog/post-a') == template_key('https://x/blog/post-b')
    assert template_key('https://x/blog') != template_key('https://x/pricing')
    assert visit_key('https://X/a/') == visit_key('https://x/a?utm_source=z')
    assert strip_tracking('https://x/a?id=3&utm_medium=m') == 'https://x/a?id=3'


def test_sample_is_template_diverse():
    items = ''.join(f'<a href="/item/{i}">Item {i}</a>' for i in range(60))
    home = ('<html><head><title>Shop</title></head><body><nav><a href="/about">About</a>'
            '<a href="/pricing">Pricing</a><a href="/faq">FAQ</a></nav>' + items + '</body></html>')
    routes = {'/': (200, home, None)}
    for path in ('/about', '/pricing', '/faq'):
        routes[path] = (200, f'<html><title>{path}</title><h1>{path}</h1></html>', None)
    for i in range(60):
        routes[f'/item/{i}'] = (200, f'<html><title>Item {i}</title><h1>Item {i}</h1></html>', None)
    url, stop = start_server(routes=routes)
    try:
        a = acquire_site(url + '/', make_deadline(LIMITS), LIMITS, allow_private_targets=True)
    finally:
        stop()
    paths = [p.url[len(url):] for p in a.pages]
    assert {'/about', '/pricing', '/faq'} <= set(paths)
    assert sum(p.startswith('/item/') for p in paths) <= LIMITS.MAX_PER_TEMPLATE


# ----------------------------------------------------------------
def test_dates_classified_by_nearest_context():
    ds = extract_visible_dates('Offer last updated 2019-03-01. Promotion valid through 2020-06-15. Founded March 1998.')
    ctx = {d['raw']: d['context'] for d in ds}
    assert ctx['2019-03-01'] == 'update_claim' and ctx['2020-06-15'] == 'expiry' and ctx['March 1998'] == 'historical'
    assert copyright_years('© 2019-2023 Acme') == [2023]
    assert not extract_visible_dates('Meeting on 04/05/2024')  # ambiguous DD/MM vs MM/DD is skipped


def test_old_reference_dates_are_not_findings():
    from assess_freshness import assess_freshness
    p = page('<html><h1>Classifiers</h1><p>Added 2006-09-30. ' + 'Development Status :: 5 ' * 50 + '</p></html>',
             'https://shop.example/classifiers/')
    res = assess_freshness({}, snapshot([p]), make_deadline(LIMITS))
    assert res['findings'] == []


def test_contradictions_expiry_and_copyright():
    from assess_freshness import assess_freshness
    today = date.today()
    old = (today - timedelta(days=900)).isoformat()
    p1 = page('<html><script type="application/ld+json">{"@type":"Article","headline":"H","datePublished":"2024-05-01",'
              '"dateModified":"2023-01-01"}</script><h1>H</h1><p>' + 'word ' * 200 + '</p>'
              '<footer>© 2019 Shop</footer></html>', 'https://shop.example/blog/h')
    p2 = page(f'<html><h1>Pricing</h1><p>Prices last updated {old}. Sale ends 2021-01-31.</p></html>',
              'https://shop.example/pricing')
    ids = {f['check_id'] for f in assess_freshness({}, snapshot([p1, p2]), make_deadline(LIMITS))['findings']}
    assert {'date-contradiction', 'expired-offer', 'stale-update-claim', 'stale-copyright'} <= ids


# ----------------------------------------------------------------
def test_pdf_only_prices_detected_and_text_prices_not():
    from analyze_nontext_facts import analyze_nontext_facts
    meta = {'coverage': {}, 'asset_links': [{'url': 'https://shop.example/price-list.pdf', 'anchor': 'Price list',
                                              'linked_from': 'https://shop.example/pricing', 'fact_keyword': True}],
            'asset_probes': []}
    bare = page('<html><h1>Pricing</h1><a href="/price-list.pdf">Price list</a></html>', 'https://shop.example/pricing')
    ids = {f['check_id'] for f in analyze_nontext_facts(snapshot([bare], meta=meta), make_deadline(LIMITS))['findings']}
    assert 'facts-in-pdf' in ids
    full = page('<html><h1>Pricing</h1><p>Basic plan Rs. 499 per month.</p><a href="/price-list.pdf">Price list</a></html>',
                'https://shop.example/pricing')
    assert analyze_nontext_facts(snapshot([full], meta=meta), make_deadline(LIMITS))['findings'] == []


def test_menu_image_detected():
    from analyze_nontext_facts import analyze_nontext_facts
    p = page('<html><h1>Menu</h1><img src="/img/menu-2026.jpg" width="1200"></html>', 'https://shop.example/menu')
    ids = {f['check_id'] for f in analyze_nontext_facts(snapshot([p]), make_deadline(LIMITS))['findings']}
    assert ids == {'facts-in-images'}


# ----------------------------------------------------------------
def test_structured_data_completeness_values_and_consistency():
    from validate_structured_data import validate_structured_data
    p = page('<html><script type="application/ld+json">{"@type":"Product","name":"Mug","offers":{"@type":"Offer",'
             '"price":"499","priceCurrency":"Rupees"}}</script><h1>Mug</h1><p>Now only Rs. 599.</p></html>',
             'https://shop.example/products/mug')
    ids = {f['check_id'] for f in validate_structured_data(snapshot([p]), make_deadline(LIMITS))['findings']}
    assert {'schema-invalid-value', 'schema-visible-mismatch'} <= ids
    q = page('<html><script type="application/ld+json">{"@type":"Offer","priceCurrency":"INR"}</script></html>',
             'https://shop.example/products/x')
    ids = {f['check_id'] for f in validate_structured_data(snapshot([q]), make_deadline(LIMITS))['findings']}
    assert 'schema-missing-required' in ids
    assert ('price', '1,299', 'a plain number such as 1299.00 (no currency symbol or thousands separator)') in invalid_values({'price': '1,299'})
    assert price_numbers('Only ₹1,299.00 today') == {'1299'}


def test_no_jsonld_lists_types_and_drafts_snippets():
    from analyze_machine_readability import analyze_machine_readability
    pages = [page('<html><title>Shop</title><h1>Shop</h1></html>', 'https://shop.example/'),
             page('<html><title>Mug</title><h1>Mug</h1></html>', 'https://shop.example/products/mug')]
    f = [x for x in analyze_machine_readability(snapshot(pages), make_deadline(LIMITS))['findings']
         if x['check_id'] == 'no-jsonld'][0]
    assert any('Product' in s for s in f['suggested_action']['steps'])
    snippets = f['suggested_action']['proposed_snippets']
    assert any('"Organization"' in s for s in snippets.values()) and any('"Product"' in s for s in snippets.values())


# ----------------------------------------------------------------
def test_crawler_blocks_weighted_by_role():
    from check_ai_crawler_access import check_ai_crawler_access
    robots = {'status': 'ok', 'ai_crawler_directives': {'GPTBot': 'disallow', 'Bingbot': 'allow'},
              'ai_crawler_paths': {'GPTBot': ['https://shop.example/'], 'ChatGPT-User': ['https://shop.example/blog/'],
                                   'Bingbot': ['https://shop.example/pricing']}}
    res = check_ai_crawler_access(snapshot([], robots=robots), make_deadline(LIMITS))
    sev = {f['check_id']: f['severity'] for f in res['findings']}
    assert sev == {'search-crawler-blocked': 'critical', 'user-fetch-blocked': 'high', 'training-crawler-blocked': 'low'}


# ----------------------------------------------------------------
def test_catalog_has_real_mechanisms_and_metadata():
    mechanisms = [v['mechanism'] for v in CATALOG.values()]
    assert not [k for k, v in CATALOG.items() if v['mechanism'].startswith('The observed condition')]
    assert len(set(mechanisms)) == len(mechanisms)
    for k in CATALOG:
        m = meta_for(k)
        assert m['gate'] in ('access', 'readability', 'extractability', 'trust', 'engagement')
        assert m['tier'] in ('core', 'hygiene')


def test_steps_render_as_readable_sentence():
    f = make_finding(category='engagement', finding_type='defect', severity='low', status='confirmed', confidence=.5,
                     title='t', root_cause='r', evidence=[], provenance={'rule_id': 'not-catalogued'},
                     suggested_action={'summary': 's', 'steps': ['Identify page types', 'Add markup'],
                                       'priority': 'low'})
    assert f['suggested_action']['implementation_detail'] == '1) Identify page types; 2) Add markup.'


# ----------------------------------------------------------------
def test_root_cause_group_merge_across_categories():
    urls = ['https://shop.example/a', 'https://shop.example/b']
    a = _f('no-headings', 'low', urls)
    b = _f('h1', 'low', urls)
    b['category'] = 'engagement'
    c = _f('no-headings', 'low', ['https://shop.example/z'])
    c['root_cause'] = 'different'
    merged = merge_findings([skill_result('s', findings=[a, b, c])])
    combined = [m for m in merged if len(m.get('check_ids', [])) == 2]
    assert len(merged) == 2 and combined and set(combined[0]['check_ids']) == {'no-headings', 'h1'}


def test_repeated_evidence_is_grouped():
    from analyze_metadata import analyze_metadata
    pages = [page('<html lang="en"><title>Same title here ok</title><h1>x</h1></html>', f'https://shop.example/{i}')
             for i in range(6)]
    f = [x for x in analyze_metadata(snapshot(pages), make_deadline(LIMITS))['findings']
         if x['check_id'] == 'missing-description'][0]
    assert len(f['evidence']) == 1 and f['evidence'][0]['description'].startswith('6 page(s)')


# ----------------------------------------------------------------
def test_report_structure():
    import run_audit
    from render_report import render_markdown
    url, stop = start_server(sitemap_mode='broken_nav')
    try:
        r = run_audit.run_audit(url + '/', LIMITS, allow_private_targets=True)
    finally:
        stop()
    assert all(f['tier'] == 'core' for f in r['findings'])
    assert all(h['id'].startswith('H-') and h['tier'] == 'hygiene' for h in r['hygiene_findings'])
    assert not {h['check_id'] for h in r['hygiene_findings']} & {f['check_id'] for f in r['findings']}
    assert r['action_plan'][0]['finding_ids'][0] == r['top_actions'][0]['finding_id']
    titles = {f['title'] for f in r['findings']}
    assert not [x for x in r['recommendations'] if x['title'] in titles]
    assert all(priority_consistent(f) for f in r['findings'])
    md = render_markdown(r)
    assert '## Top actions' in md and '**Why it matters.**' in md


# ----------------------------------------------------------------
def test_hydration_payload_gap_detected_without_browser():
    from analyze_rendering import analyze_rendering
    strings = [f'Product number {i} ships free across the whole country today' for i in range(8)]
    html = ('<html><title>Shop</title><body><div id="__next"></div><script id="__NEXT_DATA__" type="application/json">'
            + json.dumps({'props': {'items': strings}}) + '</script></body></html>')
    res = analyze_rendering(snapshot([page(html, 'https://shop.example/products')]), make_deadline(LIMITS), LIMITS, {})
    f = [x for x in res['findings'] if x['check_id'] == 'render-gap'][0]
    assert f['status'] == 'suspected' and f['confidence'] == 0.8 and 'exist only in the JS payload' in f['evidence_text']


def test_thin_page_without_spa_signal_is_not_a_defect():
    from analyze_rendering import analyze_rendering
    res = analyze_rendering(snapshot([page('<html><title>Hi</title><h1>Contact</h1><p>Call us.</p></html>',
                                           'https://shop.example/x')]), make_deadline(LIMITS), LIMITS, {})
    assert not [f for f in res['findings'] if f['finding_type'] == 'defect']


# ----------------------------------------------------------------
def test_analysis_scripts_make_no_direct_network_calls():
    allowed = {'acquire_site.py', 'analyze_rendering.py', 'run_audit.py'}
    for src in (ROOT / 'skills').glob('*/scripts/*.py'):
        if src.name in allowed:
            continue
        tree = ast.parse(src.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [n.name for n in node.names] + [getattr(node, 'module', '') or '']
                assert not any(n.startswith(('urllib.request', 'http.client', 'socket')) for n in names), src


def test_no_dev_history_references():
    """Shipped code explains itself. References to how it was built (handout
    rounds, internal change-list item numbers, work packages, old version names)
    mean nothing to a reader of the marketplace, so they stay out of it."""
    import re
    pat = re.compile(r'Round[- ]\d|\bdonor\b|\bv[0-9]\b|Step \d\.\d|\bWP\d|\(A\d{1,2}[),/]|\bA\d{1,2}:')
    sources = (list((ROOT / 'common').glob('*.py')) + list((ROOT / 'skills').glob('*/scripts/*.py'))
               + list((ROOT / 'skills').glob('*/SKILL.md')) + list((ROOT / 'skills').glob('*/references/*.md'))
               + [ROOT / 'README.md'])
    for src in sources:
        found = pat.search(src.read_text())
        assert not found, f'{src}: {found.group(0)!r}'


def test_bootstrap_finds_marketplace_and_fails_clearly_outside(tmp_path):
    from _bootstrap import marketplace_root
    assert Path(marketplace_root()) == ROOT
    lone = tmp_path / 'lone'
    lone.mkdir()
    (lone / '_bootstrap.py').write_text((ROOT / 'skills/audit-orchestrator/scripts/_bootstrap.py').read_text())
    proc = subprocess.run([sys.executable, '-c', 'import _bootstrap; _bootstrap.ensure_paths()'], cwd=lone,
                          capture_output=True, text=True, timeout=20)
    assert proc.returncode == 2 and 'install the whole marketplace' in proc.stderr.lower()


def test_site_argument_is_required():
    proc = subprocess.run([sys.executable, str(ROOT / 'skills/audit-orchestrator/scripts/run_audit.py')],
                          capture_output=True, text=True, timeout=20)
    assert proc.returncode == 2 and 'site' in proc.stderr


def test_manifest_version_and_single_entrypoint():
    m = json.loads((ROOT / 'marketplace.json').read_text())
    assert m['version'].startswith('9.') and sum(1 for s in m['skills'] if s.get('entrypoint')) == 1


def test_ordering_severity_first_and_site_level_reach():
    from prioritize_findings import prioritize_findings
    ctx = ScoringContext(10, 5, {}, 'https://shop.example/')
    low = apply_scoring(_f('h1', 'low', [f'https://shop.example/{i}' for i in range(5)]), ctx)
    med = apply_scoring(_f('bot-challenge-rate', 'medium', ['https://shop.example/deep'], effort='medium'), ctx)
    assert med['severity_rationale']['scope'] == 'site-wide'
    assert prioritize_findings([low, med])[0] is med


# ---------------------------------------------------------------- AG-01 passage
_NAV = '<nav><a href="/">Home</a> <a href="/shop">Shop</a> <a href="/login">Log in</a> Skip to main content</nav>'


def _brief(pages):
    import run_audit
    return run_audit.build_agent_brief(snapshot(pages), {'data': {'canonical_name': 'Acme'}}, {})


def test_ag01_passage_is_the_about_page_opening_without_navigation():
    home = page('<html><title>Acme</title>' + _NAV + '<h1>Acme</h1><a href="/about">About us</a></html>',
                'https://shop.example/')
    about = page('<html><title>About Acme</title><meta name="description" content="Acme makes hand tools for '
                 'carpenters in India.">' + _NAV + '<h1>About Acme</h1><p>Acme is a family company that has made '
                 'chisels and hand planes for professional carpenters since 1998.</p></html>',
                 'https://shop.example/about')
    ag = _brief([home, about])['ag01']
    assert ag['about_source'] == 'about_page' and ag['assessable'] and ag['passage_url'].endswith('/about')
    assert ag['opening_passage'].startswith('About Acme') and 'chisels' in ag['opening_passage']
    assert 'Log in' not in ag['opening_passage'] and 'Skip to main content' not in ag['opening_passage']


def test_ag01_homepage_is_used_only_when_no_about_page_exists():
    home = page('<html><title>Acme</title>' + _NAV + '<h1>Acme hand tools</h1><p>Acme sells chisels and hand planes '
                'to professional carpenters across India.</p></html>', 'https://shop.example/')
    ag = _brief([home])['ag01']
    assert ag['about_source'] == 'homepage_no_about_page' and ag['assessable']


def test_ag01_not_assessable_when_about_link_seen_but_page_not_acquired():
    home = page('<html><title>Acme</title>' + _NAV + '<h1>Acme</h1><p>Welcome to the store of tomorrow, today and '
                'always.</p><footer><a href="/company/about-us">About us</a></footer></html>', 'https://shop.example/')
    ag = _brief([home])['ag01']
    assert ag['about_source'] == 'homepage_about_not_acquired' and ag['assessable'] is False
    assert ag['about_link_seen'].endswith('/company/about-us')


def test_ag01_about_page_is_fetched_first_once_linked():
    home = ('<html><head><title>Shop</title></head><body>' + ''.join(f'<a href="/item/{i}">Item {i}</a>'
            for i in range(40)) + '<footer><a href="/about-us">About us</a></footer></body></html>')
    routes = {'/': (200, home, None), '/about-us': (200, '<html><title>About</title><h1>About</h1></html>', None)}
    for i in range(40):
        routes[f'/item/{i}'] = (200, f'<html><title>Item {i}</title><h1>Item {i}</h1></html>', None)
    url, stop = start_server(routes=routes)
    try:
        limits = Limits(MAX_PAGES_CRAWLED=3)
        a = acquire_site(url + '/', make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop()
    assert url + '/about-us' in [p.url for p in a.pages]


def test_ag01_not_assessed_entry_is_advisory_after_finalize(tmp_path):
    from ingest_agent_findings import load_agent_findings
    path = tmp_path / 'ag.json'
    path.write_text(json.dumps([{'check': 'AG-01', 'status': 'insufficient_evidence', 'severity': 'medium',
                                 'evidence': 'About page https://shop.example/about-us was not acquired; not assessed.'}]))
    result, stage = load_agent_findings(str(path))
    f = result['findings'][0]
    assert stage == 'ingested' and f['severity'] == 'low' and f['finding_type'] == 'proactive_improvement'


def test_ag01_about_section_inside_an_acquired_page():
    home = page('<html><title>Acme</title>' + _NAV + '<h1>Acme</h1><a href="/help/#about">About Acme</a></html>',
                'https://shop.example/')
    help_page = page('<html><title>Help</title><h1>Help</h1><h2>Shipping</h2><p>We ship daily.</p>'
                     '<h2>About Acme</h2><p>Acme makes chisels and hand planes for carpenters in India.</p></html>',
                     'https://shop.example/help/')
    ag = _brief([home, help_page])['ag01']
    assert ag['about_source'] == 'about_section' and ag['assessable']
    assert ag['opening_passage'].startswith('About Acme') and 'chisels' in ag['opening_passage']


def test_ag01_about_section_captured_beyond_the_visible_text_cap():
    filler = '<p>' + 'General help text that is long. ' * 900 + '</p>'
    home = page('<html><title>Acme</title><h1>Acme</h1><a href="/help/#about">About</a></html>', 'https://shop.example/')
    help_page = page('<html><title>Help</title><h1>Help</h1><ul><li><a href="#about">About</a></li></ul>' + filler +
                     '<h2>About</h2><p>Acme is a family company that has made chisels and hand planes for '
                     'professional carpenters in India since 1998. It sells online and through 40 dealers.</p>'
                     '<h2>Shipping</h2><p>We ship daily.</p></html>', 'https://shop.example/help/')
    assert 'chisels' not in help_page.visible_text  # beyond the 20,000-character cap
    ag = _brief([home, help_page])['ag01']
    assert ag['about_source'] == 'about_section' and 'chisels' in ag['opening_passage']
    assert 'We ship daily' not in ag['opening_passage']
