"""test_review_regressions.py -- the boundary cases an external review reproduced.

Each test here pins one defect that an independent review of this branch found
and that the branch's own suite did not cover. They are grouped by the review's
identifiers (A1..A13) so a regression can be traced back to the case that
motivated the rule. Everything here is offline: fixtures, pure functions and
one local ThreadingHTTPServer.
"""
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    sys.path.insert(0, str(ROOT / rel))

SITE = "https://shop.example/"


# --------------------------------------------------------------- A1 agent input
def _ingest(tmp_path, payload, site=SITE):
    from ingest_agent_findings import load_agent_findings
    path = tmp_path / "ag.json"
    path.write_text(json.dumps(payload))
    return load_agent_findings(str(path), site)


def test_a1_claim_without_an_observation_is_not_published(tmp_path):
    """[{"check": "AG-03"}] used to become a confirmed, high, 0.7-confidence
    contradiction with a generic fallback observation."""
    result, stage = _ingest(tmp_path, [{"check": "AG-03"}])
    assert result["findings"] == []
    assert result["metrics"]["rejection_reasons"] == ["AG-03:no_observation"]
    assert stage == "empty_unspecified"


def test_a1_evidence_with_urls_but_no_description_does_not_raise(tmp_path):
    """A dict carrying only urls used to raise KeyError('description')."""
    result, _ = _ingest(tmp_path, [{"check": "AG-03", "evidence": [{"type": "x", "urls": ["https://a.example/t"]}]}])
    assert result["findings"] == []  # a URL alone is not an observation


def test_a1_severity_ceiling_per_check(tmp_path):
    """The agent may lower a severity but never raise it past the check's meaning,
    and no agent finding is ever critical."""
    result, _ = _ingest(tmp_path, [{"check": "AG-01", "severity": "critical", "status": "confirmed",
                                    "evidence": [{"description": "The opening names no product and no market.",
                                                  "urls": [SITE + "about"]}]}])
    assert result["findings"][0]["severity"] == "medium"
    result, _ = _ingest(tmp_path, [{"check": "AG-02", "severity": "high", "status": "confirmed",
                                    "evidence": "Ran the brand and category queries; nothing independent came back."}])
    assert result["findings"][0]["severity"] == "low"


def test_a1_contradiction_without_a_source_is_capped_at_suspected(tmp_path):
    result, _ = _ingest(tmp_path, [{"check": "AG-03", "status": "confirmed",
                                    "evidence": "Two directories list it as a freight broker; the site says payroll."}])
    f = result["findings"][0]
    assert f["status"] == "suspected" and f["confidence"] <= 0.5
    assert f["provenance"]["evidence_gaps"] == ["no independent source URL was supplied"]
    assert any(e["type"] == "evidence_gap" for e in f["evidence"])


def test_a1_contradiction_with_a_source_is_confirmed_and_origin_split(tmp_path):
    result, _ = _ingest(tmp_path, [{"check": "AG-03", "status": "confirmed", "evidence": [
        {"description": "A directory lists it as a freight broker; the site says payroll.",
         "urls": ["https://dir.example/x", SITE + "about"]}]}])
    f = result["findings"][0]
    assert f["status"] == "confirmed" and f["severity"] == "high"
    # The third-party thread is evidence, never a page of the site with the defect.
    assert f["affected_pages"] == [SITE + "about"]
    assert f["provenance"]["source_references"] == ["https://dir.example/x"]


def test_a1_absence_claim_needs_a_recorded_search(tmp_path):
    bare = [{"check": "AG-02", "status": "confirmed",
             "evidence": "Searched the brand name and category; nothing independent came back."}]
    result, _ = _ingest(tmp_path, bare)
    assert result["findings"][0]["status"] == "suspected"
    result, _ = _ingest(tmp_path, {"search": {"available": True, "queries_run": 3}, "findings": bare})
    assert result["findings"][0]["status"] == "confirmed"


def test_a1_empty_array_is_not_an_all_pass(tmp_path):
    result, stage = _ingest(tmp_path, [])
    assert stage == "empty_unspecified"
    assert set(result["metrics"]["check_outcomes"].values()) == {"unreported"}
    assert any("not assessed rather than passed" in w for w in result["warnings"])
    # With explicit per-check outcomes the stage can say what actually passed.
    result, stage = _ingest(tmp_path, {"findings": [], "checks": {"AG-01": "pass", "AG-02": "not_assessed"},
                                       "search": {"available": False}})
    assert stage == "assessed_no_findings"
    assert result["metrics"]["check_outcomes"]["AG-01"] == "pass"
    assert result["metrics"]["check_outcomes"]["AG-03"] == "unreported"


def test_a1_findings_bound_to_another_site_are_refused(tmp_path):
    result, stage = _ingest(tmp_path, {"site": "https://other.example/",
                                       "findings": [{"check": "AG-03", "evidence": "x" * 60}]})
    assert stage == "not_supplied" and result["findings"] == []
    assert result["metrics"]["rejection_reasons"] == ["site_mismatch"]


def test_a1_oversized_handoff_is_a_skip_not_a_crash(tmp_path):
    from ingest_agent_findings import load_agent_findings, MAX_FINDINGS_BYTES
    path = tmp_path / "ag.json"
    path.write_text(json.dumps([{"check": "AG-03", "evidence": "x" * (MAX_FINDINGS_BYTES + 100)}]))
    result, stage = load_agent_findings(str(path), SITE)
    assert stage == "not_supplied" and result["status"] == "insufficient_evidence"


def test_a1_non_http_urls_and_overlong_text_are_sanitized(tmp_path):
    from ingest_agent_findings import MAX_EVIDENCE_CHARS
    result, _ = _ingest(tmp_path, [{"check": "AG-04", "evidence": [
        {"description": "The price-list image shows three prices absent from the page text. " + "z" * 2000,
         "urls": ["javascript:alert(1)", "data:text/html,x", SITE + "menu"]}]}])
    f = result["findings"][0]
    assert f["affected_pages"] == [SITE + "menu"]
    assert f["evidence"][0]["urls"] == [SITE + "menu"]
    assert len(f["evidence"][0]["description"]) <= MAX_EVIDENCE_CHARS


def test_a1_placeholder_text_is_not_an_observation(tmp_path):
    for text in ("n/a", "see above", "unknown", "Agent-supplied qualitative observation"):
        result, _ = _ingest(tmp_path, [{"check": "AG-03", "status": "confirmed", "evidence": text}])
        assert result["findings"] == [], text


def test_a1_malformed_and_blank_handoffs_stay_skips(tmp_path):
    from ingest_agent_findings import load_agent_findings
    path = tmp_path / "ag.json"
    for body in ("{ not json ,,,", "", "null", '{"findings": "nope"}'):
        path.write_text(body)
        result, stage = load_agent_findings(str(path), SITE)
        assert stage == "not_supplied", body
        assert result["status"] == "insufficient_evidence"
    # A partially usable list keeps the good entry and counts the bad ones.
    result, stage = _ingest(tmp_path, [{"check": "AG-99", "evidence": "y" * 60}, "nonsense",
                                       {"check": "AG-01", "status": "suspected", "evidence": [
                                           {"description": "The opening names no product or market.",
                                            "urls": [SITE + "about"]}]}])
    assert stage == "ingested" and len(result["findings"]) == 1
    assert result["metrics"]["findings_rejected"] == 2


