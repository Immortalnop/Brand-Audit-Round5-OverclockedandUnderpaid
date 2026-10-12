"""generate_recommendations.py -- suggestions that go beyond the detected defects.

The report has three action surfaces, each with one job:

  findings        every detected problem or opportunity (defects AND proactive
                  improvements), each with evidence and a fix -- never repeated
                  elsewhere;
  action_plan     the ordered to-do list: one row per finding, ranked by
                  priority_score, pointing back to finding ids;
  recommendations only items that are NOT findings: evidence-derived "beyond the
                  defects" suggestions plus calibrated maintenance baselines for
                  categories where nothing was found.

Recommendations are always finding_type == "proactive_improvement". Beyond items
are derived from this run's evidence (status "confirmed" = the condition they
build on was observed); baselines are general best practice (status
"not_applicable") -- they assert no site defect.
"""
from models import apply_invariant_i1
from check_catalog import enrich_finding
from action_catalog import baseline_action, evidence_status_mode
from url_keys import intent_of

_GENERIC_BASELINE = [
    {
        "category": "ai_discoverability",
        "title": "Periodically re-audit AI discoverability as content changes",
        "rationale": "Crawlers, robots policies and structured-data conventions change independently of "
                     "visible site content.",
        "steps": ["Re-run this audit on a recurring schedule",
                  "Re-validate JSON-LD after any template or CMS change"],
        "confidence": 0.5,
    },
    {
        "category": "engagement",
        "title": "Keep internal linking intentional as the site grows",
        "rationale": "No orphan or dead-end pages were confirmed now, but new pages commonly launch without "
                     "inbound links or a clear next step.",
        "steps": ["Add new pages to relevant navigation or related-content sections",
                  "Give every page at least one outbound next step"],
        "confidence": 0.5,
    },
    {
        "category": "off_site_presence",
        "title": "Continue building independent, identity-matched off-site mentions",
        "rationale": "Off-site presence is cumulative; even a well-corroborated brand benefits from continued, "
                     "diverse independent mentions.",
        "steps": ["List on relevant directories", "Keep sameAs/social profiles active"],
        "confidence": 0.4,
    },
]

_LANDING_INTENTS = {"pricing", "plans", "price", "products", "product", "shop", "store", "services", "service",
                    "solutions", "faq", "faqs", "help", "support", "docs", "menu", "fees", "admissions",
                    "admission", "courses", "course", "locations", "location"}


def _rec(rid, check_id, category, title, rationale, steps, status, confidence, pages=(), evidence=(),
         summary=None, extra_action=None):
    action = {"summary": summary or title, "steps": list(steps), "priority": "low", "effort": "low",
              "expected_benefit": "Strengthens discoverability or engagement beyond fixing defects",
              "verification": "Re-run the audit after the change"}
    action.update(extra_action or {})
    rich = baseline_action(category) if check_id.startswith("baseline:") else None
    if rich:
        action["steps"] = list(rich["steps"])
        action["verification"] = rich["verification"]
    return apply_invariant_i1({
        "id": f"R-{rid:03d}", "check_id": check_id, "category": category,
        "finding_type": "proactive_improvement", "title": title, "severity": "low",
        "confidence": confidence, "status": status,
        "evidence_status": evidence_status_mode(status),
        "affected_pages": list(pages), "root_cause": rationale, "evidence": list(evidence),
        "evidence_text": "; ".join(e.get("description", "") for e in evidence),
        "suggested_action": action,
        "provenance": {"source": "baseline_calibrated" if status == "not_applicable" else "beyond_defects"},
    })


