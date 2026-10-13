# Historical implementation checkpoints

These were incremental records. Current phase states are in IMPLEMENTATION_STATUS.md.

# Final candidate implementation record

Implementation specification: `final_version_plan.md`. Earlier plans are historical
evidence; the master plan is the accepted scope. Source documents and donor archive
are preserved outside the release package.

## Inputs and context

- Branch: `final_version`, created from freshly fetched `origin/add_md`.
- Destination: `2c6acbd2a2da7e15710a6f66b86181dcba238336`; the fetched branch
  matches the reviewed baseline, so there is no newer source delta.
- Donor ZIP: `Brand-AI-Readiness-Audit-round5-adya_v1.zip`.
- Donor commit: `c48094d60868e2bf9f404094c4b77aabfd9803ca`.
- Donor SHA-256: `7e4e2d6c67c553de94fdd21e556a4a069dc674cbde214d5d7d701889eefd421a`.
- Read the Adobe hackathon ChatGPT chat **Compare Finalist Projects**
  (`6acc8f0b-4de4-83ec-9f7f-403afbed5dea`) via the desktop read-thread tool.
  Its final handoff agrees with the supplied master plan.
- Existing local deletion of `Plan.md`, untracked `aarush's_Plan.md`, supplied
  master plan and ZIP are user changes; no reset or deletion is performed.
- No applicable `AGENTS.md` found in the repository or parent directories.
- Python: CPython 3.14.8. Test dependencies installed only in a temporary venv.

## Phase gates

| Phase | State | Evidence |
| --- | --- | --- |
| 0 baseline | Passed | Isolated reviewed base plus A01/A02 fixture corrections: 1,100 passed in 106.67s |
| 1 input/numeric boundaries | Passed | 59 new production/API/CLI regressions; full candidate suite passes (see verification below) |
| 2 packet 1.1 | Targeted checks passed | Exact emitted bounds, final references, final-content digest and current non-ready exports |
| 3 focused About | Targeted checks passed | Acquired body opening, exact fragments, aliases, unread targets and labeled fallback |
| 4 semantic AG validation | Targeted checks passed | Actual acquired quotations, eligible page scope and explicit search/vision support |
| 5 native/schema | Targeted checks passed | 43 new native/schema controls; 297 combined regressions passed |
| 6 reporting/policy/docs | Passed | Roles/explanations, policy guards, portable version and regenerated example replay |
| 7 integration/release | In progress | Final suite 1,291 passed; frozen host/release/evaluation checks next |

## Defect dispositions

| ID | Files / change | Before | Expected after / verification |
| --- | --- | --- | --- |
| A01 | `tests/test_isolation_and_coverage.py` | Slow start uses default critical timeout | Both intended timeout controls set; accounting assertions retained; full baseline passed |
| A02 | `tests/test_runtime_reliability.py` | Three-argument substitute fails before interrupt | Five-argument worker survives to real SIGINT; JSON/130 assertions retained; full baseline passed |
| A04 | `ingest_agent_findings.py`, `common/json_boundary.py`, report/merge readers | `unanswered=[{}]` raises TypeError | Typed `EnvelopeError`; CLI returns 2 without traceback and preserves all input/output files |
| A11 | Acquisition plus `common/money.py` and native fact consistency | NaN accepted as JSON, then ValueError | Malformed JSON constant diagnosed; unaffected blocks/checks survive; direct synthetic NaN rejected |
| A12 | Same numeric boundaries | 1e999 becomes infinity, then OverflowError | Numeric processing limitation, not syntax defect; unaffected blocks/checks survive |
| A13 | `common/money.py`, native fact consistency | -49→49, 1e3→13, junk→123 | Signed/exponent values retain meaning; junk/bool/nonfinite rejected; separate markup/visible grammar |

All other required register rows remain open. A11/A12/A13 numeric repairs are in
place; Phase 5 must still integrate extraction limitations with absence diagnosis
and repair subject/condition matching. D04's monetary bool control is covered,
but the corrected donor schema port is still pending. Phase 4 must enforce the
remaining AG semantics in addition to the completed A04 type boundary. Passing
metadata or synthetic envelopes do not establish real host execution or numerical
accuracy. The candidate is **not ready for release** while phases 2–7 remain open.

The first local untouched run returned 1,097 passed / 3 failed in 109.61s:
the two expected stale fixtures plus a missing PyYAML test dependency. Installing
PyYAML in the temporary environment resolved the dependency; no runtime dependency
was added. The 1,100-pass baseline used `/tmp/brand-phase0-check`, created with
`git archive` of the exact base commit and only the corrected fixtures copied in.
Timing is suite runtime, not audit runtime or a performance claim.

