# Brand AI-Readiness Audit: https://www.habitat.org/

- **Audited at:** 2026-10-13T03:16:01.815002+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 286 discovered; 6 of 111 site sections reached
- **Run time:** 20.3 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 17 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.05)

Confidence is low (0.05). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 286 discovered page(s) and reached 6 of 111 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.05 | The page sample is small or one-sided: the crawl analyzed 6 of 286 discovered page(s) and reached 6 of 111 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.60 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 8 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 7 |
| Improvement suggestions (not defects) | 7 |
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
| F-001 | Defect | medium | confirmed | Links or buttons have no accessible name | 6 |
| F-002 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 6 |
| F-003 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 6/6 sampled pages, og:image on 6/6 sampled pages, og:title on 1/6 sampled pages, og:url on 1/6 sampled pages | 6 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 5/6 sampled pages | 5 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 2/6 sampled pages | 2 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 5 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 1/6 sampled pages | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Sitemap lastmod dates are missing or unreliable | 0 |

## Finding details

### F-001: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://www.habitat.org/>
- <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>
- <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>

**Evidence:**

- 4 unnamed control(s): &lt;a href=/&gt; with only an icon, &lt;button&gt; with only an icon, &lt;button&gt; with no content, &lt;button&gt; with no content
  - <https://www.habitat.org/>
- 6 unnamed control(s): &lt;a href=/&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=/&gt; with no content, &lt;button&gt; with no content
  - <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- 6 unnamed control(s): &lt;a href=/&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=/&gt; with no content, &lt;button&gt; with no content
  - <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- 6 unnamed control(s): &lt;a href=/&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=/&gt; with no content, &lt;button&gt; with no content
  - <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- 6 unnamed control(s): &lt;a href=/&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=/&gt; with no content, &lt;button&gt; with no content
  - <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>
- and 1 more observations in the JSON report

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 6 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 6 of 286 discovered pages that were actually crawled)

**Pages:**

- <https://www.habitat.org/>
- <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>
- <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>

**Evidence:**

- 0/6 pages contain JSON-LD
  - <https://www.habitat.org/>
  - <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
  - <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
  - <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
  - <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>
  - and 1 more

**What to do:** Add Organization/Product/Article JSON-LD to key pages

**Suggested roles:** developer, seo

1. Identify page types
2. Add matching schema.org JSON-LD blocks

Effort: medium; Impact: medium; Major project: real value, plan the work.

**Expected benefit:** Key facts are also stated as explicit structured data; no ranking or citation gain is implied

**How to check the fix:** Validate JSON-LD with a schema.org validator

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- Home page https://www.habitat.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.habitat.org/#organization",
      "name": "Habitat for Humanity",
      "url": "https://www.habitat.org/",
      "logo": "https://www.habitat.org/favicon.ico",
      "description": "Habitat for Humanity is a nonprofit organization that helps people in your community and around the world build or improve a place they can call home. Donate, volunteer and raise your voice in support of decent and affordable housing.",
      "sameAs": [
        "https://www.youtube.com/watch?v=PgtlcFSG4zs",
        "https://www.facebook.com/habitatforhumanity/",
        "https://twitter.com/habitat_org",
        "https://www.youtube.com/user/HabitatForHumanity",
        "https://www.pinterest.com/habitathumanity",
        "https://www.instagram.com/habitatforhumanity/"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.habitat.org/#website",
      "name": "Habitat for Humanity",
      "url": "https://www.habitat.org/",
      "publisher": {
        "@id": "https://www.habitat.org/#organization"
      }
    }
  ]
}
</script>

<!-- Other page https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine",
  "name": "Volunteer",
  "description": "REPLACE_WITH_PAGE_DESCRIPTION",
  "about": {
    "@id": "https://www.habitat.org/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-003: Open Graph tags missing: og:description on 6/6 sampled pages, og:image on 6/6 sampled pages, og:title on 1/6 sampled pages, og:url on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.habitat.org/>
- <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>
- <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.habitat.org/>
- Missing nonempty fields: og:description, og:image
  - <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- Missing nonempty fields: og:description, og:image
  - <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- Missing nonempty fields: og:description, og:image
  - <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- Missing nonempty fields: og:description, og:image
  - <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>
- and 1 more observations in the JSON report

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

**Suggested roles:** developer, seo

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.habitat.org/ -->
<meta property="og:title" content="Habitat for Humanity">
<meta property="og:description" content="Habitat for Humanity is a nonprofit organization that helps people in your community and around the world build or improve a place they can call home. Donate, volunteer and raise your voice in support">
<meta property="og:image" content="https://www.habitat.org/sites/default/files/styles/2_1_xsmall/public/2025-11/Interstitial-FY26_November_Thanksgiving.jpg?itok=DeUxlW5A">
<meta property="og:url" content="https://www.habitat.org/">

<!-- https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine -->
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">

<!-- https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity -->
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`, `REPLACE_WITH_SHARE_IMAGE_URL`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-004: No meta description on 5/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>
- <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>

**What to do:** Write a concise page-specific meta description that matches visible content.

**Suggested roles:** developer, seo

1. Write a concise page-specific meta description that matches visible content.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides a summary candidate; search engines may choose other text.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-005: Heading levels are skipped on 2/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>

**Evidence:**

- Observed heading levels: \[2, 2, 2, 2, 2, 2, 2, 1, 3, 4, 4, 4, 4, 4\]
  - <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- Observed heading levels: \[2, 2, 2, 2, 2, 2, 2, 1, 3, 4, 4, 4, 4, 4\]
  - <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-006: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
- <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
- <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
- <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>
- <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>

**Evidence:**

- Visible breadcrumb without schema
  - <https://www.habitat.org/me/bath/habitat-humanity-7-rivers-maine>
  - <https://www.habitat.org/tx/abilene/habitat-humanity-abilene>
  - <https://www.habitat.org/pa/gettysburg/adams-county-habitat-humanity>
  - <https://www.habitat.org/wi/mauston/habitat-humanity-adams-county-wisconsin>
  - <https://www.habitat.org/vt/middlebury/habitat-humanity-addison-county-vt>

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-007: No valid twitter:card tag on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.habitat.org/>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.habitat.org/>

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.habitat.org/ -->
<meta name="twitter:card" content="summary_large_image">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-008: Sitemap lastmod dates are missing or unreliable

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-lastmod-unreliable`; Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 0 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Sitemap lastmod dates are missing, malformed or not set per page, so crawlers cannot rely on them to recrawl changed pages first

**Evidence:**

- 195 of 200 valid lastmod values are the same date (2025-10-23), so they reflect when the sitemap was generated, not when each page changed

**What to do:** Publish an accurate &lt;lastmod&gt; for every sitemap URL

**Suggested roles:** infrastructure, seo

1. Set lastmod from the date each page's content last changed, not the build time
2. Use W3C Datetime, for example 2026-03-01 or 2026-03-01T09:00:00+00:00
3. Never declare a future date

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Search and AI crawlers recrawl updated pages sooner and keep trusting the dates

**How to check the fix:** Re-run the audit and compare lastmod values with real content changes

## Other recommendations

Good practice to keep, beyond the findings above:

- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **An XML sitemap is available.** An XML sitemap was read; it lists at least 1790 URLs.
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Every page declares a canonical URL.** All 6 pages checked declare a canonical URL on this site.
- **Pages are open to indexing and snippets.** None of the 6 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 6 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 15 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
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

- 280 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 286 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 6 of 111 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 10 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.

## Notes from the run

- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- An email signup form appears on 1/6 sampled pages. A site audit cannot see the emails the site sends, so whether inbox assistants can summarize them was not checked.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
