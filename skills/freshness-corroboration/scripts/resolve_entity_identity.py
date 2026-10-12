"""resolve_entity_identity.py -- runs once; centralized, disambiguated identity
resolution.

Ambiguity handling: not every mismatch between JSON-LD blocks means the same
thing, and treating them all as "ambiguous -> low confidence" both over-penalizes
harmless formatting variance and under-explains genuine multi-brand confusion:
  - "Acme Inc." vs "Acme, Inc" vs "ACME INC" -- same entity, legal-suffix/case
    noise. Should not lower confidence at all.
  - "Acme" (name) vs "Acme Widgets Corporation" (legalName) where one name is a
    substring of the other -- a parent/sub-brand relationship, not confusion
    about which brand this is. Confidence stays reasonably high but the relation
    is recorded, since it changes how external corroboration should be read.
  - "Acme" vs "Zenith Traders" -- genuinely different, unrelated names on the same
    site. This is the real multi-brand-conflict case and should suppress broad
    name-only external search via the confidence gate below.
  - Two sameAs URLs on the *same* platform (e.g. two different LinkedIn company
    pages) pointing at different profiles is direct conflicting-identity evidence,
    independent of the name comparison above.
"""
import re
from collections import defaultdict
from collections.abc import Mapping
from structured_data import iter_nodes, types_of, CORE_ORGANIZATION_TYPES, ORGANIZATION_TYPES
from urllib.parse import urlsplit
from models import intermediate_artifact
from identity_signals import candidates as identity_candidates, agreement

_LEGAL_SUFFIX_RE = re.compile(
    r"[,.]?\s*\b(inc|incorporated|llc|l\.l\.c|ltd|limited|corp|corporation|co|company|"
    r"plc|gmbh|s\.a|pvt|pty)\b\.?\s*$",
    re.IGNORECASE,
)

_PLATFORM_HOSTS = {
    "twitter.com": "twitter", "x.com": "twitter", "facebook.com": "facebook",
    "linkedin.com": "linkedin", "instagram.com": "instagram", "youtube.com": "youtube",
    "tiktok.com": "tiktok", "pinterest.com": "pinterest",
}


def _normalize_org_name(name: str) -> str:
    if not name:
        return ""
    stripped = _LEGAL_SUFFIX_RE.sub("", name.strip())
    return re.sub(r"[^\w]+", " ", stripped.lower()).strip()


