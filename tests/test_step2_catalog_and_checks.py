"""Step 2 regression coverage: one snapshot, catalog contract and calibrated ports."""
import ast
import json
import sys
from dataclasses import replace
from pathlib import Path
from time import monotonic
from types import SimpleNamespace
from unittest.mock import patch

import pytest
ROOT=Path(__file__).resolve().parents[1]
for rel in ('common','skills/audit-orchestrator/scripts','skills/crawl-render-audit/scripts',
            'skills/freshness-corroboration/scripts','skills/engagement-audit/scripts'):
    sys.path.insert(0,str(ROOT/rel))
from check_catalog import CATALOG, get_entry
from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline, hash_artifacts
from transport import Response, Transport
from acquire_site import _extract_page, acquire_site
from analyze_metadata import analyze_metadata, CHECK_IDS as META_IDS
from analyze_performance import analyze_performance, CHECK_IDS as PERF_IDS
from analyze_answer_content import analyze_answer_content, CHECK_IDS as ANSWER_IDS
from analyze_machine_readability import _EXPECTED_SCHEMA, analyze_machine_readability
from assess_freshness import RULE_IDS as FRESHNESS_IDS
from check_ai_crawler_access import CHECK_IDS as CRAWLER_IDS
from analyze_directives import analyze_directives
from run_audit import run_audit
from fixtures_server import start_server

IDENTITY={'status':'success','data':{'canonical_name':'Acme','confidence':.95}}
LIMITS=Limits()

def page(html,url='https://fixture.example/',headers=None,truncated=False):
    response=Response(200,{'Content-Type':'text/html',**(headers or {})},html.encode(),url,truncated)
    response.network_duration_ms=100
    return _extract_page(url,response,99999,LIMITS)

def snapshot(pages, sitemap='ok'):
    return AuditArtifacts('https://fixture.example/','https://fixture.example',tuple(pages),
        freeze_value({'status':'ok'}),freeze_value({'present':True,'status':'ok'}),
        freeze_value({'status':sitemap}),freeze_value({}),())

def ids(result):return {f['check_id'] for f in result['findings']}

def meta(html):return analyze_metadata(snapshot([page(html)]),make_deadline(LIMITS))

def test_catalog_covers_static_and_dynamic_production_rules():
    declared=set(META_IDS|PERF_IDS|ANSWER_IDS)
    for source in (ROOT/'skills').glob('*/scripts/*.py'):
        tree=ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Dict):
                for key,value in zip(node.keys,node.values):
                    if isinstance(key,ast.Constant) and key.value=='rule_id':
                        if isinstance(value,ast.Constant):declared.add(value.value)
                        if isinstance(value,ast.IfExp):
                            declared.update(v.value for v in (value.body,value.orelse) if isinstance(v,ast.Constant))
            if source.name=='analyze_experience.py' and isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='add' and node.args:
                declared.add(ast.literal_eval(node.args[0]))
    declared.update('page-type-schema-gap:'+k for k in _EXPECTED_SCHEMA)
    declared.update(FRESHNESS_IDS | CRAWLER_IDS)
    declared.update(('noindex','nosnippet'))
    declared.update('baseline:'+k for k in ('ai_discoverability','engagement','off_site_presence'))
    declared.update(('beyond:search-action','beyond:ai-landing-pages'))
    assert declared == set(CATALOG), {'missing':declared-set(CATALOG),'unused':set(CATALOG)-declared}
    for check_id in declared:
        assert all(get_entry(check_id)[k].strip() for k in ('mechanism','implementation_detail','expected_outcome'))

@pytest.mark.parametrize('markup,expected',[
    ('<html><h1>Hello</h1>','missing-title'),
    ('<html><title>Hello</title>','missing-description'),
    ('<html><title>Hello</title>','missing-language'),
    ('<html lang="en"><title>Hello</title>','missing-canonical'),
    ('<html><link rel="canonical" href="javascript:bad">','invalid-canonical'),
    ('<html><link rel="canonical" href="/a"><link rel="canonical" href="/b">','invalid-canonical'),
    ('<html><link rel="canonical" href="https://other.example/">','cross-origin-canonical'),
    ('<html><title>A</title>','title-length'),
    ('<html><h1>A</h1><h3>B</h3><h4>C</h4>','heading-hierarchy'),
    ('<html><meta property="og:title" content="Title">','social-metadata'),
    ('<html><meta property="og:image" content="file:///private">','social-url'),
    ('<html><meta name="twitter:card" content="invalid">','twitter-card'),
    ('<html><p>'+('useful words '*110)+'</p>','missing-landmarks'),
])
def test_metadata_positive_cases(markup,expected):
    result=meta(markup)
    assert expected in ids(result)
    for f in result['findings']:
        entry=get_entry(f['check_id'])
        for field in entry:
            assert f[field]==entry[field]
        assert f['affected_pages'] and f['evidence']

