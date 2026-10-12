# Execution policy

Validate -> acquire once -> independent batch (14 jobs) -> identify important
facts -> dependent batch (6 jobs) -> merge (exact, then root-cause group) ->
score (common/scoring.py) -> split core / hygiene -> prioritize -> action plan +
recommendations -> validate -> JSON (+ report.md, agent_brief.json with --out-dir).
Pass 2 (finalize_report.py) ingests agent findings and repeats merge -> validate.

The public API runs the complete audit in an isolated process with a 270-second
watchdog. Analysis batches use bounded waits and record unfinished jobs.
Acquisition has a 110-second phase deadline. Watchdog failure returns an explicit
evidence-unavailable report rather than inventing findings.

All acquisition probes, redirects and pages share 90 requests and 40 MiB of body
bytes. Each hop checks URL safety and robots permission. robots.txt follows
RFC 9309 (4xx allow, 429/5xx disallow); a challenged robots file allows one
homepage request only. Cross-origin redirects are blocked. Crawl-delay is
respected; at most 3 pages per URL template; 3 consecutive challenge responses
stop the crawl. Up to 3 key-fact PDFs are range-read (64 KiB) to detect a text layer.

Optional rendering is opt-in and uses additional local caps of 20 requests,
4 MiB and 25 seconds. Only same-origin GETs are fulfilled.