## Phase 1 verification and next checkpoint

Commands use `/tmp/brand-final-venv/bin/python` on CPython 3.14.8. Temporary test
dependencies are pytest 9.1.1 and PyYAML 6.0.3; default runtime needs neither.

- Controlled before-fix probes against the exact archived base are retained in
  `verification/phase1-before.json`. They reproduce A04 and A11–A13 through
  production functions, rather than asserting that prior code failed from memory.
- Targeted boundary/compatibility run: 164 passed in 3.68s before the final two
  regression additions. Final boundary module: 59 passed in 0.21s.
- Final full suite command: `python -m pytest -q`; result retained in
  `verification/phase1-full-suite.txt`.
- Skill frontmatter and standard-library/no-network renderer dependency checks:
  2 passed in 0.08s after adding the boundary documentation reference.
- `git diff --check` passes.
- Standards checked: RFC 8259 and Python 3.14 JSON documentation. Duplicate keys
  are reported as ambiguity for page JSON-LD; processor range limitations are
  distinguished from malformed constants.

Phase 2 is next: schema 1.1, exact emitted UTF-8 packet bound, final reference
integrity, final-content digest in packet/report/envelope, timing finalized before
hashing, and current-audit non-ready exports. Reconcile that implementation with
Phase 3 focused About passages before treating AG-01 assessments as validated.

Donor reference functions inspected: `_about_link_seen`, `opening_passage`,
`section_passage`, and `build_agent_brief`. Do not reuse the donor's section
selector unchanged: it ignores the fragment. Its opening also combines metadata
with body text, so the port must preserve separate body provenance. The donor's
Organization url/@id requirement and simplistic relative sameAs rule require
correction before the selected schema port.

No release ZIP, real host workflow, holdout accuracy claim, or remote push is
claimed at this checkpoint. Existing source documents and ZIP remain untouched.

## Phases 2–4 checkpoint

Packet and outcome schema 1.1 bind the final exported contents to the saved report.
Packet fitting counts exact UTF-8 serialization, preserves selected About support,
reconciles dropped references and emits a current non-ready marker on failure.
About selection uses acquired body paragraphs and exact fragment identity; an
observed failed or excluded target never becomes an assessed homepage fallback.
Agent merge validates every check before constructing findings, requires acquired
quotes and explicit image comparisons, and limits search advice to its query scope.
Legacy findings cannot clear assessment limits or become confirmed defects.

Targeted production/API/CLI regression command (CPython 3.14.8):
`python -m pytest -q tests/test_final_agent_semantics.py tests/test_round5_agent_handoff.py tests/test_final_packet_contract.py tests/test_final_about_focus.py tests/test_final_input_boundaries.py tests/test_agent_stage_merge.py`
Result: **179 passed in 2.48s**. Full integration, regenerated example replay and
actual host execution remain Phase 7 gates. New schema 1.1 examples will be
generated from the candidate in Phase 6, rather than manually changing digests.

Phase 5 native/schema repairs are now in progress. These targeted results do not
establish independent precision, recall, calibration or host budget enforcement.

## Phase 5 checkpoint

A14 now diagnoses present malformed markup once, retaining usable mixed blocks;
unsupported/ambiguous extraction remains a limitation. A15/D06 comparisons require
actual same-subject facts and supported currency, variant, day, region or offer
conditions. Contact comparisons require named entity or same-street support.
Full cross-page support survives evidence sampling. Confirmed and suspected
findings stay separate through merging/folding.

Corrected donor subset: D02 adds no universal Organization url/@id requirement;
D03 validates calendar/time/offsets while leaving other forms unassessed; D04
excludes monetary booleans; D05 supports external bases, vocabulary, prefixes and
IRI coercion. New validation requires schema.org namespace proof and does not
fetch contexts. Currency format does not assert ISO membership. A11–A13 retain
bounded finite/sign/exponent semantics through native comparisons and rating
conversions. Existing schema/date IDs handle overlapping mechanisms.

Production regressions: `tests/test_final_native_schema.py` **43 passed**;
combined native, schema, handoff, merge and boundary modules **297 passed in
6.74s**. Positive same-product/contact conflicts remain covered, alongside traps.
Adapted old conflict fixtures now state the subject explicitly; the old legacy
AG-04 fixture correctly remains suspected. Full integration remains pending.

## Phase 6 implementation checkpoint

