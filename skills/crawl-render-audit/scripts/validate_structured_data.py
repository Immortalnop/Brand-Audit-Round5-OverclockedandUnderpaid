"""validate_structured_data.py -- is the JSON-LD that exists complete, well-formed
and consistent with the visible page?

analyze_machine_readability.py answers "is the right @type present?". This script
answers the next three questions for every typed node on every content page:

  schema-missing-required     required properties absent (an Offer without price);
                              the node cannot be used for the fact it carries
  schema-invalid-value        clearly malformed values (non-numeric price, non-ISO
                              currency/date, relative URL)
  schema-visible-mismatch     the markup states a different fact than the page:
                              Offer price not shown anywhere on the page, or the
                              Organization name absent from title and text
  schema-missing-recommended  freshness/identity properties absent (dateModified,
                              sameAs, logo ...): hygiene tier unless the property
                              is in schema_rules.CORE_RECOMMENDED

Rules and validators live in common/schema_rules.py.
"""
from collections import defaultdict
from models import skill_result, make_finding
from check_helpers import content_pages
from structured_data import iter_nodes, types_of
from schema_rules import rule_for, missing, invalid_values, price_numbers, norm_price, CORE_RECOMMENDED

_HIGH_REQUIRED = {"Product", "Offer", "AggregateOffer", "LocalBusiness"}
_NESTED_VALIDATED = {"Offer", "AggregateOffer"}


def _validated_nodes(blocks):
    """Top-level nodes and @graph members are validated in full. Nodes embedded as
    a property value (an Organization as `publisher`, a Brand, a Person author) are
    descriptions, not standalone entities, and are not held to the standalone
    required properties -- except offers, whose price IS the fact they carry."""
    tops = []
    for b in (blocks if isinstance(blocks, (list, tuple)) else [blocks]):
        if hasattr(b, "get"):
            graph = b.get("@graph")
            tops.extend(graph if isinstance(graph, (list, tuple)) else [b])
        elif isinstance(b, (list, tuple)):
            tops.extend(b)
    top_ids = {id(t) for t in tops}
    for node in iter_nodes(blocks):
        if id(node) in top_ids or (types_of(node) & _NESTED_VALIDATED):
            yield node


