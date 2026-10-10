"""Runtime, memory, and concurrency limits."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    TOTAL_AUDIT_TIMEOUT_S: float = 270
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
    MAX_EXTERNAL_CONCURRENCY: int = 4
    MAX_TOTAL_HTTP_REQUESTS: int = 90
    # Non-text media (facts locked in images and PDFs). Fetched after the page
    # crawl from whatever request, byte and time budget remains; same origin only.
    MAX_IMAGE_FETCHES: int = 6
    MAX_SVG_BYTES: int = 262_144
    MAX_IMAGE_HEADER_BYTES: int = 65_536
    MAX_PDF_FETCHES: int = 3
    MAX_PDF_BYTES: int = 1_500_000
    PDF_PARSE_BUDGET_S: float = 4.0
    MAX_IMAGE_RECORDS_PER_PAGE: int = 60


DEFAULT_LIMITS = Limits()
