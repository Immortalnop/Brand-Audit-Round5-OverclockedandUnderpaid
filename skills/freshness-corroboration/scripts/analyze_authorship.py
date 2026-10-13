"""analyze_authorship.py -- who wrote it, and why should anyone trust them?

Assistants and search engines weigh experience, expertise, authority and trust
(E-E-A-T) when they choose which article to quote. The parts of that a page can
state are its author: a visible byline, an author in Article markup typed as a
Person, and that person's credentials and profile. This check reads the
acquisition snapshot only (no requests), on article pages:

  - author-missing: an article names no author anywhere: no byline, no meta
    author, no rel=author link and no author in its Article markup.
  - author-credentials-weak: an author is named, but lacks a typed Person or
    Organization identity/profile (url or sameAs), or a Person lacks credentials
    (jobTitle, description, knowsAbout, alumniOf, award, hasCredential), or the
    markup author is not shown on the page, or the byline has no markup.

A page is an article when its markup says so (Article, BlogPosting, NewsArticle
and similar), or when it sits under a blog or news path with a slug and carries a
substantial body. Section index pages are not held to these checks.
"""
import re
from collections.abc import Mapping
from urllib.parse import urlsplit

from check_helpers import eligible_pages
from models import make_finding, skill_result
from structured_data import iter_nodes, types_of

ARTICLE_TYPES = frozenset({"Article", "BlogPosting", "NewsArticle", "TechArticle", "ScholarlyArticle",
                           "Report", "AnalysisNewsArticle", "OpinionNewsArticle", "ReviewNewsArticle",
                           "LiveBlogPosting", "SocialMediaPosting"})
_CREDENTIAL_KEYS = ("jobTitle", "description", "knowsAbout", "alumniOf", "award", "hasCredential",
                    "hasOccupation", "worksFor")
_PROFILE_KEYS = ("url", "sameAs")
_BYLINE_TEXT = re.compile(r"^(?:By|by|Written by|written by|Author:)\s+([A-Z][\w.'\u2019-]+"
                          r"(?:\s+[A-Z][\w.'\u2019-]+){1,3})")
_AUTHOR_PATH = re.compile(r"/(?:authors?|team|people|contributors?|writers?|staff)/[^/?#]+", re.I)
_MIN_ARTICLE_WORDS = 300


def _name(value):
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, Mapping) and isinstance(value.get("name"), str):
        return " ".join(value["name"].split())
    return ""


