"""merge_findings.py -- concrete, defined deduplication algorithm.

Two passes:
 1. Exact/near-duplicate merge (unchanged): same category, same scope and a
    normalized root cause with token-Jaccard >= 0.85.
 2. Root-cause group merge (A14): findings from different checks -- even in
    different categories -- describe ONE problem when they share a catalog
    `group` (e.g. heading-structure: no-headings, h1, page-orientation) and their
    affected pages overlap (Jaccard >= 0.5, or one set contains the other). They
    become one finding that keeps every check_id, the union of pages and
    evidence, the most severe member's title/severity/category, and a combined,
    de-duplicated list of steps.
"""
import re
from check_catalog import meta_for

_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

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


def _evidence_key(item: dict) -> tuple:
    """Canonical, hashable key for one evidence entry, used to drop exact
    duplicates when merging evidence from multiple contributing findings."""
    return (
        item.get("type"),
        item.get("description"),
        tuple(sorted(item.get("urls") or [])),
    )


def merge_evidence(group: list) -> dict:
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


def _check_id(f):
    return f.get("check_id") or (f.get("provenance") or {}).get("rule_id") or ""


def _pages_overlap(a, b):
    a, b = set(a or ()), set(b or ())
    if not a or not b:
        return not a and not b
    return a <= b or b <= a or len(a & b) / len(a | b) >= 0.5


def _group_merge(findings: list) -> list:
    """A14: merge findings that share a root-cause group and overlapping pages."""
    out = []
    for f in findings:
        group = meta_for(_check_id(f)).get("group")
        target = None
        if group and f.get("status") != "insufficient_evidence":
            for g in out:
                if (g.get("_group") == group and g.get("status") != "insufficient_evidence"
                        and _pages_overlap(g.get("affected_pages"), f.get("affected_pages"))):
                    target = g
                    break
        if target is None:
            f = dict(f)
            f["_group"] = group
            out.append(f)
            continue
        lead, other = (target, f) if (_SEVERITY_RANK.get(target["severity"], 0), target.get("confidence", 0)) >= \
            (_SEVERITY_RANK.get(f["severity"], 0), f.get("confidence", 0)) else (f, target)
        merged = dict(lead)
        merged["_group"] = group
        merged["check_ids"] = sorted(set(target.get("check_ids") or [_check_id(target)]) |
                                     set(f.get("check_ids") or [_check_id(f)]))
        merged["categories"] = sorted({target.get("category"), f.get("category")} |
                                      set(target.get("categories") or ()) | set(f.get("categories") or ()))
        merged["affected_pages"] = sorted(set(target.get("affected_pages") or ()) | set(f.get("affected_pages") or ()))
        seen, evidence = set(), []
        for item in list(lead.get("evidence") or ()) + list(other.get("evidence") or ()):
            k = _evidence_key(item) if isinstance(item, dict) else (str(item),)
            if k not in seen:
                seen.add(k)
                evidence.append(item)
        merged["evidence"] = evidence
        from models import make_evidence_text
        merged["evidence_text"] = make_evidence_text(evidence)
        action = dict(lead.get("suggested_action") or {})
        steps = list(dict.fromkeys(list(action.get("steps") or ()) + list((other.get("suggested_action") or {}).get("steps") or ())))
        action["steps"] = steps[:8]
        merged["suggested_action"] = action
        merged["also_reported_as"] = sorted(set(target.get("also_reported_as") or ()) | set(f.get("also_reported_as") or ())
                                            | {other.get("title")})
        prov = []
        for x in (lead, other):
            pv = x.get("provenance") or {}
            prov.extend(pv.get("contributing_skills", [pv]) if isinstance(pv, dict) else [])
        merged["provenance"] = {"contributing_skills": prov}
        out[out.index(target)] = merged
    for f in out:
        f.pop("_group", None)
    return out


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
        else:
            match = find_matching_bucket(finding, buckets, similarity_threshold=0.85)
            key = match or dedup_key(finding)
        buckets.setdefault(key, []).append(finding)
    return _group_merge([merge_evidence(group) for group in buckets.values()])
