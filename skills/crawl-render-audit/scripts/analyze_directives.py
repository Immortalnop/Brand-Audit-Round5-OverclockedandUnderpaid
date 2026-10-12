"""Indexing controls and technical signals, scoped to successfully sampled HTML.

Agent-specific meta robots tags are honoured for the classic search agents and
for the AI agents in common/constants.AI_AGENTS (A12), e.g.
<meta name="oai-searchbot" content="noindex">.
"""
import re
from urllib.parse import urlsplit
from models import make_finding, skill_result
from check_helpers import is_challenged
from constants import AI_AGENTS

_DIRECTIVE_AGENTS = frozenset({'robots', 'googlebot', 'bingbot'} | {a.lower() for a, _ in AI_AGENTS})


def is_intentional_exclusion_url(url: str) -> bool:
    """Detect URLs where noindex/nosnippet is standard, intentional industry practice
    (internal search, pagination, facet filters, component fragments, utility endpoints).
    Such URLs should not be flagged as defects on well-run sites."""
    try:
        p = urlsplit(url)
        path = (p.path or "").lower()
        query = (p.query or "").lower()

        # Never treat root / home page as an intentional exclusion
        if path in ("", "/") and not query:
            return False

        # Search patterns (filenames, paths, query params)
        if any(s in path for s in ('/search', 'search.html', 'search.php', '/find', 'search-results', 'search_results')):
            return True
        if re.search(r'(^|[?&])(q|query|s|search)=', query):
            return True

        # Pagination & facet / listing filters
        if re.search(r'/(page|p)/\d+', path) or re.search(r'(^|[?&])(page|p|sort|order|filter|facet)=', query):
            return True
        if any(s in path for s in ('/projects-programs', '/facet/', '/filter/')):
            return True

        # Fragment / component / modal / partial endpoints
        if any(s in path for s in ('/fragments/', '/fragment/', '/modals/', '/modal/', '/aside/', '/embed/', '/partials/')):
            return True

        # Auth & utility endpoints
        if any(s in path for s in ('/login', '/logout', '/signin', '/signup', '/cart', '/checkout', '/admin')):
            return True
    except Exception:
        pass
    return False