def test_complete_metadata_relative_canonical_and_decorative_alt_are_accepted():
    html='''<html lang="en"><head><title>Acme useful topic guide</title><meta name="description" content="Useful topic">
    <link rel="canonical" href="/"><meta property="og:title" content="Acme"><meta property="og:description" content="Useful topic">
    <meta property="og:url" content="https://fixture.example/"><meta property="og:image" content="https://fixture.example/a.png">
    <meta name="twitter:card" content="summary_large_image"></head><body><main><h1>Useful topic</h1>
    <img src="a.png" alt="" width="20" height="20"></main></body></html>'''
    assert not ids(meta(html))
    assert page(html).features['missing_alt']==0


def test_loading_observations_and_timing_do_not_use_pacing_duration():
    scripts=''.join('<script src="/a.js"></script>' for _ in range(6))
    html='<html><head>'+scripts+'</head><body>'+('<img src="a.png">'*10)+'</body></html>'
    p=page(html)
    result=analyze_performance(snapshot([p]),make_deadline(LIMITS))
    assert {'blocking-scripts','image-sizing'} <= ids(result)
    assert 'fetch-latency' not in ids(result)  # fetch_duration_ms=99999 includes pacing.
    f=dict(p.features);f['network_duration_ms']=3100
    assert 'fetch-latency' in ids(analyze_performance(snapshot([replace(p,features=freeze_value(f))]),make_deadline(LIMITS)))
    safe=page('<html><head>'+('<script type="module" src="/a.js"></script><script defer src="/b.js"></script>'*6)+'</head></html>')
    assert safe.features['head_blocking_scripts']==0


def test_large_markup_and_capped_pages_only_emit_positive_size_evidence():
    p=page('<html><style>'+('x'*410000)+'</style><p>'+('readable '*100)+'</p></html>')
    assert {'heavy-html','markup-ratio'} <= ids(analyze_performance(snapshot([p]),make_deadline(LIMITS)))
    capped=page('<html><p>Partial',truncated=True)
    assert not ids(analyze_metadata(snapshot([capped]),make_deadline(LIMITS)))
    assert ids(analyze_performance(snapshot([capped]),make_deadline(LIMITS)))=={'heavy-html'}


def test_sitemap_unknown_permission_does_not_become_missing_sitemap():
    p=page('<html><p>ok</p></html>')
    assert 'sitemap-unavailable' not in ids(analyze_performance(snapshot([p],'not_checked'),make_deadline(LIMITS)))
    assert 'sitemap-unavailable' in ids(analyze_performance(snapshot([p],'absent'),make_deadline(LIMITS)))


def test_http_and_redirect_observations():
    p=page('<html>ok</html>','http://fixture.example/')
    f=dict(p.features);f['redirect_hops']=3;p=replace(p,features=freeze_value(f))
    assert {'http-transport','redirect-chain'} <= ids(analyze_metadata(snapshot([p]),make_deadline(LIMITS)))


def test_answer_checks_are_calibrated_and_language_gated():
    body=' '.join(['apples fruit nutrition orchard']*90)
    p=page('<html lang="en"><title>Orbital Rocket Launch Guide</title><p>'+body+'</p></html>')
    result=analyze_answer_content(snapshot([p]),IDENTITY,make_deadline(LIMITS))
    assert {'title-body-alignment','term-repetition','brand-definition'} <= ids(result)
    assert all(f['finding_type']=='proactive_improvement' and f['status']=='suspected' for f in result['findings'])
    foreign=page('<html lang="hi"><title>Orbital Rocket Launch Guide</title><p>'+body+'</p></html>')
    assert not ids(analyze_answer_content(snapshot([foreign]),IDENTITY,make_deadline(LIMITS)))
    defined=page('<html lang="en"><p>Acme is a maker of tools for gardeners.</p><p>'+body+'</p></html>')
    assert 'brand-definition' not in ids(analyze_answer_content(snapshot([defined]),IDENTITY,make_deadline(LIMITS)))


