"""analyze_answer_format.py -- the passage formats assistants quote, from the HTML alone.

An assistant that fetches a page lifts short, self-contained passages: the
sentence right after a question heading, a row of a comparison table, an item of
a specification list. This check reads the acquisition snapshot only (no
requests):

  - question-answer-indirect (suggestion, suspected): a question-shaped H2 or
    H3 whose following text does not open with a direct answer: no text before
    the next heading, a first sentence longer than 40 words, or a filler opener
    such as "Great question". English pages only, because the opener list and
    the question words are English. Call-to-action headings ("Need more
    information?", "Want to join us?") and questions answered by their own
    subheadings (an H2 followed by H3 sections) are not judged.
  - table-headers-missing (defect, confirmed): a data table (at least two rows
    and two columns, not role="presentation") with no <th> cells. Without
    header cells a parser cannot tell which column a value belongs to.
  - comparison-table-missing (suggestion, suspected): a page whose title or
    main heading says it compares things ("vs", "versus", "comparison",
    "alternatives") but which has no data table or definition list.
  - spec-list-missing (suggestion, suspected): a product or software page with
    substantial text but no table, definition list or list of three or more
    items, so its specifications are only available as prose.

The existing answer-headings check (analyze_answer_content.py) covers pages
with no question headings at all; this one judges the ones that exist.

Pages whose raw HTML carries too little text for their type are probably built
by JavaScript. The comparison-table and spec-list checks do not judge them, and
the report says how many were skipped.
"""
import re
from check_helpers import eligible_pages, page_share, split_script_dependent, script_dependent_warning
from models import make_finding, skill_result

_MAX_ANSWER_WORDS = 40
_FILLER_OPENER = re.compile(
    r"^(?:great|good|excellent) question|^in this (?:article|section|post|guide|page)|^before we\b|^let'?s\b"
    r"|^well,|^so,|^it depends\b|^there are (?:many|several|a few|a lot of) (?:things|factors|ways|reasons)"
    r"|^this is a (?:common|popular|frequently asked) question", re.I)
# Call-to-action headings phrased as questions ("Need more information?") invite
# the visitor to act; they are not questions the page claims to answer.
_CTA_QUESTION = re.compile(
    r"^(?:need|want|ready|looking for|interested|have (?:a |any )?questions?|got (?:a |any )?questions?|still have"
    r"|questions\b|can'?t find|would you like|wish to|keen to|curious)\b", re.I)
# "Alternative" signals a comparison only as a noun naming the options compared
# ("Slack alternatives", "alternatives to Slack"); as an adjective ("Alternative
# Python implementations", "alternative routes") it does not.
_COMPARISON = re.compile(r"\b(?:vs\.?|versus|comparison|compared?)(?=\W|$)|\balternatives?\s+(?:to|for)\b"
                         r"|\balternatives\b(?!\s+[A-Za-z])|\balternatives\s+in\b", re.I)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _english(page):
    return ((page.features or {}).get("lang") or "").lower().split("-")[0] == "en"


def _data_tables(features):
    return [t for t in features.get("tables") or () if not t.get("layout") and t.get("rows", 0) >= 2
            and t.get("max_cols", 0) >= 2]


def answer_problem(answer):
    """Why the text after a question heading is not a direct answer, or None."""
    text = " ".join((answer or "").split())
    if not text:
        return "no text before the next heading"
    first = _SENTENCE_END.split(text, 1)[0]
    if _FILLER_OPENER.search(first):
        return "opens with filler (\"" + first[:40] + "\")"
    words = len(first.split())
    # A first "sentence" cut off at the 600-character capture limit is long either way.
    if words > _MAX_ANSWER_WORDS:
        return f"first sentence has {words} words"
    return None


def _action(summary, steps, priority, effort="low"):
    return {"summary": summary, "steps": steps, "priority": priority, "effort": effort,
            "expected_benefit": "Assistants can lift a complete, correctly labelled answer from the page",
            "verification": "Re-run the audit and confirm the listed passages are reported as answerable"}


