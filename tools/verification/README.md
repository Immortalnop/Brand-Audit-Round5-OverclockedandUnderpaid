# Verification utilities

These opt-in developer tools are separate from the audit entrypoint. They are
excluded from the runtime ZIP and never run automatically with the plugin.

| Utility | Purpose and inputs |
| --- | --- |
| `capture_entrypoint.py` | Wraps the normal bounded entrypoint, recording HTTP request paths and immutable acquired observations. Set `BRAND_CANDIDATE_ROOT` to the candidate package and `BRAND_RUN_DIR` to a fresh writable output directory; pass normal audit CLI arguments. |
| `collect_review_set.py` | Collects the historical six-site review profile using the wrapper. Set `BRAND_CANDIDATE_ROOT` to a frozen package containing `RELEASE.json` and optionally `BRAND_REVIEW_OUT_DIR`. It makes real read-only website requests when explicitly run. Its six-page profile is for review collection, not the full default demo. |
| `failed_about_rehearsal.py` | Runs a controlled localhost fixture with an unavailable About page. Uses the existing test-only private-target API; production CLI target policy stays unchanged. Set `BRAND_CANDIDATE_ROOT` and a fresh `BRAND_RUN_DIR` as needed. |
| `offline_contract_probe.py` | Replays local merge/render and rejection cases against dated archived packets. Takes the package directory and a fresh existing output directory as positional arguments. Requires the historical root `verification/replay-manifest/live-bare`, `live-python` and `verification/review-set/publishing` datasets. It blocks network operations and claims no new Claude assessment. |
| `summarize_evidence.py` | Summarizes the frozen 8.4.0 rehearsal/review datasets restored under root `verification/`. Its frozen commit checks are deliberate. Writes derived summaries and triage, so run against a working copy of the archived data. It does not provide independent human accuracy labels. |

The latter two tools require historical data excluded from the current tracked
tree. Original data and tool versions remain available from commit `1872f7b` or
the ignored local `reference-archive/` directory. Restore the required historical
datasets into root `verification/` before running either tool. Default generated
outputs still use that ignored directory, preserving existing data layouts and
record semantics.

Use fresh output locations, retain failed runs, and distinguish local contract
probes from executed host searches, image views and live browser assessments.
For a normal audit, use the documented Claude command or `run_audit.py` rather
than these instrumentation helpers.
