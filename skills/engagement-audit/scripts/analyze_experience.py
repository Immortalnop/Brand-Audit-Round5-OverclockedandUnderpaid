"""Calibrated UX checks over observed HTML, never claims measured bounce or layout."""
import re
from urllib.parse import urljoin,urlsplit
from models import make_finding,skill_result
from check_helpers import page_share


def _page_key(url):
    """Scheme, host and path without query, fragment or trailing slash."""
    try:parts=urlsplit(url or '')
    except ValueError:return url or ''
    return f"{parts.scheme}://{(parts.hostname or '').lower()}{parts.path.rstrip('/')}"


def _alternates(page):
    """Page keys this page names as its own language alternates (hreflang)."""
    return {_page_key(urljoin(page.final_url or page.url,h.get('href',''))) for h in page.features.get('hreflang') or ()
            if h.get('href')}


def shared_title_pages(pages):
    """Pages whose title another, different page also uses. Two URLs of one page
    (the same path with another query string) and language alternates that name
    each other through hreflang are one page here, not two."""
    groups={}
    for p in pages:
        if p.title:groups.setdefault(p.title,[]).append(p)
    out=[]
    for group in groups.values():
        distinct=[]
        for p in group:
            key,alts=_page_key(p.final_url or p.url),_alternates(p)
            if not any(key==k or key in a or k in alts for k,a in distinct):distinct.append((key,alts))
        if len(distinct)>1:out.extend(group)
    return out

