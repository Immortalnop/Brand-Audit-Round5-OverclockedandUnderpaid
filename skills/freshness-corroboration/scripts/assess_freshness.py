"""assess_freshness.py -- contextual date-review opportunities and invalid dates.
Missing or older dates do not establish factual staleness. Expired offers have
their own explicit validity check in check_offer_expiry.py.

Fact-category calibration: an old date means different things depending on what
it's attached to (see extract_claims.py). "Historical" facts (founding dates,
company-history mentions) are *supposed* to be old and are never flagged as stale.
Other older dates produce low review opportunities. A publication date or page
timestamp does not demonstrate an expired price, an incorrect contact detail or
a changed operational fact. Verify the underlying fact before recommending edits.

Two date sources are combined:
  - dates mentioned in visible text (extract_claims). When the full claims
    artifact is supplied, every text date is assessed, not only the dates that
    survived the important-facts ranking, where dates rank lowest.
  - explicit JSON-LD datePublished/dateModified (extract_claims.structured_date_claims).
    A page whose JSON-LD declares a recent update is not reported for old
    editorial dates in its text: the declared update supersedes them. Invalid
    structured dates (not ISO 8601, in the future, or modified before published)
    are reported separately as structured-date-invalid.
  - page update dates declared outside the text: sitemap <lastmod> and the HTTP
    Last-Modified header (update_signals). A page claim is added only when it is
    more recent than every JSON-LD date on that page, and a recent update from
    any source supersedes old editorial dates in the page text. Missing,
    invalid or build-stamped lastmod values are reported as
    sitemap-lastmod-unreliable.
"""
from datetime import datetime, timezone
import re
from models import skill_result, make_finding, coverage_ratio, scale_confidence
from extract_claims import structured_date_claims
from update_signals import page_update_claims

# category -> (severity, human label used in the finding title/root_cause)
_CATEGORY_CALIBRATION = {
    "commercial": ("high", "commercial (pricing/offer) facts"),
    "contact": ("high", "contact facts"),
    "operational": ("medium", "operational facts"),
    "editorial": ("low", "editorial (article/blog) dates"),
    "legal": ("low", "legal/boilerplate dates"),
}
# Historical facts (founding dates, "since 1998"-style claims) are expected to be
# old; being old is not evidence of staleness for this category, so it is excluded
# from staleness detection entirely rather than assigned a low severity.
# "unclassified" text dates (extract_claims.py) sit on pages whose type says
# nothing about them and in sentences with no operational cue, so their age alone
# is no evidence that a current fact is stale either.
_EXCLUDED_FROM_STALENESS = {"historical", "unclassified"}
_STALE_AFTER_YEARS = 3
_ISSUE_TEXT = {
    "invalid_calendar": "is an impossible calendar date or time in the supported ISO form",
    "future": "is in the future",
    "modified_before_published": "is earlier than datePublished",
}


_DECLARED_ORIGINS = ("jsonld", "update_signal")


