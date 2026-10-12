# Brand AI-Readiness Audit

A multi-skill Agent Skill Marketplace that audits any website for **AI discoverability** (can AI assistants and search engines reach, read, extract and trust its facts?) and **on-site engagement** (does a visitor who arrives from an AI answer stay?). Given a URL, the entrypoint acquires the site once (read-only, bounded, robots-respecting), runs four analysis skills on that snapshot, adds an agent-performed cross-web and vision check, and emits one structured JSON report plus a readable `report.md`. It never modifies a live site.

## How a finding is decided

Every check belongs to one gate of a chain. A failure early in the chain hides everything after it, so the gate sets the typical severity:

| Gate | Question | Examples |
|---|---|---|
| access | Can a crawler get in and receive the content? | bot-protection walls, robots.txt per RFC 9309 (incl. a rate-limited robots.txt), Googlebot/Bingbot/AI-agent blocks, noindex |
| readability | Is the content present as text? | JavaScript-only content, facts only in PDFs or images |
| extractability | Can a machine pick out the fact and the entity? | missing or invalid JSON-LD, undeclared brand identity, FAQ/HowTo/rating markup, contact details missing from markup |
| trust | Are the facts consistent and current? | markup contradicting the page, expired offers, contradictory dates, unreliable sitemap lastmod, namesakes, cross-web contradictions |
| engagement | Does the arriving visitor continue? | orphan pages, no next step, missing or generic headings, mobile viewport, newsletter email readability |

Severity is **impact** (set by the detector, adjusted only for scope; an absence claim from three pages or fewer is capped at medium). Confidence is **evidence strength** (sample size and template diversity for absence claims). Priority is **derived** in one place (`common/scoring.py`): `impact x reach x confidence / effort`. Every finding carries a `severity_rationale` that shows this.

## Skills

### 1. `audit-orchestrator` *(entrypoint)*
Validates the URL, performs one bounded acquisition (robots.txt, sitemap with lastmod, llms.txt, template-diverse page sample, key-fact PDF range reads; login pages kept out of scope), schedules the other skills, merges findings by root cause, scores them, splits SEO-hygiene items into an appendix, attaches ready-to-paste fixes, builds the action plan (with quick wins and a "start here" item), lists the checks that passed ("what's working"), adds beyond-defect recommendations, explains its confidence, validates, and writes `report.json`, `agent_brief.json` and `report.md`. Pass 2 (`finalize_report.py`) merges the agent stage without re-crawling.

### 2. `crawl-render-audit`
Access, readability and extractability: bot walls and a rate-limited robots.txt (`analyze_access.py`), role-weighted crawler access for 18 agents, robots and broken pages, indexing directives, JavaScript-only content (empty app shell and hydration payload vs HTML; a page that runs no script is never a gap), facts locked in PDFs/images/iframes, JSON-LD per page type with draft snippets, JSON-LD completeness/validity/consistency with the page, FAQ/HowTo/Review/AggregateRating markup (`analyze_citation_schema.py`), contact details shown but not in markup (`analyze_contact_markup.py`), metadata and llms.txt.

### 3. `freshness-corroboration`
Claim extraction, brand identity resolution with a five-level fallback (Organization JSON-LD or a home-page Organization subtype such as Plumber, WebSite name/og:site_name, title segment, footer copyright holder, domain), date checks by meaning (expired offers, contradictory dates, stale "last updated", stale copyright, undated articles), sitemap lastmod reliability (`update_signals.py`), sameAs and knowledge-graph links (`check_entity_links.py`), answer-content heuristics, optional scripted corroboration.

### 4. `engagement-audit`
Site graph over real content pages (orphans, isolated clusters, dead ends), next steps, missing or generic headings, generic anchors, breadcrumbs, viewport/zoom, overlays, and newsletter signups whose outbound email should stay readable to inbox AI summaries (only real newsletter forms, never contact, trial or login forms).

### 5. `entity-corroboration-agent`
Agent-performed, using the brief written by pass 1: About-page concreteness (AG-01), no independent mention (AG-02), independent sources contradicting the site (AG-03), facts inside images read with the agent's own vision (AG-04), same-named entities and no distinguishing knowledge-graph link (AG-05), and missing review or directory profiles for the brand's kind of business (AG-06). If no search tool is available the stage is recorded as `not_supplied`, never as "nothing found".