def validate_structured_data(artifacts, deadline):
    pages = content_pages(artifacts, require_features=False)
    req = defaultdict(list)       # (type, prop) -> urls
    rec = defaultdict(list)
    bad = defaultdict(list)       # (prop, expected) -> [(url, value)]
    mismatch = []                 # (url, description)
    nodes_checked = 0
    for p in pages:
        visible = ((p.visible_text or "") + " " + (p.title or "")).lower()
        page_prices = price_numbers(p.visible_text or "")
        for node in _validated_nodes(p.jsonld_blocks):
            if set(node.keys()) <= {"@type", "@id"}:
                continue  # a reference stub; the full node is validated where it is defined
            rule_type, rule = rule_for(types_of(node))
            if not rule:
                continue
            nodes_checked += 1
            r, c = missing(node, rule)
            for prop in r:
                req[(rule_type, prop)].append(p.url)
            for prop in c:
                rec[(rule_type, prop)].append(p.url)
            for prop, value, expected in invalid_values(node):
                bad[(prop, expected)].append((p.url, value))
            if rule_type in ("Offer", "AggregateOffer") and page_prices and (p.visible_text or "").strip():
                price = norm_price(node.get("price") or node.get("lowPrice"))
                if price and price not in page_prices and price != "0":
                    mismatch.append((p.url, f"markup price {node.get('price') or node.get('lowPrice')} "
                                            f"{node.get('priceCurrency', '')} not shown on the page "
                                            f"(visible prices: {', '.join(sorted(page_prices)[:5])})"))
            if rule_type == "Organization" and p.page_type == "home":
                name = str(node.get("name") or "").strip().lower()
                if len(name) >= 3 and name not in visible and len(visible) > 300:
                    mismatch.append((p.url, f"Organization name '{node.get('name')}' does not appear in the page "
                                            "title or visible text"))

    findings = []
    if req:
        lines = [f"{t}: missing {prop} on {len(urls)} page(s)" for (t, prop), urls in sorted(req.items())]
        urls = sorted({u for v in req.values() for u in v})
        high = any(t in _HIGH_REQUIRED for t, _ in req)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="high" if high else "medium",
            status="confirmed", confidence=0.9,
            title="Structured data is missing required properties",
            root_cause="Typed JSON-LD nodes lack the properties consumers need to use them: " + "; ".join(lines[:4]),
            evidence=[{"type": "structured_data", "description": line,
                       "urls": sorted(set(req[k]))[:10]} for line, k in zip(lines, sorted(req))][:8],
            affected_pages=urls,
            suggested_action={
                "summary": "Complete the required properties on each listed JSON-LD node",
                "steps": [f"{t}: add {prop}" for t, prop in sorted(req)][:6]
                         + ["Fill values from the same source as the visible page", "Re-validate with a schema.org validator"],
                "priority": "high" if high else "medium", "effort": "low",
                "expected_benefit": "Nodes become usable for the facts they carry",
                "verification": "Every listed node validates with its required properties"},
            provenance={"skill": "crawl-render-audit", "script": "validate_structured_data.py",
                        "rule_id": "schema-missing-required"}))
    if bad:
        lines = [f"{prop} should be {expected}; found " + ", ".join(sorted({repr(v) for _, v in items})[:3])
                 for (prop, expected), items in sorted(bad.items())]
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="medium", status="confirmed",
            confidence=0.9, title="Structured data contains malformed values",
            root_cause="Some JSON-LD values are in a format consumers reject: " + "; ".join(lines[:3]),
            evidence=[{"type": "structured_data", "description": line,
                       "urls": sorted({u for u, _ in items})[:10]} for line, items in zip(lines, [bad[k] for k in sorted(bad)])][:8],
            affected_pages=sorted({u for items in bad.values() for u, _ in items}),
            suggested_action={
                "summary": "Correct each malformed value to the expected format",
                "steps": [f"{prop}: use {expected}" for prop, expected in sorted(bad)][:6],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Markup validates and is not discarded",
                "verification": "A schema.org validator reports no value errors"},
            provenance={"skill": "crawl-render-audit", "script": "validate_structured_data.py",
                        "rule_id": "schema-invalid-value"}))
    if mismatch:
        findings.append(make_finding(
            category="corroboration", finding_type="defect", severity="high", status="confirmed", confidence=0.85,
            title="Structured data contradicts the visible page",
            root_cause="The markup states facts that the visible page does not: " + "; ".join(d for _, d in mismatch[:2]),
            evidence=[{"type": "fact_consistency", "description": d, "urls": [u]} for u, d in mismatch[:8]],
            affected_pages=sorted({u for u, _ in mismatch}),
            suggested_action={
                "summary": "Make the markup and the visible page state the same fact",
                "steps": ["Find which of the two values is current",
                          "Generate the JSON-LD from the same data source as the visible value"],
                "priority": "high", "effort": "medium",
                "expected_benefit": "Assistants cannot pick up a stale or wrong value from the markup",
                "verification": "Markup values appear verbatim on the page"},
            provenance={"skill": "crawl-render-audit", "script": "validate_structured_data.py",
                        "rule_id": "schema-visible-mismatch"}))
    core_rec = {k: v for k, v in rec.items() if k[1] in CORE_RECOMMENDED}
    for bucket, tier_core in ((core_rec, True), ({k: v for k, v in rec.items() if k not in core_rec}, False)):
        if not bucket:
            continue
        lines = [f"{t}: no {prop} on {len(urls)} page(s)" for (t, prop), urls in sorted(bucket.items())]
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement",
            severity="low", status="confirmed", confidence=0.85,
            title=("Structured data lacks freshness or identity properties" if tier_core
                   else "Structured data could carry more recommended properties"),
            root_cause="; ".join(lines[:4]),
            evidence=[{"type": "structured_data", "description": line, "urls": sorted(set(bucket[k]))[:10]}
                      for line, k in zip(lines, sorted(bucket))][:8],
            affected_pages=sorted({u for v in bucket.values() for u in v}),
            suggested_action={
                "summary": "Add the listed recommended properties where the information exists",
                "steps": [f"{t}: add {prop}" for t, prop in sorted(bucket)][:6],
                "priority": "low", "effort": "low",
                "expected_benefit": "Markup carries freshness and identity signals",
                "verification": "Re-run the audit"},
            provenance={"skill": "crawl-render-audit", "script": "validate_structured_data.py",
                        "rule_id": "schema-missing-recommended"}))
        if tier_core:
            findings[-1]["tier_override"] = "core"
    return skill_result("crawl-render-audit", findings=findings,
                        metrics={"structured_nodes_checked": nodes_checked, "required_gaps": len(req),
                                 "invalid_values": sum(len(v) for v in bad.values()), "fact_mismatches": len(mismatch)})
