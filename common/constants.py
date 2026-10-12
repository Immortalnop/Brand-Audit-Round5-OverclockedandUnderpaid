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
    # Representative sampling (A8): at most this many pages per URL template.
    MAX_PER_TEMPLATE: int = 3
    # Courtesy stop (A1/A2): stop crawling after this many consecutive challenge
    # or rate-limit responses -- repeating them adds load and no evidence.
    MAX_CONSECUTIVE_CHALLENGES: int = 3
    # Non-text facts (A10): small, robots-checked range reads of key-fact PDFs.
    MAX_ASSET_PROBES: int = 3
    ASSET_PROBE_BYTES: int = 65_536


DEFAULT_LIMITS = Limits()


# AI and search agents evaluated against robots.txt (A12). The role decides how
# much a block hurts: classic search indexes and AI search indexes decide whether a
# page can be found and cited at all; user-triggered fetchers are what an assistant
# uses to read a page live when a user asks about it; training crawlers only affect
# model training and blocking them is a legitimate policy choice.
AI_AGENTS = (
    ("Googlebot", "search_index"), ("Bingbot", "search_index"),
    ("OAI-SearchBot", "ai_search"), ("Claude-SearchBot", "ai_search"), ("PerplexityBot", "ai_search"),
    ("Applebot", "ai_search"), ("DuckAssistBot", "ai_search"),
    ("ChatGPT-User", "user_fetch"), ("Claude-User", "user_fetch"), ("Perplexity-User", "user_fetch"),
    ("GPTBot", "training"), ("ClaudeBot", "training"), ("Google-Extended", "training"),
    ("Applebot-Extended", "training"), ("CCBot", "training"), ("meta-externalagent", "training"),
    ("Bytespider", "training"), ("Amazonbot", "training"),
)
AI_AGENT_ROLE = dict(AI_AGENTS)

# Keywords that mark a link, file or image as carrying key business facts (A10).
FACT_KEYWORDS = (
    "price", "pricing", "prices", "rate", "rates", "tariff", "fee", "fees", "menu", "catalog", "catalogue",
    "brochure", "spec", "specs", "specification", "datasheet", "timetable", "schedule", "hours",
    "syllabus", "admission", "prospectus", "size-chart", "sizechart", "price-list", "pricelist",
)
