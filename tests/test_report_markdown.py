"""test_report_markdown.py -- Plan.md point 12: a Markdown report built from the
JSON report by common/report_markdown.py.

Covers the sections a non-expert needs, escaping of text that comes from the
audited site, the command line (UTF-8, UTF-8 with BOM and UTF-16 input, UTF-8
output, errors), and a real report from an offline archetype audit.
"""
import json
import os
import re
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts"):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from report_markdown import render, text, para, code_span, code_block, link, read_report, main

_SCRIPT = os.path.join(_ROOT, "common", "report_markdown.py")


def _finding(fid="F-001", **kw):
    f = {"id": fid, "check_id": "no-llms-txt", "title": "No llms.txt file found", "severity": "low",
         "status": "confirmed", "confidence": 0.6, "category": "ai_discoverability",
         "finding_type": "proactive_improvement", "root_cause": "Site does not publish an llms.txt file",
         "affected_pages": ["https://x.test/llms.txt"],
         "evidence": [{"type": "llms_txt", "description": "/llms.txt returned 404", "urls": ["https://x.test/llms.txt"]}],
         "suggested_action": {"summary": "Publish an llms.txt", "steps": ["Create /llms.txt", "List key pages"],
                              "priority": "low", "effort": "low", "impact": "low",
                              "quadrant_label": "Fill-in: small value, small work",
                              "expected_benefit": "A guide for AI tools", "verification": "Fetch /llms.txt",
                              "snippet": {"format": "markdown", "placement": "Save as /llms.txt",
                                          "code": "# X\n\n> REPLACE_WITH_DESCRIPTION\n",
                                          "placeholders": ["REPLACE_WITH_DESCRIPTION"],
                                          "note": "Check every value."}}}
    f.update(kw)
    return f


def _report(**kw):
    r = {"site": "https://x.test/", "audited_at": "2026-10-11T00:00:00+00:00", "execution_status": "completed",
         "summary": {"total_findings": 1, "critical": 0, "high": 0, "medium": 0, "low": 1,
                     "proactive_improvements": 1, "insufficient_evidence_items": 0, "total_recommendations": 2},
         "coverage": {"pages_discovered": 10, "pages_analyzed": 8, "sections_discovered": 3, "sections_analyzed": 3,
                      "runtime_seconds": 12.3, "pages_out_of_scope": 1,
                      "out_of_scope_pages": [{"url": "https://x.test/login", "reason": "login_page",
                                              "signals": ["password_input", "auth_path:login"]}]},
         "confidence": {"score": 0.0, "level": "low", "limiting_factor": "identity_confidence",
                        "components": {"sample_representativeness": 0.9, "identity_confidence": 0.0,
                                       "execution_penalty": 1.0},
                        "reasons": {"sample_representativeness": "The page sample stands for the site well.",
                                    "identity_confidence": "No Organization markup.",
                                    "execution_penalty": "The audit run completed normally."},
                        "explanation": "Confidence is low (0.00). No Organization markup."},
         "findings": [_finding()],
         "recommendations": [_finding("R-001"), _finding("R-002", check_id="baseline:engagement",
                                                          title="Keep internal linking intentional")],
         "top_actions": [{"finding_id": "F-001", "title": "No llms.txt file found", "summary": "Publish an llms.txt",
                          "priority": "low", "impact": "low", "effort": "low", "quick_win": False,
                          "start_here": True}],
         "quick_wins": [{"id": "F-001", "title": "No llms.txt file found", "summary": "Publish an llms.txt",
                         "impact": "medium", "effort": "low"}],
         "limitations": ["Headless rendering was not available."],
         "warnings": ["No dated facts found."]}
    r.update(kw)
    return r


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

def test_every_section_a_reader_needs_is_present():
    md = render(_report())
    for heading in ("# Brand AI-Readiness Audit: https://x.test/", "## How far to trust this report", "## Summary",
                    "## Start here", "## Top actions", "## Quick wins", "## All findings", "## Finding details",
                    "### F-001: No llms.txt file found", "## Other recommendations",
                    "## What this audit could not check", "## Notes from the run"):
        assert heading in md, heading
    assert "**Confidence:** low (0.00)" in md and "No Organization markup." in md
    assert "| Brand identity | 0.00 | No Organization markup. |" in md
    assert "- **Pages:** 8 analyzed of 10 discovered; 3 of 3 site sections reached" in md
    assert "1. Create /llms.txt\n2. List key pages" in md
    assert "```markdown\n# X\n\n> REPLACE_WITH_DESCRIPTION\n\n```" in md
    assert "Replace before publishing: `REPLACE_WITH_DESCRIPTION`" in md
    assert "<https://x.test/llms.txt>" in md
    assert "- <https://x.test/login> (password\\_input, auth\\_path:login)" in md


