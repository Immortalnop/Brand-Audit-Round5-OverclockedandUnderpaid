# Execution policy (v6)

Validate -> acquire once -> independent batch (21 jobs) -> identify important
facts -> dependent batch (9 jobs) -> merge -> prioritize -> recommendations ->
validate -> JSON. Snapshot data stays immutable until report serialization.

The public API runs the complete audit in an isolated process with a 270-second
watchdog and brief kill grace. Analysis batches use bounded waits and record
unfinished jobs. Acquisition has a 110-second phase deadline. Watchdog failure
returns an explicit evidence-unavailable report rather than inventing findings.

All acquisition probes, redirects and pages share 90 requests and 40 MiB of body
bytes; expanded gzip is bounded. Each hop checks URL safety and robots permissions.
DNS results are validated and the connection uses that address with original-host
TLS verification. Robots 404 permits crawling; unreadable/error robots fail closed.
Cross-origin redirects are blocked. Production pacing respects robots crawl-delay.

Optional rendering is opt-in and uses additional local phase caps of 20 requests,
4 MiB and 25 seconds under the outer deadline. Only allowed same-origin GETs are
fulfilled; WebSockets, service workers, downloads and other methods are disabled.
Search is optional and provider-specific. See README for capability limitations.
