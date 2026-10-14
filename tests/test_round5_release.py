"""test_round5_release.py -- Round 5 plan, phase 7 gaps in the regression matrix.

  - T7.1 final merge and Markdown: no request, and the actions, passes and
    limitations of the merged report agree with each other and with the
    Markdown rendering.
  - T7.3 the normal workflow acquires the site once: the merge sends nothing to
    the target. One controlled before/after fixture: fixing a real defect removes
    its finding, it moves to the passed checks, and the other passed checks stay.

The rest of the matrix is covered by test_round5_observations.py,
test_round5_agent_handoff.py and test_round5_budget_reports.py; see
skills/audit-orchestrator/references/validation.md. Every site is served from
127.0.0.1; nothing here touches the network.
"""
import json
from dataclasses import replace
import os
import socket
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from archetype_sites import ALLOW_ALL, serve
from constants import Limits
from report_markdown import render
from test_precision_traps import _OFFLINE_ENV

LIMITS = Limits()
WORDS = "<p>" + "Plain words about the offer and what it does for the people who use it every day. " * 15 + "</p>"
NAV = '<nav><a href="/">Home</a> <a href="/about">About Acme</a> <a href="/services">Services</a></nav>'


def _html(title, body, description="Acme repairs bicycles in Leeds."):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{title}</title><meta name="description" content="{description} {title}">'
            f"</head><body>{NAV}{body}</body></html>")


def _site(h1_on_services):
    services = ("<main><h1>Our services</h1>" if h1_on_services else "<main>") + WORDS + "</main>"
    return {"robots": ALLOW_ALL,
            "pages": {"/": _html("Acme Bicycles", "<main><h1>Acme Bicycles</h1>" + WORDS + "</main>"),
                      "/about": _html("About Acme", "<main><h1>About Acme</h1><p>Acme is a bicycle repair "
                                                    "shop in Leeds, founded in 2004, serving commuters.</p>"
                                      + WORDS + "</main>"),
                      "/services": _html("Services", services)}}


def _audit(site):
    from run_audit import run_audit_with_evidence
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    base, stop, seen = serve(site)
    try:
        report, packet = run_audit_with_evidence(base + "/", LIMITS, allow_private_targets=True)
        return base, stop, seen, report, packet
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _ids(report, key="check_id"):
    return {f.get(key) for f in report["findings"]}


def test_fixing_a_defect_removes_its_finding_and_keeps_positive_controls():
    _, stop, _, before, _ = _audit(_site(h1_on_services=False))
    stop()
    _, stop, _, after, _ = _audit(_site(h1_on_services=True))
    stop()
    assert "h1" in _ids(before) and "h1" not in _ids(after)
    passed_before = {w["check"] for w in before["whats_working"]}
    passed_after = {w["check"] for w in after["whats_working"]}
    # The repaired check now passes, and every check that passed before still does.
    assert "h1" not in passed_before and "h1" in passed_after
    assert passed_before <= passed_after
    assert {"titles", "meta-descriptions", "language", "viewport"} <= passed_after


