"""Evidence schema 1.1: bounded exports and final-content integrity.

The digest uses this project's sorted compact UTF-8 JSON encoding. It excludes
only the top-level packet_sha256 field; it is not an authenticity signature.
Export size uses the exact indented UTF-8 JSON plus newline written by the CLI.
"""
import hashlib
import json
import re

from json_boundary import validate_tree
from url_identity import page_identity

SCHEMA_VERSION = '1.1'
MAX_URL_CHARS = 2000
MAX_ALT_CHARS = 500
MAX_FOCUS_CHARS = 1500


def packet_digest(packet):
    validate_tree(packet)
    payload = {key: value for key, value in packet.items() if key != 'packet_sha256'}
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def emitted_json(value):
    validate_tree(value)
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'


def emitted_bytes(value):
    return len(emitted_json(value).encode('utf-8'))


def _is_url_key(key):
    return key in {'site', 'audited_url', 'url', 'requested_url', 'final_url', 'source_url',
                   'requested_about_url', 'aliases', 'pages', 'same_as_urls'}


def _bound(value, key, state):
    if isinstance(value, str):
        if _is_url_key(key) and len(value) > MAX_URL_CHARS:
            state['omitted'] += 1
            return None  # Never manufacture an identity by cutting a URL.
        cap = 4000 if key == 'text' else MAX_FOCUS_CHARS if key in ('opening_passage', 'focus_text') else 300 if key == 'value' else 500
        if len(value) > cap:
            state['truncated'] += 1
            return value[:cap]
        return value
    if isinstance(value, dict):
        return {k: _bound(v, k, state) for k, v in value.items()}
    if isinstance(value, list):
        cap = {'pages': 8, 'claims': 12, 'image_candidates': 8, 'aliases': 5,
               'same_as_urls': 10, 'source_refs': 8, 'fact_keywords': 12,
               'page_evidence_ids': 8, 'limitations': 16}.get(key, 20)
        if len(value) > cap:
            state['omitted'] += len(value) - cap
        out = [_bound(v, key, state) for v in value[:cap]]
        return [v for v in out if v is not None]
    return value


def _page_urls(page):
    return [u for u in [page.get('requested_url'), page.get('final_url'), *(page.get('aliases') or [])]
            if isinstance(u, str)]


def reconcile_support(packet):
    pages = packet['pages']
    by_id = {p['evidence_id']: p for p in pages}
    packet['claims'] = [c for c in packet['claims'] if c.get('page_evidence_id') in by_id and
                        page_identity(c.get('source_url')) in {page_identity(u) for u in _page_urls(by_id[c['page_evidence_id']])}]
    for image in packet['image_candidates']:
        image['page_evidence_ids'] = [ref for ref in image.get('page_evidence_ids', []) if ref in by_id]
        image['unexported_page_count'] = sum(not any(page_identity(url) == page_identity(u)
                                             for p in pages for u in _page_urls(p)) for url in image.get('pages', []))
    packet['identity']['source_refs'] = [r for r in packet['identity'].get('source_refs', []) if r in by_id]
    focus = (packet.get('focus') or {}).get('ag01')
    if focus and focus.get('page_ref') not in by_id:
        focus.update(assessable=False, opening_complete=False, page_ref=None, opening_passage='')
        reason = 'Selected opening support was omitted from the final packet.'
        if reason not in focus.setdefault('limitations', []):
            focus['limitations'].append(reason)
    budget = packet['budget']
    budget.pop('packet_bytes', None)
    budget.update(pages_selected=len(pages), pages_omitted=max(0, budget.get('pages_eligible', 0) - len(pages)),
                  pages_text_truncated=sum(p.get('text_truncated') is True for p in pages),
                  claims_selected=len(packet['claims']), images_selected=len(packet['image_candidates']))
    packet['ready_for_assessment'] = bool(pages)


def nonready_packet(audit_id, snapshot_sha256, reason, site=None):
    packet = {'schema_version': SCHEMA_VERSION, 'audit_id': audit_id, 'snapshot_sha256': snapshot_sha256,
              'site': site if isinstance(site, str) and len(site) <= MAX_URL_CHARS else None,
              'ready_for_assessment': False, 'pages': [], 'claims': [], 'image_candidates': [],
              'identity': {'source_refs': []}, 'budget': {'pages_eligible': 0, 'pages_selected': 0,
              'pages_omitted': 0, 'claims_selected': 0, 'images_selected': 0},
              'limitations': [str(reason)[:500]]}
    packet['packet_sha256'] = packet_digest(packet)
    return packet


