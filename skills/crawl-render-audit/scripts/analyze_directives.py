"""Indexing controls and technical signals, scoped to successfully sampled HTML."""
import re
from urllib.parse import urlsplit
from models import make_finding, skill_result
from url_identity import page_identity


def _snippet_action(severity):
    return {
        'summary': 'Confirm snippet suppression is intentional on this public page',
        'steps': ['Check whether the page relies on being quoted or previewed by assistants and search',
                  'Remove or raise max-snippet and restore image-preview only where suppression is unintended; '
                  'retain deliberate controls'],
        'priority': severity, 'effort': 'low',
        'expected_benefit': 'Restores snippet and preview eligibility for supporting consumers, without guaranteeing citations',
        'verification': 'Refetch HTML and headers and confirm the intended snippet policy'}


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
        if any(s in path for s in ('/facet/', '/filter/')):
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


_META_AGENTS = ('robots', 'googlebot', 'bingbot')
# Directive names that can lead an X-Robots-Tag value; anything else before a
# colon names the crawler the value applies to ("googlebot: noindex").
_HEADER_DIRECTIVES = frozenset({'max-snippet', 'max-image-preview', 'max-video-preview', 'unavailable_after'})


def _header_scope(header):
    """'X-Robots-Tag' for a value that applies to every crawler, or
    'X-Robots-Tag (name)' when the value names one crawler."""
    m = re.match(r'\s*([a-z][\w-]*)\s*:', header or '')
    if m and m.group(1) not in _HEADER_DIRECTIVES:
        return f'X-Robots-Tag ({m.group(1)})'
    return 'X-Robots-Tag'


def _token_controls(meta, header, token):
    """[(scope, detail)] for each control on one page that carries token."""
    found = []
    for agent, values in meta.items():
        if agent in _META_AGENTS and any(
                token in re.split(r'[\s,]+', v.lower()) or (token == 'noindex' and 'none' in re.split(r'[\s,]+', v.lower()))
                for v in values):
            found.append(('meta ' + agent, 'meta ' + agent))
    if re.search(r'(?<![\w-])' + token + r'(?![\w-])', header):
        found.append((_header_scope(header), 'X-Robots-Tag: ' + header))
    return found


def _snippet_controls(meta, header):
    """([(scope, detail)], hits) for max-snippet:0 and max-image-preview:none."""
    def hits_in(text):
        compact = re.sub(r'\s+', '', text.lower())
        return [h for h in ('max-snippet:0', 'max-image-preview:none')
                if (re.search(r'max-snippet:0(?![\d])', compact) if h == 'max-snippet:0' else h in compact)]
    found, hits = [], []
    for agent, values in meta.items():
        if agent in _META_AGENTS:
            page_hits = [h for v in values for h in hits_in(v)]
            if page_hits:
                found.append(('meta ' + agent, 'meta ' + agent))
                hits.extend(page_hits)
    header_hits = hits_in(header) if header else []
    if header_hits:
        found.append((_header_scope(header), 'X-Robots-Tag: ' + header))
        hits.extend(header_hits)
    return found, sorted(set(hits))


def _directive_finding(rule, severity, confidence, title, root_cause, observations, token_label):
    """One finding for a group of pages with the same control. Every affected
    requested and final URL is kept; each page's own controls are in evidence."""
    affected = sorted({u for page, _ in observations for u in (page.url, getattr(page, 'final_url', None)) if u})
    return make_finding(
        category='ai_discoverability', finding_type='defect', severity=severity, status='confirmed',
        confidence=confidence, title=title, root_cause=root_cause,
        evidence=[{'type': 'indexing_directive', 'description': detail, 'urls': [page.url]}
                  for page, detail in observations[:10]],
        suggested_action={
            'summary': f'Review whether {token_label} is intentional on these pages' if len(observations) > 1
            else f'Review whether {token_label} is intentional on this page',
            'steps': ['Confirm each page is intended for search discovery',
                      'Remove the directive only where unintended; preserve private/duplicate-page controls'],
            'priority': severity, 'effort': 'low',
            'expected_benefit': 'Restores eligibility within the affected crawler scope, without guaranteeing citations',
            'verification': f'Refetch HTML and headers and confirm the intended {token_label} policy'},
        provenance={'skill': 'crawl-render-audit', 'script': 'analyze_directives.py', 'rule_id': rule},
        affected_pages=affected)


