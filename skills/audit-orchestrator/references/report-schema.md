# Report schema

Top-level: site, audited_at, summary (status_reason first when no page could
be analyzed, then total_findings, critical, high, medium,
low, proactive_improvements, insufficient_evidence_items), coverage
(pages_discovered, pages_analyzed, pages_skipped, rendered_pages,
external_claims_checked, external_footprint_queries, external_fetches,
identity_confidence, memory_budget_used_mb, runtime_seconds,
deadline_reached), warnings, findings (see finding-schema.md),
recommendations, whats_working.

Recommendations come in two shapes. A proactive finding is linked, not
copied: `{"id": "R-...", "finding_id": "F-...", "check_id", "check_ids",
"category", "finding_type": "proactive_improvement", "title", "status",
"provenance": {"source": "finding_reference"}}`. Its evidence, steps, action
plan and snippet are on the finding it names. Validation drops a link whose
finding is not in the report. The other recommendations are baseline
maintenance items for categories with no finding; they have the full finding
fields and their own `suggested_action`.

`whats_working` lists the checks that ran and passed, in a fixed order:
`{"id": "W-...", "check", "title", "check_ids", "evidence", "pages_checked"}`.
A check is listed only when every skill that runs it finished with status
success, no finding or recommendation carries any of its `check_ids`, and the
observation in `evidence` holds on the snapshot (for example, every page
checked has a title). A check with nothing to look at is not listed.
`pages_checked` is null for robots.txt, sitemap and llms.txt checks. When no
page was analyzed only those three kinds can appear; an audit that did not
finish has an empty list. Implemented in
`skills/audit-orchestrator/scripts/whats_working.py`.


Coverage also reports `offer_expiry` (`offer_expiry_pages_scanned`,
`offer_deadlines_found`, `expired_offer_pages`, `offer_expiry_reference_date`),
`fact_consistency` (`facts_compared_with_text`, `markup_text_mismatches`,
`cross_page_conflicts`, `fact_consistency_pages`) and `ai_crawler_purposes`
(crawler name to `search`, `training`, `user_fetch` or `unclassified`, from
common/ai_crawlers.py).

Every finding and baseline recommendation also exposes a stable `check_id`, `mechanism`,
`implementation_detail` and `expected_outcome` from common/check_catalog.py.
Merged findings include `check_ids` for all contributing rules. Per-report `id`
is unchanged. A finding whose severity the severity gate lowered (see
severity-rubric.md) carries `severity_gate`: `{"from", "to", "reason"}`. Every finding
carries `coverage`: `{"affected_pages", "pages_analyzed", "pages_discovered"}`; a finding moved
from confirmed to suspected because its confidence is below 0.7 carries `status_note`. The report
coverage block adds `audited_url` and `start_redirect` (null unless the start URL redirected to
another origin that was audited instead). The action object mirrors the two catalog action-detail fields.
Missing catalog entries are rejected on the public audit path. These fields do
not replace the observed root cause, evidence, status or affected-page list.


Confidence: `confidence.score` is min(sample_representativeness,
identity_confidence, execution_penalty). sample_representativeness is
max(crawl_completeness, min(section_coverage, sample_size)): section_coverage is
sections with an analyzed page over sections discovered (a section is the first
path segment), and sample_size is pages analyzed over min(pages discovered, 30).
Coverage also reports `sections_discovered`, `sections_analyzed` and
`page_types_analyzed`.

The confidence block also carries `level` (high at 0.8 or more, medium at 0.5
or more, low below), `limiting_factor` (the component that set the score; on a
tie execution_penalty, then sample_representativeness, then
identity_confidence), `reasons` (one plain-English sentence per component) and
`explanation` (a short paragraph for a non-expert). These fields never change
the score. `coverage.identity_resolution` says how entity resolution went:
resolved, parent_sub_brand, multi_brand_conflict, conflicting_sameas,
no_organization_markup or not_completed. A report from an audit that did not
finish has score 0.0, method "no completed audit evidence" and an explanation
saying so.

Login pages: a fetched page is not analyzed only when it has a visible
password input, at most 1,500 characters of visible text, no entity structured
data (any JSON-LD or microdata type other than WebPage, WebSite, BreadcrumbList
and similar page boilerplate), and at least one of an auth path segment (login,
sign-in, wp-login.php and similar, matched as a whole segment so /author/ never
matches), a login title or H1, or a login form outside the header, nav and
footer. Any doubt keeps the page in scope. Coverage reports
`pages_out_of_scope`, `out_of_scope_pages` (up to 20 entries of `url`,
`final_url`, `reason` "login_page" and `signals`) and `start_url_out_of_scope`.
Login pages count toward the page cap and toward `pages_fetched_attempted` and
`pages_fetched_ok`, never toward `pages_analyzed`.

Action plan: every finding's and baseline recommendation's `suggested_action` also
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

No page analyzed: `execution_status` is `insufficient_evidence` and
`coverage.acquisition_failure` is `{"reason", "stage", "url", "http_status",
"detail"}` (plus `signals` for a bot challenge); it is null whenever a page was
analyzed. reason is one of dns_error, tls_error, timeout, connection_error,
unsupported_response, too_many_redirects, deadline, budget_exhausted,
cross_origin_redirect, robots_disallowed, robots_unavailable,
blocked_by_safety_policy, blocked_by_challenge, access_denied (401/403),
rate_limited (429), not_found, server_error, http_error, login_page, no_content
or not_fetched; stage is robots_txt or start_url. Only robots.txt, llms.txt,
sitemap and TLS checks are reported in that case.

Bot challenges: coverage reports `pages_challenged`, `challenged_pages` (up to
20 entries of `url`, `final_url`, `http_status` and `signals`) and
`crawl_stopped_by_challenge`. Challenged pages count toward
`pages_fetched_attempted`, never toward `pages_analyzed`.

Transport diagnostics: coverage includes transport_diagnostics, transport_environment,
robots_attempt_outcomes and robots_permission. Failed robots acquisition means
permission unknown, zero inferred blocks and degraded execution. Exact TLS
verification details and recovered attempt outcomes are retained separately from
site findings. An HTTP status is not a TLS error.