def _years(fact):
    if fact.get("origin") in _DECLARED_ORIGINS:
        return [int(fact["iso_date"][:4])]
    return [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", str(fact["value"]))]


def _dedupe(facts):
    seen, out = set(), []
    for fact in facts:
        key = (fact.get("source"), fact.get("predicate"), str(fact.get("value")))
        if key not in seen:
            seen.add(key)
            out.append(fact)
    return out


def _describe(fact):
    if fact.get("origin") == "jsonld":
        return f"JSON-LD {fact['predicate']} {fact['value']} ({fact.get('subject', 'entity')})"
    if fact.get("origin") == "update_signal":
        return f"{fact['predicate']} {fact['value']} (page last updated {fact['iso_date']})"
    return str(fact["value"])


def _invalid_dates_finding(issues):
    unique = _dedupe([{"source": i["source"], "predicate": i["field"] + i["issue"], "value": i["value"], **i}
                      for i in issues])
    evidence = []
    for issue in unique[:10]:
        detail = _ISSUE_TEXT[issue["issue"]]
        if issue["issue"] == "modified_before_published":
            detail += f" ({issue.get('published')})"
        evidence.append({"type": "structured_date",
                         "description": f"{issue['field']} '{issue['value']}' on {issue['subject']} {detail}",
                         "urls": [issue["source"]]})
    return make_finding(
        category="freshness", finding_type="defect", severity="low",
        status="confirmed", confidence=0.9,
        title="JSON-LD publication or update dates are invalid",
        root_cause="Structured datePublished/dateModified values are unparseable, in the future, "
                   "or inverted, so they cannot serve as a reliable freshness signal",
        evidence=evidence,
        affected_pages=sorted({i['source'] for i in unique}),
        suggested_action={
            "summary": "Correct the invalid datePublished and dateModified values",
            "steps": ["Emit both dates in ISO 8601 form, for example 2026-03-01 or 2026-03-01T09:00:00Z",
                      "Keep dateModified on or after datePublished",
                      "Never set a publication or update date in the future"],
            "priority": "low", "effort": "low",
            "expected_benefit": "Crawlers can read and trust the declared publication and update dates",
            "verification": "Re-run the audit and validate the markup with a structured-data validator",
        },
        provenance={"skill": "freshness-corroboration", "script": "assess_freshness.py",
                    "rule_id": "structured-date-invalid"},
    )


def _sitemap_lastmod_finding(sitemap_data, quality):
    """sitemap-lastmod-unreliable: the sitemap was read but gives crawlers no usable
    update dates (none declared, invalid values, or one date stamped on nearly
    every URL). Returns None when the sitemap was not read or its dates are fine."""
    if sitemap_data.get("status") != "ok" or not quality["url_entries"]:
        return None
    evidence, confirmed = [], False
    if not quality["with_lastmod"]:
        confirmed = True
        evidence.append({"type": "sitemap_lastmod",
                         "description": f"None of the {quality['url_entries']} sitemap URL entries "
                                        f"declares <lastmod>"})
    for item in quality["invalid"][:5]:
        confirmed = True
        detail = {"unparseable": "is not a date in W3C Datetime form",
                  "nonstandard": "is not in W3C Datetime form (a 'T' must separate date and time); "
                                 "its date was still used",
                  "future": "is in the future"}[item["issue"]]
        evidence.append({"type": "sitemap_lastmod", "description": f"lastmod '{item['value']}' {detail}",
                         "urls": [item["url"]]})
    if quality["uniform"]:
        u = quality["uniform"]
        evidence.append({"type": "sitemap_lastmod",
                         "description": f"{u['count']} of {u['of']} valid lastmod values are the same date "
                                        f"({u['date']}), so they reflect when the sitemap was generated, "
                                        f"not when each page changed"})
    if not evidence:
        return None
    invalid = bool(quality["invalid"])
    return make_finding(
        category="freshness", finding_type="defect" if invalid else "proactive_improvement",
        severity="low", status="confirmed" if confirmed else "suspected",
        confidence=0.85 if confirmed else 0.6,
        title="Sitemap lastmod dates are missing or unreliable",
        root_cause="Sitemap lastmod dates are missing, malformed or not set per page, so crawlers "
                   "cannot rely on them to recrawl changed pages first",
        evidence=evidence, affected_pages=[],
        suggested_action={
            "summary": "Publish an accurate <lastmod> for every sitemap URL",
            "steps": ["Set lastmod from the date each page's content last changed, not the build time",
                      "Use W3C Datetime, for example 2026-03-01 or 2026-03-01T09:00:00+00:00",
                      "Never declare a future date"],
            "priority": "low", "effort": "low",
            "expected_benefit": "Search and AI crawlers recrawl updated pages sooner and keep trusting the dates",
            "verification": "Re-run the audit and compare lastmod values with real content changes",
        },
        provenance={"skill": "freshness-corroboration", "script": "assess_freshness.py",
                    "rule_id": "sitemap-lastmod-unreliable"},
    )


def assess_freshness(facts, artifacts, deadline, claims=None):
    fact_list = facts.get("data", {}).get("facts", [])
    pool = list(fact_list)
    if claims is not None:
        pool += claims.get("data", {}).get("claims", [])
    text_dates = _dedupe([f for f in pool if f.get("type") == "date" and f.get("origin") != "jsonld"])
    structured, issues = structured_date_claims(artifacts.pages)
    limitations = [i for i in issues if i['issue'] == 'unsupported_format']
    issues = [i for i in issues if i['issue'] != 'unsupported_format']
    limitation_warnings = [f"Unsupported date format on {i['source']}: {i['field']}; not assessed as invalid." for i in limitations[:10]]
    structured = _dedupe(structured)
    page_updates, update_metrics, lastmod_quality = page_update_claims(
        artifacts.pages, artifacts.sitemap_data)
    newest_structured = {}
    for f in structured:
        newest_structured[f["source"]] = max(newest_structured.get(f["source"], ""), f["iso_date"])
    # A page update date adds information only when it is newer than every JSON-LD
    # date already declared on that page; otherwise the JSON-LD claim speaks for it.
    page_updates = [f for f in page_updates if f["iso_date"] > newest_structured.get(f["source"], "")]
    date_facts = text_dates + structured + page_updates
    lastmod_finding = _sitemap_lastmod_finding(artifacts.sitemap_data, lastmod_quality)

    if not date_facts and not issues and lastmod_finding is None:
        return skill_result(
            "freshness-corroboration",
            status='insufficient_evidence',
            metrics=dict(update_metrics, structured_date_limitations=len(limitations)),
            warnings=['No dated facts found; freshness cannot be assessed (absence is not proof of staleness).'] + limitation_warnings,
        )

    current_year = datetime.now(timezone.utc).year
    cutoff = current_year - _STALE_AFTER_YEARS
    recently_updated = {f["source"] for f in structured + page_updates if _years(f)[0] >= cutoff}
    superseded = [f for f in text_dates
                  if f.get("category") == "editorial" and f.get("source") in recently_updated]
    superseded_ids = {id(f) for f in superseded}
    candidates = [f for f in date_facts if id(f) not in superseded_ids]
    stale_all = [f for f in candidates if any(y < cutoff for y in _years(f))]
    stale_assessable = [f for f in stale_all if f.get("category") not in _EXCLUDED_FROM_STALENESS]
    excluded_count = len(stale_all) - len(stale_assessable)

    by_category = {}
    for f in stale_assessable:
        by_category.setdefault(f.get("category", "operational"), []).append(f)

    # Evidence completeness: dated facts only come from pages actually crawled, so
    # a stale-facts finding only ever speaks for that slice of the site. Scale
    # confidence/severity by how much of the discovered site was analyzed, and
    # separately note when a category's finding rests on a single fact (Round-3
    # review item 1: findings from thin samples should read as less certain than
    # ones backed by several corroborating mentions).
    acq_coverage = artifacts.acquisition_metadata.get("coverage", {})
    crawl_ratio = coverage_ratio(
        acq_coverage.get("urls_analyzed", len(artifacts.pages)),
        acq_coverage.get("urls_discovered", len(artifacts.pages)),
    )

    findings = []
    for category, facts_in_category in by_category.items():
        _, label = _CATEGORY_CALIBRATION.get(category, ("low", f"{category} facts"))
        severity = 'low'
        sample_ratio = min(crawl_ratio, coverage_ratio(len(facts_in_category), 3))
        findings.append(make_finding(
            category="freshness", finding_type="proactive_improvement",
            severity=severity,
            status="suspected", confidence=scale_confidence(0.6, sample_ratio),
            title=f"Older dates among {label} need contextual verification",
            root_cause=f"Older dates classified as '{category}' warrant a contextual review; age alone does not establish that a current fact is wrong"
                       + ("" if crawl_ratio >= 0.999 else " (within the pages actually crawled; the "
                                                           "rest of the site was not analyzed)"),
            evidence=[{"type": "date", "description": _describe(f), "urls": [f["source"]]}
                      for f in facts_in_category[:5]],
            affected_pages=sorted({f["source"] for f in facts_in_category if f.get("source")}),
            suggested_action={
                "summary": f"Verify whether older {label} still describe the current situation",
                "steps": [f"Review the context and current accuracy of older {label}", "Correct a fact only if it has changed; preserve valid publication and historical dates", "Set an update date only after a meaningful content change"],
                "priority": severity, "effort": "low",
                "expected_benefit": "Reduces risk of assistants citing stale facts",
                "verification": "Check the underlying fact against a current authoritative source; a newer date alone does not prove accuracy",
            },
            provenance={"skill": "freshness-corroboration", "script": "assess_freshness.py",
                        "rule_id": f"stale-dates:{category}"},
        ))
    if issues:
        findings.append(_invalid_dates_finding(issues))
    if lastmod_finding is not None:
        findings.append(lastmod_finding)

    return skill_result(
        "freshness-corroboration", findings=findings,
        warnings=limitation_warnings,
        metrics={"date_facts_found": len(date_facts), "stale_facts": len(stale_assessable),
                 "text_date_facts": len(text_dates), "structured_date_facts": len(structured),
                 "page_update_date_facts": len(page_updates), **update_metrics,
                 "structured_date_issues": len(issues),
                 "structured_date_limitations": len(limitations),
                 "text_dates_superseded_by_structured_update": len(superseded),
                 "stale_facts_excluded_as_historical": excluded_count,
                 "stale_facts_by_category": {k: len(v) for k, v in by_category.items()}},
    )
