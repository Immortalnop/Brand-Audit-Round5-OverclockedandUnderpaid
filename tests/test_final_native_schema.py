"""Phase 5 source-backed traps and supported positive controls."""
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'skills/audit-orchestrator/scripts', 'skills/crawl-render-audit/scripts',
            'skills/freshness-corroboration/scripts', 'tests'):
    sys.path.insert(0, str(ROOT / rel))

from test_offers_facts_crawlers import page, snapshot, deadline, facts, jsonld, _product, ids, SITE
from analyze_machine_readability import analyze_machine_readability
from analyze_citation_schema import _number, _count
from schema_values import date_value_state, iter_schema_nodes, resolve_iri_value, value_observations
from assess_freshness import assess_freshness
from extract_claims import structured_date_claims
from models import freeze_value
from merge_findings import merge_findings


def machine(*pages):
    return analyze_machine_readability(snapshot(*pages), deadline())


def block(raw):
    return '<script type="application/ld+json">' + raw + '</script>'


@pytest.mark.parametrize('raw,state,broken', [
    ('{"@type":"Organization",', 'malformed', True),
    ('{"@type":"Product","price":NaN}', 'malformed', True),
    ('{"@type":"Product","price":1e999}', 'unsupported', False),
    ('{"@type":"Organization","name":"A","name":"B"}', 'ambiguous', False),
])
def test_present_unusable_markup_is_never_missing_markup(raw, state, broken):
    p = page(head='<title>Home</title>' + block(raw))
    result = machine(p)
    assert 'no-jsonld' not in ids(result)
    assert ('malformed-jsonld' in ids(result)) == broken
    assert p.features['jsonld_extraction_state'] == state
    assert p.features['jsonld_block_count'] == 1


def test_mixed_blocks_keep_usable_facts_without_adding_missing_markup():
    p = page(head=block('{bad}') + jsonld({'@context':'https://schema.org', '@type':'Organization', 'name':'Acme'}))
    result = machine(p)
    assert 'malformed-jsonld' in ids(result) and 'no-jsonld' not in ids(result)
    assert len(p.jsonld_blocks) == 1


@pytest.mark.parametrize('text', [
    'Support plan costs USD 9.', 'Mug support subscription costs USD 9.',
    'Mug costs EUR 9.', 'Mug costs $9.', 'Mug costs USD 9 excluding tax.',
    'Mug variants cost USD 9 and USD 19.', 'Mug costs USD price9oops.',
    'Mug costs USD 1e3oops.',
])
def test_unrelated_ambiguous_or_conditional_price_is_not_a_conflict(text):
    assert 'fact-markup-mismatch' not in ids(facts(page('/products/mug', '<p>' + text + '</p>', head=_product('49'))))


@pytest.mark.parametrize('markup,visible,conflict', [
    ('1e3','USD 1000',False), ('-49','USD -49',False), ('0','USD 0',False),
    ('49','USD 1e3',True), ('49','USD -49',True),
])
def test_explicit_same_product_price_preserves_numeric_meaning(markup, visible, conflict):
    result = facts(page('/products/mug','<p>Mug costs ' + visible + '.</p>',head=_product(markup)))
    assert ('fact-markup-mismatch' in ids(result)) == conflict
    if conflict:
        assert result['findings'][0]['status'] == 'suspected'
        assert result['findings'][0]['severity'] == 'medium'


def test_explicit_contact_scope_does_not_compare_other_entities_or_locations():
    org = jsonld({'@type':'Organization','name':'Acme','telephone':'+1 555 010 0100',
                  'address':{'@type':'PostalAddress','streetAddress':'10 Downing Street','postalCode':'SW1A 1AA'}})
    result = facts(page('/contact','<p>Othercorp phone: (555) 010-0199</p><p>Address: 20 Other Street, London SW1A 2AA</p>',head=org))
    assert 'fact-markup-mismatch' not in ids(result)
    bakery = jsonld({'@type':'Bakery','name':'Acme Bakery','openingHours':'Mo-Fr 09:00-17:00'})
    for text in ('Other Bakery opening hours: Monday to Friday 10am - 6pm',
                 'Acme Bakery opening hours: Saturday to Sunday 10am - 6pm',
                 'Acme Bakery holiday opening hours: Monday to Friday 10am - 6pm'):
        assert 'fact-markup-mismatch' not in ids(facts(page('/visit','<p>'+text+'</p>',head=bakery)))


def product_offer(price, **kwargs):
    return {'@type':'Product','name':'Mug','gtin13':'0012345678905',
            'offers':dict({'@type':'Offer','price':price,'priceCurrency':'USD'}, **kwargs)}


@pytest.mark.parametrize('condition', ['eligibleRegion','priceValidUntil','itemCondition','eligibleQuantity','priceSpecification'])
def test_cross_page_prices_with_different_conditions_are_not_conflicts(condition):
    a,b = product_offer('49',**{condition:'A'}),product_offer('9',**{condition:'B'})
    assert 'fact-inconsistent-across-pages' not in ids(facts(page('/a',head=jsonld(a)),page('/b',head=jsonld(b))))


def test_cross_page_regional_language_and_address_are_separate_scopes():
    a = {'@type':'Organization','name':'Acme','telephone':'+44 20 7946 0000'}
    b = dict(a,telephone='+1 555 010 0199')
    assert not facts(page('/uk',head=jsonld(a),lang='en-GB'),page('/us',head=jsonld(b),lang='en-US'))['findings']
    a['address'] = {'streetAddress':'10 First Street','addressCountry':'GB'}
    b['address'] = {'streetAddress':'20 Other Street','addressCountry':'US'}
    assert not facts(page('/uk',head=jsonld(a)),page('/us',head=jsonld(b)))['findings']


