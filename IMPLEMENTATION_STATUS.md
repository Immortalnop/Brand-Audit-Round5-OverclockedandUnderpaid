# Final candidate status

Latest compatibility repair: stdout JSON again escapes Unicode for strict legacy
console encodings. Parsed report values and UTF-8 file output are unchanged. The
updated complete suite passed **1,301 tests in 126.06s**; see
[stdout verification](verification/stdout-compatibility/record.json). This
supersedes the original runtime's stdout compatibility claim. Historical freeze,
host/evaluation records and original package evidence below remain dated evidence.
The independent human/presentation gates remain pending.

The engineering changes in required Phases 0–6 are implemented on `final_version`.
Phase 7 regression, package execution and actual host rehearsals are verified.
Independent human accuracy review and the intended-laptop presentation recording
remain pending; the entire plan is therefore not certified complete.

The accepted specification is the user-supplied `final_version_plan.md`. The Adobe
hackathon ChatGPT chat **Compare Finalist Projects**
(`6acc8f0b-4de4-83ec-9f7f-403afbed5dea`) was read before implementation. Historical
plans supply context; they do not replace the user's request or master plan.

## Source and branch

- `final_version` was created from freshly fetched `origin/add_md`, commit
  `2c6acbd2a2da7e15710a6f66b86181dcba238336`. It retains that complete base.
- Adya's ZIP commit is `c48094d60868e2bf9f404094c4b77aabfd9803ca`; archive SHA-256
  is `7e4e2d6c67c553de94fdd21e556a4a069dc674cbde214d5d7d701889eefd421a`.
- Source ZIP and supplied plans remain untouched and outside the package. The
  pre-existing local deletion of `Plan.md` is preserved. No source branch reset
  or remote push was performed.
- Runtime/rule freeze: `ae61edfd60b47b39fc442ec392845de95696e8d5`, version 8.4.0;
  packet/outcome schema 1.1. Later release-evidence commits change documentation,
  recorded evidence and examples only. The final release record proves file identity.
- CPython 3.14.8 on Linux; temporary test venv has pytest 9.1.1 and PyYAML 6.0.3.
  The default runtime remains standard-library only. No applicable AGENTS.md found.

## Phase gates

| Phase | Current state | Evidence |
| --- | --- | --- |
| 0 baseline | Passed | Exact archived base plus corrected timeout/interrupt fixtures: 1,100 passed in 106.67s |
| 1 boundaries | Passed | Bounded typed input, strict JSON, atomic rejection, finite/lossless numeric handling |
| 2 packet 1.1 | Passed | Exact emitted UTF-8 bound, reconciled E/C/I references, final-content digest and current non-ready marker |
| 3 About | Passed | Separate acquired body opening, exact case-sensitive fragments, failed/excluded target stays unassessed |
| 4 AG semantics | Passed | Acquired quotes, explicit eligible comparison scope, bounded search support, conservative legacy handling |
| 5 native/schema | Passed | Explicit same-subject/condition facts; limited context/base/value interpretation; full profile reach |
| 6 reports/policy | Passed | Suggested roles, actual priority reasons, Google scope, portable version, valid five-skill structure |
| 7 regressions/package/host | Verified engineering checks | 1,293 checkout tests; 1,289 extracted tests plus one expected skipped build-tool module; actual final host traces |
| 7 independent evaluation | Human review pending | Six-site frozen review batch; 64 findings; agent triage and all source artifacts retained |
| 7 laptop/presentation | Unverified | Three chosen local-host workflow runs; intended laptop identity and complete video not established |

Every A01–A16, D01–D06 and P01 disposition and its production regression family
is recorded in [DEFECT_DISPOSITIONS.md](verification/DEFECT_DISPOSITIONS.md).
Detailed historical checkpoints are retained in
[IMPLEMENTATION_HISTORY.md](verification/IMPLEMENTATION_HISTORY.md), clearly marked historical.

## Implementation and verification

Aarush's immutable acquisition, safe transport, graph, deadline/budget accounting,
scoring and report hierarchy remain the base. Small shared helpers handle strict
JSON/numbers, packet contracts, AG semantics and limited structured values.
Adya's focused observations, corrected schema subset and role metadata were
adapted into those contracts. There is no donor scoring/transport replacement,
model server, dashboard, website modification or Adobe SDK.

Final complete command: `python -m pytest -q`; **1,293 passed in 109.19s**,
[checkout log](verification/phase7-final-candidate-suite.txt). The frozen extracted
runtime passed **1,289 tests, one skipped build-tool module in 110.08s**,
[extracted log](verification/phase7-extracted-suite.txt). The build tool is excluded
by the intended runtime allowlist; its four tests pass in the checkout. Timeout,
real SIGINT, TLS/DNS/robots/private-target, source and accounting controls remain.
Suite runtime is not audit runtime. Final example/policy/packaging/renderer/metadata asset checks: **89 passed
in 8.55s**, [asset log](verification/phase7-final-assets.txt). No test was added just to increase the count.