def test_workflow_acquires_once_and_the_merged_report_is_consistent(tmp_path, monkeypatch):
    from run_audit import main
    base, stop, seen, report, packet = _audit(_site(h1_on_services=False))
    try:
        requests_after_audit = len(seen)
        # Every request the site answered was charged to the audit's one ledger
        # (the ledger also holds the HTTPS probe to port 443, which nothing answers here).
        assert 0 < requests_after_audit <= report["coverage"]["network_budget"]["pools"]["site"]["requests"]
        about = next(p for p in packet["pages"] if p["requested_url"].endswith("/about"))
        envelope = {"schema_version": "1.1", "audit_id": report["audit_id"],
                    "snapshot_sha256": report["snapshot_sha256"], "packet_sha256": report["packet_sha256"],
                    "capabilities": {"local_reading": True, "search": False, "vision": False},
                    "checks": [{"check": "AG-01", "outcome": "pass", "source_refs": [about["evidence_id"]], "observation": {"passage": packet["focus"]["ag01"]["opening_passage"]},
                                "reason": "The About passage names Acme, its bicycle repair service and its "
                                          "local market."}]}
        files = {}
        for name, data in (("report", report), ("packet", packet), ("envelope", envelope)):
            files[name] = tmp_path / f"{name}.json"
            files[name].write_text(json.dumps(data), encoding="utf-8")
        final_path = tmp_path / "final.json"

        def refuse(*args, **kwargs):
            raise AssertionError("the merge opened a connection")
        monkeypatch.setattr(socket, "create_connection", refuse)
        monkeypatch.setattr(socket.socket, "connect", refuse)
        assert main(["--from-report", str(files["report"]), "--agent-findings", str(files["envelope"]),
                     "--evidence", str(files["packet"]), "--out", str(final_path), "--quiet"]) == 0
        # The merge made no request: the site saw nothing after the one acquisition.
        assert len(seen) == requests_after_audit
    finally:
        stop()
    final = json.loads(final_path.read_text(encoding="utf-8"))
    ids = {f["id"] for f in final["findings"]}
    reported = {c for f in final["findings"] for c in (f.get("check_ids") or [f.get("check_id")])}
    # Actions point at findings in the report; start_here, if any, is a confirmed defect.
    assert {a["finding_id"] for a in final["top_actions"]} <= ids
    for action in final["top_actions"]:
        finding = next(f for f in final["findings"] if f["id"] == action["finding_id"])
        assert finding["finding_type"] == "defect"
        if action["start_here"]:
            assert finding["status"] == "confirmed"
    # A passed check is never also reported.
    assert not any(set(w.get("check_ids") or ()) & reported for w in final["whats_working"])
    # A snippet sits only on a finding whose action it belongs to.
    for f in final["findings"]:
        snippet = (f.get("suggested_action") or {}).get("snippet")
        if snippet:
            assert snippet.get("code")
    # AG-01 assessed; the checks with no capability keep their limitation lines.
    stage = final["coverage"]["agent_stage"]
    assert stage["checks_assessed"] == ["AG-01"] and stage["checks"]["AG-04"]["outcome"] == "not_assessed"
    assert any("AG-04" in line for line in final["limitations"])
    assert final["coverage"]["agent_corroboration"]["workflow_timing"]["within_workflow_target"]
    md = render(final)
    assert "## Agent checks" in md and "AG-01 About-page concreteness | passed" in md
    for action in final["top_actions"]:
        assert action["finding_id"] in md
    for line in final["limitations"]:
        assert line[:40].replace("_", "\\_") in md or line[:40] in md


# ---------------------------------------------------------------------------
# Phase 8 package checks
# ---------------------------------------------------------------------------

def _frontmatter(path):
    import re
    text = open(path, encoding="utf-8").read()
    assert text.startswith("---\n"), path
    block = text.split("---\n", 2)[1]
    name = re.search(r"^name:\s*(\S+)\s*$", block, re.M).group(1)
    folded = re.search(r"^description:\s*>-?\s*\n((?:[ \t]+.*\n)+)", block, re.M)
    description = " ".join((folded.group(1) if folded else re.search(r"^description:\s*(.+)$", block, re.M).group(1))
                           .split())
    return name, description


def test_package_has_command_skill_five_contracts_and_one_native_entrypoint():
    manifest = json.load(open(os.path.join(_ROOT, "marketplace.json"), encoding="utf-8"))
    skills = manifest["skills"]
    assert {s['id'] for s in skills} == {'audit', 'audit-orchestrator', 'crawl-render-audit',
                                       'freshness-corroboration', 'engagement-audit', 'entity-corroboration-agent'}
    assert [s['id'] for s in skills if s.get('entrypoint')] == ['audit-orchestrator']
    for skill in skills:
        name, description = _frontmatter(os.path.join(_ROOT, skill["path"], "SKILL.md"))
        assert name == skill["id"] == os.path.basename(skill["path"])
        assert 0 < len(description) <= 1024, (name, len(description))


def test_release_version_matches_the_manifest():
    import agent_evidence
    manifest = json.load(open(os.path.join(_ROOT, "marketplace.json"), encoding="utf-8"))
    assert agent_evidence.RELEASE_VERSION == manifest["version"]
    assert agent_evidence.code_version().startswith(manifest["version"] + "+")


# ---------------------------------------------------------------------------
# T7.2 repairs from the development review
# ---------------------------------------------------------------------------

