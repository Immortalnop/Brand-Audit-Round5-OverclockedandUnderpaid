# Brand AI-Readiness Audit

A multi-skill Agent Skill Marketplace that audits any website for **AI discoverability** and **on-site engagement** problems. Given a URL, the entrypoint crawls the site (read-only, bounded) and produces a single structured JSON report containing evidence-backed findings and prioritized suggested actions. It never modifies a live site.

## Skills

### 1. `audit-orchestrator` *(entrypoint)*

Validates the target URL, performs a single bounded acquisition (robots.txt, sitemap, llms.txt, HTML pages), then schedules and composes the outputs of all other skills into one final report. Handles deduplication, severity prioritization, recommendation generation, and report validation.

### 2. `crawl-render-audit`

Analyzes the acquisition snapshot for crawlability and machine-readability issues:
- Robots.txt and AI-crawler access (GPTBot, ChatGPT-User, etc.)
- Sitemap presence; llms.txt presence, format (H1 title, Markdown links in H2 sections) and dead links it lists; the companion `llms-full.txt` is probed too
- Recursive JSON-LD structured data inspection and schema-type coverage
- Citation-oriented markup: incomplete or inconsistent FAQPage, HowTo, Review and AggregateRating markup, and pages that show questions, steps or ratings without it
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
- Answer-content quality (title-body alignment, keyword stuffing, brand definition)
- External footprint and corroboration (when search is available)

### 4. `engagement-audit`

Analyzes on-site visitor engagement and navigation:
- Site graph construction (internal link structure)
- Orphan pages, isolated clusters, and dead-end detection
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
- Produces structured findings the entrypoint merges into the report

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

All four analysis skills read the same immutable acquisition snapshot, so nothing is fetched twice.

Every suggested action carries an impact (from severity and evidence), an effort and its impact x effort quadrant. `top_actions` marks one `start_here` item and `quick_wins` lists the cheap, valuable fixes. For markup fixes (JSON-LD, llms.txt, canonical and Open Graph tags, location and contact markup) the action includes a ready-to-paste `snippet` filled from what the audit observed; anything it did not observe is a listed `REPLACE_WITH_` placeholder, never a guess.

## Quick start

```bash
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com > report.json
python3 common/report_markdown.py report.json        # optional: writes report.md
python skills/audit-orchestrator/scripts/run_audit.py snu.edu.in > results.json; python common/report_markdown.py results.json #Both in one line
```

