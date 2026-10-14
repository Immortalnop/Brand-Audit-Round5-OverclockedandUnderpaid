# Full Claude Code audit and replay

Use `Brand-AI-Readiness-Audit-round5-final_version.zip` and the setup in
`REPLAY_Overclocked_and_Underpaid_round5_final.txt`. The ZIP extracts to
`Brand-AI-Readiness-Audit-round5-final_version/` inside `audit-workspace/`;
`out/` is a sibling folder. There is no additional `package/` directory.

Load the extracted package with `claude --plugin-dir ./Brand-AI-Readiness-Audit-round5-final_version`
from the audit workspace, then run `/brand-audit:audit <url>` in Claude Code.
Each invocation creates a fresh `out/<UTC-run-id>/` directory; no prompt editing
or emptying old outputs is needed. The master skill binds `FINAL_AUDIT_PROMPT.txt`
to the current URL, package, interpreter and first-tool clock. The manifest embeds
that same prompt exactly as a manual fallback. It runs the complete default workflow with
a normal 50-page cap. The standalone worker ceiling stays 270 seconds; the demo
passes a shared host clock to bound the remaining allowance. There are no reduced
page settings or manual archive/file checksum steps. Required packet
binding fields are copied for automatic engine validation.

Use `/brand-audit:audit <url> --max-pages 100` for an optional larger sample.
The accepted range is 1-100, with 50 still the default. Request/byte allowances
follow the engine's existing scaling; the time limits and full AG/report/handoff
workflow remain the same. A larger cap does not guarantee that many acquired pages.
Main reports, agent-outcomes.json and repair-prompt.md stay at the run root.
Its `verification/` directory contains the bounded evidence packet, AG notes,
optional image/receipt and workflow metadata. Its README explains when each file
is created and how they connect. No source/report content is changed by the layout.

The Claude harness-version and model fields are intentionally blank for now.
The launch explicitly requests Opus 5.5 with `--model claude-opus-5-5`. Fill the
fields from the actual session when recording the demonstration. Configure optional
dependencies before running and report the capabilities actually exercised.

Read RELEASE.json when present; older branch ZIPs may omit it. An engine
code_version ending in +unknown is preserved rather than treated as failure.
If the archive includes historical prompts, use the revised prompt supplied here.

Keep the complete JSON/Markdown, evidence, outcomes, notes and actual transcript.
The manifest includes full setup, native-only fallback and final verification
steps. The example URL is Tartine; change it for the actual public URL.
Runtime and skills are updated for 8.5.1. The earlier evidence in
`verification/replay-manifest/record.json` describes its historical candidate; exact
Claude/laptop execution of this revision,
independent finding review and presentation recording remain pending.

The full demo now passes a UTC host clock captured before reading the contracts.
The 50-page default stays; shared-clock mode narrows the worker to remaining time
inside the 270-second target, reserves 45 seconds for finalization, and gives AG
work up to 210 seconds from the balance. Independent Claude reads run in small
batches with one writer and one merge. The clock is never reset. The compact local
handoff helper and optional single full-image fetch avoid unnecessary context
loading and provide an honest image-view path. Actual prompt-to-reply timing and
parallel overlap still require an intended-laptop Claude trace and stopwatch.

The 8.4.2 follow-up adds clock/evidence checkpoints and preflight before the single
merge. The host must retain all six outcomes, continue eligible work while time
permits, use the actual exported image parents and keep query/source records at
the check level. A blocked source does not end other checks. Exact field examples
are in the agent skill's checks reference. The final reply uses the local
`terminal` scaffold with all six AG results and the first two findings, including
evidence and fixes. The finalization reserve is already excluded from the agent
deadline; do not subtract it twice. Full Claude verification remains a separate
actual run, not an inference from native tests.

The 8.4.3 parser correction retains genuine introductory headers inside content
for AG-01 body evidence and native main headings. It changes the acquisition
observations, so older bound reports/outcomes need a fresh run. The canonical
default 50-page cap, deadlines and evidence requirements are unchanged.

The 8.5.0 workflow adds `repair-prompt.md` after merge/render, using a local helper.
It embeds the complete final report, available bound packet/outcomes and stage
notes without truncating the findings or treating them as proven. The terminal
ends with a short prompt that directs the next agent to that file. Attach the full
file and listed images when the next agent cannot read the workspace. The repair
task first verifies every finding, preserves audit artifacts and fixes supported
issues in the supplied website source. Missing source access produces a review
and repair plan, not invented repairs. This step adds no crawl or live mutation.