## How the entrypoint composes them

```
URL
 |
 v
audit-orchestrator  pass 1: run_audit.py --out-dir audit_out
 |  1. validate URL
 |  2. acquire once: robots (RFC 9309) -> sitemap -> llms.txt -> priority crawl
 |     (home, nav/footer, key intents; <= 3 pages per URL template; bot-challenge
 |     aware; login pages kept out of scope)
 |  3. independent batch (parallel): crawl-render-audit checks, claims, identity,
 |     sitemap dates, entity links, site graph
 |  4. important facts (sequential)
 |  5. dependent batch (parallel): freshness, answer content, corroboration, engagement
 |  6. merge (exact + root-cause group) -> score -> core / hygiene -> order
 |  7. fix snippets -> action plan + quick wins -> recommendations
 |  8. validate -> what's working -> report.json, agent_brief.json, report.md
 v
entity-corroboration-agent  (the calling agent searches and reads images,
 |                            writes agent_findings.json)
 v
audit-orchestrator  pass 2: finalize_report.py  (merge, re-score, re-validate; no re-crawl)
```

All analysis skills read the same immutable acquisition snapshot; no analysis script makes a network request.

## What the report gives a non-expert

- **How far to trust it**: a confidence level (high, medium, low), the factor that limits it, one reason per part and a plain-English explanation.
- **Start here** and **Top actions**: the ordered plan, with quick wins marked (medium impact or more, low effort, solid evidence).
- **Findings**: what we found, why it matters, evidence, how to fix (with a ready-to-paste snippet for markup fixes: JSON-LD, llms.txt, canonical, Open Graph, contact markup; anything the audit did not observe is a listed `REPLACE_WITH_` placeholder, never a guess), how to verify, and why this severity.
- **What's working**: checks that ran and passed, with the observation (for example "All 9 pages checked declare a canonical URL"). A check is listed only if it finished and no finding contradicts it.
- **Limitations** and pages kept out of scope.

Site text in `report.md` is escaped, so a page title cannot add headings, links, table columns or HTML.

## Quick start

```bash
# Pass 1 (deterministic, stdlib only)
python3 skills/audit-orchestrator/scripts/run_audit.py https://example.com --out-dir audit_out > audit_out.json

# Agent stage: follow skills/entity-corroboration-agent/SKILL.md with audit_out/agent_brief.json,
# write audit_out/agent_findings.json ([] if nothing fires or no search tool)

# Pass 2
python3 skills/audit-orchestrator/scripts/finalize_report.py --report audit_out/report.json \
        --agent-findings audit_out/agent_findings.json
```

Useful options: `--urls FILE` audits exactly the listed same-site pages (for example the landing pages of prompts a brand is losing); `--timeout S` lowers the 270 s cap; `--quiet` silences stderr; `--explain` prints how the run spent its budget. stdout is always pure JSON.

```
$ python3 skills/audit-orchestrator/scripts/run_audit.py https://pypi.org --quiet --explain
[explain]   runtime            11.865 s (budget 270 s)
[explain]   requests           17 attempted, 17 completed, 0 failed (budget 90)
[explain]   pages              9 analysed of 10 fetched; 9 distinct templates; 223 discovered
[explain]   stage timings      acquisition 11.72 s; independent_batch 0.06 s; ...
[explain]   acquisition share  99% of measured stage time, and all of the network cost: ...
[explain]   skips              209 robots_disallowed, 1 sensitive_route, 3 template_cap_reached
```

Those are measured numbers, not configured ones, and they are the reason the architecture is "acquire once, analyse many": acquisition carries the whole network cost, every analysis stage is CPU over one immutable snapshot, and the skipped URLs are the robots rules showing up as data.

No installation required beyond Python 3.10+. Optional: `ENABLE_RENDERING=1` with `pip install playwright && playwright install chromium` confirms render gaps with a real browser; `SEARCH_API_URL` enables scripted corroboration.

## Installation note

