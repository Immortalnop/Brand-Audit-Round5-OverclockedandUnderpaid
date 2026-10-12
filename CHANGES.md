# Changes in 9.1.0

9.1.0 is the Round 5 engine (9.0.0, branch `adya_v1`) with the best parts of the `add_md` branch merged in, the open issues from comparing the two engines on live sites fixed, and a fixture corpus that found and now pins a set of false positives.

| | 9.0.0 | 9.1.0 |
|---|---|---|
| Tests | 251 passing, 2 environment failures | **330 passing**, 0 failing |
| Checks in the catalog | 100 | 109 |
| Offline fixture sites | 1 | 10 (plus 3 robustness sites) |
| Report sections | findings, action plan, recommendations, hygiene | + what's working, quick wins, start here, explained confidence, ready-to-paste fixes |

Constraints kept: Python standard library only on the core path, GET only, robots.txt respected, under 300 s, deterministic, recommend-only, no analysis script makes a network request.

## 1. Merged from `add_md`

| Feature | Where |
|---|---|
| **What's working**: checks that ran and passed, with the observation. Listed only when the check finished and nothing in the report contradicts it; pass 2 drops entries an agent finding contradicts. | `skills/audit-orchestrator/scripts/whats_working.py` |
| **Explained confidence**: level (high/medium/low), limiting factor, one reason per component, plain-English explanation. | `execution_summary.overall_confidence` |
| **Quick wins and start here** in the action plan (medium impact or more, low effort, confidence >= 0.6). | `generate_recommendations.build_action_plan` |
| **Ready-to-paste fixes** for llms.txt, canonical, Open Graph, Twitter card, contact markup and brand identity, filled from observed facts; anything not observed is a listed `REPLACE_WITH_` placeholder. | `common/fix_snippets.py` |
| **FAQ / HowTo / Review / AggregateRating markup**: incomplete markup (`citation-schema-invalid`) and visible questions, steps or ratings with no markup (`citation-schema-opportunity`). Linked teaser headings never count. | `analyze_citation_schema.py` |
| **Contact markup**: the site's own email or phone shown but in no JSON-LD (`contact-markup-missing`). Only same-domain emails and phones on the home/contact page or two pages count, so an address quoted in a README never fires. | `analyze_contact_markup.py` |
| **Sitemap lastmod reliability**: none at all, or one build date on most entries (`sitemap-lastmod-unreliable`). A build-stamped sitemap is left out of date-contradiction checks. | `update_signals.py` |
| **Entity links** (offline part): `same-as-invalid` (share links, platform home pages, the site itself) and `kg-link-missing` (only for brands that already maintain sameAs). | `check_entity_links.py` |
| **Organization subtypes** (Plumber, Restaurant, CollegeOrUniversity ...) recognised for identity on the home page and for page-type expectations; validated as their parent type. | `common/structured_data.py`, `resolve_entity_identity.py`, `schema_rules.py` |
| **Login pages out of scope**: password field + <= 1,500 characters + no entity markup + a login path or heading. Listed in `coverage.out_of_scope_pages`; not counted against access confidence. | `common/auth_pages.py` |
| **Character encodings**: BOM, HTTP charset, `<meta charset>`, then UTF-8 with a windows-1252 fallback. 9.0.0 ignored `<meta charset>` and turned legacy pages into replacement characters. | `common/transport.decode_body` |
| **Agent checks AG-04 to AG-06**: facts inside images read with the agent's own vision (merges with the script's `facts-in-images`), namesakes with no distinguishing knowledge-graph link, missing review/directory profiles for the kind of business. The brief lists the candidate images, the declared Wikidata/Wikipedia links and the platforms to search. | `ingest_agent_findings.py`, `run_audit.build_agent_brief`, agent `SKILL.md` |
| **Safe Markdown**: site text is escaped; snippets are fenced with more backticks than they contain. | `render_report.py` |
| **Evaluation tooling**: the archetype and precision-trap fixture sites, an opt-in live benchmark that writes a CSV to label, and a scorer for precision, high-severity precision, calibration error and fixture recall. | `tests/archetype_sites.py`, `tests/live_benchmark.py`, `tests/score_benchmark.py` |

Not merged, on purpose:

- **Live Wikidata/Wikipedia and profile lookups.** These are third-party requests from analysis code, which this engine does not make. Namesake and profile checks moved to the agent stage (AG-05, AG-06), which has its own search tool.
- **Core Web Vitals via PageSpeed** (needs an API key and an external call), and **hreflang, media transcripts, accessibility, overlays, image weight, location markup, authorship**. Real gaps, listed under limitations below; each would need its own precision fixtures before shipping.
- **`add_md`'s bot-challenge detector.** It missed PyPI's "Client Challenge" page; `common/access_guard.py` already detects it.

## 2. Fixes from the live comparison

