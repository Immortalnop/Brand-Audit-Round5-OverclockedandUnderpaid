# Freshness & corroboration methodology

Entity resolution hierarchy: Organization/Product JSON-LD -> legal/registered
name on first-party pages -> canonical domain -> address/phone -> sameAs and
official social profiles -> consistent first-party naming.

Confidence gates: >=0.85 (ambiguity empty) allows broad identity-aware
external analysis; 0.65-0.849 restricts to domain-led sources and marks
partial; <0.65 or unresolved ambiguity suppresses external search and returns
insufficient_evidence.

Footprint calibration: search non-detection is never proof of real-world
absence. Footprint findings are always category=off_site_presence,
finding_type=proactive_improvement -- never critical or high solely because
few sources were found.

Date sources for freshness: dates mentioned in visible text (every extracted
text date, not only the top-ranked facts) and explicit JSON-LD datePublished /
dateModified. Each JSON-LD node contributes its most recent valid date, so an
old datePublished with a recent dateModified reads as updated. A page whose
JSON-LD declares an update within the last three years is not reported for old
editorial dates in its text. Structured dates are categorized commercial for
Product, Offer, Service and software nodes, legal on legal pages, and editorial
otherwise. Invalid structured dates (not ISO 8601, in the future, or
dateModified before datePublished) are reported as `structured-date-invalid`
(low, confirmed).

Page update dates (update_signals.py, no extra requests): the sitemap
`<lastmod>` of each crawled URL and the HTTP `Last-Modified` header of each
crawled page. Each page contributes its most recent trusted update date,
categorized by page type (product, service and software pages commercial,
contact pages contact, legal pages legal, articles and About pages editorial,
everything else operational, never historical). A page update date is used only
when it is newer than every JSON-LD date on that page, and a recent update from
any source supersedes old editorial dates in the page text. Values that are not
trusted are ignored and counted: unparseable or future values, a Last-Modified
within two minutes of the response Date header (generated per request by a
dynamic page; fifteen minutes of the audit time when Date is missing), and a
sitemap where at least 80% of five or more valid lastmod values share one date
(stamped at build time). A lastmod written as `2023-07-25 15:19:07` (a space
instead of `T`) is reported as nonstandard but its date is still used. A
sitemap that was read but has no lastmod, invalid or nonstandard lastmod
values, or build-stamped values is reported as
`sitemap-lastmod-unreliable` (low; confirmed for missing or invalid values,
suspected for build-stamped ones).

Knowledge-graph link (check_knowledge_graph.py): assistants tell same-named
entities apart through a two-way link, Organization `sameAs` naming the
Wikidata item or Wikipedia article and the item's official website (P856)
naming the site.
- No Wikidata or Wikipedia link in Organization markup: `kg-link-missing`
  (low; medium when identity resolution already found on-site ambiguity). No
  network.
- A declared link is verified by at most one Wikidata item and one Wikipedia
  article, fetched by GET from the public `/wiki/` paths after reading each
  host's robots.txt (fail closed), with a 15-second budget. A deleted item, a
  missing article, an item whose official website is another domain, or a
  Wikipedia article whose item differs from the declared Wikidata item is
  `kg-entity-mismatch` (medium, confirmed); an item with neither a matching
  name nor an official website is the same check, suspected. An item that
  matches by name but lists no official website is `kg-link-missing` (one-way
  link).
- A failed or disabled lookup (`KNOWLEDGE_GRAPH_LOOKUP=0`) is a warning and a
  report limitation, never a finding.
- The scripts never search for namesakes: robots.txt for wikidata.org and
  wikipedia.org disallows their search and API endpoints. The agent stage does
  that with its own web search (AG-05, `kg-namesake-ambiguity`).
