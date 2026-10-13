# Required defect register

Specification: supplied final_version_plan.md. Source assets remain untouched.
Tests call production APIs and retain positive controls; counts are regression
results, not independent accuracy estimates. Earlier baseline probes are retained
in phase1-before.json and phase5-before.json.

| ID | Implementation disposition | Regression evidence |
| --- | --- | --- |
| A01 | Ordinary and critical timeouts both controlled in stale fixture | test_isolation_and_coverage; baseline 1,100 passed |
| A02 | Cancellation fixture uses five worker arguments and real SIGINT | test_runtime_reliability; baseline 1,100 passed |
| A03 | AG-03 must quote actual E/C acquired support; no stitched/case-altered quote | test_final_agent_semantics |
| A04 | Typed bounded errors before set membership, hashing or mutation | test_final_input_boundaries |
| A05 | Affected scope derives from acquired supporting/compared references | test_final_agent_semantics |
| A06 | Final-content digest checked against report and envelope | test_final_packet_contract |
| A07 | Exact UTF-8 bytes; bounded all metadata; final references reconciled | test_final_packet_contract |
| A08 | AG-04 explicitly names eligible compared exported pages | test_final_agent_semantics |
| A09 | Known failed/excluded About stays unassessed | test_final_about_focus; actual failed-about host rehearsal |
| A10 | Dedicated acquired body opening survives long navigation | test_final_about_focus |
| A11 | Non-JSON constants rejected; direct nonfinite money guarded | test_final_input_boundaries; test_final_native_schema |
| A12 | Out-of-range/lossy numbers are limitations; unaffected blocks survive | test_final_input_boundaries; test_final_native_schema |
| A13 | Separate markup/visible Decimal grammar, signs/exponents preserved | test_final_input_boundaries; test_final_native_schema |
| A14 | Present malformed/ambiguous/unsupported markup never becomes missing markup | test_final_native_schema; exact baseline before probe |
| A15 | Same-subject and condition relationship required before conflicting price/contact/hours | test_final_native_schema; test_offers_facts_crawlers; before probe |
| A16 | Valid checkout metadata or validated RELEASE.json, dirty/unknown visible | test_final_reporting_policy; extracted-package execution |
| D01 | Exact decoded case-sensitive fragment, unique section and proper boundaries | test_final_about_focus |
| D02 | No universal Organization url/@id defect imported | test_final_native_schema |
| D03 | Calendar/time/offset checks; other forms remain unassessed | test_final_native_schema; test_non_text_and_dates |
| D04 | Boolean is not monetary; zero remains valid | test_final_input_boundaries; test_final_native_schema |
| D05 | Supported base/vocabulary/prefix/IRI coercion; native profile resolution uses it | test_final_native_schema; unsupported context/non-HTTP values remain limitations |
| D06 | Absence/unrelated offer never becomes a high product contradiction | test_final_native_schema |
| P01 | Google llms/FAQ scope, optional artifact requirements and safe copy | test_final_reporting_policy; supplied-artifact and Q&A controls |

Additional final-review repairs preserve every supported profile page in JSON,
reuse the existing companion probe and keep public localhost TLS test assets in
the package while excluding credentials and unrelated keys. Separate confirmed
and suspected merge groups prevent weaker observations inheriting confirmation.

Post-release Fastly correction: confirmed HTTP-200 Client Challenge responses are
excluded using exact title plus provider assets, with normal embedded-script
controls. File/profile probes use a bounded parsed title; source limits, redirects,
stdout and scoring stay unchanged. See fastly-client-challenge/record.json for
baseline failures, the unsafe supplied-patch controls, live observations and full
checkout/extracted results.
