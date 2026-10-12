"""scoring.py -- one place that turns detector output into severity, confidence and
priority (A4, A5).

Design rules
------------
1. Severity is IMPACT. Each detector sets a severity for what it observed in its
   context (e.g. noindex on the homepage is critical, on one inner page medium).
   The scorer only adjusts it for SCOPE: a page-level problem seen on a single,
   non-key page is stepped down one tier. Severity is never adjusted for how much
   of the site the crawler reached -- a sample is a confidence question, not an
   impact question.
2. Confidence is EVIDENCE STRENGTH. Direct observations (robots.txt says X, the
   homepage carries noindex) keep the detector's confidence. Absence or prevalence
   claims ("0/40 pages have JSON-LD") are multiplied by sample_strength, which
   depends on how many relevant pages and how many distinct templates were
   examined -- not on the fraction of the site's URLs that were fetched, which
   would punish every large site.
3. Priority is DERIVED, never hard-coded by a detector:
       priority_score = impact[severity] x reach x confidence / effort_cost
   and the priority bucket follows the final severity, dropping one step only for
   a high-effort fix whose evidence is weak (confidence < 0.6). Ordering is
   severity first, priority_score within a severity (prioritize_findings.py), so a
   cheap low item never outranks a more impactful one.
Every finding carries a severity_rationale so a reader can see why.
"""
from check_catalog import meta_for

SEVERITY_ORDER = ('low', 'medium', 'high', 'critical')
IMPACT = {'critical': 8, 'high': 4, 'medium': 2, 'low': 1}
EFFORT_COST = {'low': 1, 'medium': 2, 'high': 3}
REACH = {'site-wide': 1.0, 'template': 0.6, 'page': 0.3}
KEY_PAGE_TYPES = {'home', 'product', 'contact', 'about', 'service', 'software'}
OFF_SITE_CATEGORIES = {'off_site_presence', 'corroboration'}
# Absence claims from this many content pages or fewer are capped at medium.
SMALL_SAMPLE_PAGES = 3


def _step(severity, delta):
    i = SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else 0
    return SEVERITY_ORDER[max(0, min(len(SEVERITY_ORDER) - 1, i + delta))]


def sample_strength(n_pages, n_templates):
    """How well a sample supports a site-level absence/prevalence claim. Ten
    relevant pages across three templates is treated as adequate."""
    if n_pages <= 0:
        return 0.4
    return round(max(0.4, min(1.0, n_pages / 10) * min(1.0, max(1, n_templates) / 3)), 3)


class ScoringContext:
    def __init__(self, content_page_count, templates_sampled, page_types, home_url,
                 key_urls=(), identity_confidence=None):
        self.content_page_count = max(0, int(content_page_count or 0))
        self.templates_sampled = max(0, int(templates_sampled or 0))
        self.page_types = dict(page_types or {})
        self.home_url = home_url
        self.key_urls = set(key_urls or ())
        self.identity_confidence = identity_confidence

    @classmethod
    def from_artifacts(cls, artifacts, identity_confidence=None):
        from check_helpers import content_pages
        from url_keys import intent_of
        pages = content_pages(artifacts, require_features=False)
        cov = artifacts.acquisition_metadata.get('coverage', {})
        return cls(len(pages), cov.get('templates_sampled', len(pages)),
                   {p.url: p.page_type for p in artifacts.pages}, artifacts.site_url,
                   [p.url for p in pages if intent_of(p.url) or p.page_type in KEY_PAGE_TYPES],
                   identity_confidence)

    def as_dict(self):
        return {'content_page_count': self.content_page_count, 'templates_sampled': self.templates_sampled,
                'page_types': self.page_types, 'home_url': self.home_url, 'key_urls': sorted(self.key_urls),
                'identity_confidence': self.identity_confidence}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get('content_page_count', 0), d.get('templates_sampled', 0), d.get('page_types', {}),
                   d.get('home_url'), d.get('key_urls', ()), d.get('identity_confidence'))


def _scope(finding, ctx):
    pages = list(finding.get('affected_pages') or [])
    if not pages:
        return 'site-wide'
    if ctx.home_url and any(p.rstrip('/') == ctx.home_url.rstrip('/') for p in pages):
        return 'site-wide'
    if ctx.content_page_count and len(pages) >= max(2, 0.5 * ctx.content_page_count):
        return 'site-wide'
    return 'template' if len(pages) >= 2 else 'page'


