# Remaining verification before the demo

Automated test results are recorded in RELEASE_VERIFICATION.json. They verify
specific regressions and contracts; they do not establish universal correctness.

1. **Independent review of every finding.** Have another person inspect all 64
   rows in `verification/review-set/findings-review.csv`. For each row, open the
   report named in `report`, then the corresponding acquisition/evidence files.
   Check the original support, every affected page, confirmed/suspected status,
   severity, and whether the suggested action applies. Fill `label` (`tp`, `fp`
   or `irrelevant`), the five correctness/applicability fields, `note`, `reviewer`
   and `human_reviewed`. Keep opportunity usefulness separate from defect
   precision. Treat agent-triage.csv as assistance, not independent labels.
   Triage any disagreements before presenting accuracy claims; keep blocked
   sites in the denominator and retain the original dated evidence.
2. **Confirm the intended laptop and exact release.** Record OS, Python version,
   host application/version and the commit in RELEASE.json. Check the ZIP SHA-256
   against verification/RELEASE_VERIFICATION.json. Use the extracted release for
   the actual rehearsal. On Windows, exercise literal non-ASCII reports with
   `--out`; also check redirected stdout. stdout uses reversible JSON escapes;
   file output is UTF-8. Do not append multiple audits into one JSON file.
3. **Run the complete host workflow.** Test ordinary content, a partial/blocked
   site, and a Fastly interstitial using fresh output filenames. Check coverage,
   execution status, unsupported capabilities and evidence packet readiness.
   Read the exported packet with the actual agent host, obtain only supported
   outcomes, merge them, and render Markdown. Record the command/tool transcript
   and measured wall-clock timing. Search, vision and rendering remain unassessed
   unless actually exercised. Keep failed and late runs; the 270-second workflow
   target and at-most-55-second host allowance are measured honestly.
4. **Record the presentation.** Record the full frozen-release workflow and the
   intended presentation on the confirmed laptop. Rehearse the plan's eight-minute
   target, ten-minute stop, seven presented slides and five-minute Q&A. Make sure
   a judge-selected protected URL produces an evidence limitation rather than
   an assertion about unseen site content. Save the actual recording separately
   from execution transcripts, which are not video evidence.

If findings require code changes, freeze a new commit, rerun the relevant checks
and refresh the release records before using that candidate. Historical examples
and six-site batches remain dated evidence; do not silently relabel them as fresh
executions or independent accuracy measurements.
