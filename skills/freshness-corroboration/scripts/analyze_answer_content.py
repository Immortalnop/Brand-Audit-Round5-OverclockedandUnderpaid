"""AEO/GEO content heuristics and observed software identity, using shared artifacts.

English lexical rules are gated by declared language. No query ranking, citation
likelihood, app-store metadata or independent brand facts are invented here.
"""
import re
from collections import Counter
from check_helpers import eligible_pages, observation
from models import skill_result
from structured_data import iter_nodes, types_of

CHECK_IDS = frozenset({'title-body-alignment','term-repetition','answer-headings','brand-definition','app-identity',
                       'identity-not-declared'})
_STOP = frozenset('the a an and or for to in on of with by from at is are be as it this that your our you we us home about contact official website welcome more all can how what when where why who which'.split())

def terms(text):
    return [w for w in re.findall(r"[a-z]+(?:'[a-z]+)?",text.lower()) if len(w)>2 and w not in _STOP]

def english(page):
    return (page.features.get('lang') or '').lower().split('-')[0]=='en'

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
    # The brand's own name recurs on its pages by design (a masthead, a product
    # name); it is not keyword stuffing, so its words are left out of the count.
    brand_terms=set(terms(str((entity_identity.get('data') or {}).get('canonical_name') or '')))
    for p in lexical:
        body_words=re.findall(r"[a-z]+(?:'[a-z]+)?",p.visible_text.lower())
        title_terms=set(terms(p.title or ''));body_terms=Counter(terms(p.visible_text))
        if len(body_words)>=200 and len(title_terms)>=3 and len(title_terms & body_terms.keys())<=1:
            mismatch.append(p);details[p.url]='Unmatched literal title terms: '+', '.join(sorted(title_terms-body_terms.keys()))+'. Synonyms and semantic equivalence were not evaluated.'
        counted=Counter({t:c for t,c in body_terms.items() if t not in brand_terms})
        if len(body_words)>=300 and counted:
            term,count=counted.most_common(1)[0]
            if count/len(body_words)>.06:
                repeated.append(p)
                details[p.url+'#repeat']=f"Term '{term}' occurs {count} times among {len(body_words)} words. Repetition alone is not proof of spam."
    emit('title-body-alignment','Review literal title and body topic alignment',mismatch,lambda p:details[p.url])
    emit('term-repetition','Review unusually repeated terms',repeated,lambda p:details[p.url+'#repeat'])
    content=[p for p in lexical if p.page_type in ('article','product','service','software') and len(p.visible_text.split())>=200]
    if len(content)>=3 and not any(p.features.get('question_headings',0) for p in content):
        emit('answer-headings','Consider answer-oriented sections where useful',content,
             lambda p:'No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.')
    identity=entity_identity.get('data',{})
    name=identity.get('canonical_name','')
    identity_pages=[p for p in lexical if p.page_type in ('home','about') and len(p.visible_text)>300]
    if isinstance(name,str) and len(name.strip())>=3 and identity.get('confidence',0)>=.85 and identity_pages:
        name_pattern=re.compile(r'(?<!\w)'+re.escape(name)+r'(?!\w)',re.I)
        verb=re.compile(r'\b(is|are|was|helps|provides|offers|builds|makes|delivers|creates|speciali[sz]es|sells|runs|'
                        r'fixes|repairs|teaches|publishes|designs|develops|manufactures|produces|operates|serves|'
                        r'supplies|hosts|connects|powers|lets|enables|brings|bakes|roasts|trains|installs|ships)\b',re.I)
        def defines(p):
            candidates=re.split(r'(?<=[.!?])\s+',p.visible_text)+[p.meta_description or '']
            return any(20<=len(s)<=250 and name_pattern.search(s) and verb.search(s) for s in candidates)
        if not any(defines(p) for p in identity_pages):
            emit('brand-definition','Review whether the brand has a concise factual definition',identity_pages,
                 lambda p:f"No short English sentence naming '{name}' and using a common descriptive verb was matched. This lexical heuristic may miss valid wording.")
    apps=[];app_details={}
    for p in pages:
        software=[n for n in iter_nodes(p.jsonld_blocks) if types_of(n)&{'SoftwareApplication','MobileApplication','WebApplication'}]
        missing=set()
        for node in software:
            missing.update(k for k in ('name','applicationCategory','operatingSystem') if not node.get(k))
        if missing:
            apps.append(p);app_details[p.url]='Observed software markup omits: '+', '.join(sorted(missing))+'. App-store listings and rankings were not inspected.'
    emit('app-identity','Review observed software application identity fields',apps,lambda p:app_details[p.url])
    # A7: the brand name had to be inferred (no Organization JSON-LD). Reported once,
    # on the homepage, with the sources the name was inferred from.
    if identity.get('declared') is False and identity.get('canonical_name'):
        home=next((p for p in pages if p.page_type=='home'),pages[0] if pages else None)
        if home is not None:
            from models import make_finding
            sources='; '.join(f"{s['source']}: {s['name']!r}" for s in identity.get('identity_sources',[])[:4])
            out.append(make_finding(category='ai_discoverability',finding_type='defect',severity='medium',
                status='confirmed',confidence=.85,title='Brand identity is not declared in machine-readable form',
                root_cause=f"No Organization JSON-LD; the brand name was inferred as {identity['canonical_name']!r} "
                           f"(confidence {identity.get('confidence')}) from: {sources}",
                evidence=[{'type':'identity','description':sources,'urls':[home.url]}],affected_pages=[home.url],
                suggested_action={'summary':'Declare the brand with Organization JSON-LD on the homepage',
                    'steps':[f"Add Organization JSON-LD with name {identity['canonical_name']!r}, url, logo and sameAs links",
                             'Add a WebSite node with the same name','Use the same name in titles and og:site_name'],
                    'priority':'medium','effort':'low','expected_benefit':'One explicit, unambiguous identity for the brand',
                    'verification':'Re-run: identity resolves at level 1 (Organization JSON-LD)'},
                provenance={'skill':'freshness-corroboration','script':'analyze_answer_content.py','rule_id':'identity-not-declared'}))
    skipped=len(pages)-len(lexical)
    return skill_result('freshness-corroboration',findings=out,
        metrics={'answer_pages_analyzed':len(pages),'english_lexical_pages':len(lexical),
                 'lexical_pages_skipped':skipped,'software_pages_checked':sum(any(types_of(n)&{'SoftwareApplication','MobileApplication','WebApplication'} for n in iter_nodes(p.jsonld_blocks)) for p in pages),
                 'app_store_rankings_assessed':False},
        warnings=['English lexical checks skipped on pages with unknown/non-English language or truncated retained text.'] if skipped else [],
        coverage={'pages_analyzed':len(pages),'pages_skipped':len(artifacts.pages)-len(pages)})
