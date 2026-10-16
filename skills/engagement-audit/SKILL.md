---
name: engagement-audit
description: >-
  Builds a site graph from crawled pages and audits on-site engagement -- orphan pages, dead ends, navigation structure, breadcrumb consistency between visible markup and structured data, accessibility beyond alt text (form labels, control names, inline contrast, target size), blocking overlays and cookie-consent text, and context retention (site search, saved state, query parameters kept through redirects). Called by audit-orchestrator; not intended to be invoked standalone.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Engagement Audit

## When to use
Called by audit-orchestrator as part of the dependent analysis batch, so it
overlaps external-analysis work instead of trailing it.

## Dependencies
Pure-Python graph analysis over already-acquired data -- no network calls,
no optional/fallback capability (unlike rendering or external search).

## Inputs
`AuditArtifacts`, the `site_graph` intermediate artifact, and the rendering
`SkillResult` (`rendering_result`).

## Procedure
`build_site_graph`, `analyze_accessibility`, `analyze_overlays` and
`analyze_context_retention` (site search, saved state, query parameters kept
through redirects) run in the independent batch; `analyze_engagement` runs in the dependent batch. See `references/engagement-checklist.md`.

## Output
A `SkillResult` with engagement findings and metrics.

## Example

On a crawl that reached every discovered URL, a page with no inbound internal
links (an orphan) produces the finding below. On a sampled crawl orphans and
isolated clusters are counted in metrics, not reported, and a warning says so.

```json
{"skill": "engagement-audit", "status": "success",
 "findings": [{"id": "F-003", "category": "engagement", "severity": "medium",
               "status": "confirmed",
               "root_cause": "Pages exist but are not linked from anywhere else on the site"}],
 "metrics": {"orphan_pages": 1, "isolated_clusters": 0}}
```
