# URL command and repair handoff, October 14, 2026

Release 8.5.0 adds a small Claude Code master skill at skills/audit/SKILL.md,
invoked as /brand-audit:audit with one URL. Native Claude plugin metadata and a
separate local install catalog are in .claude-plugin/. The root marketplace.json
keeps the existing native entrypoint and its five execution contracts, with the
master skill added as a frontend. No duplicate native orchestrator is introduced.

The bootstrap captures the first-tool UTC clock and creates a distinct run under
the caller's writable workspace out/ folder, outside the package. It binds the
canonical replay procedure to the URL, package path, interpreter and current run
paths, quoting command arguments rather than invoking a shell. It makes no
request, edits no package file and preserves earlier outputs. Tests cover query
strings containing shell metacharacters, spaces in paths, malformed input,
credential URLs, source-directory/symlink exclusion, repeated runs and the
indented full-image command's --out-dir. That image command regression caught
and corrected a wrapper path mistake before release.

The local repair_handoff helper writes repair-prompt.md exclusively after the
report is finalized. It retains the complete final report, every finding and
recommendation, available bound packet/outcomes, stage notes and separate image
paths. No finding, status, priority or evidence list is truncated or reclassified.
Stale/mismatched artifacts fail before output creation. Missing/non-ready packets
and rejected current envelopes remain explicit limitations. Source text stays
untrusted data in an adaptive JSON fence; generated handoffs use the existing
strict JSON boundary. The terminal can append a concise copyable next prompt
only when the generated snapshot contains this exact report.

The repair instructions require checking every F-ID before changing the website
source, distinguishing defects from improvements, preserving working features
and recording verification/repair decisions and tests. An absent website source
produces an evidence review and repair plan plus an access request, not invented
repairs. The audit does not run a repair agent or mutate a live website. The full
file and listed images must accompany the task if another agent lacks filesystem
access; the short terminal suggestion alone carries paths rather than all data.

The canonical prompt and embedded manual fallback are identical. The replay now
uses the URL command and actual generated run paths, keeps blank actual model /
harness fields and the requested Opus launch, and preserves the 50-page default,
270-second workflow target, 210-second host cap and advisory 45-second reserve.
The Python audit entrypoint, acquisition behavior, AG evidence rules and native
stdout are unchanged. Plugin loading adds Skill to the documented tool list.

The full checkout suite passed 1,426 tests in 133.12 seconds. Replays of the
supplied Tartine, Fastmail and Bare Necessities ZIPs exported all 16, 19 and 19
findings respectively, all recommendations and complete packet/outcome content,
with unchanged input bytes and one separate image attachment each. These local
exports took about 0.016-0.017 seconds each in this development check; this is not
a Claude runtime benchmark. The records explicitly mark that no new host AG
assessment was executed and do not certify the historical findings' truth.

Claude Code 2.1.299 was installed only in temporary validation directories with
an isolated temporary config. Its actual plugin/marketplace validator passed
without warnings. The command/argument, namespacing, plugin-root and layout
choices follow [Claude's skills documentation](https://code.claude.com/docs/en/skills),
[manifest reference](https://code.claude.com/docs/en/plugins-reference) and
[marketplace workflow](https://code.claude.com/docs/en/plugin-marketplaces).
Package extraction, local installation and component discovery will be recorded
after the committed release build. No user Claude settings were changed.

Actual authenticated Opus execution of the new command, full operator stopwatch
timing and presentation recording still require the intended demo laptop. The
existing inert-template control false positive remains a separate pending engine
issue; this release adds the requested workflow and handoff without silently
rewriting audit findings or changing that unrelated parser behavior.
