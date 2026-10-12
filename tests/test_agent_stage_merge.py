"""test_agent_stage_merge.py -- the agent stage (AG-01 to AG-06) wired into the entrypoint.

  - load_agent_findings reads UTF-8, UTF-8 with a BOM and UTF-16, and refuses
    files that are not a list of findings, with a reason.
  - Agent entries are rebuilt through the finding factory with bounded, cleaned
    fields; affected_pages name pages of the audited site only.
  - merge_findings.fold_into joins an agent finding to the script finding that
    already reports its check, never lowering severity and never changing its
    inputs.
  - run_audit.py --from-report R --agent-findings A merges into a saved report
    with no request, and gives the same findings as a live audit run with the
    same agent findings.

Every site is served from 127.0.0.1 (tests/fixtures_server.py); nothing here
touches the network.
"""
import copy
import json
import os
import socket
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

import ingest_agent_findings as ingest
from constants import Limits
from execution_summary import AGENT_STAGE_LIMITATION_MARKS
from fixtures_server import start_server
from merge_agent_stage import ReportMergeError, merge_agent_findings
from merge_findings import fold_into
from models import make_finding

LIMITS = Limits()
_OFFLINE_ENV = {"SEARCH_API_URL": "", "SEARCH_API_KEY": "", "PAGESPEED_API_KEY": "", "FIELD_VITALS_LOOKUP": "0",
                "AGENT_FINDINGS_PATH": "", "OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0",
                "ENABLE_RENDERING": "0", "AUDIT_PROGRESS": "0"}


def _agent_items(base):
    """One entry per kind of outcome: a vision reading that joins a script
    finding, a contradiction with no script counterpart, a review profile
    named only in evidence, an unknown check and a non-object."""
    return [
        {"check": "AG-04", "affected_pages": [base + "/pricing"],
         "evidence": [{"type": "agent_vision", "description": "price-list.png shows Basic $19 and Pro $29",
                       "urls": [base + "/img/price-list.png"]}]},
        {"check": "AG-03", "evidence": "A directory listing gives a different founding year than the About page."},
        {"check": "AG-06", "status": "suspected", "affected_pages": ["https://www.trustpilot.com/review/acme"],
         "evidence": [{"description": "A Trustpilot profile exists but the site does not link it",
                       "urls": ["https://www.trustpilot.com/review/acme"]}]},
        {"check": "AG-99", "evidence": "unknown check"},
        "not an object",
    ]


def _audit(env):
    from run_audit import run_audit
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    url, stop = start_server(media=True)
    try:
        return url, run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture(scope="module")
def media_report():
    """(base URL, report) of the media fixture, audited once without agent findings."""
    return _audit(_OFFLINE_ENV)


def _agent_lines(lines):
    return [line for line in lines if any(mark in line for mark in AGENT_STAGE_LIMITATION_MARKS)]


def _shape(report):
    return sorted((f["check_id"], f["status"], f["severity"], tuple(f["affected_pages"]), len(f["evidence"]))
                  for f in report["findings"])


# ---------------------------------------------------------------- loading

@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16"])
def test_load_reads_utf8_bom_and_utf16(tmp_path, encoding):
    path = tmp_path / "ag.json"
    path.write_text(json.dumps({"findings": [{"check": "AG-01"}]}), encoding=encoding)
    assert ingest.load_agent_findings(str(path)) == [{"check": "AG-01"}]


@pytest.mark.parametrize("body", ["{not json", json.dumps({"findings": "x"}), json.dumps("text"), ""])
def test_load_refuses_unusable_files_with_a_reason(tmp_path, body):
    path = tmp_path / "ag.json"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(ingest.AgentFindingsError):
        ingest.load_agent_findings(str(path))


def test_load_refuses_missing_and_oversized_files(tmp_path, monkeypatch):
    with pytest.raises(ingest.AgentFindingsError, match="no such file"):
        ingest.load_agent_findings(str(tmp_path / "missing.json"))
    path = tmp_path / "big.json"
    path.write_text(json.dumps([{"check": "AG-01"}]), encoding="utf-8")
    monkeypatch.setattr(ingest, "MAX_FILE_BYTES", 5)
    with pytest.raises(ingest.AgentFindingsError, match="larger than"):
        ingest.load_agent_findings(str(path))


def test_live_stage_still_skips_a_bad_file_gracefully(tmp_path, monkeypatch):
    path = tmp_path / "ag.json"
    path.write_text(json.dumps({"findings": 3}), encoding="utf-8")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", str(path))
    result = ingest.ingest_agent_findings(type("A", (), {"pages": ()})(), None, None)
    assert result["status"] == "insufficient_evidence" and result["metrics"]["agent_stage"] == "not_supplied"


# ---------------------------------------------------------------- cleaning

