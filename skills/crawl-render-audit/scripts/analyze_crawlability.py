"""analyze_crawlability.py -- reachability, robots, sitemap, orphans.

Robots calibration (RFC 9309): general_disallow is only a concrete True/False when
robots.txt was actually retrieved and parsed (acquire_site sets it to None on
timeout/inaccessible/malformed/blocked). A confirmed "disallows crawling" defect
requires general_disallow is True; a robots.txt we could not check is reported as
insufficient evidence, never inferred as a block (Invariant I-1).
"""
from models import skill_result, make_finding, apply_invariant_i1, coverage_ratio
from check_helpers import is_challenged


def analyze_crawlability(artifacts, deadline):
    findings = []
    pages = artifacts.pages
    important_pages = [p for p in pages if p.url == artifacts.site_url]

    # Evidence-completeness ratio: how much of the DISCOVERED site the crawl
    # actually analyzed. "2/2 pages crawled are broken" and "2/50 pages crawled
    # are broken" are both real findings, but the first says much less about the
    # site as a whole -- confidence/severity below are scaled by this ratio
    # rather than treated as equally strong evidence.
    acq_coverage = artifacts.acquisition_metadata.get("coverage", {})
    crawl_ratio = coverage_ratio(
        acq_coverage.get("urls_analyzed", len(pages)),
        acq_coverage.get("urls_discovered", len(pages)),
    )

    general_disallow = artifacts.robots_data.get("general_disallow")
    robots_status = artifacts.robots_data.get("status", "not_checked")
    if general_disallow is True:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="high",
            status="confirmed", confidence=0.9,
            title="robots.txt disallows general crawling",
            root_cause="robots.txt blocks crawler access to the site",
            evidence=[{"type": "robots", "description": "Disallow directive found",
                       "urls": [artifacts.site_url]}],
            suggested_action={
                "summary": "Allow crawler access to public pages in robots.txt",
                "steps": ["Review robots.txt", "Remove blanket Disallow rules"],
                "priority": "high", "effort": "low",
                "expected_benefit": "Restores discoverability",
                "verification": "Re-crawl and confirm robots.txt allows access",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_crawlability.py",
                        "rule_id": "robots-block"},
        ))
    elif general_disallow is None and robots_status not in ("not_checked", "challenged"):
        # A challenged robots.txt is reported by analyze_access.py (bot-challenge-robots).
        fetched_ok = acq_coverage.get("urls_fetched_ok", 0)
        findings.append(apply_invariant_i1(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="insufficient_evidence", confidence=0.3,
            title="robots.txt could not be retrieved or parsed",
            root_cause=f"robots.txt fetch/parse status was '{robots_status}'"
                       + (f" (HTTP {artifacts.robots_data.get('http_status')})" if artifacts.robots_data.get('http_status') else "")
                       + f"; crawl permission is unknown, so the audit fetched {fetched_ok} page(s) rather than "
                         "assuming unrestricted access",
            evidence=[{"type": "robots", "description": f"robots.txt status: {robots_status}",
                       "urls": [artifacts.site_url]}],
            suggested_action={
                "summary": "Confirm robots.txt is reliably reachable and well-formed",
                "steps": ["Check robots.txt responds quickly with a 200 or a clean 404",
                          "Re-run the audit once robots.txt is reachable"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Enables a real crawl-permission verdict",
                "verification": "Re-run and confirm robots_data.status is 'ok' or 'absent'",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_crawlability.py",
                        "rule_id": "robots-unreachable"},
        )))

    # Bot-challenge interstitials often return 403/503; they are an access problem
    # (analyze_access.py), not broken pages.
    error_pages = [p for p in pages if p.status_code and p.status_code >= 400 and not is_challenged(p)]
    if error_pages:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect",
            severity="medium", status="confirmed", confidence=0.85,
            title="Broken pages found during crawl",
            root_cause="Pages return 4xx/5xx status codes"
                       + ("" if crawl_ratio >= 0.999 else
                          f" (found within {acq_coverage.get('urls_analyzed', len(pages))} of "
                          f"{acq_coverage.get('urls_discovered', len(pages))} discovered pages actually "
                          "crawled -- the rest of the site was not checked)"),
            evidence=[{"type": "http_status", "description": f"{len(error_pages)} pages returned errors ("
                       + ", ".join(sorted({str(p.status_code) for p in error_pages})) + ")",
                       "urls": [p.url for p in error_pages][:10]}],
            affected_pages=[p.url for p in error_pages],
            suggested_action={
                "summary": "Fix or redirect broken URLs",
                "steps": ["Audit error pages", "Add 301 redirects or restore content"],
                "priority": "medium", "effort": "medium",
                "expected_benefit": "Improves crawl completeness",
                "verification": "Re-crawl and confirm 200 status",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_crawlability.py",
                        "rule_id": "broken-pages"},
        ))

    # Factual coverage: pages_analyzed is only the pages that actually carried
    # readable content (2xx/3xx), and pages_skipped is the real count from
    # acquisition, never a hardcoded 0.
    coverage = {
        "pages_discovered": acq_coverage.get("urls_discovered", len(pages)),
        "pages_analyzed": acq_coverage.get("urls_analyzed", len(pages)),
        "pages_skipped": sum(acq_coverage.get("skip_reason_counts", {}).values()),
    }
    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"pages_crawled": len(pages), "important_pages_reachable": len(important_pages),
                 "crawl_coverage_ratio": round(crawl_ratio, 3)},
        coverage=coverage,
    )
