"""assess_freshness.py -- are the dates a site publishes current and consistent? (A9)

A missing date is never treated as proof of staleness, and an old date is never a
finding by itself: "founded 1998" or a 2006 entry in a reference list is supposed to
be old. Every rule below needs a date whose MEANING is known, either from a
machine-readable field or from the words around it (common/dates.py):

  expired-offer        an expiry date ("valid until", "offer ends", JSON-LD
                       priceValidUntil/validThrough/endDate) is in the past on a
                       page that is still served                  high / confirmed
  date-contradiction   the page states different dates for the same thing:
                       dateModified earlier than datePublished, JSON-LD
                       dateModified vs visible "updated" (>30 days), vs
                       article:modified_time (>30 days), vs sitemap lastmod
                       (>90 days), or a modification date in the future
                                                                 medium / confirmed
  stale-update-claim   the page itself says "last updated <date>" and that date is
                       more than 24 months old on a page whose facts change
                       (pricing, product, docs, FAQ, fees ...)    medium / suspected
  stale-copyright      the newest footer copyright year across the site is two or
                       more years old                             low / confirmed
  missing-article-dates article pages with no machine-readable published/modified
                       date (no JSON-LD date, meta or <time>)     medium / proactive
"""
from datetime import datetime, timezone, timedelta
from models import skill_result, make_finding, insufficient_evidence_result
from check_helpers import content_pages
from structured_data import iter_nodes, types_of
from dates import extract_visible_dates, copyright_years, parse_machine_date
from url_keys import intent_of

RULE_IDS = frozenset({'expired-offer', 'date-contradiction', 'stale-update-claim', 'stale-copyright',
                      'missing-article-dates'})

_VOLATILE_INTENTS = {'pricing', 'plans', 'price', 'products', 'product', 'shop', 'store', 'docs', 'doc', 'documentation',
                     'faq', 'faqs', 'help', 'support', 'fees', 'admission', 'admissions', 'menu', 'services',
                     'service', 'courses', 'course', 'programs', 'program', 'locations', 'location'}
_VOLATILE_TYPES = {'product', 'service', 'home', 'contact', 'software'}


def _meta(page, key):
    return next((v for v in ((page.features or {}).get('meta', {}) or {}).get(key, ()) if v and v.strip()), '')


def _jsonld_dates(page):
    out = {'datePublished': [], 'dateModified': [], 'expiry': []}
    for node in iter_nodes(page.jsonld_blocks):
        for key in ('datePublished', 'dateModified'):
            d = parse_machine_date(node.get(key)) if isinstance(node.get(key), str) else None
            if d:
                out[key].append(d)
        types = types_of(node)
        for key in ('priceValidUntil', 'validThrough') + (('endDate',) if types & {'Event', 'Offer', 'SaleEvent'} else ()):
            d = parse_machine_date(node.get(key)) if isinstance(node.get(key), str) else None
            if d:
                out['expiry'].append((key, d))
    return out


def _finding(rule, title, severity, status, confidence, root, evidence, pages, summary, steps, effort='low',
             ftype='defect'):
    return make_finding(
        category='freshness', finding_type=ftype, severity=severity, status=status, confidence=confidence,
        title=title, root_cause=root, evidence=evidence[:8], affected_pages=sorted(set(pages)),
        suggested_action={'summary': summary, 'steps': steps, 'priority': severity, 'effort': effort,
                          'expected_benefit': 'Assistants and readers see current, consistent dates',
                          'verification': 'Re-run the audit and confirm the dates listed in the evidence'},
        provenance={'skill': 'freshness-corroboration', 'script': 'assess_freshness.py', 'rule_id': rule})


