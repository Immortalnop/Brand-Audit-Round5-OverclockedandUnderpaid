"""test_benchmark_tools.py -- the measurement harness.

Checks the parts of tests/live_benchmark.py and tests/score_benchmark.py that
need no network: URL list parsing, CSV rows, the precision and calibration
arithmetic, the opt-in guard, and fixture recall over the offline corpora.
"""
import csv
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

import live_benchmark
import score_benchmark


def test_url_list_parsing(tmp_path):
    path = tmp_path / "urls.txt"
    path.write_text("# sites\ndev https://a.test\nholdout https://b.test  # later\nhttps://c.test\n\n",
                    encoding="utf-8")
    assert live_benchmark.read_sites(str(path)) == [("dev", "https://a.test"), ("holdout", "https://b.test"),
                                                    ("dev", "https://c.test")]


def test_runner_refuses_without_opt_in(monkeypatch, capsys):
    monkeypatch.delenv("LIVE_BENCHMARK", raising=False)
    assert live_benchmark.main(["live_benchmark.py", "urls.txt"]) == 2
    assert "LIVE_BENCHMARK=1" in capsys.readouterr().err


def test_finding_rows_leave_the_label_empty():
    report = {"site": "https://a.test", "findings": [
        {"id": "F-001", "check_id": "h1", "check_ids": ["h1", "page-orientation"], "severity": "low",
         "status": "suspected", "confidence": 0.7, "finding_type": "proactive_improvement",
         "affected_pages": ["https://a.test/x"], "title": "T", "evidence_text": "E"}]}
    (row,) = live_benchmark.finding_rows("holdout", report)
    assert row["check_ids"] == "h1 page-orientation" and row["pages"] == 1 and row["label"] == ""
    assert set(row) == set(live_benchmark.FIELDS)


def _write(tmp_path, rows):
    path = tmp_path / "findings.csv"
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=live_benchmark.FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in live_benchmark.FIELDS})
    return str(path)


def test_precision_high_severity_and_split(tmp_path):
    path = _write(tmp_path, [
        {"split": "dev", "check_ids": "a", "severity": "high", "confidence": 0.9, "label": "tp"},
        {"split": "dev", "check_ids": "a", "severity": "low", "confidence": 0.6, "label": "fp"},
        {"split": "dev", "check_ids": "b", "severity": "low", "confidence": 0.6, "label": "irrelevant"},
        {"split": "dev", "check_ids": "b", "severity": "low", "confidence": 0.6, "label": ""},
        {"split": "holdout", "check_ids": "c", "severity": "critical", "confidence": 0.8, "label": "fp"},
    ])
    dev = score_benchmark.score(score_benchmark.load_rows(path, "dev"))
    assert dev["labelled"] == 3 and dev["precision"] == round(1 / 3, 3)
    assert dev["high_severity"] == 1 and dev["high_severity_precision"] == 1.0 and dev["false_high_severity"] == 0
    assert [cid for cid, _, _ in dev["per_check"]] == ["b", "a"]
    holdout = score_benchmark.score(score_benchmark.load_rows(path, "holdout"))
    assert holdout["false_high_severity"] == 1 and holdout["precision"] == 0.0
    assert score_benchmark.score(score_benchmark.load_rows(path))["labelled"] == 4


def test_expected_calibration_error():
    perfect = [{"confidence": "0.75", "label": "tp"}] * 3 + [{"confidence": "0.75", "label": "fp"}]
    assert score_benchmark.expected_calibration_error(perfect) == 0.0
    overconfident = [{"confidence": "0.9", "label": "fp"}] * 2
    assert score_benchmark.expected_calibration_error(overconfident) == 0.9
    assert score_benchmark.expected_calibration_error([]) is None
    assert score_benchmark.expected_calibration_error([{"confidence": "1.0", "label": "tp"}]) == 0.0


def test_suggested_base_confidence_never_exceeds_measured_precision():
    rows = ([{"check_ids": "a", "label": "tp"}] * 7 + [{"check_ids": "a", "label": "fp"}] * 3
            + [{"check_ids": "b", "label": "tp"}] * 2 + [{"check_ids": "c", "label": "fp"}] * 5
            + [{"check_ids": "d", "label": "tp"}] * 5)
    suggested = score_benchmark.suggest_base_confidence(rows)
    assert suggested["a"] == (0.7, 0.7, 10)
    assert "b" not in suggested  # too few labelled rows
    assert suggested["c"] == (0.5, 0.0, 5) and suggested["d"] == (0.9, 1.0, 5)


def test_fixture_recall_is_complete_with_no_trap_hits():
    r = score_benchmark.fixture_recall()
    assert r["expected"] >= 17 and r["found"] == r["expected"] and r["trap_hits"] == 0
    assert all(ok for *_, ok in r["rows"]) and not r["traps"]
