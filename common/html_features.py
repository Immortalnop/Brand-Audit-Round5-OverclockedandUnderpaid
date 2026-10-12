"""One-pass stdlib HTML extraction. Markup observations are not rendered UX facts."""
from html.parser import HTMLParser
import re

_VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
_PROSE=re.compile(r"[A-Za-z][^.?!]{25,}\.")


def _about_ok(parts):
    """A captured About section counts only if it contains a real sentence; a table
    of contents (a list of links or questions under an 'About' heading) does not."""
    return bool(_PROSE.search(' '.join(parts)))


_QUESTION=re.compile(r'\?$|^(how|what|why|when|where|who|which|can|does|do|is|are|should|will)\b',re.I)
# A newsletter or mailing-list signup, as opposed to a trial signup, a contact form
# or a login. Matched against the form's own attributes, labels and text.
_NEWSLETTER=re.compile(r'news-?letter|subscri(be|ption)|mailing[\s_-]?list|e-?mail updates|join (our|the) (list|community)'
                       r'|get (our )?(updates|the latest)|stay (in touch|up to date|informed)|digest',re.I)
_EMAIL_TEXT=re.compile(r'(?<![\w.+-])([A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24})(?![\w-])')
_PHONE_LABEL=re.compile(r'(?:phone|tel(?:ephone)?|call(?: us)?)\s*[:.]?\s*(\+?[\d][\d\s().-]{6,20}\d)',re.I)


def is_question_heading(text):
    text=' '.join((text or '').split())
    return bool(text) and bool(_QUESTION.search(text))


_HYDRATION_IDS={'__next_data__','__nuxt_data__','__apollo_state__','__remix_context__'}
_HYDRATION_ASSIGN=re.compile(r'window\.(__INITIAL_STATE__|__NUXT__|__APOLLO_STATE__|__PRELOADED_STATE__|__NEXT_DATA__|__INITIAL_DATA__)\s*=')
_STRING_LITERAL=re.compile(r'"((?:[^"\\]|\\.){25,400})"')


def _leaf_strings(value,out,limit):
    if len(out)>=limit:return
    if isinstance(value,dict):
        for v in value.values():_leaf_strings(v,out,limit)
    elif isinstance(value,list):
        for v in value:_leaf_strings(v,out,limit)
    elif isinstance(value,str):
        s=' '.join(value.split())
        if 25<=len(s)<=400 and ' ' in s and not re.match(r'^(https?:|/|data:|[\w.-]+@)',s) and not re.search(r'[<>{}]',s):
            out.append(s)


