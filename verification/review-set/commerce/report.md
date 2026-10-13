# Brand AI-Readiness Audit: https://www.adafruit.com/

- **Audited at:** 2026-10-13T03:29:06.715222+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 120 discovered; 4 of 23 site sections reached
- **Run time:** 11.9 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 13 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.17)

Confidence is low (0.17). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 120 discovered page(s) and reached 4 of 23 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.17 | The page sample is small or one-sided: the crawl analyzed 6 of 120 discovered page(s) and reached 4 of 23 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
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
| Improvement suggestions (not defects) | 13 |
| Not enough evidence to judge | 0 |
| Recommendations | 14 |

## Start here

**F-001: Sampled content page carries noindex indexing controls**

Review whether noindex is intentional on this page

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Sampled content page carries noindex indexing controls | Review whether noindex is intentional on this page | medium | medium | low | yes | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Sampled content page carries noindex indexing controls.** Review whether noindex is intentional on this page (impact medium, effort low)
- **F-003: Video or audio is embedded without complete VideoObject or AudioObject markup.** Describe each video and audio clip with VideoObject or AudioObject JSON-LD (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Sampled content page carries noindex indexing controls | 1 |
| F-002 | Improvement opportunity | low | confirmed | About pages are missing Organization/AboutPage structured data | 1 |
| F-003 | Improvement opportunity | low | confirmed | Video or audio is embedded without complete VideoObject or AudioObject markup | 3 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 6/6 sampled pages, og:image on 3/6 sampled pages, og:title on 3/6 sampled pages, og:url on 3/6 sampled pages | 6 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 3/6 sampled pages | 3 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 3/6 sampled pages | 3 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 2 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 4/6 sampled pages | 4 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Pages lack a descriptive primary heading (H1) that says what the page is about | 2 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 3 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | No main or article landmark on 6/6 sampled pages | 6 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 6/6 sampled pages | 6 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 6/6 sampled pages | 6 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | No page or link names an audience segment across 6 sampled pages | 1 |

## Finding details

### F-001: Sampled content page carries noindex indexing controls

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `noindex`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The observed noindex directive (meta robots) limits indexing or snippets for this page within that crawler scope; intentional exclusions should be retained.

**Pages:**

- <https://www.adafruit.com/contact_us>

**Evidence:**

- meta robots
  - <https://www.adafruit.com/contact_us>

**What to do:** Review whether noindex is intentional on this page

**Suggested roles:** developer, seo

1. Confirm each page is intended for search discovery
2. Remove the directive only where unintended; preserve private/duplicate-page controls

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Restores eligibility within the affected crawler scope, without guaranteeing citations

**How to check the fix:** Refetch HTML and headers and confirm the intended noindex policy

### F-002: About pages are missing Organization/AboutPage structured data

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.90; Check: `page-type-schema-gap:about`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.9; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** 1 page(s) classified as 'about' carry no Organization/AboutPage JSON-LD, so explicit machine-readable context may be improved

**Pages:**

- <https://www.adafruit.com/about>

**Evidence:**

- 1 'about' page(s) missing Organization/AboutPage markup
  - <https://www.adafruit.com/about>

**What to do:** Add Organization/AboutPage JSON-LD to about pages

**Suggested roles:** content, developer, seo

1. Add Organization/AboutPage schema.org JSON-LD matching each about page's content
2. Validate with a schema.org/Rich Results validator

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** About facts are also stated as explicit structured data; no ranking, rich-result or citation gain is implied

**How to check the fix:** Re-crawl and confirm the expected @type is present

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.adafruit.com/about -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://www.adafruit.com/about",
  "name": "Products navigation",
  "description": "REPLACE_WITH_PAGE_DESCRIPTION",
  "about": {
    "@id": "https://www.adafruit.com/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-003: Video or audio is embedded without complete VideoObject or AudioObject markup

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `media-schema-missing`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without VideoObject or AudioObject markup, search engines and assistants have no machine-readable title, description, thumbnail or date for the media

**Pages:**

- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- video with no VideoObject markup
  - <https://www.adafruit.com/product/6333>
- video with no VideoObject markup
  - <https://www.adafruit.com/product/6353>
- video with no VideoObject markup
  - <https://www.adafruit.com/product/6354>

**What to do:** Describe each video and audio clip with VideoObject or AudioObject JSON-LD

**Suggested roles:** developer, seo

1. Add VideoObject markup with name, description, thumbnailUrl, uploadDate and duration
2. Use AudioObject or PodcastEpisode markup for audio
3. Add the transcript property where a transcript exists

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Media becomes eligible for video results and its details are quotable

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-004: Open Graph tags missing: og:description on 6/6 sampled pages, og:image on 3/6 sampled pages, og:title on 3/6 sampled pages, og:url on 3/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>
- <https://www.adafruit.com/contact_us>
- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.adafruit.com/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.adafruit.com/about>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.adafruit.com/contact_us>
- Missing nonempty fields: og:description
  - <https://www.adafruit.com/product/6333>
- Missing nonempty fields: og:description
  - <https://www.adafruit.com/product/6353>
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
<!-- https://www.adafruit.com/ -->
<meta property="og:title" content="Adafruit Industries, Unique &amp; fun DIY electronics and kits">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="https://cdn-shop.adafruit.com/310x233/6526-00.jpg">
<meta property="og:url" content="https://www.adafruit.com/">

<!-- https://www.adafruit.com/about -->
<meta property="og:title" content="About : Adafruit Industries, Unique &amp; fun DIY electronics and kits">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="https://www.adafruit.com/includes/templates/shop2019/images/about/bbb-seal.png">
<meta property="og:url" content="https://www.adafruit.com/about">

<!-- https://www.adafruit.com/contact_us -->
<meta property="og:title" content="Contact Us : Adafruit Industries, Unique &amp; fun DIY electronics and kits">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="https://cdn-shop.adafruit.com/static/apple-touch-icon-57x57.png">
<meta property="og:url" content="https://www.adafruit.com/contact_us">
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-005: Heading levels are skipped on 3/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- Observed heading levels: \[2, 3, 3, 3, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 1, 4\]
  - <https://www.adafruit.com/product/6333>
- Observed heading levels: \[2, 3, 3, 3, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.adafruit.com/product/6353>
- Observed heading levels: \[2, 3, 3, 3, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.adafruit.com/product/6354>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-006: No meta description on 3/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>
- <https://www.adafruit.com/contact_us>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.adafruit.com/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.adafruit.com/about>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.adafruit.com/contact_us>

**What to do:** Write a concise page-specific meta description that matches visible content.

**Suggested roles:** developer, seo

1. Write a concise page-specific meta description that matches visible content.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides a summary candidate; search engines may choose other text.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-007: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>

**Evidence:**

- First content image https://cdn-shop.adafruit.com/310x233/6526-00.jpg has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.adafruit.com/>
- First content image https://www.adafruit.com/includes/templates/shop2019/images/about/bbb-seal.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.adafruit.com/about>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-008: Title shorter than 15 or longer than 70 characters on 4/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 4 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://www.adafruit.com/contact_us>
- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- Title has 71 characters: Contact Us : Adafruit Industries, Unique &amp; fun DIY electronics and kits. Display width was not measured.
  - <https://www.adafruit.com/contact_us>
- Title has 106 characters: Adafruit Sparkle Motion Stick + Enclosure Kit : Adafruit Industries, Unique &amp; fun DIY electronics an. Display width was not measured.
  - <https://www.adafruit.com/product/6333>
- Title has 115 characters: Adafruit STSPIN220 Stepper Motor Driver Breakout Board : Adafruit Industries, Unique &amp; fun DIY elect. Display width was not measured.
  - <https://www.adafruit.com/product/6353>
- Title has 120 characters: Adafruit TPS61169 Constant Current Boost Converter for LEDs : Adafruit Industries, Unique &amp; fun DIY . Display width was not measured.
  - <https://www.adafruit.com/product/6354>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-009: Pages lack a descriptive primary heading (H1) that says what the page is about

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `h1`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No H1 was found on these sampled pages.

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>

**Evidence:**

- No H1 was found on these sampled pages.
  - <https://www.adafruit.com/>
  - <https://www.adafruit.com/about>
- Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.
  - <https://www.adafruit.com/about>

**What to do:** Add a descriptive primary heading where a clear page title is missing

**Suggested roles:** developer, seo

1. Add a descriptive primary heading where a clear page title is missing

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-010: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- Visible breadcrumb without schema
  - <https://www.adafruit.com/product/6333>
  - <https://www.adafruit.com/product/6353>
  - <https://www.adafruit.com/product/6354>

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-011: No main or article landmark on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-landmarks`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Content without a main or article landmark may be harder to distinguish from boilerplate.

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>
- <https://www.adafruit.com/contact_us>
- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- No main or article landmark observed on a page with substantial text.
  - <https://www.adafruit.com/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.adafruit.com/about>
- No main or article landmark observed on a page with substantial text.
  - <https://www.adafruit.com/contact_us>
- No main or article landmark observed on a page with substantial text.
  - <https://www.adafruit.com/product/6333>
- No main or article landmark observed on a page with substantial text.
  - <https://www.adafruit.com/product/6353>
- and 1 more observations in the JSON report

**What to do:** Mark the main content semantically and keep navigation outside it when appropriate.

**Suggested roles:** developer, seo

1. Mark the main content semantically and keep navigation outside it when appropriate.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves structural clarity for supporting readers and extractors.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-012: No rel=canonical tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>
- <https://www.adafruit.com/contact_us>
- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.adafruit.com/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.adafruit.com/about>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.adafruit.com/contact_us>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.adafruit.com/product/6333>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.adafruit.com/product/6353>
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
<!-- https://www.adafruit.com/ -->
<link rel="canonical" href="https://www.adafruit.com/">

<!-- https://www.adafruit.com/about -->
<link rel="canonical" href="https://www.adafruit.com/about">

<!-- https://www.adafruit.com/contact_us -->
<link rel="canonical" href="https://www.adafruit.com/contact_us">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-013: No valid twitter:card tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.adafruit.com/>
- <https://www.adafruit.com/about>
- <https://www.adafruit.com/contact_us>
- <https://www.adafruit.com/product/6333>
- <https://www.adafruit.com/product/6353>
- <https://www.adafruit.com/product/6354>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.adafruit.com/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.adafruit.com/about>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.adafruit.com/contact_us>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.adafruit.com/product/6333>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.adafruit.com/product/6353>
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
<!-- https://www.adafruit.com/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.adafruit.com/about -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.adafruit.com/contact_us -->
<meta name="twitter:card" content="summary">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-014: No page or link names an audience segment across 6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.50; Check: `audience-segment-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.5; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants weight answers toward the asker's stated role or need; a site with no page for a named audience gives them nothing to match "for small businesses" or "for students" to

**Pages:**

- <https://www.adafruit.com/>

**Evidence:**

- Checked 6 page titles and headings and 405 internal links; none names an audience ("for teams", /industries/, /use-cases/)
  - <https://www.adafruit.com/>

**What to do:** Publish one page per main audience and link it from the navigation

**Suggested roles:** content, developer, seo

1. List the two to four audiences the offer serves best
2. Give each a page that states the audience in its title and H1, with the use cases, proof and pricing that matter to it
3. Link those pages from the main navigation and the home page

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Assistants can match the brand to questions that state who is asking

**How to check the fix:** Re-run the audit and confirm audience pages are detected

## Other recommendations

Good practice to keep, beyond the findings above:

- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Structured data parses cleanly.** JSON-LD structured data is on 6 of the 6 pages checked, and every block parsed.
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 194 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
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

- 114 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 120 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 4 of 23 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Linked sameAs and review profiles were not fetched (OFF\_SITE\_LOOKUP=0), so whether they resolve and belong to the brand was not checked.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 13 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.
- sitemap.xml could not be checked (status: 'blocked'); crawl coverage may be incomplete relative to a site that publishes one.

## Notes from the run

- No dated facts found; freshness cannot be assessed (absence is not proof of staleness).
- Entity identity unresolved; corroboration suppressed.
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Off-site profile lookup disabled (OFF\_SITE\_LOOKUP=0); linked profiles were not fetched or verified.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
