# Fastly Client Challenge verification

The defect was independently confirmed on 2026-10-13 using the production
robots-first, SSRF-checked transport. PyPI's homepage returned actual content;
`/project/requests/` returned HTTP 200, title `Client Challenge`, 298 visible
characters and Fastly assets. The previous detector returned no signals.
The captured public HTML, response hash and observations are retained here.
Only robots.txt and the sampled page were requested for each probe. No challenge
script was executed or challenge asset requested.

The original PyPI report claiming 49 screens and eight findings was not supplied,
so those exact historical totals are not independently certified. The captured
response and the controlled regressions establish the classification defect.

## Why the supplied two-line patch was narrowed

Fastly documents the same namespace for embedded scripts on ordinary pages:
https://www.fastly.com/documentation/guides/security/client-challenges/embedding-dynamic-challenges-in-pages/

Applying the supplied patch to the exact parent revision caused eleven false-positive
regression failures: thin normal pages, a short integration guide, comments and
SVG/example titles were excluded merely for containing the namespace.
The repair requires the exact document title together with the provider marker,
retains the existing 2xx thinness/small-body and HTTP-status guards, and parses the
bounded HTML title when a file/profile probe supplies no title. Generic challenge
recognition, limits, robots, retries, rendering and scoring retain their policies.

## Regression evidence

- `before-suite.txt`: current Fastly regressions against exact parent `9506fd6`;
  14 failed, 29 passed. These exercise production detection, acquisition and reports.
- `supplied-patch-suite.txt`: proposed patch against normal-page controls;
  11 failed, 18 passed. It is retained as evidence, not installed in production.
- `targeted-suite.txt`: 231 passed across robustness, observations and precision traps.
- Complete checkout: 1,344 passed. Final extracted package: 1,340 passed and one
  expected build-tool module skip; its four tests passed in the checkout suite.

Controlled full audits verify zero eligible pages yields `insufficient_evidence`
and no content findings, two consecutive challenges stop acquisition without
retries or optional follow-up requests, and mixed sites retain their real pages
including those with embedded Fastly scripts. File challenges are inaccessible,
not malformed; profile challenges remain unverified, not broken or verified.

## Recheck on the demonstration laptop

1. Obtain the pushed `final_version` branch or the new release ZIP, and check
   `RELEASE.json` against `record.json` before presenting.
2. Run `python3 -m pytest tests/test_robustness.py -k fastly -q` with pytest installed.
   The regression suite uses only localhost and requires no challenge bypass.
3. Run the audit with `--out` to a new output file on a known public site and PyPI.
   Live protections vary; inspect `coverage.pages_analyzed`, `pages_challenged`,
   `challenged_pages`, `crawl_stopped_by_challenge` and `execution_status`.
   A protected response is an evidence limitation, never proof of a content defect.
4. Complete the independent finding review and actual host/presentation rehearsal
   described in `verification/FINAL_DEMO_CHECKLIST.md`. Test passes do not certify all
   findings or substitute for the intended-laptop run and screen recording.

## Final branch synchronization

A final all-branch fetch found Aarush's add_md commit `536bee6`. Its exact diff
only sets the critical timeout in a slow-start test to the ordinary timeout
already used in its bound, and adds an ignore rule. The test assertions were not
changed; all three tests in the module passed. The merge `f321bf4` retains our
ignore rules. Runtime code, skills, examples, README and marketplace metadata
are byte-identical to tested Fastly runtime freeze `df925c5`.

The final committed-snapshot ZIP includes this test correction. Its extracted
focused suite passed 234 tests; the complete extracted result is in record.json.
The live PyPI CLI was run from the earlier exact runtime freeze (identical
runtime): 8.208 seconds, one real homepage analyzed, two HTTP-200 challenges
recorded, and acquisition stopped. No challenged URL appears in finding or
recommendation affected scope. Two remaining findings concern acquired homepage
markup and acquired sitemap data; zero total findings is not promised.