def fit_packet(packet, limit):
    """Bound all source fields, fit deterministically, reconcile, then seal."""
    state = {'truncated': 0, 'omitted': 0}
    packet = _bound(packet, '', state)
    packet.pop('packet_sha256', None)
    pages = packet['pages']
    packet['pages'] = [p for p in pages if p.get('requested_url') and p.get('final_url')]
    for page in packet['pages']:
        if len(page.get('text', '')) < page.get('text_chars_observed', 0):
            page['text_truncated'] = True
    packet['claims'] = [c for c in packet['claims'] if c.get('source_url')]
    packet['image_candidates'] = [i for i in packet['image_candidates'] if i.get('url')]
    budget = packet['budget']
    budget['metadata_truncated'] = budget.get('metadata_truncated', 0) + state['truncated']
    budget['metadata_omitted'] = budget.get('metadata_omitted', 0) + state['omitted']
    if any(state.values()):
        note = 'Source metadata was bounded; overlong URLs were omitted rather than cut.'
        if note not in packet['limitations']:
            packet['limitations'].append(note)
    def seal_size():
        reconcile_support(packet)
        packet['packet_sha256'] = packet_digest(packet)
        return emitted_bytes(packet)
    while seal_size() > limit:
        focus_ref = ((packet.get('focus') or {}).get('ag01') or {}).get('page_ref')
        expendable = [p for p in reversed(packet['pages']) if p['evidence_id'] != focus_ref and len(p['text']) > 500]
        if expendable:
            page = expendable[0]
            page['text'] = page['text'][:max(500, len(page['text']) // 2)]
            page['text_truncated'] = True
        elif len(packet['pages']) > 1:
            index = next((i for i in range(len(packet['pages']) - 1, -1, -1)
                          if packet['pages'][i]['evidence_id'] != focus_ref), len(packet['pages']) - 1)
            packet['pages'].pop(index)
        else:
            packet = nonready_packet(packet.get('audit_id'), packet.get('snapshot_sha256'),
                                     'Required evidence cannot fit within the packet byte limit.', packet.get('site'))
            if emitted_bytes(packet) > limit:
                raise ValueError('packet byte limit is too small for a non-ready marker')
            return packet
        budget['shrunk_to_fit'] = True
    # Generated packets go through the same registry integrity check as merge.
    validate_registry(packet)
    return packet


def validate_registry(packet):
    """Validate final record kinds, parent/source identity and every reference."""
    validate_tree(packet)
    kinds = {'pages': ('evidence_id', 'E', 8), 'claims': ('claim_id', 'C', 12),
             'image_candidates': ('image_id', 'I', 8)}
    registry = {}
    for collection, (field, prefix, cap) in kinds.items():
        records = packet.get(collection)
        if not isinstance(records, list) or len(records) > cap:
            raise ValueError(f'packet.{collection} must be a bounded list')
        for record in records:
            ref = record.get(field) if isinstance(record, dict) else None
            if not isinstance(ref, str) or not re.fullmatch(prefix + r'\d{3}', ref):
                raise ValueError(f'packet.{collection} needs a valid {prefix} reference')
            if ref in registry:
                raise ValueError('duplicate evidence ID: ' + ref)
            registry[ref] = record
    by_page = {p['evidence_id']: p for p in packet['pages']}
    for page in by_page.values():
        if not isinstance(page.get('text'), str) or not isinstance(page.get('focus_text', ''), str):
            raise ValueError('exported page text must be a string')
    for claim in packet['claims']:
        parent = claim.get('page_evidence_id')
        if not isinstance(parent, str):
            raise ValueError('claim parent must be an exported page reference')
        page = by_page.get(parent)
        if not page or page_identity(claim.get('source_url')) not in {page_identity(u) for u in _page_urls(page)}:
            raise ValueError('claim parent/source does not resolve to acquired page support')
    for image in packet['image_candidates']:
        refs = image.get('page_evidence_ids', [])
        if not isinstance(refs, list) or any(not isinstance(r, str) or r not in by_page for r in refs):
            raise ValueError('image page reference does not resolve to an exported page')
        for ref in refs:
            if not any(page_identity(u) == page_identity(v) for u in _page_urls(by_page[ref]) for v in image.get('pages', [])):
                raise ValueError('image page reference is unrelated to its acquired association')
    identity = packet.get('identity')
    if not isinstance(identity, dict) or not isinstance(identity.get('source_refs', []), list) or any(
            not isinstance(r, str) or r not in by_page for r in identity.get('source_refs', [])):
        raise ValueError('identity source reference is not an exported page')
    for key in ('name', 'entity_type', 'ambiguity_type'):
        if identity.get(key) is not None and not isinstance(identity[key], str):
            raise ValueError('packet identity ' + key + ' must be a string')
    for key in ('aliases', 'same_as_urls'):
        if key in identity and (not isinstance(identity[key], list) or any(not isinstance(v, str) for v in identity[key])):
            raise ValueError('packet identity ' + key + ' must be a list of strings')
    if 'focus' in packet and not isinstance(packet['focus'], dict):
        raise ValueError('packet.focus must be an object')
    focus = (packet.get('focus') or {}).get('ag01')
    if focus is not None and not isinstance(focus, dict):
        raise ValueError('packet.focus.ag01 must be an object')
    if focus:
        for key in ('assessable', 'opening_complete'):
            if not isinstance(focus.get(key), bool):
                raise ValueError('focused opening assessment/completeness must be booleans')
        ref = focus.get('page_ref')
        if ref is not None and not isinstance(ref, str):
            raise ValueError('focused opening page_ref must be a string')
        passage = focus.get('opening_passage')
        if not isinstance(passage, str) or len(passage) > MAX_FOCUS_CHARS:
            raise ValueError('focused opening passage must be bounded text')
        if ref in by_page and passage != by_page[ref].get('focus_text', ''):
            raise ValueError('focused opening does not match its allocated page passage')
    if focus and focus.get('assessable') is True and focus.get('page_ref') not in by_page:
        raise ValueError('focused opening reference is not an exported page')
    for page in by_page.values():
        if len(page.get('text', '')) + len(page.get('focus_text', '')) > 4000:
            raise ValueError('page and focused text exceed the shared page character allowance')
    return registry
