---
name: crawl-render-audit
description: >-
  Off-site AI discoverability mechanics for an acquired site snapshot: can a crawler get in (robots.txt per RFC 9309, role-weighted AI/search crawler access, bot-protection walls, indexing directives, HTTPS), can it read the content (JS-only rendering via empty-shell and hydration-payload signals, facts locked in PDFs/images/iframes), and can it extract facts (JSON-LD presence per page type, required properties, malformed values, markup that contradicts the page, metadata, llms.txt). Called by audit-orchestrator; not intended to be invoked standalone.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Crawl & Render Audit

## When to use
Called by audit-orchestrator in its independent batch. Not a standalone entrypoint.

## Dependencies
Pure-Python analysis over the `AuditArtifacts` snapshot; no network calls of its
own. `analyze_rendering.py` optionally confirms gaps with Playwright when
`ENABLE_RENDERING=1` (see `common/capabilities.py`).

## Inputs
An `AuditArtifacts` snapshot produced by `acquire_site.py`.

## Procedure
Each script returns one `SkillResult`; see `references/crawl-render-checklist.md`
for every rule, its severity logic and its evidence.
1. `analyze_access.py` -- bot-challenge walls on discovery files, homepage, or after N requests.
2. `check_ai_crawler_access.py` -- 18 search/AI agents vs key URLs, weighted by role.
3. `analyze_crawlability.py` -- robots verdict, broken pages.
4. `analyze_directives.py` -- noindex / nosnippet / max-snippet, incl. AI-agent meta tags.
5. `analyze_rendering.py` -- JS-only content (static signals; browser-confirmed when available).
6. `analyze_nontext_facts.py` -- facts only in PDFs, images or viewer iframes.
7. `analyze_machine_readability.py` -- JSON-LD per page type, with draft snippets.
8. `validate_structured_data.py` -- required properties, malformed values, markup vs page.
9. `analyze_metadata.py`, `analyze_performance.py` -- metadata and HTML-weight observations
   (most are SEO-hygiene tier, reported in the appendix).
10. `check_llms_txt.py` -- llms.txt presence (absence is an opportunity, never a defect).

## Output
One `SkillResult` per script: findings (evidence + detector severity) plus metrics.
Final severity, confidence and priority are set centrally by `common/scoring.py`.

## Example
Input: a snapshot whose robots.txt answers with a Cloudflare challenge.
`analyze_access.py` output:
```json
{"skill": "crawl-render-audit", "status": "success",
 "findings": [{"title": "robots.txt / discovery files are served behind a bot challenge",
               "severity": "high", "status": "confirmed", "check_id": "bot-challenge-robots"}],
 "metrics": {"challenged_probe_files": 1, "vendor": "cloudflare"}}
```