| Issue | Fix |
|---|---|
| The email-summary finding fired on any form with an email field (it was the #2 top action on basecamp.com). | Fires only for a real newsletter or mailing-list signup: email field, newsletter/subscribe wording, no password. Contact, trial and login forms never count. |
| "No JSON-LD" rated high from a one-page sample (npmjs.com: 0/1 pages). | Absence claims from three content pages or fewer are capped at medium, with the reason in `severity_rationale.adjustment`. |
| robots.txt answering HTTP 429 produced only a low "could not be retrieved" item. | New `robots-rate-limited` finding (medium, suspected: one 429 may be transient); the homepage is fetched once to see whether the content is refused too. |
| 11 placeholder mechanisms ("The observed condition can limit retrieval...") still sat in the catalog source, overridden later. | Removed from the source; a test keeps them out. Run-on steps ("Audit error pages Add 301 redirects") rewritten as sentences. |
| llms.txt "Why it matters" repeated "What we found"; same for no-headings and dead-ends. | Real mechanisms; a test asserts no catalog mechanism equals its fix. |
| Sitemap finding titled "Review the sampled sitemap endpoint". | "No XML sitemap was found" / "The XML sitemap could not be parsed". |
| The frontmatter test needed PyYAML; the interrupt test timed out under full-suite load. | A stdlib frontmatter parser (also checks the 1,024-character description limit); a 30 s guard timeout. |

## 3. False positives found by the fixture corpus

Running the new offline corpus (`tests/test_archetype_fixtures.py`) against 9.0.0 exposed these. Each is fixed and pinned:

| Site shape | False finding | Fix |
|---|---|---|
| A page that runs no JavaScript | `render-gap-unconfirmed` | A page with no executable script cannot have a JavaScript rendering gap. |
| A login page | `render-gap-unconfirmed` | Rendering checks skip out-of-scope pages. |
| A product photo next to a price in text | `facts-in-images` | The large-image rule needs a price-type page whose text states no price. |
| "Acme sells ..." / "Acme fixes ..." | `brand-definition` | The defining-verb list covers sells, runs, fixes, repairs, teaches and similar. |
| TechArticle without datePublished | `schema-missing-required` (medium) | Article dates are recommended, as Google documents; missing dates are reported by `missing-article-dates`. |
| H1 "API reference" | `page-orientation` | Fires only on a missing, generic ("Home", "Welcome") or paragraph-length H1. |
| `/blog/`, `/news/` section indexes | `page-type-schema-gap:article` | Section indexes are a `listing` page type. |
| `href="/culture "` | `orphan-pages` + `fetch-failure` | Hrefs are whitespace-trimmed, as browsers do. |
| A masthead name repeated on a news front page | `term-repetition` | The brand's own name is left out of the count. |
| A product gallery with alt text | `email-summary-readable` | Needs the signup page's message in images: under 60 words and most images without alt. |
| Every organization | `kg-link-missing` | Only for brands that already declare sameAs profiles. |

## 4. Results on live sites (12 Oct 2026)

| Site | 9.0.0 | 9.1.0 |
|---|---|---|
| pypi.org | 4 core + 2 hygiene; confidence 0.45 | 4 core + 2 hygiene, 15 passed checks; the generic "orientation heading" item is gone and the Help page's unmarked Q&A is reported; confidence 0.45 with explanation |
| basecamp.com | 6 core (email-form padding at #2) | 7 core + 7 hygiene, 14 passed checks; the email finding is now backed by the real Mailchimp newsletter form; contact markup and FAQ opportunities added, each with a ready-to-paste fix |
| npmjs.com | robots 429 -> one low item, no bot-wall finding; "No JSON-LD" high from 1 page | bot wall reported with Cloudflare evidence; "No JSON-LD" capped at medium from 2 pages |

Live results vary with each site's bot protection and rate limits; run audits one at a time.

## 5. Compatibility

- Same entrypoint, invocation and handout-required fields; stdout is still one JSON report.
- New report fields: `whats_working`, `quick_wins`, `action_plan[].quick_win`, `action_plan[].start_here` (also on `top_actions`), `confidence.level`, `confidence.limiting_factor`, `confidence.reasons`, `confidence.explanation`, `coverage.pages_out_of_scope`, `coverage.out_of_scope_pages`, `suggested_action.snippet`, and `ag04`/`ag05`/`ag06` in the agent brief.
- New check IDs: `robots-rate-limited`, `citation-schema-invalid`, `citation-schema-opportunity`, `contact-markup-missing`, `sitemap-lastmod-unreliable`, `kg-link-missing`, `same-as-invalid`, `kg-namesake-ambiguity` (AG-05), `review-platform-missing` (AG-06).
- Changed behaviour: robots.txt 429 leads to a homepage-only probe (was: no page fetched); Article `datePublished` is recommended, not required; `page-orientation` fires on missing or generic H1s only; email checks need a newsletter signup.
- Four existing tests were changed: one asserted behaviour this release deliberately replaced (an email form with no newsletter wording no longer fires `email-summary-readable`; a negative test next to it says why); the frontmatter test no longer needs PyYAML; the interrupt test has a 30 s guard; the hard-coded-domain test allows the knowledge-graph hosts (wikidata.org, wikipedia.org) alongside schema.org.

## 6. Known limitations

- The sample is 50 pages; site-wide statements are about the sampled templates.
- Without `ENABLE_RENDERING=1`, render gaps are suspected, not confirmed.
- English-only word-based checks skip other languages.
- Not covered: hreflang, video/audio transcripts, accessibility beyond alt text, overlays beyond markup hints, Core Web Vitals, image weight, location markup, author/E-E-A-T markup, llms.txt link checks.
- Namesake, review-platform and image checks depend on the calling agent having search and vision tools; without them the stage is `not_supplied`, never "nothing found".
- The live benchmark has not been labelled yet: precision and calibration on real sites are still to be measured with `tests/live_benchmark.py` and `tests/score_benchmark.py`.
