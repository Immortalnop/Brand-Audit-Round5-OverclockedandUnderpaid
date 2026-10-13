"""Phase 6 ownership, unchanged priority, Google scope and portable provenance."""
import copy
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common','skills/audit-orchestrator/scripts','skills/crawl-render-audit/scripts','tests'):
    sys.path.insert(0,str(ROOT/rel))

from test_offers_facts_crawlers import page, snapshot, deadline, jsonld
from test_agent_stage_merge import _finding
from check_llms_txt import check_llms_txt
from analyze_citation_schema import analyze_citation_schema
from analyze_machine_readability import analyze_machine_readability
from check_catalog import enrich_finding, RETIRED_CHECK_IDS
from merge_findings import merge_findings, fold_into
from prioritize_findings import prioritize_findings, annotate_action_plan, top_actions, quick_wins
from agent_evidence import code_version, RELEASE_VERSION
from llms_txt import parse_llms_txt
from models import freeze_value
from dataclasses import replace
from report_markdown import _action, _finding_detail


def test_role_enrichment_cannot_reorder_or_rescore_substantive_findings():
    findings = [_finding('no-jsonld',['https://s.example/a']),
                _finding('robots-unreachable',[],status='confirmed',confidence=.9,severity='high')]
    ordered = prioritize_findings(copy.deepcopy(findings))
    before = [(f['check_id'],f['severity'],f['status'],f['confidence']) for f in ordered]
    for f in ordered:
        enrich_finding(f)
    annotate_action_plan(ordered,12)
    assert [(f['check_id'],f['severity'],f['status'],f['confidence']) for f in prioritize_findings(ordered)] == before
    assert all(f['suggested_action']['owner_roles'] for f in ordered)
    assert ordered[0]['priority_basis']['assessed_page_denominator'] is None
    assert ordered[0]['priority_basis']['sample_pages_analyzed'] == 12
    for row in top_actions(ordered)+quick_wins(ordered,[]):
        assert row['owner_roles'] and row['priority_basis']


def test_roles_merge_as_sorted_union_without_promoting_status():
    a=_finding('no-jsonld',['https://s.example/a'])
    b=copy.deepcopy(a)
    a['suggested_action']['owner_roles']=['developer']
    b['suggested_action']['owner_roles']=['seo','content','developer']
    merged=merge_findings([{'skill':'s','findings':[a,b]}])[0]
    assert merged['suggested_action']['owner_roles']==['content','developer','seo']
    joined,folded=fold_into([a],[b])
    assert folded==1 and joined[0]['suggested_action']['owner_roles']==['content','developer','seo']
    assert joined[0]['status']=='suspected'


def test_roles_and_priority_are_safely_rendered_and_denominator_is_explicit():
    f=_finding('no-jsonld',['https://s.example/a'])
    annotate_action_plan([f],12)
    f['suggested_action']['owner_roles']=['x|y\n<script>z</script>`']
    rendered='\n'.join(_finding_detail(f))
    assert '<script>' not in rendered and 'assessed-page denominator: unavailable' in rendered
    assert 'Priority basis:' in rendered and 'Suggested roles:' in rendered


@pytest.mark.parametrize('present',[False,True])
def test_ordinary_page_has_no_llms_presence_visibility_score_or_publish_task(present):
    data={'present':present,'status':'ok' if present else 'absent','structure_issues':[],
          'link_count':1 if present else 0,'links':['https://s.example/docs'] if present else []}
    art=replace(snapshot(page()),llms_txt_data=freeze_value(data))
    result=check_llms_txt(art,deadline())
    assert not result['findings']
    assert result['metrics']['google_search_uses_llms_txt'] is False
    assert result['metrics']['llms_txt_present'] == present
    assert 'no-llms-txt' in RETIRED_CHECK_IDS


def test_minimal_optional_llms_file_and_bom_are_valid_without_extra_requirements():
    for text in ('# Acme\n','\ufeff# Acme\n'):
        parsed=parse_llms_txt(text,'https://s.example/llms.txt')
        assert not parsed['structure_issues'] and parsed['format_advice']


def test_existing_qanda_stays_useful_without_retired_google_markup_requirement():
    body='<h2>What is it?</h2><p>A tool.</p><h2>Who uses it?</h2><p>Builders.</p><h2>Where?</h2><p>Workshops.</p>'
    p=page(body=body)
    assert not analyze_citation_schema(snapshot(p),deadline())['findings']
    questions=[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}}
               for q,a in [('What is it?','A tool.'),('Who uses it?','Builders.'),('Where?','Workshops.')]]
    p=page(body=body,head=jsonld({'@context':'https://schema.org','@type':'FAQPage','mainEntity':questions}))
    result=analyze_citation_schema(snapshot(p),deadline())
    assert not result['findings'] and result['metrics']['citation_schema_types_present']['FAQPage']==1
    p=page(head='<script type="application/ld+json">{"@type":"FAQPage",broken}</script>')
    result=analyze_machine_readability(snapshot(p),deadline())
    assert any(f['check_id']=='malformed-jsonld' for f in result['findings'])
    assert all('rich result' not in json.dumps(f).lower() for f in result['findings'])


@pytest.mark.parametrize('record,suffix', [
    ({'version':RELEASE_VERSION,'commit':'a'*40,'uncommitted_changes':False},'a'*12),
    ({'version':RELEASE_VERSION,'commit':'b'*40,'uncommitted_changes':True},'b'*12+'.dirty'),
    ({'version':RELEASE_VERSION,'commit':'c'*40,'uncommitted_changes':None},'c'*12+'.state-unknown'),
    ({'version':'8.3.0','commit':'a'*40,'uncommitted_changes':False},'unknown'),
    ({'version':RELEASE_VERSION,'commit':'invented','uncommitted_changes':False},'unknown'),
    ({'version':RELEASE_VERSION,'commit':'a'*40,'uncommitted_changes':'false'},'unknown'),
])
def test_portable_version_validates_record_and_keeps_dirty_unknown(tmp_path,record,suffix):
    (tmp_path/'RELEASE.json').write_text(json.dumps(record))
    assert code_version(tmp_path)==RELEASE_VERSION+'+'+suffix


def test_valid_checkout_provenance_is_honest_and_overrides_portable_record():
    result=code_version(ROOT)
    assert re.fullmatch(re.escape(RELEASE_VERSION)+r'\+[a-f0-9]{12}(?:\.dirty|\.state-unknown)?',result)


def test_unrequested_optional_companion_html_fallback_is_not_a_defect():
    data={'present':True,'status':'ok','structure_issues':[],'links':['https://s.example/docs'],
          'full':{'status':'malformed','served_html':True}}
    art=replace(snapshot(page()),llms_txt_data=freeze_value(data))
    assert not check_llms_txt(art,deadline())['findings']
