"""Optional Core Web Vitals field data (LCP, CLS, INP) from real Chrome users.

The default audit runs no browser, so it cannot measure Core Web Vitals. When a
PageSpeed Insights API key is configured (PAGESPEED_API_KEY), this module asks the
public PageSpeed Insights API, by one plain GET, for the Chrome UX Report field
data of the audited URL, falling back to its origin. The request starts in a
background thread when the audit starts, so the API's latency overlaps the crawl.

Rules that apply to every third-party request here also apply to this one: the
API host's robots.txt is read first (fail closed), the request is GET only and
goes through the SSRF-checked transport, and it is bounded in time and bytes. The
key is never written to the report. Without a key, or with
FIELD_VITALS_LOOKUP=0, nothing is requested and the audit reports static
estimates only. The keyless API shares one small daily quota across all users,
so it is not used.
"""
import json
import os
import threading
from dataclasses import replace
from time import monotonic
from urllib.parse import urlencode

from external_lookup import ROBOTS_MAX_BYTES, ExternalLookup
from instrumentation import Instrumentation
from transport import Transport

KEY_ENV = "PAGESPEED_API_KEY"
LOOKUP_ENV = "FIELD_VITALS_LOOKUP"
API_ORIGIN = "https://www.googleapis.com"
API_PATH = "/pagespeedonline/v5/runPagespeed"
_BUDGET_S = 60.0
_MAX_BYTES = 1_000_000

# Thresholds from web.dev (75th percentile of page loads).
THRESHOLDS = {"LCP": (2500.0, 4000.0), "CLS": (0.10, 0.25), "INP": (200.0, 500.0)}
UNITS = {"LCP": "ms", "CLS": "", "INP": "ms"}
_API_METRICS = {
    "LCP": ("LARGEST_CONTENTFUL_PAINT_MS",),
    "CLS": ("CUMULATIVE_LAYOUT_SHIFT_SCORE",),
    "INP": ("INTERACTION_TO_NEXT_PAINT", "EXPERIMENTAL_INTERACTION_TO_NEXT_PAINT"),
}


def lookup_enabled():
    return bool(os.environ.get(KEY_ENV, "").strip()) and os.environ.get(LOOKUP_ENV) != "0"


def rate(metric, value):
    good, poor = THRESHOLDS[metric]
    if value <= good:
        return "good"
    return "needs_improvement" if value <= poor else "poor"


def parse_experience(block):
    """{metric: {'p75': value, 'rating': ...}} from one loadingExperience block.
    CLS arrives multiplied by 100 and is scaled back."""
    out = {}
    metrics = (block or {}).get("metrics") if isinstance(block, dict) else None
    if not isinstance(metrics, dict):
        return out
    for name, keys in _API_METRICS.items():
        entry = next((metrics[k] for k in keys if isinstance(metrics.get(k), dict)), None)
        value = entry.get("percentile") if entry else None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            continue
        value = value / 100.0 if name == "CLS" else float(value)
        out[name] = {"p75": round(value, 3), "rating": rate(name, value)}
    return out


def parse_response(data):
    """Field data for the URL when the API has it, otherwise for the origin."""
    if not isinstance(data, dict):
        return {"status": "malformed_response"}
    page = data.get("loadingExperience")
    page_metrics = parse_experience(page)
    if page_metrics and not (isinstance(page, dict) and page.get("origin_fallback")):
        return {"status": "ok", "scope": "url", "metrics": page_metrics}
    origin_metrics = parse_experience(data.get("originLoadingExperience")) or page_metrics
    if origin_metrics:
        return {"status": "ok", "scope": "origin", "metrics": origin_metrics}
    return {"status": "no_field_data"}


def _api_transport(origin, deadline_monotonic, limits):
    bounded = replace(limits, MAX_TOTAL_HTTP_REQUESTS=3, MAX_TOTAL_BYTES=ROBOTS_MAX_BYTES + _MAX_BYTES,
                      MAX_RESPONSE_BYTES=_MAX_BYTES, PER_FETCH_TIMEOUT_MS=int(_BUDGET_S * 1000))
    return Transport(origin, deadline_monotonic, bounded, Instrumentation(), allow_private=False,
                     pool="external", stage="pagespeed_api")


def fetch_field_vitals(url, deadline_monotonic, limits, instrumentation=None, transport_factory=None):
    key = os.environ.get(KEY_ENV, "").strip()
    query = urlencode({"url": url, "strategy": "mobile", "category": "performance",
                       "fields": "loadingExperience,originLoadingExperience", "key": key})
    lookup = ExternalLookup(deadline_monotonic, limits, instrumentation, transport_factory or _api_transport)
    resp, status = lookup.get(API_ORIGIN + API_PATH + "?" + query, _MAX_BYTES)
    if status != "ok":
        return {"status": status}
    if not resp.ok:
        return {"status": f"http_{resp.status_code}"}
    if resp.truncated:
        return {"status": "response_too_large"}
    try:
        return parse_response(json.loads(resp.content.decode("utf-8")))
    except (ValueError, UnicodeDecodeError):
        return {"status": "malformed_response"}


class FieldVitalsHandle:
    """A field-data request running in the background since the audit started."""

    def __init__(self, url, deadline, limits, instrumentation=None, transport_factory=None):
        self._result = None
        end = min(monotonic() + _BUDGET_S, deadline.deadline_monotonic - limits.FINALIZATION_RESERVE_S)

        def run():
            try:
                self._result = fetch_field_vitals(url, end, limits, instrumentation, transport_factory)
            except Exception as exc:  # a failed lookup is a limitation, never an audit failure
                self._result = {"status": "failed", "error": type(exc).__name__}

        self._thread = threading.Thread(target=run, name="field-vitals", daemon=True)
        self._thread.start()

    def result(self, timeout):
        self._thread.join(max(0.0, timeout))
        return self._result if self._result is not None else {"status": "deadline"}


def start_field_lookup(url, deadline, limits, instrumentation=None, allow_private_targets=False,
                       transport_factory=None):
    """A running handle, or None when field data is not configured or the target
    is a private test host the public API could not reach anyway."""
    if allow_private_targets or not lookup_enabled():
        return None
    return FieldVitalsHandle(url, deadline, limits, instrumentation, transport_factory)
