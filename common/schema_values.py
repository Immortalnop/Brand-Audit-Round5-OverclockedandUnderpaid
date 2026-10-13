"""Corrected limited donor value rules, with explicit schema.org context proof.

Supports the schema.org context, inline @base/@vocab, simple prefixes and
term/@id coercion. Unknown remote/term-scoped contexts are uninterpreted; no
context is fetched. These are property value checks, not full JSON-LD validation.
"""
import re
from collections.abc import Mapping
from datetime import date, datetime
from urllib.parse import urljoin, urlsplit

from money import markup_money

_DATES = {'priceValidUntil', 'validThrough', 'startDate', 'endDate', 'validFrom'}
_NUMBERS = {'price', 'lowPrice', 'highPrice'}
_IRIS = {'sameAs', 'url', 'logo', 'image'}
_BAD_IRI = re.compile(r'[\s\x00-\x1f<>"{}|\\^`]')
_DATE = re.compile(r'\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:?\d{2})?)?\Z')


def date_value_state(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return 'unsupported'
    try:
        if len(value) == 10:
            date.fromisoformat(value)
        else:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return 'invalid'
    return 'valid'


def _context(raw, inherited):
    ctx = dict(inherited, prefixes=dict(inherited['prefixes']), terms=dict(inherited['terms']),
               coercions=dict(inherited['coercions']))
    if raw is None:
        return ctx
    if isinstance(raw, (list, tuple)):
        for item in raw:
            ctx = _context(item, ctx)
        return ctx
    if isinstance(raw, str):
        if raw.rstrip('/') in ('http://schema.org', 'https://schema.org'):
            ctx.update(vocab='https://schema.org/', schema_context=True)
        else:
            ctx['supported'] = False
        return ctx
    if not isinstance(raw, Mapping):
        ctx['supported'] = False
        return ctx
    for key, value in raw.items():
        if key in ('@base', '@vocab'):
            if isinstance(value, str):
                ctx['base' if key == '@base' else 'vocab'] = urljoin(ctx['base'], value)
            else:
                ctx['supported'] = False
        elif key.startswith('@'):
            if key != '@version' or value != 1.1:
                ctx['supported'] = False
        elif isinstance(value, str):
            ctx['terms'][key] = value
            if value.endswith(('/', '#', ':')):
                ctx['prefixes'][key] = value
        elif isinstance(value, Mapping) and set(value) <= {'@id', '@type', '@prefix'} and isinstance(value.get('@id'), str):
            ctx['terms'][key] = value['@id']
            if value.get('@prefix') is True:
                ctx['prefixes'][key] = value['@id']
            if value.get('@type') in ('@id', '@vocab'):
                ctx['coercions'][key] = value['@type']
            elif '@type' in value:
                ctx['supported'] = False
        else:
            ctx['supported'] = False
    return ctx


def _expand(value, ctx, vocab=False):
    if not isinstance(value, str):
        return None
    if value in ctx['terms']:
        value = ctx['terms'][value]
    if ':' in value:
        prefix, rest = value.split(':', 1)
        if prefix in ctx['prefixes']:
            return ctx['prefixes'][prefix] + rest
        return value
    return (ctx['vocab'] + value if vocab and ctx['vocab'] else urljoin(ctx['base'], value))


def schema_local(iri):
    if not isinstance(iri, str):
        return None
    try:
        parts = urlsplit(iri)
    except ValueError:
        return None
    if parts.scheme not in ('http', 'https') or parts.netloc != 'schema.org':
        return None
    name = parts.fragment if parts.path in ('', '/') and parts.fragment else parts.path.strip('/')
    return name if name and '/' not in name and not parts.query else None


def iter_schema_nodes(value, document_url, inherited=None, depth=0):
    if depth > 40:
        return
    ctx = inherited or {'base': document_url, 'vocab': None, 'prefixes': {}, 'terms': {},
                        'coercions': {}, 'supported': True, 'schema_context': False}
    if isinstance(value, (list, tuple)):
        for child in value:
            yield from iter_schema_nodes(child, document_url, ctx, depth + 1)
    elif isinstance(value, Mapping):
        if '@context' in value and value['@context'] is None:
            ctx = dict(ctx, vocab=None, prefixes={}, terms={}, coercions={}, schema_context=False)
        else:
            ctx = _context(value.get('@context'), ctx)
        raw_types = value.get('@type', ())
        raw_types = raw_types if isinstance(raw_types, (list, tuple)) else [raw_types]
        types = {name for item in raw_types if (name := schema_local(_expand(item, ctx, vocab=True)))}
        if raw_types:
            yield value, ctx, types
        for key, child in value.items():
            if key != '@context' and isinstance(child, (Mapping, list, tuple)):
                yield from iter_schema_nodes(child, document_url, ctx, depth + 1)


def resolve_iri_value(value, context, key):
    if isinstance(value, Mapping) and set(value) == {'@id'}:
        value = value['@id']
        mode = '@id'
    else:
        mode = context['coercions'].get(key) or ('@id' if context['schema_context'] else None)
    if not mode or not isinstance(value, str):
        return None, 'unsupported'
    if not value or _BAD_IRI.search(value):
        return None, 'invalid'
    iri = _expand(value, context, vocab=mode == '@vocab')
    try:
        parts = urlsplit(iri)
        if not parts.scheme:
            return None, 'unsupported'
    except ValueError:
        return None, 'invalid'
    return iri, 'valid'  # Non-HTTP identifiers are not invalid JSON-LD.


def value_observations(page):
    invalid, limitations = [], []
    for node, ctx, types in iter_schema_nodes(page.jsonld_blocks, page.final_url or page.url):
        if not ctx['supported']:
            limitations.append('Custom/remote/scoped context not interpreted; no remote context fetched.')
            continue
        if not types:
            continue  # Never conflate a foreign namespace by its local name.
        for raw_key, value in node.items():
            key = schema_local(_expand(raw_key, ctx, vocab=True))
            if key in _NUMBERS:
                if isinstance(value, (Mapping, list, tuple)):
                    limitations.append('Unsupported structured numeric value for ' + key)
                elif markup_money(value) is None:
                    text = str(value).strip()
                    if not isinstance(value, bool) and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', text):
                        limitations.append('Numeric value exceeds supported processing range for ' + key)
                    else:
                        invalid.append((key, text[:100], 'a finite decimal/exponent number; boolean is not monetary'))
            elif key in _DATES:
                state = date_value_state(value)
                if state == 'invalid':
                    invalid.append((key, str(value)[:100], 'a valid calendar Date/DateTime in the supported ISO form'))
                elif state == 'unsupported':
                    limitations.append('Unsupported date form for ' + key)
            elif key == 'priceCurrency':
                if not isinstance(value, str) or not re.fullmatch('[A-Z]{3}', value):
                    invalid.append((key, str(value)[:100], 'a three-letter uppercase currency code format; ISO membership is not verified'))
            elif key in _IRIS:
                values = value if isinstance(value, (list, tuple)) else [value]
                for entry in values:
                    _, state = resolve_iri_value(entry, ctx, raw_key)
                    if state == 'invalid':
                        invalid.append((key, str(entry)[:100], 'a supported IRI value/coercion without invalid characters'))
                    elif state == 'unsupported':
                        limitations.append('Unsupported IRI value/context form for ' + key)
    return invalid, sorted(set(limitations))
