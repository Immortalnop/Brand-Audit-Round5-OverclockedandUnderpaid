---
name: freshness-corroboration
description: >-
  Extracts factual claims from a crawled website, ranks the most important ones, resolves one brand identity (Organization JSON-LD, then WebSite name/og:site_name, title segment, footer copyright holder, domain), checks whether dated facts are current and consistent (expired offers, contradictory dates, stale update claims, stale copyright, undated articles) and whether claims are corroborated -- calibrated so insufficient external evidence is never reported as a confirmed defect. Called by audit-orchestrator; not intended to be invoked standalone.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Freshness & Corroboration

## When to use
Called by audit-orchestrator. `extract_claims`, `resolve_entity_identity`, and
`build_site_graph`-adjacent data steps run in the independent batch;
`identify_important_facts` runs once, sequentially, between the two batches;
`assess_freshness`, `corroborate_claims`, and `assess_external_footprint` run in
the dependent batch.

## Dependencies
`extract_claims`, `identify_important_facts`, `resolve_entity_identity`, and
`assess_freshness` are pure-Python, no network. Dates are parsed and classified by
their surrounding words in `common/dates.py`; first-party naming signals live in
`common/identity_signals.py`. `corroborate_claims` and
`assess_external_footprint` call the pluggable `common/search_provider.py`
(optional capability, standard-library) -- gated on `SEARCH_API_URL` being set;
unset or failing degrades to `insufficient_evidence`, never a confirmed
absence.

## Inputs
`AuditArtifacts`, the `claims` intermediate artifact, and the shared
`entity_identity` artifact (resolved once, reused by every consumer).

## Procedure
See `references/freshness-corroboration-methodology.md` for the entity
resolution hierarchy and footprint calibration table.

## Output
`SkillResult`s per analysis script, plus the `claims`, `important_facts`, and
`entity_identity` intermediate artifacts consumed by other steps.

## Example

A pricing page that says "valid through 2020-06-15" while still being served:

```json
{"skill": "freshness-corroboration", "status": "success",
 "findings": [{"category": "freshness", "severity": "high", "status": "confirmed",
               "check_id": "expired-offer",
               "title": "Expired offers or validity dates are still published"}],
 "metrics": {"date_signals_found": 4, "expired_items": 1}}
```


## Answer-content analysis

The entrypoint invokes `analyze_answer_content.py` after entity resolution using
the same immutable snapshot. It returns a SkillResult without any additional
fetches. Declared-English, complete-text pages support lexical title alignment,
repetition, optional question sections and conditional brand-definition review.
Observed software schema supports app-identity review; app-store rankings and
external listing content are never inferred. Rule guidance comes from the central
common/check_catalog.py catalog.
