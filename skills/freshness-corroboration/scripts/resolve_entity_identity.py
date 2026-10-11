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
from structured_data import iter_nodes, types_of, ORGANIZATION_TYPES
from urllib.parse import urlsplit
from models import intermediate_artifact

_LEGAL_SUFFIX_RE = re.compile(
    r"[,.]?\s*\b(inc|incorporated|llc|l\.l\.c|ltd|limited|corp|corporation|co|company|"
    r"plc|gmbh|s\.a|pvt|pty)\b\.?\s*$",
    re.IGNORECASE,
)

ORG_TYPES = frozenset({"Organization", "Corporation", "LocalBusiness", "OnlineStore", "NGO",
                       "EducationalOrganization", "GovernmentOrganization"})

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


# Title separators between a page name and the site name ("Pricing | Acme").
# The en and em dash are built from code points so the source holds neither.
_TITLE_SEPARATOR = re.compile(r"\s+(?:\||-|::|·|•|" + chr(0x2013) + "|" + chr(0x2014) + r")\s+")
_COPYRIGHT = re.compile(r"(?:©|\(c\)|copyright)\s*(?:©\s*)?(?:(?:19|20)\d{2}\s*(?:[-–]\s*(?:19|20)\d{2})?\s*,?\s*)?"
                        r"([A-Z][\w&.,' -]{1,60}?)(?=\s*(?:\.|,?\s*all rights|\||$))", re.IGNORECASE)
# Confidence of a name read from site metadata, not from Organization markup:
# enough to name the brand in text, below the 0.85 the external lookups require.
_METADATA_CONFIDENCE = {1: 0.5, 2: 0.6}


def _title_suffix(pages):
    """The trailing title segment shared by at least three pages and half of the
    titled pages, such as "Acme" in "Pricing | Acme", or None."""
    tails = [_TITLE_SEPARATOR.split((getattr(p, "title", None) or "").strip())[-1].strip()
             for p in pages if _TITLE_SEPARATOR.search(getattr(p, "title", None) or "")]
    titled = sum(1 for p in pages if getattr(p, "title", None))
    if not tails:
        return None
    best, count = max(((t, tails.count(t)) for t in set(tails) if 2 <= len(t) <= 60), key=lambda x: (x[1], x[0]),
                      default=(None, 0))
    return best if count >= 3 and count * 2 >= titled else None


def _name_from_site_metadata(artifacts):
    """Brand name from what the site says about itself when it has no Organization
    markup: WebSite JSON-LD name, og:site_name, a site name repeated as the title
    suffix, and the copyright line in the footer. Returns an entity_identity
    artifact at reduced confidence (0.6 when two sources agree, 0.5 for one), or
    None when no source names the site."""
    pages = [p for p in artifacts.pages if getattr(p, "status_code", 200) == 200]
    sources = defaultdict(set)
    shown = {}

    def add(source, value):
        if isinstance(value, str) and 2 <= len(value.strip()) <= 80:
            key = _normalize_org_name(value)
            if key:
                sources[key].add(source)
                shown.setdefault(key, value.strip())

    for p in sorted(pages, key=lambda p: p.page_type != "home"):
        for node in iter_nodes(p.jsonld_blocks):
            if isinstance(node, Mapping) and "WebSite" in types_of(node):
                add("website_markup", node.get("name"))
        meta = (getattr(p, "features", None) or {}).get("meta") or {}
        for value in list(meta.get("og:site_name") or ())[:1]:
            add("og_site_name", value)
    add("title_suffix", _title_suffix(pages))
    footers = {}
    for p in pages:
        m = _COPYRIGHT.search((getattr(p, "visible_text", None) or "")[-3000:])
        if m:
            key = _normalize_org_name(m.group(1))
            footers[key] = footers.get(key, 0) + 1
            shown.setdefault(key, m.group(1).strip())
    for key, count in footers.items():
        if key and count >= 2:
            sources[key].add("copyright_line")
    if not sources:
        return None
    key = max(sources, key=lambda k: (len(sources[k]), k))
    agreeing = len(sources[key])
    name = shown[key]
    confidence = _METADATA_CONFIDENCE[min(agreeing, 2)]
    others = sorted(shown[k] for k in sources if k != key)
    data = {
        "canonical_name": name, "legal_name": name, "domain": artifacts.normalized_origin,
        "normalized_address": None, "phone_numbers": [], "same_as_urls": [], "social_handles": [],
        "aliases": [name], "entity_type": "website",
        "identity_fingerprint": f"{key}::{artifacts.normalized_origin}",
        "confidence": confidence, "ambiguity_set": others, "ambiguity_type": "name_from_site_metadata",
        "identity_sources": sorted(sources[key]),
        "disambiguation_evidence": [f"No Organization markup; the site names itself {name!r} in "
                                    + ", ".join(sorted(sources[key]))],
    }
    return intermediate_artifact("entity_identity", data=data, status="partial",
                                 warnings=["No Organization JSON-LD found; the brand name was read from site "
                                           "metadata at reduced confidence."])


def resolve_entity_identity(artifacts, deadline):
    org_blocks = [
        # Mapping (not dict): real PageArtifacts store jsonld_blocks frozen as
        # MappingProxyType; dict-only fixtures still match too.
        block for page in artifacts.pages for block in iter_nodes(page.jsonld_blocks)
        if isinstance(block, Mapping) and types_of(block) & ORG_TYPES
    ]
    if not org_blocks:
        # A site that marks itself up only with a subtype (Plumber, Restaurant,
        # CollegeOrUniversity) still names its organization. Only the home page
        # is read for this fallback: elsewhere such nodes are often listings of
        # other businesses, which would look like a multi-brand conflict.
        org_blocks = [
            block for page in artifacts.pages if page.page_type == "home"
            for block in iter_nodes(page.jsonld_blocks)
            if isinstance(block, Mapping) and types_of(block) & ORGANIZATION_TYPES
        ]

    if not org_blocks:
        fallback = _name_from_site_metadata(artifacts)
        if fallback:
            return fallback
        return intermediate_artifact(
            "entity_identity", status="insufficient_evidence",
            data={"confidence": 0.0, "ambiguity_set": [], "entity_type": "unknown"},
            warnings=["No Organization/Product JSON-LD found; identity unresolved."],
        )

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
    }
    status = "success" if confidence >= 0.85 else "partial"
    return intermediate_artifact("entity_identity", data=data, status=status)