# ------------------------------------------------- A2 repeated finalization
_NATIVE_IMAGE_FINDING = {
    "id": "F-900", "category": "ai_discoverability", "finding_type": "defect",
    "title": "Key facts appear to be carried inside images", "severity": "medium",
    "confidence": 0.65, "status": "suspected",
    "root_cause": "Images that look like fact carriers sit on a page with little supporting text",
    "evidence": [{"type": "non_text_fact", "description": "script: /img/price-list.png on a 40-word page"}],
    "evidence_text": "script: /img/price-list.png on a 40-word page",
    "check_id": "facts-in-images", "mechanism": "m", "implementation_detail": "d", "expected_outcome": "o",
    "suggested_action": {"summary": "State the image facts as HTML text", "steps": ["Publish an HTML table"],
                         "priority": "medium", "effort": "low", "expected_benefit": "b", "verification": "v",
                         "implementation_detail": "d", "expected_outcome": "o"},
    "provenance": {"skill": "crawl-render-audit", "script": "analyze_nontext_facts.py",
                   "rule_id": "facts-in-images"},
}


def _composite_report():
    """A pass-1 report whose native facts-in-images finding covers the same page
    as the agent's AG-04, so the two merge into one composite finding."""
    report = json.loads((ROOT / "examples" / "sample-report.json").read_text())
    page = report["site"].rstrip("/") + "/product"
    native = copy.deepcopy(_NATIVE_IMAGE_FINDING)
    native["affected_pages"] = [page]
    native["evidence"][0]["urls"] = [page]
    report["findings"] = list(report["findings"]) + [native]
    return report, page


def _agent_ag04(tmp_path, report, page):
    path = tmp_path / "ag.json"
    path.write_text(json.dumps({
        "site": report["site"], "search": {"available": True, "queries_run": 2}, "checks": {"AG-04": "fail"},
        "findings": [{"check": "AG-04", "status": "confirmed", "affected_pages": [page],
                      "evidence": [{"description": "The viewed image lists three prices absent from the "
                                                   "page text.", "urls": [page]}]}]}))
    return str(path)


def _image_finding(report):
    for f in report["findings"] + report.get("hygiene_findings", []):
        if "facts-in-images" in (f.get("check_ids") or [f.get("check_id")]):
            return f
    return None


def _normalized(finding):
    """Everything a reader of this finding would act on -- not just its id."""
    action = finding.get("suggested_action") or {}
    return {
        "check_ids": sorted(finding.get("check_ids") or [finding.get("check_id")]),
        "categories": sorted(finding.get("categories") or [finding.get("category")]),
        "severity": finding["severity"], "status": finding["status"], "confidence": finding["confidence"],
        "tier": finding.get("tier"), "priority_score": finding.get("priority_score"),
        "affected_pages": sorted(finding.get("affected_pages") or []),
        "evidence": sorted(json.dumps(e, sort_keys=True, default=str) for e in finding.get("evidence") or []),
        "evidence_text": finding.get("evidence_text"),
        "steps": list(action.get("steps") or []), "priority": action.get("priority"),
        "summary": action.get("summary"), "fix_snippet": finding.get("fix_snippet"),
        "severity_rationale": json.dumps(finding.get("severity_rationale") or {}, sort_keys=True, default=str),
        "contributors": sorted(json.dumps(p, sort_keys=True, default=str) for p in
                               (finding.get("provenance") or {}).get("contributing_skills")
                               or [finding.get("provenance")]),
    }


def test_a2_repeated_finalize_keeps_the_native_contribution(tmp_path):
    """The second finalize used to keep only the agent's viewed-image evidence,
    dropping the script's observation, its step and its provenance."""
    from finalize_report import finalize
    report, page = _composite_report()
    agent = _agent_ag04(tmp_path, report, page)
    once = finalize(report, agent)
    twice = finalize(copy.deepcopy(once), agent)
    thrice = finalize(copy.deepcopy(twice), agent)
    first = _image_finding(once)
    assert first is not None
    # Both contributors survive every round, not just the agent's.
    assert sorted(first["check_ids"]) == ["facts-in-images"]
    descriptions = " ".join(e.get("description", "") for e in first["evidence"])
    assert "script: /img/price-list.png" in descriptions and "viewed image" in descriptions
    skills = {json.loads(p)["skill"] for p in _normalized(first)["contributors"]}
    assert skills == {"crawl-render-audit", "entity-corroboration-agent"}
    # "Same ids" is weaker than "same report": compare the whole finding.
    assert _normalized(first) == _normalized(_image_finding(twice))
    assert _normalized(_image_finding(twice)) == _normalized(_image_finding(thrice))


def test_a2_whole_report_is_stable_across_repeated_finalize(tmp_path):
    from finalize_report import finalize
    report, page = _composite_report()
    agent = _agent_ag04(tmp_path, report, page)
    once = finalize(report, agent)
    twice = finalize(copy.deepcopy(once), agent)
    blob = lambda r: json.dumps(r, sort_keys=True, default=str)
    assert blob(once) == blob(twice)


def test_a2_finalize_does_not_mutate_its_input_report(tmp_path):
    from finalize_report import finalize
    report, page = _composite_report()
    before = copy.deepcopy(report)
    finalize(report, str(tmp_path / "missing.json"))  # an empty finalize
    assert report == before
    finalize(report, _agent_ag04(tmp_path, report, page))
    assert report == before


def test_a2_dropping_the_agent_file_restores_the_native_finding(tmp_path):
    """A changed agent handoff must not leave stale agent evidence behind."""
    from finalize_report import finalize
    report, page = _composite_report()
    once = finalize(report, _agent_ag04(tmp_path, report, page))
    empty = tmp_path / "none.json"
    empty.write_text(json.dumps({"findings": [], "checks": {"AG-04": "pass"}}))
    back = finalize(copy.deepcopy(once), str(empty))
    f = _image_finding(back)
    assert f is not None and f["status"] == "suspected"
    assert all("viewed image" not in (e.get("description") or "") for e in f["evidence"])
    assert {json.loads(p)["skill"] for p in _normalized(f)["contributors"]} == {"crawl-render-audit"}


