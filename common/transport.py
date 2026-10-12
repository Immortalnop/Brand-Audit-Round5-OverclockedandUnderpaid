"""GET-only stdlib transport: pinned DNS, verified TLS, one shared request/byte clock."""
import codecs
import functools
import http.client
import re
import socket
import ssl
import time
import threading
import zlib
from urllib.parse import urlsplit,urljoin
from url_safety import classify_url,same_origin
from tls_context import create_context
import network_budget

USER_AGENT='BrandAIReadinessAuditBot/2.0 (read-only audit)'

_BOMS=((b'\xef\xbb\xbf','utf-8'),(b'\xff\xfe','utf-16-le'),(b'\xfe\xff','utf-16-be'))
_HTTP_CHARSET=re.compile(r'charset\s*=\s*["\']?\s*([A-Za-z0-9_.:-]+)',re.I)
# <meta charset="x"> and <meta http-equiv="Content-Type" content="text/html; charset=x">.
_META_CHARSET=re.compile(rb'<meta\b[^>]*?charset\s*=\s*["\']?\s*([A-Za-z0-9_.:-]+)',re.I)
_META_PRESCAN_BYTES=2048
# Encodings a web page can declare. Anything else (base64, rot13, unicode_escape,
# idna and other codecs Python happens to know) is ignored, never used to decode.
_WEB_ENCODING=re.compile(r'^(?:utf-8|utf-16(?:-le|-be)?|cp(?:125\d|866|874|932|949|950)|iso8859-\d+|koi8-[ru]'
                         r'|shift_jis|euc_(?:jp|kr)|gb2312|gbk|gb18030|big5(?:hkscs)?|iso2022_jp|hz|mac-(?:roman|cyrillic)'
                         r'|tis-620|ascii)$')

def _web_encoding(label):
    """Python codec name for a declared charset label, or None. As browsers do,
    ASCII and ISO-8859-1 labels decode as windows-1252."""
    if isinstance(label,bytes):label=label.decode('ascii','ignore')
    try:name=codecs.lookup(label.strip()).name
    except (LookupError,ValueError):return None
    if not _WEB_ENCODING.match(name):return None
    return 'cp1252' if name in ('ascii','iso8859-1') else name

def detect_encoding(content,content_type=''):
    """(codec, source) for a response body: a byte order mark first, then the
    HTTP charset, then <meta charset> or http-equiv in the first 2 KB of an HTML
    body, else UTF-8. source is bom, http, meta or default."""
    for bom,name in _BOMS:
        if content.startswith(bom):return name,'bom'
    m=_HTTP_CHARSET.search(content_type or '')
    name=_web_encoding(m[1]) if m else None
    if name:return name,'http'
    if 'html' in (content_type or '').lower() or not content_type:
        m=_META_CHARSET.search(content[:_META_PRESCAN_BYTES])
        name=_web_encoding(m[1]) if m else None
        # A meta tag readable as ASCII cannot really declare UTF-16 (HTML standard).
        if name:return ('utf-8' if name.startswith('utf-16') else name),'meta'
    return 'utf-8','default'

def decode_body(content,content_type=''):
    """(text, codec, source). A body sent as UTF-8 that is mostly invalid UTF-8
    (at least 3 bad sequences and more bad sequences than valid non-ASCII
    characters) is a mislabelled single-byte page and is read as windows-1252;
    a few stray bytes in a real UTF-8 page never trigger this."""
    name,source=detect_encoding(content,content_type)
    if source=='bom':
        # The mark itself is not text.
        bom=next(b for b,n in _BOMS if n==name)
        return content[len(bom):].decode(name,'replace'),name,source
    try:text=content.decode(name,'replace')
    except LookupError:name,source='utf-8','default';text=content.decode('utf-8','replace')
    if name=='utf-8' and source!='bom':
        bad=text.count('\ufffd')
        if bad>=3 and bad>sum(1 for ch in text if ch>'\x7f' and ch!='\ufffd'):
            single=content.decode('cp1252','replace')
            if single.count('\ufffd')<bad:return single,'cp1252','utf8_fallback'
    return text,name,source

class Response:
    def __init__(self,status,headers,content,url,truncated=False,hops=0):
        self.status_code=status;self.headers=headers;self.content=content;self.final_url=url
        self.truncated=truncated;self.redirect_hops=hops;self.history=[]
    @functools.cached_property
    def _decoded(self):return decode_body(self.content,self.headers.get('Content-Type',''))
    # Decoded on first use, so images and PDFs read as bytes are never decoded.
    @property
    def text(self):return self._decoded[0]
    @property
    def encoding(self):return self._decoded[1]
    @property
    def encoding_source(self):return self._decoded[2]
    @property
    def ok(self):return 200<=self.status_code<300