def test_a_po_box_is_not_physical_location_evidence():
    # Development review: a mailing address (PO Box) was reported as a physical
    # location without markup. A street address still is.
    from analyze_context_signals import analyze_context_signals
    from models import make_deadline
    from test_precision_traps import SITE, page, snapshot

    def location_findings(address):
        contact = page(f"<main><h1>Contact</h1>{WORDS}<address>{address}</address></main>",
                       url=SITE + "/contact")
        result = analyze_context_signals(snapshot(contact), make_deadline(LIMITS))
        return [f for f in result["findings"] if f["provenance"]["rule_id"] == "location-markup-missing"]

    assert location_findings("Fixture Pty Ltd, PO Box 234, Collins St West, Victoria 8007, Australia") == []
    assert location_findings("Fixture Ltd, 12 High Street, Leeds LS1 4AB, United Kingdom")


def test_one_priced_page_does_not_make_every_product_path_a_shop():
    # Development review: on a news site, one article quoting a price made 36
    # pages typed "product" count as shop pages without saved items.
    from analyze_context_retention import analyze_context_retention
    from models import make_deadline
    from test_precision_traps import SITE, page, snapshot

    def rules(*pages):
        result = analyze_context_retention(snapshot(*pages), make_deadline(LIMITS))
        return {f["provenance"]["rule_id"] for f in result["findings"]}

    articles = [page(f"<main><h1>Story {i}</h1>{WORDS}</main>", url=f"{SITE}/products/story-{i}") for i in range(4)]
    priced = page("<main><h1>Art fair</h1>" + WORDS + "<p>The piece is for sale at $4,500.</p></main>",
                  url=SITE + "/products/art-fair")
    assert "context-retention-missing" not in rules(*articles, priced)
    shop = [page(f"<main><h1>Bag {i}</h1>{WORDS}<p>Price: $89.00</p><button>Add to cart</button></main>",
                 url=f"{SITE}/products/bag-{i}") for i in range(3)]
    assert "context-retention-missing" in rules(*shop)


# ---------------------------------------------------------------------------
# T7.2 repairs from the first fresh holdout (that holdout is now development
# material; the release was scored on a second fresh holdout)
# ---------------------------------------------------------------------------

def _acquire(site, limits=LIMITS):
    from acquire_site import acquire_site
    from models import make_deadline
    base, stop, seen = serve(site)
    try:
        return base, acquire_site(base + "/", make_deadline(limits), limits, allow_private_targets=True), seen
    finally:
        stop()


def test_an_immediate_meta_refresh_root_is_followed_to_its_page():
    # Holdout: a docs root that is only <meta http-equiv="refresh" content="0;url=/en/start/">
    # left the audit with no readable page.
    site = {"robots": ALLOW_ALL,
            "pages": {"/": '<!DOCTYPE html><meta http-equiv="refresh" content="0;url=/en/start/">',
                      "/en/start/": _html("Getting started", "<main><h1>Getting started</h1>" + WORDS + "</main>"),
                      "/about": _html("About Acme", "<main><h1>About</h1>" + WORDS + "</main>"),
                      "/services": _html("Services", "<main><h1>Services</h1>" + WORDS + "</main>")}}
    base, artifacts, _ = _acquire(site)
    analyzed = {p.url[len(base):] for p in artifacts.pages}
    assert "/en/start/" in analyzed and "/" not in analyzed
    meta = artifacts.acquisition_metadata
    assert meta["url_aliases"][base + "/"] == base + "/en/start/"
    assert any(o["scope"] == "meta_refresh_redirect" for o in meta["observations"])
    # A slow refresh, or one to another origin, is page content, not a redirect.
    from acquire_site import meta_refresh_target
    from test_precision_traps import SITE, page
    slow = page('<meta http-equiv="refresh" content="30;url=/next">', url=SITE + "/")
    away = page('<meta http-equiv="refresh" content="0;url=https://other.example/">', url=SITE + "/")
    body = '<meta http-equiv="refresh" content="30;url=/next">'
    assert meta_refresh_target(slow, body, SITE) is None
    assert meta_refresh_target(away, '<meta http-equiv="refresh" content="0;url=https://other.example/">',
                               SITE) is None


