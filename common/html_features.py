"""One-pass stdlib HTML extraction. Markup observations are not rendered UX facts."""
from html.parser import HTMLParser
import re

_VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
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
        self.canonicals=[];self.paragraph_text=[];self.image_records=[]
        self._script=None
    def handle_starttag(self,tag,attrs):
        self.node_count+=1
        if len(self.stack)>=256 or self.node_count>100000:
            raise ValueError("HTML structural parsing budget reached")
        a={k:(v or '') for k,v in attrs};hidden=('hidden' in a or a.get('aria-hidden','').lower()=='true' or bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',a.get('style',''),re.I)))
        frame={'tag':tag,'a':a,'text':[],'hidden':hidden or any(x['hidden'] for x in self.stack)}
        if tag not in _VOID:self.stack.append(frame)
        if tag in ('main','article') and not frame['hidden']:self.landmarks.add(tag)
        if tag=='script' and a.get('src') and any(f['tag']=='head' for f in self.stack):
            if a.get('type','').lower() in ('','text/javascript','application/javascript') and 'async' not in a and 'defer' not in a:
                self.head_blocking_scripts+=1
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonicals.append(a.get('href',''))
        if tag=='html':self.lang=a.get('lang')
        if tag=='meta':self.meta.setdefault((a.get('name') or a.get('property') or '').lower(),[]).append(a.get('content',''))
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonical=a.get('href')
        if tag=='script':self.scripts+=1;self._script={'type':a.get('type','').lower(),'parts':[]}
        if tag=='nav' or a.get('role')=='navigation':self.has_nav=True
        if a.get('id','').lower() in {'root','app','__next','___gatsby','app-root'}:self.spa=True
        if 'itemscope' in a or 'typeof' in a:self.microdata=True
        if tag=='img':
            self.images+=1
            if not (re.fullmatch(r'[0-9]{1,9}',a.get('width','')) and int(a['width'])>0 and re.fullmatch(r'[0-9]{1,9}',a.get('height','')) and int(a['height'])>0):self.images_missing_dims+=1
            if a.get('loading','').lower()=='lazy':self.images_lazy+=1
            # alt="" is valid for decorative images; only missing attributes count.
            if 'alt' not in a and a.get('role') not in ('presentation','none'):self.missing_alt+=1
            # Bounded per-page record of visible images for the non-text media checks.
            src=(a.get('src') or a.get('data-src') or a.get('data-lazy-src') or a.get('srcset','').split(',')[0].strip().split(' ')[0]).strip()
            if src and not src.lower().startswith('data:') and not frame['hidden'] and len(self.image_records)<60:
                self.image_records.append({'src':src,'alt':a['alt'] if 'alt' in a else None,'title':a.get('title') or None,
                                           'width':a.get('width') or None,'height':a.get('height') or None})
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
        if data.strip():self.text.append(data.strip())
        for f in self.stack:
            if f['tag'] in {'a','button','p','h1','h2','h3','h4','h5','h6','span','time'}:f['text'].append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self._script:
            if self._script['type']=='application/ld+json':self.jsonld.append(''.join(self._script['parts']))
            self._script=None
        idx=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i]['tag']==tag),None)
        if idx is None:return
        frame=self.stack[idx];text=' '.join(''.join(frame['text']).split());a=frame['a']
        if not frame['hidden']:
            if tag=='a' and a.get('href'):self.links.append((a['href'],text))
            if re.fullmatch('h[1-6]',tag):self.headings.append(text);self.heading_levels.append(int(tag[1]))
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
                'image_records':self.image_records}
