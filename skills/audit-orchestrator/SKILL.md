---
name: audit-orchestrator
description: >-
  Entrypoint skill for the Brand AI-Readiness Audit marketplace. Given a website URL, acquires the site once, schedules crawl-render-audit, freshness-corroboration, and engagement-audit under one shared deadline, merges and deduplicates their findings, prioritizes them, validates the report against the required schema and Invariant I-1, and emits a single structured audit report (findings + suggested actions). Use this skill whenever a general audit of a website's AI discoverability and on-site engagement is requested.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Audit Orchestrator

## When to use
Use when asked to audit a website for AI discoverability and on-site engagement
problems, or to run the brand-ai-readiness-audit marketplace end to end.

## Dependencies
- Python 3.10+ standard library. No runtime pip installation required.
- Optional rendering: `ENABLE_RENDERING=1`, Playwright and Chromium; otherwise
  use evidence-limited static heuristics.
- Env: `SEARCH_API_URL` (optional, plus `SEARCH_API_KEY`) enables external
  corroboration/footprint search in `freshness-corroboration`; without it those
  checks report `insufficient_evidence`, never a confirmed absence.
- Network: outbound GET only, to the target site and (if configured) the
  external search endpoint. No target credentials or mutating requests; provider credentials remain optional.

## Inputs
- `site_url`: a URL or bare domain.

## Procedure
1. Call `scripts/run_audit.py: run_audit(site_url)`.
2. It validates the URL, acquires the site once (`acquire_site.py`), runs the
   independent analysis batch (crawl-render-audit checks plus the data-producing
   steps of freshness-corroboration and engagement-audit), runs the mandatory
   sequential `identify_important_facts` step, then runs the dependent batch
   (freshness, corroboration, footprint, knowledge graph, engagement).
3. Findings are merged (`merge_findings.py`), prioritized
   (`prioritize_findings.py`), and validated (`validate_report.py`).
4. Return the resulting report to the user as-is.

## Safety guarantees (enforced by `acquire_site.py`, not just documented)
- **SSRF protection**: every URL fetched -- the initial target, robots.txt,
  sitemap.xml, llms.txt, discovered links, and every redirect hop -- is checked
  by `common/url_safety.py` first. Disallowed schemes, credentials-in-URL, cloud
  metadata hosts/IPs, and (by default) loopback/private/link-local/reserved
  addresses are all rejected before any request is issued. Blocked URLs are
  recorded as safety skips, never as findings.
- **Robots.txt never fails open**: absence (a confirmed 404) is the only state
  that means "allowed". Timeout, other HTTP errors, or an undecodable body make
  the crawl conservative (no pages fetched until permission is known) and
  are surfaced as `insufficient_evidence`, never inferred as a confirmed block.
- **Read-only**: only GET requests are ever issued against the target site;
  optional rendering executes site JavaScript under a GET-only, same-origin
  network policy; the audit does not click, type or submit forms.
- **Byte budgets are enforced during download** (streaming), not after a full
  response has already been pulled into memory.
- **Non-text media is bounded**: after the page crawl, at most 6 images and 3
  linked PDFs are fetched, same origin only, robots-checked before selection, from
  the request, byte and time budget the crawl left. Raster images are read only up
  to their header (a Range request capped at 64 KiB); PDF parsing is capped at 4
  seconds per file.
- **Knowledge-graph verification is bounded and optional**: the only requests
  to hosts other than the target verify a Wikidata item or Wikipedia article the
  site itself declares in Organization sameAs. At most 4 GETs to public `/wiki/`
  pages, each host's robots.txt read first (fail closed), within 15 seconds;
  `KNOWLEDGE_GRAPH_LOOKUP=0` turns it off. A failed lookup is a limitation, never
  a finding. Sitemap `<lastmod>` and `Last-Modified` dates come from responses
  already fetched, so they cost no requests.

## Output
A JSON report matching `references/report-schema.md`: `site`, `audited_at`,
`summary`, `coverage`, `findings`, `recommendations`, `execution_status`
(completed / completed_with_timeouts / degraded / partial_deadline_reached),
`limitations` (plain-English, each tied to a real signal from the run -- never
unconditional boilerplate), and `confidence` (the minimum of crawl
completeness, identity confidence, and an execution penalty, with its method
shown). Recommend-only -- no skill ever modifies a live site.

Headless rendering runs in an isolated child process
(`common/subprocess_isolation.py`) with a hard wall-clock kill, not just
Playwright's own cooperative per-navigation timeout -- a genuinely hung browser
process cannot block the orchestrator past its deadline.

## Example

```
$ python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com
```

Illustrative excerpt (not a complete report):

```json
{
  "site": "https://example.com/",
  "audited_at": "2026-09-13T00:00:00Z",
  "summary": {"total_findings": 3, "critical": 0, "high": 1, "medium": 1, "low": 1},
  "findings": [
    {"id": "F-001", "category": "ai_discoverability", "severity": "high",
     "status": "confirmed", "root_cause": "No Product/Offer JSON-LD on product pages"}
  ],
  "recommendations": [
    {"id": "R-001", "category": "engagement", "finding_type": "proactive_improvement"}
  ],
  "execution_status": "completed",
  "confidence": {"score": 0.82, "method": "weakest_link"}
}
```
