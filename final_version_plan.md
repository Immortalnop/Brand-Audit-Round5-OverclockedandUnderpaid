**Adobe Round 5: Final master repair and integration plan**

Prepared for Overclocked & Underpaid, 13 October 2026, India time.

**Purpose and implementation instruction**

Implement this plan in Aarush's add_md codebase. Repair its identified errors, correct the selected Adya components before reuse, integrate those components, and validate one combined candidate. The coding agent owns this implementation sequence; it must not wait for either teammate to prepare more patches.

This is the complete handoff, including the later Google Search wording and check-policy correction. It supersedes the implementation instructions in the earlier final implementation, branch comparison and selective integration plans. Those documents remain historical evidence. Do not substitute main or import the other rejected repositories.

This document is a specification. The new fixes and ports described here have not been implemented by this planning review. Previously completed destination work must be preserved rather than restarted.

**Pinned inputs and baseline**

| Item | Aarush: destination | Adya: donor |
|---|---|---|
| Branch | add_md | adya_v1 |
| Latest reviewed ZIP | Brand-AI-Readiness-Audit-round5-add_md(2).zip | Brand-AI-Readiness-Audit-round5-adya_v1(1).zip |
| Archive commit | 2c6acbd2a2da7e15710a6f66b86181dcba238336 | c48094d60868e2bf9f404094c4b77aabfd9803ca |
| Manifest version | 8.3.0 | 9.1.0 |
| ZIP SHA-256 | adab2c29dc016bd3044315fa9b0eef8accb9bc5965931e3e5f63be268d16be25 | 7e4e2d6c67c553de94fdd21e556a4a069dc674cbde214d5d7d701889eefd421a |
| Shipped catalogue entries | 134 | 109 |

These identify the uploaded snapshots. If implementation starts from a newer add_md commit, inspect its delta first, update the baseline record, preserve valid newer fixes and map each remaining task to the actual code. Do not treat the live branch as identical to the reviewed ZIP without checking.

Use an isolated branch or checkout of the actual project. Respect repository instructions. Preserve the uploaded ZIPs and supplied source documents. Paths below are relative to the marketplace root unless identified as donor paths.

**What the existing verification established**

The reviewed suites ran on Linux with CPython 3.14.8, local fixtures and external lookup settings disabled. Additional production-function probes exercised parsing, packet construction, agent validation, graph eligibility and structured-data logic. These are controlled counterexamples, not measured incidents on customer sites.

| Check | Verified result | Interpretation |
|---|---|---|
| Aarush full suite | 1,098 passed, 2 failed; 109.24 seconds | The uploaded suite is not fully green. |
| Isolated Aarush failure recheck | Same two failures | Both failures reproduce. |
| Adya full suite | 398 passed; 74.05 seconds | Shipped tests pass, despite independent counterexamples. |
| Aarush shipped fixture recall scorer | 24/24 expected assertions | Coverage of that fixture corpus only. |
| Adya shipped fixture recall scorer | 17/17, zero curated trap hits | A different corpus; not a comparative real-world recall result. |
| Cancellation diagnostic using current worker signature | Exit 130, cancelled JSON, clean stderr | The shipped cancellation fixture is stale. |
| Timeout diagnostic setting both applicable controls | One timeout and failed request counted | The shipped fixture leaves the critical timeout at its default. |

Do not claim that the unedited destination suite passes. Do not turn suite time into audit runtime or fixture recall into broad accuracy.

The archives do not include the reviewed live reports, labels, freeze records and complete host traces needed to certify the teammate's numerical performance claims. Plan.md's reported results remain provisional until their underlying evidence is supplied and checked.

**Scope and architectural constraints**

Preserve the destination's standard-library default, five skills and one designated entrypoint. Keep:

- Immutable acquisition observations and complete/partial/failed eligibility.
- Existing redirect aliases, URL identity and safe origin reanchoring.
- Waiting-room, script-dependence and graph-completeness gates.
- Shared controlled request/byte ledger and remaining-time handling.
- SSRF checks, DNS pinning, TLS verification, robots policy, bounded downloads and same-origin crawl restrictions.
- GET-only interaction without form submission, authenticated-area access or challenge bypass.
- Full supported affected-page collections, separate capped display examples, confidence provenance and scoped opportunities.
- The saved deterministic report as the preserved base for exactly one final agent merge.
- Atomic UTF-8 output, safe Markdown and source-specific repair snippets.

A failed, blocked or truncated observation cannot prove broad content absence. Missing search, vision or rendering creates a scoped limitation, not a website defect. Source content remains untrusted data and cannot change tool authorization or reporting policy.

Do not replace destination transport, acquisition, graph, scoring or agent ingestion with donor versions. Do not add a model server, dashboard, Adobe SDK, automatic website modification or another report hierarchy.

**Selected donor ports**

