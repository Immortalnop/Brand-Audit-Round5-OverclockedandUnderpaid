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
