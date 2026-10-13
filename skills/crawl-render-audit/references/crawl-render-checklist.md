# Crawl & render checklist

- robots.txt: general and AI-crawler-specific directives for the labelled
  crawlers in common/ai_crawlers.py (search, user-requested fetch, training). Fetch status is one
  of `ok` / `absent` (404, allow-all) / `timeout` / `inaccessible` / `malformed`
  / `blocked` (failed the SSRF check). Only `ok` and `absent` produce a
  confirmed allow/disallow verdict; every other status is `insufficient_evidence`,
  never inferred as either an allow or a disallow.
- sitemap.xml: actually fetched and parsed (present/absent/inaccessible/malformed
  are distinguished; URLs are capped and available in `sitemap_data`).
- llms.txt: actually fetched (present/absent/inaccessible/blocked are
  distinguished; absence is observation only).
  - `llms-txt-invalid` (medium): no H1 title, more than one H1, or an explicitly
    linked `/llms-full.txt` answering with an HTML page. Lists and sections are optional.
  - `llms-txt-broken-links` (medium, confirmed): listed same-origin pages that
    answer 404 or 410. Crawled pages reuse their crawl result; at most 8 others
    get a robots-checked GET. Links on other domains, robots-disallowed links and
    links past the cap are counted in `coverage.llms_txt`, never reported as
    broken.
  - `/llms-full.txt` is probed once (first 64 KiB); its status is in
    `coverage.llms_txt.llms_full_txt_status`.
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
- Text alternatives for media (`analyze_media_text.py`, no requests):
  - `alt-text-quality` (low, medium when at least 5 images and 30% of described
    images are affected): alt text that is a file name, a camera or screenshot
    file name, a copy of the file name, a placeholder word (image, banner, logo,
    photo), a number or code, a single character, or the same alt text on four
    or more different images. Empty alt is correct for decorative images;
    `role="presentation"` images and 1x1 tracking pixels are skipped.
  - `media-transcript-missing` (low): native video or audio, or a recognized
    video or podcast embed, on a page whose text and links offer no transcript,
    unless every player has captions (a captions or subtitles track, or
    `cc_load_policy=1` on a YouTube embed). Captions inside embedded players are
    reported as not checked. A muted autoplay video with no controls is a moving
    background and is judged by neither media check.
  - `media-schema-missing` (low): video without VideoObject (JSON-LD or
    microdata), VideoObject without name, thumbnailUrl or uploadDate, or spoken
    audio without AudioObject or PodcastEpisode.
- Citation-oriented markup (`analyze_citation_schema.py`, no requests):
  - `citation-schema-invalid` (medium, defect): FAQPage without Questions, a
    Question without an accepted answer, FAQ questions mostly not shown on the
    page, HowTo without steps or with empty steps, Review without a numeric
    rating or an author, ratings outside their bestRating/worstRating scale,
    AggregateRating without a count or with zero ratings, and a top-level
    Review or AggregateRating attached to no item.
  - `citation-schema-opportunity` (low, suspected): optional structured-content export for a "How to" page with numbered steps without
    HowTo, or rating text on a product, service or software page without
    AggregateRating.
- Core Web Vitals (`analyze_web_vitals.py`):
  - `cwv-field-poor` (defect, confirmed; medium when any metric is poor):
    Chrome UX Report 75th percentiles from the PageSpeed Insights API, only
    with `PAGESPEED_API_KEY`. Good is LCP 2.5 s, CLS 0.1 and INP 200 ms or less;
    poor is above 4 s, 0.25 and 500 ms.
  - `cwv-risk` (low, suspected, labelled as an estimate): one strong or two
    moderate markup patterns per metric on a page. An estimate is dropped when
    field data rates that metric good.

- hreflang (`analyze_international.py`, no requests):
  - `hreflang-invalid` (medium when codes are malformed, duplicated, broken or
    not reciprocated; otherwise low): see SKILL.md for the full list.
  - `hreflang-missing` (low, suspected): two or more html languages, no
    hreflang in HTML, Link headers or the sitemap.
- noscript: text inside `<noscript>` does not count toward the render-gap
  threshold unless it is a real fallback at least as long as the threshold.
- Text drawn in graphics (`analyze_graphics_text.py`): `canvas-text`,
  `svg-inline-facts`, `icon-font-text` (all low).
- Image context (`analyze_image_context.py`): `image-context-missing` (low,
  suspected).
- Image weight (`analyze_image_weight.py`): `image-weight` (measured, confirmed),
  `responsive-images` (markup, suspected). Cross-origin images are never
  requested.
- Answer formats (`analyze_answer_format.py`, no requests): the passages
  assistants quote.
  - `question-answer-indirect` (low, suspected, English pages only): a
    question-shaped H2 or H3 followed by no text, a first sentence over 40
    words, or a filler opener such as "Great question". Call-to-action
    headings ("Need more information?"), questions answered by their own
    subheadings and teasers (a heading whose text a link to another page
    repeats as its text or aria-label, as on a news front) are skipped.
  - `table-headers-missing` (low, confirmed): a data table of two or more rows
    and columns, not `role="presentation"`, with no `<th>` cells.
  - `comparison-table-missing` (low, suspected): a title or main heading with
    "vs", "versus", "comparison" or "alternatives" and no data table or
    definition list.
  - `spec-list-missing` (low, suspected): a product or software page with 150
    or more words and no table, definition list or list of three items.
  - Pages built by JavaScript (raw-HTML text below the render-gap threshold for
    their page type, with no substantial `<noscript>` fallback) are not judged
    by `comparison-table-missing` or `spec-list-missing`; the report warns how
    many were skipped. Question headings and tables are judged on every page,
    because a heading or table in the raw HTML is itself content.
- Location and audience signals (`analyze_context_signals.py`, no requests;
  handout appendix E, personalization):
  - `location-markup-missing`: an address, a map embed or a directions link,
    and no address, geo, areaServed or Place in any page's structured data.
    An address is an `<address>` with a number, or a postal address written
    as plain text within one block: after a label ("Address:", "Visit us at"),
    as a street line ("12 High Street, Springfield"), or as three or more
    comma-separated parts ending in a postal code. Email, IP and web addresses
    and lists of names followed by a number do not count. Missing optional
    location markup remains low advice; additional evidence confirms applicability,
    not a universal markup requirement.
  - `contact-markup-missing` (low, suspected): an email or phone number is
    shown (mailto: or tel: links, an email written as text, a phone number
    after a label such as "Phone:" or "Call us on") and no page states an
    email, telephone or contactPoint in JSON-LD, microdata or RDFa. Retina
    file names such as logo@2x.png are not emails. The fix snippet fills the
    Organization email (preferring a generic mailbox on the site's own domain
    seen on the home or contact page) and telephone (the number shown on the
    most pages).
  - Text scans for addresses and contact details read the whole visible text
    of a page up to 500,000 characters; a longer page is read from its first
    and last 250,000 characters.
  - `local-business-incomplete`: LocalBusiness markup without an address
    (medium, confirmed) or without geo and areaServed (low, suspected).
  - `audience-segment-missing` (low, suspected): a commercial site (product,
    service, software or pricing pages) where no title, heading or internal
    link names an audience ("for students", /industries/, /use-cases/). Pages
    built by JavaScript are not counted toward the three pages it needs, and
    the report warns how many were skipped.

Missing FAQPage/llms.txt is no universal requirement. See [Search policy](search-policy.md).
