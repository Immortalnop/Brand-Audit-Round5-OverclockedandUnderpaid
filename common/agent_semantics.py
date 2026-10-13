"""Per-check evidence rules after schema, type, digest and registry validation.

These enforce acquired source binding and declared scope. Search/vision activity
and natural-language truth still require host evidence and review; declarations
are not execution receipts. This module performs no network requests.
"""
import unicodedata
from urllib.parse import urlsplit

from url_identity import page_identity
from url_safety import same_origin


def norm(value):
    return ' '.join(unicodedata.normalize('NFC', value or '').split()).casefold()


def _quote_support(quote, refs, ids, observation):
    if not quote:
        return []
    supporting = []
    for ref in refs:
        item = ids[ref]
        if item['ref_kind'] == 'page' and norm(quote) in norm(item.get('text', '') + ' ' + item.get('focus_text', '')):
            supporting.append(ref)
        elif item['ref_kind'] == 'claim' and not item.get('value_truncated') and norm(quote) == norm(item.get('value')):
            if item.get('subject') and item.get('predicate') and norm(observation.get('subject')) == norm(item['subject']) and norm(observation.get('predicate')) == norm(item['predicate']):
                supporting.append(item['page_evidence_id'])
    return supporting


def validate_semantics(check, outcome, refs, sources, queries, obs, packet, ids, origin):
    errors, support = [], []
    details = {}
    page_refs = [r for r in refs if ids[r]['ref_kind'] == 'page']
    images = [r for r in refs if ids[r]['ref_kind'] == 'image']
    name = (packet.get('identity') or {}).get('name')
    if not name:
        # An unresolved structured identity can still support a scoped search
        # for a positively observed name, cited by its acquired page reference.
        name = next((ids[r].get('title') for r in page_refs if ids[r].get('title') and
                     norm(ids[r]['title']) in norm(obs.get('identity')) and
                     norm(ids[r]['title']) in norm(ids[r].get('text'))), None)
        if name:
            details['identity_basis'] = 'Observed title also stated in referenced body text; structured identity unresolved.'
    if check == 'AG-01':
        focus = (packet.get('focus') or {}).get('ag01') or {}
        selected = focus.get('page_ref')
        if focus.get('assessable') is not True or focus.get('opening_complete') is not True:
            errors.append('AG-01 selected focused opening is not assessable/complete; record not_assessed')
        if selected not in page_refs or len(page_refs) != 1:
            errors.append('AG-01 must assess only the selected focused page reference')
        if norm(obs.get('passage')) != norm(focus.get('opening_passage')) or not obs.get('passage'):
            errors.append('observation.passage is not the complete selected focused opening in the referenced packet page')
        support = [selected] if selected in ids else []
    if check in ('AG-02', 'AG-03', 'AG-05', 'AG-06'):
        identity = obs.get('identity') or ''
        if not name or norm(name) not in norm(identity):
            errors.append('search assessment needs observation.identity bound to the acquired brand name')
        if not obs.get('context'):
            errors.append('search assessment needs observation.context (entity, date and query scope)')
        if not queries:
            errors.append('a search assessment needs the searches that ran (queries)')
        for query in queries:
            if name and norm(name) not in norm(query['query']):
                errors.append('query is not relevant to the acquired brand identity')
            if not query.get('executed_at'):
                errors.append('each query needs its executed_at date/context')
            matched = query.get('matching_result_count')
            independent = query.get('independent_result_count')
            for key, value in (('matching_result_count', matched), ('independent_result_count', independent)):
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= query['result_count']:
                    errors.append('query needs a bounded integer ' + key)
            if isinstance(matched, int) and isinstance(independent, int) and independent > matched:
                errors.append('independent_result_count cannot exceed matching_result_count')
        details['query_scope'] = {'identity': identity, 'context': obs.get('context'), 'queries': queries}
    if check == 'AG-02':
        if outcome == 'finding' and any(q.get('independent_result_count', 0) != 0 for q in queries):
            errors.append('AG-02 missing-mention finding conflicts with positive independent matching results')
        if outcome == 'pass' and (not any(q.get('independent_result_count', 0) > 0 for q in queries) or
                                  not any(s.get('kind') == 'inspected_page' and s.get('quote') and
                                          not same_origin(s['url'], origin) for s in sources)):
            errors.append('AG-02 pass needs an inspected independent matching mention')
    elif check == 'AG-03':
        quote = obs.get('site_quote')
        support = _quote_support(quote, refs, ids, obs)
        if not support:
            errors.append('AG-03 site_quote is not bound to the referenced acquired E/C claim and subject/predicate')
        inspected = [s for s in sources if s['kind'] == 'inspected_page' and s.get('quote')]
        if not inspected:
            errors.append('AG-03 needs an inspected conflicting page or agreement passage; search snippets are insufficient')
        origins = [origin] + [p.get('final_url') for p in packet['pages']] + [u for p in packet['pages'] for u in p.get('aliases', [])]
        for source in inspected:
            if any(u and same_origin(source['url'], u) for u in origins):
                errors.append('audited origin/observed aliases are not independent external sources')
            if not source.get('authorship'):
                errors.append('inspected AG-03 sources need declared authorship')
        if not obs.get('same_entity') or not obs.get('independence'):
            errors.append('AG-03 needs same_entity and independence explanations')
        if outcome == 'finding':
            if not obs.get('conflict_explanation') or not isinstance(obs.get('material'), bool):
                errors.append('AG-03 needs conflict_explanation and materiality')
            if inspected and all(norm(quote) in norm(s['quote']) for s in inspected):
                errors.append('external passages merely agree with the acquired site_quote')
        authors = {norm(s.get('authorship')) for s in inspected if s.get('authorship')}
        domains = {(urlsplit(s['url']).hostname or '').lower().removeprefix('www.') for s in inspected}
        passages = {norm(s['quote']) for s in inspected}
        details['independent_substantive_conflict'] = (outcome == 'finding' and obs.get('material') is True
            and len(authors) >= 2 and len(domains) >= 2 and len(passages) >= 2 and not errors)
        details['site_quote'] = quote
    elif check == 'AG-04':
        compared = obs.get('compared_page_refs') or []
        if not images or obs.get('image_viewed') is not True or not obs.get('transcription'):
            errors.append('AG-04 needs an actually viewed full I image and transcription')
        if not compared or any(r not in page_refs for r in compared):
            errors.append('AG-04 needs explicit compared_page_refs present among its E source references')
        eligible = {r for image in images for r in ids[image].get('page_evidence_ids', [])}
        if any(r not in eligible for r in compared):
            errors.append('AG-04 compared page is not an exported acquired association of the viewed image')
        if not obs.get('text_comparison') or obs.get('comparison_scope') not in ('raw_html_text', 'rendered_text', 'pdf_text'):
            errors.append('AG-04 needs text_comparison and explicit comparison_scope')
        records = [ids[r] for r in compared if r in ids and ids[r]['ref_kind'] == 'page']
        if any(p.get('source_kind') != obs.get('comparison_scope') for p in records):
            errors.append('AG-04 comparison_scope differs from the acquired source provenance')
        complete = bool(records) and all(p.get('observation_status') == 'complete' and not p.get('text_truncated') for p in records)
        if outcome == 'pass' and not complete:
            errors.append('AG-04 pass needs complete eligible compared text')
        if outcome == 'finding' and obs.get('markup_comparison_complete') is not True and not obs.get('markup_limitation'):
            errors.append('AG-04 needs complete relevant markup comparison or a scoped markup_limitation')
        if obs.get('markup_comparison_complete') is True and any(p.get('markup_comparison_available') is not True for p in records):
            errors.append('AG-04 packet does not support a complete relevant markup comparison; state a limitation')
        details['complete_comparison'] = complete and obs.get('markup_comparison_complete') is True
        support = compared
    elif check == 'AG-05':
        if not page_refs:
            errors.append('AG-05 needs acquired target entity page support')
        owned = {page_identity(u) for u in (packet.get('identity') or {}).get('same_as_urls', [])}
        for entity in obs.get('competing_entities', []):
            if page_identity(entity.get('url')) in owned or same_origin(entity.get('url'), origin):
                errors.append('the brand own origin/sameAs profile is not a competing entity')
            if not any(s['url'] == entity.get('url') and s.get('quote') and s['kind'] in ('inspected_page', 'knowledge_graph_page') for s in sources):
                errors.append('each competing entity needs its actually inspected distinguishing source')
        if outcome == 'finding' and not obs.get('competing_entities'):
            errors.append('AG-05 finding needs competing entity sources')
    elif check == 'AG-06':
        if not obs.get('business_applicability') or any(not q.get('platform') for q in queries):
            errors.append('AG-06 needs applicable named platform queries')
        missing = {norm(p) for p in obs.get('platforms_missing', [])}
        zero = {norm(q['platform']) for q in queries if q.get('matching_result_count') == 0}
        if outcome == 'finding' and (not missing or not missing <= zero):
            errors.append('AG-06 platforms_missing must be a subset of queried zero-matching platforms')
        if outcome == 'pass' and any(q.get('matching_result_count', 0) < 1 or not any(
                norm(s.get('platform')) == norm(q['platform']) and s.get('quote') for s in sources) for q in queries):
            errors.append('AG-06 pass needs actual matching outcomes and matching sources for each queried platform')
    # Page findings derive reach from validated support. Search advice reports query scope.
    if check in ('AG-02', 'AG-05', 'AG-06'):
        support = []
    elif check == 'AG-03':
        support = list(dict.fromkeys(support))
    return support, details, errors