def analyze_directives(artifacts, deadline):
    findings = []
    # Inner pages with the same control are reported together: grouped by token,
    # crawler scope (meta robots, meta googlebot, X-Robots-Tag and the crawler it
    # names) and severity. noindex and nosnippet, or a general and a
    # crawler-specific control, never share a group. Two URLs of one page (same
    # identity after redirects: url_identity) count once; different query
    # strings stay different pages.
    groups = {}
    seen = set()
    for p in artifacts.pages:
        if p.status_code != 200 or 'non_html_content' in p.warnings:
            continue
        meta = (p.features or {}).get('meta', {})
        header = (p.response_headers or {}).get('X-Robots-Tag', '').lower()
        # Intentional exclusions (internal search, pagination, facet/fragments) are standard practice
        if is_intentional_exclusion_url(p.url):
            continue
        identity = page_identity(getattr(p, 'final_url', None) or p.url)
        is_root = urlsplit(p.url).path.lower() in ("", "/") and not urlsplit(p.url).query

        for token, base_severity in [('noindex', 'critical'), ('nosnippet', 'high')]:
            # Agent-specific directives are scoped in evidence; do not infer all-bot exclusion.
            controls = _token_controls(meta, header, token)
            if not controls:
                continue
            detail = '; '.join(d for _, d in controls)
            if is_root:
                # A homepage control restricts the homepage. It does not show that
                # deeper pages are excluded; they are judged on their own.
                findings.append(_directive_finding(
                    token, base_severity, 0.98, f'Homepage carries {token} indexing controls',
                    f'The site homepage carries a {token} directive, which keeps the homepage itself out of search and '
                    f'assistant results that honour it. Deeper pages are judged on their own controls.',
                    [(p, detail)], token))
                continue
            key = (token, tuple(sorted({s for s, _ in controls})))
            if (key, identity) in seen:
                continue
            seen.add((key, identity))
            groups.setdefault(key, []).append((p, detail))

        controls, hits = _snippet_controls(meta, header)
        if controls:
            detail = '; '.join(d for _, d in controls) + ' (' + ', '.join(hits) + ')'
            if is_root:
                # On the home page the directive usually comes from a site-wide
                # template, on one inner page it limits only that page.
                findings.append(make_finding(
                    category='ai_discoverability', finding_type='defect', severity='high', status='confirmed',
                    confidence=0.95, title='Homepage suppresses snippet or preview eligibility',
                    root_cause='The observed ' + ' and '.join(hits) + ' directive keeps the page indexed but removes the snippet or preview a supporting consumer would quote, reducing the chance a clear fact is surfaced.',
                    evidence=[{'type': 'indexing_directive', 'description': detail, 'urls': [p.url]}],
                    suggested_action=_snippet_action('high'),
                    provenance={'skill': 'crawl-render-audit', 'script': 'analyze_directives.py', 'rule_id': 'snippet-suppression'},
                    affected_pages=[p.url]))
            else:
                key = ('snippet-suppression', tuple(sorted({s for s, _ in controls})))
                if (key, identity) not in seen:
                    seen.add((key, identity))
                    groups.setdefault(key, []).append((p, detail))

    for (rule, scopes), observations in groups.items():
        count = len(observations)
        scope_text = ', '.join(scopes)
        if rule == 'snippet-suppression':
            findings.append(make_finding(
                category='ai_discoverability', finding_type='defect', severity='low', status='confirmed',
                confidence=0.85,
                title='Sampled content page suppresses snippet or preview eligibility' if count == 1
                else f'{count} sampled content pages suppress snippet or preview eligibility',
                root_cause=f'The observed snippet controls ({scope_text}) keep these pages indexed but remove the '
                           'snippet or preview a supporting consumer would quote, reducing the chance a clear fact is '
                           'surfaced.',
                evidence=[{'type': 'indexing_directive', 'description': detail, 'urls': [page.url]}
                          for page, detail in observations[:10]],
                suggested_action=_snippet_action('low'),
                provenance={'skill': 'crawl-render-audit', 'script': 'analyze_directives.py', 'rule_id': 'snippet-suppression'},
                affected_pages=sorted({u for page, _ in observations
                                       for u in (page.url, getattr(page, 'final_url', None)) if u})))
            continue
        severity = 'medium' if rule == 'noindex' else 'low'
        findings.append(_directive_finding(
            rule, severity, 0.85,
            f'Sampled content page carries {rule} indexing controls' if count == 1
            else f'{count} sampled content pages carry {rule} indexing controls',
            f'The observed {rule} directive ({scope_text}) limits indexing or snippets for '
            + ('this page' if count == 1 else 'these pages') + ' within that crawler scope; intentional exclusions '
            'should be retained.',
            observations, rule))
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
