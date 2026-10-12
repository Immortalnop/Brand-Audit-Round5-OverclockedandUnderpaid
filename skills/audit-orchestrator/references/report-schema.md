# Report schema

Top-level (required by the handout and enforced by `validate_report.py`): `site`,
`audited_at`, `summary` (`total_findings`, `critical`, `high`, `medium`, `low`,
`proactive_improvements`, `insufficient_evidence_items`, `total_recommendations`,
`hygiene_items`), `findings`, plus `coverage`, `execution_status`,
`limitations`, `confidence`.

Round-5 additions:
- `action_plan`: ordered `{rank, finding_ids, summary, severity, priority, effort,
  owner_role, priority_score}` rows; references findings by id, never repeats them.
- `top_actions`: the first five `action_plan` rows.
- `recommendations`: only items that are NOT findings -- evidence-derived
  `beyond:*` suggestions and `baseline:*` maintenance items
  (status `not_applicable`, `evidence_status: general_best_practice`).
- `hygiene_findings`: SEO-hygiene items (`H-001` ...), excluded from severity counts.
- `scoring_context`: the inputs `common/scoring.py` used (needed by finalize).
- `agent_stage`: `{status: not_supplied|empty|ingested, brief, next_step}`.

Every finding and recommendation exposes a stable `check_id`, `mechanism`,
`implementation_detail` and `expected_outcome` from `common/check_catalog.py`.
Merged findings carry `check_ids` (and `also_reported_as` for root-cause merges).
Scored findings carry `priority_score`, `tier` and `severity_rationale`
(`gate`, `detector_severity`, `scope`, `prevalence`, `adjustment`,
`sample_strength`, `priority_formula`). `suggested_action.priority` must be equal
to severity or one tier lower (validated). Missing catalog entries are rejected.

Coverage includes discovered/fetched/analysed/challenged page counts,
`templates_sampled`, `pages_per_template`, `key_intents_found`,
`asset_links_found`, transport diagnostics and `robots_permission`. A failed
robots acquisition means permission unknown and zero inferred blocks.
