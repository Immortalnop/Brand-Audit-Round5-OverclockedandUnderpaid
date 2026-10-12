"""analyze_access.py -- does an automated client receive the site's content, or a
bot-protection interstitial?

Reads only the acquisition snapshot: per-page access verdicts from
common/access_guard.py, the robots.txt access verdict and challenged probe files.

Three findings, by where the wall sits:
  bot-challenge-robots   robots.txt / sitemap / llms.txt challenged. Crawlers read
                         these first; a challenged robots.txt is "unreachable",
                         which RFC 9309 crawlers treat as disallow-all. Confirmed:
                         it was observed directly.
  bot-challenge-sitewide the homepage itself (or every fetched page) is
                         challenged. Suspected, not confirmed: the firewall may
                         allowlist *verified* crawlers by IP range, which an
                         outside audit cannot prove either way.
  bot-challenge-rate     the first pages were served, later ones challenged or
                         rate-limited: per-client rate rules that a crawler
                         fetching several pages in a row will also hit.
"""
from models import skill_result, make_finding
from access_guard import VENDOR_HINTS


def _access(page):
    return ((page.features or {}).get('access') or {})


def analyze_access(artifacts, deadline):
    findings = []
    pages = list(artifacts.pages)
    robots_access = artifacts.robots_data.get('access') or {}
    probes = list(artifacts.acquisition_metadata.get('challenged_probes', ()))
    if artifacts.robots_data.get('status') == 'challenged':
        probes.insert(0, {'url': artifacts.normalized_origin + '/robots.txt',
                          'status': artifacts.robots_data.get('http_status')})
    challenged = [p for p in pages if _access(p).get('kind') in ('challenge', 'rate_limited')]
    served = [p for p in pages if p.status_code == 200 and _access(p).get('kind', 'ok') == 'ok']
    vendor = (robots_access.get('vendor') or next((_access(p).get('vendor') for p in challenged if _access(p).get('vendor')), None)
              or 'generic')
    hint = VENDOR_HINTS.get(vendor, VENDOR_HINTS['generic'])
    home = next((p for p in pages if p.url == artifacts.site_url), None)
    home_challenged = home is not None and _access(home).get('kind') in ('challenge', 'rate_limited')

    if probes:
        signals = '; '.join(robots_access.get('signals', [])[:3])
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='high', status='confirmed',
            confidence=0.9,
            title='robots.txt / discovery files are served behind a bot challenge',
            root_cause='Crawler discovery files returned a bot-protection challenge instead of their content'
                       + (f' (vendor: {vendor})' if vendor != 'generic' else ''),
            evidence=[{'type': 'access', 'description': f"{p['url']} returned a challenge (HTTP {p.get('status')})"
                       + (f'; signals: {signals}' if signals and i == 0 else ''), 'urls': [p['url']]}
                      for i, p in enumerate(probes[:4])],
            affected_pages=[p['url'] for p in probes],
            suggested_action={
                'summary': 'Exempt /robots.txt, /sitemap*.xml and /llms.txt from all bot challenges',
                'steps': ['Add a firewall/bot-management skip rule for /robots.txt, /sitemap*.xml and /llms.txt',
                          hint, 'Verify with a plain HTTP client that robots.txt returns 200 text/plain'],
                'priority': 'high', 'effort': 'low',
                'expected_benefit': 'Crawlers can read permissions and discover URLs again',
                'verification': 'curl -sI <site>/robots.txt returns 200 text/plain with no challenge markers'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_access.py', 'rule_id': 'bot-challenge-robots'}))

    if artifacts.robots_data.get('status') == 'rate_limited':
        # A 429 on robots.txt, the first request of the audit. One observation can
        # be transient, so this is suspected; if it persists, RFC 9309 crawlers
        # treat the whole site as disallowed.
        robots_url = artifacts.normalized_origin + '/robots.txt'
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='medium', status='suspected',
            confidence=0.6,
            title='robots.txt answered HTTP 429 (rate limited)',
            root_cause='The first request of the audit, for robots.txt, was refused with HTTP 429. Under RFC 9309 a '
                       'crawler that receives 429 for robots.txt treats the site as fully disallowed until the file '
                       'is reachable again.',
            evidence=[{'type': 'access', 'description': f"{robots_url} -> {'; '.join((robots_access.get('signals') or ['HTTP 429'])[:2])}",
                       'urls': [robots_url]}]
                     + ([{'type': 'access', 'description': f'homepage then answered HTTP {home.status_code}'
                          + (' with a challenge' if home_challenged else ''), 'urls': [home.url]}] if home is not None else []),
            affected_pages=[robots_url],
            suggested_action={
                'summary': 'Exempt /robots.txt from rate limiting and serve it as a fast, cacheable 200',
                'steps': ['Add a rate-limit and bot-management exemption for /robots.txt, /sitemap*.xml and /llms.txt',
                          hint, 'Re-test from a fresh client: the first request for /robots.txt must return 200 text/plain'],
                'priority': 'medium', 'effort': 'low',
                'expected_benefit': 'Crawlers get a stable permission verdict instead of assuming disallow-all',
                'verification': 'curl -sI <site>/robots.txt returns 200 from a client that has made no other request'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_access.py', 'rule_id': 'robots-rate-limited'}))

    if home_challenged or (challenged and not served):
        sample = ([home] if home_challenged else []) + [p for p in challenged if p is not home]
        sig = _access(sample[0]).get('signals', [])
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='high', status='suspected',
            confidence=0.75,
            title='Automated clients receive a bot challenge instead of the site content',
            root_cause='The homepage was answered with a bot-protection interstitial'
                       + (f' ({vendor})' if vendor != 'generic' else '')
                       + '. Unless the firewall allowlists verified crawlers by IP, search and AI crawlers store '
                         'the challenge page, not the site.',
            evidence=[{'type': 'access', 'description': f'{p.url} -> {"; ".join(_access(p).get("signals", [])[:3])}',
                       'urls': [p.url]} for p in sample[:5]],
            affected_pages=[p.url for p in sample],
            suggested_action={
                'summary': 'Allow verified search and AI crawlers through the bot-management layer',
                'steps': [hint,
                          'Check firewall logs for Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User, PerplexityBot '
                          'and Claude-SearchBot and confirm they receive HTTP 200 with real content',
                          'Return 429 with Retry-After (never 200 with challenge HTML) when you do need to slow a client'],
                'priority': 'high', 'effort': 'low',
                'expected_benefit': 'AI and search crawlers can read and cite the site',
                'verification': 'Firewall logs show 200 responses with full HTML for verified crawler user agents'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_access.py', 'rule_id': 'bot-challenge-sitewide'}))
    elif challenged and served:
        first_index = next(i for i, p in enumerate(pages) if p in challenged)
        findings.append(make_finding(
            category='ai_discoverability', finding_type='defect', severity='medium', status='confirmed',
            confidence=0.8,
            title='Deeper pages are challenged or rate-limited after a few requests',
            root_cause=f'{len(served)} page(s) were served normally, then {len(challenged)} later request(s) '
                       f'received a bot challenge or rate limit (first at request #{first_index + 1}). Crawlers that '
                       'fetch several pages in a row hit the same rule.',
            evidence=[{'type': 'access', 'description': f'{p.url} -> {"; ".join(_access(p).get("signals", [])[:3])}',
                       'urls': [p.url]} for p in challenged[:5]],
            affected_pages=[p.url for p in challenged],
            suggested_action={
                'summary': 'Relax per-client rate rules for verified crawlers',
                'steps': [hint, 'Set a crawl-delay in robots.txt if crawl rate is the concern, instead of challenging',
                          'Serve 429 with Retry-After rather than 200 with challenge HTML'],
                'priority': 'medium', 'effort': 'medium',
                'expected_benefit': 'Deeper pages stay fetchable for crawlers that respect crawl-delay',
                'verification': 'A paced crawl of 20+ pages receives no challenge responses'},
            provenance={'skill': 'crawl-render-audit', 'script': 'analyze_access.py', 'rule_id': 'bot-challenge-rate'}))

    return skill_result('crawl-render-audit', findings=findings,
                        metrics={'challenged_pages': len(challenged), 'served_pages': len(served),
                                 'challenged_probe_files': len(probes), 'vendor': vendor if (challenged or probes) else None})
