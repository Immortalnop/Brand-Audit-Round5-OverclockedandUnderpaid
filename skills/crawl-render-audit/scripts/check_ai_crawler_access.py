"""check_ai_crawler_access.py -- compares general vs AI-specific robots verdicts.
When robots.txt could not be retrieved/parsed, directives are
empty and this reports insufficient evidence rather than silently implying
AI crawlers are allowed."""
from models import skill_result, make_finding, apply_invariant_i1


def check_ai_crawler_access(artifacts, deadline):
    directives = artifacts.robots_data.get("ai_crawler_directives", {})
    robots_status = artifacts.robots_data.get("status", "not_checked")
    blocked = [agent for agent, verdict in directives.items() if verdict == "disallow"]

    findings = []
    if not directives and robots_status not in ("ok", "absent", "not_checked"):
        findings.append(apply_invariant_i1(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="insufficient_evidence", confidence=0.3,
            title="AI-crawler access could not be checked",
            root_cause=f"robots.txt status was '{robots_status}'; AI-crawler directives were not evaluated",
            evidence=[{"type": "robots", "description": f"robots.txt status: {robots_status}", "urls": []}],
            suggested_action={
                "summary": "Confirm robots.txt is reliably reachable", "steps": ["Re-run once reachable"],
                "priority": "low", "effort": "low", "expected_benefit": "Enables a real verdict",
                "verification": "Re-run and confirm robots_data.status is 'ok' or 'absent'",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_ai_crawler_access.py",
                        "rule_id": "ai-crawler-unchecked"},
        )))
    search_bots = {"OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "Googlebot"}
    search_blocked = sorted(set(blocked) & search_bots)
    if blocked:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect" if search_blocked else "proactive_improvement", severity="high" if search_blocked else "low",
            status="confirmed", confidence=0.9,
            title="AI crawlers are blocked by robots.txt" if search_blocked
            else "robots.txt blocks training or user-fetch AI crawlers: " + ", ".join(blocked),
            root_cause=f"robots.txt disallows: {', '.join(blocked)}. Search, model-training and user-triggered retrieval controls have different effects; training exclusions do not establish search exclusion.",
            evidence=[{"type": "robots", "description": "AI crawler directives disallow access",
                       "urls": [artifacts.site_url]}],
            suggested_action={
                "summary": "Review crawler access against the intended search and training policy",
                "steps": [f"Review the {a} rule; change only if the exclusion is unintended" for a in blocked],
                "priority": "high" if search_blocked else "low", "effort": "low",
                "expected_benefit": "Restores access for selected crawlers; citation is not guaranteed",
                "verification": "Re-check robots.txt for the listed user-agents",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_ai_crawler_access.py",
                        "rule_id": "ai-crawler-blocked"},
        ))

    return skill_result("crawl-render-audit", findings=findings, metrics={"blocked_ai_crawlers": blocked})
