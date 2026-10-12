"""score_benchmark.py -- precision, high-severity precision, calibration and recall.

Usage:
    python tests/score_benchmark.py findings.csv [--split dev|holdout|all] [--recall] [--suggest]

findings.csv is the file tests/live_benchmark.py writes, with its label column
filled in: tp (a real problem), fp (not a problem) or irrelevant (true but not
worth reporting for this kind of site). Unlabelled rows are ignored.

Reports, for the chosen split, with the SCOPE of each number named -- a
precision figure is only meaningful next to the set it was measured over:
  - precision (all findings): tp / labelled rows in the core findings list AND
    the hygiene appendix. Both are user-visible, so both count. Reporting only
    the core list would let a headline improve by moving a questionable output
    into an unscored appendix rather than by fixing it.
  - precision (core findings) and precision (hygiene appendix), separately, so
    the split is visible rather than averaged away;
  - recommendations, scored separately: they are beyond-defect suggestions, not
    claims that something is wrong, so they do not belong in a defect-precision
    figure either way;
  - high-severity precision: over high and critical findings only;
  - per-check precision, worst first, to show which rule to fix next;
  - expected calibration error (ECE): the weighted gap between stated
    confidence and observed precision, over confidence bins of width 0.1.
With --suggest it prints, from dev rows only, a base confidence per check equal to
its measured precision rounded down to a 0.1 step: set each rule's confidence to
that value in its script, then confirm on holdout that ECE fell.
With --recall it also audits the offline fixture corpus (tests/archetype_sites.py,
expectations in tests/test_archetype_fixtures.py) and reports the share of planted
defects found, plus the number of trap check IDs wrongly raised. That part makes
no request outside 127.0.0.1 and needs pytest installed.

Working targets: precision (all findings) >= 0.95 and zero false high or
critical findings on holdout, recall 1.0 and zero trap hits on the fixtures,
ECE <= 0.1.

Rows written by an older live_benchmark.py have no `section` column; they are
treated as core, and the report says so, so an old CSV is not silently scored as
if it covered the appendix.
"""
import csv
import os
import sys

_LABELS = ("tp", "fp", "irrelevant")
_HIGH = ("high", "critical")


def load_rows(path, split="all"):
    """Labelled rows of one split ('all' keeps every split)."""
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if (r.get("label") or "").strip().lower() in _LABELS]
    for r in rows:
        r["label"] = r["label"].strip().lower()
    return rows if split == "all" else [r for r in rows if r.get("split", "dev") == split]


def _precision(rows):
    return round(sum(r["label"] == "tp" for r in rows) / len(rows), 3) if rows else None


def expected_calibration_error(rows, width=0.1):
    """Sum over confidence bins of (bin share) x |mean confidence - observed precision|."""
    bins = {}
    for r in rows:
        try:
            conf = min(max(float(r["confidence"]), 0.0), 1.0)
        except (TypeError, ValueError):
            continue
        bins.setdefault(min(int(conf / width), int(1 / width) - 1), []).append((conf, r["label"] == "tp"))
    total = sum(len(v) for v in bins.values())
    if not total:
        return None
    gap = sum(len(v) / total * abs(sum(c for c, _ in v) / len(v) - sum(t for _, t in v) / len(v))
              for v in bins.values())
    return round(gap, 3)


_CONFIDENCE_STEPS = (0.5, 0.6, 0.7, 0.8, 0.9)


def suggest_base_confidence(rows, min_rows=5):
    """{check_id: (suggested confidence, measured precision, rows)} for checks with
    at least min_rows labelled findings: the measured precision rounded down to
    the nearest step in 0.5..0.9, so a check never claims more than it earned. A
    check below 0.5 gets 0.5 and needs fixing more than recalibrating. Use dev
    rows only; holdout rows are for the final score."""
    by_check = {}
    for r in rows:
        for check_id in (r.get("check_ids") or "?").split():
            by_check.setdefault(check_id, []).append(r)
    out = {}
    for check_id, rs in sorted(by_check.items()):
        if len(rs) < min_rows:
            continue
        precision = sum(r["label"] == "tp" for r in rs) / len(rs)
        step = max([s for s in _CONFIDENCE_STEPS if s <= precision + 1e-9] or [_CONFIDENCE_STEPS[0]])
        out[check_id] = (step, round(precision, 3), len(rs))
    return out


def _section(row):
    """The report section a row came from. Rows from an older export have no
    section column; they are core findings, and the caller reports that."""
    return (row.get("section") or "core").strip().lower() or "core"


