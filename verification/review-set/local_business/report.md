# Brand AI-Readiness Audit: https://www.tatteredcover.com/

- **Audited at:** 2026-10-13T03:29:27.759132+00:00
- **Run:** Completed
- **Pages:** 5 analyzed of 307 discovered; 2 of 6 site sections reached
- **Run time:** 10.3 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 17 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.17)

Confidence is low (0.17). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 5 of 307 discovered page(s) and reached 2 of 6 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): The brand identity is clear: the Organization markup names one brand. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.17 | The page sample is small or one-sided: the crawl analyzed 5 of 307 discovered page(s) and reached 2 of 6 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.92 | The brand identity is clear: the Organization markup names one brand. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 9 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 8 |
| Improvement suggestions (not defects) | 8 |
| Not enough evidence to judge | 0 |
| Recommendations | 8 |

## Start here

**F-001: Links or buttons have no accessible name**

Name every icon-only link and button

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Links or buttons have no accessible name | Name every icon-only link and button | medium | medium | low | yes | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Links or buttons have no accessible name.** Name every icon-only link and button (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Links or buttons have no accessible name | 5 |
| F-002 | Improvement opportunity | low | confirmed | Organization markup does not link the brand to a knowledge-graph entity | 1 |
| F-003 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:image on 1/5 sampled pages | 1 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | Visible text is under 3% of the HTML on 4/5 sampled pages | 4 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 1/5 sampled pages | 1 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | No question-shaped headings on 4/4 content pages | 4 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Sitemap lastmod dates are missing or unreliable | 0 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 5 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Physical location is shown on the page but stated in no structured data | 5 |

## Finding details

### F-001: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://www.tatteredcover.com/>
- <https://www.tatteredcover.com/products/0025096985925>
- <https://www.tatteredcover.com/products/9780735329546>
- <https://www.tatteredcover.com/products/9780735367982>
- <https://www.tatteredcover.com/products/9781039498365>

**Evidence:**

- 1 unnamed control(s): &lt;a href=/pages/tattered-cover-book-clubs&gt; with only an icon
  - <https://www.tatteredcover.com/>
- 6 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/products/0025096985925&gt; with no content
  - <https://www.tatteredcover.com/products/0025096985925>
- 6 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/products/9780735329546&gt; with no content
  - <https://www.tatteredcover.com/products/9780735329546>
- 6 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/products/9780735367982&gt; with no content
  - <https://www.tatteredcover.com/products/9780735367982>
- 6 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/products/9781039498365&gt; with no content
  - <https://www.tatteredcover.com/products/9781039498365>

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: Organization markup does not link the brand to a knowledge-graph entity

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `kg-link-missing`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No Wikidata or Wikipedia link is declared, so nothing ties the brand to one knowledge-graph entity

**Pages:**

- <https://www.tatteredcover.com/>

**Evidence:**

- Organization markup on 1 page(s) declares sameAs: https://www.facebook.com/tattered.cover, https://www.instagram.com/tatteredcoverbookstore/, https://www.linkedin.com/company/tatteredcoverbookstore, https://www.tiktok.com/@tattered.cover, https://twitter.com/TatteredCover; none names a Wikidata item or Wikipedia article
  - <https://www.tatteredcover.com/>

**What to do:** Link the brand to its Wikidata item in Organization sameAs

**Suggested roles:** developer, seo

1. Find the brand's Wikidata item, or create one if the organization meets Wikidata's notability policy (public, serious references)
2. Add the item URL (and the Wikipedia article, if one exists) to Organization sameAs
3. Make sure the item lists this site as its official website (P856)

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Assistants can tell the brand apart from same-named entities

**How to check the fix:** Re-run the audit after the markup or the knowledge-graph entry changes

### F-003: Open Graph tags missing: og:image on 1/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.tatteredcover.com/>

**Evidence:**

- Missing nonempty fields: og:image
  - <https://www.tatteredcover.com/>

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

**Suggested roles:** developer, seo

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.tatteredcover.com/ -->
<meta property="og:image" content="https://www.tatteredcover.com/cdn/shop/files/Fall_for_All_Reading_Program_Website_Banner_2000_x_525_px.png?v=1791579667&amp;width=2000">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-004: Visible text is under 3% of the HTML on 4/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `markup-ratio`; Seen on 4 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A small visible-text share in a large HTML document can indicate excess markup.

**Pages:**

- <https://www.tatteredcover.com/>
- <https://www.tatteredcover.com/products/0025096985925>
- <https://www.tatteredcover.com/products/9780735329546>
- <https://www.tatteredcover.com/products/9780735367982>

**Evidence:**

- Visible text represents 2.1% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.tatteredcover.com/>
- Visible text represents 2.5% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.tatteredcover.com/products/0025096985925>
- Visible text represents 2.9% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.tatteredcover.com/products/9780735329546>
- Visible text represents 2.7% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.tatteredcover.com/products/9780735367982>

**What to do:** Inspect inline assets and template boilerplate before trimming unnecessary HTML.

**Suggested roles:** developer, seo

1. Inspect inline assets and template boilerplate before trimming unnecessary HTML.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Reduces document overhead if the sampled ratio reflects avoidable markup.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-005: Title shorter than 15 or longer than 70 characters on 1/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://www.tatteredcover.com/>

**Evidence:**

- Title has 14 characters: Tattered Cover. Display width was not measured.
  - <https://www.tatteredcover.com/>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-006: No question-shaped headings on 4/4 content pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `answer-headings`; Seen on 4 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Question-shaped sections may help readers locate direct answers where that format fits the content.

**Pages:**

- <https://www.tatteredcover.com/products/0025096985925>
- <https://www.tatteredcover.com/products/9780735329546>
- <https://www.tatteredcover.com/products/9780735367982>
- <https://www.tatteredcover.com/products/9781039498365>

**Evidence:**

- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.tatteredcover.com/products/0025096985925>
- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.tatteredcover.com/products/9780735329546>
- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.tatteredcover.com/products/9780735367982>
- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.tatteredcover.com/products/9781039498365>

**What to do:** Review audience questions and add useful question headings with concise answers; do not add empty FAQs or inappropriate schema.

**Suggested roles:** content, developer, seo

1. Review audience questions and add useful question headings with concise answers; do not add empty FAQs or inappropriate schema.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** May improve answer readability; questions are not required for retrieval or citation.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-007: Sitemap lastmod dates are missing or unreliable

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-lastmod-unreliable`; Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 0 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Sitemap lastmod dates are missing, malformed or not set per page, so crawlers cannot rely on them to recrawl changed pages first

**Evidence:**

- 200 of 200 valid lastmod values are the same date (2026-10-12), so they reflect when the sitemap was generated, not when each page changed

**What to do:** Publish an accurate &lt;lastmod&gt; for every sitemap URL

**Suggested roles:** infrastructure, seo

1. Set lastmod from the date each page's content last changed, not the build time
2. Use W3C Datetime, for example 2026-03-01 or 2026-03-01T09:00:00+00:00
3. Never declare a future date

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Search and AI crawlers recrawl updated pages sooner and keep trusting the dates

**How to check the fix:** Re-run the audit and compare lastmod values with real content changes

### F-008: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <https://www.tatteredcover.com/>
- <https://www.tatteredcover.com/products/0025096985925>
- <https://www.tatteredcover.com/products/9780735329546>
- <https://www.tatteredcover.com/products/9780735367982>
- <https://www.tatteredcover.com/products/9781039498365>

**Evidence:**

- None of the 5 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <https://www.tatteredcover.com/>
  - <https://www.tatteredcover.com/products/0025096985925>
  - <https://www.tatteredcover.com/products/9780735329546>

**What to do:** Claim and link review profiles that fit the business, such as Trustpilot, the Better Business Bureau, Crunchbase or an industry directory

**Suggested roles:** content, developer, seo

1. Claim or create profiles on review platforms that fit the business (Trustpilot, the Better Business Bureau, Crunchbase or an industry directory)
2. Link them from the site footer and list them in Organization sameAs
3. Ask real customers for reviews and answer them publicly

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Independent ratings and reviews corroborate the brand in assistant answers

**How to check the fix:** Re-run the audit after the links or profiles change

### F-009: Physical location is shown on the page but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `location-markup-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer location-dependent questions from machine-readable addresses, coordinates and service areas; a location shown only as text or a map is easy to miss

**Pages:**

- <https://www.tatteredcover.com/>
- <https://www.tatteredcover.com/products/0025096985925>
- <https://www.tatteredcover.com/products/9780735329546>
- <https://www.tatteredcover.com/products/9780735367982>
- <https://www.tatteredcover.com/products/9781039498365>

**Evidence:**

- address: 1997-2026 Tattered Cover Booksellers, LLC 33 East 17th Street, New York, NY 10003. No address, geo or areaServed in any page's JSON-LD
  - <https://www.tatteredcover.com/>
- address: 2526 E Colfax Avenue, Denver, CO 80206. No address, geo or areaServed in any page's JSON-LD
  - <https://www.tatteredcover.com/products/0025096985925>
- address: 2526 E Colfax Avenue, Denver, CO 80206. No address, geo or areaServed in any page's JSON-LD
  - <https://www.tatteredcover.com/products/9780735329546>
- address: 2526 E Colfax Avenue, Denver, CO 80206. No address, geo or areaServed in any page's JSON-LD
  - <https://www.tatteredcover.com/products/9780735367982>
- address: 2526 E Colfax Avenue, Denver, CO 80206. No address, geo or areaServed in any page's JSON-LD
  - <https://www.tatteredcover.com/products/9781039498365>

**What to do:** State the address, coordinates and service area in Organization or LocalBusiness JSON-LD

**Suggested roles:** content, developer, seo

1. Add a PostalAddress (streetAddress, addressLocality, postalCode, addressCountry) to the Organization or LocalBusiness markup
2. Add geo coordinates for each physical location, and areaServed for the regions served
3. Keep the visible address, the markup and the business profile identical

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** The brand can be matched to location-specific questions

**How to check the fix:** Validate the markup and confirm the address matches the visible text

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.tatteredcover.com/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.tatteredcover.com/#organization",
  "name": "Tattered Cover",
  "url": "https://www.tatteredcover.com/",
  "logo": "https://www.tatteredcover.com/cdn/shop/files/TC_Website_Favicon.png?v=1749838786&width=180",
  "description": "Tattered Cover",
  "sameAs": [
    "https://twitter.com/TatteredCover",
    "https://www.facebook.com/tattered.cover",
    "https://www.instagram.com/tatteredcoverbookstore/",
    "https://www.linkedin.com/company/tatteredcoverbookstore",
    "https://www.tiktok.com/@tattered.cover"
  ],
  "address": "1997-2026 Tattered Cover Booksellers, LLC 33 East 17th Street, New York, NY 10003",
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "REPLACE_WITH_LATITUDE",
    "longitude": "REPLACE_WITH_LONGITUDE"
  },
  "areaServed": "REPLACE_WITH_AREA_SERVED"
}
</script>
```

Replace before publishing: `REPLACE_WITH_AREA_SERVED`, `REPLACE_WITH_LATITUDE`, `REPLACE_WITH_LONGITUDE`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **An XML sitemap is available.** An XML sitemap was read; it lists 2002 URLs.
- **llms.txt is present and well formed.** /llms.txt is present, follows the optional artifact format and lists 3 links. Google Search ignores it; visibility gains are unmeasured.
- **Pages are served over HTTPS.** All 5 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 5 pages checked have a document title.
- **Every page has a meta description.** All 5 pages checked have a meta description.
- **Every page declares its language.** All 5 pages checked declare their language (html lang).
- **Every page declares a canonical URL.** All 5 pages checked declare a canonical URL on this site.
- **Pages are open to indexing and snippets.** None of the 5 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Structured data parses cleanly.** JSON-LD structured data is on 5 of the 5 pages checked, and every block parsed.
- **Content is in the raw HTML.** All 5 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 5 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 5 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 128 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
- **Every page links onward.** Each of the 5 pages crawled links to at least one other page on the site.

## Agent checks

Received: not supplied. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The agent stage was not supplied. |
| AG-02 Independent mentions | not assessed | The agent stage was not supplied. |
| AG-03 Independent contradiction | not assessed | The agent stage was not supplied. |
| AG-04 Facts drawn inside images | not assessed | The agent stage was not supplied. |
| AG-05 Namesake ambiguity | not assessed | The agent stage was not supplied. |
| AG-06 Review and profile opportunity | not assessed | The agent stage was not supplied. |

## What this audit could not check

- 301 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 307 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 2 of 6 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- No search for same-named knowledge-graph entities was run: robots.txt for Wikidata and Wikipedia disallows their search endpoints, so only the agent stage (AG-05) can look the brand name up; namesake ambiguity is unassessed.
- Linked sameAs and review profiles were not fetched (OFF\_SITE\_LOOKUP=0), so whether they resolve and belong to the brand was not checked.
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- 3 link(s) listed in llms.txt were not checked (another domain, robots rules, the per-audit cap or a fetch error; see coverage.llms\_txt).
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 37 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.

## Notes from the run

- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- No external search provider configured (SEARCH\_API\_URL unset); footprint assessment is an optional capability in this deployment (not checked, not "no presence found").
- Off-site profile lookup disabled (OFF\_SITE\_LOOKUP=0); linked profiles were not fetched or verified.
- An email signup form appears on 5/5 sampled pages. A site audit cannot see the emails the site sends, so whether inbox assistants can summarize them was not checked.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