Actions now carry suggested semantic owner roles, merged deterministically and
propagated to top actions/quick wins. Priority explanations reflect the actual
ordering and confidence provenance without a new score. Unknown per-rule assessed
denominators remain unavailable. New fields use the existing safe Markdown renderer.

Release version is 8.4.0 and packet/outcome version 1.1. A16 now uses valid Git
metadata for this checkout or validated RELEASE.json outside Git, with dirty and
unknown states explicit. Five frontmatter names/descriptions satisfy the official
format (description lengths 372–1013; one manifest entrypoint).

Google policy controls remove automatic no-llms publication tasks, keep supplied
artifact defects scoped, and do not infer Google gains from presence. Missing
FAQPage creates no Q&A markup finding. Existing useful Q&A and generic malformed
JSON diagnoses remain. Primary policy sources were checked on 2026-10-13; the
llms.txt proposal also confirms file lists and H2 sections are optional.

Targeted reporting/policy/compatibility command: 262 passed in 10.17s. The old
schema 1.0 examples are deliberately not hand-edited; regeneration from this
candidate, complete suite and host workflow are the next required checks.

## Phase 7 integration and runtime freeze

Final integrated command: `python -m pytest -q`; **1,291 passed in 110.10s**.
Result: `verification/phase7-full-suite.txt`. This supersedes intermediate full
runs whose remaining failures were old optional-artifact expectations, catalogue
metadata assumptions and a style assertion incorrectly applied to source evidence.
No timeout, interrupt, source-binding or private-target assertion was weakened.

Final review additionally rejects case-altered or artificially stitched quotes,
requires lossless retained JSON float values (other valid precision is a processor
limitation), applies explicit price/contact relations, and limits absolute agent
deadlines to the declared maximum 55 seconds within remaining workflow time.
An explicitly indexed llms-full companion reuses its existing bounded probe;
unrequested optional companions cannot become website defects.

The development Python.org host rehearsal took 48.421 seconds to merge, assessed
AG-01 from the actual read packet, and explicitly skipped search/vision. It
revealed the absolute-deadline defect, so it is development evidence rather than
the final frozen rehearsal. The current examples were generated by that host
workflow; final frozen examples will replace them without editing hashes/passes.

Before-fix production probes for A14/A15 are retained in
`verification/phase5-before.json` against the exact archived base. Official skill
metadata/reference validation is recorded in `verification/skills-format.json`.
`git diff --check` and compilation checks pass.

All engineering defect dispositions are implemented and covered. Phase 7 still
requires frozen host rehearsals, extracted-package verification and a quality
review record. Independent human labels and an actual presentation recording
cannot be replaced with synthetic outcomes or test counts. No independent
precision, calibration, business uplift or complete-plan claim is made yet.

## Final native profile correction

Review of the first frozen six-site batch found that native off-site profile
advice used its three-page display sample as affected reach. All supported pages
now survive in JSON; broken/mismatched profile groups also retain full source
reach. The native profile interpreter now resolves supported external-base and
`@id` forms, skips unsupported/non-HTTP forms with limitations, and filters names
before deduplication so structured values cannot cause an unhashable-member crash.
Regression controls cover twelve supported pages and actual resolved profile URLs.

Final candidate suite after this correction: **1,293 passed in 109.19s**;
`verification/phase7-final-candidate-suite.txt`. No confidence rescore was applied.
The first frozen review set is now development evidence, not untouched holdout.
A fresh candidate, new review set and final rehearsals will retain their own hashes.

The packaging review also restored the three documented public localhost TLS test
fixtures to an explicit allowlist; unrelated private keys remain excluded. The
extracted first-frozen package passed **1,287 tests, one skipped build-tool module**
in 110.57s, including the real TLS controls. The final extraction is checked again.

## Fastly interstitial correction and branch synchronization (2026-10-13)

Committed local results/reference ignores (9506fd6), verified and fixed Fastly
interstitial classification with 43 new regressions (df925c5), and merged the
new add_md test-only correction 536bee6 into final_version (f321bf4). The latter
retains all runtime bytes and test assertions; its three module tests passed.
The final committed-snapshot archive passes 1,340 tests, with one intentional
build-tool module skip, after the runtime checkout passed all 1,344 tests.
Actual frozen-runtime PyPI execution analyzes one real page, records two Fastly
challenges and stops; no challenged page contributes to affected finding scope.
Evidence, original-patch counterexamples, prior release identity and remaining
human/laptop verification steps are retained in fastly-client-challenge/ and
FINAL_DEMO_CHECKLIST.md. The historical 49-screen/eight-finding totals cannot be
independently confirmed without the original report.
