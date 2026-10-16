"""live_benchmark.py -- opt-in runner that audits real sites for hand-labelling.

Not part of the test suite (the file name does not start with test_) and it
refuses to run unless LIVE_BENCHMARK=1 is set, because it makes real requests.
Each site is audited by the same entrypoint and safety rules as a normal audit:
read-only GETs, robots.txt obeyed, the SSRF policy on, the usual time budget.
Sites are audited one after another, never in parallel, so no host sees more
than one audit at a time.

Usage:
    LIVE_BENCHMARK=1 python tests/live_benchmark.py urls.txt [out_dir]

urls.txt holds one site per line, optionally prefixed with its split:
    dev https://example.com
    holdout https://example.org
    https://example.net            (no prefix: dev)
Lines starting with # are ignored. Keep the list local; it is not committed.

Writes, in out_dir (default benchmark_runs/):
    <host>.json     the full report, UTF-8
    findings.csv    one row per finding, with an empty "label" column to fill
                    with tp (a real problem), fp (not a problem) or irrelevant
                    (true but not worth reporting for this kind of site).
    runs.json       one record per site, failed ones included: when it ran,
                    measured wall time, execution status, pages analyzed,
                    requests and bytes from coverage.network_budget, and the
                    code version. Live sites change, so a rerun may differ.
Score a labelled file with tests/score_benchmark.py. Tune rules on dev rows
only; score holdout rows once, at the end.
"""
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

FIELDS = ["split", "site", "finding_id", "check_ids", "severity", "status", "confidence", "finding_type",
          "pages", "title", "evidence", "label", "note"]
_SPLITS = ("dev", "holdout")


def read_sites(path):
    """[(split, url)] from a URL list file."""
    sites = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            split, url = (parts[0].lower(), parts[1]) if len(parts) > 1 and parts[0].lower() in _SPLITS \
                else ("dev", parts[0])
            sites.append((split, url))
    return sites


def finding_rows(split, report):
    """CSV rows for every finding in one report, label left empty."""
    rows = []
    for f in report.get("findings", []):
        evidence = (f.get("evidence_text") or "")[:300]
        rows.append({"split": split, "site": report.get("site", ""), "finding_id": f.get("id", ""),
                     "check_ids": " ".join(f.get("check_ids") or [f.get("check_id", "")]),
                     "severity": f.get("severity", ""), "status": f.get("status", ""),
                     "confidence": f.get("confidence", ""), "finding_type": f.get("finding_type", ""),
                     "pages": len(f.get("affected_pages") or ()), "title": f.get("title", ""),
                     "evidence": evidence, "label": "", "note": ""})
    return rows


def run_record(split, url, report, started_at, wall_seconds):
    """What one audit cost and how far it got, for the completion and runtime summary."""
    coverage = report.get("coverage") or {}
    budget = coverage.get("network_budget") or {}
    return {"split": split, "site": url, "started_at": started_at, "wall_seconds": round(wall_seconds, 1),
            "runtime_seconds": coverage.get("runtime_seconds"),
            "execution_status": report.get("execution_status"),
            "pages_analyzed": coverage.get("pages_analyzed", 0),
            "requests": budget.get("total_requests"), "bytes": budget.get("total_bytes"),
            "findings": len(report.get("findings") or ()), "code_version": report.get("code_version")}


def _file_name(url):
    host = urlsplit(url if "://" in url else "https://" + url).hostname or "site"
    return re.sub(r"[^a-z0-9.-]", "_", host.lower()) + ".json"


def main(argv):
    if os.environ.get("LIVE_BENCHMARK") != "1":
        print("live_benchmark makes real requests; set LIVE_BENCHMARK=1 to run it.", file=sys.stderr)
        return 2
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    out_dir = argv[2] if len(argv) > 2 else os.path.join(_ROOT, "benchmark_runs")
    os.makedirs(out_dir, exist_ok=True)
    from run_audit import run_audit
    rows, runs = [], []
    for split, url in read_sites(argv[1]):
        print(f"[benchmark] {split}: auditing {url}", file=sys.stderr)
        started_at, started = datetime.now(timezone.utc).isoformat(), time.monotonic()
        try:
            report = run_audit(url)
        except Exception as exc:  # one failed site must not stop the batch
            print(f"[benchmark] {url}: audit failed ({type(exc).__name__}: {exc})", file=sys.stderr)
            runs.append({"split": split, "site": url, "started_at": started_at,
                         "wall_seconds": round(time.monotonic() - started, 1),
                         "execution_status": "runner_error", "error": f"{type(exc).__name__}: {exc}"})
            continue
        runs.append(run_record(split, url, report, started_at, time.monotonic() - started))
        with open(os.path.join(out_dir, _file_name(url)), "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        rows.extend(finding_rows(split, report))
        with open(os.path.join(out_dir, "runs.json"), "w", encoding="utf-8") as handle:
            json.dump(runs, handle, indent=2)
    path = os.path.join(out_dir, "findings.csv")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[benchmark] {len(rows)} findings written to {path}; fill the label column, then run "
          f"tests/score_benchmark.py", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
