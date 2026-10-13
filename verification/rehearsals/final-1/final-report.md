# Brand AI-Readiness Audit: https://www.djangoproject.com/foundation/

- **Audited at:** 2026-10-13T03:29:00.587922+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 416 discovered; 6 of 20 site sections reached
- **Run time:** 5.8 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 14 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.20)

Confidence is low (0.20). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 416 discovered page(s) and reached 6 of 20 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.20 | The page sample is small or one-sided: the crawl analyzed 6 of 416 discovered page(s) and reached 6 of 20 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.50 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 11 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 10 |
| Improvement suggestions (not defects) | 8 |
| Not enough evidence to judge | 0 |
| Recommendations | 9 |

## Start here

**F-001: Form fields have no label**

Give every form field a visible label tied to it

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Form fields have no label | Give every form field a visible label tied to it | medium | medium | low | yes | developer, seo |
| 2 | F-003: Data tables have no header cells on 1/6 sampled pages | Mark the header row and header column of each data table with &lt;th&gt; | low | low | low | no | developer, seo |
| 3 | F-004: Image alt text is a file name, placeholder or repeated label that describes nothing | Replace placeholder alt text with a short description of each image | low | low | low | no | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Form fields have no label.** Give every form field a visible label tied to it (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Form fields have no label | 1 |
| F-002 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 6 |
| F-003 | Defect | low | confirmed | Data tables have no header cells on 1/6 sampled pages | 1 |
| F-004 | Defect | low | confirmed | Image alt text is a file name, placeholder or repeated label that describes nothing | 1 |
| F-005 | Improvement opportunity | low | confirmed | Sitemap lastmod dates are missing or unreliable | 0 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 5/6 sampled pages | 5 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 2 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 1/6 sampled pages but stated in no structured data | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 1/6 sampled pages | 1 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 6/6 sampled pages | 6 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Most images have no width and height on 2/6 sampled pages | 2 |

## Finding details

### F-001: Form fields have no label

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `form-label-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A field with no label, aria-label or title has no name in the accessibility tree, so screen-reader users and AI agents filling the form cannot tell what it asks for

**Pages:**

- <https://www.djangoproject.com/community/badges/>

**Evidence:**

- 14 unlabeled field(s): &lt;textarea&gt;, &lt;textarea&gt;, &lt;textarea&gt;, &lt;textarea&gt;
  - <https://www.djangoproject.com/community/badges/>

**What to do:** Give every form field a visible label tied to it

**Suggested roles:** developer, seo

1. Add &lt;label for="field-id"&gt; with visible text for each field, or wrap the field in &lt;label&gt;
2. Use aria-label only where a visible label is impossible; a placeholder is not a label

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 6 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 6 of 416 discovered pages that were actually crawled)

**Pages:**

- <https://www.djangoproject.com/accessibility/>
- <https://www.djangoproject.com/community/badges/>
- <https://www.djangoproject.com/foundation/>
- <https://www.djangoproject.com/multidb-changeset/>
- <https://www.djangoproject.com/screencasts/>
- <https://www.djangoproject.com/weblog/2026/oct/08/django-security-reporting-update/>

**Evidence:**

- 0/6 pages contain JSON-LD
  - <https://www.djangoproject.com/foundation/>
  - <https://www.djangoproject.com/weblog/2026/oct/08/django-security-reporting-update/>
  - <https://www.djangoproject.com/accessibility/>
  - <https://www.djangoproject.com/community/badges/>
  - <https://www.djangoproject.com/multidb-changeset/>
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
<!-- Home page https://www.djangoproject.com/foundation/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.djangoproject.com/#organization",
      "name": "Django Project",
      "url": "https://www.djangoproject.com/",
      "logo": "https://static.djangoproject.com/img/icon-touch.e4872c4da341.png",
      "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION",
      "sameAs": [
        "https://github.com/django/django",
        "https://github.com/django/dsf-minutes",
        "https://github.com/django",
        "https://x.com/djangoproject",
        "https://bsky.app/profile/djangoproject.com",
        "https://www.linkedin.com/company/django-software-foundation",
        "https://github.com/sponsors/django"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.djangoproject.com/#website",
      "name": "Django Project",
      "url": "https://www.djangoproject.com/",
      "publisher": {
        "@id": "https://www.djangoproject.com/#organization"
      }
    }
  ]
}
</script>

<!-- Other page https://www.djangoproject.com/accessibility/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://www.djangoproject.com/accessibility/",
  "name": "Django Accessibility Statement",
  "description": "REPLACE_WITH_PAGE_DESCRIPTION",
  "about": {
    "@id": "https://www.djangoproject.com/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`, `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-003: Data tables have no header cells on 1/6 sampled pages

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `table-headers-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A parser maps each table value to its meaning through &lt;th&gt; header cells; a table built only from &lt;td&gt; cells leaves values such as prices or limits without a label

**Pages:**

- <https://www.djangoproject.com/foundation/>

**Evidence:**

- 2 data table(s) without &lt;th&gt;: 13 rows x 8 columns, 12 rows x 8 columns
  - <https://www.djangoproject.com/foundation/>

**What to do:** Mark the header row and header column of each data table with &lt;th&gt;

**Suggested roles:** developer, seo

1. Change the first row's cells to &lt;th scope="col"&gt; and any row labels to &lt;th scope="row"&gt;
2. Add a &lt;caption&gt; that says what the table compares
3. Keep layout tables out of content, or mark them role="presentation"

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Assistants can lift a complete, correctly labelled answer from the page

**How to check the fix:** Re-run the audit and confirm the listed passages are reported as answerable

### F-004: Image alt text is a file name, placeholder or repeated label that describes nothing

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `alt-text-quality`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Alt text such as a file name or a word like 'banner' gives crawlers, assistants and screen readers no description of the image

**Pages:**

- <https://www.djangoproject.com/community/badges/>

**Evidence:**

- 4 image(s) with uninformative alt text, for example alt="a django site." (the same alt text on 6 different images) on https://www.djangoproject.com/m/img/badges/djangosite100x25.gif; alt="a django site." (the same alt text on 6 different images) on https://www.djangoproject.com/m/img/badges/djangosite100x25\_grey.gif; alt="a django site." (the same alt text on 6 different images) on https://www.djangoproject.com/m/img/badges/djangosite80x15.gif
  - <https://www.djangoproject.com/community/badges/>

**What to do:** Replace placeholder alt text with a short description of each image

**Suggested roles:** developer, seo

1. Write alt text that says what each informative image shows, in a short phrase
2. Use an empty alt="" for purely decorative images instead of a placeholder word
3. Fix the CMS or template default that fills alt text with the file name

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Crawlers, assistants and screen readers can tell what each image shows

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-005: Sitemap lastmod dates are missing or unreliable

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `sitemap-lastmod-unreliable`; Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 0 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Sitemap lastmod dates are missing, malformed or not set per page, so crawlers cannot rely on them to recrawl changed pages first

**Evidence:**

- None of the 1020 sitemap URL entries declares &lt;lastmod&gt;

**What to do:** Publish an accurate &lt;lastmod&gt; for every sitemap URL

**Suggested roles:** infrastructure, seo

1. Set lastmod from the date each page's content last changed, not the build time
2. Use W3C Datetime, for example 2026-03-01 or 2026-03-01T09:00:00+00:00
3. Never declare a future date

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Search and AI crawlers recrawl updated pages sooner and keep trusting the dates

**How to check the fix:** Re-run the audit and compare lastmod values with real content changes

### F-006: No meta description on 5/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <https://www.djangoproject.com/accessibility/>
- <https://www.djangoproject.com/community/badges/>
- <https://www.djangoproject.com/foundation/>
- <https://www.djangoproject.com/multidb-changeset/>
- <https://www.djangoproject.com/screencasts/>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.djangoproject.com/foundation/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.djangoproject.com/accessibility/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.djangoproject.com/community/badges/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.djangoproject.com/multidb-changeset/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.djangoproject.com/screencasts/>

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

- <https://www.djangoproject.com/community/badges/>
- <https://www.djangoproject.com/foundation/>

**Evidence:**

- First content image https://media.djangoproject.com/cache/7a/f9/7af9c770dc49465739a82c91a0eb3d51.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.djangoproject.com/foundation/>
- First content image https://www.djangoproject.com/m/img/badges/djangopowered126x54.gif has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.djangoproject.com/community/badges/>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-008: Email or phone shown on 1/6 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://www.djangoproject.com/weblog/2026/oct/08/django-security-reporting-update/>

**Evidence:**

- email: security@djangoproject.com. No email, telephone or contactPoint in any page's structured data
  - <https://www.djangoproject.com/weblog/2026/oct/08/django-security-reporting-update/>

**What to do:** State the main email and phone number in the Organization JSON-LD

**Suggested roles:** content, developer, seo

1. Add email and telephone to the Organization or LocalBusiness markup on the home page
2. Add a contactPoint for each department visitors contact (sales, support, admissions), with its contactType, telephone and email
3. Use the same details as the contact page, written in international format (+country code)

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Assistants can give the brand's own contact details when asked

**How to check the fix:** Validate the markup and confirm it matches the visible contact details

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.djangoproject.com/foundation/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.djangoproject.com/#organization",
  "name": "Django Project",
  "url": "https://www.djangoproject.com/",
  "logo": "https://static.djangoproject.com/img/icon-touch.e4872c4da341.png",
  "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION",
  "sameAs": [
    "https://github.com/django/django",
    "https://github.com/django/dsf-minutes",
    "https://github.com/django",
    "https://x.com/djangoproject",
    "https://bsky.app/profile/djangoproject.com",
    "https://www.linkedin.com/company/django-software-foundation",
    "https://github.com/sponsors/django"
  ],
  "email": "security@djangoproject.com",
  "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "security@djangoproject.com",
      "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`, `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`, `REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-009: Title shorter than 15 or longer than 70 characters on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://www.djangoproject.com/multidb-changeset/>

**Evidence:**

- Title has 13 characters: Code \| Django. Display width was not measured.
  - <https://www.djangoproject.com/multidb-changeset/>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-010: No rel=canonical tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <https://www.djangoproject.com/accessibility/>
- <https://www.djangoproject.com/community/badges/>
- <https://www.djangoproject.com/foundation/>
- <https://www.djangoproject.com/multidb-changeset/>
- <https://www.djangoproject.com/screencasts/>
- <https://www.djangoproject.com/weblog/2026/oct/08/django-security-reporting-update/>

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.djangoproject.com/foundation/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.djangoproject.com/weblog/2026/oct/08/django-security-reporting-update/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.djangoproject.com/accessibility/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.djangoproject.com/community/badges/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.djangoproject.com/multidb-changeset/>
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
<!-- https://www.djangoproject.com/accessibility/ -->
<link rel="canonical" href="https://www.djangoproject.com/accessibility/">

<!-- https://www.djangoproject.com/community/badges/ -->
<link rel="canonical" href="https://www.djangoproject.com/community/badges/">

<!-- https://www.djangoproject.com/foundation/ -->
<link rel="canonical" href="https://www.djangoproject.com/foundation/">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-011: Most images have no width and height on 2/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `image-sizing`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Images without dimensions may lack reserved space unless CSS already supplies it.

**Pages:**

- <https://www.djangoproject.com/community/badges/>
- <https://www.djangoproject.com/foundation/>

**Evidence:**

- 10/10 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://www.djangoproject.com/foundation/>
- 15/15 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://www.djangoproject.com/community/badges/>

**What to do:** Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

**Suggested roles:** developer, seo

1. Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Can reduce layout movement and unnecessary loading; layout shift is not measured.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

## Other recommendations

Good practice to keep, beyond the findings above:

- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **An XML sitemap is available.** An XML sitemap was read; it lists 1020 URLs.
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 6 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 6 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Every page links onward.** Each of the 6 pages crawled links to at least one other page on the site.

## Agent checks

Received: outcome envelope. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The observed About Django target /start/overview/ was not acquired within this six-page sample. The foundation page cannot substitute for this known target. |
| AG-02 Independent mentions | not assessed | External search was not performed. |
| AG-03 Independent contradiction | not assessed | External search was not performed. |
| AG-04 Facts drawn inside images | not assessed | No image was viewed. |
| AG-05 Namesake ambiguity | not assessed | External search was not performed. |
| AG-06 Review and profile opportunity | not assessed | External search was not performed. |

## What this audit could not check

- 410 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 416 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 6 of 20 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 10 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.
- Agent check AG-01 (About-page concreteness) was not assessed: The observed About Django target /start/overview/ was not acquired within this six-page sample. The foundation page cannot substitute for this known target.
- Agent check AG-02 (Independent mentions) was not assessed: External search was not performed.
- Agent check AG-03 (Independent contradiction) was not assessed: External search was not performed.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No image was viewed.
- Agent check AG-05 (Namesake ambiguity) was not assessed: External search was not performed.
- Agent check AG-06 (Review and profile opportunity) was not assessed: External search was not performed.

## Notes from the run

- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
