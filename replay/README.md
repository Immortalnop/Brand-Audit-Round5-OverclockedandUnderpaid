# Full Claude Code audit and replay

Use `Brand-AI-Readiness-Audit-round5-final_version.zip` and the setup in
`REPLAY_Overclocked_and_Underpaid_round5_final.txt`. The ZIP extracts to
`Brand-AI-Readiness-Audit-round5-final_version/` inside `audit-workspace/`;
`out/` is a sibling folder. There is no additional `package/` directory.

Paste `FINAL_AUDIT_PROMPT.txt` once into a fresh Claude Code session. The manifest
embeds that same prompt exactly. It runs the complete default workflow with
a normal 50-page cap. The standalone worker ceiling stays 270 seconds; the demo
passes a shared host clock to bound the remaining allowance. There are no reduced
page settings or manual archive/file checksum steps. Required packet
binding fields are copied for automatic engine validation.

The Claude harness-version and model fields are intentionally blank for now.
The launch explicitly requests Opus 5.5 with `--model claude-opus-5-5`. Fill the
fields from the actual session when recording the demonstration. Configure optional
dependencies before running and report the capabilities actually exercised.

Read RELEASE.json when present; older branch ZIPs may omit it. An engine
code_version ending in +unknown is preserved rather than treated as failure.
If the archive includes historical prompts, use the revised prompt supplied here.

Keep the complete JSON/Markdown, evidence, outcomes, notes and actual transcript.
The manifest includes full setup, native-only fallback and final verification
steps. The example URL is Bare Necessities; change it for the actual public URL.
Runtime and skills are updated for 8.4.1. The earlier evidence in
`verification/replay-manifest/record.json` describes its historical candidate; exact
Claude/laptop execution of this revision,
independent finding review and presentation recording remain pending.

The full demo now passes a UTC host clock captured before reading the contracts.
The 50-page default stays; shared-clock mode narrows the worker to remaining time
inside the 270-second target, reserves 60 seconds for finalization, and gives AG
work up to 180 seconds from the balance. Independent Claude reads run in small
batches with one writer and one merge. The clock is never reset. The compact local
handoff helper and optional single full-image fetch avoid unnecessary context
loading and provide an honest image-view path. Actual prompt-to-reply timing and
parallel overlap still require an intended-laptop Claude trace and stopwatch.