def test_question_headings_are_optional_and_require_relevant_sample():
    body=' '.join(['clear practical useful topics']*60)
    pages=[page('<html lang="en"><h2>Useful topic</h2><p>'+body+'</p></html>',f'https://fixture.example/blog/{i}') for i in range(3)]
    assert 'answer-headings' in ids(analyze_answer_content(snapshot(pages),IDENTITY,make_deadline(LIMITS)))
    answered=page('<html lang="en"><h2>How does this work?</h2><p>'+body+'</p></html>','https://fixture.example/blog/4')
    assert 'answer-headings' not in ids(analyze_answer_content(snapshot(pages+[answered]),IDENTITY,make_deadline(LIMITS)))
    assert 'answer-headings' not in ids(analyze_answer_content(snapshot(pages[:1]),IDENTITY,make_deadline(LIMITS)))


def test_software_schema_and_service_classification_use_nested_types():
    app=page('<html><script type="application/ld+json">'+json.dumps({'@graph':[{'@type':['https://schema.org/MobileApplication'],'name':'Acme App'}]})+'</script></html>')
    assert app.page_type=='home'
    app=replace(app,page_type='software')
    assert 'app-identity' in ids(analyze_answer_content(snapshot([app]),IDENTITY,make_deadline(LIMITS)))
    assert 'page-type-schema-gap:software' not in ids(analyze_machine_readability(snapshot([app]),make_deadline(LIMITS)))
    service=page('<html><script type="application/ld+json">{"@type":"Service","name":"Repair"}</script></html>','https://fixture.example/services/repair')
    assert service.page_type=='service'


def test_tls_failure_refines_existing_failure_without_duplicate():
    p=replace(page('<html>'),status_code=None,warnings=('fetch_tls_certificate_error',))
    result=analyze_directives(snapshot([p]),make_deadline(LIMITS))
    assert ids(result)=={'tls-health'}
    assert result['findings'][0]['status']=='insufficient_evidence'
    assert result['findings'][0]['severity']=='low'


def test_new_checks_share_immutable_snapshot_and_never_fetch():
    a=snapshot([page('<html lang="en"><h1>hello</h1></html>')])
    before=hash_artifacts(a)
    with patch.object(Transport,'get',side_effect=AssertionError('New checks must not fetch')):
        analyze_metadata(a,make_deadline(LIMITS))
        analyze_performance(a,make_deadline(LIMITS))
        analyze_answer_content(a,IDENTITY,make_deadline(LIMITS))
    assert hash_artifacts(a)==before


def test_every_emitted_check_id_resolves_after_merge_and_recommendations():
    url,stop=start_server()
    try:
        report=run_audit(url+'/',allow_private_targets=True)
        assert report['coverage']['pages_analyzed']>0,report['warnings']
        for f in report['findings']+report['recommendations']:
            assert f['check_id'] in CATALOG
            for rid in f.get('check_ids',[]):get_entry(rid)
            for key,value in get_entry(f['check_id']).items():assert f[key]==value
        assert not any('Dropped' in w for w in report['warnings'])
        json.dumps(report,allow_nan=False)
    finally:stop()


def test_no_em_dash_or_second_skill_orchestrator():
    for p in ROOT.rglob('*'):
        if p.is_file() and p.suffix in ('.py','.md','.txt','.json'):
            assert chr(0x2014) not in p.read_text(),str(p)
    entry=(ROOT/'skills/audit-orchestrator/scripts/run_audit.py').read_text()
    assert 'subprocess.run(' not in entry and '--workdir' not in entry


def test_robots_probe_tls_failure_is_reported_without_fetching_pages():
    with patch('acquire_site.classify_url',return_value=SimpleNamespace(safe=True)), \
         patch.object(Transport,'get',return_value=(None,'tls_certificate_error')) as fetch:
        a=acquire_site('https://fixture.example/',make_deadline(LIMITS),LIMITS)
    assert fetch.call_count==2 and not a.pages
    result=analyze_directives(a,make_deadline(LIMITS))
    assert ids(result)=={'tls-health'}
    assert result['findings'][0]['evidence'][0]['urls']==['https://fixture.example/robots.txt']


