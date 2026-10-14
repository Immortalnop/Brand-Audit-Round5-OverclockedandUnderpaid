# Brand AI-Readiness Audit

A multi-skill Agent Skill Marketplace that audits any website for **AI discoverability** and **on-site engagement** problems. Given a URL, the entrypoint crawls the site (read-only, bounded) and produces a single structured JSON report containing evidence-backed findings and prioritized suggested actions. It never modifies a live site.

## Skills

### 1. `audit-orchestrator` *(entrypoint)*

Validates the target URL, performs a single bounded acquisition (robots.txt, sitemap, llms.txt, HTML pages), then schedules and composes the outputs of all other skills into one final report. Handles deduplication, severity prioritization, recommendation generation, and report validation.

### 2. `crawl-render-audit`

Analyzes the acquisition snapshot for crawlability and machine-readability issues:
- Robots.txt and AI-crawler access for 18 crawlers, each labelled search (OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot), user-requested fetch (ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User) or training (GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider); a whole-site block of a search crawler is high, any other block low
- Sitemap presence; optional supplied llms.txt observation, format (H1 title, Markdown links in H2 sections) and dead links it lists; the companion `llms-full.txt` is probed too
- Recursive JSON-LD structured data inspection and schema-type coverage
- Citation-oriented markup: incomplete or inconsistent FAQPage, HowTo, Review and AggregateRating markup, and optional structured export of existing steps or ratings
- Technical metadata (titles, descriptions, canonicals, language, social cards)
- Page performance (HTML size, markup ratio, fetch latency)
- Core Web Vitals (LCP, CLS, INP): real-user field data when a PageSpeed Insights key is set (`PAGESPEED_API_KEY`), otherwise estimates from markup patterns, labelled as estimates
- Rendering gap detection (JS-dependent content); `<noscript>` text is not counted as content unless it is a real fallback, and a "JavaScript required" notice is cited as evidence
- hreflang and multi-language sites: malformed codes, relative URLs, missing self-references, alternates that do not link back or answer 404, and pages in several languages with no hreflang (from HTML, Link headers and the sitemap)
- Text drawn in graphics: canvases with no text alternative, facts that exist only in inline SVG, and icon-font glyphs or ligature names leaking into page text
- Image context: content images with no alt text, figcaption, title or link text
- Image weight: file size, served format and pixel size of up to 4 same-origin content images (one Range GET each), and main images without srcset or `<picture>` sources
- Text alternatives for media: alt text that is a file name or placeholder word, video and audio without a transcript or captions, and missing or incomplete VideoObject/AudioObject markup
- Facts locked in non-text media: text drawn in same-origin SVG images, raster images named as price lists, menus or spec sheets, facts that exist only in linked PDFs, and scanned PDFs with no text layer
- Answer formats: question headings not followed by a direct answer, data tables without header cells, comparison pages without a comparison table, and product pages whose specifications exist only as prose
- Personalization signals: a physical location shown on the page but absent from structured data, incomplete LocalBusiness markup, and commercial sites with no page for a named audience

### 3. `freshness-corroboration`

