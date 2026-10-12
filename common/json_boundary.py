"""Bounded JSON contracts. Public inputs never use permissive JSON defaults.

JSON-LD uses the same grammar checks but reports duplicate keys and processor
limits separately from syntax errors. Numbers are supported to 100 significant
digits and adjusted decimal exponents from -100 to 100; no Decimal values escape
this boundary into snapshots or reports.
"""
import json
import math
import os
import tempfile
from decimal import Decimal, InvalidOperation

MAX_DEPTH = 40
MAX_MEMBERS = 10000
MAX_STRING = 200000
MAX_NODES = 300000


class JSONLimitError(ValueError):
    """Valid grammar outside this processor's documented bounds."""


class JSONAmbiguityError(ValueError):
    """Duplicate keys cannot be interpreted deterministically."""


class JSONSyntaxError(ValueError):
    """Non-JSON constants, as distinct from a numeric range limitation."""


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise JSONAmbiguityError("duplicate object key: " + key[:80])
        result[key] = value
    return result


def _constant(value):
    raise JSONSyntaxError("non-JSON numeric constant: " + value)


def _number(value):
    if len(value) > 128:
        raise JSONLimitError("number exceeds 128 characters")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise JSONLimitError("unsupported number") from exc
    if not number.is_finite() or len(number.as_tuple().digits) > 100 or not -100 <= number.adjusted() <= 100:
        raise JSONLimitError("number exceeds supported precision/exponent range")
    converted = float(number)
    if not math.isfinite(converted):
        raise JSONLimitError("number is outside finite range")
    return converted


def _integer(value):
    if len(value.lstrip('-')) > 100:
        raise JSONLimitError("integer exceeds 100 digits")
    return int(value)


def validate_tree(value, *, max_string=MAX_STRING, max_members=MAX_MEMBERS):
    """Validate decoded/programmatic JSON before hashing, sorting or rendering."""
    stack = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise JSONLimitError("JSON nesting or node limit exceeded")
        if item is None or isinstance(item, bool):
            continue
        if isinstance(item, str):
            if len(item) > max_string:
                raise JSONLimitError("JSON string limit exceeded")
            try:
                item.encode('utf-8')
            except UnicodeEncodeError as exc:
                raise ValueError("JSON contains an invalid Unicode surrogate") from exc
        elif isinstance(item, int):
            if item.bit_length() > 333:
                raise JSONLimitError("integer exceeds supported range")
        elif isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("nonfinite JSON number")
        elif isinstance(item, (list, dict)):
            if len(item) > max_members:
                raise JSONLimitError("JSON collection limit exceeded")
            if isinstance(item, dict):
                if any(not isinstance(key, str) for key in item):
                    raise ValueError("JSON object keys must be strings")
                stack.extend((key, depth + 1) for key in item)
                stack.extend((child, depth + 1) for child in item.values())
            else:
                stack.extend((child, depth + 1) for child in item)
        else:
            raise ValueError("unsupported JSON value type: " + type(item).__name__)
    return value


def loads(text, **bounds):
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant,
                           parse_float=_number, parse_int=_integer)
    except RecursionError as exc:
        raise JSONLimitError("JSON nesting limit exceeded") from exc
    return validate_tree(value, **bounds)


def read_json(path, limit, **bounds):
    with open(path, 'rb') as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise JSONLimitError(f"input is larger than {limit} bytes")
    text = raw.decode('utf-16') if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-8-sig')
    return loads(text, **bounds)