def test_crawl_delay_remains_the_policy_for_every_fetch():
    url,stop=start_server(robots_body='User-agent: *\nAllow: /\nCrawl-delay: 0.04\n')
    seen=[]
    original=Transport.get
    def tracked(self,url,**kwargs):
        seen.append((url,self.delay,self.requests))
        return original(self,url,**kwargs)
    try:
        limits=replace(LIMITS,MAX_PAGES_CRAWLED=1)
        with patch.object(Transport,'get',tracked):
            a=acquire_site(url+'/',make_deadline(limits),limits,allow_private_targets=True)
        assert len(seen)>=4
        assert all(delay>=.04 for _,delay,_ in seen[1:])
        assert a.acquisition_metadata['total_requests']>=len(seen)
    finally:stop()


def test_new_checks_respect_expired_deadline():
    a=snapshot([page('<html>')])
    expired=SimpleNamespace(expired=lambda:True)
    for result in (analyze_metadata(a,expired),analyze_performance(a,expired),analyze_answer_content(a,IDENTITY,expired)):
        assert not result['findings'] and result['status']=='insufficient_evidence'


def test_malformed_canonical_and_bare_attributes_do_not_abort_audit():
    p=page('<html lang><head><meta name="description" content><link rel="canonical" href="http://[invalid"></head><body><img width="²" height="20" alt><div style>Visible</div></body></html>')
    assert 'html_parse_incomplete' not in p.warnings
    result=analyze_metadata(snapshot([p]),make_deadline(LIMITS))
    assert 'invalid-canonical' in ids(result)


def test_2_3_engagement_micro_checks_fire_and_are_i1_capped():
    from analyze_experience import analyze_experience
    anchors="".join('<a href="/p%d">read more</a>' % i for i in range(12))
    generic_html=("<html lang=\"en\"><head><title>T</title></head><body>"
          "<h1>About our team</h1><p>"+("word "*450)+"</p>"+anchors+"</body></html>")
    generic_page=page(generic_html,url='https://fixture.example/about')
    # No H1 and no internal links: page-orientation + internal-discoverability.
    bare_html=("<html lang=\"en\"><head><title>T</title></head><body>"
          "<p>"+("word "*450)+"</p></body></html>")
    bare_page=page(bare_html,url='https://fixture.example/guide')
    result=analyze_experience(snapshot([generic_page,bare_page]),make_deadline(LIMITS))
    fired=ids(result)
    assert {'generic-anchor-text','page-orientation','internal-discoverability'} <= fired
    for f in result['findings']:
        if f['status']=='insufficient_evidence':
            assert f['severity']=='low' and f['finding_type']=='proactive_improvement'


def test_2_3_email_summary_readable_fires_on_image_carried_substance():
    from analyze_experience import analyze_experience
    imgs="<img src='a.png'><img src='b.png'><img src='c.png'>"
    html=("<html lang=\"en\"><head><title>T</title></head><body>"
          "<form><input type='email'><button>Subscribe to our newsletter</button></form>"+imgs+"<p>Sign up.</p></body></html>")
    result=analyze_experience(snapshot([page(html)]),make_deadline(LIMITS))
    assert {'email-summary','email-summary-readable'} <= ids(result)


@pytest.mark.parametrize('form',[
    "<form action='/contact'><input type='email' name='email'><textarea></textarea><button>Send message</button></form>",
    "<form action='/trial'><input type='email'><button>Start your free trial</button></form>",
    "<form action='/login'><input type='email'><input type='password'><button>Subscribe</button></form>",
])
def test_email_summary_needs_a_newsletter_signup(form):
    """Contact, trial and login forms with an email field are not newsletter signups."""
    from analyze_experience import analyze_experience
    html="<html lang=\"en\"><head><title>T</title></head><body>"+form+"<p>Hello.</p></body></html>"
    fired=ids(analyze_experience(snapshot([page(html)]),make_deadline(LIMITS)))
    assert not {'email-summary','email-summary-readable'} & fired


