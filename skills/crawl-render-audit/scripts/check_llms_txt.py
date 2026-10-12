"""check_llms_txt.py -- presence/validity is a metric; absence is proactive only.
llms.txt is now actually fetched by acquire_site.py (it was
previously hardcoded to "not present" regardless of reality); this script
distinguishes a confirmed 404 ("absent" -- worth a proactive suggestion) from a
fetch that failed or was blocked ("inaccessible"/"blocked" -- insufficient
evidence, never reported as a confirmed absence)."""
from models import skill_result, make_finding, apply_invariant_i1


def check_llms_txt(artifacts, deadline):
    present = artifacts.llms_txt_data.get("present", False)
    status = artifacts.llms_txt_data.get("status", "not_checked")
    findings = []

    if not present and status == "absent":
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.6,
            title="No llms.txt file found",
            root_cause="Site does not publish an llms.txt guidance file",
            evidence=[{"type": "llms_txt", "description": "/llms.txt returned 404",
                       "urls": [artifacts.normalized_origin.rstrip('/') + "/llms.txt"]}],
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
                       "urls": [artifacts.normalized_origin.rstrip('/') + "/llms.txt"]}],
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

    return skill_result("crawl-render-audit", findings=findings,
                         metrics={"llms_txt_present": present, "llms_txt_status": status})
