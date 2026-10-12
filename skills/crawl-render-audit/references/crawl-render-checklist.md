# Crawl & render checklist

Gate 1 -- access (can a crawler get in and receive the content?)
- robots.txt per RFC 9309: `ok` obeyed; `absent`/`unavailable_4xx` = no
  restrictions; `inaccessible` (429/5xx/timeout) = disallow-all; `challenged` =
  permission unknown (homepage-only probe); `malformed`/`blocked` = unknown.
  Only `ok`/`absent`/`unavailable_4xx` produce allow/disallow verdicts.
- Bot walls (`analyze_access.py`): `bot-challenge-robots` (high, confirmed),
  `bot-challenge-sitewide` (high, suspected -- verified-bot allowlists cannot be
  proven from outside), `bot-challenge-rate` (medium, confirmed).
- Crawler access by role (`check_ai_crawler_access.py`): Googlebot/Bingbot
  critical; AI search and user-triggered fetchers high; training-only low and
  proactive. Evaluated on the homepage, key-intent URLs, sitemap and llms.txt.
- Indexing directives: noindex (homepage critical), nosnippet, max-snippet:0.
- Broken pages (4xx/5xx, excluding challenge pages); HTTP vs HTTPS.

Gate 2 -- readability (is the content present as text?)
- Render gap: empty SPA mount / noscript JS requirement + hydration strings
  missing from server HTML (suspected); browser-confirmed when rendering is on.
  Thin text alone is insufficient evidence, never a defect.
- Facts in PDFs (fact-keyword document + no facts in page text), images
  (fact-named images on thin pages), viewer iframes.

Gate 3 -- extractability (can a machine pick out the fact and the entity?)
- JSON-LD presence per page type; site-wide absence lists page types and
  attaches draft snippets.
- Required properties, malformed values, markup contradicting the visible page.
- llms.txt presence (proactive only). Metadata and HTML-weight items are hygiene.
