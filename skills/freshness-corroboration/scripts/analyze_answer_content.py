"""AEO/GEO content heuristics and observed software identity, using shared artifacts.

English lexical rules are gated by declared language. No query ranking, citation
likelihood, app-store metadata or independent brand facts are invented here.
"""
import re
from collections import Counter
from urllib.parse import urlsplit
from check_helpers import eligible_pages, observation, page_share
from models import skill_result
from structured_data import iter_nodes, types_of

CHECK_IDS = frozenset({'title-body-alignment','term-repetition','answer-headings','brand-definition','app-identity'})
_STOP = frozenset('the a an and or for to in on of with by from at is are be as it this that your our you we us home about contact official website welcome more all can how what when where why who which'.split())

def terms(text):
    return [w for w in re.findall(r"[a-z]+(?:'[a-z]+)?",text.lower()) if len(w)>2 and w not in _STOP]

def english(page):
    return (page.features.get('lang') or '').lower().split('-')[0]=='en'

def _brand_terms(artifacts,entity_identity):
    """Terms of the brand's name: the resolved canonical name, whatever its
    confidence, and the first label of the site's host ("python" for
    www.python.org)."""
    name=(entity_identity or {}).get('data',{}).get('canonical_name')
    out=set(terms(name)) if isinstance(name,str) else set()
    try:host=(urlsplit(getattr(artifacts,'site_url','') or '').hostname or '').lower()
    except ValueError:host=''
    if host.startswith('www.'):host=host[4:]
    label=host.split('.')[0] if host else ''
    out.update(terms(label.replace('-',' ')))
    return out

def analyze_answer_content(artifacts, entity_identity, deadline):
    pages=eligible_pages(artifacts)
    out=[]
    if deadline.expired():
        return skill_result('freshness-corroboration',status='insufficient_evidence',warnings=['Answer-content checks skipped: deadline reached.'])
    def emit(rid,title,selected,detail):
        if selected:
            out.append(observation(rid,title,selected,{p.url:detail(p) for p in selected},
                                   skill='freshness-corroboration',script='analyze_answer_content.py'))
    lexical=[p for p in pages if english(p) and p.features.get('visible_text_complete',False)]
    mismatch=[];repeated=[];details={}
    brand=_brand_terms(artifacts,entity_identity)
    for p in lexical:
        body_words=re.findall(r"[a-z]+(?:'[a-z]+)?",p.visible_text.lower())
        title_terms=set(terms(p.title or ''));body_terms=Counter(terms(p.visible_text))
        if len(body_words)>=200 and len(title_terms)>=3 and len(title_terms & body_terms.keys())<=1:
            mismatch.append(p);details[p.url]='Unmatched literal title terms: '+', '.join(sorted(title_terms-body_terms.keys()))+'. Synonyms and semantic equivalence were not evaluated.'
        # Stuffing is written into sentences. Short blocks (list items, card labels,
        # "3 colours available", "5 years ago", "Chapter 4" in a table of contents)
        # repeat a word by design, so only blocks of at least 12 words are counted
        # (html_features running_text). The brand's own name is expected to recur
        # on its own site, so it is not counted as a repeated term either.
        prose=p.features.get('running_text') or ''
        prose_words=re.findall(r"[a-z]+(?:'[a-z]+)?",prose.lower())
        repeat_terms=Counter({t:c for t,c in Counter(terms(prose)).items() if t not in brand})
        if len(prose_words)>=300 and repeat_terms:
            term,count=repeat_terms.most_common(1)[0]
            if count/len(prose_words)>.06:
                repeated.append(p)
                details[p.url+'#repeat']=f"Term '{term}' occurs {count} times among {len(prose_words)} words of running text. Repetition alone is not proof of spam."
    emit('title-body-alignment','Title words do not appear in the body text on '+page_share(mismatch,lexical),mismatch,lambda p:details[p.url])
    emit('term-repetition','One word makes up more than 6% of the text on '+page_share(repeated,lexical),repeated,lambda p:details[p.url+'#repeat'])
    content=[p for p in lexical if p.page_type in ('article','product','service','software') and len(p.visible_text.split())>=200]
    if len(content)>=3 and not any(p.features.get('question_headings',0) for p in content):
        emit('answer-headings','No question-shaped headings on '+page_share(content,content,'content page'),content,
             lambda p:'No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.')
    identity=entity_identity.get('data',{})
    name=identity.get('canonical_name','')
    identity_pages=[p for p in lexical if p.page_type in ('home','about') and len(p.visible_text)>300]
    # A name that is a URL or a bare domain (markup that names the organization
    # by its address) is not wording a sentence would use: nothing to search for.
    url_like=isinstance(name,str) and bool(re.match(r'\s*(?:https?://|www\.)|\s*[\w-]+(?:\.[\w-]+)+/?\s*$',name,re.I))
    if isinstance(name,str) and len(name.strip())>=3 and not url_like and identity.get('confidence',0)>=.85 and identity_pages:
        name_pattern=re.compile(r'(?<!\w)'+re.escape(name)+r'(?!\w)',re.I)
        # Descriptive verbs a one-sentence brand definition uses ("Acme sells...",
        # "Acme runs daily ferries...", "Acme repairs boilers...").
        verb=re.compile(r'\b(is|are|helps|provides|offers|builds|makes|delivers|creates|specializes|sells|runs|'
                        r'operates|serves|designs|develops|manufactures|produces|publishes|supplies|repairs|fixes|'
                        r'connects|teaches|trains|hosts|organizes|organises)\b',re.I)
        def defines(p):
            candidates=re.split(r'(?<=[.!?])\s+',p.visible_text)+[p.meta_description or '']
            return any(20<=len(s)<=250 and name_pattern.search(s) and verb.search(s) for s in candidates)
        if not any(defines(p) for p in identity_pages):
            emit('brand-definition','No one-sentence definition of the brand on the home or About page',identity_pages,
                 lambda p:f"No short English sentence naming '{name}' and using a common descriptive verb was matched. This lexical heuristic may miss valid wording.")
    apps=[];app_details={}
    for p in pages:
        software=[n for n in iter_nodes(p.jsonld_blocks) if types_of(n)&{'SoftwareApplication','MobileApplication','WebApplication'}]
        missing=set()
        for node in software:
            missing.update(k for k in ('name','applicationCategory','operatingSystem') if not node.get(k))
        if missing:
            apps.append(p);app_details[p.url]='Observed software markup omits: '+', '.join(sorted(missing))+'. App-store listings and rankings were not inspected.'
    emit('app-identity','Software markup lacks name, category or operating system on '+page_share(apps,pages),apps,lambda p:app_details[p.url])
    skipped=len(pages)-len(lexical)
    return skill_result('freshness-corroboration',findings=out,
        metrics={'answer_pages_analyzed':len(pages),'english_lexical_pages':len(lexical),
                 'lexical_pages_skipped':skipped,'software_pages_checked':sum(any(types_of(n)&{'SoftwareApplication','MobileApplication','WebApplication'} for n in iter_nodes(p.jsonld_blocks)) for p in pages),
                 'app_store_rankings_assessed':False},
        warnings=['English lexical checks skipped on pages with unknown/non-English language or truncated retained text.'] if skipped else [],
        coverage={'pages_analyzed':len(pages),'pages_skipped':len(artifacts.pages)-len(pages)})
