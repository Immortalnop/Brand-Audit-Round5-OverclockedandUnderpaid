---
name: entity-corroboration-agent
description: >-
  Agent-executed qualitative stage. Judges whether the brand About-page self-description is concrete enough for an assistant to quote (AG-01), whether independent sources corroborate (AG-02) or contradict (AG-03) the site, reads facts locked inside images with the agent's own vision (AG-04), checks for same-named entities and a missing knowledge-graph link (AG-05) and for missing review or directory profiles (AG-06). The calling agent performs it with its own reading, vision and web_search tools, using the agent_brief.json written by the entrypoint, and hands structured findings back for finalize_report.py to merge. Use when diagnosing entity confusion, hallucinated brand attributes, facts hidden in images, or a lack of multi-source consensus.
license: MIT
allowed-tools: Read Write WebSearch WebFetch
---

# Entity Corroboration (agent stage)

## When to use

Some things the handout asks for cannot be settled by a deterministic script:
whether a self-description is concrete enough to quote, whether the wider web
agrees with it, what an image of a price list says, and whether same-named
entities exist (Wikidata, Wikipedia and review platforms refuse scripted search).
These are judgment calls over language and pixels, or lookups a robots-respecting
script cannot make. This skill is where the calling agent contributes them, in
the same finding shape as every script, so the entrypoint composes it like any
other source.

Skip it entirely if no reading or search capability is available. A skipped stage
is recorded as not_supplied and costs nothing; an invented stage would cost
accuracy.

## Execution model

Two passes, no re-crawl. Pass 1 (`run_audit.py --out-dir audit_out`) writes
`audit_out/agent_brief.json`, taken from the site snapshot: brand name, aliases
and where the name came from, category hints, the About-page URL and its first
1,200 characters, key claims, sameAs links, and ready-made search queries. The
agent reads that brief, runs its searches, and writes
`audit_out/agent_findings.json`. Pass 2 (`finalize_report.py`) rebuilds each entry
through the shared finding factory, so catalog wording and Invariant I-1 apply
exactly as for script findings, then merges, re-scores and re-validates the
report. The agent supplies only what it observed.

## Inputs

- `audit_out/agent_brief.json`. Use `brand_name`, `category_hint`,
  `suggested_queries` and the `ag01`, `ag04`, `ag05` and `ag06` blocks; do not
  fetch the audited site's pages again (the images listed in `ag04.images` are
  the one exception: open them to read them).
  Everything AG-01 needs is in `ag01`:
  - `opening_passage`: the page's own opening (H1, meta description, first body
    paragraphs) with navigation boilerplate removed -- this is the text to judge;
  - `about_source` and `assessable`: which page the passage came from and whether
    AG-01 may be judged on it (see Step 1);
  - `passage_url`, `about_link_seen`, and `raw_visible_excerpt` (the unfiltered
    first 1,200 characters, for context only).

## Procedure

Step 1, About-page concreteness (AG-01). Read `ag01.about_source` first:

