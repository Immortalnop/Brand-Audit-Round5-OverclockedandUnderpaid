# Crawl & render checklist

- robots.txt: general and AI-crawler-specific directives. Fetch status is one
  of `ok` / `absent` (404, allow-all) / `timeout` / `inaccessible` / `malformed`
  / `blocked` (failed the SSRF check). Only `ok` and `absent` produce a
  confirmed allow/disallow verdict; every other status is `insufficient_evidence`,
  never inferred as either an allow or a disallow.
- sitemap.xml: actually fetched and parsed (present/absent/inaccessible/malformed
  are distinguished; URLs are capped and available in `sitemap_data`).
- llms.txt: actually fetched (present/absent/inaccessible/blocked are
  distinguished; absence is `proactive_improvement` only, never a defect).
- HTTP status / broken pages
- Raw-vs-rendered content gaps (rendering-dependent checks report
  insufficient_evidence when no rendering was performed, never a defect)
- JSON-LD presence and coverage
- Semantic headings
- Facts locked in non-text media (`analyze_non_text.py`; all fetches happen in
  acquisition, after the page crawl, same origin only, robots-checked, capped at
  6 images and 3 PDFs per audit):
  - `facts-in-images`, confirmed: a same-origin SVG draws prices, phone numbers
    or specifications that the embedding page states nowhere in its text, alt
    text, meta description or JSON-LD.
  - `facts-in-images`, suspected: an image named or labelled as a price list,
    menu, opening hours or spec sheet (logos, icons and backgrounds excluded) on
    a page whose text carries no matching facts. Raster pixels are never read by
    a script; the agent vision stage (AG-04) can confirm.
  - `pdf-only-facts`: a linked PDF states at least two prices, specifications or
    phone numbers that no crawled HTML page states. Confirmed only when the crawl
    covered every discovered page; otherwise suspected and stepped down.
  - `pdf-image-only`: a linked PDF has pages that draw images and no text.
  - A PDF that is encrypted, uses an unsupported encoding or could not be
    fetched is recorded as a warning and a limitation, never a finding.
