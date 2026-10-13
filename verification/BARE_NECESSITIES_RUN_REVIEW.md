# Bare Necessities Claude run: verification and proposed corrections

Reviewed on 2026-10-13. This is an analysis record, not a corrected audit. The supplied reports and evidence remain unchanged. Runtime code, tests, skills and `FINAL_AUDIT_PROMPT.txt` were not edited. The replay launch now requests `--model claude-opus-5-5`; its accompanying model-selection wording was updated. Actual session metadata fields remain blank.

The pipeline completed and its saved outputs are internally consistent, but this run is **not sufficient to certify finding accuracy or complete agent coverage**. Two findings have clear context problems, a third reproduces a false byline, and several template-based findings need narrower interpretation. Passing contract tests does not settle these semantic issues.

## What was supplied and verified

- Source: `/home/dionysus/Downloads/out_barenecessities.zip`, 87,230 bytes; ten audit files, excluding macOS archive metadata. ZIP CRC verification passed. All ten extracted files still match the original archive bytes.
- The pasted response was reviewed against the JSON, Markdown, envelope, notes and both logs. Empty `run-audit.stdout` and `merge.stdout` are consistent with using `--out`; progress and save confirmations are in the logs.
- Audit ID: `a611a72bba10476bb7edfb9a18f1736c`. Reported runtime: `8.4.0+unknown`. A source ZIP without Git or RELEASE.json can legitimately report `+unknown`.
- All four JSON files pass the production JSON boundary reader. Both reports pass shape and strict catalog validation without alterations. The evidence packet's content digest verifies, and the report, packet and envelope bindings agree.
- The production envelope validator accepts exactly one finding, AG-01, and five `not_assessed` outcomes. No outcome reports an error.
- Replaying the merge with network operations blocked reproduces the final JSON exactly except for the new merge timestamp and elapsed-time record. Re-rendering the supplied final JSON reproduces the Markdown byte for byte. All 21 native findings are preserved; one agent finding is added, none folded.
- Base: 21 findings, 3 medium, 18 low, 17 improvements, 18 recommendations. Final: 22 findings, 4 medium, 18 low, 18 improvements, 19 recommendations. Neither report has high or critical findings. The final four defect classifications are F-001/F-003/F-004/F-022. Recommendations comprise 18 improvement references and one explicitly advisory off-site baseline; defect actions remain on their findings.
- Relevant existing tests: **212 passed in 3.66 seconds**, using the existing temporary test environment. The restricted attempt could not create localhost fixture sockets; the permitted rerun passed. No test dependencies were installed and no tests were added or edited.

The ZIP does not include the original full acquisition snapshot, full Claude tool transcript, model/harness metadata, package-before/after evidence, or a separate renderer exit log. Its reported command exit statuses cannot all be independently reconstructed: the audit exit 0 is logged, successful merge is supported by the saved output and replay, and rendering is verified by exact content reproduction. Claims about every original source page, tool execution or package immutability therefore have limits.

Fresh verification fetched robots.txt and four public pages—About, homepage, book product and Press—with the engine transport and its normal audit User-Agent, verified TLS and robots checks. Each answered HTTP 200 without truncation. These are **current corroborating sources, not replacement original-run evidence**. Local parser and in-memory attribution probes were run without changing source files or reports. No browser visibility measurement was performed.

## The deadline sequence

Times below are UTC on 2026-10-13. Search/save details come from the agent's notes, not an independently supplied tool transcript.

| Event | Time | Meaning |
| --- | --- | --- |
| Engine session starts | 17:04:02.094 | Start of the engine's clock, not necessarily the user's complete Claude request |
| Core finishes | Approximately 17:05:02.349; wrapper logs 17:05:02.388 | Core elapsed 60.255 seconds |
| First AG-01 envelope save, per notes | 17:05:21 | Roughly 19 seconds of the host allowance already used |
| AG-02 WebSearch, per notes | Approximately 17:05:22–31 | Nine listed results, with counts not fully classified and saved |
| Independent WebFetch returns, per notes | 17:05:49 | Only about 8.35 seconds left |
| Host-stage deadline | 17:05:57.349 | Core finish plus the maximum 55-second host allowance |
| Notes finalized, per notes | 17:06:08.245 | Approximately 10.90 seconds after the host deadline |
| Merge | 17:06:12.951 | Core-to-merge host/finalization interval 70.602 seconds; engine-start-to-merge 130.857 seconds |
| Overall engine workflow target | 17:08:32.094 | 270 seconds from engine start |

