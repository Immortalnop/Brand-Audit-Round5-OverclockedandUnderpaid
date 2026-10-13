"""check_llms_txt.py -- observation and repair of an optional supplied artifact.
llms.txt is now actually fetched by acquire_site.py (it was
previously hardcoded to "not present" regardless of reality); this script
distinguishes a confirmed 404 ("absent", observation only) from a
fetch that failed or was blocked ("inaccessible"/"blocked" -- insufficient
evidence, never reported as a confirmed absence).

When llms.txt is present, acquisition also parses it (common/llms_txt.py) and
checks that the pages it lists resolve: crawled pages reuse the crawl result,
others get a bounded, robots-checked, same-origin GET. It also probes the
companion /llms-full.txt. This script reports:
  - llms-txt-invalid: the file does not follow the llms.txt format (no H1 title or duplicate H1 titles), or llms-full.txt is
    served as an HTML page.
  - llms-txt-broken-links: pages listed in llms.txt answer 404 or 410.
A link that could not be checked (cross-origin, robots rules, the request cap, a
server error) is counted in metrics, never reported as broken.
"""
from check_catalog import calibrated_confidence
from models import skill_result, make_finding, apply_invariant_i1


def _url(artifacts, path):
    return artifacts.normalized_origin.rstrip('/') + path


def check_llms_txt(artifacts, deadline):
    data = artifacts.llms_txt_data
    present = data.get("present", False)
    status = data.get("status", "not_checked")
    full = data.get("full") or {}
    findings = []

    # Absence/fetch failure is observation only. No declared consumer means no
    # automatic publishing task or website/Google visibility penalty.
    format_problems = []
    if present:
        format_problems.extend(data.get("structure_issues", ()))
    # The companion file is judged only beside a published llms.txt: a site that
    # answers every unknown path with its HTML home page publishes neither file,
    # which is not a malformed one.
    if full.get("status") == "malformed" and present:
        format_problems.append("/llms-full.txt answers with an HTML page instead of a text file"
                               if full.get("served_html") else
                               "/llms-full.txt is empty or redirects to a different path")
    if format_problems:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.8,
            title="llms.txt does not follow the llms.txt format",
            root_cause="Tools that read llms.txt expect an H1 title and sections of Markdown links; a file "
                       "without them, or an HTML page served as llms-full.txt, gives them nothing to follow",
            evidence=[{"type": "llms_txt", "description": problem,
                       "urls": [_url(artifacts, "/llms-full.txt" if "llms-full" in problem else "/llms.txt")]}
                      for problem in format_problems],
            suggested_action={
                "summary": "Rewrite llms.txt in the llms.txt format",
                "steps": ["Start the file with one H1 line naming the site ('# Name')",
                          "Add a one-line '>' summary under the title",
                          "List key pages under H2 sections as Markdown links: '- [Page name](url): note'",
                          "Serve /llms-full.txt as plain text, or answer 404 if it does not exist"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Readers deliberately configured to use this supplied artifact can follow its links; Google Search ignores llms.txt",
                "verification": "Re-run the audit and confirm no format problem is listed",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_llms_txt.py",
                        "rule_id": "llms-txt-invalid"},
        ))

    checks = list(data.get("link_checks", ()))
    broken = [c for c in checks if c.get("status") == "broken"]
    if broken:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="medium",
            status="confirmed", confidence=0.9,
            title="llms.txt lists pages that do not exist",
            root_cause="The supplied llms.txt artifact points its readers at pages that answer 404 or 410, so the guide sends them "
                       "to dead ends instead of the content it promises",
            evidence=[{"type": "llms_txt",
                       "description": f"{len(broken)} of {len(checks)} checked llms.txt link(s) answer "
                                      + ", ".join(f"HTTP {c.get('http_status')} for {c['url']}" for c in broken[:5]),
                       "urls": [_url(artifacts, "/llms.txt")]}],
            affected_pages=[_url(artifacts, "/llms.txt")],
            suggested_action={
                "summary": "Fix or remove the dead links in llms.txt",
                "steps": ["Update each listed URL to the page's current address, or remove the entry",
                          "Regenerate llms.txt whenever pages move"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "The supplied artifact no longer directs its configured readers to known dead links; visibility gains are unmeasured",
                "verification": "Re-run the audit and confirm no llms.txt link is broken",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_llms_txt.py",
                        "rule_id": "llms-txt-broken-links"},
        ))

    summary = dict(data.get("link_summary") or {})
    return skill_result("crawl-render-audit", findings=findings,
                        metrics={"llms_txt_present": present, "google_search_uses_llms_txt": False, "llms_txt_scope": "optional supplied artifact; intended reader must be identified", "llms_txt_status": status,
                                 "llms_txt_links": data.get("link_count", 0), 'llms_txt_optional_format_advice': list(data.get('format_advice') or ()),
                                 "llms_txt_links_checked": sum(v for k, v in summary.items()
                                                               if k in ("ok", "broken")),
                                 "llms_txt_link_outcomes": {k: v for k, v in summary.items() if k != "requests"},
                                 "llms_full_txt_status": full.get("status", "not_checked"),
                                 "llms_full_txt_present": bool(full.get("present"))})