def analyze_directives(artifacts, deadline):
    findings = []
    for p in artifacts.pages:
        if p.status_code != 200 or 'non_html_content' in p.warnings or is_challenged(p):
            continue
        meta = (p.features or {}).get('meta', {})
        directives = ' '.join(meta.get('robots', ())).lower()
        header = next((str(v) for k, v in dict(p.response_headers or {}).items() if str(k).lower() == 'x-robots-tag'), '').lower()

        intentional = is_intentional_exclusion_url(p.url)
        p_path = urlsplit(p.url).path.lower()
        is_root = p_path in ("", "/") and not urlsplit(p.url).query

        for token, base_severity in [('noindex', 'critical'), ('nosnippet', 'high')]:
            # Agent-specific directives are scoped in evidence; do not infer all-bot exclusion.
            matched = []
            for agent, values in meta.items():
                if agent in _DIRECTIVE_AGENTS and any(
                    (token in re.split(r'[\s,]+', v.lower()) or (token == 'noindex' and 'none' in re.split(r'[\s,]+', v.lower())))
                    for v in values
                ):
                    matched.append('meta ' + agent)
            if re.search(r'(?<![\w-])' + token + r'(?![\w-])', header):
                matched.append('X-Robots-Tag: ' + header)
            if matched:
                # Intentional exclusions (internal search, pagination, facet/fragments) are standard practice
                if intentional:
                    continue

                if is_root:
                    severity = base_severity
                    conf = 0.98
                    title = f'Homepage carries {token} indexing controls'
                    root_cause = f'The site homepage carries a {token} directive, limiting search and assistant indexing for the entire site.'
                else:
                    severity = 'medium' if base_severity == 'critical' else 'low'
                    conf = 0.85
                    title = f'Sampled content page carries {token} indexing controls'
                    root_cause = f'The observed {token} directive limits indexing or snippets for this page; intentional exclusions should be retained.'

                findings.append(make_finding(
                    category='ai_discoverability', finding_type='defect', severity=severity, status='confirmed', confidence=conf,
                    title=title, root_cause=root_cause,
                    evidence=[{'type': 'indexing_directive', 'description': '; '.join(matched), 'urls': [p.url]}],
                    suggested_action={
                        'summary': f'Review whether {token} is intentional on this page',
                        'steps': ['Confirm the page is intended for search discovery', 'Remove the directive only if unintended; preserve private/duplicate-page controls'],
                        'priority': severity, 'effort': 'low',
                        'expected_benefit': 'Restores eligibility within the affected crawler scope, without guaranteeing citations',
                        'verification': f'Refetch HTML and headers and confirm the intended {token} policy'
                    },
                    provenance={'skill': 'crawl-render-audit', 'script': 'analyze_directives.py', 'rule_id': token},
                    affected_pages=[p.url]
                ))

        # Snippet-length suppression
        combined = directives + ' ' + header
        snippet_hits = []
        if re.search(r'max-snippet\s*:\s*0(?![\d])', combined):
            snippet_hits.append('max-snippet:0')
        if re.search(r'max-image-preview\s*:\s*none', combined):
            snippet_hits.append('max-image-preview:none')
        if snippet_hits and not intentional:
            where = []
            for agent, values in meta.items():
                if agent in _DIRECTIVE_AGENTS and any(
                    ('max-snippet:0' in re.sub(r'\s+', '', v.lower()) or 'max-image-preview:none' in re.sub(r'\s+', '', v.lower()))
                    for v in values
                ):
                    where.append('meta ' + agent)
            if header and ('max-snippet:0' in re.sub(r'\s+', '', header) or 'max-image-preview:none' in re.sub(r'\s+', '', header)):
                where.append('X-Robots-Tag: ' + header)
            sev = 'high'
            findings.append(make_finding(
                category='ai_discoverability', finding_type='defect', severity=sev, status='confirmed', confidence=0.95,
                title='Sampled page suppresses snippet or preview eligibility',
                root_cause='The observed ' + ' and '.join(snippet_hits) + ' directive keeps the page indexed but removes the snippet or preview a supporting consumer would quote, reducing the chance a clear fact is surfaced.',
                evidence=[{'type': 'indexing_directive', 'description': '; '.join(where) or '; '.join(snippet_hits), 'urls': [p.url]}],
                suggested_action={
                    'summary': 'Confirm snippet suppression is intentional on this public page',
                    'steps': ['Check whether the page relies on being quoted or previewed by assistants and search', 'Remove or raise max-snippet and restore image-preview only where suppression is unintended; retain deliberate controls'],
                    'priority': sev, 'effort': 'low',
                    'expected_benefit': 'Restores snippet and preview eligibility for supporting consumers, without guaranteeing citations',
                    'verification': 'Refetch HTML and headers and confirm the intended snippet policy'
                },
                provenance={'skill': 'crawl-render-audit', 'script': 'analyze_directives.py', 'rule_id': 'snippet-suppression'},
                affected_pages=[p.url]
            ))
    # Client transport evidence cannot establish an independently reproduced site defect.
    failures=[]
    for p in artifacts.pages:
        if p.status_code is None:
            reason=next((w[6:] for w in p.warnings if w.startswith('fetch_')),None)
            if reason in {'timeout','failed','tls_certificate_error','tls_handshake_error','tls_protocol_error','tls_configuration_error','connection_error','dns_error'}:
                failures.append({'url':p.url,'reason':reason})
    failures.extend(artifacts.acquisition_metadata.get('probe_failures',()))
    diagnostics=artifacts.acquisition_metadata.get('transport_diagnostics',())
    for failure in failures:
        reason=failure['reason']
        tls=reason=='tls_certificate_error'
        detail=[dict(d) for d in diagnostics if d.get('url')==failure['url']]
        findings.append(make_finding(category='ai_discoverability',finding_type='proactive_improvement',
            severity='low',status='insufficient_evidence',confidence=.3,
            title='TLS verification prevented this audit from reading a URL' if tls else 'Acquisition could not assess a URL',
            root_cause='This audit client encountered '+reason+'. Local trust, network routing and server causes are not independently distinguished; crawler permission remains unknown when robots cannot be read.',
            evidence=[{'type':'transport_limitation','description':'Acquisition outcome: '+reason+
                       '. Verified same-client attempt outcomes: '+str(list(failure.get('attempt_outcomes',())))+
                       '. This is not independent reproduction of a site defect.',
                       'urls':[failure['url']], 'transport_diagnostics':detail}],
            suggested_action={'summary':'Compare the exact failure with the working client and repair the confirmed cause',
                'steps':['Inspect coverage.transport_diagnostics for verification code, phase and runtime details',
                         'Compare Python trust roots and direct routing with the successful client',
                         'If required, configure an administrator-approved CA bundle using AUDIT_CA_BUNDLE; never disable verification',
                         'Rerun the audit and inspect robots rules only after verified retrieval succeeds'],
                'priority':'low','effort':'medium','expected_benefit':'Restores reliable audit evidence when the local or remote cause is resolved',
                'verification':'A verified robots GET succeeds, or repeated exact failure remains an explicit limitation'},
            provenance={'skill':'crawl-render-audit','script':'analyze_directives.py','rule_id':'tls-health' if tls else 'fetch-failure'}))
    return skill_result('crawl-render-audit',findings=findings)
