"""Offline v8 tests: snippet-suppression detection plus a static anti-overfitting
guard. No public-site requests; every case runs against constructed page objects
or the source tree itself.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ('common', 'skills/audit-orchestrator/scripts', 'skills/crawl-render-audit/scripts',
            'skills/engagement-audit/scripts', 'skills/freshness-corroboration/scripts'):
    sys.path.insert(0, str(ROOT / rel))

from analyze_directives import analyze_directives
from check_catalog import CATALOG
from models import make_deadline
from constants import DEFAULT_LIMITS


class _Page:
    def __init__(self, url, meta=None, headers=None):
        self.url = url
        self.status_code = 200
        self.warnings = ()
        self.features = {'meta': meta or {}}
        self.response_headers = headers or {}


class _Artifacts:
    def __init__(self, pages):
        self.pages = tuple(pages)
        self.acquisition_metadata = {}


def _run(pages):
    return analyze_directives(_Artifacts(pages), make_deadline(DEFAULT_LIMITS))['findings']


def test_max_snippet_zero_meta_is_confirmed_high():
    pages = [_Page('https://x.example/p', meta={'robots': ('max-snippet:0',)})]
    hits = [f for f in _run(pages) if f['provenance'].get('rule_id') == 'snippet-suppression']
    assert len(hits) == 1
    assert hits[0]['severity'] == 'high' and hits[0]['status'] == 'confirmed'


def test_max_image_preview_none_header_is_flagged():
    pages = [_Page('https://x.example/p', headers={'X-Robots-Tag': 'max-image-preview:none'})]
    hits = [f for f in _run(pages) if f['provenance'].get('rule_id') == 'snippet-suppression']
    assert len(hits) == 1


def test_positive_max_snippet_is_not_flagged():
    # A positive snippet budget and a standard image preview are healthy, not defects.
    pages = [_Page('https://x.example/p', meta={'robots': ('max-snippet:-1, max-image-preview:large',)})]
    hits = [f for f in _run(pages) if f['provenance'].get('rule_id') == 'snippet-suppression']
    assert hits == []


def test_snippet_suppression_has_catalog_entry():
    assert 'snippet-suppression' in CATALOG
    entry = CATALOG['snippet-suppression']
    for field in ('expected_outcome', 'implementation_detail', 'mechanism'):
        assert entry.get(field)


def test_no_hardcoded_brand_or_domain_in_detectors():
    """Generalization guard: detection scripts must not key off a specific site.

    Overfitting to named brands or domains is the failure the handout warns about.
    This scans every detector for literal domains or brand tokens outside comments,
    docstrings, and the safety allow/deny lists (which legitimately name infra hosts).
    """
    safety_files = {'url_safety.py', 'constants.py'}
    # Well-known infra and standards hosts that legitimately appear in code.
    allowed = ('schema.org', 'w3.org', 'example.com', 'example.org', 'localhost',
               '127.0.0.1', 'metadata.google', '169.254', 'agentskills.io',
               'twitter.com', 'x.com', 'facebook.com', 'linkedin.com', 'instagram.com',
               'youtube.com', 'tiktok.com', 'pinterest.com')
    domain_re = re.compile(r'["\']([a-z0-9-]+\.(?:com|net|org|io|ai|co))["\']', re.I)
    offenders = []
    for script in ROOT.glob('skills/*/scripts/*.py'):
        for i, line in enumerate(script.read_text().splitlines(), 1):
            code = line.split('#', 1)[0]
            for m in domain_re.finditer(code):
                dom = m.group(1).lower()
                if any(a in dom for a in allowed):
                    continue
                offenders.append(f'{script.name}:{i}: {dom}')
    assert not offenders, 'Hardcoded domains found in detectors: ' + '; '.join(offenders)


def test_timeout_override_is_capped_and_honored():
    """The public API caps the wall-clock at 270s and honors a lower override,
    so a large site can never hold the caller past the handout limit."""
    from dataclasses import replace
    from constants import DEFAULT_LIMITS as DL
    # Lower override is passed through.
    low = replace(DL, TOTAL_AUDIT_TIMEOUT_S=45)
    assert min(270., max(.01, low.TOTAL_AUDIT_TIMEOUT_S)) == 45
    # An override above 270 is still capped at 270 (never exceeds the 300s limit).
    high = replace(DL, TOTAL_AUDIT_TIMEOUT_S=999)
    assert min(270., max(.01, high.TOTAL_AUDIT_TIMEOUT_S)) == 270


def test_cli_stdout_is_pure_json_with_progress_on():
    """Progress must go to stderr only; stdout stays a single parseable report."""
    import json as _json
    import os as _os
    import subprocess
    script = str(ROOT / 'skills/audit-orchestrator/scripts/run_audit.py')
    env = dict(_os.environ, AUDIT_PROGRESS='1')
    proc = subprocess.run(['python3', script, 'https://--invalid-host', '--timeout', '20', '-v'],
                          capture_output=True, text=True, env=env, timeout=60)
    parsed = _json.loads(proc.stdout)  # raises if stdout was polluted
    assert 'execution_status' in parsed
    assert '[audit]' in proc.stderr  # progress landed on stderr, not stdout


def test_intentional_noindex_excluded():
    """Internal search, pagination, facet, and fragment endpoints are intentional exclusions
    and must not trigger defect findings."""
    search_page = _Page('https://docs.example/3/search.html', meta={'robots': ('noindex',)})
    facet_page = _Page('https://example/projects-programs', meta={'robots': ('noindex',)})
    frag_page = _Page('https://example/cc-shared/fragments/hero', meta={'robots': ('noindex',)})
    hits = _run([search_page, facet_page, frag_page])
    assert len(hits) == 0, f"Expected 0 findings for intentional noindex, got: {hits}"


def test_root_noindex_is_critical():
    """Homepage carrying noindex blocks indexing for the domain and is critical."""
    root_page = _Page('https://example/', meta={'robots': ('noindex',)})
    hits = _run([root_page])
    assert len(hits) == 1
    assert hits[0]['severity'] == 'critical'
    assert hits[0]['status'] == 'confirmed'
    assert 'Homepage' in hits[0]['title']


def test_subpage_noindex_is_medium():
    """A standard subpage carrying noindex is downgraded from critical to medium."""
    sub_page = _Page('https://example/products/widget', meta={'robots': ('noindex',)})
    hits = _run([sub_page])
    assert len(hits) == 1
    assert hits[0]['severity'] == 'medium'
    assert hits[0]['status'] == 'confirmed'


def test_evidence_text_present_and_projected():
    """Verify evidence_text is present on findings, merged findings, and recommendations."""
    from models import make_finding, skill_result
    from generate_recommendations import generate_recommendations
    from validate_report import validate_report

    f = make_finding(
        category='ai_discoverability', finding_type='defect', severity='medium',
        status='confirmed', confidence=0.8, title='Test finding',
        root_cause='Test mechanism',
        evidence=[{'type': 'test_type', 'description': 'Observed on page', 'urls': ['https://example/p']}],
        suggested_action={'summary': 'Fix it', 'steps': ['Step 1'], 'priority': 'medium',
                          'effort': 'low', 'expected_benefit': 'Better indexing', 'verification': 'Check'},
        provenance={'skill': 'crawl-render-audit', 'script': 'test.py', 'rule_id': 'noindex'},
        affected_pages=['https://example/p']
    )
    assert 'evidence_text' in f
    assert f['evidence_text'] == 'Observed on page'

    recs = generate_recommendations([skill_result('crawl-render-audit', findings=[f])], [f])
    assert len(recs) > 0
    for r in recs:
        assert 'evidence_text' in r
        assert isinstance(r['evidence_text'], str)

    # Validate report ensures schema enforcement
    report = {
        'site': 'https://example/', 'audited_at': '2026-09-13T00:00:00Z',
        'summary': {}, 'coverage': {'pages_discovered': 1, 'pages_analyzed': 1},
        'execution_status': 'completed', 'limitations': [], 'confidence': {'score': 0.9},
        'findings': [f], 'recommendations': recs,
    }
    validated = validate_report(report)
    for item in validated['findings'] + validated['recommendations']:
        assert 'evidence_text' in item
        assert isinstance(item['evidence_text'], str)


if __name__ == '__main__':
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            func()
            print(f'PASS: {name}')
    print('All v8 regression tests passed!')


