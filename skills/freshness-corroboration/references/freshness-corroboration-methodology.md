# Freshness & corroboration methodology

Entity resolution hierarchy (implemented in `resolve_entity_identity.py` +
`common/identity_signals.py`):
1. Organization/LocalBusiness/Corporation JSON-LD name (0.92); when no such node
   exists, an Organization subtype (Plumber, Restaurant, CollegeOrUniversity ...)
   on the home page only -- elsewhere a subtype may be a listing
2. WebSite JSON-LD name or og:site_name consistent on >= 2 pages (0.75)
3. Common title segment on >= 60% of pages (0.70)
4. Footer copyright holder (0.65)
5. Domain label (0.40)
Confidence = best level's weight + 0.05 per agreeing source; inferred identities
(levels 2-5) are capped at 0.80 and flagged `declared: false`.

Confidence gates: >= 0.85 (ambiguity empty) allows identity-aware external
search; below that external search is suppressed and returns insufficient_evidence.

Freshness rules (`assess_freshness.py`): an old date is never a finding by
itself. Dates are classified by the words around them (update claim, expiry,
historical, copyright, editorial, unclassified) and by machine fields
(datePublished, dateModified, priceValidUntil, validThrough, endDate,
article:modified_time, sitemap lastmod). Rules: expired-offer, date-contradiction,
stale-update-claim (>24 months, volatile pages only), stale-copyright (>= 2 years),
missing-article-dates. A build-stamped sitemap (>= 80% of lastmod values on one
day) is left out of the date comparisons and reported once instead.

Sitemap update dates (`update_signals.py`): `sitemap-lastmod-unreliable` (low)
when a sitemap of five or more entries carries no lastmod at all, or one date on
at least 80% of them.

Entity links (`check_entity_links.py`, no requests): `same-as-invalid` (low) for
sameAs values that cannot be a profile (not an absolute URL, the site itself, a
share link, a platform home page); `kg-link-missing` (low, proactive) only when
the brand already declares sameAs profiles but none is a Wikidata item or
Wikipedia article. Namesake checks need third-party search and run in the agent
stage (AG-05).

Footprint calibration: search non-detection is never proof of real-world absence.
Footprint findings are always category=off_site_presence,
finding_type=proactive_improvement -- never critical or high solely because few
sources were found.