def score(rows):
    """Metrics for labelled rows, scoped by report section.

    Findings (core + hygiene) are what the audit claims is wrong, so they share
    one precision figure and are also reported apart. Recommendations are
    beyond-defect suggestions and are scored on their own."""
    findings = [r for r in rows if _section(r) in ("core", "hygiene")]
    core = [r for r in findings if _section(r) == "core"]
    hygiene = [r for r in findings if _section(r) == "hygiene"]
    recommendations = [r for r in rows if _section(r) == "recommendation"]
    high = [r for r in findings if r.get("severity") in _HIGH]
    by_check = {}
    for r in findings:
        for check_id in (r.get("check_ids") or "?").split():
            by_check.setdefault(check_id, []).append(r)
    per_check = sorted(((cid, _precision(rs), len(rs)) for cid, rs in by_check.items()),
                       key=lambda item: (item[1], -item[2], item[0]))
    return {"labelled": len(findings),
            # Named and scoped: every user-visible finding, core and appendix.
            "scope": "core findings + hygiene appendix",
            "precision": _precision(findings),
            "core_labelled": len(core), "core_precision": _precision(core),
            "hygiene_labelled": len(hygiene), "hygiene_precision": _precision(hygiene),
            "recommendations_labelled": len(recommendations),
            "recommendations_precision": _precision(recommendations),
            "sections_present": sorted({_section(r) for r in rows}),
            "high_severity": len(high), "high_severity_precision": _precision(high),
            "false_high_severity": sum(r["label"] != "tp" for r in high),
            "ece": expected_calibration_error(findings), "per_check": per_check}


def fixture_recall():
    """Audit every offline fixture site and score it against the corpus
    expectations. Returns {found, expected, trap_hits, rows, traps}, where rows is
    one (site, check_id, detected, pages_ok) per planted defect and traps is one
    (site, check_id) per trap check wrongly raised."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "tests"))
    import test_archetype_fixtures as corpus
    from archetype_sites import serve
    from constants import Limits
    from run_audit import run_audit
    saved = {k: os.environ.get(k) for k in corpus.OFFLINE_ENV}
    os.environ.update(corpus.OFFLINE_ENV)
    rows, traps = [], []
    try:
        for name, site in corpus.SITES.items():
            base, stop, _ = serve(site)
            try:
                report = run_audit(base + "/", limits=Limits(), allow_private_targets=True)
            finally:
                stop()
            checks = corpus.by_check(base, report)
            for check_id, pages in corpus.EXPECTED[name].items():
                detected = check_id in checks
                rows.append((name, check_id, detected, detected and (pages is None or pages <= checks[check_id])))
            traps.extend((name, c) for c in sorted(corpus.ABSENT[name] & set(checks)))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return {"found": sum(1 for *_, ok in rows if ok), "expected": len(rows),
            "trap_hits": len(traps), "rows": rows, "traps": traps}


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    split = "all"
    if "--split" in argv:
        split = argv[argv.index("--split") + 1]
    rows = load_rows(argv[1], split)
    result = score(rows)
    print(f"split: {split}; labelled findings: {result['labelled']} ({result['scope']})")
    if "section" not in (rows[0] if rows else {}):
        print("note: this CSV has no 'section' column (written by an older live_benchmark.py); "
              "every row is scored as a core finding.")
    print(f"precision, {result['scope']}: {result['precision']}")
    print(f"  core findings    : {result['core_precision']} ({result['core_labelled']} labelled)")
    print(f"  hygiene appendix : {result['hygiene_precision']} ({result['hygiene_labelled']} labelled)")
    print(f"recommendations (scored separately, not defect claims): "
          f"{result['recommendations_precision']} ({result['recommendations_labelled']} labelled)")
    print(f"high/critical findings: {result['high_severity']}, precision {result['high_severity_precision']}, "
          f"false {result['false_high_severity']}")
    print(f"expected calibration error: {result['ece']}")
    print("per-check precision (worst first):")
    for check_id, precision, count in result["per_check"]:
        print(f"  {check_id:40} {precision}  ({count})")
    if "--suggest" in argv:
        rows = load_rows(argv[1], "dev")
        print("suggested base confidence from dev rows (check: suggested, measured precision, rows):")
        for check_id, (step, precision, count) in suggest_base_confidence(rows).items():
            print(f"  {check_id:40} {step}  {precision}  ({count})")
    if "--recall" in argv:
        r = fixture_recall()
        print(f"\nfixture corpus ({len(set(site for site, *_ in r['rows']))} offline sites): recall "
              f"{r['found']}/{r['expected']} = {round(r['found'] / r['expected'], 3) if r['expected'] else None}; "
              f"trap check IDs wrongly raised: {r['trap_hits']}")
        print(f"  {'site':8} {'planted check':34} detected")
        for site, check_id, detected, ok in r["rows"]:
            mark = "yes" if ok else ("wrong pages" if detected else "NO")
            print(f"  {site:8} {check_id:34} {mark}")
        for site, check_id in r["traps"]:
            print(f"  {site:8} {check_id:34} FALSE POSITIVE (must not fire)")
    return 0


if __name__ == "__main__":
    sys.path[:0] = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), rel) for rel in (
        "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
        "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
        "skills/entity-corroboration-agent/scripts")]
    sys.exit(main(sys.argv))
