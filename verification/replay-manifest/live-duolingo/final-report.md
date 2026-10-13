# Brand AI-Readiness Audit: https://www.duolingo.com/

- **Audited at:** 2026-10-13T13:06:29.066304+00:00
- **Run:** Completed
- **Pages:** 1 analyzed of 64 discovered; 1 of 24 site sections reached
- **Run time:** 58.8 seconds
- **Time limits:** audit worker stopped at 270 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 72 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.03)

Confidence is low (0.03). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 1 of 64 discovered page(s) and reached 1 of 24 site section(s); how many pages the site has is unknown, so the discovered URLs may not be all of it. Also weak: Not every page was read in full: 3 fetch(es) returned no readable content (a challenge, waiting room, timeout or failure). Brand identity (reported separately, not part of the score): No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.03 | The page sample is small or one-sided: the crawl analyzed 1 of 64 discovered page(s) and reached 1 of 24 site section(s); how many pages the site has is unknown, so the discovered URLs may not be all of it. |
| Brand identity (not in the score) | 0.00 | No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 8 |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 8 |
| Improvement suggestions (not defects) | 8 |
| Not enough evidence to judge | 0 |
| Recommendations | 8 |

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 1 |
| F-002 | Improvement opportunity | low | confirmed | Sitemap lastmod dates are missing or unreliable | 0 |
| F-003 | Improvement opportunity | low | confirmed | Dead-end pages with no outgoing links | 1 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 1/1 sampled page, og:image on 1/1 sampled page, og:title on 1/1 sampled page, og:url on 1/1 sampled page | 1 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | No main or article landmark on 1/1 sampled page | 1 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 1/1 sampled page | 1 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | No site search on 1/1 sampled page of a site with 79 URLs | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 1 |

## Finding details

### F-001: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 1 of 64 discovered pages that were actually crawled)

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- 0/1 pages contain JSON-LD
  - <https://www.duolingo.com/nojs/splash>

**What to do:** Add Organization/Product/Article JSON-LD to key pages

**Suggested roles:** developer, seo

1. Identify page types
2. Add matching schema.org JSON-LD blocks

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Key facts are also stated as explicit structured data; no ranking or citation gain is implied

**How to check the fix:** Validate JSON-LD with a schema.org validator

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- Home page https://www.duolingo.com/nojs/splash -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.duolingo.com/#organization",
      "name": "Duolingo: Learn Spanish, French and other languages for free",
      "url": "https://www.duolingo.com/",
      "logo": "REPLACE_WITH_LOGO_URL",
      "description": "Bring the world's most popular language-learning platform to your classroom. No ads, 100% free."
    },
    {
      "@type": "WebSite",
      "@id": "https://www.duolingo.com/#website",
      "name": "Duolingo: Learn Spanish, French and other languages for free",
      "url": "https://www.duolingo.com/",
      "publisher": {
        "@id": "https://www.duolingo.com/#organization"
      }
    }
  ]
}
</script>