| about_source | What to do |
| --- | --- |
| `about_page` | Judge `ag01.opening_passage`. |
| `about_section` | The About link points to a section of an acquired page (for example /help/#about); `ag01.opening_passage` is that section. Judge it. |
| `homepage_no_about_page` | The site links to no About page, so the homepage opening is the prescribed passage: judge `ag01.opening_passage`. |
| `about_section_not_captured` | The About section's page was acquired but its text could not be isolated. Treat exactly like the next row: one insufficient_evidence entry, no judgement. |
| `homepage_about_not_acquired` | An About page exists (`about_link_seen`) but could not be acquired. Do not judge the homepage in its place and do not fetch the page. Supply one AG-01 entry with status insufficient_evidence and evidence naming the URL. |
| `none` | Nothing was acquired; supply no AG-01 entry. |

When the passage is assessable, check whether it answers all three of: who the
organization is, what it specifically sells or does, and in what category or
market. Fire AG-01 only if at least one of the three is genuinely unanswerable from
that passage, and quote the passage's first sentence in the evidence. Marketing
register is not itself a defect: enthusiastic phrasing that still names a product
and a market passes. If all three are answerable, record nothing; a passing check
is not a finding.

Step 2, cross-web corroboration (AG-02 / AG-03). If a web_search tool is available,
run the brief's `suggested_queries` (at most 4 searches, about 90 seconds): the
brand name plus its category, and separately restricted to public community
platforms, for example:

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

Step 3, images, namesakes and platforms (AG-04 to AG-06); see
`references/checks.md` for when each fires.

- AG-04: if you can read images, open each URL in `ag04.images` and fire only
  when it shows concrete facts (prices, hours, items, specifications) that the
  page text does not state. Put the page URL in `affected_pages`.
- AG-05: run `ag05.queries`. Fire when same-named organizations appear and
  `ag05.declared_wikidata` is empty or names a different entity.
- AG-06: run `ag06.queries`. Fire only when the searches ran and found no
  profile on the listed platforms. `business_kind: public` never fires.

Step 4, graceful fallback, and why a bare `[]` is not enough. If no search tool
exists, it errors, or it is rate-limited: do not abort, and do not report absence
of corroboration. The distinction matters: "nobody discusses this brand" is a
finding about the brand; "I could not check" is a finding about the audit.
Collapsing the second into the first is the single most common way an audit
manufactures a false positive.

A bare empty array cannot express that distinction -- it reads the same whether
every check passed or no tool was available -- so write the object form and say
per check what happened:

```json
{
  "site": "https://example.com/",
  "search": {"available": false, "queries_run": 0, "reason": "no web_search tool in this environment"},
  "checks": {"AG-01": "pass", "AG-02": "not_assessed", "AG-03": "not_assessed",
             "AG-04": "not_assessed", "AG-05": "not_assessed", "AG-06": "not_assessed"},
  "findings": []
}
```

`checks` takes `pass` (the check ran and the site is fine), `fail` (it fired --
supply the finding too) or `not_assessed` (it could not be run). A check left out
of the map is recorded as unreported, which the report lists under limitations as
not assessed -- never as passed. When a search did run, say so in `search`
(`{"available": true, "queries_run": 4}`): AG-02 and AG-06 are absence claims and
are capped at suspected unless the handoff records that someone actually looked.

Step 5, handoff. Write a JSON array of finding objects to
`audit_out/agent_findings.json` and run `finalize_report.py` as the orchestrator
procedure says. Do not edit report.json yourself; finalize rebuilds each finding
through the shared factory, re-applies Invariant I-1, merges it with script
findings by root cause, and prioritizes everything together.

## Output

`audit_out/agent_findings.json` (or any path passed to `finalize_report.py
--agent-findings`; the `AGENT_FINDINGS_PATH` environment variable is also
honoured): an object with `findings`, `checks`, `search` and `site` as in Step 4
(a bare JSON array of findings is still accepted, but it cannot record per-check
outcomes). Useful keys per finding: check (AG-01 to AG-06), title, severity,
status, evidence, affected_pages (optional, page URLs the finding is about), and
suggested_action with summary and steps. mechanism, implementation_detail and
expected_outcome are filled automatically from common/check_catalog.py, so supply
only what you observed.

What each check must be given, or it is not published (ingest_agent_findings.py
`_AG_RULES[...]["requires"]`):

| Check | Needs | Severity ceiling |
| --- | --- | --- |
| AG-01 | the observation, plus the passage page URL in `affected_pages` or an evidence `urls` entry | medium |
| AG-02 | the observation, plus `search.queries_run` > 0 | low |
| AG-03 | the observation, plus at least one independent (off-site) source URL | high |
| AG-04 | the observation, plus the page URL the image sits on | medium |
| AG-05 | the observation, plus at least one off-site URL showing the namesake | medium |
| AG-06 | the observation, plus `search.queries_run` > 0 | low |

The observation is your own sentence about what you read or saw (at least 25
characters); an entry with no observation behind it is rejected and counted in
`agent_stage.findings_rejected`, not published. A missing source URL or search
record does not void the finding: it caps it at `suspected` and the gap is
printed in its evidence. A severity above the ceiling is lowered to it, and no
agent finding is ever critical. URLs are split by origin: pages of the audited
site become `affected_pages`; everything else becomes cited sources.

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

If nothing fires, supply an empty `findings` array *with* a `checks` map: the
stage records `assessed_no_findings` and the checks you marked `pass` leave the
limitations list. An empty array on its own records `empty_unspecified` and every
check stays not assessed. If no file is supplied at all, or it names a different
site than the audit, the stage records `not_supplied`.

## Guarantees

Read-only. Does not fetch the audited site (it reads the agent brief). Never
reports an unavailable capability as a site defect: a stage that did not run is
recorded as `not_supplied` and listed under limitations; any
insufficient_evidence entry is capped low and advisory by Invariant I-1.