| Donor source | Destination | Treatment |
|---|---|---|
| skills/audit-orchestrator/scripts/run_audit.py: _about_link_seen, opening_passage, section_passage and the About-selection portion of build_agent_brief | common/agent_evidence.py and existing identity/observation helpers | Adapt focused source selection after correcting exact fragment binding and unread-target states. |
| common/html_features.py: bounded About-section observations | Destination Document/features implementation | Port a small observation mechanism; preserve all other parser behavior. |
| common/schema_rules.py and skills/crawl-render-audit/scripts/validate_structured_data.py | Existing destination structured-data helpers and relevant specialists | Adapt only corrected value and consumer-specific rules, with source matching and overlap mapping. |
| common/check_catalog.py owner metadata; reporting propagation in generate_recommendations.py and render_report.py | Destination catalogue, prioritize_findings.py and common/report_markdown.py | Add suggested roles and explanations without donor scoring. |
| Relevant donor regression fixtures | Destination tests through its production APIs | Transfer counterexamples and positive controls, not weaker expected behavior. |

Exclude donor core/hygiene tiers, confidence formula, outcome envelope, repeated-finalization storage, acquisition policy, graph eligibility, transport and separate post-core search budget. Do not duplicate PDF, iframe, date or schema checks merely because donor IDs differ.

Bootstrap and an explain view are optional after required gates pass.

**Defect register**

All required rows must have an implementation disposition and meaningful regression result.

| ID | Reproduced or inspected issue | Required result | Phase |
|---|---|---|---|
| A01 | Timeout fixture sets ordinary timeout, but start fetch uses the new critical timeout. | Correct controls; preserve timeout/accounting assertions. | 0 |
| A02 | Cancellation fixture substitutes the old three-argument worker; current caller supplies five arguments. | Correct signature; preserve real interrupt, JSON and exit-130 assertions. | 0 |
| A03 | AG-03 accepts an invented site claim citing unrelated valid page evidence and can emit confirmed/high. | Actual acquired claim and appropriate reference-kind binding. | 4 |
| A04 | AG-01 unanswered=[{}] raises TypeError during set construction. | Typed bounded envelope error, no traceback or overwrite. | 1, 4 |
| A05 | Valid page reference plus an unacquired same-origin affected URL is accepted. | Affected scope derives from validated acquired support. | 4 |
| A06 | Edited packet text with unchanged audit/snapshot headers is accepted. | Bind final packet contents with a checked digest. | 2 |
| A07 | A 600,000-character image alt yields a 603,782-byte packet; dropped pages leave an image's E001 reference dangling. | Exact byte bound across all fields and valid final references. | 1, 2 |
| A08 | AG-04 confirms both an exported and an unexported image-associated page. | Explicit eligible compared-page scope; no inherited confirmation. | 4 |
| A09 | Known About target returning 503 becomes not_discovered and homepage fallback. | Known-but-unacquired target stays not assessed. | 3, 4 |
| A10 | Long navigation displaces real About opening/section beyond the generic 4,000-character excerpt. | Focused acquired body passage survives export. | 3 |
| A11 | JSON-LD price NaN crashes native fact consistency with ValueError. | Reject non-JSON constants safely; unaffected checks survive. | 1, 5 |
| A12 | JSON-LD price 1e999 becomes infinity and crashes native fact consistency with OverflowError. | Supported numeric-range handling without false syntax diagnosis. | 1, 5 |
| A13 | parse_price turns -49 into 49, 1e3 into 13, and price123oops into 123. | Preserve meaning or return unsupported; never manufacture a price. | 5 |
| A14 | Present malformed JSON-LD also produces “No structured data found.” | Separate absent, malformed, ambiguous and unsupported extraction states. | 5 |
| A15 | Product 49 USD versus unrelated support-plan 9 produces a suspected mismatch. | Match subject and conditions before describing contradiction. | 5 |
| A16 | Packaged code_version returns +unknown despite available RELEASE.json. | Honest portable metadata fallback. | 6 |
| D01 | section_passage ignores fragment; #team can select unrelated #about. | Correct exact target identity before porting. | 3 |
| D02 | Organization name without url/@id becomes a confirmed missing-required defect. | No universal requirement; applicable enrichment stays advice. | 5 |
| D03 | Calendar validator accepts 2026-99-99. | Calendar-aware supported-format handling. | 5 |
| D04 | Numeric validator accepts boolean price true. | Bool is not a monetary number. | 5 |
| D05 | Relative sameAs with inline external @base and @id coercion is wrongly rejected. | Respect supported base/vocabulary/coercion semantics. | 5 |
| D06 | Product 49 versus unrelated support price 9 becomes confirmed/high because 49 was not found in text. | Explicit conflicting same-subject fact required. | 5 |
| P01 | llms.txt/FAQ advice could promise unsupported Google or universal visibility gains. | Explicit consumer policy, accurate copy and regression guards. | 6 |