def test_recommendations_already_covered_by_a_finding_are_not_repeated():
    md = render(_report())
    section = md.split("## Other recommendations", 1)[1].split("##", 1)[0]
    assert "Keep internal linking intentional" in section
    assert "No llms.txt" not in section


def test_unfinished_audit_report_renders():
    md = render({"site": "https://x.test/", "audited_at": "t", "summary": {}, "findings": [],
                 "recommendations": [], "coverage": {"pages_discovered": 0, "pages_analyzed": 0},
                 "execution_status": "partial_deadline_reached",
                 "limitations": ["The audit worker did not return a complete report."],
                 "confidence": {"score": 0.0, "method": "no completed audit evidence", "level": "low",
                                "explanation": "Confidence is low (0.00). The audit did not finish."}})
    assert "Stopped at the time limit" in md and "nothing can be concluded" in md
    assert "## All findings" not in md and "## Start here" not in md
    assert "The audit worker did not return a complete report." in md


def test_missing_fields_render_and_wrong_shapes_are_controlled_errors():
    md = render({"findings": [{"id": "F-001"}], "recommendations": [{}]})
    assert md.endswith("\n") and "### F-001:" in md
    with pytest.raises(ValueError, match='list of objects'):
        render({"findings": [None, "x", {"id": "F-001"}]})
    with pytest.raises(ValueError, match='must be an object'):
        render({"coverage": []})
    with pytest.raises(ValueError, match='list of objects'):
        render({"top_actions": "nope"})
    with pytest.raises(ValueError):
        render(["not", "a", "report"])


def test_lowered_severity_is_explained():
    gated = _finding(severity="medium", severity_gate={"from": "high", "to": "medium",
                                                       "reason": "Not confirmed and one kind of evidence."})
    md = render(_report(findings=[gated]))
    assert "**Severity lowered** from high to medium: Not confirmed and one kind of evidence." in md
    assert "Severity lowered" not in render(_report())
    assert "### F-001:" in render(_report(findings=[_finding(severity_gate="odd")]))


def test_output_is_deterministic_and_has_no_blank_line_runs():
    assert render(_report()) == render(_report())
    assert "\n\n\n" not in render(_report())


def test_findings_are_capped_but_counted():
    pages = [f"https://x.test/p{i}" for i in range(25)]
    md = render(_report(findings=[_finding(affected_pages=pages)]))
    assert "- <https://x.test/p9>" in md and "<https://x.test/p10>" not in md
    assert "- and 15 more" in md
    assert "| F-001 | Improvement opportunity | low | confirmed | No llms.txt file found | 25 |" in md


# ---------------------------------------------------------------------------
# Escaping of text from the audited site
# ---------------------------------------------------------------------------

_HOSTILE = "Evil | title `code` <script>alert(1)</script> [x](javascript:alert(1)) *bold* _u_ ~s~ #tag\n## Injected"


def test_text_is_one_line_with_markdown_and_html_neutralised():
    out = text(_HOSTILE)
    assert "\n" not in out and "<script>" not in out and "&lt;script&gt;" in out
    for raw in ("|", "`", "[", "]", "*", "_", "~", "#"):
        assert re.search(r"(?<!\\)" + re.escape(raw), out) is None, raw


def test_hostile_titles_cannot_break_tables_or_add_headings():
    md = render(_report(findings=[_finding(title=_HOSTILE)],
                        top_actions=[{"finding_id": "F-001", "title": _HOSTILE, "summary": "- injected list",
                                      "start_here": True}]))
    assert "<script>" not in md
    assert not re.search(r"^## Injected", md, re.M)
    row = next(line for line in md.splitlines() if line.startswith("| F-001 |"))
    assert len(re.findall(r"(?<!\\)\|", row)) == 7  # six columns
    # A summary that opens its own line cannot become a list item.
    assert "\n\\- injected list\n" in md


def test_para_escapes_block_starts():
    assert para("- item") == "\\- item"
    assert para("+ item") == "\\+ item"
    assert para("= heading") == "\\= heading"
    assert para("12. item") == "12\\. item"
    assert para("3) item") == "3\\) item"
    assert para("# head") == "\\# head"
    assert para("Plain text.") == "Plain text."


def test_links_only_for_http_urls_and_never_break_out():
    assert link("https://x.test/a b>c") == "<https://x.test/a%20b%3Ec>"
    assert link("javascript:alert(1)") == "javascript:alert(1)"
    assert link("data:text/html,<b>x</b>") == "data:text/html,&lt;b&gt;x&lt;/b&gt;"
    assert link(None) == ""
    assert link("https://x.test/p", label="A [label]") == "[A \\[label\\]](https://x.test/p)"


