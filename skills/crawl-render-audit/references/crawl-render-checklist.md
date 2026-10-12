# Crawl & render checklist

Gate 1 -- access (can a crawler get in and receive the content?)
- robots.txt per RFC 9309: `ok` obeyed; `absent`/`unavailable_4xx` = no
  restrictions; `inaccessible` (5xx/timeout) = disallow-all; `challenged` and
  `rate_limited` (HTTP 429) = permission unknown (homepage-only probe);
  `malformed`/`blocked` = unknown.
  Only `ok`/`absent`/`unavailable_4xx` produce allow/disallow verdicts.
- Bot walls (`analyze_access.py`): `bot-challenge-robots` (high, confirmed),
  `bot-challenge-sitewide` (high, suspected -- verified-bot allowlists cannot be
  proven from outside), `bot-challenge-rate` (medium, confirmed),
  `robots-rate-limited` (medium, suspected: one 429 may be transient).
- Crawler access by role (`check_ai_crawler_access.py`): Googlebot/Bingbot
  critical; AI search and user-triggered fetchers high; training-only low and
  proactive. Evaluated on the homepage, key-intent URLs, sitemap and llms.txt.
- Indexing directives: noindex (homepage critical), nosnippet, max-snippet:0.
- Broken pages (4xx/5xx, excluding challenge pages); HTTP vs HTTPS.

Gate 2 -- readability (is the content present as text?)
- Render gap: empty SPA mount / noscript JS requirement + hydration strings
  missing from server HTML (suspected); browser-confirmed when rendering is on.
  Thin text alone is insufficient evidence, never a defect, and a page that runs
  no script is never a rendering gap.
- Facts in PDFs (fact-keyword document + no facts in page text), images
  (fact-named images on thin pages, or a large image on a price-type page whose
  text states no price), viewer iframes. The agent stage (AG-04) reads the listed
  images with its own vision and confirms or drops the suspicion.

Gate 3 -- extractability (can a machine pick out the fact and the entity?)
- JSON-LD presence per page type; site-wide absence lists page types and
  attaches draft snippets.
- Required properties, malformed values, markup contradicting the visible page.
- Citation markup (`analyze_citation_schema.py`): `citation-schema-invalid`
  (medium) for FAQPage/HowTo/Review/AggregateRating missing required parts or
  contradicting the page; `citation-schema-opportunity` (low) for at least three
  answered question headings, a "How to" page with numbered steps, or visible
  rating text with no matching markup. Linked teaser headings never count.
- Contact markup (`analyze_contact_markup.py`): the site's own email (same
  domain, not no-reply) or a phone on the home/contact page or on two pages,
  stated in no JSON-LD. Runs only when the site already publishes JSON-LD.
- llms.txt presence (proactive only). Metadata and HTML-weight items are hygiene.
- Login pages (password field, <= 1,500 characters, no entity markup, a login
  path or heading) are out of scope for every check above.
