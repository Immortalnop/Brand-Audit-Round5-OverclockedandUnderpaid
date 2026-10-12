"""Shared, network-free helpers for snapshot check modules."""
from collections import defaultdict
from check_catalog import get_entry, meta_for
from models import make_finding

# Pages whose body is not the site's real content are never analysed for content
# defects. bot_challenge / rate_limited (A1) are firewall interstitials; the others
# are incomplete or non-HTML responses.
EXCLUDED_WARNINGS = frozenset({'non_html_content', 'response_truncated_at_byte_budget',
                               'html_parse_incomplete', 'bot_challenge', 'rate_limited'})


def is_challenged(page):
    return bool({'bot_challenge', 'rate_limited'} & set(page.warnings or ()))


def content_pages(artifacts, require_features=True):
    """The single definition of 'a page whose content we can judge': HTTP 200,
    parsed, complete, and not a bot-protection interstitial."""
    return [p for p in artifacts.pages if p.status_code == 200
            and (not require_features or (p.features and p.features.get('observation_version') == 2))
            and not EXCLUDED_WARNINGS & set(p.warnings)]


def eligible_pages(artifacts):
    return content_pages(artifacts)


def grouped_evidence(pages, details, evidence_type='snapshot_observation', limit=10):
    """A16: one evidence line per distinct observation ('40 page(s): ...'), not one
    identical line per page."""
    by_detail = defaultdict(list)
    for p in pages:
        by_detail[details[p.url]].append(p.url)
    ordered = sorted(by_detail.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return [{'type': evidence_type,
             'description': (f'{len(urls)} page(s): {d}' if len(urls) > 1 else d),
             'urls': urls[:10]} for d, urls in ordered][:limit]


def numbered(steps):
    """Render action steps as one readable sentence: '1) ...; 2) ...'."""
    steps = [str(s).strip().rstrip('.') for s in steps if str(s).strip()]
    if len(steps) == 1:
        return steps[0] + '.'
    return '; '.join(f'{i}) {s}' for i, s in enumerate(steps, 1)) + '.'


def observation(check_id, title, pages, details, *, skill='crawl-render-audit',
                script='analyze_metadata.py', severity='low', confirmed=False, category=None):
    """Absence-based heuristics default to suspected, low-priority opportunities."""
    entry = get_entry(check_id)
    category = category or meta_for(check_id).get('category') or 'ai_discoverability'
    return make_finding(
        category=category, finding_type='defect' if confirmed else 'proactive_improvement',
        severity=severity, status='confirmed' if confirmed else 'suspected',
        confidence=.95 if confirmed else .6, title=title,
        # What was observed (root cause) is stated separately from why it matters
        # (the catalog mechanism, added by enrich_finding).
        root_cause=f"{title} on {len(pages)} sampled page(s); e.g. {details[pages[0].url]}",
        affected_pages=[p.url for p in pages],
        evidence=grouped_evidence(pages, details),
        suggested_action={'summary':entry['implementation_detail'],
                          'steps':[entry['implementation_detail']], 'priority':severity,
                          'effort':'medium' if check_id in ('http-transport','heavy-html','fetch-latency') else 'low',
                          'expected_benefit':entry['expected_outcome'],
                          'verification':'Repeat the affected observation and verify the intended behavior.'},
        provenance={'skill':skill, 'script':script, 'rule_id':check_id})