def _as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def _has(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return any(_has(v) for v in value)
    if isinstance(value, Mapping):
        return any(_has(v) for k, v in value.items() if not str(k).startswith("@"))
    return value is not None and not isinstance(value, bool)


def is_article(page):
    if any(types_of(n) & ARTICLE_TYPES for n in iter_nodes(page.jsonld_blocks)):
        return True
    if page.page_type != "article":
        return False
    try:
        segments = [s for s in urlsplit(page.url).path.split("/") if s]
    except ValueError:
        return False
    features = page.features or {}
    body = features.get('body_text', page.visible_text or '')
    return len(segments) >= 2 and len(body.split()) >= _MIN_ARTICLE_WORDS


def _structured_authors(page):
    """[(name, kind, node)] for the authors of the page's article markup, with
    @id references resolved against the other nodes on the page."""
    nodes = list(iter_nodes(page.jsonld_blocks))
    by_id = {n.get("@id"): n for n in nodes if isinstance(n.get("@id"), str)}
    authors = []
    for node in nodes:
        if not types_of(node) & ARTICLE_TYPES:
            continue
        for raw in _as_list(node.get("author")) + _as_list(node.get("creator")):
            # A reference such as {"@id": "#author", "name": "Jo"} points at a node
            # defined elsewhere in the graph; merge it, keeping the reference's keys.
            if isinstance(raw, Mapping) and isinstance(raw.get("@id"), str) and raw["@id"] in by_id:
                raw = {**dict(by_id[raw["@id"]].items()), **dict(raw.items())}
            if isinstance(raw, str):
                authors.append((_name(raw), "text", None))
            elif isinstance(raw, Mapping):
                kind = "person" if "Person" in types_of(raw) else (
                    "organization" if types_of(raw) & {"Organization", "Corporation", "NewsMediaOrganization"}
                    else "untyped")
                authors.append((_name(raw), kind, raw))
    return [(n, k, node) for n, k, node in authors if n or node is not None]


def _visible_bylines(page):
    features = page.features or {}
    bylines = [b for b in features.get("bylines", ()) if b]
    bylines += [m for m in (features.get("meta") or {}).get("author", ()) if isinstance(m, str) and m.strip()]
    # Bare "by" in navigation or narrative is not a byline. Explicit author
    # elements/meta above remain supported; unmarked bylines start a paragraph.
    opening = (features.get('body_opening') or {}).get('passage', '')
    for paragraph in features.get('content_paragraphs', features.get('opening_paragraphs', ())):
        if paragraph not in opening: continue
        match = _BYLINE_TEXT.search(paragraph)
        if match: bylines.append(match.group(1))
    return bylines


def _profile_links(page):
    features = page.features or {}
    links = list(features.get("author_links", ()))
    links += [href for href, _ in features.get("anchors", ()) if _AUTHOR_PATH.search(href or "")]
    return links


def assess_page(page):
    """(missing, problems) for one article page."""
    authors = _structured_authors(page)
    bylines = _visible_bylines(page)
    profiles = _profile_links(page)
    if not authors and not bylines and not profiles:
        return True, []
    problems = []
    if not authors:
        problems.append("the byline is not stated in Article markup (no author property)")
    else:
        persons = [(n, node) for n, kind, node in authors if kind == "person"]
        organizations = [(n,node) for n,kind,node in authors if kind=='organization']
        if not persons and not organizations:
            kinds = sorted({kind for _, kind, _ in authors})
            problems.append("the Article author is " + " and ".join(
                {"text": "a plain name string", "organization": "an Organization",
                 "untyped": "an untyped object"}[k] for k in kinds) + ", not a Person or Organization")
        for name,node in organizations[:2]:
            if not name:problems.append('an Organization author has no name')
            if not any(_has(node.get(k)) for k in _PROFILE_KEYS) and not profiles:
                problems.append(f'Organization author {name or "(no name)"} has no profile link (url or sameAs)')
        for name, node in persons[:2]:
            label = f"author {name or '(no name)'}"
            if not name:
                problems.append("a Person author has no name")
            if not any(_has(node.get(k)) for k in _PROFILE_KEYS) and not profiles:
                problems.append(f"{label} has no profile link (url or sameAs) and no author page is linked")
            if not any(_has(node.get(k)) for k in _CREDENTIAL_KEYS):
                problems.append(f"{label} has no credentials in markup (jobTitle, description, knowsAbout, "
                                f"alumniOf, award or hasCredential)")
        names = [n for n, _, _ in authors if n]
        visible = (page.visible_text or "").lower()
        shown = " ".join(bylines).lower()
        if names and (page.features or {}).get("visible_text_complete", False) \
                and not any(n.lower() in visible or n.lower() in shown for n in names):
            problems.append(f"the markup author ({names[0][:60]}) is not named anywhere on the page")
    return False, list(dict.fromkeys(problems))


def analyze_authorship(artifacts, deadline):
    if deadline.expired():
        return skill_result("freshness-corroboration", status="insufficient_evidence",
                            warnings=["Authorship checks skipped: deadline reached."])
    articles = [p for p in eligible_pages(artifacts) if is_article(p)]
    missing, weak = [], []
    for page in articles:
        no_author, problems = assess_page(page)
        if no_author:
            missing.append(page)
        elif problems:
            weak.append((page, problems))

    findings = []
    if missing:
        findings.append(make_finding(
            category="answer_content", finding_type="proactive_improvement", severity="medium",
            status="confirmed", confidence=0.8,
            title="Articles do not name an author",
            root_cause="Articles name no author in a byline, meta author, author link or Article markup, "
                       "so assistants have no person to credit and no expertise to weigh",
            affected_pages=[p.url for p in missing],
            evidence=[{"type": "authorship",
                       "description": "No byline, meta author, rel=author link or Article author was found",
                       "urls": [p.url for p in missing[:10]]}],
            suggested_action={
                "summary": "Name the author of every article, on the page and in Article markup",
                "steps": ["Show a byline with the author's name near the article title",
                          "Add author to the Article markup as a Person with name and url",
                          "Link the byline to an author page that states the author's role and expertise"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Articles carry a named, checkable author that assistants can credit",
                "verification": "Re-run the audit; the articles should no longer be listed"},
            provenance={"skill": "freshness-corroboration", "script": "analyze_authorship.py",
                        "rule_id": "author-missing"},
        ))
    if weak:
        findings.append(make_finding(
            category="answer_content", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.75,
            title="Article authors have incomplete identity or profile signals",
            root_cause="Author identity or profile details are incomplete in the sampled article markup. "
                       "Both Person and Organization authors are supported; personal credentials apply to people",
            affected_pages=[p.url for p, _ in weak],
            evidence=[{"type": "authorship", "description": "; ".join(problems[:4]), "urls": [page.url]}
                      for page, problems in weak[:10]],
            suggested_action={
                "summary": "State the actual article author with a suitable identity and profile",
                "steps": ["Use Person for an individual author or Organization for an organizational author",
                          "Give the author a url or sameAs link to a matching profile",
                          "For a person, add accurate role or expertise details where appropriate",
                          "Show the same author name in the visible byline"],
                "priority": "low", "effort": "low",
                "expected_benefit": "The expertise behind each article becomes explicit and checkable",
                "verification": "Validate the Article markup and re-run the audit"},
            provenance={"skill": "freshness-corroboration", "script": "analyze_authorship.py",
                        "rule_id": "author-credentials-weak"},
        ))
    return skill_result(
        "freshness-corroboration", findings=findings,
        metrics={"article_pages_analyzed": len(articles), "articles_without_author": len(missing),
                 "articles_with_weak_author_signals": len(weak)},
        coverage={"pages_analyzed": len(articles), "pages_skipped": 0,
                  "queries_attempted": 0, "queries_completed": 0},
    )
