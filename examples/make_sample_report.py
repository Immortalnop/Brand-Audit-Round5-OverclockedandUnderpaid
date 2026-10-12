"""Regenerate examples/sample-report.json and sample-report.md from the local test
fixture (no third-party site, no network). The fixture host is rewritten to
https://shop.example so the sample reads like a real report.

    python3 examples/make_sample_report.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "skills", "audit-orchestrator", "scripts"))


def main():
    from fixtures_server import start_server
    import run_audit
    from render_report import render_markdown
    from validate_report import validate_report
    url, stop = start_server(sitemap_mode="broken_nav")
    try:
        report = run_audit.run_audit(url + "/", allow_private_targets=True)
    finally:
        stop()
    text = json.dumps(report, indent=2, default=str)
    text = re.sub(r"http://127\.0\.0\.1:\d+", "https://shop.example", text).replace("127.0.0.1", "shop.example")
    report = validate_report(json.loads(text), strict_catalog=True)
    out = os.path.join(ROOT, "examples")
    with open(os.path.join(out, "sample-report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    with open(os.path.join(out, "sample-report.md"), "w", encoding="utf-8") as fh:
        fh.write(render_markdown(report))
    print(f"wrote {len(report['findings'])} findings to examples/sample-report.json and .md")


if __name__ == "__main__":
    main()
