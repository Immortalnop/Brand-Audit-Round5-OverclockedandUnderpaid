"""Shared JSON-LD normalization for raw and immutable acquisition artifacts."""
from collections.abc import Mapping

def normalize_type(value):
    return value.strip().rsplit('/', 1)[-1].rsplit('#', 1)[-1].rsplit(':', 1)[-1] if isinstance(value, str) else ''

def types_of(node):
    value = node.get('@type', ())
    return {normalize_type(v) for v in (value if isinstance(value, (list, tuple)) else [value]) if isinstance(v, str)}

def iter_nodes(value, depth=0):
    # JSON is bounded at acquisition; cap nesting too, including synthetic inputs.
    if depth > 40:
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_nodes(item, depth + 1)
    elif isinstance(value, Mapping):
        if '@type' in value:
            yield value
        for key, child in value.items():
            if key != '@context' and isinstance(child, (Mapping, list, tuple)):
                yield from iter_nodes(child, depth + 1)