The Markdown report is built from the JSON report alone, with no new requests: confidence and why, a summary, where to start, top actions, quick wins, every finding with its evidence, steps and ready-to-paste fix, and what the audit could not check. It reads UTF-8 or UTF-16 JSON (PowerShell's `>` writes UTF-16) and always writes UTF-8. Text from the audited site is escaped, so it cannot add headings, links, table columns or HTML. Pass a second path to name the file, or `-` to print it.

No installation required beyond Python 3.10+ standard library. No pip install, no API keys, no browser download.

Optional environment variables:

| Variable | Effect |
|---|---|
| `PAGESPEED_API_KEY` | Fetch Core Web Vitals field data from the PageSpeed Insights API (one GET, started at audit start). Without it, LCP, CLS and INP are estimated from markup. |
| `FIELD_VITALS_LOOKUP=0` | Never call the PageSpeed Insights API, even with a key. |
| `OFF_SITE_LOOKUP=0` | Do not fetch sameAs or review profiles; only the checks that need no network run. |
| `KNOWLEDGE_GRAPH_LOOKUP=0` | Do not verify the declared Wikidata or Wikipedia entity. |
| `SEARCH_API_URL`, `SEARCH_API_KEY` | Optional search provider for corroboration, footprint and review-platform search. |
| `AGENT_FINDINGS_PATH` | JSON findings from the agent stage (AG-01 to AG-06). |

## Safety

- **Read-only**: only HTTP GET; no authentication, form submission, or site modification.
- **Login pages out of scope**: a fetched page is not analyzed only when it has a visible password input, at most 1,500 characters of visible text, no entity structured data (Organization, Product, Article and so on), and a login signal: an auth path (`/login`, `/sign-in`, `/wp-login.php`, matched as a whole path segment), a login title or H1, or a login form outside the header, nav and footer. Any page with real copy or entity markup is always audited. It is listed in `coverage.out_of_scope_pages` with its signals, and the report warns when the start URL is a login page.
- **SSRF protection**: every URL (target, redirects, discovered links, sitemaps) is validated against loopback, private, link-local, multicast, reserved, and cloud-metadata ranges.
- **Robots-first**: unknown robots permission prevents page acquisition (fail closed, not open).
- **Redirects to another site**: never followed during the crawl. When the start URL itself (or its robots.txt) redirects to another origin, such as `example.so` to `example.com` or `http` to `https`, and nothing could be analyzed, the audit moves once to that origin, checks it against the SSRF policy, reads its robots.txt first, and names both URLs in the report.
- **Sampled, not exhaustive**: sitemap URLs are crawled round-robin across site sections (first path segment), so a bounded crawl reaches every section before any section gets a second page. Overall confidence measures how representative the analyzed sample is (sections reached and sample size), not only the share of discovered URLs; a page fetched but not analyzed counts for nothing, and brand identity is reported beside the score rather than in it. Each finding's confidence says how likely the stated problem is real, and its `coverage` says how many analyzed pages showed it. The confidence block also names its `level` (high, medium or low), the `limiting_factor` that set it, and a plain-English `explanation`. `--max-pages N` (at most 100) crawls deeper on purpose; the request and byte budgets grow with it, the time limit does not.
- **Bounded**: 50-page crawl cap by default, 90-request budget, 40 MiB body limit, 270-second wall-clock timeout. After the page crawl, at most 6 images and 3 PDFs are fetched (same origin, robots-checked) from the budget that remains; PDF parsing is capped at 4 seconds per file. A site served over plain HTTP gets one GET of `https://<host>/robots.txt` to check whether HTTPS is available. Up to 4 same-origin content images get a Range GET of their first 32 KiB to read file size and format. llms.txt adds at most 1 probe of `/llms-full.txt` and 8 GETs of listed same-origin pages that were not already crawled. Third-party requests are limited to links the site itself declares, and each host's robots.txt is read first (fail closed): the knowledge-graph verification (at most 4 GETs to public `/wiki/` pages of wikidata.org and wikipedia.org, within 15 seconds) and the sameAs and review profiles (at most 8 profile GETs, 2 per host, within 18 seconds). With `PAGESPEED_API_KEY` set, one GET to the PageSpeed Insights API runs alongside the crawl (at most 60 seconds); the key is never written to the report. A failed or blocked lookup only adds a limitation.
- **Streaming**: response bodies are streamed under per-request byte caps to prevent memory exhaustion.

## Marketplace structure

```
Brand-AI-Readiness-Audit/          <- marketplace root 
├── marketplace.json               <- manifest: lists all skills, marks the entrypoint
├── README.md                      <- this file
├── .gitignore
├── common/                        <- shared library imported by every skill
│   ├── __init__.py
│   ├── action_catalog.py          <- baseline suggested-action templates per category
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
```

`tests/conftest.py` switches the third-party lookups off for every test, so the suite never leaves the machine; tests of those lookups inject a fake transport.

### Measuring precision on real sites (opt-in)

`tests/live_benchmark.py` audits a local list of real sites, one after another, with the normal safety rules, and writes each report plus a `findings.csv` with an empty `label` column. Label each row `tp`, `fp` or `irrelevant`, then score it:

```bash
LIVE_BENCHMARK=1 python3 tests/live_benchmark.py urls.txt      # lines: "dev https://..." or "holdout https://..."
python3 tests/score_benchmark.py benchmark_runs/findings.csv --split holdout --recall
```

The scorer reports precision, high-severity precision, per-check precision and expected calibration error, and with `--recall` the share of planted defects found in the offline fixture corpora. Tune rules on `dev` sites only and score `holdout` once, so the numbers stay honest about unseen sites. The runner refuses to start without `LIVE_BENCHMARK=1`, and the suite never runs it.