# ------------------------------------------------------------- A3 access guard
# Short, entirely ordinary pages that happen to load a bot-manager script. A
# vendor tag is not a block page: misclassifying these removes real content from
# every downstream check and can raise a bot-wall finding against a site with no
# wall. These are the positive controls the review asked for.
_PROTECTED_BUT_NORMAL = {
    "datadome tag": "<html><head><title>Our pricing</title>"
                    "<script src='https://js.datadome.co/tags.js'></script></head>"
                    "<body><nav><a href='/'>Home</a></nav><h1>Pricing</h1>"
                    "<p>Plans start at $9 per month.</p></body></html>",
    "cloudflare js detections": "<html><head><title>Contact</title>"
                                "<script src='/cdn-cgi/challenge-platform/h/b/scripts/jsd/main.js'>"
                                "</script></head><body><h1>Contact us</h1><p>Call 555-0100.</p></body></html>",
    "turnstile widget on a form": "<html><head><title>Sign up</title>"
                                  "<script src='https://challenges.cloudflare.com/turnstile/v0/api.js'></script>"
                                  "</head><body><h1>Sign up</h1><form><div class='cf-turnstile'></div></form>"
                                  "</body></html>",
    "imperva resource script": "<html><head><title>Hours</title></head><body><h1>Opening hours</h1>"
                               "<p>Mon-Fri 9-5.</p><script src='/_Incapsula_Resource?SWJIYLWA=719d'>"
                               "</script></body></html>",
    "aws waf sdk": "<html><head><title>Menu</title><script src='https://abc.awswaf.com/abc/challenge.js'>"
                   "</script></head><body><h1>Menu</h1><p>Dosa 80. Idli 50.</p></body></html>",
    "perimeterx tag": "<html><head><title>Shop</title><script>window._pxAppId='PXabc'</script></head>"
                      "<body><h1>Shop</h1><p>Free delivery over 500.</p></body></html>",
}


def test_a3_short_legitimate_pages_behind_a_bot_manager_are_content():
    from access_guard import classify_access
    headers = {"Content-Type": "text/html", "server": "cloudflare", "x-datadome": "protected"}
    for name, body in _PROTECTED_BUT_NORMAL.items():
        result = classify_access(200, headers, body, 120)
        assert result["kind"] == "ok", (name, result)


def test_a3_real_interstitials_are_still_detected():
    from access_guard import classify_access
    cases = [
        (403, {"cf-mitigated": "challenge"},
         "<html><head><title>Just a moment...</title></head><body>"
         "<script>window._cf_chl_opt={cZone:'x'}</script></body></html>", 40, "cloudflare"),
        (403, {"x-datadome": "blocked"},
         "<html><body><script src='https://geo.captcha-delivery.com/captcha/?initialCid=x'></script>"
         "</body></html>", 20, "datadome"),
        (403, {}, "<html><body>Request unsuccessful. Incapsula incident ID: 123-456</body></html>", 60, "imperva"),
        (403, {"server": "AkamaiGHost"},
         "<html><head><title>Access Denied</title></head><body>Access Denied: reference #18.ab12cd34"
         "</body></html>", 70, "akamai"),
        (200, {}, "<html><head><title>Client Challenge</title></head><body>JavaScript is disabled in your "
                  "browser. Please enable JavaScript to proceed.</body></html>", 90, "generic"),
        (405, {"x-amzn-waf-action": "captcha"}, "<html><body>x</body></html>", 5, "aws_waf"),
    ]
    for status, headers, body, visible, vendor in cases:
        result = classify_access(status, headers, body, visible)
        assert result["kind"] == "challenge" and result["vendor"] == vendor, (vendor, result)


def test_a3_vendor_presence_alone_needs_a_refusing_status():
    from access_guard import classify_access
    body = "<html><body>Forbidden</body></html>"
    # Refused on a page served behind a bot manager: an access problem, and the
    # signals say explicitly that no interstitial marker was found.
    blocked = classify_access(403, {"x-datadome": "protected"}, body, 9)
    assert blocked["kind"] == "challenge" and blocked["vendor"] == "datadome"
    assert any("no vendor-specific interstitial marker" in s for s in blocked["signals"])
    # The same vendor header on a served page is not a challenge.
    assert classify_access(200, {"x-datadome": "protected"}, body, 9)["kind"] == "ok"


def test_a3_long_page_naming_vendors_is_never_a_challenge():
    from access_guard import classify_access
    body = ("<html><title>Our CDN</title><body>"
            + "We moved to Cloudflare and challenges.cloudflare.com and DataDome docs helped. " * 60
            + "</body></html>")
    assert classify_access(200, {"server": "cloudflare"}, body, 5000)["kind"] == "ok"


# -------------------------------------------------- A4 acquisition policy
def test_a4_https_probe_asks_robots_not_the_homepage(monkeypatch):
    """The probe used to GET the https homepage with robots_exempt=True, i.e.
    fetch content from an origin whose permissions it had not read. It now asks
    for /robots.txt, the one URL a crawler may always request."""
    import acquire_site as acq

    asked = []
    original_get = acq.Transport.get

    def spy_get(self, url, **kwargs):
        asked.append((url, kwargs.get("robots_exempt", False)))
        return original_get(self, url, **kwargs)

    monkeypatch.setattr(acq.Transport, "get", spy_get)
    from constants import Limits
    from instrumentation import Instrumentation
    from models import make_deadline
    limits = Limits()
    deadline = make_deadline(limits)
    i = Instrumentation()
    tr = acq.Transport("http://127.0.0.1:1", deadline.deadline_monotonic, limits, i, True)
    probe = acq._probe_https("127.0.0.1:1", tr, limits, i, True)
    assert probe["probe_url"] == "https://127.0.0.1:1/robots.txt"
    assert asked and asked[0][0].endswith("/robots.txt")
    # The probe's requests are charged back to the shared acquisition counter.
    assert tr.requests >= probe["requests_used"]


def test_a4_robots_policy_table_is_documented():
    """"Fail-closed" is only an honest description if the one exception is stated."""
    source = (ROOT / "skills/audit-orchestrator/scripts/acquire_site.py").read_text()
    assert "ROBOTS_POLICY" in source
    assert "THE ONE EXCEPTION" in source
    assert "2.3.1.3" in source and "2.3.1.4" in source


# ------------------------------------------------- A5 one shared request budget
def _acquire_with_cap(cap):
    from dataclasses import replace
    from constants import Limits
    from models import make_deadline
    from acquire_site import acquire_site
    from fixtures_server import start_server
    url, stop = start_server(sitemap_mode="ok")
    try:
        limits = replace(Limits(), MAX_TOTAL_HTTP_REQUESTS=cap)
        return acquire_site(url + "/", make_deadline(limits), limits, allow_private_targets=True), cap
    finally:
        stop()


def test_a5_auxiliary_probes_never_exceed_the_request_cap():
    """The HTTPS probe used to build its own one-request Transport and add its
    counters back afterwards, so MAX_TOTAL_HTTP_REQUESTS=4 produced 5 requests."""
    for cap in (3, 4, 5, 6, 8, 12):
        artifacts, _ = _acquire_with_cap(cap)
        total = artifacts.acquisition_metadata["total_requests"]
        assert total <= cap, (cap, total)


