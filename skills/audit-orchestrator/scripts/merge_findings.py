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
        finding.get("status"),
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
        cascade_key = ("ai_discoverability", "robots-inaccessible-cascade", ("site-wide",), finding.get("status"))
        return cascade_key if cascade_key in buckets else None
    key = dedup_key(finding)
    if key in buckets:
        return key
    cat = finding["category"]
    scope = tuple(sorted(finding.get("affected_pages") or [])) or ("site-wide",)
    norm_cause = normalize_text(finding["root_cause"])
    for existing_key in buckets:
        e_cat, e_cause, e_scope, e_status = existing_key
        if e_status == finding.get("status") and e_cat == cat and e_scope == scope and similarity(norm_cause, e_cause) >= similarity_threshold:
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
    return ("family", family, ("site-wide",), finding.get("status")) if family else None


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


def _check_ids_of(finding: dict) -> set:
    """Every check ID one finding stands for: its own and any merged into it."""
    ids = {c for c in finding.get("check_ids") or () if isinstance(c, str)}
    cid = finding.get("check_id") or (finding.get("provenance") or {}).get("rule_id")
    if cid:
        ids.add(cid)
    return ids


def _contributors(finding: dict) -> list:
    """The provenance entries behind one finding, flattened one level."""
    prov = finding.get("provenance")
    if isinstance(prov, dict) and isinstance(prov.get("contributing_skills"), list):
        return list(prov["contributing_skills"])
    return [prov]


def fold_finding(base: dict, addition: dict) -> dict:
    """base with addition folded in. The base keeps its title, action and any
    fix snippet; evidence and pages are joined without duplicates and the check
    IDs and provenance of both are kept. As in merge_evidence, the more
    confident of the two sets status, confidence and finding type; severity is
    the higher of the two, so a fold never lowers what the reader sees."""
    if base.get("status") != addition.get("status"):
        raise ValueError("Cannot fold confirmed and suspected assessment groups")
    from models import apply_invariant_i1, make_evidence_text
    merged = dict(base)
    evidence = [e for e in base.get("evidence") or () if isinstance(e, dict)]
    seen = {_evidence_key(e) for e in evidence}
    for item in addition.get("evidence") or ():
        if isinstance(item, dict) and _evidence_key(item) not in seen:
            seen.add(_evidence_key(item))
            evidence.append(item)
    merged["evidence"] = evidence
    merged["evidence_text"] = make_evidence_text(evidence)
    merged["affected_pages"] = sorted(set(base.get("affected_pages") or ()) | set(addition.get("affected_pages") or ()))
    merged["check_ids"] = sorted(_check_ids_of(base) | _check_ids_of(addition))
    merged["provenance"] = {"contributing_skills": _contributors(base) + _contributors(addition)}
    if addition.get("confidence", 0) > base.get("confidence", 0):
        for field in ("status", "confidence", "finding_type"):
            merged[field] = addition.get(field, base.get(field))
    if _SEVERITY_RANK.get(addition.get("severity"), 0) > _SEVERITY_RANK.get(base.get("severity"), 0):
        merged["severity"] = addition["severity"]
    if merged.get("status") != base.get("status") or merged.get("severity") != base.get("severity"):
        # Notes about the old status or severity no longer describe the finding;
        # prioritize_findings records them again if they still apply.
        merged.pop("status_note", None)
        merged.pop("severity_gate", None)
    action = dict(base.get("suggested_action") or {})
    if _SEVERITY_RANK.get(merged.get("severity"), 0) > _SEVERITY_RANK.get(action.get("priority"), 0):
        action["priority"] = merged["severity"]
    merged["suggested_action"] = action
    return apply_invariant_i1(merged)


def fold_into(findings: list, additions: list, strict_pages: bool = False) -> tuple:
    """(findings, folded): findings with each addition folded into the finding
    that already reports it, or appended. An addition folds into, in order:
    an original finding of the same category that carries its check ID, the one
    sharing the most pages when there are several (an agent's vision reading of
    an image joins the script's facts-in-images finding); else a finding of the
    same check family;
    else one with the same or a near-identical root cause on the same pages, as
    merge_findings decides. folded counts the additions that joined a finding.
    With strict_pages, an addition that names pages joins only a finding of its
    check that shares one of them, and is otherwise appended: an agent's image
    reading of one page never joins a script finding about other pages.
    Neither input is changed."""
    out = [dict(f) for f in findings]
    originals = len(out)
    keys = {}
    for index, finding in enumerate(out):
        keys.setdefault(_family_key(finding) or dedup_key(finding), index)
    folded = 0
    for addition in additions:
        ids = _check_ids_of(addition)
        pages = set(addition.get("affected_pages") or ())
        same_check = [i for i in range(originals)
                      if out[i].get("category") == addition.get("category") and out[i].get("status") == addition.get("status") and ids & _check_ids_of(out[i])]
        strict = strict_pages and bool(pages)
        if strict:
            same_check = [i for i in same_check if pages & set(out[i].get("affected_pages") or ())]
        # Of several findings for the check, the one sharing the most pages; the first on a tie.
        target = max(same_check, key=lambda i: (len(pages & set(out[i].get("affected_pages") or ())), -i),
                     default=None)
        if target is None and not strict:
            key = _family_key(addition) or find_matching_bucket(addition, keys)
            target = keys.get(key) if key is not None else None
        if target is None:
            # Same shape as a merge_findings result: every finding lists its check IDs.
            out.append(dict(addition, check_ids=sorted(_check_ids_of(addition))))
            keys.setdefault(_family_key(addition) or dedup_key(addition), len(out) - 1)
        else:
            out[target] = fold_finding(out[target], addition)
            folded += 1
    return out, folded


def merge_findings(results: list) -> list:
    """Input MUST be list[SkillResult]; intermediate artifacts are rejected outright."""
    for r in results:
        if "skill" not in r or "findings" not in r:
            raise ValueError("merge_findings accepts SkillResult objects only")

    buckets: dict = {}
    all_findings = [f for r in results for f in r["findings"]]
    for finding in all_findings:
        if _is_robots_inaccessible_finding(finding):
            key = ("ai_discoverability", "robots-inaccessible-cascade", ("site-wide",), finding.get("status"))
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
