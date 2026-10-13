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
- Env (optional): `PAGESPEED_API_KEY` adds Core Web Vitals field data;
  `OFF_SITE_LOOKUP=0`, `KNOWLEDGE_GRAPH_LOOKUP=0` and `FIELD_VITALS_LOOKUP=0`
  switch the third-party lookups off.
- Network: outbound GET only, to the target site, to profiles and
  knowledge-graph entries the site itself declares, and (if configured) the
  external search endpoint and the PageSpeed Insights API. No target credentials
  or mutating requests; provider credentials remain optional.

## Inputs
- `site_url`: a URL or bare domain.
- Saved report, packet and handoff inputs use the limits and numeric policy in
  [references/input-boundaries.md](references/input-boundaries.md). Invalid typed
  inputs are rejected atomically before merge; source content remains data.

## Procedure
1. Call `scripts/run_audit.py: run_audit(site_url)`.
2. It validates the URL, acquires the site once (`acquire_site.py`), runs the
   independent analysis batch (crawl-render-audit checks plus the data-producing
   steps of freshness-corroboration and engagement-audit), runs the mandatory
   sequential `identify_important_facts` step, then runs the dependent batch
   (freshness, corroboration, footprint, knowledge graph, off-site profiles,
   Core Web Vitals, engagement). The optional Core Web Vitals field-data request
   starts before acquisition so its latency overlaps the crawl.
3. Findings are merged (`merge_findings.py`; checks that report one problem with
   one fix, such as missing alt attributes and images with no text alternative,
   become one finding), prioritized (`prioritize_findings.py`), and validated
   (`validate_report.py`). Both of the last two apply the severity gate: a high or
   critical finding must be confirmed or backed by two independent kinds of
   evidence, else it is lowered and says why. See `references/severity-rubric.md`.
