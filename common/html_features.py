"""One-pass stdlib HTML extraction. Markup observations are not rendered UX facts."""
from html.parser import HTMLParser
import re

_VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
_PROSE=re.compile(r"[A-Za-z][^.?!]{25,}\.")


def _about_ok(parts):
    """A captured About section counts only if it contains a real sentence; a table
    of contents (a list of links or questions under an 'About' heading) does not."""
    return bool(_PROSE.search(' '.join(parts)))


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
    for clients that execute JavaScript (A18)."""
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
        # Round-5 observations (A8, A9, A10, A18): which links sit in site-wide
        # navigation regions, footer text (copyright year / holder), image and
        # iframe metadata (facts locked in non-text), <time datetime> values, and
        # client-side hydration payloads (raw-vs-rendered proxy without a browser).
        self.region_links=[];self.footer_text=[];self.images_meta=[];self.iframes=[]
        self.time_values=[];self.noscript_text=[];self.hydration_strings=[]
        self._mount_marks=[];self.mount_empty=False
        # AG-01 support: the text under an "About ..." heading is captured while
        # parsing, independent of the visible-text cap, so the qualitative stage
        # always receives the passage it must judge (even on very long pages).
        self.about_section=[];self._about_level=None;self._about_done=False
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
        if tag not in _VOID:self.stack.append(frame)
        if tag in ('main','article') and not frame['hidden']:self.landmarks.add(tag)
        if tag=='script' and a.get('src') and any(f['tag']=='head' for f in self.stack):
            if a.get('type','').lower() in ('','text/javascript','application/javascript') and 'async' not in a and 'defer' not in a:
                self.head_blocking_scripts+=1
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonicals.append(a.get('href',''))
        if tag=='html':self.lang=a.get('lang')
        if tag=='meta':self.meta.setdefault((a.get('name') or a.get('property') or '').lower(),[]).append(a.get('content',''))
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonical=a.get('href')
        if tag=='script':self.scripts+=1;self._script={'type':a.get('type','').lower(),'id':a.get('id','').lower(),'parts':[]}
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
            self.email_capture |= a.get('type','').lower()=='email'
            self.search |= a.get('type','').lower()=='search'
            if a.get('type','').lower()=='submit':self.buttons.append(a.get('value',''))
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
        if not frame['hidden']:
            if tag=='a' and a.get('href'):
                self.links.append((a['href'],text))
                if any(f['tag'] in ('nav','header','footer') or f['a'].get('role')=='navigation' for f in self.stack[:idx]):
                    if len(self.region_links)<200:self.region_links.append(a['href'])
            if re.fullmatch('h[1-6]',tag):
                self.headings.append(text);self.heading_levels.append(int(tag[1]))
                if not self._about_done and re.match(r"(about\b|who we are|our story|our company)",text,re.I):
                    self._about_level=int(tag[1]);self.about_section=[text]
            if tag=='p':
                self.paragraphs.append(len(text))
                if len(self.paragraph_text)<12:self.paragraph_text.append(text[:600])
            if tag=='button':self.buttons.append(text)
            if tag in ('a','span') and any('breadcrumb' in str(f['a']).lower() for f in self.stack):self.breadcrumb.append(text)
        del self.stack[idx:]
    def features(self):
        return {'observation_version':2, 'landmarks':sorted(self.landmarks),
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
