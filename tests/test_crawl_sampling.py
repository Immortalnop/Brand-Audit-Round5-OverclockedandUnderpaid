"""Crawl sampling: stratified sitemap order, representativeness-based confidence,
and the optional --max-pages flag. The acquisition test runs against a local
server only."""
import sys
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

from constants import Limits, DEFAULT_LIMITS
from models import AuditArtifacts, freeze_value, make_deadline
from acquire_site import acquire_site, stratify_by_section, site_section
from execution_summary import overall_confidence, derive_limitations
from run_audit import limits_for_pages, main, MAX_PAGES_CEILING

SECTIONS = ("news", "people", "programs")


def test_site_section():
    assert site_section("https://a.example/about/team/") == "about"
    assert site_section("https://a.example/") == ""
    assert site_section("https://a.example/News?x=1") == "news"


def test_stratify_round_robins_sections_and_keeps_their_order():
    urls = [f"https://a.example/{s}/{i}" for s in SECTIONS for i in range(3)] + ["https://a.example/solo"]
    out = stratify_by_section(urls)
    assert out[:4] == ["https://a.example/news/0", "https://a.example/people/0",
                       "https://a.example/programs/0", "https://a.example/solo"]
    assert sorted(out) == sorted(urls) and len(out) == len(urls)
    assert [u for u in out if "/news/" in u] == [f"https://a.example/news/{i}" for i in range(3)]
    assert stratify_by_section([]) == []


class _Site(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        host = self.headers.get("Host")
        if self.path == "/robots.txt":
            body, ctype = f"User-agent: *\nAllow: /\nSitemap: http://{host}/sitemap.xml\n", "text/plain"
        elif self.path == "/sitemap.xml":
            locs = "".join(f"<url><loc>http://{host}/{s}/{i}</loc></url>" for s in SECTIONS for i in range(30))
            body = f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'
            ctype = "application/xml"
        elif self.path in ("/llms.txt", "/llms-full.txt"):
            self.send_response(404)
            self.end_headers()
            return
        else:
            body = f"<html lang='en'><head><title>Page {self.path}</title></head><body><p>Text for {self.path}.</p></body></html>"
            ctype = "text/html"
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def test_bounded_crawl_samples_every_sitemap_section():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Site)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        limits = replace(Limits(), MAX_PAGES_CRAWLED=7, REQUEST_DELAY_S=0)
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        artifacts = acquire_site(url, make_deadline(limits), limits, allow_private_targets=True)
    finally:
        server.shutdown()
    sections = [site_section(p.url) for p in artifacts.pages]
    assert len(artifacts.pages) == 7
    assert set(SECTIONS) <= set(sections), sections
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["sections_discovered"] == 4 and cov["sections_analyzed"] == 4  # three sections plus the home page


def test_confidence_credits_a_representative_sample():
    base = {"pages_discovered": 826, "pages_fetched_attempted": 50, "pages_analyzed": 49,
            "identity_confidence": 0.95}
    broad = overall_confidence({**base, "sections_discovered": 12, "sections_analyzed": 12}, "completed")
    assert broad["score"] == 0.95 and broad["components"]["crawl_completeness"] == 0.06
    narrow = overall_confidence({**base, "sections_discovered": 12, "sections_analyzed": 3}, "completed")
    assert narrow["score"] == 0.25 and narrow["components"]["section_coverage"] == 0.25
    tiny = overall_confidence({**base, "pages_fetched_attempted": 5, "pages_analyzed": 5,
                               "sections_discovered": 2, "sections_analyzed": 2}, "completed")
    assert tiny["score"] == 0.17  # 5 pages are too few, even if every section was reached
    assert "sample_representativeness" in broad["method"]


def test_limitation_names_the_sections_reached():
    art = AuditArtifacts("https://a.example/", "https://a.example", (), freeze_value({"status": "ok"}),
                         freeze_value({"present": True, "status": "ok"}), freeze_value({"status": "ok"}),
                         freeze_value({"coverage": {}}), ())
    lines = derive_limitations(art,{"headless_rendering": True, "external_search": True},
                               {"pages_never_attempted": 776, "pages_discovered": 826,
                                "pages_fetched_attempted": 50, "sections_discovered": 12,
                                "sections_analyzed": 9}, "completed")
    assert any("reached 9 of 12 site sections" in line for line in lines)


def test_limits_for_pages_scales_budgets_but_not_time():
    bigger = limits_for_pages(DEFAULT_LIMITS, 100)
    assert bigger.MAX_PAGES_CRAWLED == 100
    assert bigger.MAX_TOTAL_HTTP_REQUESTS == DEFAULT_LIMITS.MAX_TOTAL_HTTP_REQUESTS + 50
    assert bigger.MAX_TOTAL_BYTES == DEFAULT_LIMITS.MAX_TOTAL_BYTES * 2
    assert bigger.TOTAL_AUDIT_TIMEOUT_S == DEFAULT_LIMITS.TOTAL_AUDIT_TIMEOUT_S
    smaller = limits_for_pages(DEFAULT_LIMITS, 10)
    assert smaller.MAX_PAGES_CRAWLED == 10
    assert smaller.MAX_TOTAL_HTTP_REQUESTS == DEFAULT_LIMITS.MAX_TOTAL_HTTP_REQUESTS
    assert limits_for_pages(DEFAULT_LIMITS, 10_000).MAX_PAGES_CRAWLED == MAX_PAGES_CEILING


@pytest.mark.parametrize("value", ["0", str(MAX_PAGES_CEILING + 1), "-5"])
def test_cli_rejects_out_of_range_max_pages(value, monkeypatch):
    monkeypatch.setenv("AUDIT_PROGRESS", "0")  # main() sets it; monkeypatch restores it afterwards
    with pytest.raises(SystemExit) as exc:
        main(["https://example.com", "--max-pages", value])
    assert exc.value.code == 2
