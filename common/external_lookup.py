"""Bounded, read-only GETs to third-party hosts, with robots.txt read first.

One Transport per origin, so the same-origin redirect rule, the SSRF checks and
the request and byte caps all apply per host. Each host's robots.txt is fetched
before anything else on that host; when it cannot be read, nothing else is
requested there (fail closed). Every request is logged so a report can show
exactly what was fetched.
"""
import threading
import time
from urllib.parse import urlsplit

from robots_policy import RobotsPolicy
from transport import USER_AGENT

ROBOTS_MAX_BYTES = 512_000
# Outcomes that mean no request was sent, so they are not counted as fetches.
NOT_SENT = frozenset({"deadline", "budget_exhausted", "robots_disallowed", "robots_unavailable", "dns_error"})
# url_safety resolves names with a small, non-blocking pool of DNS workers, so a
# lookup that runs beside other lookups can be turned away; it is retried briefly.
DNS_RETRIES = 3


class ExternalLookup:
    """Robots-checked GETs to third-party hosts, one transport per origin.

    transport_factory(origin, deadline_monotonic, limits) builds the transport for
    an origin; tests inject a fake one so no test touches the network. Safe to
    share between threads; a single origin should be used from one thread at a
    time, because a transport paces its own requests.
    """

    def __init__(self, deadline_monotonic, limits, instrumentation, transport_factory):
        self.deadline = deadline_monotonic
        self.limits = limits
        self.instrumentation = instrumentation
        self.factory = transport_factory
        self.transports = {}
        self.robots = {}
        self.requests = []
        self._lock = threading.Lock()

    def _record(self, url, status, http_status=None):
        with self._lock:
            self.requests.append({"url": url, "status": status, "http_status": http_status})
        if self.instrumentation is not None and status not in NOT_SENT:
            self.instrumentation.record_external_fetch(ok=status == "ok")

    def _transport(self, origin):
        with self._lock:
            tr = self.transports.get(origin)
            if tr is not None:
                return tr
            tr = self.factory(origin, self.deadline, self.limits)
            self.transports[origin] = tr
            self.robots[origin] = "pending"
        robots_url = origin + "/robots.txt"
        resp, status = self._fetch(tr, robots_url, robots_exempt=True, max_bytes=ROBOTS_MAX_BYTES)
        self._record(robots_url, status, resp.status_code if resp else None)
        text = None
        if status == "ok" and resp.status_code in (404, 410):
            text = ""
        elif status == "ok" and resp.status_code == 200 and not resp.truncated:
            try:
                text = resp.content.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None and text.lstrip().lower().startswith(("<html", "<!doctype")):
                text = None
        if text is None:
            # Fail closed: without readable robots rules nothing else is requested.
            tr.robots = RobotsPolicy("User-agent: *\nDisallow: /")
            outcome = "unavailable"
        else:
            tr.robots = RobotsPolicy(text)
            tr.delay = max(tr.delay, tr.robots.crawl_delay(USER_AGENT))
            outcome = "ok"
        with self._lock:
            self.robots[origin] = outcome
        return tr

    def get(self, url, max_bytes, headers=None):
        origin = _origin(url)
        tr = self._transport(origin)
        if self.robots.get(origin) != "ok":
            self._record(url, "robots_unavailable")
            return None, "robots_unavailable"
        resp, status = self._fetch(tr, url, max_bytes=max_bytes, headers=headers or {"Accept-Encoding": "gzip"})
        self._record(url, status, resp.status_code if resp else None)
        return resp, status

    def _fetch(self, tr, url, **kwargs):
        for attempt in range(DNS_RETRIES + 1):
            resp, status = tr.get(url, **kwargs)
            pause = 0.25 * (attempt + 1)
            if status != "dns_error" or attempt == DNS_RETRIES or time.monotonic() + pause >= self.deadline:
                return resp, status
            time.sleep(pause)
        return resp, status


def _origin(url):
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"
