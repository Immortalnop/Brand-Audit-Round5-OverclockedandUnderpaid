"""analyze_citation_schema.py -- markup for the content assistants quote most.

Questions with answers, step-by-step instructions and review ratings are the
passages assistants lift into answers. FAQPage, HowTo, Review and AggregateRating
markup state them as explicit question/answer pairs, ordered steps and rating
numbers. This check reads the acquisition snapshot only (no requests):

  - citation-schema-invalid (defect): the markup is present but unusable, so
    parsers drop it. Examples: an FAQPage with no Question, a Question with no
    accepted answer text, FAQ questions that are not visible on the page, a HowTo
    with no steps, a Review with no rating value or author, an AggregateRating
    with no count, a rating outside its own scale, or a rating that is attached to
    nothing.
  - citation-schema-opportunity (suggestion): the page visibly carries the
    content (question headings, numbered steps, star ratings or review counts)
    but no matching markup.

Google limits FAQ rich results to a few site types and no longer shows HowTo rich
results; the value reported here is machine-readable structure, not a promised
search feature.
"""
import re
from collections.abc import Mapping

from check_helpers import eligible_pages
from models import make_finding, skill_result
from structured_data import normalize_type

_ITEM_TYPES = frozenset({"Product", "Service", "SoftwareApplication", "MobileApplication", "WebApplication",
                         "Organization", "LocalBusiness", "Corporation", "Restaurant", "Book", "Course",
                         "CreativeWork", "Event", "Recipe", "Movie", "Game", "HowTo", "Place", "Store",
                         "Hotel", "LodgingBusiness", "MediaObject", "VideoObject", "Offer"})
_FAQ_TYPES = frozenset({"FAQPage", "QAPage"})
_RATING_TEXT = re.compile(r"\b[0-5](?:[.,]\d)?\s*(?:/|out of)\s*5\b|\u2605{3,}|\b\d[\d,.]*\s+(?:customer\s+|verified\s+)?"
                          r"(?:reviews|ratings)\b", re.I)
_STEP_HEADING = re.compile(r"^\s*step\s*\d+\b", re.I)
_HOW_TO_TITLE = re.compile(r"^\s*how\s+to\b", re.I)


def _types(node):
    value = node.get("@type", ())
    values = value if isinstance(value, (list, tuple)) else [value]
    return {normalize_type(v) for v in values if isinstance(v, str)}


def walk(value, parent_key=None, depth=0):
    """Yield (node, parent_key) for every typed JSON-LD node; parent_key is None or
    '@graph' at the top level, otherwise the property that holds the node."""
    if depth > 40:
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk(item, parent_key, depth + 1)
    elif isinstance(value, Mapping):
        if "@type" in value:
            yield value, parent_key
        for key, child in value.items():
            if key != "@context" and isinstance(child, (Mapping, list, tuple)):
                yield from walk(child, key if key != "@graph" else parent_key if parent_key else "@graph",
                                depth + 1)


