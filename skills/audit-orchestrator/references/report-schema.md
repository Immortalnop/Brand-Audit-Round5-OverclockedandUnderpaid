# Report schema

Top-level (required by the handout and enforced by `validate_report.py`): `site`,
`audited_at`, `summary` (`total_findings`, `critical`, `high`, `medium`, `low`,
`proactive_improvements`, `insufficient_evidence_items`, `total_recommendations`,
`hygiene_items`), `findings`, plus `coverage`, `execution_status`,
`limitations`, `confidence`.

Beyond the required fields:
- `action_plan`: ordered `{rank, finding_ids, summary, severity, priority, effort,
  owner_role, priority_score, quick_win, start_here}` rows; references findings by
  id, never repeats them. `quick_win`: medium severity or above, low effort,
  confidence >= 0.6. `start_here`: true on the first row only.
- `top_actions`: the first five `action_plan` rows, with `quick_win` and `start_here`.
- `quick_wins`: finding ids of every quick win, in plan order.
- `whats_working`: checks that ran to completion and passed, `{id (W-001...), check,
  title, check_ids, evidence, pages_checked}`. A check is listed only when every
  specialist that runs it succeeded, no finding, hygiene item or recommendation
  carries any of its check IDs, and its observation holds on the snapshot.
  finalize_report.py drops any entry an agent finding contradicts.
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

`confidence` carries `score`, `level` (high >= 0.75, medium >= 0.4, low),
`limiting_factor` (the component that set the score), `method`, `components`,
`reasons` (one sentence per component) and `explanation` (plain English).

`suggested_action.snippet` (optional) is a ready-to-paste fix: `{format,
placement, code, filled_from, placeholders, note}`. Values the audit did not
observe are `REPLACE_WITH_...` placeholders, all listed in `placeholders`.

Coverage includes discovered/fetched/analysed/challenged page counts,
`pages_out_of_scope` and `out_of_scope_pages` (login pages, with their signals),
`templates_sampled`, `pages_per_template`, `key_intents_found`,
`asset_links_found`, transport diagnostics and `robots_permission`. A failed
robots acquisition means permission unknown and zero inferred blocks.
