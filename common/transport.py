"""GET-only stdlib transport: pinned DNS, verified TLS, one shared request/byte clock."""
import http.client
import socket
import ssl
import time
import threading
import zlib
from urllib.parse import urlsplit,urljoin
from url_safety import classify_url,same_origin
from tls_context import create_context

USER_AGENT='BrandAIReadinessAuditBot/2.0 (read-only audit)'
import codecs,re
_META_CHARSET=re.compile(rb'<meta[^>]+charset\s*=\s*["\']?\s*([A-Za-z0-9._:-]{1,40})',re.I)
_BOMS=((codecs.BOM_UTF8,'utf-8-sig'),(codecs.BOM_UTF16_LE,'utf-16'),(codecs.BOM_UTF16_BE,'utf-16'))

# Canonical Python names of the encodings a browser will use for a web document
# (the WHATWG Encoding set, as far as the standard library implements it).
#
# This whitelist is the point: codecs.lookup() alone is not a charset validator.
# It happily resolves rot13, base64, hex, quopri, uu, bz2 and zlib -- codecs that
# are not text encodings at all -- so a Content-Type of "text/html; charset=rot13"
# passed as a known encoding and then raised LookupError inside bytes.decode(),
# turning an ordinary page into a transport failure. A label outside this set is
# ignored exactly as a browser ignores an unknown one, and the body is read with
# the next source of truth instead.
_WEB_ENCODINGS=frozenset({
 'ascii','big5','big5hkscs','cp1006','cp1250','cp1251','cp1252','cp1253','cp1254','cp1255',
 'cp1256','cp1257','cp1258','cp866','cp874','cp932','cp949','cp950','euc_jis_2004',
 'euc_jisx0213','euc_jp','euc_kr','gb18030','gb2312','gbk','hz','iso2022_jp','iso2022_jp_1',
 'iso2022_jp_2','iso2022_jp_2004','iso2022_jp_3','iso2022_jp_ext','iso2022_kr','iso8859-1',
 'iso8859-10','iso8859-11','iso8859-13','iso8859-14','iso8859-15','iso8859-16','iso8859-2',
 'iso8859-3','iso8859-4','iso8859-5','iso8859-6','iso8859-7','iso8859-8','iso8859-9','johab',
 'koi8-r','koi8-t','koi8-u','mac-cyrillic','mac-greek','mac-iceland','mac-latin2','mac-roman',
 'mac-turkish','ptcp154','shift_jis','shift_jis_2004','shift_jisx0213','tis-620','utf-16',
 'utf-16-be','utf-16-le','utf-32','utf-32-be','utf-32-le','utf-7','utf-8','utf-8-sig',
})
# Bodies a text decode would only waste work on. Their text is never built unless
# something asks for it (Response.text is lazy), so a 1.5 MB PDF or image costs
# nothing to decode.
_BINARY_TYPES=re.compile(r'^(?:image|audio|video|font)/|^application/(?:pdf|zip|octet-stream|x-|vnd\.(?!.*\+xml))',re.I)


def _web_charset(label):
    """A charset label as browsers use it: unknown labels and non-text codecs are
    ignored, and ISO-8859-1/ASCII mean windows-1252 (WHATWG Encoding)."""
    if not label:return None
    try:name=codecs.lookup(label.strip().strip('"\'').lower()).name
    except LookupError:return None
    if name not in _WEB_ENCODINGS:return None
    return 'cp1252' if name in ('latin_1','iso8859-1','ascii') else name


def decode_body(content,content_type='',provenance=None):
    """Text of a response body, decoded the way a browser does: byte order mark,
    then the HTTP charset, then <meta charset> / http-equiv in the first 2 KB,
    then UTF-8. A body sent as UTF-8 that is mostly invalid UTF-8 is read as
    windows-1252, so a mislabelled legacy page does not turn into replacement
    characters.

    provenance, when a dict is passed, is filled with which source decided the
    encoding and what was ignored, so a garbled page can be explained rather than
    guessed at."""
    note=provenance if provenance is not None else {}
    for bom,name in _BOMS:
        if content.startswith(bom):
            note.update(encoding=name,source='byte_order_mark')
            return content.decode(name,errors='replace')
    m=re.search(r'charset=["\']?([^;"\' ]+)',content_type or '',re.I)
    declared=m[1] if m else None
    charset=_web_charset(declared) if declared else None
    if charset:note.update(encoding=charset,source='http_content_type',declared=declared)
    elif declared:note.update(ignored_label=declared,ignored_reason='not a web text encoding')
    if charset is None:
        mm=_META_CHARSET.search(content[:2048])
        meta_label=mm[1].decode('ascii','ignore') if mm else None
        charset=_web_charset(meta_label) if meta_label else None
        if charset:note.update(encoding=charset,source='meta_charset',declared=meta_label)
        elif meta_label and 'ignored_label' not in note:
            note.update(ignored_label=meta_label,ignored_reason='not a web text encoding')
    if charset is None:
        charset='utf-8';note.update(encoding='utf-8',source='default')
    text=content.decode(charset,errors='replace')
    if charset=='utf-8' and text.count('\ufffd')>max(3,len(text)//200):
        note.update(encoding='cp1252',source='utf8_mostly_invalid_fallback')
        text=content.decode('cp1252',errors='replace')
    return text


class Response:
    def __init__(self,status,headers,content,url,truncated=False,hops=0):
        self.status_code=status;self.headers=headers;self.content=content;self.final_url=url
        self.truncated=truncated;self.redirect_hops=hops;self.history=[]
        self._text=None;self.encoding_provenance={}
    @property
    def text(self):
        """Decoded body, built on first use. A binary body (image, PDF, archive)
        decodes to nothing a caller wants, so it is not decoded at all unless
        something actually reads .text."""
        if self._text is None:
            ctype=self.headers.get('Content-Type','')
            if _BINARY_TYPES.match((ctype or '').split(';')[0].strip()):
                self.encoding_provenance={'encoding':None,'source':'binary_content_type','declared':ctype}
                self._text=''
            else:
                note={}
                self._text=decode_body(self.content,ctype,note)
                self.encoding_provenance=note
        return self._text
    @property
    def ok(self):return 200<=self.status_code<300

class Transport:
    def __init__(self,origin,deadline,limits,instrumentation,allow_private=False):
        self.origin=origin;self.deadline=deadline;self.limits=limits;self.i=instrumentation
        self.allow_private=allow_private;self.bytes=0;self.requests=0;self.last_request=0.
        self.diagnostics=[];self._address_attempts={};self.tls_settings={}
        # Cross-origin redirects are refused (scope and SSRF policy), but the
        # destination is recorded: a site whose /robots.txt redirects to its
        # canonical origin is a configuration fact the caller needs in order to
        # re-anchor deliberately instead of reporting an unreachable site.
        self.blocked_redirects=[]
        self.robots=None;self.delay=0. if allow_private else getattr(limits,'REQUEST_DELAY_S',.2)
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

    def get(self,url,*,robots_exempt=False,max_bytes=None,headers=None):
        network_elapsed=0.0
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
            timeout=min(self.limits.PER_FETCH_TIMEOUT_MS/1000,max(.001,self.deadline-time.monotonic()))
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
                        if len(self.blocked_redirects)<8:self.blocked_redirects.append({'from':url,'to':dest,'status':status})
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
                timer.cancel()
                timer.join(.1)
                conn.close()
                if conn_sock:conn_sock.close()
        return None,'too_many_redirects'

