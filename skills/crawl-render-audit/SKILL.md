---
name: crawl-render-audit
description: >-
  Analyzes off-site AI discoverability mechanics for a crawled website -- reachability, robots.txt (with fetch-status calibration: ok/absent/timeout/ inaccessible/malformed/blocked, never inferring a disallow from a failed fetch) and AI-crawler-specific access, raw-vs-rendered content gaps, machine-readable structured data (JSON-LD), sitemap.xml discovery, llms.txt presence, and facts locked in non-text media (SVG image text, raster images named as price lists or menus, and linked PDFs). Called by audit-orchestrator as part of its independent analysis batch; not intended to be invoked standalone.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Crawl & Render Audit

## When to use
Called by audit-orchestrator. Not a standalone entrypoint.

## Dependencies
Pure-Python analysis over an already-acquired `AuditArtifacts` snapshot --
no network calls of its own. `analyze_rendering.py` additionally checks for
`playwright` (optional; degrades to a heuristic, `suspected` gap-detection
when absent, per `common/capabilities.py`).

## Inputs
An `AuditArtifacts` snapshot produced by `acquire_site.py`.

## Procedure
Run `analyze_crawlability`, `analyze_rendering`, `analyze_machine_readability`,
`check_ai_crawler_access`, `check_llms_txt`, and `analyze_non_text` -- see
`references/crawl-render-checklist.md`.

## Output
One `SkillResult` per script: findings (evidence + severity) plus metrics.

## Example

Input: an `AuditArtifacts` with one page that has no JSON-LD.
`analyze_machine_readability` output:

```json
{"skill": "crawl-render-audit", "status": "success",
 "findings": [{"id": "F-002", "category": "ai_discoverability",
               "severity": "high", "status": "confirmed",
               "root_cause": "Home page has no Organization/WebSite JSON-LD"}],
 "metrics": {"pages_missing_jsonld": 1}}
```


## Additional snapshot analysis

The entrypoint invokes `analyze_metadata.py` and `analyze_performance.py` as
in-process functions consuming the shared AuditArtifacts snapshot and returning
SkillResult objects. They make no network requests. Metadata covers titles,
descriptions, canonical hints, language, landmarks, heading hierarchy and social
previews. Performance covers observed document bytes, synchronous head scripts,
image dimension hints and retrieval timing, never fabricated Core Web Vitals.
Use common/check_catalog.py for rule mechanisms and implementation guidance.

## Non-text media

`analyze_non_text.py` reads the image and PDF observations that acquisition
collected (`common/non_text.py` for SVG text and image headers,
`common/pdf_text.py` for standard-library PDF text extraction). It compares the
facts found in media with the facts stated in readable text and reports
`facts-in-images`, `pdf-only-facts` and `pdf-image-only`. It makes no network
requests of its own.