The code uses the equivalent of:

`agent_deadline = min(engine_start + 270 - 15, core_finish + 55)`

At core completion, approximately 194.745 seconds remained before the overall finalization reserve, but the separate 55-second ceiling applied. Approximately 139.745 seconds were therefore unavailable to host assessments under the current contract. This is deliberate policy in `common/constants.py`, `run_audit.timing_plan`, the agent skill and the final plan; it is not a failed crawl or accidental 55-second core timeout.

The actual host interval exceeded that deadline by 15.602 seconds. The merge records `within_workflow_target=true` **and** `within_agent_deadline=false`. A late merge is accepted and disclosed; it does not automatically fabricate passes or erase saved outcomes. The 70.602-second figure also includes envelope/notes writing and local finalization up to the merge; it is not purely search time.

The claim “whole request about 131 seconds” is too broad. The verified number covers engine start through merge. Contract reading before the engine, Markdown rendering afterward, and the final explanation are outside that measured interval. Full user-request-to-final-output time remains unverified.

## Agent outcomes and their causes

| Check | Recorded result | Review |
| --- | --- | --- |
| AG-01 About concreteness | Finding | Structurally valid but selected the wrong content region. F-002 should not be presented as a supported criticism of the About opening. |
| AG-02 Independent mentions | Not assessed | Search and one external page inspection were attempted. Required query counts/identity/source evidence were not completed and saved within the allowance. Do not change it to pass retrospectively. |
| AG-03 Contradiction | Not assessed | No search/inspection for this check was recorded before the cutoff. This says nothing about whether the brand has inaccurate claims. |
| AG-04 Image-only facts | Not assessed | No full image was viewed. There is also an independent packet association defect: all four I candidates have empty `page_evidence_ids`. None can support the required exported-page comparison. |
| AG-05 Namesakes | Not assessed | No namesake search/inspection was recorded. Own social profiles must not be substituted for competitors. |
| AG-06 Review/profile opportunities | Not assessed | No applicable platform-specific queries were recorded. No platform absence can be inferred. |

The summary's opening statement that all five skips resulted from the deadline is inaccurate for AG-04. Its later table correctly describes the missing image view. Likewise, “none of the checks passed” should explicitly mean **none of the six AG checks passed**: the JSON retains 14 native positive observations.

The declared `vision=false` establishes that no visual assessment was performed; it does not prove Claude or this tool configuration is incapable of vision. Claude Code's Read tool supports image viewing, but the run needs an actual full local image and a valid compared-page association. WebFetch is a lossy text extraction tool, not proof that an image was seen. [Claude Code tools reference](https://code.claude.com/docs/en/tools-reference)

## Reproduced accuracy problems

### 1. AG-01/F-002: announcement captions became the About opening

The original E002 export already contains the brand's name, its personal-care category and substantive introductory copy. Its selected focus instead consists of “Certified B Corporation Our Annual Impact Report”. This contradicts the focus's description as an eligible About body opening.

Current HTML and the unchanged parser reproduce that exact focus. Both paragraphs are inside an announcement-bar dropdown before `<main>`, with class `wt-announcement-bar__dropdown-heading`. The genuine introductory paragraph is inside `<main id="root">`. The parser excludes standard header/nav/footer tags, but this custom announcement component falls outside those exclusions. It takes the first two qualifying paragraphs, and `opening_complete=true` certifies paragraph retention/completion rather than correct body-region selection.

The envelope validator correctly checks that Claude quoted the selected focus. It cannot make a wrongly selected focus semantically correct. The prompt's “assess exactly focus” instruction makes the host follow that bad selection. This needs a parser/exporter correction plus a prompt guard; a model upgrade alone will not repair it.

### 2. F-003: a publication date was classified as a pricing/offer date

The book page's date is its publication date, not an offer expiry or price-validity date. The original E008 export identifies publication in 2021; the current product specification explicitly labels the reported day as publication. The unchanged extractor classifies it as `commercial` solely because the page type is `product`.

Thus this is a reproduced date-category false positive. Keep the publication date. The supplied evidence supports no conclusion that the displayed price is stale. The engine's separate offer-expiry coverage found **zero expired-offer pages**, which should not be conflated with the generic old-date heuristic. [Book product specifications](https://barenecessities.in/products/bare-necessities-how-to-live-a-zero-waste-life-book)