def _hydration_strings(script,limit):
    """Human-readable strings carried in a client-side hydration payload. If many
    of them never appear in the server-sent visible text, the content exists only
    for clients that execute JavaScript."""
    raw=''.join(script['parts'])
    if not raw or len(raw)>2_000_000:return []
    is_payload=script['id'] in _HYDRATION_IDS or (script['type']=='application/json' and len(raw)>200) or _HYDRATION_ASSIGN.search(raw[:5000])
    if not is_payload:return []
    import json
    out=[]
    body=raw
    m=_HYDRATION_ASSIGN.search(raw[:5000])
    if m:body=raw[m.end():].strip().rstrip(';')
    try:_leaf_strings(json.loads(body),out,limit)
    except (ValueError,RecursionError):
        for lit in _STRING_LITERAL.findall(raw[:500_000]):
            try:lit=json.loads('"'+lit+'"')
            except ValueError:continue
            _leaf_strings(lit,out,limit)
            if len(out)>=limit:break
    return out[:limit]


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.node_count=0
        self.stack=[];self.text=[];self.title_parts=[];self.meta={};self.canonical=None
        self.links=[];self.headings=[];self.heading_levels=[];self.paragraphs=[];self.jsonld=[]
        self.breadcrumb=[];self.scripts=0;self.spa=False;self.has_nav=False;self.lang=None
        self.images=0;self.missing_alt=0;self.forms=0;self.email_capture=False;self.search=False
        self.buttons=[];self.media=0;self.details=0;self.overlay=False;self.microdata=False
        self.landmarks=set();self.head_blocking_scripts=0;self.images_missing_dims=0;self.images_lazy=0
        self.canonicals=[];self.paragraph_text=[]
        self._script=None
        # Which links sit in site-wide navigation regions, footer text
        # (copyright year and holder), image and iframe metadata (facts locked in
        # non-text), <time datetime> values, and client-side hydration payloads
        # (a raw-vs-rendered proxy that needs no browser).
        self.region_links=[];self.footer_text=[];self.images_meta=[];self.iframes=[]
        self.time_values=[];self.noscript_text=[];self.hydration_strings=[]
        self._mount_marks=[];self.mount_empty=False
        # AG-01 support: the text under an "About ..." heading is captured while
        # parsing, independent of the visible-text cap, so the qualitative stage
        # always receives the passage it must judge (even on very long pages).
        self.about_section=[];self._about_level=None;self._about_done=False
        # Forms by purpose (newsletter signup vs trial/contact/login), visible
        # password inputs (login pages), questions with the text that answers
        # them (FAQ markup opportunities), list sizes (HowTo), microdata types
        # and contact details shown on the page (contact markup).
        self.form_records=[];self.password_inputs=0;self.loose_signup_inputs=0;self.executable_scripts=0
        self.question_answers=[];self._qa=None;self.max_ordered_list_items=0
        self.microdata_types=[];self.icon_links=[]
    def _open(self,*tags):
        return next((f for f in reversed(self.stack) if f['tag'] in tags),None)
    def _close_qa(self,level=None):
        if self._qa is not None and not self._qa['parts'] and level:self._qa['next_level']=level
        self._qa=None
    def handle_starttag(self,tag,attrs):
        self.node_count+=1
        if len(self.stack)>=256 or self.node_count>100000:
            raise ValueError("HTML structural parsing budget reached")
        a={k:(v or '') for k,v in attrs};hidden=('hidden' in a or a.get('aria-hidden','').lower()=='true' or bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',a.get('style',''),re.I)))
        frame={'tag':tag,'a':a,'text':[],'hidden':hidden or any(x['hidden'] for x in self.stack)}
        if self._about_level is not None and re.fullmatch('h[1-6]',tag) and int(tag[1])<=self._about_level:
            # Next heading at the same or a higher level ends the About section.
            self._about_level=None
            if _about_ok(self.about_section):self._about_done=True
            else:self.about_section=[]
        if re.fullmatch('h[1-6]',tag):self._close_qa(int(tag[1]))
        if tag=='form':frame['form']={'attrs':' '.join(a.get(k,'') for k in ('id','class','name','action','aria-label'))[:300],
                                      'email':False,'password':False,'words':[],'chars':0,'hidden':frame['hidden']}
        if tag=='li':
            owner=self._open('ol','ul')
            if owner is not None:owner['items']=owner.get('items',0)+1
        if a.get('itemtype') and len(self.microdata_types)<30:
            for value in a['itemtype'].split()[:5]:
                name=value.rstrip('/').rsplit('/',1)[-1].rsplit('#',1)[-1]
                if name and name not in self.microdata_types:self.microdata_types.append(name[:80])
        if tag=='link' and a.get('href','').strip() and len(self.icon_links)<6 and \
                {'icon','apple-touch-icon'}&set(a.get('rel','').lower().split()):
            self.icon_links.append({'rel':a.get('rel','').lower()[:40],'href':a['href'].strip()[:500]})
        if tag not in _VOID:self.stack.append(frame)
        if tag in ('main','article') and not frame['hidden']:self.landmarks.add(tag)
        if tag=='script' and a.get('src') and any(f['tag']=='head' for f in self.stack):
            if a.get('type','').lower() in ('','text/javascript','application/javascript') and 'async' not in a and 'defer' not in a:
                self.head_blocking_scripts+=1
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonicals.append(a.get('href',''))
        if tag=='html':self.lang=a.get('lang')
        if tag=='meta':self.meta.setdefault((a.get('name') or a.get('property') or '').lower(),[]).append(a.get('content',''))
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonical=a.get('href')
        if tag=='script':
            self.scripts+=1;self._script={'type':a.get('type','').lower(),'id':a.get('id','').lower(),'parts':[]}
            # Only code a browser runs: not JSON-LD, JSON data blocks or templates.
            if a.get('type','').lower().strip() in ('','text/javascript','application/javascript','module'):self.executable_scripts+=1
        if tag=='nav' or a.get('role')=='navigation':self.has_nav=True
        if a.get('id','').lower() in {'root','app','__next','___gatsby','app-root','__nuxt','svelte'}:
            self.spa=True
            if tag not in _VOID:self._mount_marks.append((len(self.stack)-1,len(self.text)))
        if tag=='time' and a.get('datetime') and len(self.time_values)<40:self.time_values.append(a['datetime'][:40])
        if tag=='iframe' and a.get('src') and len(self.iframes)<20:self.iframes.append(a['src'][:300])
        if 'itemscope' in a or 'typeof' in a:self.microdata=True
        if tag=='img':
            self.images+=1
            if not (re.fullmatch(r'[0-9]{1,9}',a.get('width','')) and int(a['width'])>0 and re.fullmatch(r'[0-9]{1,9}',a.get('height','')) and int(a['height'])>0):self.images_missing_dims+=1
            if a.get('loading','').lower()=='lazy':self.images_lazy+=1
            # alt="" is valid for decorative images; only missing attributes count.
            if 'alt' not in a and a.get('role') not in ('presentation','none'):self.missing_alt+=1
            if len(self.images_meta)<60:
                self.images_meta.append({'src':(a.get('src') or a.get('data-src') or '')[:300],'alt':a.get('alt') if 'alt' in a else None,
                    'width':int(a['width']) if re.fullmatch(r'[0-9]{1,6}',a.get('width','')) else None,
                    'height':int(a['height']) if re.fullmatch(r'[0-9]{1,6}',a.get('height','')) else None,
                    'in_main':any(f['tag'] in ('main','article') for f in self.stack)})
        if tag=='form':self.forms+=1
        if tag=='input':
            kind=a.get('type','').lower()
            self.email_capture |= kind=='email'
            self.search |= kind=='search'
            if kind=='submit':self.buttons.append(a.get('value',''))
            owner=self._open('form')
            label=' '.join(a.get(k,'') for k in ('name','id','placeholder','aria-label','value')).strip()
            if kind=='password' and not frame['hidden']:self.password_inputs+=1
            if owner is not None:
                rec=owner['form']
                rec['email'] |= kind=='email' or (kind in ('','text') and bool(re.search(r'e-?mail',label,re.I)))
                rec['password'] |= kind=='password'
                if label and len(rec['words'])<12:rec['words'].append(label[:80])
            elif kind=='email' and not frame['hidden'] and _NEWSLETTER.search(label):
                # An email field outside any form (a JavaScript-submitted widget)
                # counts only when its own label names a newsletter.
                self.loose_signup_inputs+=1
        if tag in ('video','audio','iframe'):self.media+=1
        if tag=='details':self.details+=1
        if not frame['hidden'] and re.search(r'newsletter-popup|modal-backdrop|interstitial|overlay-active',a.get('class',''),re.I):self.overlay=True
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in _VOID:self.handle_endtag(tag)
    def handle_data(self,data):
        tags={f['tag'] for f in self.stack}
        if 'script' in tags:
            if self._script:self._script['parts'].append(data)
            return
        if 'style' in tags or 'template' in tags:return
        if 'title' in tags:self.title_parts.append(data);return
        if any(f['hidden'] for f in self.stack):return
        if data.strip():
            self.text.append(data.strip())
            if 'footer' in tags and len(self.footer_text)<80:self.footer_text.append(data.strip()[:300])
            if 'noscript' in tags and len(self.noscript_text)<10:self.noscript_text.append(data.strip()[:300])
            qa=self._qa
            if qa is not None and qa['chars']<600 and not tags&{'h1','h2','h3','h4','h5','h6'}:
                qa['parts'].append(data.strip());qa['chars']+=len(data.strip())+1
            owner=self._open('form')
            if owner is not None and owner['form']['chars']<400:
                owner['form']['words'].append(data.strip()[:120]);owner['form']['chars']+=len(data.strip())
            if self._about_level is not None and not self._about_done:
                self.about_section.append(data.strip())
                if len(' '.join(self.about_section))>=1500:self._about_done=True;self._about_level=None
        for f in self.stack:
            if f['tag'] in {'a','button','p','h1','h2','h3','h4','h5','h6','span','time'}:f['text'].append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self._script:
            if self._script['type']=='application/ld+json':self.jsonld.append(''.join(self._script['parts']))
            elif len(self.hydration_strings)<200:
                self.hydration_strings.extend(_hydration_strings(self._script,200-len(self.hydration_strings)))
            self._script=None
        idx=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i]['tag']==tag),None)
        if idx is None:return
        frame=self.stack[idx];text=' '.join(''.join(frame['text']).split());a=frame['a']
        if self._mount_marks and self._mount_marks[-1][0]==idx:
            _,text_len=self._mount_marks.pop()
            if len(self.text)==text_len:self.mount_empty=True
        if tag=='ol' and not frame['hidden']:self.max_ordered_list_items=max(self.max_ordered_list_items,frame.get('items',0))
        if tag=='form' and len(self.form_records)<20:
            rec=frame['form'];words=' '.join([rec['attrs']]+rec['words'])
            self.form_records.append({'email':rec['email'],'password':rec['password'],'hidden':rec['hidden'],
                                      'newsletter':bool(rec['email'] and not rec['password'] and _NEWSLETTER.search(words)),
                                      'in_footer':any(f['tag']=='footer' for f in self.stack[:idx]),
                                      'text':' '.join(words.split())[:200]})
        if not frame['hidden']:
            if tag=='a' and a.get('href'):
                self.links.append((a['href'],text))
                if any(f['tag'] in ('nav','header','footer') or f['a'].get('role')=='navigation' for f in self.stack[:idx]):
                    if len(self.region_links)<200:self.region_links.append(a['href'])
                # Link text inside a heading: a heading that is mostly a link names
                # another page (a teaser on a listing), not a question this page answers.
                heading=next((f for f in reversed(self.stack[:idx]) if re.fullmatch('h[1-6]',f['tag'])),None)
                if heading is not None:heading['link_chars']=heading.get('link_chars',0)+len(text)
            if re.fullmatch('h[1-6]',tag):
                self.headings.append(text);self.heading_levels.append(int(tag[1]))
                linked=(any(f['tag']=='a' and f['a'].get('href') for f in self.stack[:idx])
                        or (bool(text) and frame.get('link_chars',0)>=0.6*len(text)))
                if tag in ('h2','h3') and not linked and is_question_heading(text) and len(self.question_answers)<20:
                    self._qa={'question':text[:200],'parts':[],'chars':0,'level':int(tag[1]),'next_level':None}
                    self.question_answers.append(self._qa)
                if not self._about_done and re.match(r"(about\b|who we are|our story|our company)",text,re.I):
                    self._about_level=int(tag[1]);self.about_section=[text]
            if tag=='p':
                self.paragraphs.append(len(text))
                if len(self.paragraph_text)<12:self.paragraph_text.append(text[:600])
            if tag=='button':self.buttons.append(text)
            if tag in ('a','span') and any('breadcrumb' in str(f['a']).lower() for f in self.stack):self.breadcrumb.append(text)
        del self.stack[idx:]
    def _contact(self):
        """Email addresses and phone numbers the page shows: mailto:/tel: links,
        emails written in visible text, and labelled phone numbers. Bounded."""
        from urllib.parse import unquote
        emails,phones=[],[]
        for href,_ in self.links:
            h=(href or '').strip()
            if h.lower().startswith('mailto:'):
                addr=unquote(h[7:].split('?',1)[0]).strip()
                if _EMAIL_TEXT.fullmatch(addr):emails.append(addr.lower())
            elif h.lower().startswith('tel:'):
                num=re.sub(r'[^\d+]','',unquote(h[4:]))
                if 7<=len(num.lstrip('+'))<=15:phones.append(num)
        text=' '.join(self.text)
        if len(text)>200_000:text=text[:100_000]+' '+text[-100_000:]
        emails+= [m.lower() for m in _EMAIL_TEXT.findall(text)[:20]]
        phones+= [re.sub(r'[^\d+]','',m) for m in _PHONE_LABEL.findall(text)[:10]]
        phones=[p for p in phones if 7<=len(p.lstrip('+'))<=15]
        return list(dict.fromkeys(emails))[:10],list(dict.fromkeys(phones))[:10]
    def features(self):
        self._close_qa()
        emails,phones=self._contact()
        return {'observation_version':2, 'landmarks':sorted(self.landmarks),
                'form_records':self.form_records,'password_inputs':self.password_inputs,
                'executable_scripts':self.executable_scripts,
                'newsletter_signup':any(f['newsletter'] and not f['hidden'] for f in self.form_records) or self.loose_signup_inputs>0,
                'question_answers':[{'question':q['question'],'answer':' '.join(q['parts'])[:600],
                                     'answered_by_subheadings':bool(q['next_level'] and q['next_level']>q['level'])}
                                    for q in self.question_answers],
                'max_ordered_list_items':self.max_ordered_list_items,'microdata_types':self.microdata_types,
                'icon_links':self.icon_links,'contact_emails':emails,'contact_phones':phones,
                'head_blocking_scripts':self.head_blocking_scripts,'images_missing_dims':self.images_missing_dims,
                'images_lazy':self.images_lazy,'canonical_values':self.canonicals[:20],
                'opening_paragraphs':self.paragraph_text,
                'full_visible_chars':len(' '.join(self.text)),
                'full_visible_bytes':len(' '.join(self.text).encode('utf-8')),
                'question_headings':sum(bool(re.search(r'\?$|^(how|what|why|when|where|who|can|does|is|are|should)\b',h.strip(),re.I)) for h,l in zip(self.headings,self.heading_levels) if l in (2,3)),
                'viewport':self.meta.get('viewport',[]),'lang':self.lang,'has_nav':self.has_nav,
                'h1_count':self.heading_levels.count(1),'subheadings':sum(x>1 for x in self.heading_levels),
                'heading_levels':self.heading_levels[:200],'paragraph_lengths':self.paragraphs[:400],
                'buttons':self.buttons[:50],'anchors':self.links[:200],'scripts':self.scripts,'spa_mount':self.spa,
                'images':self.images,'missing_alt':self.missing_alt,'forms':self.forms,'email_capture':self.email_capture,
                'search':self.search,'media':self.media,'details':self.details,'overlay_pattern':self.overlay,
                'alternative_structured_markup':self.microdata,'meta':self.meta,
                'region_links':self.region_links,'footer_text':' '.join(self.footer_text)[:3000],
                'images_meta':self.images_meta,'iframes':self.iframes,'time_values':self.time_values,
                'noscript_text':' '.join(self.noscript_text)[:1000],'spa_mount_empty':self.mount_empty,
                'hydration_strings':self.hydration_strings[:200],
                'about_section':' '.join(self.about_section)[:1500] if (self._about_done or _about_ok(self.about_section)) else ''}