def assess_freshness(facts, artifacts, deadline, today=None):
    today = today or datetime.now(timezone.utc).date()
    pages = content_pages(artifacts, require_features=False)
    lastmods = dict(artifacts.sitemap_data.get('lastmod', {}) or {})
    from update_signals import lastmod_quality
    if lastmod_quality(artifacts.sitemap_data or {})['problem'] == 'uniform':
        # A build-stamped lastmod records the deploy, not the page: comparing it
        # with dateModified would report the same root cause on every page.
        # sitemap-lastmod-unreliable reports it once instead.
        lastmods = {}
    expired, contradictions, stale_claims, missing_dates = [], [], [], []
    copyright = []
    dated_signals = 0
    for p in pages:
        visible = extract_visible_dates(p.visible_text or '')
        jd = _jsonld_dates(p)
        dated_signals += len(visible) + sum(len(v) for v in jd.values())
        # expired-offer
        if p.page_type != 'article':
            for d in visible:
                if d['context'] == 'expiry' and d['date'].year >= 2000 and d['date'] < today:
                    expired.append((p.url, f"visible '{d['raw']}' ({d['window'][:80]}) is in the past"))
        for key, d in jd['expiry']:
            if d < today:
                expired.append((p.url, f"JSON-LD {key} {d.isoformat()} is in the past"))
        # date-contradiction
        dm = max(jd['dateModified']) if jd['dateModified'] else None
        dp = min(jd['datePublished']) if jd['datePublished'] else None
        mm = parse_machine_date(_meta(p, 'article:modified_time') or _meta(p, 'og:updated_time'))
        vu = max((d['date'] for d in visible if d['context'] == 'update_claim' and d['precision'] == 'day'), default=None)
        sl = parse_machine_date(lastmods.get(p.url) or lastmods.get(p.final_url or '') or '')
        if dm and dp and dm < dp:
            contradictions.append((p.url, f"dateModified {dm} is earlier than datePublished {dp}"))
        if dm and vu and abs((dm - vu).days) > 30:
            contradictions.append((p.url, f"JSON-LD dateModified {dm} vs visible 'updated' {vu}"))
        if dm and mm and abs((dm - mm).days) > 30:
            contradictions.append((p.url, f"JSON-LD dateModified {dm} vs article:modified_time {mm}"))
        if dm and sl and abs((dm - sl).days) > 90:
            contradictions.append((p.url, f"JSON-LD dateModified {dm} vs sitemap lastmod {sl}"))
        for label, d in (('dateModified', dm), ('article:modified_time', mm), ('visible updated date', vu)):
            if d and d > today + timedelta(days=2):
                contradictions.append((p.url, f"{label} {d} is in the future"))
        # stale-update-claim
        intent = intent_of(p.url)
        if vu and (today - vu).days > 730 and (intent in _VOLATILE_INTENTS or p.page_type in _VOLATILE_TYPES):
            stale_claims.append((p.url, f"page states it was updated {vu} ({(today - vu).days // 30} months ago)"))
        # copyright
        footer = (p.features or {}).get('footer_text') or (p.visible_text or '')[-600:]
        years = [y for y in copyright_years(footer) if 1990 <= y <= today.year + 1]
        if years:
            copyright.append((p.url, max(years)))
        # missing-article-dates
        if p.page_type == 'article' and len((p.visible_text or '').split()) > 150:
            has_machine = bool(jd['datePublished'] or jd['dateModified'] or _meta(p, 'article:published_time')
                               or (p.features or {}).get('time_values'))
            if not has_machine:
                missing_dates.append(p.url)

    findings = []
    if expired:
        findings.append(_finding('expired-offer', 'Expired offers or validity dates are still published', 'high',
                                 'confirmed', 0.85,
                                 'Live pages state offer, price-validity or event end dates that have already passed',
                                 [{'type': 'date', 'description': d, 'urls': [u]} for u, d in expired],
                                 [u for u, _ in expired], 'Update or remove expired offers and validity dates',
                                 ['Update the offer or remove it from the live page',
                                  'Set priceValidUntil / validThrough to the real end date',
                                  'Automate expiry so ended offers are unpublished on schedule']))
    if contradictions:
        findings.append(_finding('date-contradiction', 'Pages publish contradictory dates', 'medium', 'confirmed',
                                 0.85, 'The same page states different publication/modification dates in different '
                                       'places, so freshness signals cannot be trusted',
                                 [{'type': 'date', 'description': d, 'urls': [u]} for u, d in contradictions],
                                 [u for u, _ in contradictions],
                                 'Derive every date signal from one source of truth',
                                 ['Output dateModified, the visible updated date and sitemap lastmod from the CMS '
                                  'last-modified time', 'Never set modification dates in the future']))
    if stale_claims:
        findings.append(_finding('stale-update-claim', 'Key pages say they were last updated years ago', 'medium',
                                 'suspected', 0.7,
                                 'Pages whose facts change (pricing, product, docs, FAQ) explicitly state an old '
                                 '"last updated" date',
                                 [{'type': 'date', 'description': d, 'urls': [u]} for u, d in stale_claims],
                                 [u for u, _ in stale_claims], 'Review these pages and refresh facts and date together',
                                 ['Review each fact on the page for accuracy',
                                  'Update the content and the "last updated" date together']))
    if copyright:
        newest = max(y for _, y in copyright)
        if newest <= today.year - 2:
            findings.append(_finding('stale-copyright', f'Footer copyright year is {newest}', 'low', 'confirmed', 0.9,
                                     f'The newest copyright year found across {len(copyright)} sampled page(s) is '
                                     f'{newest}, {today.year - newest} years ago',
                                     [{'type': 'date', 'description': f'(c) {y}', 'urls': [u]} for u, y in copyright[:3]],
                                     [u for u, _ in copyright], 'Render the copyright year dynamically',
                                     ['Generate the footer year from the current date or the last content update']))
    if missing_dates:
        findings.append(_finding('missing-article-dates', 'Articles carry no machine-readable dates', 'medium',
                                 'confirmed', 0.8,
                                 'Article pages have no datePublished/dateModified in JSON-LD, no article:published_time '
                                 'meta and no <time datetime>',
                                 [{'type': 'date', 'description': f'{len(missing_dates)} article page(s) without a machine-readable date',
                                   'urls': missing_dates[:10]}],
                                 missing_dates, 'Add machine-readable published and modified dates to articles',
                                 ['Add datePublished and dateModified to Article/BlogPosting JSON-LD',
                                  'Show the same dates visibly near the headline'],
                                 ftype='proactive_improvement'))
    if not dated_signals and not copyright and not findings:
        return insufficient_evidence_result(
            'freshness-corroboration',
            'No dated facts found; freshness cannot be assessed (absence is not proof of staleness).',
            metrics={'date_signals_found': 0})
    return skill_result('freshness-corroboration', findings=findings,
                        metrics={'date_signals_found': dated_signals, 'expired_items': len(expired),
                                 'date_contradictions': len(contradictions), 'stale_update_claims': len(stale_claims),
                                 'newest_copyright_year': max((y for _, y in copyright), default=None),
                                 'articles_without_dates': len(missing_dates)})