def test_entries_are_cleaned_and_bounded():
    site = "https://shop.example"
    [finding] = ingest.build_agent_findings([{
        "check": "ag-04", "title": "T " * 400,
        "affected_pages": [site + "/menu", "https://other.example/menu", "javascript:alert(1)", 7],
        "evidence": [{"description": "menu.jpg lists prices", "urls": "https://shop.example/menu"},
                     {"type": "x" * 200, "text": "second", "urls": [site + "/a.jpg", 5, "ftp://x"]},
                     {"note": "no description and no urls"}, "plain string"],
        "suggested_action": {"summary": 12, "steps": ["Write the prices as text", None, ""], "effort": "huge"},
    }], origin=site)
    assert finding["check_id"] == "facts-in-images"
    assert finding["affected_pages"] == [site + "/menu"]
    assert len(finding["title"]) <= 300
    # A string where a list belongs is not read character by character.
    assert finding["evidence"][0] == {"type": "agent_observation", "description": "menu.jpg lists prices"}
    assert finding["evidence"][1]["urls"] == [site + "/a.jpg"] and len(finding["evidence"][1]["type"]) <= 60
    assert len(finding["evidence"]) == 2
    action = finding["suggested_action"]
    assert action["steps"] == ["Write the prices as text"] and action["effort"] == "medium"
    assert action["summary"] == ingest._AG_RULES["AG-04"]["summary"]


def test_third_party_urls_stay_in_evidence_not_affected_pages():
    [finding] = ingest.build_agent_findings([{
        "check": "AG-06", "evidence": [{"description": "Profile found", "urls": ["https://www.g2.com/p/acme"]}]}],
        origin="https://acme.example")
    assert finding["affected_pages"] == []
    assert finding["evidence"][0]["urls"] == ["https://www.g2.com/p/acme"]


def test_at_most_max_agent_findings_are_read():
    items = [{"check": "AG-02", "evidence": f"note {i}"} for i in range(ingest.MAX_AGENT_FINDINGS + 10)]
    assert len(ingest.build_agent_findings(items)) == ingest.MAX_AGENT_FINDINGS


# ---------------------------------------------------------------- folding

def _finding(check_id, pages, severity="low", status="suspected", confidence=0.6, skill="crawl-render-audit"):
    return make_finding(
        category="ai_discoverability", finding_type="proactive_improvement", severity=severity, status=status,
        confidence=confidence, title=f"{check_id} title", root_cause=f"cause of {check_id} " + " ".join(pages),
        evidence=[{"type": "snapshot_observation", "description": f"{check_id} on {p}", "urls": [p]} for p in pages],
        affected_pages=pages,
        suggested_action={"summary": "s", "steps": ["a"], "priority": severity, "effort": "low",
                          "expected_benefit": "b", "verification": "v"},
        provenance={"skill": skill, "script": "x.py", "rule_id": check_id})


def test_fold_joins_the_same_check_sharing_most_pages_and_keeps_inputs():
    a = _finding("facts-in-images", ["https://s.example/"])
    b = _finding("facts-in-images", ["https://s.example/pricing"])
    other = _finding("no-jsonld", ["https://s.example/pricing"])
    vision = _finding("facts-in-images", ["https://s.example/pricing"], severity="medium", status="confirmed",
                      confidence=0.7, skill="entity-corroboration-agent")
    before = copy.deepcopy([a, b, other, vision])
    out, folded = fold_into([a, b, other], [vision])
    assert [a, b, other, vision] == before
    assert folded == 1 and len(out) == 3
    joined = out[1]
    assert joined["title"] == b["title"] and joined["status"] == "confirmed" and joined["severity"] == "medium"
    assert joined["suggested_action"]["priority"] == "medium"
    assert [p.get("skill") for p in joined["provenance"]["contributing_skills"]] == \
        ["crawl-render-audit", "entity-corroboration-agent"]
    assert joined["check_ids"] == ["facts-in-images"] and len(joined["evidence"]) == 1
    assert out[0] == a


def test_fold_never_lowers_severity_and_less_confident_addition_keeps_status():
    base = _finding("review-platform-missing", [], severity="medium", status="confirmed", confidence=0.9)
    weak = _finding("review-platform-missing", [], severity="low", status="suspected", confidence=0.55)
    [joined], folded = fold_into([base], [weak])
    assert folded == 1 and joined["severity"] == "medium" and joined["status"] == "confirmed"
    assert joined["confidence"] == 0.9


def test_unmatched_addition_is_appended_with_check_ids():
    out, folded = fold_into([_finding("no-jsonld", ["https://s.example/"])],
                            [_finding("kg-namesake-ambiguity", [], skill="entity-corroboration-agent")])
    assert folded == 0 and out[-1]["check_ids"] == ["kg-namesake-ambiguity"]


# ---------------------------------------------------------------- merge-only mode