def _beyond_items(artifacts, findings):
    """Evidence-derived suggestions that no detector reports as a problem."""
    if artifacts is None:
        return []
    from check_helpers import content_pages
    from structured_data import iter_nodes, types_of
    pages = content_pages(artifacts, require_features=False)
    items = []
    has_search_ui = [p.url for p in pages if (p.features or {}).get("search")]
    has_search_action = any("SearchAction" in types_of(n) for p in pages for n in iter_nodes(p.jsonld_blocks))
    if has_search_ui and not has_search_action:
        items.append(dict(
            check_id="beyond:search-action", category="engagement",
            title="Declare the on-site search to agents with a WebSite SearchAction",
            rationale="A site-search input was observed, but no WebSite SearchAction declares it.",
            steps=["Add a WebSite JSON-LD node with potentialAction SearchAction",
                   "Set urlTemplate to the real search URL, e.g. https://example.com/search?q={search_term_string}"],
            status="confirmed", confidence=0.7, pages=has_search_ui[:5],
            evidence=[{"type": "html_observation", "description": "search input present; no SearchAction in JSON-LD",
                       "urls": has_search_ui[:5]}]))
    landing = []
    for p in pages:
        intent = intent_of(p.url)
        if intent not in _LANDING_INTENTS:
            continue
        opening = ((p.features or {}).get("opening_paragraphs") or [""])[0]
        if not opening or len(opening) > 320:
            landing.append((p.url, intent, len(opening)))
    if landing:
        items.append(dict(
            check_id="beyond:ai-landing-pages", category="engagement",
            title="Make the pages AI assistants send visitors to open with the answer",
            rationale="These high-intent pages are the likely landing pages for AI-referred visitors, and their "
                      "opening does not state a short, direct answer.",
            steps=["Open each listed page with a 2-3 sentence answer-first summary of its key facts",
                   "Place one primary next step (compare, buy, book, contact) directly under it"],
            status="confirmed", confidence=0.6, pages=[u for u, _, _ in landing[:8]],
            evidence=[{"type": "html_observation",
                       "description": f"{intent} page: " + ("no opening paragraph" if not n else f"first paragraph is {n} characters"),
                       "urls": [u]} for u, intent, n in landing[:6]]))
    return items


def is_quick_win(finding):
    """Worth doing and cheap: medium severity or above, low effort, and evidence
    strong enough (confidence >= 0.6) that the fix is not a gamble."""
    a = finding.get("suggested_action") or {}
    return (finding.get("severity") in ("critical", "high", "medium") and a.get("effort") == "low"
            and (finding.get("confidence") or 0) >= 0.6 and finding.get("status") != "insufficient_evidence")


def build_action_plan(findings, limit=12):
    """Ordered to-do list referencing findings by id (no duplicated content).
    Each row says whether it is a quick win (impact x effort); the first row is
    marked start_here so a non-expert knows where to begin."""
    # Same order as the findings array (severity first, then priority_score).
    from prioritize_findings import prioritize_findings
    ranked = prioritize_findings(list(findings))
    plan = []
    for rank, f in enumerate([f for f in ranked if f["status"] != "insufficient_evidence"][:limit], 1):
        a = f.get("suggested_action") or {}
        plan.append({"rank": rank, "finding_ids": [f["id"]], "summary": a.get("summary", f["title"]),
                     "severity": f["severity"], "priority": a.get("priority"), "effort": a.get("effort"),
                     "owner_role": a.get("owner_role"), "priority_score": f.get("priority_score", 0),
                     "quick_win": is_quick_win(f), "start_here": rank == 1})
    return plan


def top_actions(plan, limit=5):
    """The first rows of the action plan in the compact top_actions shape."""
    return [{"finding_id": a["finding_ids"][0], "summary": a["summary"], "priority": a["priority"],
             "severity": a["severity"], "effort": a["effort"], "owner_role": a["owner_role"],
             "quick_win": a.get("quick_win", False), "start_here": a.get("start_here", False)}
            for a in plan[:limit]]


def quick_wins(plan):
    """Finding ids of every quick win in the action plan, in plan order."""
    return [a["finding_ids"][0] for a in plan if a.get("quick_win")]


def generate_recommendations(skill_results: list, merged_findings: list, artifacts=None) -> list:
    covered = {f["category"] for f in merged_findings}
    raw = _beyond_items(artifacts, merged_findings)
    for item in _GENERIC_BASELINE:
        if item["category"] not in covered:
            raw.append(dict(check_id="baseline:" + item["category"], category=item["category"], title=item["title"],
                            rationale=item["rationale"], steps=item["steps"], status="not_applicable",
                            confidence=item["confidence"]))
    if not raw:
        b = _GENERIC_BASELINE[0]
        raw.append(dict(check_id="baseline:ai_discoverability", category=b["category"], title=b["title"],
                        rationale=b["rationale"], steps=b["steps"], status="not_applicable", confidence=b["confidence"]))
    recs = [_rec(i, **item) for i, item in enumerate(raw, 1)]
    return [enrich_finding(r) for r in recs]