### 3. F-007: navigation text was treated as a person's byline

On the current Press page, the unchanged classifier assigns `article` to `/pages/press`. The byline regex then extracts **“Shop Body Care Soap”** from navigation beginning “Shop by …”, and reproduces the reported missing-Article-author-property warning. The page is a founder/brand story, not proven to be an authored article merely by its URL.

This is a reproduced classifier/byline-context error, with the original full Press snapshot unavailable. Article applicability and byline recognition both need correction. Broadly excluding all press pages would also be wrong: real press releases/articles must remain assessable.

### 4. F-001/F-011/F-017: cart templates inflate live-page interpretations

The nameless `/cart` link is `cart-notification-button`, inside a notification component. The delivered HTML includes a stylesheet rule hiding `.cart-notification`; scripts may later populate and display it. It is not the named header cart control described by a simple “Open cart” fix.

The two reported modal dialogs are the cart notification and cart drawer. Their `aria-modal=true` identifies modal semantics, not proof that they obstruct arrival. Current homepage and Press heading jumps arise from the cart drawer's final H4 account prompt, outside the main content outline.

An attribution experiment removed only those two cart template blocks **in memory**, then reran the unchanged parser:

| Current source | Unnamed controls, actual → without templates | Modal dialogs | Heading jumps |
| --- | --- | --- | --- |
| Homepage | 4 → 3 | 2 → 0 | 1 → 0 |
| About | 1 → 0 | 2 → 0 | 0 → 0 |
| Book | 1 → 0 | 2 → 0 | 0 → 0 |
| Press | 1 → 0 | 2 → 0 | 1 → 0 |

This establishes the source of the signals, not a complete rendered accessibility test. The homepage's three other unnamed links remain, so it would be wrong to discard the entire accessibility finding. Its claimed 49-page prevalence and confirmed live-control interpretation need review. F-011 is reproduced as a template-outline issue on two of its five reported pages; the remaining three were not freshly fetched.