def analyze_answer_format(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Answer-format checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    # The comparison-table and spec-list checks conclude that something is
    # missing, so they judge only pages whose raw HTML carries their content: the
    # title of a page built by JavaScript can say "vs" while its table arrives
    # later. Question headings and tables are judged wherever they appear,
    # because a heading or table in the raw HTML is itself content.
    judged, built = split_script_dependent(pages)
    judged_ids = {id(p) for p in judged}
    english = [p for p in pages if _english(p)]
    indirect, headerless, comparison, spec = [], [], [], []
    questions_checked = 0
    for p in pages:
        f = p.features or {}
        tables = _data_tables(f)
        bare = [t for t in tables if not t.get("header_cells")]
        if bare:
            headerless.append((p, bare))
        lists = (f.get("definition_lists") or 0) + (f.get("unordered_lists") or 0) + (f.get("ordered_lists") or 0)
        lead = " ".join([p.title or ""] + [h for h in p.headings[:1]])
        if id(p) in judged_ids and _COMPARISON.search(lead) and not tables and not f.get("definition_lists"):
            comparison.append(p)
        if (id(p) in judged_ids and p.page_type in ("product", "software") and len(p.visible_text.split()) >= 150
                and not tables and not lists):
            spec.append(p)
        if _english(p):
            problems = []
            for qa in f.get("question_answers") or ():
                if _CTA_QUESTION.search((qa.get("question") or "").strip()) or (
                        not (qa.get("answer") or "").strip() and qa.get("answered_by_subheadings")):
                    continue
                questions_checked += 1
                problem = answer_problem(qa.get("answer"))
                if problem:
                    problems.append((qa.get("question", ""), problem))
            if problems:
                indirect.append((p, problems))

    findings = []
    if indirect:
        count = sum(len(items) for _, items in indirect)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.6,
            title=f"{count} question heading(s) are not followed by a direct answer on "
                  + page_share([p for p, _ in indirect], english),
            root_cause="Assistants quote the sentence right after a question heading; when that sentence is "
                       "missing, very long or a filler opener, the answer is not liftable as one passage",
            affected_pages=[p.url for p, _ in indirect],
            evidence=[{"type": "question_answer",
                       "description": "; ".join(f"\"{q[:80]}\": {why}" for q, why in items[:3]),
                       "urls": [p.url]} for p, items in indirect[:10]],
            suggested_action=_action(
                "Open each answer with one sentence that answers the question directly",
                ["Start the text under each listed question with a direct answer of 40 words or fewer",
                 "Put supporting detail, caveats and examples after that first sentence",
                 "Remove filler openers such as \"Great question\" or \"In this article\""],
                "low"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_answer_format.py",
                        "rule_id": "question-answer-indirect"},
        ))
    if headerless:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="low", status="confirmed",
            confidence=0.85,
            title="Data tables have no header cells on " + page_share([p for p, _ in headerless], pages),
            root_cause="A parser maps each table value to its meaning through <th> header cells; a table "
                       "built only from <td> cells leaves values such as prices or limits without a label",
            affected_pages=[p.url for p, _ in headerless],
            evidence=[{"type": "table_structure",
                       "description": f"{len(tables)} data table(s) without <th>: "
                                      + ", ".join(f"{t['rows']} rows x {t['max_cols']} columns" for t in tables[:3]),
                       "urls": [p.url]} for p, tables in headerless[:10]],
            suggested_action=_action(
                "Mark the header row and header column of each data table with <th>",
                ["Change the first row's cells to <th scope=\"col\"> and any row labels to <th scope=\"row\">",
                 "Add a <caption> that says what the table compares",
                 "Keep layout tables out of content, or mark them role=\"presentation\""],
                "low"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_answer_format.py",
                        "rule_id": "table-headers-missing"},
        ))
    if comparison:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.6,
            title="Comparison pages have no comparison table on " + page_share(comparison, judged),
            root_cause="Comparison answers are assembled from rows that pair an attribute with each option; "
                       "a comparison written only as prose forces the assistant to reconstruct that pairing",
            affected_pages=[p.url for p in comparison],
            evidence=[{"type": "comparison_format",
                       "description": f"Title \"{(p.title or '')[:80]}\" signals a comparison, but no data table "
                                      "or definition list was found in the HTML",
                       "urls": [p.url]} for p in comparison[:10]],
            suggested_action=_action(
                "Summarize each comparison in an HTML table",
                ["Add a table with one column per option and one row per attribute (price, limits, support)",
                 "Use <th> for the option names and the attribute names",
                 "Keep the prose explanation below the table"],
                "low", effort="medium"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_answer_format.py",
                        "rule_id": "comparison-table-missing"},
        ))
    if spec:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.5,
            title="Product pages state specifications only as prose on "
                  + page_share(spec, [p for p in judged if p.page_type in ("product", "software")], "product page"),
            root_cause="Specification questions are answered from labelled facts; a list or table states each "
                       "fact once with its label, while prose spreads it across sentences",
            affected_pages=[p.url for p in spec],
            evidence=[{"type": "spec_format",
                       "description": f"{len(p.visible_text.split())} words of text, no table, definition list or "
                                      "list of three or more items in the HTML",
                       "urls": [p.url]} for p in spec[:10]],
            suggested_action=_action(
                "Add a specification list or table to each product page",
                ["List the key specifications (size, price, compatibility, limits) as a <dl> or a two-column table",
                 "Repeat the same values in the Product JSON-LD where a property exists"],
                "low"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_answer_format.py",
                        "rule_id": "spec-list-missing"},
        ))
    warnings = [script_dependent_warning(built, pages, "comparison tables and specification lists")] if built else []
    return skill_result(
        "crawl-render-audit", findings=findings, warnings=warnings,
        metrics={"answer_format_pages_analyzed": len(pages),
                 "answer_format_script_dependent_pages": len(built),
                 "answer_format_question_headings_checked": questions_checked,
                 "answer_format_indirect_answers": sum(len(items) for _, items in indirect),
                 "answer_format_data_tables": sum(len(_data_tables(p.features or {})) for p in pages),
                 "answer_format_english_pages": len(english)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0})
