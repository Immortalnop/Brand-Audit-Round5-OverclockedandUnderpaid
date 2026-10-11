"""merge_findings.py -- concrete, defined deduplication algorithm."""
import re

_STOPWORDS = {"a", "an", "the", "is", "are", "was", "were", "be", "been", "of", "to",
              "in", "on", "for", "with", "and", "or", "that", "this", "it", "its",
              "as", "by", "at", "from", "has", "have", "had"}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    tokens = [t for t in tokens if t not in _STOPWORDS]
    lemmas = []
    for t in tokens:
        for suf in ("ing", "edly", "ed", "es", "s"):
            if t.endswith(suf) and len(t) - len(suf) >= 3:
                t = t[: -len(suf)]
                break
        lemmas.append(t)
    return " ".join(sorted(lemmas))


def dedup_key(finding: dict) -> tuple:
    normalized_cause = normalize_text(finding["root_cause"])
    return (
        finding["category"],
        normalized_cause,
        tuple(sorted(finding.get("affected_pages") or [])) or ("site-wide",),
    )


def _token_set(s: str) -> set:
    return set(s.split())


def similarity(a: str, b: str) -> float:
    ta, tb = _token_set(a), _token_set(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _is_robots_inaccessible_finding(finding: dict) -> bool:
    cid = finding.get("check_id") or (finding.get("provenance") or {}).get("rule_id")
    if cid in ("robots-unreachable", "ai-crawler-unchecked"):
        return True
    if cid == "fetch-failure":
        urls = list(finding.get("affected_pages") or []) + [
            u for e in (finding.get("evidence") or []) if isinstance(e, dict) for u in e.get("urls", [])
        ]
        if any(isinstance(u, str) and (u.endswith("/robots.txt") or "/robots.txt" in u) for u in urls):
            return True
    return False


def find_matching_bucket(finding: dict, buckets: dict, similarity_threshold: float = 0.85):
    if _is_robots_inaccessible_finding(finding):
        cascade_key = ("ai_discoverability", "robots-inaccessible-cascade", ("site-wide",))
        return cascade_key if cascade_key in buckets else None
    key = dedup_key(finding)
    if key in buckets:
        return key
    cat = finding["category"]
    scope = tuple(sorted(finding.get("affected_pages") or [])) or ("site-wide",)
    norm_cause = normalize_text(finding["root_cause"])
    for existing_key in buckets:
        e_cat, e_cause, e_scope = existing_key
        if e_cat == cat and e_scope == scope and similarity(norm_cause, e_cause) >= similarity_threshold:
            return existing_key
    return None


# Checks from different skills that report one underlying problem with one fix.
# Their findings merge into a single finding whatever their wording or pages:
#   images: images with no alt attribute (engagement) and content images with no
#     alt text, caption or link text (crawl-render) both mean "describe the image".
#   primary-heading: no H1, no descriptive opening heading on content pages, and
#     weak homepage orientation all mean "lead each page with a descriptive H1".
_FAMILIES = {
    "missing-alt": "image-text-alternative",
    "image-context-missing": "image-text-alternative",
    "h1": "primary-heading",
    "page-orientation": "primary-heading",
    "homepage-orientation": "primary-heading",
}
# Title of a merged family finding: true of every page the merged checks name.
_FAMILY_TITLES = {
    "image-text-alternative": "Images have no text alternative: no alt text, caption or link text says what they show",
    "primary-heading": "Pages lack a descriptive primary heading (H1) that says what the page is about",
}
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _family_key(finding: dict):
    cid = finding.get("check_id") or (finding.get("provenance") or {}).get("rule_id")
    family = _FAMILIES.get(cid)
    # The first element never equals a real category, so a family bucket is
    # matched only through this key.
    return ("family", family, ("site-wide",)) if family else None


def _evidence_key(item: dict) -> tuple:
    """Canonical, hashable key for one evidence entry, used to drop exact
    duplicates when merging evidence from multiple contributing findings."""
    return (
        item.get("type"),
        item.get("description"),
        tuple(sorted(item.get("urls") or [])),
    )


def merge_evidence(group: list, by_severity: bool = False) -> dict:
    """One finding from a group. The representative is the most confident one, or
    for a family of related checks the most severe (then most confident) one, so a
    merge never lowers the severity the reader sees."""
    if by_severity:
        best = max(group, key=lambda f: (_SEVERITY_RANK.get(f.get("severity"), 0), f.get("confidence", 0)))
    else:
        best = max(group, key=lambda f: (f.get("confidence", 0), 1 if f.get("check_id") == "robots-unreachable" else 0))
    evidence, provenance = [], []
    seen_evidence = set()
    for f in group:
        for item in f.get("evidence") or []:
            key = _evidence_key(item)
            if key in seen_evidence:
                continue
            seen_evidence.add(key)
            evidence.append(item)
        provenance.append(f.get("provenance"))
    merged = dict(best)
    merged["check_ids"] = sorted({f["check_id"] for f in group if f.get("check_id")})
    merged["evidence"] = evidence
    from models import make_evidence_text
    merged["evidence_text"] = make_evidence_text(evidence)
    merged["provenance"] = {"contributing_skills": provenance}
    all_pages = sorted(set(p for f in group for p in (f.get("affected_pages") or [])))
    if all_pages:
        merged["affected_pages"] = all_pages
    return merged


def merge_findings(results: list) -> list:
    """Input MUST be list[SkillResult]; intermediate artifacts are rejected outright."""
    for r in results:
        if "skill" not in r or "findings" not in r:
            raise ValueError("merge_findings accepts SkillResult objects only")

    buckets: dict = {}
    all_findings = [f for r in results for f in r["findings"]]
    for finding in all_findings:
        if _is_robots_inaccessible_finding(finding):
            key = ("ai_discoverability", "robots-inaccessible-cascade", ("site-wide",))
        elif _family_key(finding):
            key = _family_key(finding)
        else:
            match = find_matching_bucket(finding, buckets, similarity_threshold=0.85)
            key = match or dedup_key(finding)
        buckets.setdefault(key, []).append(finding)
    merged = []
    for key, group in buckets.items():
        finding = merge_evidence(group, by_severity=key[0] == "family")
        if key[0] == "family" and len(finding["check_ids"]) > 1:
            finding["title"] = _FAMILY_TITLES[key[1]]
        merged.append(finding)
    return merged