def apply_scoring(finding, ctx):
    """Mutates and returns the finding with final severity, confidence, priority,
    priority_score and severity_rationale."""
    check_id = finding.get('check_id') or (finding.get('provenance') or {}).get('rule_id') or ''
    meta = meta_for(check_id)
    # Idempotent: re-scoring (finalize_report.py after the agent stage) starts from
    # the detector's original values, never from an already-adjusted result.
    prior = finding.get('severity_rationale') or {}
    detector_severity = prior.get('detector_severity', finding['severity'])
    detector_confidence = prior.get('detector_confidence', finding.get('confidence', 0.5))
    # Site-level checks (robots, bot walls, llms.txt, identity ...) describe the
    # whole site even when evidence names one URL.
    scope = _scope(finding, ctx) if meta['scope_sensitive'] else 'site-wide'
    severity, adjustment = detector_severity, 'none'
    pages = list(finding.get('affected_pages') or [])
    if (meta['scope_sensitive'] and scope == 'page' and finding['status'] != 'insufficient_evidence'
            and not any(p in ctx.key_urls or ctx.page_types.get(p) in KEY_PAGE_TYPES for p in pages)):
        severity, adjustment = _step(detector_severity, -1), 'single non-key page: one tier lower'
    confidence = float(detector_confidence)
    strength = None
    if meta['absence_claim']:
        strength = sample_strength(ctx.content_page_count, ctx.templates_sampled)
        confidence = round(confidence * strength, 3)
        if ctx.content_page_count <= SMALL_SAMPLE_PAGES and SEVERITY_ORDER.index(severity) > SEVERITY_ORDER.index('medium'):
            # "0 of 1 pages has X" is a fact about one page, not about the site:
            # an absence claim from a tiny sample never ranks above medium.
            severity = 'medium'
            adjustment = (f'absence observed on only {ctx.content_page_count} content page(s): capped at medium'
                          if adjustment == 'none' else adjustment + f'; capped at medium ({ctx.content_page_count} page sample)')
    if finding.get('category') in OFF_SITE_CATEGORIES and ctx.identity_confidence is not None:
        # A6: identity confidence gates only the off-site findings that depend on it.
        confidence = round(min(confidence, max(0.3, ctx.identity_confidence)), 3)
    if finding['status'] == 'insufficient_evidence':
        severity = 'low'
    action = dict(finding.get('suggested_action') or {})
    effort = action.get('effort', 'medium')
    if effort not in EFFORT_COST:
        effort = 'medium'
    reach = REACH[scope]
    score = round(IMPACT[severity] * reach * max(confidence, 0.05) / EFFORT_COST[effort], 3)
    priority = severity
    if effort == 'high' and confidence < 0.6:
        priority = _step(severity, -1)
    if finding['status'] == 'insufficient_evidence':
        priority = 'low'
    action['priority'] = priority
    action['effort'] = effort
    action.setdefault('owner_role', meta['owner'])
    finding['suggested_action'] = action
    finding['severity'] = severity
    finding['confidence'] = confidence
    finding['priority_score'] = score
    finding['severity_rationale'] = {
        'gate': meta['gate'], 'detector_severity': detector_severity,
        'detector_confidence': detector_confidence, 'scope': scope,
        'prevalence': f"{len(pages)}/{ctx.content_page_count} sampled content pages" if pages else 'site-level observation',
        'templates_sampled': ctx.templates_sampled, 'adjustment': adjustment,
        'sample_strength': strength,
        'priority_formula': f"impact {IMPACT[severity]} x reach {reach} x confidence {confidence} / effort {EFFORT_COST[effort]}",
    }
    return finding


def priority_consistent(finding):
    """A5 validation: the action priority may differ from severity by at most one
    tier, and never sits above it."""
    sev, pri = finding.get('severity'), (finding.get('suggested_action') or {}).get('priority')
    if sev not in SEVERITY_ORDER or pri not in SEVERITY_ORDER:
        return False
    d = SEVERITY_ORDER.index(sev) - SEVERITY_ORDER.index(pri)
    return 0 <= d <= 1
