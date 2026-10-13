# Brand AI-Readiness Audit: http://127.0.0.1:44267/

- **Audited at:** 2026-10-13T03:16:28.535848+00:00
- **Run:** Completed
- **Pages:** 1 analyzed of 2 discovered; 1 of 2 site sections reached
- **Run time:** 0.0 seconds
- **Time limits:** audit worker stopped at 60 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 7 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** medium (0.50)

Confidence is medium (0.50). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 1 of 2 discovered page(s) and reached 1 of 2 site section(s); how many pages the site has is unknown, so the discovered URLs may not be all of it. Brand identity (reported separately, not part of the score): No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.50 | The page sample is small or one-sided: the crawl analyzed 1 of 2 discovered page(s) and reached 1 of 2 site section(s); how many pages the site has is unknown, so the discovered URLs may not be all of it. |
| Brand identity (not in the score) | 0.00 | No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 11 |
| Critical | 0 |
| High | 1 |
| Medium | 3 |
| Low | 7 |
| Improvement suggestions (not defects) | 8 |
| Not enough evidence to judge | 0 |
| Recommendations | 8 |

## Start here

**F-002: Pages lack a mobile viewport declaration**

Add an appropriate responsive viewport declaration

Impact medium, effort low. Details are under F-002 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Sampled content was retrieved over HTTP | Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment. | high | high | medium | no | infrastructure, seo |
| 2 | F-002: Pages lack a mobile viewport declaration | Add an appropriate responsive viewport declaration | medium | medium | low | yes | developer, seo |
| 3 | F-003: Broken pages found during crawl | Fix or redirect broken URLs | medium | medium | medium | no | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-002: Pages lack a mobile viewport declaration.** Add an appropriate responsive viewport declaration (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | high | confirmed | Sampled content was retrieved over HTTP | 1 |
| F-002 | Defect | medium | confirmed | Pages lack a mobile viewport declaration | 1 |
| F-003 | Defect | medium | confirmed | Broken pages found during crawl | 1 |
| F-004 | Improvement opportunity | medium | confirmed | No structured data (JSON-LD) found on any crawled page | 1 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 1/1 sampled page | 1 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 1/1 sampled page, og:image on 1/1 sampled page, og:title on 1/1 sampled page, og:url on 1/1 sampled page | 1 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 1/1 sampled page | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | No XML sitemap found | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 1/1 sampled page | 1 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 1/1 sampled page | 1 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 1 |

## Finding details

### F-001: Sampled content was retrieved over HTTP

Type: Defect; Severity: high; Status: confirmed; Confidence: 0.95; Check: `http-transport`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** high severity, confirmed status, confidence 0.95; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** HTTP does not encrypt the fetched connection.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- Retrieved URL: http://127.0.0.1:44267/
  - <http://127.0.0.1:44267/>

**What to do:** Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment.

**Suggested roles:** infrastructure, seo

1. Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment.

Effort: medium; Impact: high; Major project: real value, plan the work.

**Expected benefit:** Protects transport confidentiality and integrity; ranking gains are not asserted.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-002: Pages lack a mobile viewport declaration

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.95; Check: `viewport`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.95; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No viewport declaration was observed; actual layout behavior requires visual verification.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- No viewport declaration was observed; actual layout behavior requires visual verification.
  - <http://127.0.0.1:44267/>

**What to do:** Add an appropriate responsive viewport declaration

**Suggested roles:** developer, seo

1. Add an appropriate responsive viewport declaration
2. Verify that layout reflows and remains readable

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-003: Broken pages found during crawl

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.90; Check: `broken-pages`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.9; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages return 4xx/5xx status codes (found within 1 of 2 discovered pages actually crawled -- the rest of the site was not checked)

**Pages:**

- <http://127.0.0.1:44267/about>

**Evidence:**

- 1 pages returned errors
  - <http://127.0.0.1:44267/about>

**What to do:** Fix or redirect broken URLs

**Suggested roles:** developer, seo

1. Audit error pages
2. Add 301 redirects or restore content

Effort: medium; Impact: medium; Major project: real value, plan the work.

**Expected benefit:** Improves crawl completeness

**How to check the fix:** Re-crawl and confirm 200 status

### F-004: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 1 of 2 discovered pages that were actually crawled)

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- 0/1 pages contain JSON-LD
  - <http://127.0.0.1:44267/>

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
<!-- Home page http://127.0.0.1:44267/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "http://127.0.0.1:44267/#organization",
      "name": "REPLACE_WITH_BRAND_NAME",
      "url": "http://127.0.0.1:44267/",
      "logo": "REPLACE_WITH_LOGO_URL",
      "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION"
    },
    {
      "@type": "WebSite",
      "@id": "http://127.0.0.1:44267/#website",
      "name": "REPLACE_WITH_BRAND_NAME",
      "url": "http://127.0.0.1:44267/",
      "publisher": {
        "@id": "http://127.0.0.1:44267/#organization"
      }
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_BRAND_NAME`, `REPLACE_WITH_LOGO_URL`, `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-005: No meta description on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <http://127.0.0.1:44267/>

**What to do:** Write a concise page-specific meta description that matches visible content.

**Suggested roles:** developer, seo

1. Write a concise page-specific meta description that matches visible content.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides a summary candidate; search engines may choose other text.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-006: Open Graph tags missing: og:description on 1/1 sampled page, og:image on 1/1 sampled page, og:title on 1/1 sampled page, og:url on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <http://127.0.0.1:44267/>

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

**Suggested roles:** developer, seo

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- http://127.0.0.1:44267/ -->
<meta property="og:title" content="Acme">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">
<meta property="og:url" content="http://127.0.0.1:44267/">
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`, `REPLACE_WITH_SHARE_IMAGE_URL`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: Title shorter than 15 or longer than 70 characters on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- Title has 4 characters: Acme. Display width was not measured.
  - <http://127.0.0.1:44267/>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: No XML sitemap found

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-unavailable`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without a discovered sitemap, this audit relies more heavily on sampled links.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- Sitemap probe status: absent; checked: http://127.0.0.1:44267/sitemap.xml (absent). No additional sitemap discovery was attempted by this check.
  - <http://127.0.0.1:44267/>

**What to do:** If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

**Suggested roles:** infrastructure, seo

1. If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves inventory discovery; absence is not a universal indexing defect.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-009: No rel=canonical tag on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <http://127.0.0.1:44267/>

**What to do:** Assess real duplicates before declaring the correct absolute canonical URL.

**Suggested roles:** developer, seo

1. Assess real duplicates before declaring the correct absolute canonical URL.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Helps supporting consumers consolidate duplicate URLs when applicable.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- http://127.0.0.1:44267/ -->
<link rel="canonical" href="http://127.0.0.1:44267/">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-010: No valid twitter:card tag on 1/1 sampled page

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <http://127.0.0.1:44267/>

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- http://127.0.0.1:44267/ -->
<meta name="twitter:card" content="summary">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-011: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 1 of 1 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <http://127.0.0.1:44267/>

**Evidence:**

- None of the 1 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <http://127.0.0.1:44267/>

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
- **Every page has a title.** All 1 page checked have a document title.
- **Every page declares its language.** All 1 page checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 1 page checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 1 page checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 1 page checked have an H1 heading.

## Agent checks

Received: outcome envelope. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The observed About target returned HTTP 503. Its body opening is unavailable, and the homepage cannot stand in for this known failed target. |
| AG-02 Independent mentions | not assessed | Search was not performed in this failed-About rehearsal. |
| AG-03 Independent contradiction | not assessed | Search was not performed in this failed-About rehearsal. |
| AG-04 Facts drawn inside images | not assessed | No image was viewed. |
| AG-05 Namesake ambiguity | not assessed | Search was not performed in this failed-About rehearsal. |
| AG-06 Review and profile opportunity | not assessed | Search was not performed in this failed-About rehearsal. |

## What this audit could not check

- How many pages the site has is unknown: no sitemap was available, so URLs were found by following links from the pages fetched. Findings speak for the 2 discovered URL(s), not for pages the crawl did not find.
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- Agent check AG-01 (About-page concreteness) was not assessed: The observed About target returned HTTP 503. Its body opening is unavailable, and the homepage cannot stand in for this known failed target.
- Agent check AG-02 (Independent mentions) was not assessed: Search was not performed in this failed-About rehearsal.
- Agent check AG-03 (Independent contradiction) was not assessed: Search was not performed in this failed-About rehearsal.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No image was viewed.
- Agent check AG-05 (Namesake ambiguity) was not assessed: Search was not performed in this failed-About rehearsal.
- Agent check AG-06 (Review and profile opportunity) was not assessed: Search was not performed in this failed-About rehearsal.

## Notes from the run

- No dated facts found; freshness cannot be assessed (absence is not proof of staleness).
- Entity identity unresolved; corroboration suppressed.
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: 1 fetched page(s) could not be read in full or build their links with JavaScript (see the site graph's crawl\_scope.unresolved), so links from them are unknown.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
