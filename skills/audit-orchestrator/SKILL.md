---
name: audit-orchestrator
description: >-
  Entrypoint skill for the Brand AI-Readiness Audit marketplace. Given a website URL, acquires the site once (robots/RFC 9309, bot-wall detection, login pages kept out of scope, template-diverse sampling), runs crawl-render-audit, freshness-corroboration and engagement-audit on that snapshot, hands an agent brief to entity-corroboration-agent for cross-web and vision checks, then merges findings by root cause, scores severity/confidence/priority in one place, attaches ready-to-paste fixes, lists the checks that passed, validates the report and emits findings, an ordered action plan with quick wins and beyond-defect recommendations as JSON plus a readable report.md. Use whenever a website's AI discoverability and on-site engagement need auditing.
license: MIT
allowed-tools: Bash(python3:*) Read Write WebSearch WebFetch
---
# Audit Orchestrator

## When to use
Use when asked to audit a website for AI discoverability and on-site engagement
problems, or to run the brand-ai-readiness-audit marketplace end to end.

## Dependencies
- Python 3.10+ standard library. No runtime pip installation required.
- Optional rendering: `ENABLE_RENDERING=1`, Playwright and Chromium; otherwise
  static render signals (empty app shell, hydration payload vs HTML) are used.
- Optional: `SEARCH_API_URL` (+ `SEARCH_API_KEY`) for scripted corroboration.
- Network: outbound GET only, to the target site (and the optional search API).

## Inputs
- `site_url`: a URL or bare domain.
- Optional `--urls FILE`: audit exactly these same-site pages (e.g. the landing
  pages for prompts a brand is losing) instead of a sampled crawl.
- Optional `--explain`: print how the run spent its budget (timings, requests,
  sampling, skips) on stderr. The same numbers are in `coverage.instrumentation`.

## Procedure
1. **Pass 1 -- deterministic audit.** Run
   `python3 skills/audit-orchestrator/scripts/run_audit.py <site_url> --out-dir audit_out`.
   This writes `audit_out/report.json`, `audit_out/agent_brief.json` and
   `audit_out/report.md` (stdout is the same JSON report).
2. **Agent stage -- cross-web corroboration.** If you have a web-search tool,
   follow `skills/entity-corroboration-agent/SKILL.md` using
   `audit_out/agent_brief.json` (checks AG-01 to AG-06; at most 8 searches, about
   150 s; AG-04 needs image input). Write the
   result to `audit_out/agent_findings.json` -- an empty array `[]` if nothing
   fires. If you have no search tool, write `[]` and skip the searches.
3. **Pass 2 -- finalize.** Run
   `python3 skills/audit-orchestrator/scripts/finalize_report.py --report audit_out/report.json --agent-findings audit_out/agent_findings.json`.
   It merges the agent findings, re-scores, re-orders and re-validates, and
   rewrites `report.json` and `report.md`. No re-crawl.
4. **Report back.** Show the user the confidence line, the "Start here" item,
   the "Top actions" table and the summary from `audit_out/report.md`, then point
   to `report.json` for the full evidence.
   Never edit findings by hand; never claim a check ran if the report says it
   was not supplied.

Scripts, in order (all in `scripts/`): `run_audit.py` (CLI + pipeline),
`acquire_site.py` (single bounded acquisition), `merge_findings.py`
(dedup + root-cause merge), `prioritize_findings.py` (ordering),
`generate_recommendations.py` (action plan, quick wins, beyond-defect items),
`whats_working.py` (checks that ran and passed), `validate_report.py`,
`execution_summary.py` (status, limitations, explained confidence),
`finalize_report.py`, `render_report.py`, `diagnose_transport.py`. Shared scoring
lives in `common/scoring.py`; every check's wording and metadata in
`common/check_catalog.py`; ready-to-paste fixes in `common/fix_snippets.py`.

## Safety guarantees (enforced in code, not just documented)
- **SSRF protection**: every URL fetched -- target, robots.txt, sitemap, llms.txt,
  discovered links, redirects -- is checked by `common/url_safety.py` first.
- **robots.txt per RFC 9309**: 200 is obeyed; 4xx (not 429) means no
  restrictions; 5xx/timeout means disallow-all (no pages fetched); a robots file
  that answers 429 or sits behind a bot challenge means permission unknown --
  only the homepage is fetched, once, to identify the cause.
- **Login pages out of scope**: a page with a visible password field, little
  text, no entity markup and a login path or heading is never analysed as
  content; it is listed in `coverage.out_of_scope_pages`.
- **Courtesy**: crawl-delay honoured; a template that starts returning
  challenges is not sampled further; 3 consecutive challenges stop the crawl.
- **Read-only**: only GET requests; optional rendering runs under a GET-only,
  same-origin policy; the audit never clicks, types or submits forms.
- **Bounded**: 50 pages, 90 requests, 40 MiB, 270 s wall clock; byte budgets
  enforced while streaming. The 90 requests are ONE allowance covering robots,
  sitemap and llms.txt probes, page fetches, redirect hops, retries, the
  auxiliary HTTPS and PDF diagnostics, and optional headless rendering -- which
  reserves from what is left rather than getting a budget of its own.
  `coverage.request_accounting` reports the split, and a diagnostic is skipped
  rather than run off-budget.
- **Which stages make requests**: acquisition always; optional headless
  rendering when a browser is available (same GET-only, same-origin,
  robots-checked policy, through a child-process Transport); optional claim
  corroboration and off-site footprint when a search provider is configured,
  and those go to the provider, not to the audited site. Every other analysis
  script is pure over the acquisition snapshot.

## Output
`report.json` (schema: `references/report-schema.md`): `site`, `audited_at`,
`summary` (counts by severity), `findings` (each with evidence, severity,
`severity_rationale`, `suggested_action` incl. priority, effort, owner role and,
for markup fixes, a ready-to-paste `snippet` or `proposed_snippets`),
`action_plan` (with `quick_win` and `start_here`), `top_actions`, `quick_wins`,
`recommendations` (beyond-defect items only), `hygiene_findings` (SEO hygiene
appendix), `whats_working` (passed checks with evidence), `coverage`,
`agent_stage`, `execution_status`, `limitations`, `confidence` (score, level,
limiting factor, reasons and a plain-English explanation).
`report.md` renders the same content for a non-expert reader.
Recommend-only -- no skill ever modifies a live site.

## Example
```
$ python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --out-dir audit_out
```
Excerpt:
```json
{"site": "https://example.com/", "summary": {"total_findings": 7, "critical": 0, "high": 2, "medium": 3, "low": 2},
 "findings": [{"id": "F-001", "title": "Automated clients receive a bot challenge instead of the site content",
   "severity": "high", "status": "suspected",
   "severity_rationale": {"gate": "access", "scope": "site-wide"},
   "suggested_action": {"summary": "Allow verified search and AI crawlers through the bot-management layer",
                        "priority": "high", "effort": "low", "owner_role": "infra"}}],
 "action_plan": [{"rank": 1, "finding_ids": ["F-001"], "severity": "high"}]}
```