class Transport:
    def __init__(self,origin,deadline,limits,instrumentation,allow_private=False,*,budget=None,pool='site',stage='acquisition'):
        """limits holds this transport's own ceilings. budget is the audit's shared
        ledger (common/network_budget.py; the active one when not given), charged
        in pool under the label stage, which a caller may change between requests."""
        self.origin=origin;self.deadline=deadline;self.limits=limits;self.i=instrumentation
        self.budget=budget if budget is not None else network_budget.active();self.pool=pool;self.stage=stage
        self.allow_private=allow_private;self.bytes=0;self.requests=0;self.last_request=0.
        self.diagnostics=[];self._address_attempts={};self.tls_settings={}
        self.robots=None;self.delay=0. if allow_private else getattr(limits,'REQUEST_DELAY_S',.2)
        # Where the last redirect to another origin pointed ({'from','to'}); the
        # redirect itself is never followed by this transport.
        self.last_cross_origin_redirect=None
    def _diagnostic(self,url,category,exc=None,**details):
        item={'url':url,'category':category,**details}
        if category.startswith('tls_') and self.tls_settings:item['tls_settings']=dict(self.tls_settings)
        if exc is not None:
            item.update(exception_type=type(exc).__name__, message=str(exc)[:500])
            for key in ('verify_code','verify_message','reason','library'):
                value=getattr(exc,key,None)
                if value is not None:item[key]=value if isinstance(value,int) else str(value)[:300]
        if len(self.diagnostics)<self.limits.MAX_TOTAL_HTTP_REQUESTS:
            self.diagnostics.append(item)

    def get(self,url,*,robots_exempt=False,max_bytes=None,headers=None,timeout_ms=None):
        """timeout_ms overrides PER_FETCH_TIMEOUT_MS for this request (robots.txt
        and the start URL); the transport deadline still caps it."""
        network_elapsed=0.0
        per_fetch_s=(timeout_ms if timeout_ms is not None else self.limits.PER_FETCH_TIMEOUT_MS)/1000
        for hops in range(6):
            if time.monotonic()>=self.deadline:return None,'deadline'
            if self.bytes>=self.limits.MAX_TOTAL_BYTES or self.requests>=self.limits.MAX_TOTAL_HTTP_REQUESTS:
                self.i.record_skip('global_request_or_byte_budget');return None,'budget_exhausted'
            if not same_origin(url,self.origin):
                self.i.record_skip('cross_origin_redirect_blocked');return None,'cross_origin_redirect_blocked'
            # Only the original robots URL is exempt; redirects are limited to the same origin.
            if not robots_exempt and self.robots is not None and not self.robots.can_fetch(USER_AGENT,url):
                self.i.record_skip('robots_disallowed');return None,'robots_disallowed'
            check=classify_url(url,allow_private=self.allow_private)
            if not check.safe:
                if check.reason in ('dns_resolution_failed','dns_resolution_error'):
                    self._diagnostic(url,'dns_error',reason=check.reason)
                    return None,'dns_error'
                self.i.record_safety_block(url,check.reason);return None,'blocked'
            wait=self.delay-(time.monotonic()-self.last_request)
            if wait>0:
                if time.monotonic()+wait>=self.deadline:return None,'deadline'
                time.sleep(wait)
            remaining=self.limits.MAX_TOTAL_BYTES-self.bytes
            cap=min(remaining,max_bytes if max_bytes is not None else getattr(self.limits,'MAX_RESPONSE_BYTES',1_500_000))
            if cap<=0:return None,'budget_exhausted'
            # The shared ledger reserves the request and its byte cap before anything is sent.
            granted=0
            if self.budget is not None:
                granted=self.budget.reserve(self.pool,self.stage,cap)
                if granted<=0:
                    self.i.record_skip('global_request_or_byte_budget');return None,'budget_exhausted'
                cap=granted
            timeout=min(per_fetch_s,max(.001,self.deadline-time.monotonic()))
            end=min(self.deadline,time.monotonic()+timeout)
            p=urlsplit(url);port=p.port or (443 if p.scheme=='https' else 80)
            conn=http.client.HTTPConnection(p.hostname,port,timeout=timeout)
            network_started=time.monotonic()
            content=b'';conn_sock=None;counted=False;wire=0;size=0
            attempt=self._address_attempts.get(url,0)
            address=check.addresses[attempt % len(check.addresses)]
            self._address_attempts[url]=attempt+1
            phase='tls_configuration' if p.scheme=='https' else 'connect'
            self.requests+=1;self.last_request=time.monotonic()
            timed_out=threading.Event()
            def interrupt_socket():
                timed_out.set()
                try:
                    if conn_sock:conn_sock.shutdown(socket.SHUT_RDWR)
                except (OSError,AttributeError):pass
            timer=threading.Timer(max(.001,end-time.monotonic()),interrupt_socket)
            timer.daemon=True;timer.start()
            try:
                # Connect to the validated address while preserving Host and TLS SNI.
                context=create_context() if p.scheme=='https' else None
                if context is not None:
                    self.tls_settings={'hostname_verification':context.check_hostname,'verify_mode':int(context.verify_mode),'verify_flags':int(context.verify_flags),'ca_certificates_loaded':context.cert_store_stats().get('x509_ca',0)}
                phase='connect'
                conn_sock=socket.create_connection((address,port),max(.001,end-time.monotonic()))
                if context is not None:
                    phase='tls_handshake'
                    conn_sock.settimeout(max(.001,end-time.monotonic()))
                    conn_sock=context.wrap_socket(conn_sock,server_hostname=p.hostname)
                phase='http_response'
                conn_sock.settimeout(max(.001,end-time.monotonic()))
                conn.sock=conn_sock
                req_headers={'User-Agent':USER_AGENT,'Accept':'text/html,application/xml,text/plain,*/*;q=0.5','Accept-Encoding':'identity',**(headers or {})}
                path=(p.path or '/')+('?' + p.query if p.query else '')
                conn.request('GET',path,headers=req_headers)
                resp=conn.getresponse();status=resp.status
                if status>=400:self._diagnostic(url,'http_error',http_status=status)
                hdr=dict(resp.getheaders())
                for key in ('Content-Type','Content-Encoding','Location','X-Robots-Tag'):
                    vals=resp.headers.get_all(key,[])
                    if vals:hdr[key]=', '.join(vals)
                if status in (301,302,303,307,308) and hdr.get('Location'):
                    self.i.record_request(True);counted=True
                    dest=urljoin(url,hdr['Location'])
                    if not same_origin(dest,self.origin):
                        self.last_cross_origin_redirect={'from':url,'to':dest,'http_status':status}
                        self.i.record_skip('cross_origin_redirect_blocked');return None,'cross_origin_redirect_blocked'
                    network_elapsed+=time.monotonic()-network_started
                    self.i.record_redirect();url=dest;continue
                chunks=[];size=0;decoder=None;wire=0;truncated=False
                encoding=hdr.get('Content-Encoding','').lower()
                if encoding not in ('','identity','gzip'):
                    self.i.record_request(False);counted=True
                    return None,'unsupported_encoding'
                if encoding=='gzip':decoder=zlib.decompressobj(16+zlib.MAX_WBITS)
                while size<cap:
                    left=end-time.monotonic()
                    if left<=0:raise TimeoutError('response deadline')
                    conn_sock.settimeout(left)
                    raw=resp.read1(min(8192,cap-size,cap-wire))
                    if not raw:break
                    wire+=len(raw)
                    if decoder is None and wire==len(raw) and raw.startswith(b'\x1f\x8b'):decoder=zlib.decompressobj(16+zlib.MAX_WBITS)
                    data=decoder.decompress(raw,cap-size) if decoder else raw
                    chunks.append(data);size+=len(data)
                    if wire>=cap and size<cap:truncated=True;break
                    if resp.isclosed():break
                if size>=cap:truncated=True
                content=b''.join(chunks)
                if timed_out.is_set():raise TimeoutError('absolute response deadline')
                # Budget both encoded wire and expanded bytes (whichever is larger).
                charged=max(wire,len(content));self.bytes+=charged
                self.i.record_request(True,charged);counted=True
                if truncated:self.i.record_truncated()
                result=Response(status,hdr,content,url,truncated,hops)
                result.network_duration_ms=round((network_elapsed+time.monotonic()-network_started)*1000)
                return result,'ok'
            except (TimeoutError,socket.timeout) as exc:
                self._diagnostic(url,'timeout',exc,phase=phase,address=address)
                self.bytes+=max(wire,size);self.i.record_request(False,max(wire,size),timed_out=True);counted=True;return None,'timeout'
            except ssl.SSLCertVerificationError as exc:
                self._diagnostic(url,'tls_certificate_error',exc,phase=phase,address=address)
                self.bytes+=max(wire,size);self.i.record_request(False,max(wire,size));counted=True;return None,'tls_certificate_error'
            except ssl.SSLError as exc:
                category='timeout' if timed_out.is_set() else 'tls_configuration_error' if phase=='tls_configuration' else 'tls_handshake_error' if phase=='tls_handshake' else 'tls_protocol_error'
                self._diagnostic(url,category,exc,phase=phase,address=address)
                self.bytes+=max(wire,size);self.i.record_request(False,max(wire,size),timed_out=category=='timeout');return None,category
            except socket.gaierror as exc:
                self._diagnostic(url,'dns_error',exc,phase=phase)
                self.i.record_request(False);return None,'dns_error'
            except (OSError,http.client.HTTPException,zlib.error,ValueError) as exc:
                category='timeout' if timed_out.is_set() else 'tls_configuration_error' if phase=='tls_configuration' else 'connection_error' if phase=='connect' else 'failed'
                self._diagnostic(url,category,exc,phase=phase,address=address)
                self.bytes+=max(wire,size);self.i.record_request(False,max(wire,size),timed_out=category=='timeout');return None,category
            # Connections and sockets are always closed, including failed handshakes.
            finally:
                if granted:self.budget.settle(self.pool,self.stage,granted,max(wire,size))
                timer.cancel()
                timer.join(.1)
                conn.close()
                if conn_sock:conn_sock.close()
        return None,'too_many_redirects'

