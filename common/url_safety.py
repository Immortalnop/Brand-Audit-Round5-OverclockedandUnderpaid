"""url_safety.py -- SSRF protection for every outbound fetch the audit makes
(initial URL, discovered links, sitemap URLs, redirect targets, browser
navigations). Applied before any request is issued, never after.

Policy:
  - only http/https are ever fetched
  - credentials embedded in the URL (user:pass@host) are rejected
  - known cloud-metadata hosts/IPs are always rejected, even with allow_private
  - the hostname is resolved and EVERY returned address is checked -- a
    hostname that resolves to more than one IP is only safe if all of them are
  - by default (allow_private=False) loopback, private, link-local, multicast,
    unspecified, and reserved ranges are all rejected
  - DNS resolution failure is treated as unsafe (fail closed), not skipped

`allow_private=True` exists only so local test fixtures (a ThreadingHTTPServer
on 127.0.0.1) can be exercised; production callers (run_audit's default) never
set it.
"""
from __future__ import annotations
import ipaddress
import re
import socket
import threading
import queue
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https"}

# Cloud metadata endpoints: blocked unconditionally, even with allow_private,
# because there is never a legitimate reason for a website audit to reach them.
_BLOCKED_HOSTS = {
    "metadata.google.internal",
    "metadata.goog",
}
_BLOCKED_IPS = {
    "169.254.169.254",  # AWS/GCP/Azure/most clouds' instance-metadata address
    "fd00:ec2::254",     # AWS IMDS IPv6
}


@dataclass(frozen=True)
class UrlSafetyResult:
    safe: bool
    reason: Optional[str]  # None when safe
    addresses: tuple = ()


_DNS_SLOTS = threading.BoundedSemaphore(2)
DNS_LOOKUP_TIMEOUT_S = 2.0

def _resolve(hostname: str):
    """Returns a list of ipaddress objects, or raises socket.gaierror."""
    if not _DNS_SLOTS.acquire(blocking=False):raise socket.gaierror("DNS worker capacity reached")
    mailbox=queue.Queue(maxsize=1)
    def lookup():
        try:mailbox.put((socket.getaddrinfo(hostname,None),None))
        except Exception as exc:mailbox.put((None,exc))
        finally:_DNS_SLOTS.release()
    threading.Thread(target=lookup,daemon=True).start()
    try:infos,error=mailbox.get(timeout=DNS_LOOKUP_TIMEOUT_S)
    except queue.Empty:raise socket.gaierror("DNS lookup exceeded bounded timeout") from None
    if error:raise error
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def _ip_is_blocked(ip: "ipaddress._BaseAddress", allow_private: bool) -> Optional[str]:
    if str(ip) in _BLOCKED_IPS:
        return "cloud_metadata_address"
    if allow_private:
        return None
    if ip.is_loopback:
        return "loopback_address"
    if ip.is_link_local:
        return "link_local_address"
    if ip.is_multicast:
        return "multicast_address"
    if ip.is_unspecified:
        return "unspecified_address"
    if ip.is_private:
        return "private_address"
    if ip.is_reserved:
        return "reserved_address"
    return None


def classify_url(url: str, *, allow_private: bool = False) -> UrlSafetyResult:
    """The single choke point every outbound fetch must pass through first."""
    try:
        parts = urlsplit(url)
        _ = parts.port
        if any(ord(c) < 32 for c in url):
            return UrlSafetyResult(False, "control_character")
    except ValueError:
        return UrlSafetyResult(False, "unparseable_url")

    scheme = (parts.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return UrlSafetyResult(False, f"disallowed_scheme:{scheme or 'none'}")

    if parts.username or parts.password:
        return UrlSafetyResult(False, "credentials_in_url")

    hostname = parts.hostname
    if not hostname:
        return UrlSafetyResult(False, "no_hostname")

    hostname_lower = hostname.lower().rstrip(".")
    if hostname_lower in _BLOCKED_HOSTS:
        return UrlSafetyResult(False, "cloud_metadata_hostname")

    # A literal IP in the URL is checked directly; a DNS name is resolved and
    # every returned address is checked. The transport pins the connection to
    # one of these validated addresses; it does not resolve the name again.
    try:
        ips = _resolve(hostname_lower)
    except socket.gaierror:
        return UrlSafetyResult(False, "dns_resolution_failed")
    except Exception:
        return UrlSafetyResult(False, "dns_resolution_error")

    if not ips:
        return UrlSafetyResult(False, "dns_resolution_failed")

    for ip in ips:
        reason = _ip_is_blocked(ip, allow_private)
        if reason:
            return UrlSafetyResult(False, reason)

    return UrlSafetyResult(True, None, tuple(sorted({str(ip) for ip in ips})))


def is_safe_url(url: str, *, allow_private: bool = False) -> bool:
    return classify_url(url, allow_private=allow_private).safe


def same_origin(url: str, origin: str) -> bool:
    def key(value):
        p = urlsplit(value)
        host = (p.hostname or '').lower().rstrip('.')
        host = re.sub(r'^www\d*\.', '', host)
        return p.scheme.lower(), host, p.port or (443 if p.scheme == 'https' else 80)
    try:
        return key(url) == key(origin)
    except ValueError:
        return False

