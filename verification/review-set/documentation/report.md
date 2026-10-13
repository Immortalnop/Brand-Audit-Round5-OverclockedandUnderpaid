# Brand AI-Readiness Audit: https://developer.mozilla.org/en-US/docs/Web

- **Audited at:** 2026-10-13T03:29:40.967756+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 327 discovered; 1 of 13 site sections reached
- **Run time:** 12.9 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 17 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.08)

Confidence is low (0.08). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 327 discovered page(s) and reached 1 of 13 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.08 | The page sample is small or one-sided: the crawl analyzed 6 of 327 discovered page(s) and reached 1 of 13 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.50 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 12 |
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 10 |
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
| 2 | F-002: Sampled content page carries noindex indexing controls | Review whether noindex is intentional on this page | medium | medium | low | yes | developer, seo |
| 3 | F-003: Images are heavier than they need to be | Compress, resize and convert the listed images | low | low | medium | no | developer, seo |
| 4 | F-004: Image alt text is a file name, placeholder or repeated label that describes nothing | Replace placeholder alt text with a short description of each image | low | low | low | no | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Links or buttons have no accessible name.** Name every icon-only link and button (impact medium, effort low)
- **F-002: Sampled content page carries noindex indexing controls.** Review whether noindex is intentional on this page (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Links or buttons have no accessible name | 6 |
| F-002 | Defect | medium | confirmed | Sampled content page carries noindex indexing controls | 1 |
| F-003 | Defect | low | confirmed | Images are heavier than they need to be | 1 |
| F-004 | Defect | low | confirmed | Image alt text is a file name, placeholder or repeated label that describes nothing | 1 |
| F-005 | Improvement opportunity | low | confirmed | Article authors lack a Person profile or credentials | 1 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Likely Largest Contentful Paint (LCP) risk, estimated from markup and not measured | 2 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 1/6 sampled pages | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 3/6 sampled pages | 3 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Visible text is under 3% of the HTML on 1/6 sampled pages | 1 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 6 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 6 |

## Finding details

### F-001: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://developer.mozilla.org/en-US/>
- <https://developer.mozilla.org/en-US/404>
- <https://developer.mozilla.org/en-US/about>
- <https://developer.mozilla.org/en-US/advertising>
- <https://developer.mozilla.org/en-US/blog/>
- <https://developer.mozilla.org/en-US/docs/Web>

**Evidence:**

- 13 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/de/docs/Web&gt; with no content
  - <https://developer.mozilla.org/en-US/docs/Web>
- 13 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/de/&gt; with no content
  - <https://developer.mozilla.org/en-US/>
- 4 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/en-US/404&gt; with no content
  - <https://developer.mozilla.org/en-US/404>
- 4 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/en-US/about&gt; with no content
  - <https://developer.mozilla.org/en-US/about>
- 13 unnamed control(s): &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;button&gt; with no content, &lt;a href=/de/advertising&gt; with no content
  - <https://developer.mozilla.org/en-US/advertising>
- and 1 more observations in the JSON report

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: Sampled content page carries noindex indexing controls

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `noindex`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The observed noindex directive (meta robots) limits indexing or snippets for this page within that crawler scope; intentional exclusions should be retained.

**Pages:**

- <https://developer.mozilla.org/en-US/404>

**Evidence:**

- meta robots
  - <https://developer.mozilla.org/en-US/404>

**What to do:** Review whether noindex is intentional on this page

**Suggested roles:** developer, seo

1. Confirm each page is intended for search discovery
2. Remove the directive only where unintended; preserve private/duplicate-page controls

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Restores eligibility within the affected crawler scope, without guaranteeing citations

**How to check the fix:** Refetch HTML and headers and confirm the intended noindex policy

### F-003: Images are heavier than they need to be

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.90; Check: `image-weight`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.9; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Large, oversized or legacy-format image files delay the largest paint and cost mobile visitors data, so visitors arriving from search or an AI answer wait longer

**Pages:**

- <https://developer.mozilla.org/en-US/blog/>

**Evidence:**

- https://developer.mozilla.org/en-US/blog/daily-holiday-javascript-challenges/featured.png: the file is 317 KB; it is served as PNG although the request accepted AVIF and WebP
  - <https://developer.mozilla.org/en-US/blog/>

**What to do:** Compress, resize and convert the listed images

**Suggested roles:** developer, seo

1. Serve AVIF or WebP, with JPEG or PNG only as a fallback in &lt;picture&gt;
2. Resize each image to the largest size it is displayed at and add srcset and sizes for smaller screens
3. Compress photos, aiming for under 200 KB for the largest image of a page

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Faster largest paint and less data for visitors on mobile

**How to check the fix:** Re-run the audit and confirm the listed images are smaller

### F-004: Image alt text is a file name, placeholder or repeated label that describes nothing

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `alt-text-quality`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Alt text such as a file name or a word like 'banner' gives crawlers, assistants and screen readers no description of the image

**Pages:**

- <https://developer.mozilla.org/en-US/blog/>

**Evidence:**

- 4 image(s) with uninformative alt text, for example alt="author avatar" (the same alt text on 18 different images) on https://developer.mozilla.org/en-US/blog/author/brian-smith/avatar.jpg; alt="author avatar" (the same alt text on 18 different images) on https://developer.mozilla.org/en-US/blog/author/debugbear/avatar.png; alt="author avatar" (the same alt text on 18 different images) on https://developer.mozilla.org/en-US/blog/author/gitlab/avatar.png
  - <https://developer.mozilla.org/en-US/blog/>

**What to do:** Replace placeholder alt text with a short description of each image

**Suggested roles:** developer, seo

1. Write alt text that says what each informative image shows, in a short phrase
2. Use an empty alt="" for purely decorative images instead of a placeholder word
3. Fix the CMS or template default that fills alt text with the file name

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Crawlers, assistants and screen readers can tell what each image shows

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-005: Article authors lack a Person profile or credentials

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `author-credentials-weak`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.75; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The article author is not stated as a Person with a profile and credentials, so the expertise behind the content cannot be checked

**Pages:**

- <https://developer.mozilla.org/en-US/blog/>

**Evidence:**

- the byline is not stated in Article markup (no author property)
  - <https://developer.mozilla.org/en-US/blog/>

**What to do:** State each article author as a Person with a profile and credentials

**Suggested roles:** content, developer, seo

1. Type the Article author as a Person, not a plain string or the Organization
2. Give the Person a url to an author page and sameAs links to professional profiles
3. Add jobTitle, description or knowsAbout that state the author's expertise
4. Show the same author name in the visible byline

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** The expertise behind each article becomes explicit and checkable

**How to check the fix:** Validate the Article markup and re-run the audit

### F-006: Likely Largest Contentful Paint (LCP) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Markup patterns that delay the largest paint were observed: the main content may appear slowly

**Pages:**

- <https://developer.mozilla.org/en-US/>
- <https://developer.mozilla.org/en-US/about>

**Evidence:**

- Estimate, not a measurement: the first content image is lazy-loaded in the HTML; 20 render-blocking scripts and stylesheets in the head
  - <https://developer.mozilla.org/en-US/>
- Estimate, not a measurement: the first content image is lazy-loaded in the HTML; 11 render-blocking scripts and stylesheets in the head
  - <https://developer.mozilla.org/en-US/about>

**What to do:** Check LCP in a browser or with field data, and remove the listed patterns

**Suggested roles:** developer, seo

1. Do not lazy-load the first large image; give it fetchpriority="high" or preload it
2. Defer or async non-critical scripts and inline only critical CSS
3. Reduce server response time with caching
4. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Largest Contentful Paint score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-007: Heading levels are skipped on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://developer.mozilla.org/en-US/about>

**Evidence:**

- Observed heading levels: \[1, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4\]
  - <https://developer.mozilla.org/en-US/about>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://developer.mozilla.org/en-US/about>

**Evidence:**

- First content image https://mdn.dev/generic-content/about/screenshots/20050121103200-960x540@1x.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://developer.mozilla.org/en-US/about>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-009: Title shorter than 15 or longer than 70 characters on 3/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://developer.mozilla.org/en-US/>
- <https://developer.mozilla.org/en-US/about>
- <https://developer.mozilla.org/en-US/blog/>

**Evidence:**

- Title has 12 characters: MDN Web Docs. Display width was not measured.
  - <https://developer.mozilla.org/en-US/>
- Title has 9 characters: About MDN. Display width was not measured.
  - <https://developer.mozilla.org/en-US/about>
- Title has 8 characters: MDN Blog. Display width was not measured.
  - <https://developer.mozilla.org/en-US/blog/>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-010: Visible text is under 3% of the HTML on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `markup-ratio`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A small visible-text share in a large HTML document can indicate excess markup.

**Pages:**

- <https://developer.mozilla.org/en-US/404>

**Evidence:**

- Visible text represents 2.6% of decoded HTML body bytes. This is not a ranking metric.
  - <https://developer.mozilla.org/en-US/404>

**What to do:** Inspect inline assets and template boilerplate before trimming unnecessary HTML.

**Suggested roles:** developer, seo

1. Inspect inline assets and template boilerplate before trimming unnecessary HTML.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Reduces document overhead if the sampled ratio reflects avoidable markup.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-011: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://developer.mozilla.org/en-US/>
- <https://developer.mozilla.org/en-US/404>
- <https://developer.mozilla.org/en-US/about>
- <https://developer.mozilla.org/en-US/advertising>
- <https://developer.mozilla.org/en-US/blog/>
- <https://developer.mozilla.org/en-US/docs/Web>

**Evidence:**

- Visible breadcrumb without schema
  - <https://developer.mozilla.org/en-US/docs/Web>
  - <https://developer.mozilla.org/en-US/>
  - <https://developer.mozilla.org/en-US/404>
  - <https://developer.mozilla.org/en-US/about>
  - <https://developer.mozilla.org/en-US/advertising>
  - and 1 more

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-012: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <https://developer.mozilla.org/en-US/>
- <https://developer.mozilla.org/en-US/404>
- <https://developer.mozilla.org/en-US/about>
- <https://developer.mozilla.org/en-US/advertising>
- <https://developer.mozilla.org/en-US/blog/>
- <https://developer.mozilla.org/en-US/docs/Web>

**Evidence:**

- None of the 6 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <https://developer.mozilla.org/en-US/docs/Web>
  - <https://developer.mozilla.org/en-US/>
  - <https://developer.mozilla.org/en-US/404>

**What to do:** Claim and link review profiles that fit the business, such as Trustpilot, the Better Business Bureau, Crunchbase or an industry directory

**Suggested roles:** content, developer, seo

1. Claim or create profiles on review platforms that fit the business (Trustpilot, the Better Business Bureau, Crunchbase or an industry directory)
2. Link them from the site footer and list them in Organization sameAs
3. Ask real customers for reviews and answer them publicly

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Independent ratings and reviews corroborate the brand in assistant answers

**How to check the fix:** Re-run the audit after the links or profiles change

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **An XML sitemap is available.** An XML sitemap was read; it lists at least 10743 URLs.
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page has a meta description.** All 6 pages checked have a meta description.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Every page declares a canonical URL.** All 6 pages checked declare a canonical URL on this site.
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 6 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Every page links onward.** Each of the 6 pages crawled links to at least one other page on the site.

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

- 321 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 327 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 1 of 13 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 5 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.

## Notes from the run

- English lexical checks skipped on pages with unknown/non-English language or truncated retained text.
- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
