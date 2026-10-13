# Validation

How each required regression case of the Round 5 plan (T7.1) is checked. Every
test below uses offline inputs or controlled localhost fixtures and is part of the normal suite
(`python -m pytest tests`).

| Case | Required result | Test |
| --- | --- | --- |
| All waiting-room responses | Insufficient evidence, no page-content findings or passes, no bypass | `test_round5_observations.py::test_every_url_a_waiting_room_is_insufficient_evidence`, `::test_mixed_site_keeps_real_pages_and_lists_the_gated_path`, `::test_holding_page_with_a_long_contact_list_is_still_a_waiting_room` |
| Queue wording in a real article | Normal content stays eligible | `test_round5_observations.py::test_article_about_queue_software_is_not_a_waiting_room` |
| Bare SPA without queue signals | Reaches the rendering assessment | `test_round5_observations.py::test_thin_app_shell_without_queue_wording_reaches_rendering` |
| State in attributes | Bounded, source-labelled detection; no rendered content invented | `test_round5_observations.py::test_attribute_state_is_detected_bounded_and_labelled`, `::test_large_settings_attribute_on_a_rich_page_is_not_state` |
| Framework or state plus thin shell | Correlated signs do not force high severity | `test_round5_observations.py::test_correlated_shell_signs_alone_do_not_make_an_inner_page_high` |
| 503 on a possible inbound-link source | No confirmed site-wide orphan claim | `test_round5_observations.py::test_failed_linking_page_prevents_an_orphan_claim` |
| Truncated HTML or link list | Partial observation stated; no full graph or absence claim | `test_round5_observations.py::test_truncated_page_is_partial_and_never_a_dead_end`, `::test_truncated_single_page_never_gets_full_assurance` |
| Complete static sampled dead end | Local scoped observation kept | `test_round5_observations.py::test_complete_static_dead_end_is_still_reported` |
| Redirect aliases with one content copy | Every alias reaches the kept node | `test_round5_observations.py::test_link_to_a_dropped_redirect_alias_reaches_the_kept_page` |
| Different query-based products | Not merged only because the path matches; view, sort and paging variants stay one page | `test_round5_observations.py::test_query_pages_with_different_content_are_different_pages`, `::test_view_and_paging_query_variants_stay_one_page_with_different_text` |
| One malformed block among many | Parse location and reach-based severity | `test_round5_observations.py::test_one_bad_block_among_many_is_proportionate_and_located`, `::test_widespread_bad_blocks_escalate` |
| Byte-truncated valid block | Transport limitation, not malformed source JSON | `test_round5_observations.py::test_byte_truncated_valid_block_is_not_malformed_source` |
| Repeated noindex variants | Grouped only when page identity and crawler scope match | `test_round5_observations.py::test_noindex_pages_are_grouped_by_scope_without_losing_pages`, `::test_homepage_noindex_does_not_claim_the_whole_site` |
| Slow permitted robots or start response | Critical allowance used without extending the stage | `test_round5_observations.py::test_slow_robots_uses_the_critical_allowance` |
| Nearly expired deadline | Workers and fetches stop promptly | `test_round5_observations.py::test_nearly_expired_stage_returns_promptly` |
| Bare, critical or mismatched agent input | Rejected with reasons, or capped with the reason recorded | `test_round5_agent_handoff.py::test_bare_ag03_rejected_and_report_preserved`, `::test_ag01_critical_override_is_capped_with_reason`, `::test_mismatched_or_stale_bindings_are_rejected`, `::test_duplicate_unknown_and_invalid_outcomes_are_rejected` |
| Partial or no-capability agent stage | Per-check not_assessed, limitations kept | `test_round5_agent_handoff.py::test_missing_vision_leaves_ag04_not_assessed`, `::test_legacy_ag01_only_array_leaves_ag06_unassessed` |
| Valid no-defect AG-01 | Source-backed pass, no padding finding | `test_round5_agent_handoff.py::test_about_passage_assessed_without_search_round_trip` |
| Malicious instructions in site text | Cannot change severity, policy or tools | `test_round5_agent_handoff.py::test_instruction_like_site_text_is_flagged_and_cannot_raise_severity` |
| Twelve affected pages | Counts stay twelve despite capped examples | `test_round5_budget_reports.py::test_twelve_orphans_stay_twelve`, `::test_schema_absence_lists_every_page` |
| Final merge and Markdown | No request; actions, snippets, passes and limitations agree | `test_round5_release.py::test_workflow_acquires_once_and_the_merged_report_is_consistent` |
| Optional transport concurrency | Combined counters stay under the stated allowance | `test_round5_budget_reports.py::test_reservations_never_exceed_the_ceiling_across_threads`, `::test_second_transport_inherits_what_the_first_left`, `::test_headless_child_is_charged_its_reserved_slice` |

T7.3 before and after: `test_round5_release.py::test_fixing_a_defect_removes_its_finding_and_keeps_positive_controls`
shows that adding the missing H1 removes the `h1` finding, moves the check to
the passed checks and keeps every check that passed before. It validates
diagnosis and verification only, not any ranking, citation or conversion gain.

## Environments

The original destination notes recorded Windows 11 with Python 3.14.4. The 8.4.0
candidate was also verified on Linux with CPython 3.14.8: 1,293 checkout tests
passed, and 1,289 extracted-runtime tests passed with one build-tool module skipped
(the tool is excluded from the package). No macOS run or confirmation of the
intended demonstration laptop is claimed.

Three actual host workflows read the frozen packet, assessed its exact raw About
opening, explicitly skipped search/vision and merged once without further
requests. A known failed-About case stayed unassessed. Local-host rehearsals are
not independent accuracy evaluation or a presentation recording. The native
six-site review retains blocked runs and blank human labels; numerical accuracy
and calibration targets remain unverified. Source-backed editorial suggestions
still require human judgment. Heuristic confidence is not a calibrated probability.