Analyzes page content quality and entity identity:
- Claim extraction and important-fact ranking
- Freshness assessment of dated facts from visible text and from JSON-LD `datePublished`/`dateModified`, plus invalid structured dates
- Page update dates from sitemap `<lastmod>` and the HTTP `Last-Modified` header (build-stamped, per-request and invalid values are ignored), and a check for missing or unreliable `lastmod`
- Entity identity resolution from structured data
- Knowledge-graph link: whether Organization `sameAs` names a Wikidata item or Wikipedia article, and, for a declared link, whether that entity's name and official website match the site (a few robots-checked GETs to public `/wiki/` pages; off with `KNOWLEDGE_GRAPH_LOOKUP=0`)
- sameAs and profile links: invalid values (share links, platform home pages, the site itself, relative URLs) without any request; then, for the rest, whether each profile resolves and names the brand or the site (robots-checked GETs, at most 8 profiles and 2 per host, 18-second budget; off with `OFF_SITE_LOOKUP=0`). Platforms that forbid crawlers or answer bots with a challenge are reported as unverified, never as broken
- Review and directory presence: Trustpilot, G2, Capterra, Google Business Profile, Yelp and similar profiles linked from the site or sameAs, plus one "reviews" search when a search provider is configured
- Authorship and E-E-A-T on articles: a byline, an Article author typed as a Person, a profile link and credentials
- Expired offers: "sale ends", "offer valid until" and similar wording followed by a full date that has passed, and Offer `priceValidUntil` or `validThrough` in the past (editorial, legal, archive and event pages are skipped)
- On-site fact consistency: a telephone, postal code, opening hours or product price in JSON-LD that the visible pages contradict, and one organization or product (same @id, organization name or product GTIN) with two values for one property on different pages in the same language
- Answer-content quality (title-body alignment, keyword stuffing, brand definition)
- External footprint and corroboration (when search is available)

### 4. `engagement-audit`

Analyzes on-site visitor engagement and navigation:
- Site graph construction (internal link structure)
- Orphan pages and isolated clusters (pages keyed by their final URL after redirects; reported only when the crawl reached every discovered URL, since a sample cannot show what unfetched pages link to), and dead-end detection
- Breadcrumb and orientation analysis
- Internal discoverability and generic anchor text
- Visitor retention opportunities
- Accessibility beyond alt text: unlabeled form fields, links and buttons with no accessible name, low contrast and small targets where inline styles set them
- Overlays and cookie banners: blocking dialogs, full-screen layers and scroll locks in the delivered HTML, consent-platform markup and scripts, and cookie wording used as the page description
- Context retention: large sites without site search, shops without saved or recently viewed items, and redirects that drop a deep link's query parameters

### 5. `entity-corroboration-agent`

An agent-executed qualitative stage. When invoked by an AI agent with web search capability, it:
- Assesses About-page concreteness
- Checks cross-web entity agreement or contradiction
- Reads facts drawn inside raster images with the agent's own vision (AG-04)
- Searches Wikidata and Wikipedia for entities that share the brand name (AG-05); robots.txt disallows their search endpoints to scripts
- Searches review and directory platforms, Reddit and Quora for the brand's profiles (AG-06); those platforms block automated clients
- Produces structured findings the entrypoint merges into the report: either merged into a saved report afterwards (`run_audit.py --from-report report.json --agent-findings agent.json`, no request and no new crawl) or read during the audit (`run_audit.py <site> --agent-findings agent.json`). An agent finding that reports the same check as a script finding, such as AG-04 and facts-in-images, is folded into it

Skips gracefully when no search capability is available; it does not report its own absence as a site defect.

## How the entrypoint composes them

```
URL input
    │
    ▼
┌─────────────────────────┐
│   audit-orchestrator     │  ← entrypoint
│   1. Validate URL        │
│   2. Acquire site once   │
│      (robots, sitemap,   │
│       llms.txt, pages)   │
│   3. Schedule analysis   │
│      DAG in parallel:    │
│      ┌─────────────────┐ │
│      │ crawl-render     │ │
│      │ freshness        │ │
│      │ engagement       │ │
│      │ entity-agent     │ │
│      └─────────────────┘ │
│   4. Merge & deduplicate │
│   5. Prioritize findings │
│   6. Generate recs       │
│   7. Validate report     │
│   8. Add fix snippets +  │
│      impact x effort     │
│   9. Emit JSON to stdout │
└─────────────────────────┘
```

The three native specialist skills read the immutable acquisition snapshot. The host entity agent reads its bounded evidence packet; merge and rendering make no requests.