<!-- Other page https://www.duolingo.com/nojs/splash -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://www.duolingo.com/nojs/splash",
  "name": "Learn a language for free. Forever.",
  "description": "Bring the world's most popular language-learning platform to your classroom. No ads, 100% free.",
  "about": {
    "@id": "https://www.duolingo.com/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_LOGO_URL`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-002: Sitemap lastmod dates are missing or unreliable

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `sitemap-lastmod-unreliable`; Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 0 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Sitemap lastmod dates are missing, malformed or not set per page, so crawlers cannot rely on them to recrawl changed pages first

**Evidence:**

- None of the 79 sitemap URL entries declares &lt;lastmod&gt;

**What to do:** Publish an accurate &lt;lastmod&gt; for every sitemap URL

**Suggested roles:** infrastructure, seo

1. Set lastmod from the date each page's content last changed, not the build time
2. Use W3C Datetime, for example 2026-03-01 or 2026-03-01T09:00:00+00:00
3. Never declare a future date

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Search and AI crawlers recrawl updated pages sooner and keep trusting the dates

**How to check the fix:** Re-run the audit and compare lastmod values with real content changes

### F-003: Dead-end pages with no outgoing links

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.70; Check: `dead-ends`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.7; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The delivered HTML of these pages links to no other page of the site, so a visitor or crawler reading it has no next step

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- 1 page(s) whose delivered HTML, read in full, has no link to another page of the site
  - <https://www.duolingo.com/nojs/splash>

**What to do:** Add related links or calls-to-action on dead-end pages

**Suggested roles:** developer, seo

1. Add related-content links
2. Add a clear next-step call-to-action

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each listed page offers a next step; visitor behaviour is not measured

**How to check the fix:** Confirm pages link to at least one next step

### F-004: Open Graph tags missing: og:description on 1/1 sampled page, og:image on 1/1 sampled page, og:title on 1/1 sampled page, og:url on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.duolingo.com/nojs/splash>

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

**Suggested roles:** developer, seo

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.duolingo.com/nojs/splash -->
<meta property="og:title" content="Duolingo: Learn Spanish, French and other languages for free">
<meta property="og:description" content="Bring the world&#x27;s most popular language-learning platform to your classroom. No ads, 100% free.">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">
<meta property="og:url" content="https://www.duolingo.com/nojs/splash">
```

Replace before publishing: `REPLACE_WITH_SHARE_IMAGE_URL`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-005: No main or article landmark on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-landmarks`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Content without a main or article landmark may be harder to distinguish from boilerplate.

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- No main or article landmark observed on a page with substantial text.
  - <https://www.duolingo.com/nojs/splash>

**What to do:** Mark the main content semantically and keep navigation outside it when appropriate.

**Suggested roles:** developer, seo

1. Mark the main content semantically and keep navigation outside it when appropriate.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves structural clarity for supporting readers and extractors.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-006: No valid twitter:card tag on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.duolingo.com/nojs/splash>

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.duolingo.com/nojs/splash -->
<meta name="twitter:card" content="summary">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: No site search on 1/1 sampled page of a site with 79 URLs

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `site-search-missing`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A visitor who arrives from an AI answer with a follow-up need must browse menus to find it when a large site offers no search box, and many leave instead

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- No search input, role="search" form or SearchAction on 1 sampled pages; the sitemap and crawl list 79 URLs
  - <https://www.duolingo.com/nojs/splash>

**What to do:** Add a site search box to the header of every page

**Suggested roles:** developer, seo

1. Add a &lt;form role="search"&gt; with a labelled search input to the shared header
2. Make results pages reachable by URL (for example /search?q=term) so they can be linked
3. Declare the search URL as a WebSite SearchAction in JSON-LD

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Visitors can restate their need in one step instead of leaving

**How to check the fix:** Re-run the audit and confirm a search form is detected

### F-008: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <https://www.duolingo.com/nojs/splash>

**Evidence:**

- None of the 1 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <https://www.duolingo.com/nojs/splash>

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
- **An XML sitemap is available.** An XML sitemap was read; it lists 79 URLs.
- **Pages are served over HTTPS.** All 1 page checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 1 page fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 1 page checked have a document title.
- **Every page has a meta description.** All 1 page checked have a meta description.
- **Every page declares its language.** All 1 page checked declare their language (html lang).
- **Every page declares a canonical URL.** All 1 page checked declare a canonical URL on this site.
- **Pages are open to indexing and snippets.** None of the 1 page checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 1 page checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 1 page checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 1 page checked declare a mobile viewport, and none blocks zooming.

## Agent checks

Received: outcome envelope. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The packet-selected homepage opening is not assessable or complete; no eligible selected body opening is supplied. No substitute passage was fetched. |
| AG-02 Independent mentions | not assessed | The packet identity is unresolved; no packet-supported identity binding satisfying the search contract was available. Host search was not executed. |
| AG-03 Independent contradiction | not assessed | The packet identity is unresolved and no eligible bound claim/identity comparison was assessed. No independent conflict inspection was executed. |
| AG-04 Facts drawn inside images | not assessed | No full packet-listed image was viewed. Filename, alt text or header evidence is not a visual assessment. |
| AG-05 Namesake ambiguity | not assessed | The acquired target identity lacks the binding needed by the search contract. No namesake search was executed. |
| AG-06 Review and profile opportunity | not assessed | The acquired identity lacks the binding needed by the search contract. No platform search was executed; profile absence is not established. |

## What this audit could not check

- How many pages the site has is unknown: URLs were found by following links from the pages fetched. Findings speak for the 64 discovered URL(s), not for pages the crawl did not find.
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- Agent check AG-01 (About-page concreteness) was not assessed: The packet-selected homepage opening is not assessable or complete; no eligible selected body opening is supplied. No substitute passage was fetched.
- Agent check AG-02 (Independent mentions) was not assessed: The packet identity is unresolved; no packet-supported identity binding satisfying the search contract was available. Host search was not executed.
- Agent check AG-03 (Independent contradiction) was not assessed: The packet identity is unresolved and no eligible bound claim/identity comparison was assessed. No independent conflict inspection was executed.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No full packet-listed image was viewed. Filename, alt text or header evidence is not a visual assessment.
- Agent check AG-05 (Namesake ambiguity) was not assessed: The acquired target identity lacks the binding needed by the search contract. No namesake search was executed.
- Agent check AG-06 (Review and profile opportunity) was not assessed: The acquired identity lacks the binding needed by the search contract. No platform search was executed; profile absence is not established.

## Notes from the run

- Entity identity unresolved; corroboration suppressed.
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: 3 fetched page(s) could not be read in full or build their links with JavaScript (see the site graph's crawl\_scope.unresolved), so links from them are unknown.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