def test_2_4_baseline_recommendations_carry_rich_action_and_evidence_status():
    from generate_recommendations import generate_recommendations
    from action_catalog import EVIDENCE_STATUS_MODES
    recs=generate_recommendations([],[])
    assert recs, "baseline recommendations must always ship"
    for r in recs:
        assert r.get('evidence_status') in EVIDENCE_STATUS_MODES.values()
    eng=next(r for r in recs if r['category']=='engagement')
    action=eng['suggested_action']
    assert len(action['steps'])>=3
    assert action.get('implementation_detail') and action.get('expected_outcome')


def _agent_import():
    import importlib
    sys.path.insert(0,str(ROOT/'skills/entity-corroboration-agent/scripts'))
    return importlib.import_module('ingest_agent_findings')


def test_2_5_agent_stage_skips_gracefully_when_not_supplied(monkeypatch):
    mod=_agent_import()
    monkeypatch.delenv('AGENT_FINDINGS_PATH',raising=False)
    a=snapshot([page('<html lang="en"><title>T</title></html>')])
    result=mod.ingest_agent_findings(a,IDENTITY,make_deadline(LIMITS),None)
    assert result['status']=='insufficient_evidence'
    assert result['metrics']['agent_stage']=='not_supplied'
    assert not result['findings']
    assert any('not checked' in w for w in result['warnings'])


def test_2_5_agent_findings_ingest_in_process_and_are_i1_capped(tmp_path,monkeypatch):
    mod=_agent_import()
    supplied=[
        {'check':'AG-01','status':'suspected','evidence':'About names no product or category.'},
        {'check':'AG-02','status':'confirmed','evidence':'No independent mention found.'},
        {'check':'AG-03','status':'confirmed','severity':'high','evidence':'A community thread describes a different category.',
         'suggested_action':{'summary':'Reconcile the category','steps':['Fix source','Update markup']}},
        {'check':'AG-99','evidence':'unknown check, must be ignored'},
        {'check':'AG-02','status':'insufficient_evidence','evidence':'could not check'},
    ]
    p=tmp_path/'agent_findings.json'
    p.write_text(json.dumps(supplied))
    monkeypatch.setenv('AGENT_FINDINGS_PATH',str(p))
    a=snapshot([page('<html lang="en"><title>T</title></html>')])
    result=mod.ingest_agent_findings(a,IDENTITY,make_deadline(LIMITS),None)
    assert result['status']=='success'
    rules={f['check_id'] for f in result['findings']}
    assert {'about-concreteness','no-independent-mention','independent-contradiction'} <= rules
    # AG-99 ignored; four known entries built (AG-02 appears twice).
    assert result['metrics']['findings_ingested']==4
    for f in result['findings']:
        assert f['check_id'] in CATALOG
        if f['status']=='insufficient_evidence':
            assert f['severity']=='low' and f['finding_type']=='proactive_improvement'
        assert f['mechanism'] and f['suggested_action']['implementation_detail']


def test_2_5_agent_stage_wired_into_full_report(monkeypatch):
    # With no agent findings supplied, the full report still completes and records
    # the stage as not_supplied rather than asserting a corroboration defect.
    monkeypatch.delenv('AGENT_FINDINGS_PATH',raising=False)
    url,stop=start_server()
    try:
        report=run_audit(url+'/',replace(LIMITS,MAX_PAGES_CRAWLED=3),allow_private_targets=True)
    finally:stop()
    assert report['coverage']['agent_corroboration_stage']=='not_supplied'


def test_2_6_sample_report_exists_validates_and_is_clean():
    from validate_report import validate_report
    path=ROOT/'examples'/'sample-report.json'
    assert path.is_file(), "examples/sample-report.json must be shipped for grader review"
    text=path.read_text(encoding='utf-8')
    assert '\u2014' not in text, "sample report must contain no em dashes"
    assert '127.0.0.1' not in text, "sample report must not leak fixture host"
    report=json.loads(text)
    validated=validate_report(report,strict_catalog=True)
    # Strict validation drops nothing from a clean sample.
    assert len(validated['findings'])==len(report['findings'])
    assert len(validated['recommendations'])==len(report['recommendations'])
    for item in validated['findings']+validated['recommendations']:
        assert item['check_id'] in CATALOG
        if item['status']=='insufficient_evidence':
            assert item['severity']=='low' and item['finding_type']=='proactive_improvement'
