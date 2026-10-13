# Full Claude Code audit and replay

Use `Brand-AI-Readiness-Audit-round5-final_version.zip` and the setup in
`REPLAY_Overclocked_and_Underpaid_round5_final.txt`. The ZIP extracts to
`Brand-AI-Readiness-Audit-round5-final_version/` inside `audit-workspace/`;
`out/` is a sibling folder. There is no additional `package/` directory.

Paste `FINAL_AUDIT_PROMPT.txt` once into a fresh Claude Code session. The manifest
embeds that same prompt exactly. It runs the complete default workflow with
50-page acquisition and the normal 270-second core ceiling. There are no reduced
page/time overrides or manual archive/file checksum steps. Required packet
binding fields are copied for automatic engine validation.

The Claude harness-version and model fields are intentionally blank for now.
The launch uses the account's configured model. Fill the fields from the actual
session when recording the demonstration. Configure optional dependencies before
running and report the capabilities actually exercised.

The supplied source ZIP has no RELEASE.json, so reading it is optional. An engine
code_version ending in +unknown is preserved rather than treated as failure.
If the archive includes historical prompts, use the revised prompt supplied here.

Keep the complete JSON/Markdown, evidence, outcomes, notes and actual transcript.
The manifest includes full setup, native-only fallback and final verification
steps. The example URL is Bare Necessities; change it for the actual public URL.
Runtime code and skills are unchanged. Verification evidence is recorded in
`verification/replay-manifest/record.json`; exact Claude/laptop execution,
independent finding review and presentation recording remain pending.