The marketplace is installed as a unit: the skills share one library (`common/`) so every check, score and wording rule is defined once. Each skill's `scripts/_bootstrap.py` locates the folder containing `marketplace.json` and exits with a clear message if a skill folder was copied out on its own.

## Safety

- **Read-only**: only HTTP GET; no authentication, form submission or site modification.
- **SSRF protection**: every URL (target, redirects, discovered links, sitemaps) is validated against loopback, private, link-local, multicast, reserved and cloud-metadata ranges.
- **robots.txt per RFC 9309**: 4xx means no restrictions; 5xx/timeout means disallow-all; a robots file that answers 429 or sits behind a bot challenge means permission unknown, so only the homepage is fetched, once.
- **Login pages out of scope**: a page with a visible password field, little text, no entity markup and a login path or heading is never analysed as content; a home page with a login box stays in scope.
- **Courtesy**: crawl-delay honoured; a template that returns challenges is not sampled further; 3 consecutive challenges stop the crawl.
- **Bounded**: 50 pages, 90 requests, 40 MiB, 270 s; byte caps enforced while streaming.
- **Character encodings**: byte order mark, then HTTP charset, then `<meta charset>`, then UTF-8 (mostly invalid UTF-8 is read as windows-1252), so legacy pages are read correctly.

## Marketplace structure

```
Brand-AI-Readiness-Audit/
  marketplace.json           manifest: lists all skills, marks the entrypoint
  README.md
  common/                    shared library
    access_guard.py          bot-challenge / WAF interstitial detection
    auth_pages.py            login pages kept out of scope
    url_keys.py              visit keys and URL templates for sampling
    scoring.py               severity / confidence / priority model
    check_catalog.py         every check: mechanism, fix, outcome, gate, group, tier, owner
    fix_snippets.py          ready-to-paste fixes built from observed facts
    schema_rules.py          JSON-LD required/recommended properties and validators
    dates.py                 date parsing and context classification
    identity_signals.py      brand-name fallbacks
    action_catalog.py, auth_pages.py, capabilities.py, check_helpers.py, constants.py,
    html_features.py, instrumentation.py, models.py, robots_policy.py,
    search_provider.py, structured_data.py, subprocess_isolation.py,
    tls_context.py, transport.py, url_safety.py
  skills/
    audit-orchestrator/      ENTRYPOINT (run_audit, acquire_site, merge, prioritize,
                             recommendations, whats_working, validate, finalize_report,
                             render_report)
    crawl-render-audit/
    freshness-corroboration/
    engagement-audit/
    entity-corroboration-agent/
  examples/                  sample-report.json / .md (generated from the local fixture)
  tests/                     pytest suite, local fixture servers, benchmark tools
```

## Testing and evaluation

```bash
python3 -m pytest -q                       # full suite, offline (local fixture servers)
python3 examples/make_sample_report.py     # regenerate examples/sample-report.{json,md}
```

The same site audited twice produces the same findings, scores, order and passed checks (pinned by `test_two_audits_of_one_site_produce_the_same_report`); only the clock and the measured timings differ. `finalize_report.py` is idempotent, so re-running pass 2 cannot drift.

Generalization is tested by construction: `tests/archetype_sites.py` builds nine small sites offline -- a single-page app, a shop, a local business, a documentation site, a blog, a multi-language site, and three precision traps (a news publisher, a splash page, a store) -- with defects planted on purpose and page shapes that commonly trip heuristics. `tests/test_archetype_fixtures.py` asserts which checks must fire (and on which pages) and which must not. `python3 tests/score_benchmark.py <csv> --recall` prints that corpus as a scored table (17 planted defects, recall and trap checks wrongly raised).

Precision on real sites is measured with an opt-in harness that never runs in the suite:

```bash
LIVE_BENCHMARK=1 python3 tests/live_benchmark.py urls.txt   # lines: "dev https://..." or "holdout https://..."
# label each row of benchmark_runs/findings.csv as tp, fp or irrelevant, then:
python3 tests/score_benchmark.py benchmark_runs/findings.csv --split holdout --recall
```

The scorer reports precision, high-severity precision, per-check precision, expected calibration error and, with `--recall`, the share of planted fixture defects found and the number of trap checks wrongly raised. Tune on `dev` sites only and score `holdout` once.