Suggested `owner_roles` identify semantic roles (developer, infrastructure, content, SEO); they assign no teammates. `priority_basis` records the actual severity/status/confidence/reach/effort ordering and tie breakers, without rescoring. Rule-specific assessed denominators are shown when recorded; otherwise they are unavailable. Every suggested action carries an impact (from severity and evidence), an effort and its impact x effort quadrant. `top_actions` marks one `start_here` item and `quick_wins` lists the cheap, valuable fixes. For markup fixes (JSON-LD, llms.txt, canonical and Open Graph tags, location and contact markup) the action includes a ready-to-paste `snippet` filled from what the audit observed; anything it did not observe is a listed `REPLACE_WITH_` placeholder, never a guess.

`recommendations` link to proactive findings by `finding_id` rather than copying their evidence and steps; only the baseline maintenance items carry their own action. `whats_working` lists the checks that ran and passed (for example "All 12 pages checked have a document title"). A check appears there only when its skill finished, no finding or recommendation carries its check IDs, and the stated observation holds on the crawled pages, so the section never hides a skipped check or contradicts a finding.

## Quick start

For the complete Claude Code workflow, load the extracted package from a writable
workspace outside that package. This is a native Claude plugin; the root
marketplace.json continues to describe the audit engine's skill contracts.

```bash
claude --plugin-dir /absolute/path/to/Brand-AI-Readiness-Audit-round5-final_version
```

In Claude Code, run:

```text
/brand-audit:audit https://tartinebakery.com/
```

Change only the URL for another site. Each invocation creates a fresh
out/<UTC-run-id>/ folder and uses the maintained full audit procedure. It keeps
the normal 50-page cap, shared clock, supported AG checks and local merge. The
final summary includes a short next prompt and links repair-prompt.md, which
contains the full report and available evidence/outcomes for verification and
repairs in the website's source repository. It does not apply repairs itself.

For persistent use, install the extracted release once from its local catalog:

```bash
claude plugin marketplace add /absolute/path/to/Brand-AI-Readiness-Audit-round5-final_version
claude plugin install brand-audit@brand-audit-marketplace
```