def test_code_fences_outlast_backticks_inside():
    block = code_block("a\n````\nb", "html")
    assert block.startswith("`````html\n") and block.endswith("\n`````")
    assert code_block("plain", "Bad Lang!").startswith("```badlang\n")
    assert code_span("a`b") == "`` a`b ``"
    assert code_span("no-llms-txt") == "`no-llms-txt`"


def test_snippet_with_backtick_fence_inside_stays_in_its_block():
    snippet = {"format": "html", "code": "<script>x</script>\n```\n## not a heading", "placeholders": []}
    md = render(_report(findings=[_finding(suggested_action={"summary": "s", "steps": [], "snippet": snippet})]))
    assert "````html\n<script>x</script>\n```\n## not a heading\n````" in md


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("encoding,bom", [("utf-8", b""), ("utf-8", b"\xef\xbb\xbf"), ("utf-16-le", b"\xff\xfe"),
                                          ("utf-16-be", b"\xfe\xff")])
def test_reads_utf8_bom_and_utf16_reports(tmp_path, encoding, bom):
    path = tmp_path / "results.json"
    path.write_bytes(bom + json.dumps(_report(site="https://x.test/été")).encode(encoding))
    assert read_report(str(path))["site"] == "https://x.test/été"


def test_cli_writes_utf8_markdown_next_to_the_report(tmp_path):
    src = tmp_path / "results.json"
    src.write_bytes(b"\xff\xfe" + json.dumps(_report(site="https://x.test/café")).encode("utf-16-le"))
    assert main([str(src)]) == 0
    out = (tmp_path / "results.md").read_bytes()
    assert not out.startswith(b"\xef\xbb\xbf") and b"\r\n" not in out
    assert "café" in out.decode("utf-8")
    assert main([str(src), str(tmp_path / "named.md")]) == 0
    assert (tmp_path / "named.md").read_bytes() == out


def test_cli_errors_are_clear_and_never_overwrite_the_report(tmp_path):
    def run(*args):
        return subprocess.run([sys.executable, _SCRIPT, *args], capture_output=True, text=True, timeout=60)
    missing = run(str(tmp_path / "nope.json"))
    assert missing.returncode == 2 and "no such file" in missing.stderr
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = run(str(bad))
    assert result.returncode == 2 and "not a readable JSON audit report" in result.stderr
    good = tmp_path / "r.json"
    good.write_text(json.dumps(_report()), encoding="utf-8")
    result = run(str(good), str(good))
    assert result.returncode == 2 and "overwrite" in result.stderr
    assert json.loads(good.read_text(encoding="utf-8"))["site"] == "https://x.test/"
    printed = run(str(good), "-")
    assert printed.returncode == 0 and printed.stdout.startswith("# Brand AI-Readiness Audit")


def test_renderer_imports_only_the_standard_library_and_no_network():
    import ast
    tree = ast.parse(open(_SCRIPT, encoding="utf-8").read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    # The shared boundary is also standard-library-only and has no transport.
    assert imported <= {"html", "json", "os", "re", "sys", "urllib.parse", "argparse", "json_boundary"}, imported
    boundary = ast.parse(open(os.path.join(_ROOT, 'common', 'json_boundary.py'), encoding='utf-8').read())
    dependencies = {a.name for n in ast.walk(boundary) if isinstance(n, ast.Import) for a in n.names}
    dependencies |= {n.module for n in ast.walk(boundary) if isinstance(n, ast.ImportFrom)}
    assert dependencies <= {'json', 'math', 'os', 'tempfile', 'decimal'}


# ---------------------------------------------------------------------------
# A real report
# ---------------------------------------------------------------------------

def test_renders_a_real_offline_audit_report():
    from archetype_sites import ARCHETYPES, serve
    from constants import Limits
    from run_audit import run_audit
    offline = {"SEARCH_API_URL": "", "PAGESPEED_API_KEY": "", "FIELD_VITALS_LOOKUP": "0", "AGENT_FINDINGS_PATH": "",
               "OFF_SITE_LOOKUP": "0", "KNOWLEDGE_GRAPH_LOOKUP": "0", "ENABLE_RENDERING": "0", "AUDIT_PROGRESS": "0"}
    saved = {k: os.environ.get(k) for k in offline}
    os.environ.update(offline)
    base, stop, _ = serve(ARCHETYPES["shop"])
    try:
        report = run_audit(base + "/", limits=Limits(), allow_private_targets=True)
    finally:
        stop()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    md = render(json.loads(json.dumps(report)))
    for f in report["findings"]:
        assert f"### {f['id']}: " in md
    assert "## Start here" in md and "## What this audit could not check" in md
    assert "Login pages that were fetched but not analyzed" in md
    assert "```html" in md  # the Product JSON-LD fix snippet
    assert chr(0x2014) not in md