def test_merge_folds_adds_and_refreshes_the_report(media_report):
    base, report = media_report
    original = copy.deepcopy(report)
    merged = merge_agent_findings(report, _agent_items(base), source="ag.json")
    assert report == original
    info = merged["coverage"]["agent_corroboration"]
    assert info["findings_supplied"] == 5 and info["findings_ingested"] == 3
    assert info["findings_folded_into_existing"] == 2 and info["findings_added"] == 1
    assert merged["coverage"]["agent_corroboration_stage"] == "ingested"
    images = [f for f in merged["findings"] if f["check_id"] == "facts-in-images"]
    assert len(images) == len([f for f in report["findings"] if f["check_id"] == "facts-in-images"])
    assert any("Basic $19" in e["description"] for f in images for e in f["evidence"])
    [contradiction] = [f for f in merged["findings"] if f["check_id"] == "independent-contradiction"]
    assert contradiction["severity"] == "high" and contradiction["status"] == "confirmed"
    assert contradiction["coverage"]["pages_analyzed"] == report["coverage"]["pages_analyzed"]
    assert not any("trustpilot" in p for f in merged["findings"] for p in f["affected_pages"])
    # Numbering, references and summary agree with the new findings.
    assert [f["id"] for f in merged["findings"]] == [f"F-{i:03d}" for i in range(1, len(merged["findings"]) + 1)]
    ids = {f["id"] for f in merged["findings"]}
    assert all(r["finding_id"] in ids for r in merged["recommendations"] if "finding_id" in r)
    assert all(t["finding_id"] in ids for t in merged["top_actions"])
    assert merged["summary"]["total_findings"] == len(merged["findings"]) == len(report["findings"]) + 1
    assert merged["summary"]["high"] == report["summary"]["high"] + 1
    # The stage is no longer reported as missing.
    assert _agent_lines(report["limitations"]) and not _agent_lines(merged["limitations"])
    assert ingest.NOT_SUPPLIED_WARNING in report["warnings"]
    assert ingest.NOT_SUPPLIED_WARNING not in merged["warnings"]
    assert merged["confidence"] == report["confidence"]


def test_empty_merge_changes_nothing_but_the_stage(media_report):
    _, report = media_report
    merged = merge_agent_findings(report, [])
    for key in ("findings", "recommendations", "top_actions", "quick_wins", "whats_working", "summary"):
        assert merged[key] == report[key], key


def test_merge_refuses_a_second_merge_an_empty_audit_and_a_non_report(media_report):
    base, report = media_report
    merged = merge_agent_findings(report, _agent_items(base))
    with pytest.raises(ReportMergeError, match="already merged"):
        merge_agent_findings(merged, [])
    empty = copy.deepcopy(report)
    empty["coverage"]["pages_analyzed"] = 0
    with pytest.raises(ReportMergeError, match="no page"):
        merge_agent_findings(empty, [])
    with pytest.raises(ReportMergeError):
        merge_agent_findings({"findings": []}, [])
    broken = copy.deepcopy(report)
    del broken["findings"][0]["root_cause"]
    with pytest.raises(ReportMergeError, match="unedited"):
        merge_agent_findings(broken, [])


def test_merge_drops_whats_working_entries_a_new_finding_contradicts(media_report):
    _, report = media_report
    report = copy.deepcopy(report)
    report["whats_working"] = list(report["whats_working"]) + [
        {"id": "W-099", "check": "probe", "title": "t", "check_ids": ["independent-contradiction"],
         "evidence": "e", "pages_checked": 1}]
    merged = merge_agent_findings(report, [{"check": "AG-03", "evidence": "Different category elsewhere."}])
    assert not any(w["check"] == "probe" for w in merged["whats_working"])
    assert [w["id"] for w in merged["whats_working"]] == \
        [f"W-{i:03d}" for i in range(1, len(merged["whats_working"]) + 1)]


def test_merge_matches_a_live_audit_with_the_same_agent_findings(media_report, tmp_path):
    base, report = media_report
    # The fixture server picks a new port per run, so the entries are written for each base URL.
    live_dir = tmp_path / "live"
    live_dir.mkdir()
    path = live_dir / "ag.json"

    def items_for(url):
        return [dict(item, affected_pages=[p.replace(base, url) for p in item.get("affected_pages", [])])
                if isinstance(item, dict) else item
                for item in _agent_items(base)]

    from run_audit import run_audit
    url, stop = start_server(media=True)
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    try:
        path.write_text(json.dumps(items_for(url)), encoding="utf-8")
        os.environ.update(dict(_OFFLINE_ENV, AGENT_FINDINGS_PATH=str(path)))
        live = run_audit(url + "/", LIMITS, allow_private_targets=True)
    finally:
        stop()
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    merged = merge_agent_findings(report, items_for(base))

    def normalized(r, origin):
        return [(c, s, v, tuple(p.replace(origin, "ORIGIN") for p in pages), n)
                for c, s, v, pages, n in _shape(r)]
    assert live["coverage"]["agent_corroboration_stage"] == "ingested"
    assert normalized(live, url) == normalized(merged, base)
    assert not _agent_lines(live["limitations"])