A07 is a helper-level counterexample. The current CLI refuses the non-ready oversized result; the probe did not establish that it wrote that oversized file. Its refusal wording and handling of a pre-existing export path also need correction.

A11/A12 crash the native fact-consistency function. Stage isolation may contain that error; do not claim the probes prove the entire audit always crashes.

P01 is a required policy audit and guard, not a claim that every relevant current string was re-inspected after the runtime disconnected. If a current rule already satisfies it, preserve that behavior and add only missing verification.

**Implementation order**

| Phase | Deliverable | Dependencies |
|---|---|---|
| 0 | Pinned candidate, corrected stale fixtures, defect/test record | None |
| 1 | Typed bounded input and numeric boundaries | 0 |
| 2 | Bounded packet, valid references and content binding | 1; reconcile final observations with 3 |
| 3 | Corrected focused About port | 0, 1 |
| 4 | Per-check semantic validation and supported affected scope | 1, 2, 3 |
| 5 | Native fact repairs and corrected limited schema port | 1, existing observation gates |
| 6 | Action metadata, Google policy, docs, examples and portable versioning | 2–5 |
| 7 | Integrated tests, actual host workflow, evaluation and release | 0–6 |

P0 source-binding, fabricated-high, packet-bound and crash failures block the affected enabled capability. Required correctness work cannot be replaced by more features. Optional cleanup is separate.

**Phase 0: establish the candidate**

Record exact base/donor commits and whether newer changes were reviewed. Preserve source ZIPs. Implement in a branch or isolated checkout; do not overwrite teammate changes or reset a shared branch.

Correct:

- tests/test_isolation_and_coverage.py::test_timeouts_are_counted_distinctly_from_other_failures: apply both intended ordinary and critical timeout controls to the slow critical fetch.
- tests/test_runtime_reliability.py::test_real_cli_interrupt_returns_json_and_130: substitute a worker compatible with the current five-argument call and keep it alive until interrupted.

Do not remove these tests or accept their broken outcomes. Preserve behavioral assertions.

Build controlled regression fixtures through current production APIs and immutable snapshot types. Every new restriction needs a genuine positive control: actual acquired AG-03 conflict, complete focused About opening, same-subject price conflict and valid supported relative/base JSON-LD.

For each task retain files changed, failure before, expected behavior after, targeted tests and remaining scope.

**Gate:** baseline suite is green before integration is described as validated; original 1,098/2 result remains documented.

**Phase 1: typed bounded input and numeric boundaries**

Primary areas: ingest_agent_findings.py, common/report_markdown.py, JSON-LD extraction, output writers and a small shared boundary helper if useful.

Keep the existing size policy: agent input 2 MiB, packet 512 KiB, saved-report input 50 MiB. Read at most limit+1 bytes and reject excess. A preliminary file-size check alone is insufficient.

Preserve UTF-8, UTF-8 BOM and documented UTF-16 saved-input compatibility; emit UTF-8.

For report/packet/envelope contracts:

1. Require expected root and nested types before sets, sorting, hashing, enum membership or numeric comparisons.
2. Reject duplicate object keys, evidence IDs and check outcomes instead of silently using the last value.
3. Validate strings, booleans, integer result counts, finite confidence/ranges and list elements explicitly. Bool is not a numeric count.
4. Bound nesting, lists, URLs, text and error output. Do not stringify arbitrary objects into valid semantic fields.
5. Reject nonfinite values and unsupported shapes with normal public errors.
6. Keep rejection atomic: no partial final report, no overwritten saved input/output and no validation fetches.

For page JSON-LD, distinguish syntax failure from processing limits. NaN/Infinity constants are outside JSON grammar. A number such as 1e999 is syntactically legal but can exceed the processor's supported range. Python's default behavior needs explicit handling. [S1][S2]

Use strict constant rejection and a documented bounded finite numeric policy. Range-limited blocks record extraction limitations, not invented syntax defects. Duplicate page-JSON keys record ambiguity rather than a blanket assertion that JSON grammar prohibits them. Keep other usable blocks and page observations.

Use bounded Decimal processing for money where needed, not a new Decimal representation across arbitrary snapshots/reports. Audit later conversions and serialize nonfinite values as prohibited. Do not use default=str to hide invalid semantic types.

**Gate:** malformed members, including unanswered=[{}], produce controlled errors; numeric inputs cannot crash a specialist; encoding compatibility and valid controls remain.

**Phase 2: packet limits, reference integrity and content binding**

Primary areas: common/agent_evidence.py, run_audit.py, packet reader, ingest_agent_findings.py and merge_agent_stage.py.

Retain eight pages, 4,000 characters of exported page text, twelve claims, eight images and 512 KiB emitted JSON. Focused About text must be allocated within the declared page allowance, not silently add an unbounded channel.

