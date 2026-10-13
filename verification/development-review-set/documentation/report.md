# Brand AI-Readiness Audit: https://www.sqlite.org/docs.html

- **Audited at:** 2026-10-13T03:15:40.699431+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 183 discovered; 6 of 129 site sections reached
- **Run time:** 20.3 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 12 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.05)

Confidence is low (0.05). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 183 discovered page(s) and reached 6 of 129 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.05 | The page sample is small or one-sided: the crawl analyzed 6 of 183 discovered page(s) and reached 6 of 129 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.00 | No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 14 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 13 |
| Improvement suggestions (not defects) | 12 |
| Not enough evidence to judge | 0 |
| Recommendations | 12 |

## Start here

**F-001: Form fields have no label**

Give every form field a visible label tied to it

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Form fields have no label | Give every form field a visible label tied to it | medium | medium | low | yes | developer, seo |
| 2 | F-002: Pages omit an explicit document language | Set an accurate BCP 47 lang attribute on the html element; verify multilingual sections separately. | low | medium | low | yes | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Form fields have no label.** Give every form field a visible label tied to it (impact medium, effort low)
- **F-002: Pages omit an explicit document language.** Set an accurate BCP 47 lang attribute on the html element; verify multilingual sections separately. (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Form fields have no label | 4 |
| F-002 | Defect | low | confirmed | Pages omit an explicit document language | 6 |
| F-003 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 6 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 6/6 sampled pages | 6 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 6/6 sampled pages, og:image on 6/6 sampled pages, og:title on 6/6 sampled pages, og:url on 6/6 sampled pages | 6 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Likely Largest Contentful Paint (LCP) risk, estimated from markup and not measured | 2 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 1/6 sampled pages | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Dense paragraphs may obscure key answers | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Pages lack a descriptive primary heading (H1) that says what the page is about | 1 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | No main or article landmark on 6/6 sampled pages | 6 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 6/6 sampled pages | 6 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 6/6 sampled pages | 6 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | No XML sitemap found | 1 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 3 |

## Finding details

### F-001: Form fields have no label

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `form-label-missing`; Seen on 4 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A field with no label, aria-label or title has no name in the accessibility tree, so screen-reader users and AI agents filling the form cannot tell what it asks for

**Pages:**

- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- 4 unlabeled field(s): &lt;select name=s&gt;, &lt;input type=text name=q&gt;, &lt;select name=s&gt;, &lt;input type=text name=q&gt;
  - <https://www.sqlite.org/docs.html>
- 2 unlabeled field(s): &lt;select name=s&gt;, &lt;input type=text name=q&gt;
  - <https://www.sqlite.org/about.html>
- 2 unlabeled field(s): &lt;select name=s&gt;, &lt;input type=text name=q&gt;
  - <https://www.sqlite.org/34to35.html>
- 2 unlabeled field(s): &lt;select name=s&gt;, &lt;input type=text name=q&gt;
  - <https://www.sqlite.org/35to36.html>

**What to do:** Give every form field a visible label tied to it

**Suggested roles:** developer, seo

1. Add &lt;label for="field-id"&gt; with visible text for each field, or wrap the field in &lt;label&gt;
2. Use aria-label only where a visible label is impossible; a placeholder is not a label

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: Pages omit an explicit document language

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.95; Check: `missing-language`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.95; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing document language can impede assistive pronunciation and language interpretation.

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- The html lang attribute is absent or empty.
  - <https://www.sqlite.org/docs.html>
- The html lang attribute is absent or empty.
  - <https://www.sqlite.org/about.html>
- The html lang attribute is absent or empty.
  - <https://sqlite.org/android/>
- The html lang attribute is absent or empty.
  - <https://sqlite.org/sqlar/>
- The html lang attribute is absent or empty.
  - <https://www.sqlite.org/34to35.html>
- and 1 more observations in the JSON report

**What to do:** Set an accurate BCP 47 lang attribute on the html element; verify multilingual sections separately.

**Suggested roles:** developer, seo

1. Set an accurate BCP 47 lang attribute on the html element; verify multilingual sections separately.

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Gives consumers an explicit language hint.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-003: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 6 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 6 of 183 discovered pages that were actually crawled)

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- 0/6 pages contain JSON-LD
  - <https://www.sqlite.org/docs.html>
  - <https://www.sqlite.org/about.html>
  - <https://sqlite.org/android/>
  - <https://sqlite.org/sqlar/>
  - <https://www.sqlite.org/34to35.html>
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
<!-- Home page https://www.sqlite.org/docs.html -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.sqlite.org/#organization",
      "name": "SQLite Documentation",
      "url": "https://www.sqlite.org/",
      "logo": "REPLACE_WITH_LOGO_URL",
      "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION"
    },
    {
      "@type": "WebSite",
      "@id": "https://www.sqlite.org/#website",
      "name": "SQLite Documentation",
      "url": "https://www.sqlite.org/",
      "publisher": {
        "@id": "https://www.sqlite.org/#organization"
      }
    }
  ]
}
</script>