def test_a_long_crawl_delay_fetches_pages_before_the_sitemap_and_llms_txt(monkeypatch):
    # Holdout: a 30-second crawl delay spent the stage on the sitemap and llms.txt
    # and the start URL was never fetched.
    import acquire_site
    monkeypatch.setattr(acquire_site, "_SLOW_CRAWL_DELAY_S", 0.5)
    site = {"robots": "User-agent: *\nCrawl-delay: 1\nDisallow:\n",
            "pages": {"/": _html("Acme Bicycles", "<main><h1>Acme Bicycles</h1>" + WORDS + "</main>")}}
    _, artifacts, seen = _acquire(site, replace(LIMITS, MAX_PAGES_CRAWLED=1))
    paths = [p for _, p in seen]
    assert paths[:2] == ["/robots.txt", "/"]
    assert "/sitemap.xml" not in paths and "/llms.txt" not in paths
    assert artifacts.sitemap_data["status"] == "not_checked" and artifacts.llms_txt_data["status"] == "not_checked"
    assert any("not checked, not absent" in w for w in artifacts.warnings)


def test_brand_definition_never_searches_for_a_url_as_the_brand_name():
    # Holdout: Organization markup named the brand by its URL, and the check
    # reported that no sentence named "https://www.example...".
    from analyze_answer_content import analyze_answer_content
    from models import make_deadline
    from test_precision_traps import SITE, page, snapshot
    home = page("<main><h1>Welcome</h1>" + WORDS + "</main>", url=SITE + "/")

    def rules(name):
        identity = {"data": {"canonical_name": name, "confidence": 0.9}}
        result = analyze_answer_content(snapshot(home), identity, make_deadline(LIMITS))
        return {f["provenance"]["rule_id"] for f in result["findings"]}

    assert "brand-definition" not in rules("https://www.fixture.example")
    assert "brand-definition" not in rules("fixture.example")
    assert "brand-definition" in rules("Fixture Bakery")


# ---------------------------------------------------------------------------
# Failures found by the second fresh holdout, repaired after it was scored.
# They have not been re-scored on unseen sites.
# ---------------------------------------------------------------------------

def test_checking_connection_403_is_a_challenge_not_a_broken_page():
    from bot_challenge import challenge_signals
    body = "<html><head><title>Checking connection</title></head><body>Checking connection...<script>challenge()</script>"
    assert challenge_signals(403, {"Server": "Varnish"}, body, "Checking connection", 25) == ["challenge_title"]
    # On a 200 page the same title alone is not a challenge.
    assert challenge_signals(200, {}, body, "Checking connection", 25) == []


def test_html_soft_404_for_both_llms_files_is_not_a_malformed_llms_txt():
    from check_llms_txt import check_llms_txt
    from models import make_deadline, freeze_value
    from test_precision_traps import SITE, page, snapshot
    from dataclasses import replace as dc_replace
    artifacts = snapshot(page("<main><h1>Docs</h1>" + WORDS + "</main>"))
    soft = {"present": False, "status": "malformed", "full": {"present": False, "status": "malformed",
                                                             "served_html": True}}
    result = check_llms_txt(dc_replace(artifacts, llms_txt_data=freeze_value(soft)), make_deadline(LIMITS))
    assert "llms-txt-invalid" not in {f["provenance"]["rule_id"] for f in result["findings"]}


def test_shipped_examples_replay_offline_to_the_shipped_final_report(monkeypatch):
    # examples/ holds one complete run of the workflow. Replaying its merge with
    # no network gives the same agent stage and findings as the shipped final report.
    from merge_agent_stage import merge_agent_envelope
    ex = os.path.join(_ROOT, "examples")
    load = lambda name: json.load(open(os.path.join(ex, name), encoding="utf-8"))
    base, packet, envelope, final = (load(n) for n in ("sample-report.json", "evidence.json",
                                                       "agent-outcomes.json", "final-report.json"))
    assert base["audit_id"] == packet["audit_id"] == envelope["audit_id"] == final["audit_id"]
    assert base["snapshot_sha256"] == packet["snapshot_sha256"] == final["snapshot_sha256"]

    def refuse(*args, **kwargs):
        raise AssertionError("the replay opened a connection")
    monkeypatch.setattr(socket, "create_connection", refuse)
    replayed = merge_agent_envelope(base, envelope, packet)
    for key in ("submission_status", "assessment_status", "checks_assessed", "checks"):
        assert replayed["coverage"]["agent_stage"][key] == final["coverage"]["agent_stage"][key]
    assert [f["check_id"] for f in replayed["findings"]] == [f["check_id"] for f in final["findings"]]
    md = open(os.path.join(ex, "final-report.md"), encoding="utf-8").read()
    assert "## Agent checks" in md and final["site"] in md
