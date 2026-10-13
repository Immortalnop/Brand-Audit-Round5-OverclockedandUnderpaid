"""Runtime, memory, and concurrency limits."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    # The controlled audit worker is hard-stopped at TOTAL_AUDIT_TIMEOUT_S. Most
    # sites finish well before it; the optional agent stage gets what the worker
    # left before the workflow target, at most AGENT_STAGE_BUDGET_S, and the
    # finalization MERGE_FINALIZATION_S (saving, merge, rendering and reply).
    # A supplied host start clock also bounds the worker to the remaining time.
    # Only the worker limit is enforced by this code;
    # the agent stage is timed and reported, not stopped (run_audit.timing_plan).
    TOTAL_AUDIT_TIMEOUT_S: float = 270
    WORKFLOW_TARGET_S: float = 270
    AGENT_STAGE_BUDGET_S: float = 180
    MERGE_FINALIZATION_S: float = 60
    # Inside the worker: acquisition, then the analysis batches, then the report.
    ACQUISITION_BUDGET_S: float = 110
    RENDERING_BUDGET_S: float = 55
    EXTERNAL_ANALYSIS_BUDGET_S: float = 55
    FINALIZATION_RESERVE_S: float = 20

    MAX_PAGES_CRAWLED: int = 50
    REQUEST_DELAY_S: float = 0.2
    MAX_RESPONSE_BYTES: int = 1_500_000
    MAX_CRAWL_DEPTH: int = 4
    MAX_TOTAL_BYTES: int = 40 * 1024 * 1024
    MAX_RENDERED_PAGES: int = 8
    MAX_RETAINED_RENDERED_PAGES: int = 6
    EVIDENCE_SNIPPET_MAX_CHARS: int = 500
    VISIBLE_TEXT_MAX_CHARS: int = 20_000
    MAX_ANALYSIS_WORKERS: int = 6
    MAX_CLAIMS_CORROBORATED: int = 12
    MAX_EXTERNAL_FETCHES: int = 20
    MAX_FOOTPRINT_QUERIES: int = 4
    MAX_FETCH_RETRIES: int = 1
    PER_FETCH_TIMEOUT_MS: int = 3500
    # robots.txt and the start URL: without them nothing else can be read, so a
    # slow first answer gets longer. Still capped by the remaining stage deadline,
    # and the single retry still applies, so one critical resource can spend up to
    # about 20 seconds.
    CRITICAL_FETCH_TIMEOUT_MS: int = 10000
    MAX_EXTERNAL_CONCURRENCY: int = 4
    # Shared site allowance (common/network_budget.py "site" pool): every request
    # to the audited origin, re-anchored origin included, plus the headless
    # browser's reserved slice. MAX_TOTAL_BYTES above is its byte ceiling.
    MAX_TOTAL_HTTP_REQUESTS: int = 90
    # Shared third-party allowance ("external" pool): knowledge graphs, linked
    # profiles, the PageSpeed API and a configured search provider, each still
    # under its own smaller cap.
    MAX_EXTERNAL_HTTP_REQUESTS: int = 40
    MAX_EXTERNAL_BYTES: int = 16 * 1024 * 1024
    # Slice of the site pool reserved for the optional headless browser, which
    # runs in a child process and is charged its whole slice.
    HEADLESS_RENDER_REQUESTS: int = 20
    HEADLESS_RENDER_BYTES: int = 4_000_000
    # Non-text media (facts locked in images and PDFs). Fetched after the page
    # crawl from whatever request, byte and time budget remains; same origin only.
    MAX_IMAGE_FETCHES: int = 6
    MAX_SVG_BYTES: int = 262_144
    MAX_IMAGE_HEADER_BYTES: int = 65_536
    MAX_PDF_FETCHES: int = 3
    MAX_PDF_BYTES: int = 1_500_000
    PDF_PARSE_BUDGET_S: float = 4.0
    MAX_IMAGE_RECORDS_PER_PAGE: int = 60
    # llms.txt companion file and link checks. Same origin only; links already
    # crawled reuse the crawl result and cost no request.
    LLMS_FULL_PROBE_BYTES: int = 65_536
    MAX_LLMS_LINK_CHECKS: int = 8
    LLMS_LINK_CHECK_BYTES: int = 32_768
    # Image weight: a Range GET of the first bytes of the largest same-origin
    # content images reads their total size, format and pixel dimensions.
    MAX_IMAGE_WEIGHT_PROBES: int = 4
    IMAGE_WEIGHT_PROBE_BYTES: int = 32_768


DEFAULT_LIMITS = Limits()