def _text(value):
    """Concatenated string content of a JSON-LD value."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        return " ".join(t for t in (_text(value.get(k)) for k in ("text", "name", "@value")) if t)
    if isinstance(value, (list, tuple)):
        return " ".join(t for t in (_text(v) for v in value) if t)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
            return float(text)
        if re.fullmatch(r"-?\d+,\d+", text):  # decimal comma, as in "4,5"
            return float(text.replace(",", "."))
    return None


def _count(value):
    if isinstance(value, str) and re.fullmatch(r"\d{1,3}(?:,\d{3})+", value.strip()):
        value = value.replace(",", "")
    number = _number(value)
    return number if number is not None and number >= 0 and number == int(number) else None


def _as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _norm(text):
    return " ".join(re.findall(r"\w+", text.lower()))


def _faq_problems(node, page):
    questions = [q for q in _as_list(node.get("mainEntity")) if isinstance(q, Mapping)]
    questions = [q for q in questions if "Question" in _types(q)] or questions
    if not questions:
        return ["FAQPage has no Question in mainEntity"]
    problems = []
    unanswered = 0
    for q in questions:
        answers = _as_list(q.get("acceptedAnswer")) or _as_list(q.get("suggestedAnswer"))
        if not _text(q.get("name")) or not any(_text(a) for a in answers):
            unanswered += 1
    if unanswered:
        problems.append(f"{unanswered} of {len(questions)} FAQ question(s) lack a question name or "
                        f"accepted answer text")
    names = [_norm(_text(q.get("name")))[:80] for q in questions if _text(q.get("name"))]
    if names and (page.features or {}).get("visible_text_complete", False):
        visible = _norm(page.visible_text or "")
        shown = sum(1 for n in names if n and n in visible)
        if shown * 2 < len(names):
            problems.append(f"only {shown} of {len(names)} FAQ questions in the markup appear in the "
                            f"visible page text")
    return problems


def _howto_problems(node):
    steps = _as_list(node.get("step"))
    if not steps:
        return ["HowTo has no step"]
    empty = 0
    for step in steps:
        if isinstance(step, str):
            empty += not step.strip()
        elif isinstance(step, Mapping):
            inner = _as_list(step.get("itemListElement"))
            if not (_text(step.get("text")) or _text(step.get("name")) or any(_text(i) for i in inner)):
                empty += 1
    return [f"{empty} of {len(steps)} HowTo step(s) have no text"] if empty else []


def _rating_scale(rating):
    best = _number(rating.get("bestRating"))
    worst = _number(rating.get("worstRating"))
    return (worst if worst is not None else 1.0), (best if best is not None else 5.0)


def _review_problems(node, parent_key):
    problems = []
    rating = node.get("reviewRating")
    value = _number(rating.get("ratingValue")) if isinstance(rating, Mapping) else None
    if value is None:
        problems.append("Review has no numeric reviewRating.ratingValue")
    else:
        worst, best = _rating_scale(rating)
        if not worst <= value <= best:
            problems.append(f"Review rating {value:g} is outside its scale {worst:g} to {best:g}")
    if not _text(node.get("author")):
        problems.append("Review has no author name")
    if parent_key in (None, "@graph") and not node.get("itemReviewed"):
        problems.append("Review is not attached to an item (no itemReviewed and not nested in one)")
    return problems


def _aggregate_problems(node, parent_key):
    problems = []
    value = _number(node.get("ratingValue"))
    counts = [c for c in (_count(node.get("ratingCount")), _count(node.get("reviewCount"))) if c is not None]
    if value is None:
        problems.append("AggregateRating has no numeric ratingValue")
    else:
        worst, best = _rating_scale(node)
        if not worst <= value <= best:
            problems.append(f"AggregateRating {value:g} is outside its scale {worst:g} to {best:g}")
    if not counts:
        problems.append("AggregateRating has no ratingCount or reviewCount")
    elif max(counts) == 0:
        problems.append("AggregateRating declares zero ratings")
    if parent_key in (None, "@graph") and not node.get("itemReviewed"):
        problems.append("AggregateRating is not attached to an item (no itemReviewed and not nested in one)")
    return problems


def _page_markup(page):
    found, problems = set(), []
    nodes = list(walk(page.jsonld_blocks))
    # Ratings defined at the top level but referenced by an item, as in
    # {"@type": "Product", "aggregateRating": {"@id": "#rating"}}, are attached.
    referenced = {ref["@id"] for node, _ in nodes for key in ("aggregateRating", "review")
                  for ref in _as_list(node.get(key)) if isinstance(ref, Mapping) and isinstance(ref.get("@id"), str)}
    for node, parent_key in nodes:
        if parent_key in (None, "@graph") and node.get("@id") in referenced:
            parent_key = "referenced"
        types = _types(node)
        if types & _FAQ_TYPES:
            found.add("FAQPage")
            if "FAQPage" in types:
                problems.extend(_faq_problems(node, page))
        if "HowTo" in types:
            found.add("HowTo")
            problems.extend(_howto_problems(node))
        if "Review" in types or "EmployerReview" in types or "CriticReview" in types:
            found.add("Review")
            problems.extend(_review_problems(node, parent_key))
        if "AggregateRating" in types or "EmployerAggregateRating" in types:
            found.add("AggregateRating")
            problems.extend(_aggregate_problems(node, parent_key))
        if types & _ITEM_TYPES and (node.get("aggregateRating") or node.get("review")):
            found.add("AggregateRating" if node.get("aggregateRating") else "Review")
    microdata = set((page.features or {}).get("microdata_types", ()))
    found |= {t for t in ("FAQPage", "HowTo", "Review", "AggregateRating") if t in microdata}
    if microdata & {"QAPage"}:
        found.add("FAQPage")
    return found, list(dict.fromkeys(problems))


def _opportunities(page, found):
    features = page.features or {}
    english = (features.get("lang") or "").lower().split("-")[0] in ("en", "")
    out = []
    # FAQPage fits only questions the page itself answers: a question heading
    # followed by answer text. Headline teasers that link to other pages are not
    # counted as question headings at all, and neither are teasers whose text a
    # link to another page repeats (common/html_features.py).
    answered = sum(1 for qa in features.get("question_answers") or ()
                   if (qa.get("answer") or "").strip() and not qa.get("teaser"))
    if "FAQPage" not in found and answered >= 3:
        out.append(f"{answered} question-shaped H2/H3 headings with no FAQPage markup")
    headings = list(page.headings or ())
    steps = sum(1 for h in headings if _STEP_HEADING.match(h or ""))
    how_to = english and (_HOW_TO_TITLE.match(page.title or "") or any(_HOW_TO_TITLE.match(h or "")
                                                                       for h in headings[:2]))
    if "HowTo" not in found and how_to and (steps >= 3 or features.get("max_ordered_list_items", 0) >= 3):
        out.append("a 'How to' page with numbered steps and no HowTo markup")
    if (not found & {"AggregateRating", "Review"} and page.page_type in ("product", "service", "software")
            and _RATING_TEXT.search(page.visible_text or "")):
        match = _RATING_TEXT.search(page.visible_text or "")
        out.append(f"visible rating text ('{match.group(0)[:40]}') with no AggregateRating or Review markup")
    return out


def analyze_citation_schema(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Citation schema checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    invalid, opportunities, present = [], [], {}
    for page in pages:
        found, problems = _page_markup(page)
        for kind in found:
            present[kind] = present.get(kind, 0) + 1
        if problems:
            invalid.append((page, problems))
        gaps = _opportunities(page, found)
        if gaps:
            opportunities.append((page, gaps))

    findings = []
    if invalid:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="medium",
            status="confirmed", confidence=0.85,
            title="FAQ, HowTo or review markup is incomplete or inconsistent",
            root_cause="FAQPage, HowTo, Review or AggregateRating markup is missing required parts or "
                       "contradicts the page, so parsers discard it",
            affected_pages=[p.url for p, _ in invalid],
            evidence=[{"type": "structured_data", "description": "; ".join(problems[:5]), "urls": [page.url]}
                      for page, problems in invalid[:10]],
            suggested_action={
                "summary": "Repair the FAQ, HowTo and review markup so every required part is present",
                "steps": ["Give every FAQ Question a name and an acceptedAnswer with text, and show the same "
                          "questions on the page",
                          "Give every HowTo at least one HowToStep with text",
                          "Give every Review a numeric reviewRating.ratingValue and an author, and every "
                          "AggregateRating a ratingValue and a ratingCount or reviewCount inside its scale",
                          "Nest each rating in the Product, Service or other item it rates"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Question, step and rating facts become reliably machine-readable",
                "verification": "Validate the pages with a schema.org validator and re-run the audit"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_citation_schema.py",
                        "rule_id": "citation-schema-invalid"},
        ))
    if opportunities:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.6,
            title="Pages show questions, steps or ratings without matching markup",
            root_cause="Questions, numbered steps and ratings are visible on the page but are not stated "
                       "as FAQPage, HowTo or AggregateRating markup",
            affected_pages=[p.url for p, _ in opportunities],
            evidence=[{"type": "structured_data", "description": "; ".join(gaps), "urls": [page.url]}
                      for page, gaps in opportunities[:10]],
            suggested_action={
                "summary": "Mark up visible questions, steps and ratings where the content really is that",
                "steps": ["Add FAQPage markup only for genuine question-and-answer sections shown on the page",
                          "Add HowTo markup for real step-by-step instructions",
                          "Add AggregateRating to Product or Service markup only when the ratings shown are "
                          "real customer ratings"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Assistants can lift answers, steps and ratings as explicit facts",
                "verification": "Validate the pages with a schema.org validator and re-run the audit"},
            provenance={"skill": "crawl-render-audit", "script": "analyze_citation_schema.py",
                        "rule_id": "citation-schema-opportunity"},
        ))
    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"citation_schema_pages_analyzed": len(pages), "citation_schema_types_present": present,
                 "pages_with_invalid_citation_schema": len(invalid),
                 "pages_with_citation_schema_opportunity": len(opportunities)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0},
    )
