"""check_llms_txt.py -- presence/validity is a metric; absence is proactive only.
llms.txt is now actually fetched by acquire_site.py (it was
previously hardcoded to "not present" regardless of reality); this script
distinguishes a confirmed 404 ("absent" -- worth a proactive suggestion) from a
fetch that failed or was blocked ("inaccessible"/"blocked" -- insufficient
evidence, never reported as a confirmed absence).

When llms.txt is present, acquisition also parses it (common/llms_txt.py) and
checks that the pages it lists resolve: crawled pages reuse the crawl result,
others get a bounded, robots-checked, same-origin GET. It also probes the
companion /llms-full.txt. This script reports:
  - llms-txt-invalid: the file does not follow the llms.txt format (no H1 title,
    no links, bare URLs, links not grouped in sections), or llms-full.txt is
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

    if not present and status == "absent":
        evidence = [{"type": "llms_txt", "description": "/llms.txt returned 404",
                     "urls": [_url(artifacts, "/llms.txt")]}]
        if full.get("present"):
            evidence.append({"type": "llms_txt", "description": "/llms-full.txt exists, but the /llms.txt "
                                                                "index that points to it does not",
                             "urls": [_url(artifacts, "/llms-full.txt")]})
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=calibrated_confidence("no-llms-txt", 0.9),
            title="No llms.txt file found",
            root_cause="Site does not publish an llms.txt guidance file",
            evidence=evidence,
            suggested_action={
                "summary": "Publish an llms.txt summarizing key pages for AI assistants",
                "steps": ["Create /llms.txt", "List key pages and a short site summary"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Offers an optional guide to tools that support this convention; not a search eligibility requirement",
                "verification": "Confirm /llms.txt is reachable and valid",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_llms_txt.py",
                        "rule_id": "no-llms-txt"},
        ))
    elif not present and status in ("inaccessible", "blocked", "malformed"):
        findings.append(apply_invariant_i1(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="insufficient_evidence", confidence=0.3,
            title="llms.txt could not be checked",
            root_cause=f"/llms.txt fetch status was '{status}'",
            evidence=[{"type": "llms_txt", "description": f"/llms.txt status: {status}",
                       "urls": [_url(artifacts, "/llms.txt")]}],
            suggested_action={
                "summary": "Confirm /llms.txt is reachable and re-run the audit",
                "steps": ["Check that /llms.txt responds", "Re-run the audit"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Enables a real presence/absence verdict",
                "verification": "Re-run and confirm llms_txt_data.status is 'ok' or 'absent'",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_llms_txt.py",
                        "rule_id": "llms-txt-unchecked"},
        )))

    format_problems = []
    if present:
        format_problems.extend(data.get("structure_issues", ()))
    if full.get("status") == "malformed":
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
                "expected_benefit": "Tools that support llms.txt can follow it to the key pages",
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
            root_cause="llms.txt points assistants at pages that answer 404 or 410, so the guide sends them "
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
                "expected_benefit": "Every page llms.txt points to can be read",
                "verification": "Re-run the audit and confirm no llms.txt link is broken",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_llms_txt.py",
                        "rule_id": "llms-txt-broken-links"},
        ))

    summary = dict(data.get("link_summary") or {})
    return skill_result("crawl-render-audit", findings=findings,
                        metrics={"llms_txt_present": present, "llms_txt_status": status,
                                 "llms_txt_links": data.get("link_count", 0),
                                 "llms_txt_links_checked": sum(v for k, v in summary.items()
                                                               if k in ("ok", "broken")),
                                 "llms_txt_link_outcomes": {k: v for k, v in summary.items() if k != "requests"},
                                 "llms_full_txt_status": full.get("status", "not_checked"),
                                 "llms_full_txt_present": bool(full.get("present"))})
