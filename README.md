# Brand AI-Readiness Audit

A multi-skill Agent Skill Marketplace that audits any website for **AI discoverability** (can AI assistants and search engines reach, read, extract and trust its facts?) and **on-site engagement** (does a visitor who arrives from an AI answer stay?). Given a URL, the entrypoint acquires the site once (read-only, bounded, robots-respecting), runs four analysis skills on that snapshot, adds an agent-performed cross-web check, and emits one structured JSON report plus a readable `report.md`. It never modifies a live site.

## How a finding is decided

Every check belongs to one gate of a chain. A failure early in the chain hides everything after it, so the gate sets the typical severity:

| Gate | Question | Examples |
|---|---|---|
| access | Can a crawler get in and receive the content? | bot-protection walls, robots.txt per RFC 9309, Googlebot/Bingbot/AI-agent blocks, noindex |
| readability | Is the content present as text? | JavaScript-only content, facts only in PDFs or images |
| extractability | Can a machine pick out the fact and the entity? | missing or invalid JSON-LD, undeclared brand identity |
| trust | Are the facts consistent and current? | markup contradicting the page, expired offers, contradictory dates, cross-web contradictions |
| engagement | Does the arriving visitor continue? | orphan pages, no next step, weak orientation, mobile viewport |

Severity is **impact** (set by the detector, adjusted only for scope). Confidence is **evidence strength** (sample size and template diversity for absence claims). Priority is **derived** in one place (`common/scoring.py`): `impact x reach x confidence / effort`. Every finding carries a `severity_rationale` that shows this.

## Skills

### 1. `audit-orchestrator` *(entrypoint)*
Validates the URL, performs one bounded acquisition (robots.txt, sitemap with lastmod, llms.txt, template-diverse page sample, key-fact PDF range reads), schedules the other skills, merges findings by root cause, scores them, splits SEO-hygiene items into an appendix, builds the action plan and beyond-defect recommendations, validates, and writes `report.json`, `agent_brief.json` and `report.md`. Pass 2 (`finalize_report.py`) merges the agent stage without re-crawling.

### 2. `crawl-render-audit`
Access, readability and extractability: bot walls (`analyze_access.py`), role-weighted crawler access for 18 agents (`check_ai_crawler_access.py`), robots and broken pages, indexing directives, JavaScript-only content (empty app shell + hydration payload vs HTML, browser-confirmed when enabled), facts locked in PDFs/images/iframes (`analyze_nontext_facts.py`), JSON-LD per page type with draft snippets, JSON-LD completeness/validity/consistency with the page (`validate_structured_data.py`), metadata and llms.txt.

### 3. `freshness-corroboration`
Claim extraction, brand identity resolution with a five-level fallback (Organization JSON-LD, WebSite name/og:site_name, title segment, footer copyright holder, domain), date checks by meaning (expired offers, contradictory dates, stale "last updated", stale copyright, undated articles), answer-content heuristics, optional scripted corroboration.

### 4. `engagement-audit`
Site graph over real content pages (orphans, isolated clusters, dead ends), next steps, orientation, generic anchors, breadcrumbs, viewport/zoom, overlays, email-capture pages whose substance is in images.

### 5. `entity-corroboration-agent`
Agent-performed: About-page concreteness (AG-01), no independent mention (AG-02), independent sources contradicting the site (AG-03), using the agent's own web search on public sources (including Reddit and Quora) and the brief written by pass 1. If no search tool is available the stage is recorded as `not_supplied`, never as "nothing found".

## How the entrypoint composes them

```
URL
 |
 v
audit-orchestrator  pass 1: run_audit.py --out-dir audit_out
 |  1. validate URL
 |  2. acquire once: robots (RFC 9309) -> sitemap -> llms.txt -> priority crawl
 |     (home, nav/footer, key intents; <= 3 pages per URL template; bot-challenge aware)
 |  3. independent batch (parallel): crawl-render-audit checks, claims, identity, site graph
 |  4. important facts (sequential)
 |  5. dependent batch (parallel): freshness, answer content, corroboration, engagement
 |  6. merge (exact + root-cause group) -> score -> core / hygiene -> order -> action plan
 |  7. validate -> report.json, agent_brief.json, report.md
 v
entity-corroboration-agent  (the calling agent searches, writes agent_findings.json)
 |
 v
audit-orchestrator  pass 2: finalize_report.py  (merge, re-score, re-validate; no re-crawl)
```

All analysis skills read the same immutable acquisition snapshot; no analysis script makes a network request.

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

Useful options: `--urls FILE` audits exactly the listed same-site pages (for example the landing pages of prompts a brand is losing); `--timeout S` lowers the 270 s cap; `--quiet` silences stderr. stdout is always pure JSON.

No installation required beyond Python 3.10+. Optional: `ENABLE_RENDERING=1` with `pip install playwright && playwright install chromium` confirms render gaps with a real browser; `SEARCH_API_URL` enables scripted corroboration.

## Installation note

The marketplace is installed as a unit: the skills share one library (`common/`) so every check, score and wording rule is defined once. Each skill's `scripts/_bootstrap.py` locates the folder containing `marketplace.json` and exits with a clear message if a skill folder was copied out on its own.

## Safety

- **Read-only**: only HTTP GET; no authentication, form submission or site modification.
- **SSRF protection**: every URL (target, redirects, discovered links, sitemaps) is validated against loopback, private, link-local, multicast, reserved and cloud-metadata ranges.
- **robots.txt per RFC 9309**: 4xx means no restrictions; 429/5xx/timeout means disallow-all; a robots file behind a bot challenge means permission unknown, so only the homepage is fetched, once.
- **Courtesy**: crawl-delay honoured; a template that returns challenges is not sampled further; 3 consecutive challenges stop the crawl.
- **Bounded**: 50 pages, 90 requests, 40 MiB, 270 s; byte caps enforced while streaming.

## Marketplace structure

```
Brand-AI-Readiness-Audit/
  marketplace.json           manifest: lists all skills, marks the entrypoint
  README.md, Changes_A.md     (what changed in Round 5 and why)
  common/                    shared library
    access_guard.py          bot-challenge / WAF interstitial detection
    url_keys.py              visit keys and URL templates for sampling
    scoring.py               severity / confidence / priority model
    check_catalog.py         every check: mechanism, fix, outcome, gate, group, tier, owner
    schema_rules.py          JSON-LD required/recommended properties and validators
    dates.py                 date parsing and context classification
    identity_signals.py      brand-name fallbacks
    action_catalog.py, capabilities.py, check_helpers.py, constants.py, errors.py,
    html_features.py, instrumentation.py, models.py, robots_policy.py,
    search_provider.py, structured_data.py, subprocess_isolation.py,
    tls_context.py, transport.py, url_safety.py
  skills/
    audit-orchestrator/      ENTRYPOINT (run_audit, acquire_site, merge, prioritize,
                             recommendations, validate, finalize_report, render_report)
    crawl-render-audit/
    freshness-corroboration/
    engagement-audit/
    entity-corroboration-agent/
  examples/                  sample-report.json / .md (generated from the local fixture)
  tests/                     pytest suite + local fixture server
```

## Testing

```bash
python3 -m pytest -q                       # full suite, offline (local fixture server)
python3 examples/make_sample_report.py     # regenerate examples/sample-report.{json,md}
```