def atomic_write_text(path, text):
    """Replace only after a complete UTF-8 write succeeds."""
    path = os.path.abspath(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.report-', suffix='.tmp', dir=os.path.dirname(path))
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return path


def validate_report_shape(report):
    """Validate report contracts, leaving unrelated measurement metadata alone."""
    validate_tree(report)
    if not isinstance(report, dict):
        raise ValueError('the report must be a JSON object')
    def fields(obj, keys, kind, where, nullable=True):
        for key in keys:
            if key not in obj or (nullable and obj[key] is None):
                continue
            value = obj[key]
            valid = isinstance(value, kind)
            if kind is int:
                valid = valid and not isinstance(value, bool) and value >= 0
            if not valid:
                name = {dict: 'an object', str: 'a string', list: 'a list', int: 'a nonnegative integer'}[kind]
                raise ValueError(f'{where}.{key} must be {name}')
    def strings(obj, keys, where):
        fields(obj, keys, list, where)
        for key in keys:
            if obj.get(key) is not None and any(not isinstance(v, str) for v in obj[key]):
                raise ValueError(f'{where}.{key} must be a list of strings')
    def records(obj, keys, where):
        for key in keys:
            if key not in obj:
                continue
            value = obj[key]
            if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
                raise ValueError(f'{where}.{key} must be a list of objects')
    def probability(obj, keys, where):
        for key in keys:
            if key in obj and obj[key] is not None:
                value = obj[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    raise ValueError(f'{where}.{key} must be a finite number from 0 to 1')
    fields(report, ('coverage', 'summary', 'confidence', 'timing'), dict, 'report')
    fields(report, ('site', 'audited_at', 'execution_status', 'audit_id', 'snapshot_sha256',
                    'packet_sha256', 'code_version'), str, 'report')
    strings(report, ('warnings', 'limitations'), 'report')
    collections = ('findings', 'recommendations', 'top_actions', 'quick_wins', 'whats_working')
    records(report, collections, 'report')
    coverage = report.get('coverage') or {}
    fields(coverage, ('pages_analyzed', 'pages_discovered', 'pages_fetched', 'pages_fetched_attempted',
                      'pages_out_of_scope', 'pages_challenged', 'pages_partially_observed',
                      'sections_analyzed', 'sections_discovered'), int, 'report.coverage')
    fields(coverage, ('agent_stage',), dict, 'report.coverage')
    fields(coverage, ('agent_corroboration_stage', 'audited_url'), str, 'report.coverage')
    records(coverage, ('out_of_scope_pages',), 'report.coverage')
    confidence = report.get('confidence') or {}
    fields(confidence, ('level', 'limiting_factor'), str, 'report.confidence')
    fields(confidence, ('components', 'reasons'), dict, 'report.confidence')
    probability(confidence, ('score',), 'report.confidence')
    summary = report.get('summary') or {}
    fields(summary, ('total_findings', 'total_recommendations', 'critical', 'high', 'medium', 'low',
                     'proactive_improvements', 'insufficient_evidence_items'), int, 'report.summary')
    for collection in collections:
        seen = set()
        for index, item in enumerate(report.get(collection, [])):
            where = f'report.{collection}[{index}]'
            fields(item, ('id', 'finding_id', 'check_id', 'title', 'severity', 'status', 'category',
                          'finding_type', 'root_cause', 'priority', 'effort', 'impact', 'summary'), str, where)
            if item.get('id') is not None:
                if item['id'] in seen:
                    raise ValueError(f'duplicate {collection} ID: ' + item['id'][:80])
                seen.add(item['id'])
            fields(item, ('suggested_action', 'provenance', 'coverage'), dict, where)
            strings(item, ('affected_pages', 'check_ids', 'owner_roles', 'source_refs'), where)
            probability(item, ('confidence',), where)
            if collection == 'whats_working':
                fields(item, ('evidence',), str, where)
                evidence_items = []
            else:
                records(item, ('evidence',), where)
                evidence_items = item.get('evidence', [])
            for evidence in evidence_items:
                fields(evidence, ('description', 'type'), str, where + '.evidence')
                strings(evidence, ('urls',), where + '.evidence')
            action = item.get('suggested_action') or {}
            fields(action, ('summary', 'priority', 'effort', 'impact', 'expected_benefit',
                            'verification'), str, where + '.suggested_action')
            strings(action, ('steps', 'owner_roles'), where + '.suggested_action')
            fields(action, ('snippet',), dict, where + '.suggested_action')
    return report
