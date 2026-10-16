"""check_ai_crawler_access.py -- compares general vs AI-specific robots verdicts.
When robots.txt could not be retrieved/parsed, directives are
empty and this reports insufficient evidence rather than silently implying
AI crawlers are allowed."""
from models import skill_result, make_finding, apply_invariant_i1
from ai_crawlers import SEARCH_CRAWLERS, describe, group_by_purpose, purpose_of, PURPOSE_LABELS


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
    search_bots = SEARCH_CRAWLERS
    search_blocked = sorted(set(blocked) & search_bots)
    if blocked:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect" if search_blocked else "proactive_improvement", severity="high" if search_blocked else "low",
            status="confirmed", confidence=0.9,
            title="AI search crawlers are blocked by robots.txt: " + ", ".join(search_blocked) if search_blocked
            else "robots.txt blocks training or user-fetch AI crawlers: " + ", ".join(blocked),
            root_cause=f"robots.txt disallows ({describe(blocked)}). Search, model-training and user-triggered "
                       "retrieval controls have different effects; training exclusions do not establish search "
                       "exclusion.",
            evidence=[{"type": "robots", "description": f"robots.txt disallows the {PURPOSE_LABELS[purpose]} "
                                                        f"crawler(s) {', '.join(names)} for the start URL",
                       "urls": [artifacts.site_url]} for purpose, names in group_by_purpose(blocked).items()],
            suggested_action={
                "summary": "Review crawler access against the intended search and training policy",
                "steps": [f"Review the {a} rule; change only if the exclusion is unintended" for a in blocked]
                         + ["If blocking is a deliberate content or licensing decision, keep it: this finding "
                            "records its cost in AI search visibility, not a configuration error"],
                "priority": "high" if search_blocked else "low", "effort": "low",
                "expected_benefit": "Restores access for selected crawlers; citation is not guaranteed",
                "verification": "Re-check robots.txt for the listed user-agents",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_ai_crawler_access.py",
                        "rule_id": "ai-crawler-blocked"},
        ))

    # Sections closed to AI crawlers that robots.txt leaves open to crawlers in
    # general (acquire_site._ai_crawler_section_blocks). Crawlers already blocked
    # from the whole site are reported above, not again per section.
    sections = {agent: urls for agent, urls in (artifacts.robots_data.get("ai_crawler_section_blocks") or {}).items()
                if agent not in blocked and urls}
    if sections:
        search_sections = sorted(set(sections) & search_bots)
        urls = sorted({u for us in sections.values() for u in us})
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect" if search_sections else "proactive_improvement",
            severity="medium" if search_sections else "low", status="confirmed", confidence=0.9,
            title=("AI search crawlers are blocked from some site sections" if search_sections
                   else "robots.txt blocks training or user-fetch AI crawlers from some site sections"),
            root_cause="robots.txt rules for " + describe(sections) + " disallow sections of the site that "
                       "it leaves open to other crawlers, so those sections cannot be read or cited by these crawlers",
            affected_pages=urls,
            evidence=[{"type": "robots", "description": f"{agent} ({PURPOSE_LABELS[purpose_of(agent)]}) may not fetch: "
                                                        + ", ".join(us[:5]),
                       "urls": list(us[:5])} for agent, us in sorted(sections.items())],
            suggested_action={
                "summary": "Review the section rules for AI crawlers against the intended search and training policy",
                "steps": [f"Review the {agent} rules that cover {', '.join(us[:3])}" for agent, us in sorted(sections.items())]
                         + ["If the exclusion is deliberate, keep it: this finding records its effect on AI visibility"],
                "priority": "medium" if search_sections else "low", "effort": "low",
                "expected_benefit": "Content sections become readable by the AI crawlers that cite sources",
                "verification": "Re-check robots.txt for the listed user-agents and paths",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_ai_crawler_access.py",
                        "rule_id": "ai-crawler-section-blocked"},
        ))

    return skill_result("crawl-render-audit", findings=findings,
                        metrics={"blocked_ai_crawlers": blocked, "ai_crawler_section_blocks": sorted(sections),
                                 "ai_crawler_purposes": {name: purpose_of(name) for name in directives}})
