"""check_ai_crawler_access.py -- which search and AI agents may fetch the key pages?

Every agent in common/constants.AI_AGENTS is evaluated against robots.txt for
the key URLs the crawl actually sampled (homepage, one URL per key intent such as
/pricing or /blog, the sitemap and /llms.txt), not just '/'. A block is weighted by
the agent's role:

  search_index  Googlebot, Bingbot                -> critical (classic search, AI
                Overviews/AI Mode, and Bing-backed ChatGPT search and Copilot)
  ai_search     OAI-SearchBot, PerplexityBot, ... -> high
  user_fetch    ChatGPT-User, Claude-User, ...    -> high (the assistant cannot
                read the page live when a user asks about it)
  training      GPTBot, ClaudeBot, CCBot, ...     -> low, proactive: a legitimate
                policy choice that does not remove the site from AI search

When robots.txt could not be retrieved/parsed, directives are unknown and this
reports insufficient evidence rather than implying either allow or disallow.
"""
from collections import defaultdict
from models import skill_result, make_finding, apply_invariant_i1
from constants import AI_AGENT_ROLE

_ROLE_RULE = {
    'search_index': ('search-crawler-blocked', 'critical', 'defect',
                     'Search-engine crawlers are blocked from key pages'),
    'ai_search': ('ai-crawler-blocked', 'high', 'defect',
                  'AI search crawlers are blocked from key pages'),
    'user_fetch': ('user-fetch-blocked', 'high', 'defect',
                   'User-triggered AI fetchers are blocked from key pages'),
    'training': ('training-crawler-blocked', 'low', 'proactive_improvement',
                 'Training-only AI crawlers are excluded (policy check)'),
}

CHECK_IDS = frozenset({'ai-crawler-unchecked'} | {rule for rule, *_ in _ROLE_RULE.values()})


def check_ai_crawler_access(artifacts, deadline):
    directives = artifacts.robots_data.get("ai_crawler_directives", {})
    paths = {k: list(v) for k, v in dict(artifacts.robots_data.get("ai_crawler_paths", {}) or {}).items()}
    robots_status = artifacts.robots_data.get("status", "not_checked")
    # A root-level disallow counts even when no path detail exists.
    for agent, verdict in directives.items():
        if verdict == "disallow" and agent not in paths:
            paths[agent] = [artifacts.site_url]
    blocked = sorted(paths)

    findings = []
    if not directives and robots_status not in ("ok", "absent", "not_checked", "challenged"):
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

    by_role = defaultdict(list)
    for agent in blocked:
        by_role[AI_AGENT_ROLE.get(agent, 'training')].append(agent)
    for role in ('search_index', 'ai_search', 'user_fetch', 'training'):
        agents = by_role.get(role)
        if not agents:
            continue
        rule_id, severity, ftype, title = _ROLE_RULE[role]
        urls = sorted({u for a in agents for u in paths[a]})
        root_blocked = [a for a in agents if directives.get(a) == "disallow"]
        detail = "; ".join(f"{a}: disallowed on {', '.join(paths[a][:4])}" + (" ..." if len(paths[a]) > 4 else "")
                           for a in agents)
        findings.append(make_finding(
            category="ai_discoverability", finding_type=ftype, severity=severity, status="confirmed",
            confidence=0.95, title=title,
            root_cause=(f"robots.txt disallows {', '.join(agents)}"
                        + (" for the whole site" if len(root_blocked) == len(agents) else " on sampled key URLs")
                        + (". Training exclusions do not establish search exclusion; this is reported so the policy "
                           "can be confirmed as intentional." if role == 'training' else ".")),
            evidence=[{"type": "robots", "description": detail, "urls": urls[:10]}],
            affected_pages=urls,
            suggested_action={
                "summary": ("Confirm the training-crawler exclusion is intentional" if role == 'training'
                            else f"Allow {', '.join(agents)} on public pages"),
                "steps": [f"Review the robots.txt group that matches {a}; remove or narrow the Disallow only if the "
                          f"exclusion is unintended" for a in agents][:6],
                "priority": severity, "effort": "low",
                "expected_benefit": ("Policy stays deliberate" if role == 'training'
                                     else "Restores access for these agents; citation is not guaranteed"),
                "verification": "Re-check robots.txt for the listed user-agents against the listed URLs",
            },
            provenance={"skill": "crawl-render-audit", "script": "check_ai_crawler_access.py", "rule_id": rule_id},
        ))

    return skill_result("crawl-render-audit", findings=findings,
                        metrics={"blocked_ai_crawlers": blocked,
                                 "blocked_by_role": {r: sorted(a) for r, a in by_role.items()}})
