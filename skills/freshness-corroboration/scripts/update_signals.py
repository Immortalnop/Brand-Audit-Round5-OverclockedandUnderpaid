"""update_signals.py -- is the sitemap's <lastmod> a usable record of change?

Search engines and AI crawlers use sitemap <lastmod> to decide which URLs to
re-fetch. Two patterns make it useless, and both are visible in the sitemap the
acquisition stage already read (no requests here):

  - no <lastmod> at all on a sitemap with several URL entries;
  - one date stamped on (nearly) every entry: the sitemap is generated at build
    or deploy time, so lastmod records the build, not content changes.

A small sitemap (under MIN_ENTRIES entries) is not judged. Dates that do not
parse are ignored rather than counted against the site.
"""
import re
from collections import Counter

from models import make_finding, skill_result

MIN_ENTRIES = 5
UNIFORM_SHARE = 0.8
_W3C = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def lastmod_day(value):
    """The YYYY-MM-DD day of a W3C Datetime value, or None."""
    m = _W3C.match(str(value or "").strip())
    return m.group(0) if m else None


def lastmod_quality(sitemap):
    """{'entries', 'with_lastmod', 'problem', 'detail'}; problem is None,
    'missing' or 'uniform'."""
    entries = int(sitemap.get("url_entries") or len(sitemap.get("urls") or ()))
    with_lastmod = int(sitemap.get("lastmod_entries") or len(sitemap.get("lastmod") or {}))
    out = {"entries": entries, "with_lastmod": with_lastmod, "problem": None, "detail": ""}
    if sitemap.get("status") != "ok" or entries < MIN_ENTRIES:
        return out
    if with_lastmod == 0:
        out.update(problem="missing", detail=f"None of the {entries} sitemap URL entries declares <lastmod>")
        return out
    days = [d for d in (lastmod_day(v) for v in (sitemap.get("lastmod") or {}).values()) if d]
    if len(days) >= MIN_ENTRIES:
        day, count = Counter(days).most_common(1)[0]
        if count / len(days) >= UNIFORM_SHARE:
            out.update(problem="uniform",
                       detail=f"{count} of {len(days)} sampled <lastmod> values are the same day ({day}): the "
                              "sitemap appears to be stamped at build time")
    return out


def check_sitemap_lastmod(artifacts, deadline):
    sitemap = artifacts.sitemap_data or {}
    q = lastmod_quality(sitemap)
    findings = []
    if q["problem"]:
        sitemap_url = artifacts.normalized_origin.rstrip("/") + "/sitemap.xml"
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="low", status="confirmed",
            confidence=0.85,
            title=("Sitemap entries carry no <lastmod> dates" if q["problem"] == "missing"
                   else "Sitemap <lastmod> dates are stamped at build time"),
            root_cause=q["detail"] + ", so crawlers cannot tell which pages changed.",
            evidence=[{"type": "sitemap_lastmod", "description": q["detail"], "urls": [sitemap_url]}],
            affected_pages=[],
            suggested_action={
                "summary": "Emit <lastmod> from each page's real content-modified time",
                "steps": ["Generate <lastmod> per URL from the CMS last-modified time of that page",
                          "Do not use the build or deploy time; leave lastmod out rather than guess",
                          "Update the value only when the page content really changes"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Changed pages are re-crawled sooner",
                "verification": "Sitemap lastmod values differ by page and match each page's last edit"},
            provenance={"skill": "freshness-corroboration", "script": "update_signals.py",
                        "rule_id": "sitemap-lastmod-unreliable"}))
    return skill_result("freshness-corroboration", findings=findings,
                        metrics={"sitemap_url_entries": q["entries"], "sitemap_lastmod_entries": q["with_lastmod"],
                                 "sitemap_lastmod_problem": q["problem"]})