def test_full_supported_reach_is_not_capped_by_evidence_samples():
    pages = [page('/p'+str(i), head=jsonld(product_offer('49' if i < 6 else '9'))) for i in range(12)]
    result = facts(*pages)
    finding = next(f for f in result['findings'] if f['check_id']=='fact-inconsistent-across-pages')
    assert len(finding['affected_pages']) == 12
    assert len(finding['evidence'][0]['urls']) == 12


@pytest.mark.parametrize('value,state', [
    ('2026-99-99','invalid'),('2026-02-29','invalid'),('2024-02-29','valid'),
    ('2026-01-01T99:00:00Z','invalid'),('2026-01-01T12:00:00+05:30','valid'),
    ('2026-01-01T12:00:00+99:99','invalid'),('March 5, 2020','unsupported'),
])
def test_calendar_aware_supported_forms(value,state):
    assert date_value_state(value) == state


def schema_page(node):
    return page(head=jsonld(dict({'@context':'https://schema.org'},**node)))


def test_selected_value_rules_skip_unknown_context_and_foreign_namespaces():
    base = {'@type':'Product','name':'Mug','price':True}
    assert value_observations(schema_page(base))[0]
    for context in ('https://foreign.example/context', {'@vocab':'https://foreign.example/'}):
        p = page(head=jsonld(dict(base,**{'@context':context})))
        assert not value_observations(p)[0]
    p = schema_page(dict(base,**{'@type':['https://foreign.example/Product','https://schema.org/Product']}))
    assert value_observations(p)[0]  # deterministic recognized member, independent of order
    assert not value_observations(schema_page({'@type':'Organization','name':'Acme'}))[0]


def test_currency_format_does_not_claim_iso_membership_and_zero_is_valid():
    assert not value_observations(schema_page({'@type':'Offer','price':0,'priceCurrency':'ZZZ'}))[0]
    assert value_observations(schema_page({'@type':'Offer','price':True,'priceCurrency':'usd'}))[0]
    invalid, limitations = value_observations(schema_page({'@type':'Offer','price':'1e999'}))
    assert not invalid and limitations


def test_document_base_external_base_vocab_prefix_and_id_coercion_are_distinct():
    context = {'@base':'https://identity.example/profiles/','@vocab':'https://schema.org/',
               's':'https://schema.org/', 'sameAs':{'@id':'s:sameAs','@type':'@id'},
               'kind':{'@id':'s:url','@type':'@vocab'}}
    p = page(head=jsonld({'@context':context,'@type':'s:Organization','name':'Acme','sameAs':'acme','kind':'Organization'}))
    node, ctx, types = next(iter_schema_nodes(p.jsonld_blocks,p.url))
    assert types == {'Organization'}
    assert resolve_iri_value('acme',ctx,'sameAs') == ('https://identity.example/profiles/acme','valid')
    assert resolve_iri_value('Organization',ctx,'kind') == ('https://schema.org/Organization','valid')
    assert resolve_iri_value({'@id':'urn:brand:acme'},ctx,'sameAs') == ('urn:brand:acme','valid')
    assert not value_observations(p)[0]


def test_unsupported_publication_format_is_a_limit_not_confirmed_invalid():
    p = schema_page({'@type':'Article','datePublished':'March 5, 2020'})
    result = assess_freshness({'data':{'facts':[]}},snapshot(p),deadline())
    assert 'structured-date-invalid' not in ids(result)
    assert result['metrics']['structured_date_limitations'] == 1
    assert result['status'] == 'insufficient_evidence'
    p = schema_page({'@type':'Article','datePublished':'2026-99-99'})
    assert 'structured-date-invalid' in ids(assess_freshness({'data':{'facts':[]}},snapshot(p),deadline()))


@pytest.mark.parametrize('value',[True,float('nan'),float('inf'),'1e999','price123oops'])
def test_rating_downstream_conversions_are_bounded(value):
    assert _number(value) is None and _count(value) is None


def test_confirmed_and_suspected_native_groups_stay_separate():
    result = facts(page('/products/mug','<p>Mug costs USD 9.</p>',head=_product('49')))
    suspected = result['findings'][0]
    confirmed = dict(suspected,status='confirmed',confidence=.9)
    assert len(merge_findings([dict(result,findings=[suspected,confirmed])])) == 2


def test_named_product_cooccurrence_does_not_assign_another_products_price():
    for passage in ('Mug is displayed beside Saucer, which costs USD 9.', 'Mugwort costs USD 9.'):
        assert not facts(page('/products/mug','<p>'+passage+'</p>',head=_product('49')))['findings']


def test_named_contact_cooccurrence_does_not_assign_another_companys_number():
    org={'@type':'Organization','name':'Acme','telephone':'+1 555 010 0100'}
    assert not facts(page('/contact','<p>Acme sponsors Othercorp. Othercorp phone: (555) 010-0199</p>',head=jsonld(org)))['findings']


def test_differently_dated_entity_facts_are_not_assumed_simultaneously_current():
    a={'@type':'Organization','name':'Acme','telephone':'+1 555 010 0100','validFrom':'2020-01-01'}
    b=dict(a,telephone='+1 555 010 0199',validFrom='2026-01-01')
    assert not facts(page('/old',head=jsonld(a)),page('/new',head=jsonld(b)))['findings']