def analyze_experience(artifacts,deadline):
    pages=[p for p in artifacts.pages if p.status_code==200 and 'html_parse_incomplete' not in p.warnings and p.features and 'response_truncated_at_byte_budget' not in p.warnings and 'non_html_content' not in p.warnings]
    out=[];warnings=[]
    def add(rule,title,pages,detail,steps,severity='low',defect=False,confidence=.7):
        if not pages:return
        out.append(make_finding(category='engagement',finding_type='defect' if defect else 'proactive_improvement',severity=severity,status='confirmed' if defect else 'suspected',confidence=confidence,
            title=title,root_cause=detail,evidence=[{'type':'html_observation','description':detail,'urls':[p.url for p in pages]}],
            suggested_action={'summary':steps[0],'steps':steps,'priority':severity,'effort':'low','expected_benefit':'Improves orientation, readability or the relevant next step when the observed issue affects visitors','verification':'Inspect the affected pages on mobile and desktop; re-crawl after changes'},
            provenance={'skill':'engagement-audit','script':'analyze_experience.py','rule_id':rule}))
    add('viewport','Pages lack a mobile viewport declaration',[p for p in pages if not p.features['viewport']], 'No viewport declaration was observed; actual layout behavior requires visual verification.', ['Add an appropriate responsive viewport declaration','Verify that layout reflows and remains readable'],'medium',True,.95)
    add('zoom','Viewport declarations restrict user zoom',[p for p in pages if any(re.search(r'user-scalable\s*=\s*no|maximum-scale\s*=\s*1(?:\.0)?(?:\s*,|$)',v,re.I) for v in p.features['viewport'])], 'The observed viewport configuration restricts zoom.', ['Remove unnecessary zoom restrictions','Verify pinch zoom and readable text'],'medium',True,.95)
    add('h1','Pages have no primary H1 heading',[p for p in pages if not p.features['h1_count'] and len(p.visible_text)>100], 'No H1 was found on these sampled pages.', ['Add a descriptive primary heading where a clear page title is missing'])
    add('scannability','Long pages lack subsection headings',[p for p in pages if len(p.visible_text.split())>800 and not p.features['subheadings']], 'Pages exceed 800 words without observed subsection headings.', ['Divide long content into meaningful sections with descriptive headings'])
    add('long-paragraphs','Dense paragraphs may obscure key answers',[p for p in pages if sum(p.features['paragraph_lengths'])>2000 and sum(n>600 for n in p.features['paragraph_lengths'])>len(p.features['paragraph_lengths'])*.4], 'More than 40% of paragraphs exceed 600 characters on substantial pages.', ['Review dense passages and split by topic','Use lists or tables where appropriate'])
    add('duplicate-titles','Different sampled URLs share page titles',shared_title_pages(pages), 'Multiple sampled URLs share the same title; verify canonical duplicates before editing.', ['Give distinct content pages descriptive, distinct titles','Preserve intentional canonical variants'])
    add('missing-alt','Images lack alt attributes',[p for p in pages if p.features['missing_alt']>=3], 'At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.', ['Describe informative images and keep decorative alt text empty','Repeat essential image-only facts in nearby text'])
    # Overlays and cookie banners are judged by analyze_overlays.py.
    add('hash-routing','Navigation uses client-only route fragments',[p for p in pages if sum(h.startswith(('#/','#!')) for h,t in p.features['anchors'])>=2], 'Route fragments are not sent in HTTP requests. Browser deep links may still work; raw-HTML retrieval may lose destination-specific content.', ['Verify direct arrival and raw HTML for each destination','Prefer server-resolvable paths where route-specific content needs indexing'])
    # Only an email subscription form (email field, signup wording, no password;
    # html_features.is_signup_form) means the site sends email worth summarizing.
    # Contact, search and login forms also hold email fields and do not count.
    # The emails themselves are out of reach of a site audit, so this is a stated
    # limit of the audit, not a finding: nothing wrong was observed.
    signup=[p for p in pages if p.features.get('signup_forms',0)]
    if signup:
        warnings.append('An email signup form appears on '+page_share(signup,pages)+'. A site audit cannot see the emails '
                        'the site sends, so whether inbox assistants can summarize them was not checked.')
    commercial=[p for p in pages if p.page_type in ('product','category')]
    stuck=[p for p in commercial if not p.features['buttons'] and not p.features['forms'] and not p.internal_links]
    add('next-step','No button, form or internal link on '+page_share(stuck,commercial,'commercial page'),stuck, 'No form, button or internal next-step link was observed on these commercial pages.', ['Add a relevant purchase, inquiry or comparison route if missing'])
    # 2.3 Generic anchor text (ported from donor EN-15, re-plumbed onto the immutable
    # snapshot). Descriptive anchors tell both visitors and machines what a target
    # page is about; the check runs only when enough internal anchors are sampled to
    # make a ratio meaningful, so a couple of "read more" links never trip it.
    _GENERIC={'click here','here','read more','learn more','more','link','this','details','view','go','click'}
    origin=(artifacts.normalized_origin or '').lower()
    def _internal(href):
        h=href.strip().lower()
        return h.startswith('/') or (origin and origin in h) or (h and not h.startswith(('http://','https://','#','mailto:','tel:','javascript:')))
    for p in pages:
        texts=[(t or '').strip().lower() for href,t in p.features['anchors'] if _internal(href) and (t or '').strip()]
        if len(texts)>=10:
            gen=sum(t in _GENERIC for t in texts)
            if gen/len(texts)>0.3:
                add('generic-anchor-text','Internal links use generic, non-descriptive anchor text',[p],
                    'About {:.0f}% of {} sampled internal anchors are generic phrases such as "read more" or "click here".'.format(gen/len(texts)*100,len(texts)),
                    ['Rewrite link text to name the destination, for example "compare pricing plans" instead of "learn more"','Keep anchor text meaningful when read out of context'])
    # 2.3 Weak page orientation on non-home content pages. Mirrors the homepage
    # orientation heuristic already in analyze_engagement but scoped to substantial
    # inner pages: substantial body text with no descriptive H1 gives an arriving
    # visitor no immediate sense of what the page is about.
    # A short H1 such as "About us" or "Ian Berry obituary" orients a visitor as well
    # as a long one; only a missing H1, or first headings that are all empty or
    # longer than 14 words, leave the page without one.
    orient=[p for p in pages if p.page_type not in ('home',) and len(p.visible_text.split())>300 and (not p.features['h1_count'] or not any(1<=len(h.split())<=14 for h in p.headings[:2]))]
    add('page-orientation','Content pages lack a clear orientation heading above the fold',orient,
        'Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.',
        ['Lead each content page with a descriptive H1 that names the topic','Follow with scannable H2 sections so the page structure is clear at a glance'])
    # 2.3 Internal discoverability gap: substantial pages that expose few or no
    # internal links leave a visitor (and a crawler) no path onward from that page.
    # Distinct from analyze_engagement's site-graph orphan/dead-end view, which is
    # about inbound links across the crawled graph; this is per-page outbound density.
    disc=[p for p in pages if len(p.visible_text.split())>400 and len([1 for href,_ in p.features['anchors'] if _internal(href)])<=1]
    add('internal-discoverability','Substantial pages offer almost no internal links onward',disc,
        'Sampled content pages expose at most one internal link, so visitors arriving from an AI answer have no clear related content to continue to.',
        ['Add contextual links to related pages within the body content','Ensure primary destinations are reachable from every substantial page'])
    # 2.3 Email-summary-friendly formatting (handout Appendix Concept F). Inbox AI
    # summaries are built from readable text; when an email-capture flow ships but
    # the surrounding page carries the substance only in images (no matching visible
    # text), a summarizer has little to work with. Conservative: fires only when an
    # email flow is present AND the page is image-heavy relative to its visible text.
    # Substance is "in images" only when at least three images carry no alt text:
    # described images (a product gallery with alt text) put their facts in text too.
    esf=[p for p in pages if p.features.get('signup_forms',0) and p.features['missing_alt']>=3 and len(p.visible_text.split())<120]
    add('email-summary-readable','Email-capture pages carry substance in images, not readable text',esf,
        'An email-capture flow was observed on pages whose visible text is sparse relative to their images; AI inbox summaries are built from readable text, so image-carried substance can be dropped.',
        ['Provide the key message as real text near the top, not only inside images','In outbound emails put the important lines first and keep decorative content secondary'])
    # Absence of FAQ/search/video/interactive widgets is deliberately NOT a generic defect.
    return skill_result('engagement-audit',findings=out,warnings=warnings,metrics={'experience_pages_analyzed':len(pages)})