# ---------------------------------------------------------------- command line

def _no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("merge-only mode opened a connection")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def test_cli_merges_a_utf16_report_without_any_request(media_report, tmp_path, monkeypatch, capsys):
    from run_audit import main
    base, report = media_report
    report_path, agent_path, out_path = tmp_path / "r.json", tmp_path / "ag.json", tmp_path / "merged.json"
    report_path.write_text(json.dumps(report), encoding="utf-16")
    agent_path.write_text(json.dumps(_agent_items(base)), encoding="utf-8-sig")
    _no_network(monkeypatch)
    assert main(["--from-report", str(report_path), "--agent-findings", str(agent_path),
                 "--out", str(out_path)]) == 0
    merged = json.loads(out_path.read_text(encoding="utf-8"))
    assert merged["coverage"]["agent_corroboration"]["merged_from"] == "ag.json"
    assert any(f["check_id"] == "independent-contradiction" for f in merged["findings"])
    err = capsys.readouterr().err
    assert "merged 3 of 5 agent finding(s)" in err


def test_cli_merge_can_overwrite_its_own_input(media_report, tmp_path, monkeypatch):
    from run_audit import main
    _, report = media_report
    report_path, agent_path = tmp_path / "r.json", tmp_path / "ag.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    agent_path.write_text("[]", encoding="utf-8")
    _no_network(monkeypatch)
    main(["--from-report", str(report_path), "--agent-findings", str(agent_path), "--out", str(report_path),
          "--quiet"])
    assert json.loads(report_path.read_text(encoding="utf-8"))["coverage"]["agent_corroboration_stage"] == "ingested"


@pytest.mark.parametrize("extra", [[], ["https://example.com"], ["--max-pages", "5"], ["--timeout", "30"]])
def test_cli_merge_rejects_crawl_options_and_a_missing_agent_file(tmp_path, monkeypatch, extra):
    from run_audit import main
    report_path = tmp_path / "r.json"
    report_path.write_text("{}", encoding="utf-8")
    _no_network(monkeypatch)
    args = ["--from-report", str(report_path)] + extra
    if extra:
        args += ["--agent-findings", str(report_path)]
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2


@pytest.mark.parametrize("report_body, agent_body", [
    ("{not json", "[]"),
    (json.dumps({"coverage": {}, "findings": [], "recommendations": []}), "[]"),
    (json.dumps({"x": 1}), "[]"),
])
def test_cli_merge_explains_unusable_inputs(tmp_path, monkeypatch, capsys, report_body, agent_body):
    from run_audit import main
    report_path, agent_path = tmp_path / "r.json", tmp_path / "ag.json"
    report_path.write_text(report_body, encoding="utf-8")
    agent_path.write_text(agent_body, encoding="utf-8")
    _no_network(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        main(["--from-report", str(report_path), "--agent-findings", str(agent_path)])
    assert exc.value.code == 2 and "--from-report" in capsys.readouterr().err


def test_cli_audit_checks_the_agent_file_before_crawling(tmp_path, monkeypatch, capsys):
    import run_audit
    def no_audit(*args, **kwargs):
        raise AssertionError("the audit started despite an unusable agent findings file")
    monkeypatch.setattr(run_audit, "run_audit", no_audit)
    # main() writes these variables; monkeypatch restores them afterwards.
    monkeypatch.setenv("AUDIT_PROGRESS", "0")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", "")
    bad = tmp_path / "ag.json"
    bad.write_text("{oops", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_audit.main(["https://example.com", "--agent-findings", str(bad), "--quiet"])
    assert exc.value.code == 2 and "--agent-findings" in capsys.readouterr().err


def test_cli_audit_passes_the_agent_file_to_the_worker(tmp_path, monkeypatch):
    import run_audit
    seen = {}
    def fake_audit(site, limits=None):
        seen["path"] = os.environ.get("AGENT_FINDINGS_PATH")
        return {"coverage": {}}
    monkeypatch.setattr(run_audit, "run_audit", fake_audit)
    # main() writes these variables; monkeypatch restores them afterwards.
    monkeypatch.setenv("AUDIT_PROGRESS", "0")
    monkeypatch.setenv("AGENT_FINDINGS_PATH", "")
    good = tmp_path / "ag.json"
    good.write_text("[]", encoding="utf-8")
    run_audit.main(["https://example.com", "--agent-findings", str(good), "--quiet", "--out",
                    str(tmp_path / "out.json")])
    assert seen["path"] == os.path.abspath(str(good))
