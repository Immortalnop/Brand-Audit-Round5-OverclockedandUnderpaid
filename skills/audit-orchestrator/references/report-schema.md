# Report schema

Top-level: site, audited_at, summary (total_findings, critical, high, medium,
low, proactive_improvements, insufficient_evidence_items), coverage
(pages_discovered, pages_analyzed, pages_skipped, rendered_pages,
external_claims_checked, external_footprint_queries, external_fetches,
identity_confidence, memory_budget_used_mb, runtime_seconds,
deadline_reached), warnings, findings (see finding-schema.md).


Every finding and recommendation also exposes a stable `check_id`, `mechanism`,
`implementation_detail` and `expected_outcome` from common/check_catalog.py.
Merged findings include `check_ids` for all contributing rules. Per-report `id`
is unchanged. The action object mirrors the two catalog action-detail fields.
Missing catalog entries are rejected on the public audit path. These fields do
not replace the observed root cause, evidence, status or affected-page list.


Confidence: `confidence.score` is min(sample_representativeness,
identity_confidence, execution_penalty). sample_representativeness is
max(crawl_completeness, min(section_coverage, sample_size)): section_coverage is
sections with an analyzed page over sections discovered (a section is the first
path segment), and sample_size is pages analyzed over min(pages discovered, 30).
Coverage also reports `sections_discovered`, `sections_analyzed` and
`page_types_analyzed`.

Action plan: every finding's and recommendation's `suggested_action` also
carries `impact` (low, medium, high), `effort`, `quadrant` (quick_win,
major_project, fill_in, deprioritize), `quadrant_label` and `quick_win`.
Impact comes from severity, capped at medium for suspected items and low for
insufficient evidence, and raised from low to medium for a confirmed issue on
at least half of the analyzed pages. Medium and high impact count as valuable;
medium and high effort count as real work.

Top-level `top_actions` lists up to 5 defects in priority order with
`finding_id`, `title`, `summary`, `priority`, `impact`, `effort`, `quadrant`,
`quick_win` and `start_here` (the first quick win, or the first defect when
there is none). `quick_wins` lists up to 5 quick wins across findings and
recommendations.

Fix snippets: for no-jsonld, page-type-schema-gap:*, no-llms-txt,
llms-txt-invalid, missing-canonical, invalid-canonical, social-metadata,
social-url, twitter-card, location-markup-missing and contact-markup-missing,
`suggested_action.snippet`
holds ready-to-paste code built from observed facts (`format`, `placement`,
`code`, `filled_from`, `placeholders`, `note`). Values the audit did not
observe are REPLACE_WITH_... placeholders, all listed in `placeholders`.

Transport diagnostics: coverage includes transport_diagnostics, transport_environment,
robots_attempt_outcomes and robots_permission. Failed robots acquisition means
permission unknown, zero inferred blocks and degraded execution. Exact TLS
verification details and recovered attempt outcomes are retained separately from
site findings. An HTTP status is not a TLS error.
