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
`analyze_authorship`, `check_offer_expiry` and `check_fact_consistency` also
run in the independent batch;
`assess_freshness`, `corroborate_claims`, `assess_external_footprint`,
`check_knowledge_graph` and `check_off_site_profiles` run in the dependent batch.

## Dependencies
`extract_claims`, `identify_important_facts`, `resolve_entity_identity`, and
`assess_freshness` (with `update_signals`) are pure-Python, no network.
`check_knowledge_graph` checks Organization `sameAs` for a Wikidata or Wikipedia
link without network access; it verifies a declared link with at most a few
robots-checked GETs to the public `/wiki/` paths of wikidata.org and
wikipedia.org (15-second budget, off with `KNOWLEDGE_GRAPH_LOOKUP=0`). A failed
lookup is a warning, never a finding. `check_off_site_profiles` reports
invalid sameAs values without network access, then fetches each remaining
sameAs or linked review profile (at most 8, 2 per host, 18-second budget, each
host's robots.txt read first and failing closed; off with `OFF_SITE_LOOKUP=0`).
Profiles that robots.txt forbids, or that answer with a bot challenge or login
wall, are reported as unverified, never as broken. `analyze_authorship` is
pure-Python, no network. `corroborate_claims` and
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

## Off-site profiles and review platforms

`check_off_site_profiles.py` reports `profile-link-broken` (a sameAs value that
is a share link, a platform home page, the site itself or not an absolute URL,
or a profile that answers 404 or 410, confirmed; a "not found" page or a
redirect to the platform home page, suspected), `profile-identity-mismatch`
(a profile page about its handle that names neither the brand nor the site,
suspected) and `review-platform-missing` (no review or directory profile, such
as Trustpilot, G2, Capterra, Google Business Profile or Yelp, is linked from the
site or sameAs; with a search provider, one "<brand> reviews" query adds
platforms found by search; not applied to government, education or non-profit
bodies). Review sites block automated clients, so searching them by name is the
agent stage's job (AG-06).

## Authorship (E-E-A-T)

`analyze_authorship.py` checks article pages (Article-type markup, or a blog or
news path with a slug and a substantial body). `author-missing`: no byline, meta
author, rel=author link or Article author. `author-credentials-weak`: the author
is a plain string or an Organization rather than a Person, the Person has no
profile link or credentials (jobTitle, description, knowsAbout, alumniOf, award,
hasCredential), the markup author is not shown on the page, or a visible byline
has no markup.

## Expired offers and fact consistency

`check_offer_expiry.py` reports `expired-offer` (confirmed, medium) when visible
text pairs an offer word (offer, sale, deal, discount, coupon...) with a
present-tense deadline ("ends", "expires", "valid until", "available through")
and a full date more than a day before the audit, or when an Offer's
`priceValidUntil` or `validThrough` has passed. Past tense ("ended"), dates
without a year and numeric dates whose two readings disagree are never read as
expired; editorial, listing, legal, archive and event pages are skipped.

`check_fact_consistency.py` reports `fact-markup-mismatch` (suspected, medium)
when JSON-LD states a telephone or postal code that no sampled page shows while
the pages carrying it show another one, opening hours none of whose times appear
in the hours the site shows, or a single Offer price a product page never shows
while it shows other prices in that currency. Only pages whose whole text was
read and that do not build their text with JavaScript are compared. It reports
`fact-inconsistent-across-pages` (confirmed, medium) when one entity (same
absolute @id, same name for a non-local organization, same GTIN for a product;
a SKU or MPN often names a product family whose variants differ in price) has two values for telephone, email, foundingDate, postal code or
price in one currency on two pages in the same language. A property one page
states with several values (variants, several telephones) is not compared. Both
scripts make no request.
