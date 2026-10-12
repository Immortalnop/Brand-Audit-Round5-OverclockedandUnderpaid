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
class Response:
    def __init__(self,status,headers,content,url,truncated=False,hops=0):
        self.status_code=status;self.headers=headers;self.content=content;self.final_url=url
        self.truncated=truncated;self.redirect_hops=hops;self.history=[]
        charset='utf-8'
        import re
        m=re.search(r'charset=["\']?([^;"\' ]+)',headers.get('Content-Type',''),re.I)
        if m:charset=m[1]
        try:self.text=content.decode(charset,errors='replace')
        except LookupError:self.text=content.decode('utf-8',errors='replace')
    @property
    def ok(self):return 200<=self.status_code<300

class Transport:
    def __init__(self,origin,deadline,limits,instrumentation,allow_private=False):
        self.origin=origin;self.deadline=deadline;self.limits=limits;self.i=instrumentation
        self.allow_private=allow_private;self.bytes=0;self.requests=0;self.last_request=0.
        self.diagnostics=[];self._address_attempts={};self.tls_settings={}
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

