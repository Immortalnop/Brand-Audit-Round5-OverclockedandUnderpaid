# Demo revision 8.4.1 verification

The October 14 scheduling request supersedes the uploaded plan's internal
55-second AG allowance. The uploaded source plan is preserved. The ordinary
50-page cap and 270-second standalone worker ceiling remain. The Claude prompt
captures a host clock before contract reading, narrows acquisition to the
remaining 270-second target, reserves 60 seconds for finalization and gives AG
work up to 180 seconds from the remaining allowance. Native read calls may run
in small independent batches; saves and the single merge remain sequential.

The complete checkout suite passed: **1,377 tests in 116.34 seconds**. The first
full attempt found optional-argument compatibility failures and outdated
calibration expectations; these were corrected before the passing run. Regression
coverage includes actual opening text, short vague openings, hidden/unknown/open
widgets, real heading skips, genuine bylines, legitimate organization authors,
publication dates versus expiry, optional location markup, packet/image parent
selection, integrity checks, expired/future clocks, Unicode output, helper limits,
exclusive outputs and byte-identical prompt embedding.

Fresh default live engine runs completed on Tartine (26 pages, 23.840 seconds
through local merge/render) and Bare Necessities (49 pages, 50.025 seconds).
Both exported assessable complete openings and two image candidates with E
parents. All six AG outcomes were deliberately not_assessed during these native
verification runs; no Claude execution or search/vision assessment is claimed.
Their base reports and packets remained byte-identical through the merge/render
path, and native summary counts were unchanged. See native-live-runs.json for
actual timestamps, execution status, version and scope. These are observations
from two runs, not a general benchmark or an accuracy certification.

Claude Code is unavailable on this execution host. The intended-laptop Opus 5.5
trace must verify actual parallel overlap, external source evidence, image Read,
full prompt-to-reply duration and behavior on slow/blocked sources. Clock guards
cannot cancel arbitrary Claude tools; late results must remain disclosed.
Independent finding review and presentation recording are also still pending.

Original uploads, historical results and the user's fastmail.json/tartarine.json
are preserved. No add_md changes were pulled into this revision.

The deliverable archive was built from committed source 72f9b35 and extracted
outside the checkout. Its full distributed suite passed **1,373 tests, with one
expected module skip** for excluded build tooling, in 123.19 seconds. Seven
checkout packaging/prompt tests also passed after adding replay to the allowlist.
The archive is 803,020 bytes, has the expected folder root, portable RELEASE.json
provenance, and the exact canonical prompt. CRC verification passed. Data stores,
user result files, caches and uploaded planning/source archives are excluded by
the release allowlist without deleting them from the workspace. See package.json
and extracted-suite.txt. No manual archive hash check is added to the replay.
