---
name: freshness-corroboration
description: >-
  Extracts factual claims from a crawled website, ranks the most important ones, resolves a single disambiguated brand identity, and assesses whether those facts are fresh and corroborated by independent sources -- calibrated so that insufficient external evidence is never reported as a confirmed defect. Called by audit-orchestrator; not intended to be invoked standalone.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Freshness & Corroboration

## When to use
Called by audit-orchestrator. `extract_claims`, `resolve_entity_identity`, and
`build_site_graph`-adjacent data steps run in the independent batch;
`identify_important_facts` runs once, sequentially, between the two batches;
`assess_freshness`, `corroborate_claims`, `assess_external_footprint`, and
`check_knowledge_graph` run in the dependent batch.

## Dependencies
`extract_claims`, `identify_important_facts`, `resolve_entity_identity`, and
`assess_freshness` (with `update_signals`) are pure-Python, no network.
`check_knowledge_graph` checks Organization `sameAs` for a Wikidata or Wikipedia
link without network access; it verifies a declared link with at most a few
robots-checked GETs to the public `/wiki/` paths of wikidata.org and
wikipedia.org (15-second budget, off with `KNOWLEDGE_GRAPH_LOOKUP=0`). A failed
lookup is a warning, never a finding. `corroborate_claims` and
`assess_external_footprint` call the pluggable `common/search_provider.py`
(optional capability, standard-library) -- gated on `SEARCH_API_URL` being set;
unset or failing degrades to `insufficient_evidence`, never a confirmed
absence.

## Inputs
`AuditArtifacts` (including JSON-LD `datePublished`/`dateModified`, read by
`extract_claims.structured_date_claims`; sitemap `<lastmod>` and the HTTP
`Last-Modified` header, read by `update_signals.page_update_claims`), the
`claims` intermediate artifact, and the shared
`entity_identity` artifact (resolved once, reused by every consumer).

## Procedure
See `references/freshness-corroboration-methodology.md` for the entity
resolution hierarchy and footprint calibration table.

## Output
`SkillResult`s per analysis script, plus the `claims`, `important_facts`, and
`entity_identity` intermediate artifacts consumed by other steps.

## Example

A `/product` page with a 2019 date and no offsetting recent update:

```json
{"skill": "freshness-corroboration", "status": "success",
 "findings": [{"id": "F-004", "category": "freshness", "severity": "high",
               "status": "suspected",
               "root_cause": "Dated content classified as 'commercial' appears outdated"}],
 "metrics": {"date_facts_found": 3, "stale_facts": 3}}
```


## Answer-content analysis

The entrypoint invokes `analyze_answer_content.py` after entity resolution using
the same immutable snapshot. It returns a SkillResult without any additional
fetches. Declared-English, complete-text pages support lexical title alignment,
repetition, optional question sections and conditional brand-definition review.
Observed software schema supports app-identity review; app-store rankings and
external listing content are never inferred. Rule guidance comes from the central
common/check_catalog.py catalog.