Bound all fields before fitting: alt text, titles, keywords, URLs, aliases, identity, claim values, associated-page lists and limitation messages. Initial new bounds can use 500 characters per alt, 2,000 per URL and 1,500 for the focused opening, with small named list caps. Record truncation and omissions honestly.

Repair fitting:

- Prioritize the focused target and necessary support.
- Shrink expendable excerpts/metadata and drop lower-priority records deterministically.
- Recompute counts and completeness from final records.
- Remove or mark unassessable children whose support was dropped.
- Check every E/C/I reference, parent and source after fitting.
- Measure the exact emitted UTF-8 serialization, including digest and any newline.
- Never return a ready packet above the limit.

Revise packet and outcome contracts together to schema 1.1. Add packet_sha256 to packet, saved-report binding and envelope.

Use this documented project canonical encoding for the digest:

~~~python
json.dumps(
    packet_without_its_top_level_packet_sha256,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8")
~~~

Hash with SHA-256. Exclude only the packet's own top-level digest field. This is a project encoding, not a claim of full canonical-JSON standard conformance.

Finalize all contents, including focus, limits and timing, before hashing. Do not mutate them afterward. Store exact emitted byte count in report coverage rather than a self-referential packet byte field.

Merge requires supported versions/readiness, matching audit/snapshot IDs, recomputed packet digest, the report's expected digest and the envelope's digest. Validate the registry before using it.

Include newly used focused and structured-claim observations in the documented snapshot-digest scope. Do not claim that digest covers raw bytes the snapshot did not retain.

Digest binding detects altered/replayed mismatched content; it does not authenticate a website, prove natural-language truth or protect a report and packet deliberately rewritten together.

If export was requested but is not assessable, atomically write a bounded non-ready marker for the current audit and record its real reason. Do not silently leave an older ready packet at that path. Report write failures explicitly while preserving usable core output.

Schema 1.0 bound envelopes require matching regenerated export/assessment; no silent upgrade into 1.1 passes. Legacy arrays may remain legacy_partial, with conservative ceilings, no checks counted as assessed and no unsupported confirmed factual claims.

**Gate:** changed content with old headers fails; harmless formatting follows canonicalization; pathological metadata stays bounded; no dangling references or stale ready exports.

**Phase 3: corrected focused About port**

Destination: common/html_features.py and common/agent_evidence.py, using common/url_identity.py's existing interfaces. Donor functions are references, not file replacements.

Reuse acquired opening_paragraphs before extending parsing. Read body opening separately from title/heading/meta context; metadata alone must not prove the body opening concrete.

| Observation | Selected AG-01 evidence |
|---|---|
| Eligible acquired About page | Its focused body opening |
| Observed fragment with matching captured section | That exact section |
| Known failed/blocked/excluded/budget-skipped/omitted About | Not assessed with actual reason |
| Acquired page but target passage not isolatable | Not assessed |
| No About target observed in bounded discovery | Labelled homepage body-opening fallback |
| No eligible opening | Not assessed |

Support conventional and nonstandard About paths, observed redirects and fragments without a new packet-building crawl.

Keep fragments separate from page identity. Decode appropriately without lowercasing case-sensitive element IDs. A link to #team cannot select unrelated #about text.

Capture bounded section ID, heading/level, passage, source and completion/truncation. Stop at appropriate section or peer/ancestor heading boundaries. Preserve supported hidden/template/script exclusions and the parser's existing hydration, forms, accessibility, links, contacts, media and budget observations.

Add a focused descriptor, with proposed fields:

~~~json
{
  "ag01": {
    "source_kind": "about_section",
    "assessable": true,
    "page_ref": "E002",
    "requested_about_url": "https://brand.example/company#team",
    "section_id": "team",
    "opening_passage": "The actual acquired opening.",
    "opening_complete": true,
    "selection_reason": "Observed About link targets this section",
    "limitations": []
  }
}
~~~

Keep separate raw_html_text/rendered_text/pdf_text provenance. Completeness concerns the defined opening being judged, not the whole site. A complete opening can coexist with incomplete unrelated page content; a cut opening cannot support unqualified absence.

Reconcile descriptor, selected text, digest and final fitter together.

**Gate:** real descriptions survive long navigation; exact fragments/aliases work; known unread targets remain unassessed; focused evidence and references survive fitting.

**Phase 4: semantic AG validation and affected scope**

Primary areas: ingest_agent_findings.py, merge_agent_stage.py, agent SKILL.md/references/checks.md, orchestrator instructions and tests.

Apply shared typed validators followed by explicit per-check rules. Pass outcomes also require supporting evidence. Omitted checks remain not_assessed; errors/capability gaps preserve their own reasons.

| Check | Required evidence | Ceiling/interpretation |
|---|---|---|
| AG-01 | Assessable focused opening, its E reference and actual passage; typed unanswered subset for a finding | Medium, suspected qualitative improvement |
| AG-02 | Executed relevant queries, counts/results, identity and date/context | Low opportunity scoped to those searches |
| AG-03 | Acquired site quote/claim, inspected conflicting independent evidence, same entity, date/context and materiality | High only for supported substantive conflict; no critical |
| AG-04 | Actually viewed full image, I reference, transcription and explicit eligible compared E references | Medium; incomplete scope cannot prove image-only |
| AG-05 | Target/competing entity sources, distinguishing facts and relevant queries | Medium advisory; no proved assistant confusion |
| AG-06 | Applicable platform-specific queries and actual matching/zero-result outcomes | Low opportunity scoped to checked platforms |

AG-01 must assess the selected source for both pass and finding. Reject home assessment when About was selected or known About is unassessed. Require a complete selected opening for an unqualified assessment; validate unanswered members before forming a set. Missing focus is an assessment limit.

For AG-03:

- Require an actual site_quote and appropriate E/C support. Normalize whitespace/harmless Unicode representation without removing material numbers or negation.
- Match the quote to the referenced passage or structured value and its subject/predicate/source. A C reference resolves to acquired support.
- Keep explanatory paraphrase separate from source quote. Unrelated E/C or I-only references cannot bind a textual claim.
- Reject the reproduced invented submarine claim and sources that merely agree with the actual site description.
- Audited origin/observed aliases are not independent. Distinct domains or repeated syndicated copies alone do not prove independent contradiction.
- Require inspected source passages and same-entity/time/context/materiality explanations.
- Keep the evidence inspectable. Structural checks enforce binding; host reasoning and human review still evaluate the natural-language conflict.

AG-04 needs an explicit compared-page set. Every claimed affected page has its own eligible E reference. An unexported association cannot inherit confirmation. Truncated export cannot establish full-text absence; markup comparison needs relevant coverage or a limitation. Raw-only evidence cannot claim the complete rendered experience was assessed. Filename, alt and header bytes are not vision.

AG-05 must not treat the brand's sameAs profiles as competitors by default. AG-06's missing platforms must be a subset of actual applicable queries and outcomes. Search passes need equivalent execution/relevance evidence.

Derive affected_pages from validated acquired references and aliases. Supplied URLs can narrow support, not expand it. Brand-level search advice reports query scope, not invented page counts.

Validate the entire envelope before constructing output. Reject atomically. Recompute actions and completion after enforcement while preserving native contributions and unrelated limits. Keep one final merge; do not add repeated incremental finalization.

Capability flags, queries and quotes are declarations. Verify actual host activity in Phase 7; do not invent execution receipts or attestation APIs.

**Gate:** all AG counterexamples are rejected or appropriately scoped; genuine supported cases work; partial input cannot clear missing-capability limits; merge does not fetch.

**Phase 5: native fact repair and corrected schema subset**

Primary areas: acquisition JSON-LD extraction, common/structured_data.py, skills/freshness-corroboration/scripts/check_fact_consistency.py and existing relevant schema/date/offer checks.

**5a: extraction states.** Track absent, malformed, unsupported/ambiguous and usable blocks separately. no-jsonld applies to observed absence under eligibility gates. A malformed present block needs repair, not a second add-missing-markup action. Preserve usable blocks on mixed pages.

**5b: monetary normalization.** Separate markup-number parsing from visible-money parsing. Preserve signs, decimals and supported exponent meaning; reject bool/nonfinite/junk. Use bounded Decimal operations with length, exponent and precision limits. Supported 1e3 means 1000, never 13; -49 is preserved or receives a documented semantic rejection, never 49. Ambiguous currency/locale is unknown. Zero is not universally invalid. Audit downstream conversions, grouping and formatting. [S4]

**5c: fact matching.** Before contradiction, match entity/product, offer/variant, currency, unit, region and relevant date when available. Multiple offers, ProductGroup, ranges, tax, discounts or unrelated subscriptions are not automatically comparable.

Require explicit conflicting acquired facts. Absence of the markup value is not itself conflict. Product 49 USD versus unrelated support-plan 9 must not become a confirmed/high contradiction or be described as a conflicting product price. Uncertain candidates remain clearly scoped verification advice or not assessed, with conservative ceilings.

Apply the same matching principle to affected telephone/address/hours/cross-page rules. Keep confirmed and suspected groups separate. Full supported page sets remain data; capped evidence samples do not change reach.

**5d: selected value rules.**

| Rule | Required correction |
|---|---|
| Numeric values | Bool excluded; finite bounded numbers; sign/exponent meaning preserved |
| Date/DateTime | Calendar-aware supported formats, leap days and time zones; unsupported forms distinguished from invalid dates |
| Currency | Format distinguished from verified membership; no arbitrary three-letter code treated as proven ISO membership |
| IRI-valued fields | Supported document base, inline @base, @vocab, prefixes and @id coercion |
| Types | Recognized schema.org namespace and deterministic multi-type handling; no foreign namespace local-name conflation |
| Consumer eligibility | Named use case and sourced requirement; recommended/enrichment fields are not universal requirements |

Support a documented limited set of context/value forms. Unsupported custom/remote/scoped contexts or values remain uninterpreted, not automatically defective. Do not add remote context fetching or claim full JSON-LD conformance. Base and vocabulary resolution differ; the external-base sameAs fixture must work. [S3]

Do not rely on convenience local-name stripping as namespace proof for new validation. IRI interpretation also differs from network authorization: a non-HTTP identifier is not automatically malformed JSON-LD, although it may not be fetchable or usable by a named consumer.

Google's general Organization guide has no required properties. Product snippet requirements belong to that consumer, not universal schema validity. [S4][S5]

Map overlaps to existing IDs/actions. Add a new rule only for an uncovered mechanism, with applicability, source, confidence basis and concrete repair.

**Gate:** A11–A15 and D02–D06 corrected; valid controls preserved; no duplicates, unsupported certainty or parser crashes.

**Phase 6: reporting, Google policy, skills and metadata**

**6a: action ownership and priority explanations**

Add optional owner_roles to existing suggested actions and propagate to top_actions/quick_wins. Map semantic roles such as developer, infrastructure, content and SEO; these are suggestions, not teammate assignments. Merge roles deterministically.

Derive priority_basis after final merging/enforcement from the actual destination order: severity, status, confidence/provenance, supported page count, effort and stable ID. Preserve existing ordering and impact/effort behavior for identical substantive input. No donor rescore.

Show assessed denominators where recorded; otherwise say unavailable. A homepage or half a sample does not prove site-wide reach. Preserve confirmed-defect start_here and opportunities as separate classes.

Use existing safe rendering for source text, URLs, newlines, table separators, backticks and snippets. Keep full JSON counts and bounded Markdown samples.

**6b: required llms.txt, FAQ and visibility-claim correction**

Google Search ignores llms.txt for visibility/ranking, including its generative Search features. FAQ rich results stopped appearing on 7 May 2026. These are Google-specific statements, not evidence about every other assistant or consumer. [S7][S8]

Audit existing and selected donor detectors, catalogue/actions, implicit scoring, snippets, What's Working, instructions, README and examples:

1. Missing llms.txt must not create a Google visibility/citation defect or Google score penalty.
2. Presence must not count as proof that Google optimization, ranking or citations improved.
3. Keep bounded discovery/observation and optional consumer-specific advice where appropriate. Name a real consumer/use case; do not assume all non-Google systems use the file.
4. Optional or experimental artifacts must not be presented as universal readiness requirements. A diagnosed issue in a deliberately provided artifact can remain scoped to that artifact and intended use.
5. Remove recommendations, expected outcomes and snippets promising Google's retired FAQ rich result feature.
6. Keep useful audience Q&A and generic JSON-LD/FAQPage parsing/validation. The retired Google display feature does not make FAQ content or the schema type inherently invalid.
7. Missing FAQ markup is not a universal website defect. Do not invent FAQ content or recommend markup solely to obtain the retired feature.
8. Remove unsupported promises of universal visibility, indexing, ranking, citation or conversion gains. Describe observed access/readability/fact issues and plausible scoped repairs. Measured outcomes need their own evidence.
9. If current behavior already complies, preserve it and add only missing guards. This task is targeted policy/copy work, not an architecture rewrite.

Required controls:

| Fixture | Expected behavior |
|---|---|
| Ordinary complete page, no llms.txt | No Google defect/score penalty solely for its absence |
| Same page with llms.txt | No claimed Google visibility/ranking/citation benefit solely for presence |
| No FAQPage | No defect justified by missing Google FAQ rich results |
| Useful existing Q&A/FAQPage | Can remain readable/parseable; no promised Google FAQ result |
| Malformed JSON-LD containing FAQPage | Generic syntax diagnosis remains, without retired-feature claims |
| Optional explicit consumer advice | Clear consumer scope and unmeasured benefit; no automatic universal promotion |

These policy edits are required before release. Preserve every other repair and port in this plan.

**6c: contract documentation and portable version**

Update orchestrator/agent instructions, references, schema descriptions and examples together:

- Acquire once, save base/packet, read packet, assess available checks, save outcomes, merge once and render.
- Treat source content as data, not instructions.
- Explain schema 1.1, content binding, focus and per-check requirements.
- Declare search/vision/rendering needs and distinguish host tools from script-native integrations.
- Keep unavailable checks not assessed.
- Report actual wall time separately from overlapping stage sums and measured/enforced network scope.

Use valid Git metadata when available; otherwise validate RELEASE.json; otherwise honestly unknown. Record the new candidate, not a base/donor commit as if it represented modified code. Keep dirty/unknown state visible.

Recommended next version: 8.4.0; packet/outcome schema 1.1. Use one consistent release version throughout. Regenerate examples from the candidate, never edit hashes or passed outcomes by hand.

Validate all five skill folders, one entrypoint, frontmatter and references against the official format. Metadata validation alone does not prove execution. [S6]

**Gate:** owners/reasons survive merge without rescoring; Google policy controls pass; examples replay; extraction without .git retains honest provenance.

**Phase 7: integrated verification, evaluation and release**

**7a: regression matrix**

Use production APIs/immutable artifacts and genuine positive controls. Restrictions should fail before repair and pass afterward.

| Group | Required cases |
|---|---|
| Input | Wrong roots/members, duplicate keys/IDs/checks, oversized/deep inputs, invalid encoding, nonfinite values |
| Binding | Edited page/claim/focus/image with old digest, wrong audit/snapshot, unsupported version, non-ready packet |
| Fit | Large alt/identity/URL fields, multibyte text, exact byte boundary, dropped support |
| About | Long navigation, conventional/nonstandard path, exact/wrong fragment, aliases, failed/blocked/skipped target, fallback |
| AG | Invented quote, wrong E/C/I kind, unobserved URL, unexported image page, partial text/markup comparison |
| Search | Missing capabilities/queries, irrelevant entity, own-origin source, syndicated sources, unqueried platform |
| Native/schema | NaN/Infinity/1e999, bool/sign/exponent/junk price, malformed-present blocks, external base, foreign namespace, invalid dates |
| Facts | True same-subject conflict versus support-plan/variant/currency/language/time differences |
| Existing precision | Waiting room, ordinary vendor, bundle-only shell, failed linker, partial sitemap and intentional exclusions |
| Google policy | All Phase 6b negative and positive controls |
| Safety/runtime | Private/redirect targets, DNS/TLS/robots, optional paths near shared caps, timeout, interrupt and expired deadline |
| Output | Twelve supported affected pages, malicious Markdown, capability gaps, legacy partial, repeated merge rejection, writer failure |
| Packaging | Clean extraction, common imports, no secrets/data/caches, valid skills/manifest and metadata |

Run targeted checks during development and the full destination suite after integration and material later fixes. Do not rerun solely to increase counts. Adapt donor tests to destination contracts rather than ship incompatible duplicate suites.

**7b: actual host-agent workflow**

Run the actual entrypoint in the demonstration/evaluation environment. Preserve input, acquisition, packet read, source-backed AG-01 result, actual optional search/vision or explicit skips, outcomes, final merge and JSON/Markdown.

Record direct target-page requests to demonstrate one acquisition. Merge and Markdown render make no network requests. External evidence inspection/image viewing belongs to the declared host stage and its measured scope.

Rehearse no search, no vision and failed About. Script-generated envelopes prove mechanics, not real host assessment.

Measure complete user-request-to-final-output wall time. Preserve core 270-second hard stop and maximum 55-second agent allowance within remaining workflow time; do not add a fresh allowance after exhausting the target. Only claim host enforcement where supported timeout/cancellation controls actually enforce it.

Retain the earlier under-five-minute typical-audit target and ZIP limit of 50 MB. Separately, Round 5 presentation targets eight minutes, stops at ten, uses at most seven presented slides and has five-minute Q&A. Do not confuse those budgets.

**7c: all twelve requested quality dimensions**

| Dimension | Evidence |
|---|---|
| Safety/security | Fetch controls, adversarial inputs/source text, bounds and atomic rejection |
| Precision, all findings | Reviewed support/correctness of every emitted finding, with criteria/counts |
| Precision, high severity | Manual review of every high/critical source, scope and severity; false-high count |
| Recall | Independently planted defects with explicit expected set and trap/positive controls |
| Calibration | Confidence basis and ECE/reliability diagnostics with bins, counts and label scope |
| Robustness | Failed/partial/blocked/SPA/budget runs retained in completion accounting |
| Evidence/actionability | Matched sources, supported reach, corrective steps and suggested roles |
| Honesty | Per-check not-assessed states and raw/rendered/measured/enforced distinctions |
| Speed | Whole-workflow runs, p50/p95, timeouts and controlled requests/bytes |
| Skill design | Five-skill composition, one entrypoint, portable needs and actual host execution |
| Test effectiveness | Before/after counterexamples and meaningful positive controls |
| Maintainability | Small shared helpers, stable IDs/contracts, provenance and minimal cross-cutting changes |

Review development outputs against acquired evidence. Score defect precision separately from opportunity usefulness. An all-finding measure must define support for both, not inflate defect precision with generic advice.

Freeze code, rules, confidence settings, capabilities, dataset manifest and scorer before fresh holdout evaluation. Aim for at least six diverse new sites across commerce, publishing, local business, documentation, education and nonprofit, including static/script-dependent shapes. This is a practical failure-finding matrix, not conclusive statistical accuracy.

Label correctness, scope, status, severity and action applicability for all findings. Agent labels can assist triage; independent claims require human review. Retain every high/critical review and disagreement. Do not discard blocked/no-evidence sites from completion accounting.

A holdout used to tune becomes development data. A changed candidate requires fresh untouched evidence for unseen-site claims.

Internal targets remain support precision >=0.95, zero false high/critical, planted-defect recall >=0.90 and ECE <=0.10. These are targets, not achieved results. Heuristic confidence is not automatically a calibrated probability.

Keep versions, dataset/source hashes, commands, capabilities, timestamps, report/packet/outcome hashes, labels, scorer and failure states. Numerical presentation claims must trace to those records.

**7d: package, rehearse and freeze**

Use tools/package_release.py's allowlist from the clean committed candidate when available. Inspect the extracted ZIP, not only the checkout. Retain consistent RELEASE.json and versions.

Exclude credentials, caches, benchmark runs, planning PDFs and unused SQLite files/journals/WAL/shared-memory files. Preserve supplied source/reference assets outside the release; do not delete them. Include intended runtime, skill references, current examples and meaningful tests.

Run the chosen complete workflow at least three times on the intended laptop. Keep a recording from the same frozen candidate. Rehearsals are separate from untouched holdout evaluation.

Use the separate Section 5 research proposal for Adobe relevance. Describe a concrete content/SEO readiness workflow and proposed value. Do not claim an implemented Adobe SDK integration or measured ranking/citation/conversion uplift.

**Optional work after required gates**

A small detached-install bootstrap error can be adapted if useful. Do not rewrite all import paths. An optional saved-report explain view must be read-only, reflect real accounting and avoid “only acquisition makes requests” or summed-overlap-as-wall-time claims. Recheck affected imports/reporting/packaging if included.

**Executable workflow after implementation**

Create an existing output folder and use the actual authorized target. Current CLI flags remain; schema 1.1 is planned behavior.

~~~bash
python3 -m pytest -q
python3 skills/audit-orchestrator/scripts/run_audit.py https://brand.example --timeout 200 --out out/base-report.json --evidence-out out/evidence.json
~~~

The host reads the packet and updated skill, performs only available assessments and writes out/agent-outcomes.json. No command here substitutes for that actual assessment.

~~~bash
python3 skills/audit-orchestrator/scripts/run_audit.py --from-report out/base-report.json --agent-findings out/agent-outcomes.json --evidence out/evidence.json --out out/final-report.json
python3 common/report_markdown.py out/final-report.json out/final-report.md
python3 tools/package_release.py dist
~~~

Use declared test dependencies if pytest is unavailable. Record optional capability settings; do not assume provider keys exist.

**Definition of done and final implementation report**

Finish required Phases 0–7. Every register row must have a change or justified already-satisfied disposition and regression evidence.

Release requires:

- Integrated suite passes without weakened timeout, cancellation or source assertions.
- No known fabricated-high, input/numeric-crash, oversize-packet, altered-packet or dangling-reference failure remains enabled.
- Selected donor ports are corrected and integrated into destination contracts.
- Real host workflow succeeds, with unavailable capabilities visible.
- Extracted package runs with consistent provenance.
- Google-specific policy and unsupported-outcome wording are corrected.
- Numerical or business claims match their actual evidence.

Report changed files, defect mapping, targeted/full tests, actual-host status, evaluation evidence, release identity and remaining limits. An unavailable environment check is unverified, not passing. Do not mark the whole plan complete merely because code compiles.

**Sources and verification record**

Code evidence comes from the pinned uploaded ZIPs and the previous independent suites, diagnostics and production-function probes. No new full-suite result is claimed merely by preparing this file.

The supplied Round 3/Round 5 PDFs and mentor notes define project and presentation constraints. Earlier review artifacts provide history; this document supplies the current implementation scope without requiring Codex to recover those chats or temporary review paths.

| Ref | Primary source | Use |
|---|---|---|
| S1 | [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) | JSON numeric grammar versus processing range and object ambiguity |
| S2 | [Python JSON documentation](https://docs.python.org/3.14/library/json.html) | Explicit nonfinite/duplicate handling and serialization |
| S3 | [W3C JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) | Base, vocabulary, relative IRI and coercion semantics |
| S4 | [Google Product snippet structured data](https://developers.google.com/search/docs/appearance/structured-data/product-snippet) | Consumer-specific requirements and price handling |
| S5 | [Google Organization structured data](https://developers.google.com/search/docs/appearance/structured-data/organization) | No universal required-property rule |
| S6 | [Agent Skills specification](https://agentskills.io/specification) | Frontmatter, references and portable skill structure |
| S7 | [Google generative Search optimization guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | llms.txt is ignored by Google Search; no universal special-markup requirement |
| S8 | [Google Search documentation updates](https://developers.google.com/search/updates) | FAQ feature ended 7 May 2026; llms.txt clarification |

These primary sources were checked during the preceding review on 12–13 October 2026. They constrain selected semantics; code counterexamples come from the uploaded snapshots.
