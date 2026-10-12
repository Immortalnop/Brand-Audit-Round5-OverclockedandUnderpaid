---
name: entity-corroboration-agent
description: >-
  Agent-executed qualitative stage. Judges whether the brand About-page self-description is concrete enough for an assistant to quote (AG-01), and whether independent sources across the wider web corroborate (AG-02) or contradict (AG-03) what the site claims about itself. Unlike every other skill in this marketplace it runs no deterministic script: the calling agent performs it with its own reading and web_search tools, then hands structured findings back to the entrypoint, which ingests them in-process. Use when diagnosing entity confusion, hallucinated brand attributes, or a lack of multi-source consensus. It also reads facts drawn inside raster images with the agent's own vision (AG-04), the one part of the facts-in-images check a script cannot do, searches knowledge graphs for entities that share the brand name (AG-05), which robots.txt stops a script from doing, and searches review and directory platforms for the brand's profiles (AG-06), which those platforms block scripts from doing.
license: MIT
allowed-tools: Read WebSearch WebFetch
---

# Entity Corroboration (agent stage)

## When to use

Two things the handout asks for cannot be settled by a deterministic script:
whether a self-description is concrete enough to quote, and whether the wider web
agrees with it. Both are judgment calls over natural language. This skill is where
the calling agent contributes that judgment, in the same finding shape as every
script, so the entrypoint composes it like any other source.

Skip it entirely if no reading or search capability is available. A skipped stage
is recorded as not_supplied and costs nothing; an invented stage would cost
accuracy.

## Execution model

This marketplace runs one orchestration model: the entrypoint acquires a single
immutable site snapshot and every specialist is an in-process function that
returns a SkillResult. This stage fits that model. It is not a subprocess and does
not use a workdir handoff. The calling agent writes its observations to a small
JSON file and hands it to run_audit.py with --agent-findings (merged into a saved
report with --from-report, or read during an audit like AGENT_FINDINGS_PATH), and
run_audit.py ingests it in-process through ingest_agent_findings.py, which
reconstructs each entry with the shared finding factory. That means catalog
enrichment and Invariant I-1 cap agent findings exactly as they cap script
findings; the agent supplies only what it observed.

## Inputs

- The audited site URL and the already-acquired site snapshot. Do not re-crawl the
  site: the page text, titles and JSON-LD are already available to the audit. The
  only site requests this stage may make are AG-04 image views (at most 8 GETs,
  only for images on paths robots.txt allows). AG-05 uses web search plus at
  most 4 GETs to public `/wiki/` pages of wikidata.org or wikipedia.org (never
  `/w/api.php`, `/w/rest.php`, `/api/` or `Special:Search`, which their
  robots.txt disallows). AG-06 uses web search only. Read
  the brand name from the resolved identity (Organization JSON-LD name, og:site_name
  or title).

## Procedure

Step 1, About-page concreteness (AG-01). Read the About page text (or the homepage
if there is no About page). Check whether the opening answers all three of: who the
organization is, what it specifically sells or does, and in what category or
market. Fire AG-01 only if at least one of the three is genuinely unanswerable from
that text. Marketing register is not itself a defect: enthusiastic phrasing that
still names a product and a market passes. If all three are answerable, record
nothing; a passing check is not a finding.

Step 2, cross-web corroboration (AG-02 / AG-03). If a web_search tool is available,
search for the brand name plus its category, and separately restrict to public
community platforms, for example:

```
"<brand name>" <category>
"<brand name>" site:reddit.com OR site:quora.com
```

The handout explicitly allows querying public community platforms such as Reddit
and Quora for brand visibility. Then classify into exactly one of three outcomes:

| Outcome | Finding | Severity | Status |
| --- | --- | --- | --- |
| Independent sources exist and agree with the site | none, record in notes | -- | -- |
| No independent mention found at all | AG-02 | low | confirmed |
| An independent source contradicts the site (different category, ownership, location, or a same-named different entity dominating results) | AG-03 | high | confirmed |

Step 2b, text inside images (AG-04). Only if you can view images. Take the image
URLs listed in the evidence of a facts-in-images finding from an earlier report of
this audit; without one, use the large images on the home, pricing, product,
menu and contact pages. View at most 8 images. Fire AG-04 for an image only when
it shows a concrete fact (a price, opening hours, a phone number, a specification)
that the page text does not state. A decorative photo, a logo, or an image whose
facts are repeated in the page text records nothing. List the page URLs in
affected_pages so the finding merges with the script finding for those pages.