def test_a5_request_accounting_adds_up_to_the_total():
    artifacts, cap = _acquire_with_cap(12)
    acct = dict(artifacts.acquisition_metadata["request_accounting"])
    parts = acct["robots"] + acct["sitemap_and_llms"] + acct["pages"] + acct["auxiliary_probes"]
    assert parts == acct["total"] == artifacts.acquisition_metadata["total_requests"]
    assert acct["allowance"] == cap and acct["remaining"] == cap - acct["total"]
    # Redirect hops and retries are inside the same total, not beside it.
    assert "redirect_hops_followed" in acct and "retries" in acct


def test_a5_probe_is_skipped_rather_than_run_off_budget():
    from dataclasses import replace
    from constants import Limits
    from models import make_deadline
    from acquire_site import acquire_site
    from fixtures_server import start_server
    url, stop = start_server(sitemap_mode="ok")
    try:
        limits = replace(Limits(), MAX_TOTAL_HTTP_REQUESTS=5)
        artifacts = acquire_site(url + "/", make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop()
    probe = dict(artifacts.acquisition_metadata["https_probe"])
    assert probe["attempted"] is False
    assert artifacts.acquisition_metadata["total_requests"] <= 5


def test_a5_headless_rendering_reserves_from_the_remaining_allowance():
    """Rendering makes real requests from a child process. With no allowance left
    it is skipped and says so, instead of running on a private budget."""
    from analyze_rendering import _render_with_headless_browser
    from constants import Limits
    lengths, timed_out, error, usage = _render_with_headless_browser(
        ["https://example.invalid/"], Limits(), timeout_s=1, request_allowance=0, byte_allowance=0)
    assert lengths == {} and not timed_out
    assert "no request allowance" in (error or "")
    assert usage["requests"] == 0


def test_a5_report_accounts_for_every_stage_that_makes_requests():
    from run_audit import run_audit
    from constants import Limits
    from fixtures_server import start_server
    url, stop = start_server(clean=True)
    try:
        report = run_audit(url + "/", Limits(), allow_private_targets=True)
    finally:
        stop()
    acct = report["coverage"]["request_accounting"]
    assert acct["within_allowance"] is True
    assert acct["allowance"] == Limits().MAX_TOTAL_HTTP_REQUESTS
    assert acct["on_site_requests"] == acct["acquisition"]["total"] + acct["headless_rendering"]["requests"]
    assert "external_search_queries" in acct


# ------------------------------- A6 canonical origin and homepage-first sampling
def test_a6_canonical_variant_never_widens_scope():
    from acquire_site import _canonical_variant
    assert _canonical_variant("http://ex.com", "https://www.ex.com/robots.txt") == "https://www.ex.com"
    assert _canonical_variant("http://ex.com", "https://ex.com/robots.txt") == "https://ex.com"
    assert _canonical_variant("https://www.ex.com", "https://ex.com/robots.txt") == "https://ex.com"
    # Anything that is not a scheme/www variant of the requested origin stays refused.
    for origin, dest in (("https://ex.com", "http://ex.com/robots.txt"),        # downgrade
                         ("https://ex.com", "https://evil.com/robots.txt"),     # other host
                         ("https://ex.com", "https://sub.ex.com/robots.txt"),   # subdomain
                         ("https://ex.com", "https://ex.com:8443/robots.txt"),  # other port
                         ("https://ex.com", "https://ex.com/robots.txt")):      # no move
        assert _canonical_variant(origin, dest) is None, (origin, dest)


def test_a6_robots_redirect_to_canonical_origin_is_followed_once(monkeypatch):
    """The checked re-anchor: a site whose /robots.txt 301s to its canonical
    origin is not unreachable. Without it the audit made no target request and
    analysed zero pages of a healthy site."""
    import acquire_site as acq
    from constants import Limits
    from models import make_deadline
    from fixtures_server import start_server

    canonical, stop_canonical = start_server(sitemap_mode="ok")
    routes = {"/robots.txt": (301, "", {"Location": canonical + "/robots.txt", "Content-Type": "text/plain"}),
              "/": (301, "", {"Location": canonical + "/", "Content-Type": "text/html"})}
    bare, stop_bare = start_server(routes=routes)
    # Two loopback ports are a different origin by any correct rule, so the
    # variant test is widened for this fixture only; _resolve_robots and the rest
    # of acquisition are the real code under test.
    real_variant = acq._canonical_variant
    monkeypatch.setattr(acq, "_canonical_variant",
                        lambda origin, dest: canonical if dest.startswith(canonical) else real_variant(origin, dest))
    try:
        limits = Limits()
        artifacts = acq.acquire_site(bare + "/", make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop_bare()
        stop_canonical()
    anchor = dict(artifacts.robots_data["canonical_origin"])
    assert anchor["reanchored"] is True and anchor["to"] == canonical
    assert artifacts.robots_data["status"] == "ok"
    assert not artifacts.robots_data["conservative_fail_closed"]
    assert artifacts.pages and artifacts.pages[0].url == canonical + "/"
    assert any("canonical_origin_reanchored" in w for w in artifacts.warnings)
    # The refused first request is still charged to the shared allowance.
    assert artifacts.acquisition_metadata["total_requests"] >= 2


def test_a6_non_canonical_redirect_is_refused_with_its_reason():
    from constants import Limits
    from models import make_deadline
    from acquire_site import acquire_site
    from fixtures_server import start_server
    other, stop_other = start_server()
    routes = {"/robots.txt": (301, "", {"Location": other + "/robots.txt", "Content-Type": "text/plain"})}
    bare, stop_bare = start_server(routes=routes)
    try:
        limits = Limits()
        artifacts = acquire_site(bare + "/", make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop_bare()
        stop_other()
    anchor = dict(artifacts.robots_data["canonical_origin"])
    assert anchor["reanchored"] is False and anchor["refused_redirect"].startswith(other)
    assert artifacts.robots_data["conservative_fail_closed"] is True


def test_a6_homepage_is_always_the_first_content_request():
    """The priority frontier used to rank an About page ahead of the homepage, so
    a one-page budget fetched /about and missed the site's identity and its
    indexing controls entirely."""
    from dataclasses import replace
    from constants import Limits
    from models import make_deadline
    from acquire_site import acquire_site
    from fixtures_server import start_server
    for page_cap in (1, 2, 3):
        url, stop = start_server(sitemap_mode="ok")
        try:
            limits = replace(Limits(), MAX_PAGES_CRAWLED=page_cap)
            artifacts = acquire_site(url + "/", make_deadline(limits), limits, allow_private_targets=True)
        finally:
            stop()
        assert artifacts.pages[0].url == url + "/", (page_cap, [p.url for p in artifacts.pages])
        assert artifacts.acquisition_metadata["coverage"]["home_fetched_first"] is True
        if page_cap >= 2:
            # Home first, then the About page the AG-01 passage comes from.
            assert artifacts.pages[1].url == url + "/about"


def test_a6_template_cap_exemptions_are_bounded_and_counted():
    """"Never more than three pages per template" was stronger than the
    enforcement: key intents and site-wide links are exempt from the soft cap.
    The exemption is now bounded by a hard ceiling and reported."""
    from constants import Limits
    from models import make_deadline
    from acquire_site import acquire_site
    from fixtures_server import start_server
    limits = Limits()
    assert limits.MAX_PER_TEMPLATE_HARD >= limits.MAX_PER_TEMPLATE
    url, stop = start_server(sitemap_mode="ok")
    try:
        artifacts = acquire_site(url + "/", make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop()
    cov = artifacts.acquisition_metadata["coverage"]
    assert cov["template_cap"] == limits.MAX_PER_TEMPLATE
    assert cov["template_cap_hard"] == limits.MAX_PER_TEMPLATE_HARD
    assert isinstance(dict(cov["template_cap_exemptions"]), dict)
    # No template may exceed the hard ceiling, exempt or not.
    assert all(n <= limits.MAX_PER_TEMPLATE_HARD for n in dict(cov["pages_per_template"]).values())


# ------------------------------------------------------------ A7 site graph
def _page(html, url=SITE, status=200, headers=None, final_url=None):
    from constants import Limits
    from transport import Response
    from acquire_site import _extract_page
    r = Response(status, {"Content-Type": "text/html", **(headers or {})}, html.encode(), url)
    r.network_duration_ms = 10
    if final_url:
        r.final_url = final_url
    return _extract_page(url, r, 10, Limits())


def _snapshot(pages, coverage=None):
    from models import AuditArtifacts, freeze_value
    return AuditArtifacts(SITE, SITE.rstrip("/"), tuple(pages),
                          freeze_value({"status": "ok", "ai_crawler_directives": {}}),
                          freeze_value({"present": False, "status": "absent"}),
                          freeze_value({"status": "ok", "urls": [], "lastmod": {}}),
                          freeze_value({"coverage": coverage or {}}), ())


def test_a7_complete_requires_readable_links_not_just_attempted_urls():
    """An unread 503 may be the page that links to an apparent orphan. Excluding
    the failed node does not supply its missing inbound links, so "complete" is
    no longer "urls_never_attempted == 0"."""
    from build_site_graph import build_site_graph
    from models import make_deadline
    from constants import Limits
    home = _page("<html><title>H</title><h1>Home</h1><a href='/a'>A</a></html>", SITE)
    a = _page("<html><title>A</title><h1>A</h1><a href='/'>Home</a></html>", SITE + "a")
    broken = _page("<html><body>error</body></html>", SITE + "b", status=503)
    graph = build_site_graph(_snapshot([home, a, broken], {"urls_discovered": 3, "urls_never_attempted": 0}),
                             make_deadline(Limits()))["data"]
    ev = graph["link_evidence"]
    assert ev["urls_never_attempted"] == 0
    assert ev["urls_fetched_but_unread"] == 1 and ev["complete"] is False
    assert SITE + "b" in ev["unread_pages"]
    # With every page readable the ledger is complete again.
    graph = build_site_graph(_snapshot([home, a], {"urls_discovered": 2, "urls_never_attempted": 0}),
                             make_deadline(Limits()))["data"]
    assert graph["link_evidence"]["complete"] is True


def test_a7_js_shell_pages_are_not_dead_ends():
    """A page whose navigation is assembled in the browser delivers no links in
    the HTML we read. Calling that a dead end states a rendering fact as an
    engagement defect."""
    from build_site_graph import build_site_graph
    from models import make_deadline
    from constants import Limits
    home = _page("<html><title>H</title><h1>Home</h1><a href='/app'>App</a></html>", SITE)
    shell = _page("<html><title>App</title><body><div id='root'></div>"
                  "<script>window.__NEXT_DATA__={\"props\":{\"nav\":\"Pricing and plans for teams\"}}</script>"
                  "</body></html>", SITE + "app")
    graph = build_site_graph(_snapshot([home, shell]), make_deadline(Limits()))["data"]
    assert SITE + "app" in graph["rendering_scope"]["raw_shell_pages"]
    assert SITE + "app" not in graph["dead_ends"]
    assert graph["nodes"][SITE + "app"]["raw_shell"] is True
    # A genuinely link-free static page is still a dead end.
    static = _page("<html><title>T</title><h1>Terms</h1><p>No links here at all.</p></html>", SITE + "terms")
    graph = build_site_graph(_snapshot([home, static]), make_deadline(Limits()))["data"]
    assert SITE + "terms" in graph["dead_ends"]


def test_a7_redirect_aliases_collapse_into_one_node():
    """/a and /b both delivering /c is one page with two aliases. Keying nodes by
    requested URL split one page's inbound links across two entries."""
    from build_site_graph import build_site_graph
    from models import make_deadline
    from constants import Limits
    home = _page("<html><title>H</title><h1>Home</h1><a href='/a'>A</a> <a href='/b'>B</a></html>", SITE)
    via_a = _page("<html><title>C</title><h1>C</h1><a href='/'>Home</a></html>", SITE + "a",
                  final_url=SITE + "c")
    via_b = _page("<html><title>C</title><h1>C</h1><a href='/'>Home</a></html>", SITE + "b",
                  final_url=SITE + "c")
    graph = build_site_graph(_snapshot([home, via_a, via_b]), make_deadline(Limits()))["data"]
    assert len(graph["nodes"]) == 2, sorted(graph["nodes"])
    node = graph["nodes"][SITE + "a"]
    assert sorted(node["aliases"]) == [SITE + "b", SITE + "c"]
    # Both links from the homepage land on the same node, and it is no orphan.
    assert node["in_degree"] == 1 and graph["orphans"] == []


def test_a7_orphans_in_an_incomplete_graph_are_not_confirmed_defects():
    from build_site_graph import build_site_graph
    from analyze_engagement import analyze_engagement
    from models import make_deadline, skill_result
    from constants import Limits
    home = _page("<html><title>H</title><h1>Home</h1><a href='/a'>A</a></html>", SITE)
    a = _page("<html><title>A</title><h1>A</h1><a href='/'>Home</a></html>", SITE + "a")
    orphan = _page("<html><title>O</title><h1>Orphan</h1><a href='/'>Home</a></html>", SITE + "orphan")
    broken = _page("<html><body>error</body></html>", SITE + "b", status=503)
    snap = _snapshot([home, a, orphan, broken], {"urls_discovered": 4, "urls_analyzed": 3,
                                                 "urls_never_attempted": 0})
    deadline = make_deadline(Limits())
    graph = build_site_graph(snap, deadline)
    result = analyze_engagement(snap, graph, skill_result("r", metrics={"raw_rendered_gap_pages": []}), deadline)
    orphan_findings = [f for f in result["findings"] if f["check_id"] == "orphan-pages"]
    assert orphan_findings, [f["check_id"] for f in result["findings"]]
    f = orphan_findings[0]
    assert f["status"] == "suspected" and f["finding_type"] == "proactive_improvement"
    assert "could not be read" in f["root_cause"]
    assert result["metrics"]["link_evidence_complete"] is False
    assert result["metrics"]["pages_fetched_but_unread"] == 1


def test_a7_navigation_absence_excludes_js_shell_pages():
    from build_site_graph import build_site_graph
    from analyze_engagement import analyze_engagement
    from models import make_deadline, skill_result
    from constants import Limits
    shells = [_page(f"<html><title>P{i}</title><body><div id='app'></div>"
                    "<script>window.__INITIAL_STATE__={\"nav\":\"Products, pricing and support\"}</script>"
                    "</body></html>", SITE + f"p{i}") for i in range(4)]
    snap = _snapshot(shells, {"urls_discovered": 4, "urls_analyzed": 4, "urls_never_attempted": 0})
    deadline = make_deadline(Limits())
    result = analyze_engagement(snap, build_site_graph(snap, deadline),
                                skill_result("r", metrics={"raw_rendered_gap_pages": []}), deadline)
    ids = {f["check_id"] for f in result["findings"]}
    assert "no-internal-navigation" not in ids, sorted(ids)
    assert "dead-ends" not in ids
    assert result["metrics"]["raw_shell_pages"] == 4


# -------------------------------------------- A8 coverage counts and confidence
def test_a8_analyzed_count_matches_what_the_checks_can_use():
    """Acquisition counted a page truncated at the byte budget as analyzed if it
    had any text, scripts or JSON-LD, while check_helpers.content_pages excluded
    it -- so coverage reported a page the graph and the checks could not use."""
    from dataclasses import replace
    from constants import Limits
    from models import make_deadline
    from acquire_site import acquire_site
    from check_helpers import content_pages
    from fixtures_server import start_server
    url, stop = start_server(sitemap_mode="ok", big_body_bytes=200_000)
    try:
        # A tiny response cap truncates the pages that are fetched.
        limits = replace(Limits(), MAX_RESPONSE_BYTES=600, MAX_PAGES_CRAWLED=4)
        artifacts = acquire_site(url + "/", make_deadline(limits), limits, allow_private_targets=True)
    finally:
        stop()
    reported = artifacts.acquisition_metadata["coverage"]["urls_analyzed"]
    usable = len(content_pages(artifacts, require_features=False))
    assert reported == usable, (reported, usable, [list(p.warnings) for p in artifacts.pages])


def test_a8_absence_confidence_uses_the_pages_the_check_assessed():
    """A sample multiplier must not use twenty unrelated pages to establish the
    strength of a check that could only assess two."""
    from scoring import ScoringContext, apply_scoring, sample_strength
    from models import make_finding
    ctx = ScoringContext(20, 5, {}, SITE)

    def absence(assessed=None):
        f = make_finding(category="ai_discoverability", finding_type="proactive_improvement", severity="low",
                         status="confirmed", confidence=0.9, title="t", root_cause="no description",
                         evidence=[{"type": "x", "description": "d", "urls": [SITE + "a"]}],
                         suggested_action={"summary": "s", "steps": ["a"], "priority": "low", "effort": "low",
                                           "expected_benefit": "b", "verification": "v"},
                         provenance={"skill": "s", "script": "x.py", "rule_id": "missing-description"},
                         affected_pages=[SITE + "a"])
        if assessed is not None:
            f["assessed_pages"] = assessed
            f["assessed_templates"] = 1
        return apply_scoring(f, ctx)

    wide = absence()
    narrow = absence(assessed=2)
    assert wide["severity_rationale"]["sample_strength"] == sample_strength(20, 5)
    assert narrow["severity_rationale"]["sample_strength"] == sample_strength(2, 1)
    assert narrow["confidence"] < wide["confidence"]
    assert "eligible for this check" in narrow["severity_rationale"]["sample_basis"]
    assert "wider than the check" in wide["severity_rationale"]["sample_basis"]


def test_a8_absence_detectors_record_their_denominator():
    from constants import Limits
    from models import make_deadline
    from analyze_metadata import analyze_metadata
    pages = [_page(f"<html><title>Page {i} of the shop</title><h1>P{i}</h1>"
                   f"<p>{'word ' * 60}</p></html>", SITE + f"p{i}") for i in range(4)]
    result = analyze_metadata(_snapshot(pages), make_deadline(Limits()))
    absence = [f for f in result["findings"] if f["check_id"] in ("missing-description", "missing-canonical")]
    assert absence, [f["check_id"] for f in result["findings"]]
    for f in absence:
        assert f["assessed_pages"] == 4, (f["check_id"], f.get("assessed_pages"))


def test_a8_scope_label_publishes_the_basis_it_was_inferred_from():
    """"Site-wide" is a weighting decision, not a measurement. Each route to it
    now says which one it took."""
    from scoring import ScoringContext, apply_scoring
    from models import make_finding
    ctx = ScoringContext(10, 3, {}, SITE)

    def scored(pages, assessed=None):
        f = make_finding(category="engagement", finding_type="defect", severity="medium", status="confirmed",
                         confidence=0.9, title="t", root_cause="orphan pages",
                         evidence=[{"type": "x", "description": "d", "urls": pages}],
                         suggested_action={"summary": "s", "steps": ["a"], "priority": "medium", "effort": "low",
                                           "expected_benefit": "b", "verification": "v"},
                         provenance={"skill": "s", "script": "x.py", "rule_id": "orphan-pages"},
                         affected_pages=pages)
        if assessed is not None:
            f["assessed_pages"] = assessed
        return apply_scoring(f, ctx)

    home = scored([SITE])
    assert home["severity_rationale"]["scope"] == "site-wide"
    assert "entry point" in home["severity_rationale"]["scope_basis"]
    half = scored([SITE + f"p{i}" for i in range(6)])
    assert "prevalence in the sample" in half["severity_rationale"]["scope_basis"]
    one = scored([SITE + "deep"])
    assert one["severity_rationale"]["scope"] == "page"
    whole = scored([SITE + "a", SITE + "b"], assessed=2)
    assert "every one of the 2 page(s) this check assessed" in whole["severity_rationale"]["scope_basis"]
    # A site-level check says so instead of implying a measurement.
    site_level = scored([SITE + "deep"])
    site_level["check_id"] = "robots-block"
    site_level.pop("severity_rationale")
    site_level = apply_scoring(site_level, ctx)
    assert "site-level check" in site_level["severity_rationale"]["scope_basis"]


def test_a8_complete_small_site_is_a_census_not_a_thin_sample():
    """The size heuristic penalised a genuinely complete one-page site. A census
    has no sampling question left, and the basis says which one applies."""
    from execution_summary import overall_confidence
    census = overall_confidence({"pages_analyzed": 1, "pages_discovered": 1, "pages_fetched_attempted": 1,
                                 "pages_never_attempted": 0, "templates_sampled": 1}, "completed")
    assert census["sample_basis"] == "census"
    assert census["components"]["sample_quality"] == 1.0
    assert "not a sample of it" in census["reasons"]["sample_quality"]
    sampled = overall_confidence({"pages_analyzed": 4, "pages_discovered": 40, "pages_fetched_attempted": 4,
                                  "pages_never_attempted": 36, "templates_sampled": 2}, "completed")
    assert sampled["sample_basis"] == "size_heuristic"
    assert "not that it is representative" in sampled["reasons"]["sample_quality"]
    assert "explicit size heuristic" in sampled["reasons"]["sample_quality"]
    # An unknown discovered count is unknown, never read as completeness.
    unknown = overall_confidence({"pages_analyzed": 4, "pages_fetched_attempted": 5, "pages_out_of_scope": 1,
                                  "templates_sampled": 2}, "completed")
    assert unknown["sample_basis"] == "size_heuristic"


# ------------------------------------------------- A9 structured-data semantics
def test_a9_relative_iri_is_valid_jsonld_not_a_malformed_value():
    """JSON-LD 1.1 resolves a relative IRI against the base IRI, so "url": "/"
    and "logo": "/logo.png" are well-formed markup. They used to be reported as
    confirmed malformed values."""
    from schema_rules import invalid_values, consumer_gaps, rule_for
    node = {"@type": "Organization", "name": "X", "url": "/", "logo": "/logo.png", "sameAs": ["/about"]}
    assert invalid_values(node) == []
    # The absolute-URL preference survives, as a named consumer requirement.
    gaps = consumer_gaps(node, rule_for({"Organization"})[1])
    props = {p for p, _, _ in gaps}
    assert {"url", "logo", "sameAs"} <= props
    assert all(consumer and why for _, consumer, why in gaps)


def test_a9_values_that_are_not_web_addresses_are_still_malformed():
    from schema_rules import invalid_values
    bad = {prop for prop, _, _ in invalid_values(
        {"@type": "Organization", "name": "X", "url": "javascript:alert(1)", "logo": "a b.png",
         "image": "data:image/png;base64,AAA", "price": "1,299", "priceCurrency": "rupees",
         "datePublished": "12/10/2026"})}
    assert {"url", "logo", "image", "price", "priceCurrency", "datePublished"} <= bad


def test_a9_rule_selection_is_deterministic_across_hash_seeds():
    """rule_for iterated a set, so for an Organization + LocalBusiness node the
    selected rule -- and with it the address and url requirements -- changed with
    the process hash seed."""
    import subprocess
    script = (
        "import sys; sys.path.insert(0, 'common');"
        "from schema_rules import rule_for;"
        "t, r = rule_for({'Organization', 'LocalBusiness', 'Store'});"
        "print(t, sorted(r['required']), sorted(r['matched_types']))"
    )
    outputs = {subprocess.run([sys.executable, "-c", script], cwd=str(ROOT), capture_output=True,
                              text=True, env={**os.environ, "PYTHONHASHSEED": str(seed)}).stdout.strip()
               for seed in range(1, 8)}
    assert len(outputs) == 1, outputs
    # Both declared types are held to their requirements, deduplicated.
    only = outputs.pop()
    assert only.startswith("LocalBusiness")
    assert "'address'" in only and "'name'" in only


def test_a9_rich_result_eligibility_is_not_a_validity_requirement():
    """"required properties" mixed generic validity with Google's Product rich
    result wanting an offer, rating or review."""
    from schema_rules import rule_for, missing, consumer_gaps
    _, rule = rule_for({"Product"})
    node = {"@type": "Product", "name": "Chisel", "description": "A bench chisel."}
    required, _ = missing(node, rule)
    assert required == []  # the node carries its fact: it is a named product
    gaps = consumer_gaps(node, rule)
    assert [p for p, _, _ in gaps] == ["offers or aggregateRating or review"]
    assert gaps[0][1] == "Google Product rich result"


def test_a9_consumer_requirements_are_reported_as_recommendations():
    from constants import Limits
    from models import make_deadline
    from validate_structured_data import validate_structured_data
    html = ('<html><title>Acme</title><script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Organization","name":"Acme","url":"/",'
            '"logo":"/logo.png"}</script><h1>Acme</h1><p>' + "word " * 80 + '</p></html>')
    result = validate_structured_data(_snapshot([_page(html, SITE)]), make_deadline(Limits()))
    ids = {f["check_id"] for f in result["findings"]}
    assert "schema-invalid-value" not in ids, [f["root_cause"] for f in result["findings"]]
    rec = [f for f in result["findings"] if f["check_id"] == "schema-missing-recommended"]
    assert rec and "Google structured-data consumers" in " ".join(
        e["description"] for f in rec for e in f["evidence"])


def test_a9_price_mismatch_respects_truncation_and_variant_context():
    from dataclasses import replace
    from constants import Limits
    from models import make_deadline, AuditArtifacts, freeze_value
    from transport import Response
    from acquire_site import _extract_page
    from validate_structured_data import validate_structured_data

    def offer_page(limits, body, offers):
        blocks = "".join('<script type="application/ld+json">%s</script>' % o for o in offers)
        html = f'<html><title>Chisel</title>{blocks}<h1>Chisel</h1><p>{body}</p></html>'
        r = Response(200, {"Content-Type": "text/html"}, html.encode(), SITE + "product")
        r.network_duration_ms = 10
        return _extract_page(SITE + "product", r, 10, limits)

    one = '{"@context":"https://schema.org","@type":"Offer","price":"999","priceCurrency":"INR"}'
    # Complete text, one price context, price nowhere on the page: a contradiction.
    page = offer_page(Limits(), "Our price is Rs 1299 including tax. " * 5, [one])
    result = validate_structured_data(_snapshot([page]), make_deadline(Limits()))
    mism = [f for f in result["findings"] if f["check_id"] == "schema-visible-mismatch"]
    assert mism and mism[0]["status"] == "confirmed"

    # Same markup, but the page text was truncated at the capture limit: a price
    # absent from the text we could read is not proof the page omits it.
    tiny = replace(Limits(), VISIBLE_TEXT_MAX_CHARS=120)
    page = offer_page(tiny, "Our price is Rs 1299 including tax. " * 30, [one])
    assert page.features["visible_text_complete"] is False
    result = validate_structured_data(_snapshot([page]), make_deadline(Limits()))
    mism = [f for f in result["findings"] if f["check_id"] == "schema-visible-mismatch"]
    assert mism and mism[0]["status"] == "suspected"
    assert "truncated" in mism[0]["evidence"][0]["description"]

    # Several declared prices: the odd one out may be a variant the page does not show.
    two = ['{"@context":"https://schema.org","@type":"Offer","price":"999","priceCurrency":"INR"}',
           '{"@context":"https://schema.org","@type":"Offer","price":"1299","priceCurrency":"INR"}']
    page = offer_page(Limits(), "Our price is Rs 1299 including tax. " * 5, two)
    result = validate_structured_data(_snapshot([page]), make_deadline(Limits()))
    mism = [f for f in result["findings"] if f["check_id"] == "schema-visible-mismatch"]
    assert mism and mism[0]["status"] == "suspected"
    assert "variant" in mism[0]["evidence"][0]["description"]


# ---------------------------------------------------------- A10 text decoding
def test_a10_non_text_codec_labels_are_ignored_not_fatal():
    """codecs.lookup is not a charset validator: it resolves rot13, base64, hex,
    quopri, uu, bz2 and zlib, none of which bytes.decode can use. A
    Content-Type of charset=rot13 used to raise LookupError and turn an ordinary
    page into a transport failure."""
    from transport import decode_body, _web_charset
    for label in ("rot13", "rot-13", "base64", "hex", "quopri", "uu", "bz2", "zlib", "nonsense-7"):
        assert _web_charset(label) is None, label
        # The body is read with the next source of truth, exactly as a browser does.
        assert decode_body(b"<html>hello</html>", f"text/html; charset={label}") == "<html>hello</html>"


def test_a10_real_web_encodings_still_resolve():
    import codecs
    from transport import _web_charset, _WEB_ENCODINGS
    assert _web_charset("Shift_JIS") == "shift_jis"
    assert _web_charset("windows-1251") == "cp1251"
    assert _web_charset("EUC-KR") == "euc_kr"
    assert _web_charset("gb18030") == "gb18030"
    # WHATWG: ISO-8859-1 and US-ASCII mean windows-1252.
    assert _web_charset("iso-8859-1") == "cp1252" and _web_charset("us-ascii") == "cp1252"
    # Every name in the whitelist is a real codec, so a typo cannot silently
    # shrink it.
    for name in _WEB_ENCODINGS:
        assert codecs.lookup(name).name == name or codecs.lookup(name)


def test_a10_malformed_label_regressions_still_hold():
    from transport import decode_body
    # A mislabelled legacy page is read as windows-1252 rather than filled with
    # replacement characters.
    body = ("<html><body>" + "caf\xe9 " * 40 + "</body></html>").encode("cp1252")
    assert "caf\xe9" in decode_body(body, "text/html; charset=utf-8")
    # A byte order mark wins over a conflicting declared charset.
    assert decode_body("﻿<html>x</html>".encode("utf-8-sig"), "text/html; charset=iso-8859-5") \
        .lstrip("﻿") == "<html>x</html>"
    # An empty or absent label falls through to UTF-8.
    assert decode_body("<html>é</html>".encode(), "") == "<html>é</html>"
    assert decode_body("<html>é</html>".encode(), "text/html; charset=") == "<html>é</html>"


def test_a10_encoding_provenance_is_recorded():
    from transport import decode_body, Response
    note = {}
    decode_body(b"<html>x</html>", "text/html; charset=windows-1251", note)
    assert note["encoding"] == "cp1251" and note["source"] == "http_content_type"
    note = {}
    decode_body(b"<html>x</html>", "text/html; charset=rot13", note)
    assert note["ignored_label"] == "rot13" and note["source"] == "default"
    note = {}
    decode_body(b'<meta charset="shift_jis"><html>x</html>', "text/html", note)
    assert note["source"] == "meta_charset" and note["encoding"] == "shift_jis"
    r = Response(200, {"Content-Type": "text/html; charset=utf-8"}, b"<html>hi</html>", SITE)
    assert r.text == "<html>hi</html>"
    assert r.encoding_provenance["encoding"] == "utf-8"


def test_a10_binary_bodies_are_not_decoded():
    from transport import Response
    pdf = Response(200, {"Content-Type": "application/pdf"}, b"%PDF-1.4 \x80\x81\xfe", SITE + "a.pdf")
    assert pdf.text == "" and pdf.encoding_provenance["source"] == "binary_content_type"
    png = Response(200, {"Content-Type": "image/png"}, b"\x89PNG\r\n\x1a\n\xff", SITE + "a.png")
    assert png.text == ""
    # An XML-ish body is still text.
    xml = Response(200, {"Content-Type": "application/xml"}, b"<urlset></urlset>", SITE + "sitemap.xml")
    assert xml.text == "<urlset></urlset>"


# ------------------------------------------------- A11 crawler product tokens
def test_a11_applebot_group_does_not_apply_to_applebot_extended():
    """Substring matching applied an `Applebot` group to Applebot-Extended, so a
    site that blocks Apple's search crawler appeared to have opted out of AI
    training too -- two different tokens with two different purposes."""
    from robots_policy import RobotsPolicy
    rp = RobotsPolicy("User-agent: *\nAllow: /\n\nUser-agent: Applebot\nDisallow: /\n")
    assert rp.can_fetch("Applebot", "https://x.example/a") is False
    assert rp.can_fetch("Applebot-Extended", "https://x.example/a") is True
    # And the other way round: an Extended-only block says nothing about search.
    rp = RobotsPolicy("User-agent: *\nAllow: /\n\nUser-agent: Applebot-Extended\nDisallow: /\n")
    assert rp.can_fetch("Applebot", "https://x.example/a") is True
    assert rp.can_fetch("Applebot-Extended", "https://x.example/a") is False


def test_a11_equivalent_prefix_cases_stay_separate():
    from robots_policy import RobotsPolicy
    for blocked, others in (("Claude-SearchBot", ("Claude-User", "ClaudeBot")),
                            ("Google-Extended", ("Googlebot",)),
                            ("Googlebot", ("Google-Extended",)),
                            ("Perplexity-User", ("PerplexityBot",)),
                            ("ChatGPT-User", ("OAI-SearchBot", "GPTBot"))):
        rp = RobotsPolicy(f"User-agent: *\nAllow: /\n\nUser-agent: {blocked}\nDisallow: /\n")
        assert rp.can_fetch(blocked, "https://x.example/a") is False, blocked
        for other in others:
            assert rp.can_fetch(other, "https://x.example/a") is True, (blocked, other)


def test_a11_product_token_extraction_and_own_user_agent():
    from robots_policy import RobotsPolicy, product_token
    from transport import USER_AGENT
    assert product_token("Applebot-Extended") == "applebot-extended"
    assert product_token(USER_AGENT) == "brandaireadinessauditbot"
    assert product_token("Googlebot/2.1") == "googlebot"
    assert product_token("") == ""
    # A group naming this audit's own token is still honoured.
    rp = RobotsPolicy("User-agent: BrandAIReadinessAuditBot\nDisallow: /private\n")
    assert rp.can_fetch(USER_AGENT, "https://x.example/private") is False
    assert rp.can_fetch(USER_AGENT, "https://x.example/public") is True


def test_a11_wildcard_and_crawl_delay_follow_the_same_token_rule():
    from robots_policy import RobotsPolicy
    rp = RobotsPolicy("User-agent: *\nCrawl-delay: 2\nDisallow: /admin\n\n"
                      "User-agent: Applebot\nCrawl-delay: 5\nDisallow: /\n")
    # Applebot takes its own group's delay; Applebot-Extended falls to the wildcard.
    assert rp.crawl_delay("Applebot") == 5.0
    assert rp.crawl_delay("Applebot-Extended") == 2.0
    assert rp.can_fetch("Applebot-Extended", "https://x.example/admin") is False
    assert rp.can_fetch("Applebot-Extended", "https://x.example/pricing") is True
