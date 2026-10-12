---
name: engagement-audit
description: >-
  Builds a site graph from the crawled content pages and audits on-site engagement for visitors who arrive (often deep, from an AI answer) -- orphan pages, isolated clusters, dead ends, missing next steps, missing or generic headings, generic anchors, breadcrumb/markup consistency, mobile viewport/zoom, overlays, and newsletter signups (only real newsletter or mailing-list forms, never contact, trial or login forms) whose outbound email should stay readable to inbox AI summaries. Called by audit-orchestrator; not intended to be invoked standalone.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Engagement Audit

## When to use
Called by audit-orchestrator as part of the dependent analysis batch, so it
overlaps external-analysis work instead of trailing it.

## Dependencies
Pure-Python graph analysis over already-acquired data -- no network calls.
Only real content pages are graph nodes (bot-challenge interstitials are
excluded), and URLs are matched by `common/url_keys.visit_key`, so `/a` and `/a/`
are one node.

## Inputs
`AuditArtifacts`, the `site_graph` intermediate artifact, and the rendering
`SkillResult` (`rendering_result`).

## Procedure
`build_site_graph` runs in the independent batch; `analyze_engagement` runs in
the dependent batch. See `references/engagement-checklist.md`.

## Output
A `SkillResult` with engagement findings and metrics.

## Example

A page with no inbound internal links (an orphan) produces:

```json
{"skill": "engagement-audit", "status": "success",
 "findings": [{"id": "F-003", "category": "engagement", "severity": "medium",
               "status": "confirmed",
               "root_cause": "Pages exist but are not linked from anywhere else on the site"}],
 "metrics": {"orphan_pages": 1, "isolated_clusters": 0}}
```