<!-- Other page https://sqlite.org/android/doc/trunk/www/index.wiki -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://sqlite.org/android/doc/trunk/www/index.wiki",
  "name": "SQLite Android Bindings",
  "description": "REPLACE_WITH_PAGE_DESCRIPTION",
  "about": {
    "@id": "https://www.sqlite.org/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_LOGO_URL`, `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`, `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-004: No meta description on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.sqlite.org/docs.html>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.sqlite.org/about.html>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://sqlite.org/android/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://sqlite.org/sqlar/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.sqlite.org/34to35.html>
- and 1 more observations in the JSON report

**What to do:** Write a concise page-specific meta description that matches visible content.

**Suggested roles:** developer, seo

1. Write a concise page-specific meta description that matches visible content.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides a summary candidate; search engines may choose other text.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-005: Open Graph tags missing: og:description on 6/6 sampled pages, og:image on 6/6 sampled pages, og:title on 6/6 sampled pages, og:url on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.sqlite.org/docs.html>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.sqlite.org/about.html>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://sqlite.org/android/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://sqlite.org/sqlar/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.sqlite.org/34to35.html>
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
<!-- https://sqlite.org/android/doc/trunk/www/index.wiki -->
<meta property="og:title" content="SQLite Android Bindings: Documentation">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">
<meta property="og:url" content="https://sqlite.org/android/doc/trunk/www/index.wiki">

<!-- https://sqlite.org/sqlar/doc/trunk/README.md -->
<meta property="og:title" content="SQLite Archiver: Documentation">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">
<meta property="og:url" content="https://sqlite.org/sqlar/doc/trunk/README.md">

<!-- https://www.sqlite.org/34to35.html -->
<meta property="og:title" content="SQLite Changes From Version 3.4.2 To 3.5.0">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="REPLACE_WITH_SHARE_IMAGE_URL">
<meta property="og:url" content="https://www.sqlite.org/34to35.html">
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`, `REPLACE_WITH_SHARE_IMAGE_URL`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-006: Likely Largest Contentful Paint (LCP) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Markup patterns that delay the largest paint were observed: the main content may appear slowly

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>

**Evidence:**

- Estimate, not a measurement: the HTML took 3974 ms to arrive
  - <https://sqlite.org/android/>
- Estimate, not a measurement: the HTML took 3256 ms to arrive
  - <https://sqlite.org/sqlar/>

**What to do:** Check LCP in a browser or with field data, and remove the listed patterns

**Suggested roles:** developer, seo

1. Do not lazy-load the first large image; give it fetchpriority="high" or preload it
2. Defer or async non-critical scripts and inline only critical CSS
3. Reduce server response time with caching
4. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Largest Contentful Paint score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-007: Title shorter than 15 or longer than 70 characters on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://www.sqlite.org/about.html>

**Evidence:**

- Title has 12 characters: About SQLite. Display width was not measured.
  - <https://www.sqlite.org/about.html>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: Dense paragraphs may obscure key answers

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `long-paragraphs`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** More than 40% of paragraphs exceed 600 characters on substantial pages.

**Pages:**

- <https://sqlite.org/android/>

**Evidence:**

- More than 40% of paragraphs exceed 600 characters on substantial pages.
  - <https://sqlite.org/android/>

**What to do:** Review dense passages and split by topic

**Suggested roles:** developer, seo

1. Review dense passages and split by topic
2. Use lists or tables where appropriate

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-009: Pages lack a descriptive primary heading (H1) that says what the page is about

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `h1`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No H1 was found on these sampled pages.

**Pages:**

- <https://www.sqlite.org/docs.html>

**Evidence:**

- No H1 was found on these sampled pages.
  - <https://www.sqlite.org/docs.html>
- Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.
  - <https://www.sqlite.org/docs.html>

**What to do:** Add a descriptive primary heading where a clear page title is missing

**Suggested roles:** developer, seo

1. Add a descriptive primary heading where a clear page title is missing

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-010: No main or article landmark on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-landmarks`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Content without a main or article landmark may be harder to distinguish from boilerplate.

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- No main or article landmark observed on a page with substantial text.
  - <https://www.sqlite.org/docs.html>
- No main or article landmark observed on a page with substantial text.
  - <https://www.sqlite.org/about.html>
- No main or article landmark observed on a page with substantial text.
  - <https://sqlite.org/android/>
- No main or article landmark observed on a page with substantial text.
  - <https://sqlite.org/sqlar/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.sqlite.org/34to35.html>
- and 1 more observations in the JSON report

**What to do:** Mark the main content semantically and keep navigation outside it when appropriate.

**Suggested roles:** developer, seo

1. Mark the main content semantically and keep navigation outside it when appropriate.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves structural clarity for supporting readers and extractors.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-011: No rel=canonical tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.sqlite.org/docs.html>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.sqlite.org/about.html>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://sqlite.org/android/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://sqlite.org/sqlar/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.sqlite.org/34to35.html>
- and 1 more observations in the JSON report

**What to do:** Assess real duplicates before declaring the correct absolute canonical URL.

**Suggested roles:** developer, seo

1. Assess real duplicates before declaring the correct absolute canonical URL.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Helps supporting consumers consolidate duplicate URLs when applicable.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://sqlite.org/android/doc/trunk/www/index.wiki -->
<link rel="canonical" href="https://sqlite.org/android/doc/trunk/www/index.wiki">

<!-- https://sqlite.org/sqlar/doc/trunk/README.md -->
<link rel="canonical" href="https://sqlite.org/sqlar/doc/trunk/README.md">

<!-- https://www.sqlite.org/34to35.html -->
<link rel="canonical" href="https://www.sqlite.org/34to35.html">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-012: No valid twitter:card tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://sqlite.org/android/>
- <https://sqlite.org/sqlar/>
- <https://www.sqlite.org/34to35.html>
- <https://www.sqlite.org/35to36.html>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.sqlite.org/docs.html>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.sqlite.org/about.html>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://sqlite.org/android/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://sqlite.org/sqlar/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.sqlite.org/34to35.html>
- and 1 more observations in the JSON report

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://sqlite.org/android/doc/trunk/www/index.wiki -->
<meta name="twitter:card" content="summary">

<!-- https://sqlite.org/sqlar/doc/trunk/README.md -->
<meta name="twitter:card" content="summary">

<!-- https://www.sqlite.org/34to35.html -->
<meta name="twitter:card" content="summary">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-013: No XML sitemap found

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-unavailable`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without a discovered sitemap, this audit relies more heavily on sampled links.

**Pages:**

- <https://www.sqlite.org/docs.html>

**Evidence:**

- Sitemap probe status: absent; checked: https://www.sqlite.org/sitemap.xml (absent). No additional sitemap discovery was attempted by this check.
  - <https://www.sqlite.org/docs.html>

**What to do:** If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

**Suggested roles:** infrastructure, seo

1. If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves inventory discovery; absence is not a universal indexing defect.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-014: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <https://sqlite.org/android/>
- <https://www.sqlite.org/about.html>
- <https://www.sqlite.org/docs.html>

**Evidence:**

- None of the 6 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <https://www.sqlite.org/docs.html>
  - <https://www.sqlite.org/about.html>
  - <https://sqlite.org/android/>

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
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Pages are open to indexing and snippets.** None of the 6 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 4 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
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

- 177 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 183 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 6 of 129 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.

## Notes from the run

- English lexical checks skipped on pages with unknown/non-English language or truncated retained text.
- Entity identity unresolved; corroboration suppressed.
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