4. Agent stage (AG-01 to AG-06). Run the audit with the evidence packet
   (`python3 scripts/run_audit.py <site> --out report.json --evidence-out packet.json`).
   The report is complete at this point; the agent stage is optional. Then
   follow `skills/entity-corroboration-agent/SKILL.md`: read the packet (never
   the audit's process, and never a new crawl of the site), run each check your
   tools allow, and write one outcome per check to an outcome envelope. Merge
   it, with no request:
   `python3 scripts/run_audit.py --from-report report.json --agent-findings envelope.json --evidence packet.json --out final.json`.
   The envelope is checked against the report and the packet (audit ID,
   snapshot and final packet digests (schema 1.1), final references, focused source,
   per-check semantics, supported affected scope and severity ceilings) and
   rejected as a whole, with reasons, if anything fails; report.json is left
   unchanged either way and stays the merge base. AG-01 needs only the packet;
   AG-02, AG-03, AG-05 and AG-06 need a search tool; AG-04 needs image viewing.
   A missing capability leaves only its own checks `not_assessed`, and their
   limitations stay in the report. A legacy findings array is still accepted
   (`legacy_partial`) but assesses no check. Skip this step when you have no
   such tools: the report then records the stage as `not_supplied`.
5. Return the resulting report to the user as-is.

## Safety guarantees (enforced by `acquire_site.py`, not just documented)
- **SSRF protection**: every URL fetched -- the initial target, robots.txt,
  sitemap.xml, llms.txt, discovered links, and every redirect hop -- is checked
  by `common/url_safety.py` first. Disallowed schemes, credentials-in-URL, cloud
  metadata hosts/IPs, and (by default) loopback/private/link-local/reserved
  addresses are all rejected before any request is issued. Blocked URLs are
  recorded as safety skips, never as findings.
- **One re-anchor, never a cross-origin crawl**: redirects to another origin are
  not followed during the crawl. Only when the start URL or its robots.txt
  redirects to another origin and no page could be analyzed does the audit move,
  once, to that origin: the target must resolve and pass the SSRF check, its own
  robots.txt is read first, and the report names both URLs
  (`coverage.start_redirect`, `coverage.audited_url`).
- **Bot challenges are never bypassed**: a bot-protection interstitial is
  recorded (`coverage.challenged_pages`), never analyzed as content and never
  retried; the User-Agent never changes. Two challenges in a row, or three in
  all, end the crawl (`common/bot_challenge.py`).
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
- **Off-site profiles are bounded and optional**: sameAs and linked review
  profiles get at most 8 GETs (2 per host) within 18 seconds, each host's
  robots.txt read first (fail closed); `OFF_SITE_LOOKUP=0` turns it off.
  Platforms that forbid crawlers or answer bots with a challenge are reported as
  unverified, never as broken.
- **Image weight checks are bounded**: at most 4 same-origin, robots-checked
  Range GETs of 32 KiB read content-image size and format. A plain-HTTP site
  gets one GET of `https://<host>/robots.txt`.
- **llms.txt checks are bounded**: one probe of `/llms-full.txt` and at most 8
  same-origin, robots-checked GETs of listed pages that were not already
  crawled; links to other domains are never requested.
- **Core Web Vitals field data is opt-in**: only with `PAGESPEED_API_KEY`, one
  GET to the PageSpeed Insights API after reading its robots.txt, at most 60
  seconds, running alongside the crawl. The key never appears in the report.
  Without it, LCP, CLS and INP are estimated from markup and labelled as
  estimates.

## Output
A JSON report matching `references/report-schema.md`: `site`, `audited_at`,
`summary`, `coverage`, `findings`, `recommendations`, `execution_status`
(completed / completed_with_timeouts / degraded / partial_deadline_reached /
insufficient_evidence when no page could be analyzed: then
`coverage.acquisition_failure` names the reason, `summary.status_reason`,
the first limitation and the confidence explanation lead with it, and only
robots.txt, llms.txt, sitemap and TLS findings are kept),
`limitations` (plain-English, each tied to a real signal from the run -- never
unconditional boilerplate), and `confidence` (the minimum of sample
representativeness, counted from analyzed pages, and an execution penalty, with
its method shown, plus a `level`, the `limiting_factor` and a plain-English
`explanation`; brand identity confidence is reported beside the score, not in
it). Each finding's `confidence` is the probability that the stated problem is
real (a `confirmed` finding needs at least 0.7) and its `coverage` states how
many of the analyzed pages it was seen on. Login pages (a visible password input, at most 1,500
characters of visible text, no entity structured data, plus an auth path, a
login title or a login form outside the page chrome) are fetched but not analyzed;
`coverage.out_of_scope_pages` lists them with their signals. Sitemap URLs (chosen from the first 2,000 entries) are crawled round-robin across site sections, so a
bounded crawl samples every section first, including sections a large sitemap lists late; `--max-pages N` (at most 100)
crawls deeper with proportionally larger request and byte budgets. Recommend-only -- no skill ever modifies a live site.

`common/report_markdown.py` turns a saved JSON report into a Markdown report
for a non-expert (`python common/report_markdown.py report.json` writes
`report.md`). It reads only the JSON, makes no requests and escapes all site text.

After validation the entrypoint adds two aids a non-expert can act on
(`common/fix_snippets.py`, `prioritize_findings.annotate_action_plan`):
ready-to-paste fix snippets (JSON-LD, llms.txt, canonical and Open Graph tags,
location and contact markup) built only from observed facts, with every unknown value left
as a listed REPLACE_WITH_ placeholder; and an impact x effort placement on every
action, surfaced as `top_actions` (with one `start_here`) and `quick_wins`.

`recommendations` link to proactive findings by `finding_id` instead of
copying them; only baseline maintenance items carry their own action.
`whats_working` (`scripts/whats_working.py`) lists the checks that ran and
passed, each with the observation that shows it. A check is listed only when
its skill finished, no finding or recommendation carries its check IDs, and the
observation holds on the snapshot, so it never hides a skipped check or
contradicts a finding.

Headless rendering runs in an isolated child process
(`common/subprocess_isolation.py`) with a hard wall-clock kill, not just
Playwright's own cooperative per-navigation timeout -- a genuinely hung browser
process cannot block the orchestrator past its deadline.

## Example

```
$ python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com
$ python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --out report.json
$ python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --out report.json --evidence-out packet.json
$ python3 skills/audit-orchestrator/scripts/run_audit.py --from-report report.json --agent-findings envelope.json --evidence packet.json --out final.json
```

`--out PATH` writes the same JSON as UTF-8 (use it in Windows PowerShell, whose
`>` writes UTF-16). `--evidence-out PATH` also writes the bounded agent evidence
packet; it is written only when at least one page was analyzed. The report,
packet, agent input and final report must be four different files.

Time plan: the audit worker is stopped at 270 seconds (`--timeout` lowers it).
The whole workflow targets 270 seconds: the agent stage gets what the audit
left before that, at most 55 seconds, and the merge 15. A slow site that uses
the full worker limit leaves no agent time. The report's `timing` and the
packet's `timing` give the agent deadline as a UTC time. This code cannot stop the host agent: stop the agent
stage by that deadline, and skip it when `agent_stage_recommended` is false.
The merge records the measured workflow time. Network: every request of the
audit is charged to one ledger with a site pool (90 requests, 40 MiB by
default) and an external pool (40 requests, 16 MiB), reported in
`coverage.network_budget`; the agent's own tool calls are not in it.

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
  "confidence": {"score": 0.82, "level": "high", "limiting_factor": "sample_representativeness",
                 "explanation": "Confidence is high (0.82). ..."}
}
```