Then start Claude in a writable audit workspace and use the same URL command.
The release includes .claude-plugin/plugin.json and a distinct Claude marketplace
catalog. See [Claude's skill invocation](https://code.claude.com/docs/en/skills)
and [local plugin installation](https://code.claude.com/docs/en/plugin-marketplaces).
[The replay manifest](replay/REPLAY_Overclocked_and_Underpaid_round5_final.txt)
has the full demo launch, optional capabilities and recording instructions.

The Python entrypoint remains available for a native audit without the Claude
host stage or repair export:

```bash
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com > report.json
python3 skills/audit-orchestrator/scripts/run_audit.py --max-pages 100 https://example.com > report.json ##allows you to crawl for 100 pages instead of default 50 pages. Can't go any higher, needs a code change then.
python3 common/report_markdown.py report.json        # optional: writes report.md
```

Stdout JSON escapes non-ASCII characters so legacy console encodings can print it;
JSON readers recover the original Unicode text. In Windows PowerShell 5, `>`
writes UTF-16. Use `--out` for a UTF-8 file with literal Unicode and the same JSON
values; it prints nothing to stdout:

```powershell
python skills/audit-orchestrator/scripts/run_audit.py snu.edu.in --out results.json; python common/report_markdown.py results.json
```

The full workflow with the optional agent stage acquires the site once. The audit writes the report and a bounded evidence packet; the host agent reads the packet, runs the `entity-corroboration-agent` checks (AG-01 to AG-06) its tools allow and writes one outcome per check; the merge and the Markdown make no request:

```bash
python3 skills/audit-orchestrator/scripts/run_audit.py <site> --out out/base-report.json --evidence-out out/evidence.json
# the host agent reads out/evidence.json and writes out/agent-outcomes.json (see the entity-corroboration-agent SKILL.md)
python3 skills/audit-orchestrator/scripts/run_audit.py --from-report out/base-report.json --agent-findings out/agent-outcomes.json --evidence out/evidence.json --out out/final-report.json
python3 common/report_markdown.py out/final-report.json out/final-report.md
python3 common/repair_handoff.py --report out/final-report.json --out out/repair-prompt.md
```

Release 8.4.1 uses packet/outcome schema 1.1. It corrects body/template/date context and adds the shared host clock, compact handoff setup and one bounded full-image fetch. Independent Claude reads can overlap; outcome writes remain sequential. Final packet digests bind every exported passage, claim, focus and image to the report; edits require a new export and assessment. Known failed About targets remain not assessed, and exact fragments identify the selected body passage. Git/release provenance records dirty or unknown state explicitly.

Release 8.4.3 retains introductory headers inside main, section and article content when selecting body openings, exporting body text and counting main headings. Document headers, navigation, footers, explicit chrome roles and hidden content remain excluded. Existing reports and packets keep their original observations; run a new acquisition and agent assessment to use the corrected evidence.

Release 8.5.0 adds the Claude audit command and local verification/repair handoff.
The handoff retains every finding, recommendation and available bound evidence
without reclassifying them. Its file checks establish consistency, not truth;
the next agent must verify the findings and obtain the website's editable source.
The audit engine, AG rules, native stdout and timing/crawl defaults are unchanged.

The base report is never overwritten (the merge refuses to write over its input) and stays the merge base. AG-01 needs only the packet; checks that need search or vision are recorded as not assessed when the host did not run them. `examples/` holds one complete run of this workflow: `sample-report.json` (the base report), `evidence.json`, `agent-outcomes.json`, `final-report.json` and `final-report.md`. `tests/test_round5_release.py` replays the same workflow offline on a fixture site.

`--out` checks the path before the audit starts, writes the file in one step (a failed run never leaves half a report), and prints the report to stdout instead if the file cannot be written.

The Markdown report is built from the JSON report alone, with no new requests: confidence and why, a summary, where to start, top actions, quick wins, every finding with its evidence, steps and ready-to-paste fix, what is working, and what the audit could not check. It reads UTF-8 or UTF-16 JSON (PowerShell's `>` writes UTF-16) and always writes UTF-8. Text from the audited site is escaped, so it cannot add headings, links, table columns or HTML. Pass a second path to name the file, or `-` to print it.

No installation required beyond Python 3.10+ standard library. No pip install, no API keys, no browser download.

Optional environment variables:

| Variable | Effect |
|---|---|
| `PAGESPEED_API_KEY` | Fetch Core Web Vitals field data from the PageSpeed Insights API (one GET, started at audit start). Without it, LCP, CLS and INP are estimated from markup. |
| `FIELD_VITALS_LOOKUP=0` | Never call the PageSpeed Insights API, even with a key. |
| `OFF_SITE_LOOKUP=0` | Do not fetch sameAs or review profiles; only the checks that need no network run. |
| `KNOWLEDGE_GRAPH_LOOKUP=0` | Do not verify the declared Wikidata or Wikipedia entity. |
| `SEARCH_API_URL`, `SEARCH_API_KEY` | Optional search provider for corroboration, footprint and review-platform search. |
| `AGENT_FINDINGS_PATH` | JSON findings from the agent stage (AG-01 to AG-06), read during the audit; `--agent-findings PATH` does the same. |

## Safety

- **Read-only**: only HTTP GET; no authentication, form submission, or site modification.
- **Login pages out of scope**: a fetched page is not analyzed only when it has a visible password input, at most 1,500 characters of visible text, no entity structured data (Organization, Product, Article and so on), and a login signal: an auth path (`/login`, `/sign-in`, `/wp-login.php`, matched as a whole path segment), a login title or H1, or a login form outside the header, nav and footer. Any page with real copy or entity markup is always audited. It is listed in `coverage.out_of_scope_pages` with its signals, and the report warns when the start URL is a login page.
- **SSRF protection**: every URL (target, redirects, discovered links, sitemaps) is validated against loopback, private, link-local, multicast, reserved, and cloud-metadata ranges.
- **Robots-first**: unknown robots permission prevents page acquisition (fail closed, not open).
- **Bot challenges are respected, never bypassed**: a response that is a bot-protection interstitial (a challenge header, an error status with a challenge or block-page marker, or a nearly empty 2xx page with a challenge-only marker) is recorded in `coverage.challenged_pages` and never analyzed as site content, so it is never reported as a thin, untitled or broken page. Fastly's `Client Challenge` interstitial requires its exact title together with a `/_fs-ch-…/` asset marker; an embedded Fastly script alone leaves a normal page eligible. The audit never retries a challenge, runs its script or changes its User-Agent; two challenges in a row, or three in all, end the crawl, and no optional request follows.
- **Honest empty reports**: when no page could be analyzed, `execution_status` is `insufficient_evidence`, `coverage.acquisition_failure` gives the reason (DNS, TLS, timeout, robots.txt, 401/403, 429, server error, bot challenge, cross-origin redirect, login page, safety policy), the summary, limitations and confidence explanation lead with it, and only checks that never read page content (robots.txt, llms.txt, sitemap, TLS) are reported.
- **Character encodings**: a byte order mark, then the HTTP charset, then `<meta charset>` or `http-equiv` in the first 2 KB, then UTF-8. Labels that are not web encodings are ignored; ISO-8859-1 and ASCII read as windows-1252, as browsers do. A page sent as UTF-8 that is mostly invalid UTF-8 is read as windows-1252.
- **Redirects to another site**: never followed during the crawl. When the start URL itself (or its robots.txt) redirects to another origin, such as `example.so` to `example.com` or `http` to `https`, and nothing could be analyzed, the audit moves once to that origin, checks it against the SSRF policy, reads its robots.txt first, and names both URLs in the report.
- **Sampled, not exhaustive**: sitemap URLs are crawled round-robin across site sections (first path segment), so a bounded crawl reaches every section before any section gets a second page. The 200 candidate URLs are chosen this way from the first 2,000 sitemap entries, so a section listed after the 200th entry of a large sitemap is still reached. Overall confidence measures how representative the analyzed sample is (sections reached and sample size), not only the share of discovered URLs; a page fetched but not analyzed counts for nothing, and brand identity is reported beside the score rather than in it. Each finding's confidence says how likely the stated problem is real, and its `coverage` says how many analyzed pages showed it. The confidence block also names its `level` (high, medium or low), the `limiting_factor` that set it, and a plain-English `explanation`. `--max-pages N` (at most 100) crawls deeper on purpose; the request and byte budgets grow with it, the time limit does not.
- **Bounded**: 50-page crawl cap by default. One shared network ledger per audit (`coverage.network_budget`): 90 requests and 40 MiB for the audited site (robots.txt, retries, redirect hops, a re-anchored origin, the HTTPS probe, media, llms.txt checks and the optional headless browser's reserved slice all count) and 40 requests and 16 MiB for third-party lookups; the agent stage's own tool calls are not counted. The audit worker is stopped at 270 seconds. The optional agent stage gets at most 210 seconds from the remaining 270-second workflow target, with 45 seconds reserved for saving, merge, rendering and reply. The Claude demo passes a host start clock captured before reading skills; this also narrows the worker to remaining time. Ordinary direct CLI runs retain the 270-second worker ceiling and default 50-page cap. Only the worker and optional image-fetch helper have enforced process limits; arbitrary host tool cancellation is not enforced. Merge timing excludes rendering and the final reply. After the page crawl, at most 6 images and 3 PDFs are fetched (same origin, robots-checked) from the budget that remains; PDF parsing is capped at 4 seconds per file. A site served over plain HTTP gets one GET of `https://<host>/robots.txt` to check whether HTTPS is available. Up to 4 same-origin content images get a Range GET of their first 32 KiB to read file size and format. llms.txt adds at most 1 probe of `/llms-full.txt` and 8 GETs of listed same-origin pages that were not already crawled. Third-party requests are limited to links the site itself declares, and each host's robots.txt is read first (fail closed): the knowledge-graph verification (at most 4 GETs to public `/wiki/` pages of wikidata.org and wikipedia.org, within 15 seconds) and the sameAs and review profiles (at most 8 profile GETs, 2 per host, within 18 seconds). With `PAGESPEED_API_KEY` set, one GET to the PageSpeed Insights API runs alongside the crawl (at most 45 seconds); the key is never written to the report. A failed or blocked lookup only adds a limitation.
- **Streaming**: response bodies are streamed under per-request byte caps to prevent memory exhaustion.

## Marketplace structure

```
Brand-AI-Readiness-Audit/          <- marketplace root 
├── marketplace.json               <- manifest: lists all skills, marks the entrypoint
├── .claude-plugin/                <- Claude plugin metadata and local install catalog
├── README.md                      <- this file
├── .gitignore
├── common/                        <- shared library imported by every skill
│   ├── __init__.py
│   ├── action_catalog.py          <- baseline suggested-action templates per category
│   ├── ai_crawlers.py             <- AI and search crawlers, each labelled search, training or user fetch
│   ├── capabilities.py            <- runtime capability detection (rendering, search)
│   ├── check_catalog.py           <- single source of check_id -> mechanism/fix wording
│   ├── check_helpers.py
│   ├── constants.py               <- crawl caps, budgets, timeouts
│   ├── errors.py
│   ├── external_lookup.py         <- robots-checked GETs to third-party hosts
│   ├── field_vitals.py            <- optional Core Web Vitals field data (PageSpeed Insights)
│   ├── fix_snippets.py            <- ready-to-paste JSON-LD, llms.txt, canonical and OG fixes
│   ├── html_features.py
│   ├── instrumentation.py         <- request/stage telemetry
│   ├── llms_txt.py                <- llms.txt format parser
│   ├── models.py                  <- immutable AuditArtifacts, finding factory, invariants
│   ├── non_text.py                <- SVG text, image headers, fact comparison for media
│   ├── pdf_text.py                <- bounded standard-library PDF text extraction
│   ├── platforms.py               <- video, podcast, review and directory platform hosts
│   ├── report_markdown.py         <- JSON report to a readable Markdown report
│   ├── robots_policy.py           <- robots.txt parsing and fail-closed policy
│   ├── search_provider.py         <- optional external-search adapter
│   ├── structured_data.py         <- JSON-LD extraction/parsing
│   ├── subprocess_isolation.py    <- bounded worker isolation
│   ├── tls_context.py             <- verified-TLS transport context
│   ├── transport.py               <- streaming, byte-capped HTTP GET
│   └── url_safety.py              <- SSRF validation (loopback/private/metadata ranges)
├── skills/
│   ├── audit-orchestrator/        <- ENTRYPOINT: composes all other skills
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── audit-state-schema.md
│   │   │   ├── execution-policy.md
│   │   │   ├── finding-schema.md
│   │   │   └── report-schema.md
│   │   └── scripts/
│   │       ├── run_audit.py               <- CLI + top-level pipeline
│   │       ├── acquire_site.py            <- single bounded acquisition
│   │       ├── merge_findings.py          <- dedup + merge across skills
│   │       ├── prioritize_findings.py     <- severity ordering
│   │       ├── generate_recommendations.py
│   │       ├── validate_report.py         <- schema + invariant enforcement
│   │       ├── whats_working.py           <- checks that ran and passed, with evidence
│   │       ├── merge_agent_stage.py       <- --from-report: agent findings into a saved report
│   │       ├── execution_summary.py       <- status/limitations/confidence
│   │       └── diagnose_transport.py
│   ├── crawl-render-audit/        <- crawlability + machine-readability checks
│   │   ├── SKILL.md
│   │   ├── references/crawl-render-checklist.md
│   │   └── scripts/
│   │       ├── analyze_crawlability.py
│   │       ├── analyze_directives.py
│   │       ├── analyze_machine_readability.py
│   │       ├── analyze_metadata.py
│   │       ├── analyze_performance.py
│   │       ├── analyze_rendering.py
│   │       ├── check_ai_crawler_access.py
│   │       ├── check_llms_txt.py          <- llms.txt presence, format, links, llms-full.txt
│   │       ├── analyze_non_text.py        <- facts locked in images and PDFs
│   │       ├── analyze_media_text.py      <- alt text quality, transcripts, VideoObject
│   │       ├── analyze_citation_schema.py <- FAQPage, HowTo, Review, AggregateRating
│   │       ├── analyze_web_vitals.py      <- Core Web Vitals field data or estimates
│   │       ├── analyze_international.py   <- hreflang and multi-language sites
│   │       ├── analyze_graphics_text.py   <- canvas, inline SVG and icon-font text
│   │       ├── analyze_image_context.py   <- alt text, captions and link text as image context
│   │       ├── analyze_image_weight.py    <- image file size, format and srcset
│   │       ├── analyze_answer_format.py   <- direct answers, table headers, comparison and spec formats
│   │       └── analyze_context_signals.py <- location and contact markup, audience segments
│   ├── freshness-corroboration/  <- content quality, freshness, entity identity
│   │   ├── SKILL.md
│   │   ├── references/freshness-corroboration-methodology.md
│   │   └── scripts/
│   │       ├── extract_claims.py
│   │       ├── identify_important_facts.py
│   │       ├── assess_freshness.py
│   │       ├── update_signals.py          <- sitemap lastmod and Last-Modified dates
│   │       ├── check_knowledge_graph.py   <- Wikidata/Wikipedia link verification
│   │       ├── check_off_site_profiles.py <- sameAs profiles and review platforms
│   │       ├── analyze_authorship.py      <- article authors and credentials (E-E-A-T)
│   │       ├── check_offer_expiry.py      <- offers whose stated end date has passed
│   │       ├── check_fact_consistency.py  <- JSON-LD facts vs visible text, and across pages
│   │       ├── resolve_entity_identity.py
│   │       ├── analyze_answer_content.py
│   │       ├── corroborate_claims.py
│   │       └── assess_external_footprint.py
│   ├── engagement-audit/         <- on-site navigation + visitor engagement
│   │   ├── SKILL.md
│   │   ├── references/engagement-checklist.md
│   │   └── scripts/
│   │       ├── build_site_graph.py
│   │       ├── analyze_engagement.py
│   │       ├── analyze_experience.py
│   │       ├── analyze_accessibility.py   <- form labels, control names, contrast, target size
│   │       ├── analyze_overlays.py        <- blocking dialogs, cookie banners, consent text
│   │       └── analyze_context_retention.py <- site search, saved state, deep-link parameters
│   └── entity-corroboration-agent/  <- agent-executed qualitative corroboration
│       ├── SKILL.md
│       ├── references/checks.md
│       └── scripts/ingest_agent_findings.py
└── tests/                        <- pytest suite + local fixtures (not required to run an audit)
    ├── fixtures_server.py
    ├── tls-fixtures/             <- self-signed certs for TLS-recovery tests
    └── test_*.py
```

## Testing

```bash
pip install pytest   # optional, for pytest runner
python3 tests/test_smoke.py              # quick DAG + report validation
python3 tests/test_safety.py             # SSRF, robots, redirects
python3 tests/test_integration.py        # full end-to-end against local fixture
python3 tests/test_dedup_and_recommendations.py  # dedup + recommendations
python3 -m pytest tests/test_non_text_and_dates.py  # images, PDFs, structured dates
python3 -m pytest tests/test_update_signals_and_kg.py  # lastmod, Last-Modified, knowledge graph
python3 -m pytest tests/test_media_schema_authorship.py  # alt text, video/audio, FAQ/HowTo/ratings, authors
python3 -m pytest tests/test_llms_profiles_vitals.py  # llms.txt, sameAs/review profiles, Core Web Vitals
python3 -m pytest tests/test_points_15_21.py  # hreflang, noscript, graphics text, image context and weight, accessibility, overlays
python3 -m pytest tests/test_points_6_11.py  # concrete titles, answer formats, location and context, fix snippets, impact x effort
python3 -m pytest tests/test_precision_traps.py  # false-positive traps, severity gate, rendering-gap evidence
python3 -m pytest tests/test_benchmark_tools.py  # measurement harness and fixture recall
python3 -m pytest tests/test_robustness.py  # blocked and empty runs, bot challenges, encodings, --out
python3 -m pytest tests/test_whats_working.py  # passed checks: never skipped, never contradicting a finding
python3 -m pytest tests/test_offers_facts_crawlers.py  # expired offers, fact consistency, labelled AI crawlers
python3 -m pytest tests/test_agent_stage_merge.py  # agent stage: --agent-findings, --from-report merge
python3 -m pytest tests/test_dev_calibration_fixes.py  # rules corrected on the dev benchmark: teasers, background video, short H1s
python3 -m pytest tests/test_round5_observations.py tests/test_round5_agent_handoff.py tests/test_round5_budget_reports.py tests/test_round5_release.py  # Round 5 regression matrix
```

`skills/audit-orchestrator/references/validation.md` maps each required regression case to its test and lists the environments the suite has run on.

`tests/conftest.py` switches the third-party lookups off for every test, so the suite never leaves the machine; tests of those lookups inject a fake transport.

### Measuring precision on real sites (opt-in)

`tests/live_benchmark.py` audits a local list of real sites, one after another, with the normal safety rules, and writes each report plus a `findings.csv` with an empty `label` column. Label each row `tp`, `fp` or `irrelevant`, then score it:

```bash
LIVE_BENCHMARK=1 python3 tests/live_benchmark.py urls.txt      # lines: "dev https://..." or "holdout https://..."
python3 tests/score_benchmark.py benchmark_runs/findings.csv --split holdout --recall
```

The scorer reports precision, high-severity precision, per-check precision and expected calibration error, and with `--recall` the share of planted defects found in the offline fixture corpora. Tune rules on `dev` sites only and score `holdout` once, so the numbers stay honest about unseen sites. The base confidences that `--suggest` measured on the dev sites live in one table, `CALIBRATED_CONFIDENCE` in `common/check_catalog.py`; a check not listed keeps its script's own confidence. The runner refuses to start without `LIVE_BENCHMARK=1`, and the suite never runs it. It also writes `runs.json` (time, status, pages, requests and bytes per site, failed runs included), and the scorer then reports completion, no-evidence rate, run time p50/p95, request and byte use, and opportunity usefulness separately from defect precision.

## Packaging

`python3 tools/package_release.py --committed` builds the exact committed HEAD snapshot, preserving local source assets and edits. Without that flag the tool reports the working tree state. The builder writes `dist/brand-ai-readiness-audit-<version>.zip` from an allowlist (`marketplace.json`, `README.md`, `skills/`, `common/`, `examples/`, `tests/`, `replay/`) with a `RELEASE.json` naming the version, the commit and whether the tree was clean. Planning PDFs and notes, `data/store.sqlite` (no code reads it), `benchmark_runs/` and `.env` files are left out of the archive but never deleted.

Google Search ignores llms.txt for visibility and ranking, including generative
Search. FAQ rich results ended on 7 May 2026. Useful Q&A and generic FAQPage
parsing remain supported. Missing either artifact creates no universal readiness
defect; supplied llms.txt issues stay scoped to that optional artifact and its
configured readers. No repair proves ranking, citation or conversion gains.
Sources and scope: [Search policy](skills/crawl-render-audit/references/search-policy.md).