Before-fix production probes against the pinned base remain in
[phase1-before.json](verification/phase1-before.json) and
[phase5-before.json](verification/phase5-before.json). Positive acquired conflicts,
complete focused passages, valid base/coercion, and twelve-page reach controls
remain. The fixture expected-check scorer detects 21/21 assertions; that set also
contains opportunities and is not independent broad defect recall.

Official five-skill frontmatter/reference checks are in
[skills-format.json](verification/skills-format.json). The package includes public
localhost TLS fixtures needed by safety tests; credentials, caches, databases,
user plans, donor ZIP, verification runs and build tools are excluded.

## Actual host workflow

The final extracted runtime was invoked once per audit, its actual packet was
read, source-backed AG-01 observations were written, and the saved base was merged
once and rendered. Search, vision and rendering were explicitly unassessed in
these runs. Merge/render made zero observed requests; the acquisition-call trace
has one call per run. Direct requests, including redirects, are recorded by host
and path. The controlled failed-About server independently records HTTP 503.

[Final rehearsal summary](verification/rehearsals/final-summary.json) retains all
four public runs and the controlled failed-About case. The three chosen Python.org
runs took 38.846, 34.376 and 32.363 seconds from entrypoint invocation through final
Markdown (p50 34.376; nearest-rank p95 38.846, n=3). Across all four public runs,
p50 is 36.611 and nearest-rank p95 is 80.047 seconds. The Django target's host stage
exceeded the 55-second allowance; that run is retained. These small observations
are not a general performance claim.

The code enforces the core worker stop and reports the host deadline within the
remaining 270-second target; the host allowance is advisory here. Earlier whole
user-request start and intended laptop identity were not instrumented. Command
records are execution evidence, not a screen recording. Canonical examples are
byte-for-byte copies of `final-4`, including real hashes and outcomes.

## Accuracy and remaining gates

The fresh six-site batch has **five completed sites and one insufficient-evidence
site**, all retained in its denominator. It emitted **64 findings: 11 defects and
53 opportunities, eight medium and 56 low; no high/critical**. No positive
high-severity precision denominator exists. Runtime, scorer, manifests, capabilities,
network ledgers, source hashes and failure states are frozen in
[review-set](verification/review-set/manifest.json).

All 64 rows have separate agent triage notes against saved reports/observations.
The [human review CSV](verification/review-set/findings-review.csv) retains blank
labels for support, scope, status, severity and action applicability. Triage flags
include intentional noindex on an error page, irrelevant commercial-directory
advice, uniform lastmod dates that do not prove generation time, and address
ownership before publishing generated snippets. Heuristic opportunity usefulness
and confirmed raw-parser observations need independent review. The dataset was
not used for tuning; independent prior holdout history is unavailable.

The first evaluated batch that led to the native profile repair is retained under
`verification/development-review-set` and is development data. No independent
precision, ECE, ranking/citation/conversion uplift, calibrated probability, or
complete-plan claim is made. Targets remain goals. The twelve requested quality
dimensions and review instructions are in
[QUALITY_REVIEW.md](verification/QUALITY_REVIEW.md).

To close the remaining Phase 7 gates, a person must review the 64 labelled-later
rows and disagreements, confirm the intended laptop and capture the complete
frozen workflow/presentation recording. Presentation budgets (eight-minute target,
ten-minute stop, seven presented slides, five-minute Q&A) are separate from audit
and host-stage budgets. No Adobe integration or measured business uplift is claimed.

## Release artifact

The candidate ZIP is `dist/brand-ai-readiness-audit-8.4.0.zip`, built from clean
committed snapshot `f144c1888e3a3482aa61f9ec375033599eb3a7cf`. It is 745,185 bytes
and contains 166 intended files plus RELEASE.json. SHA-256:
`eea21f7cd6823fb19cb832bf01e7ee7c925125a61c6bb3d9fb01c94b7c7ac979`.

All 137 Python files match the full-tested ae61edf runtime. The six changed assets
are the five actual final examples and one validation reference. Final ZIP
extraction, portable version and those changed assets were checked separately:
**85 passed, one expected build-tool module skipped in 9.59s**. Packaging intentionally
excludes the build tool. The runtime full-suite results above apply to identical
Python/test files; no additional full run is claimed after documentation/example
changes. The complete metadata and individual packaged file hashes are in
[RELEASE_VERIFICATION.json](verification/RELEASE_VERIFICATION.json) and
[release-files-sha256.json](verification/release-files-sha256.json).

A later evidence-only commit can have a different HEAD; the ZIP accurately names
its own committed source snapshot. The package is an engineering candidate for
review, not certification of pending independent human or presentation gates.