def _platform_of(url: str) -> str:
    try:
        host = urlsplit(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""
    return _PLATFORM_HOSTS.get(host, host)


def _names_are_substrings(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return a in b or b in a


def resolve_entity_identity(artifacts, deadline):
    org_blocks = [
        # Mapping (not dict): real PageArtifacts store jsonld_blocks frozen as
        # MappingProxyType; dict-only fixtures still match too.
        block for page in artifacts.pages for block in iter_nodes(page.jsonld_blocks)
        if isinstance(block, Mapping) and types_of(block) & CORE_ORGANIZATION_TYPES
    ]
    if not org_blocks:
        # A site marked up only with an Organization subtype (Plumber, Restaurant,
        # CollegeOrUniversity ...) declares itself on the home page. Subtypes on
        # other pages may be listings, so they are not read as the site's identity.
        home_key = artifacts.site_url.rstrip('/')
        org_blocks = [block for page in artifacts.pages
                      if page.page_type == 'home' or (page.final_url or page.url).rstrip('/') == home_key
                      for block in iter_nodes(page.jsonld_blocks)
                      if isinstance(block, Mapping) and types_of(block) & ORGANIZATION_TYPES]

    from check_helpers import content_pages
    pages = content_pages(artifacts, require_features=False)
    fallback = identity_candidates(pages, artifacts.normalized_origin)
    if not org_blocks:
        # No Organization JSON-LD. Fall back through WebSite name / og:site_name,
        # the common title segment, the footer copyright holder and finally the
        # domain label. Confidence is the weight of the best level found, plus 0.05
        # per other source that agrees, but capped below 0.85 -- an inferred
        # identity never unlocks the identity-gated external searches that need a
        # declared one.
        if not fallback:
            return intermediate_artifact(
                "entity_identity", status="insufficient_evidence",
                data={"confidence": 0.0, "ambiguity_set": [], "entity_type": "unknown", "identity_sources": []},
                warnings=["No Organization JSON-LD and no first-party naming signal; identity unresolved."],
            )
        level, weight, name, source = fallback[0]
        agree = max(0, agreement(name, fallback) - 1)
        confidence = round(min(0.8, weight + 0.05 * agree), 3)
        others = sorted({n for lv, _, n, _ in fallback if lv <= 3 and _normalize_org_name(n) and not
                         _names_are_substrings(_normalize_org_name(n), _normalize_org_name(name))})
        data = {
            "canonical_name": name, "legal_name": name, "domain": artifacts.normalized_origin,
            "normalized_address": None, "phone_numbers": [], "same_as_urls": [], "social_handles": [],
            "aliases": [name], "entity_type": "organization",
            "identity_fingerprint": f"{_normalize_org_name(name) or name.lower()}::{artifacts.normalized_origin}",
            "confidence": confidence, "ambiguity_set": others,
            "ambiguity_type": "fallback_name_conflict" if others else None,
            "disambiguation_evidence": [f"Conflicting first-party names: {name!r} vs {', '.join(others)}"] if others else [],
            "identity_level": level,
            "identity_sources": [{"level": lv, "weight": w, "name": n, "source": src} for lv, w, n, src in fallback],
            "declared": False,
        }
        return intermediate_artifact("entity_identity", data=data, status="partial",
                                     warnings=["Identity inferred from first-party naming signals; no Organization JSON-LD."])

    primary = org_blocks[0]
    name = primary.get("name") or artifacts.normalized_origin

    raw_names = sorted({b.get("name") for b in org_blocks if b.get("name")})
    normalized_groups = defaultdict(list)
    for n in raw_names:
        normalized_groups[_normalize_org_name(n)].append(n)
    distinct_normalized = [g for g in normalized_groups.keys() if g]

    disambiguation_evidence = []
    ambiguity_set = []
    ambiguity_type = None

    if len(distinct_normalized) <= 1:
        # All names collapse to the same normalized form (legal-suffix/case/
        # punctuation noise only) -- not ambiguity.
        confidence = 0.92
    else:
        primary_norm = _normalize_org_name(name)
        other_norms = [g for g in distinct_normalized if g != primary_norm]
        substring_related = [g for g in other_norms if _names_are_substrings(primary_norm, g)]
        unrelated = [g for g in other_norms if g not in substring_related]

        if unrelated:
            ambiguity_type = "multi_brand_conflict"
            confidence = 0.55
            ambiguity_set = [normalized_groups[g][0] for g in unrelated]
            disambiguation_evidence.append(
                f"Unrelated organization names found on the same site: "
                f"{name!r} vs {', '.join(normalized_groups[g][0] for g in unrelated)}"
            )
        else:
            ambiguity_type = "parent_sub_brand"
            confidence = 0.8
            ambiguity_set = [normalized_groups[g][0] for g in substring_related]
            disambiguation_evidence.append(
                f"Related but distinct names found (likely parent/sub-brand): "
                f"{name!r} vs {', '.join(normalized_groups[g][0] for g in substring_related)}"
            )

    # Conflicting sameAs: two DIFFERENT profile URLs on the same platform is direct
    # evidence of identity conflict, independent of the name comparison above.
    same_as_all = []
    for b in org_blocks:
        sa = b.get("sameAs", [])
        if isinstance(sa, (list, tuple)):
            same_as_all.extend(sa)
        elif sa:
            same_as_all.append(sa)

    platform_urls = defaultdict(set)
    for url in same_as_all:
        if url:
            platform_urls[_platform_of(url)].add(url)
    conflicting_sameas = {p: sorted(u) for p, u in platform_urls.items() if len(u) > 1}
    if conflicting_sameas:
        if ambiguity_type is None:
            ambiguity_type = "conflicting_sameas"
        confidence = min(confidence, 0.6)
        for platform, urls in conflicting_sameas.items():
            disambiguation_evidence.append(
                f"Conflicting sameAs URLs on {platform}: {' vs '.join(urls)}"
            )

    same_as = sorted({u for urls in platform_urls.values() for u in urls}) or same_as_all

    data = {
        "canonical_name": name,
        "legal_name": primary.get("legalName", name),
        "domain": artifacts.normalized_origin,
        "normalized_address": primary.get("address"),
        "phone_numbers": [primary.get("telephone")] if primary.get("telephone") else [],
        "same_as_urls": same_as,
        "social_handles": [],
        "aliases": list(raw_names) or [name],
        "entity_type": str(primary.get("@type", "organization")).lower(),
        "identity_fingerprint": f"{_normalize_org_name(name) or name.lower()}::{artifacts.normalized_origin}",
        "confidence": confidence,
        "ambiguity_set": ambiguity_set,
        "ambiguity_type": ambiguity_type,
        "disambiguation_evidence": disambiguation_evidence,
        "identity_level": 1,
        "identity_sources": [{"level": 1, "weight": 0.92, "name": name, "source": "Organization JSON-LD"}]
                            + [{"level": lv, "weight": w, "name": n, "source": src} for lv, w, n, src in fallback],
        "declared": True,
    }
    status = "success" if confidence >= 0.85 else "partial"
    return intermediate_artifact("entity_identity", data=data, status=status)