Static inspection must distinguish a displayed modal, a known hidden component, and a component whose state is unknown. The report already calls overlays suspected, but still describes their existence as a blocking signal. [W3C modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

### 5. F-004/F-022: old page-update timestamps do not prove stale facts

F-004's evidence is a contact page sitemap lastmod from 2022. F-022 similarly uses old lastmod values on recipes, stores, headquarters, campaign and other pages. These establish an old declared page update; they do not identify an incorrect address, phone number, operational deadline or other outdated fact.

The code maps update-date categories from page type and defaults other pages to operational. It then labels old timestamps as suspected defects. The action catalog is more cautious, but these still become top actions and, for contact, a medium quick win. They should remain review signals unless actual current-fact evidence supports a defect. Historical recipes and campaign records need particular protection. Changing valid lastmod dates merely to look recent is inappropriate: they should reflect real significant updates. [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)

## Review of all 22 findings

“Static support” means the report contains plausible bounded HTML evidence, not that all 49 original pages were independently replayed. The original full snapshot is absent.

| ID | Check | Assessment |
| --- | --- | --- |
| F-001 | Accessible control names | Partly supported: three homepage links remain unnamed in fresh probes; repeated cart-template signal overstates live scope. Needs state-aware validation. |
| F-002 | About concreteness | Wrong focus region; do not rely on this finding. |
| F-003 | Old commercial date | Reproduced publication-date misclassification. |
| F-004 | Old contact date | Old lastmod only; does not establish stale contact details. |
| F-005 | Media schema | Plausible optional markup gap. Verify content-bearing media, applicability and current schema on each affected page before asserting all 21. |
| F-006 | Media transcript | Plausible absence of an exported page transcript. Embedded-player captions are explicitly unchecked; do not imply every video lacks captions or requires transcription irrespective of content. |
| F-007 | Author credentials | Reproduced navigation-as-byline and article-applicability errors. |
| F-008 | Meta descriptions | Bounded static opportunity; no ranking penalty proved. Twelve-page count not independently recomputed from original HTML. |
| F-009 | Contact markup | Plausible optional structured-data opportunity; visible contact information already exists. |
| F-010 | Responsive images | Plausible static absence of srcset/picture on selected images. Does not establish wasted transfer bytes or failure to resize through CSS/server delivery. |
| F-011 | Heading hierarchy | Two current reproductions are caused by the cart drawer's H4, not the main outline. Full five-page claim needs review. Evidence lists only the first 20 levels on the homepage, omitting the offending jump. |
| F-012 | CLS risk | Correctly labeled a markup estimate. CSS may reserve space without width/height attributes; field/browser CLS remains unknown. |
| F-013 | Text/markup ratio | Static measurement and inspection suggestion, explicitly not a ranking metric. No proven UX or crawler harm. |
| F-014 | Title-length outliers | Heuristic review opportunity, not a mandatory character quota or measured truncation. |
| F-015 | Image alternatives | Plausible static gap. Several examples are video preview thumbnails; informative/decorative/player context needs manual review. |
| F-016 | H1/orientation | Missing H1 is an observable markup fact. About has a descriptive H2 hero; “no immediate orientation” is stronger than that evidence warrants. Scope merged wording accordingly. |
| F-017 | Arrival overlay | Two cart components detected; arrival blocking not measured and notification is hidden by delivered CSS. Treat as a state/visibility gap. |
| F-018 | Breadcrumb markup | Plausible optional BreadcrumbList opportunity; does not mean visible navigation is missing. |
| F-019 | HTML size | Retained response size is a real static observation. Compression, total assets and perceived speed are not measured by it. |
| F-020 | Rating/step exports | Plausible optional structured-export opportunity. Actual ratings/consumer requirements must be checked; no guaranteed search uplift. |
| F-021 | Location markup | Plausible optional structured-location opportunity. It does not imply the visible address is absent or incorrect. Generated snippet values/placeholders need operator verification. |
| F-022 | Old operational dates | Timestamp-only review signal; not evidence that recipes, campaigns or current operational facts are wrong. |

The 14 native positives cover crawl permission, checked AI crawler access, sitemap, llms.txt, HTTPS, HTTP status, titles, language, canonicals, indexing directives, parsable structured data, raw HTML content, mobile viewport and onward links. Their scope is the checked sample and declarations, not guaranteed live search indexing or universal crawler access.

## Other coverage limits and packet gaps

- **50 successful page fetches, 49 analyzed, 282 discovered, 3/11 sections.** The 232 unattempted URLs and three-section sample explain the low representativeness score. The code counts successful fetches separately from responses with analyzable content; these files do not identify the exact fiftieth URL or its exclusion. This is not evidence that a redirect fix regressed. There were zero recorded redirect duplicates, aliases or followed redirects in this run.
- **Confidence 0.27 is a heuristic coverage rating, not 27% accuracy.** Its execution component rates core completion; the merge does not lower it for incomplete AG work. Read agent coverage and individual finding confidence separately.
- **No challenge/robots/TLS failure occurred in the core.** No analyzed pages were partial or timed out. Auxiliary truncated-response counters need not imply page truncation: media probes intentionally read only prefixes.
- Native search was unconfigured, while Claude host search was available. These are separate capabilities. One native external request was a profile/robots verification, not evidence that native search ran. Host calls are explicitly outside the engine's request ledger.
- No headless rendering or PageSpeed key: static heuristics do not establish measured CWV or on-screen behavior. One linked profile remained unverified, not broken. Missing Organization markup prevented relevant identity/knowledge-graph checks; it did not prove the brand lacks a real-world entity.
- All eight exported E pages are text-truncated at the shared 4,000-character allowance, despite the core having fully read its 49 eligible pages. Large repeated navigation occupies much of that allowance. Full-page absence cannot be established from these exports.
- All four I candidates have **zero exported associated E references**. Image viewing alone cannot make AG-04 eligible under the current validator. Candidate selection and page selection are independent and need a joint usable evidence chain.
- All twelve C claims are `name` values: Product, Brand and ten FAQ Questions, from one product page. This consumes the claim budget with identifiers/questions rather than diverse checkable assertions. AG-03 can still use an actual E quote, but the current selection under-serves corroboration.
- No external-source inspection or count was saved as an assessed AG-02 record. The notes preserve partial attempts, appropriately without transforming nine listed results into nine verified independent mentions.

## Proposed approach before another final rehearsal

1. **Correct evidence selection and interpretation first.** Isolate AG-01's genuine main-body opening while preserving provenance, complete-opening limits and explicit fallbacks. Make page publication/history dates distinct from current pricing/expiry facts. Reclassify timestamp-only freshness signals as review opportunities unless substantive stale-fact evidence exists. Correct article applicability/byline extraction and component-state interpretation. Preserve positive cases for actual unnamed active controls, displayed blocking modals, bad main-content outlines, genuine stale offers and real article bylines.
2. **Make packet evidence usable without another crawl.** Coordinate page/claim/image selection, within the existing bounded export: include an acquired parent E for selected I candidates, expose useful comparison scope, and prioritize material/diverse assertions over repeated Question.name values. Preserve the snapshot and binding contract; regenerate fresh packets after exporter changes. Do not retrofit new evidence into this saved run.
3. **Streamline the host stage within 55 seconds.** Prepare contract understanding before acquisition. Immediately after core completion, use one local operation to parse/validate base metadata, obtain the UTC clock and expose the compact packet facts needed for AG work. Defer full report narration until after the host stage. Initialize the envelope immediately, save query observations as they happen, and reserve concrete time for outcome writes/merge rather than spending nearly the whole allowance on one search/fetch. Native Claude WebSearch/WebFetch latency has no proven universal cancellation guarantee; a clock check alone cannot stop an already running tool.
4. **Provide an explicit bounded full-image workflow when support is usable.** Fetch only an authorized packet-listed image into out/, with MIME/size/robots/URL/deadline checks and separate host-call accounting; actually Read the full image. Header bytes and WebFetch text must remain insufficient. If no supported parent comparison is exported, record that precise evidence limit instead of spending time fetching an unusable image. Do not force an AG-04 pass when exported text is truncated.
5. **Update the prompt after code corrections are reviewed.** Add a wrong-focus guard producing `not_assessed` rather than an unsupported finding; never silently substitute a new AG-01 passage under the old contract. Add explicit I-to-E eligibility checks, compact stage preparation, bounded external-call planning, immediate observation saves and a deadline stop rule with a measured finalization reserve. In the response, distinguish core completion, AG coverage, host lateness and true full-request time. Preserve default 50 pages, one acquisition, one merge, schema/binding checks, honest skips and capability disclosures. Do not load remembered brand facts or weaken search/source evidence requirements to increase assessment counts.
6. **Treat a longer agent allowance as a separate design decision if still necessary.** Current plan section 7 and the skills expressly require at most 55 seconds. Changing only the prompt or pretending the remaining 270-second time is available would conflict with them. Any new budget must consistently update plan, constants, timing metadata, skills, tests and replay, reserve finalization, and prove end-to-end timing. No such change is implemented or approved by this analysis. A six-check guarantee is not credible when source tools or evidence can be unavailable.

## Verification gates for proposed fixes

- Add regressions that fail on the current patterns: custom announcement dropdown before main; valid About prose; a product's book publication date beside a current price; historical campaign/recipe updates; “Shop by …” navigation on a non-article press page; stylesheet-hidden/inactive cart templates; main outline versus drawer headings; and I candidates whose acquired parent pages would otherwise be omitted.
- Pair each negative regression with real positive cases. Do not globally suppress commercial dates, press pages, dialogs, icons or namesakes. Keep the existing AG semantic/binding adversarial tests passing.
- Check generated packet size, truncation, exact focus provenance and I/C parent references. Truncated evidence must remain unable to certify full-page absence. Old or tampered packets/envelopes must still reject atomically.
- Rerun relevant tests, then the full repository suite after runtime changes. Existing green tests here verify mechanics, not these newly identified patterns.
- Rehearse on the actual Claude laptop with default 50-page acquisition and the selected Opus model. Capture true request start, each external call, envelope saves, merge/render completion, actual model/version/effort and optional capabilities. Record all six outcomes, including honest NA/error cases, without predetermining the number of findings.
- Review every emitted finding against acquired context. Compare each new run with its own snapshot; changing live-site results are not regressions solely because counts differ. Check supported pages and selected actions, especially freshness/accessibility priorities.
- Retain raw tool traces and permitted evidence for independent review. Do not turn this run's partial AG attempts into retroactive passes or edit its original outputs to look complete.

## Replay model edit

The launch command now includes `--model claude-opus-5-5`. Anthropic documents that full model ID and requires Claude Code **v2.1.280 or later** for Opus 5.5. Confirm the actual selected model on the demo account; the supplied output ZIP does not identify its prior model. The remaining launch flags and embedded prompt are unchanged, and the embedded prompt still equals the standalone file. [Model configuration](https://code.claude.com/docs/en/model-config), [CLI reference](https://code.claude.com/docs/en/cli-reference)

The external replay document is updated; the already supplied/downloaded ZIP has not been rewritten. Use the updated replay launch when starting the next session. This review is not a new demo run, release certification or implemented bug fix.