Step 2c, same-named entities (AG-05). Only if a web_search tool is available.
The scripts verify a Wikidata or Wikipedia entity the site already declares in
Organization sameAs (kg-link-missing, kg-entity-mismatch), but they cannot look
a name up, because robots.txt for both hosts disallows their search endpoints.
Search for the brand name restricted to the knowledge graphs, for example:

```
"<brand name>" site:wikidata.org
"<brand name>" site:wikipedia.org
```

Open at most 4 of the results by their `/wiki/` URL. Fire AG-05 only when at
least one entity with the same or a near-identical name is a different
organization, person, place or product (its description, official website or
country differs from the site's), and the site does not already declare its own
entity in sameAs. List the namesakes with their Wikidata IDs in evidence. If
every match is the brand itself, or nothing matches, record nothing: having no
Wikidata entry is not a defect for a small organization.

Step 2d, review and directory platforms (AG-06). Only if a web_search tool is
available, and only when the report has a review-platform-missing finding or
coverage.off_site_profiles.review_platforms_linked is empty. The scripts see only
the review profiles the site links: Trustpilot, G2, Capterra, Yelp and similar
sites answer automated clients with a challenge page or forbid them in
robots.txt, and Google Business Profile has no stable public page. Search the
platforms that fit the business (coverage.off_site_profiles.business_kind:
local, software or general), for example:

```
"<brand name>" site:trustpilot.com OR site:g2.com OR site:capterra.com
"<brand name>" reviews
"<brand name>" site:reddit.com OR site:quora.com
```

Fire AG-06 only when the searches ran and found no profile of the brand on any
platform that fits its business; list the platforms searched in evidence. When a
profile exists but the site does not link it, fire AG-06 with status suspected
and name the profile URLs in evidence, so the site can link them and add them to
sameAs. A platform that does not fit the business (Yelp for a software company)
records nothing.

Step 3, graceful fallback. If no search tool exists, it errors, or it is
rate-limited: do not abort, and do not report absence of corroboration. Supply
nothing (or a single entry with status insufficient_evidence). The distinction
matters: "nobody discusses this brand" is a finding about the brand; "I could not
check" is a finding about the audit. Collapsing the second into the first is the
single most common way an audit manufactures a false negative.

Step 4, handoff. Write a JSON array of finding objects to a file (agent.json
below). Do not edit the report yourself; the entrypoint ingests that file,
reconstructs each finding through the shared factory, re-applies Invariant I-1,
folds it into the script finding that reports the same check, and prioritizes
everything together. Two ways in:

```
python3 skills/audit-orchestrator/scripts/run_audit.py --from-report report.json --agent-findings agent.json --out report.json
python3 skills/audit-orchestrator/scripts/run_audit.py <site> --agent-findings agent.json --out report.json
```

The first merges into the report the audit already wrote, with no request and no
new crawl; use it after reading that report. The second runs the audit with the
file (the same as setting AGENT_FINDINGS_PATH). affected_pages keeps only pages
of the audited site; put third-party URLs (a review profile, a namesake's
Wikidata item) in an evidence entry's urls. At most 50 entries are read.

## Output

The file passed with --agent-findings (or named by AGENT_FINDINGS_PATH): a JSON
array of findings (or an object with a findings array), UTF-8 or UTF-16. Useful
keys per finding: check (AG-01 to AG-06), title, severity, status, evidence (a
string, or a list of objects with description and urls), affected_pages, and
suggested_action with summary and steps. mechanism,
implementation_detail and expected_outcome are filled automatically from
common/check_catalog.py, so supply only what you observed.

```json
[
  {
    "check": "AG-03",
    "title": "Independent sources describe the brand differently from the site",
    "severity": "high",
    "status": "confirmed",
    "evidence": "Site describes itself as a payroll platform; two community threads and one directory describe it as an accounting firm. A same-named consultancy dominates the first page of results.",
    "suggested_action": {
      "summary": "Reconcile the category description on-site and in Organization markup, and correct the third-party listings that state the wrong category.",
      "steps": ["Identify the contradicted fact and its source", "Correct the wrong source", "State the accurate version on-site and in markup"]
    }
  }
]
```

If nothing fires, supply an empty array (the stage is then recorded as ingested
with no finding), or supply no file at all (recorded as not_supplied).

## Guarantees

Read-only. Does not crawl the audited site (it reads the already-acquired
snapshot); AG-04 views at most 8 images by plain GET; AG-05 opens at most 4
robots-allowed knowledge-graph pages by plain GET; AG-06 uses web search only. Never reports an unavailable capability as a site defect: the absence of
the stage is recorded as insufficient_evidence, capped low and advisory by
Invariant I-1.
