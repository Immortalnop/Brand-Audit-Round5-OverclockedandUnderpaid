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
    findings.csv    one row per USER-VISIBLE item, with an empty "label" column
                    to fill with tp (a real problem), fp (not a problem) or
                    irrelevant (true but not worth reporting for this kind of
                    site).

Every item a reader of the report sees is exported, each tagged with the
`section` it appears in:

    core            report.findings -- the main findings list
    hygiene         report.hygiene_findings -- the SEO-hygiene appendix
    recommendation  report.recommendations -- beyond-defect suggestions

This matters for measurement, not just completeness. The exporter used to
iterate report.findings only, so anything the scorer moved into the hygiene
appendix was never labelled and never counted against precision -- which means a
headline precision figure could be improved by reclassifying a questionable
output instead of fixing it. score_benchmark.py reports precision per section
and makes its scope explicit: core, hygiene, core+hygiene (every finding), and
recommendations separately.

Score a labelled file with tests/score_benchmark.py. Tune rules on dev rows
only; score holdout rows once, at the end.
"""
import csv
import json
import os
import re
import sys
from urllib.parse import urlsplit

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
             "skills/entity-corroboration-agent/scripts"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

FIELDS = ["split", "site", "section", "tier", "finding_id", "check_ids", "severity", "status", "confidence",
          "finding_type", "pages", "title", "evidence", "label", "note"]
_SPLITS = ("dev", "holdout")
# (report key, section name) for every list a reader of the report sees.
_SECTIONS = (("findings", "core"), ("hygiene_findings", "hygiene"), ("recommendations", "recommendation"))


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
    """CSV rows for every user-visible item in one report, label left empty.

    Core findings, the hygiene appendix and the recommendations are all exported,
    each tagged with its section, so nothing a reader sees can sit outside the
    measurement."""
    rows = []
    for key, section in _SECTIONS:
        for f in report.get(key, []) or []:
            evidence = (f.get("evidence_text") or "")[:300]
            rows.append({"split": split, "site": report.get("site", ""), "section": section,
                         "tier": f.get("tier", ""), "finding_id": f.get("id", ""),
                         "check_ids": " ".join(f.get("check_ids") or [f.get("check_id", "")]),
                         "severity": f.get("severity", ""), "status": f.get("status", ""),
                         "confidence": f.get("confidence", ""), "finding_type": f.get("finding_type", ""),
                         "pages": len(f.get("affected_pages") or ()), "title": f.get("title", ""),
                         "evidence": evidence, "label": "", "note": ""})
    return rows


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
    rows = []
    for split, url in read_sites(argv[1]):
        print(f"[benchmark] {split}: auditing {url}", file=sys.stderr)
        try:
            report = run_audit(url)
        except Exception as exc:  # one failed site must not stop the batch
            print(f"[benchmark] {url}: audit failed ({type(exc).__name__}: {exc})", file=sys.stderr)
            continue
        with open(os.path.join(out_dir, _file_name(url)), "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        rows.extend(finding_rows(split, report))
    path = os.path.join(out_dir, "findings.csv")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    from collections import Counter
    by_section = Counter(r["section"] for r in rows)
    print(f"[benchmark] {len(rows)} user-visible items written to {path} "
          f"({', '.join(f'{n} {s}' for s, n in sorted(by_section.items())) or 'none'}); "
          f"fill the label column, then run tests/score_benchmark.py", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
