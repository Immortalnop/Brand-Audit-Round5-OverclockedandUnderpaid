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
| 2 packet 1.1 | Pending | Bounds, references, final-content digest |
| 3 focused About | Pending | Corrected selective donor port |
| 4 semantic AG validation | Pending | Acquired support and affected scope |
| 5 native/schema | Pending | Extraction states, money, facts, limited context semantics |
| 6 reporting/policy/docs | Pending | Roles, explanations, Google policy, portable version |
| 7 integration/release | Pending | Full suite, host workflow, extraction and evaluation limits |

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
