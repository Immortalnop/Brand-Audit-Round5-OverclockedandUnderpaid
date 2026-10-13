# Brand AI-Readiness Audit: https://www.donorschoose.org/

- **Audited at:** 2026-10-13T03:30:08.121257+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 52 discovered; 2 of 25 site sections reached
- **Run time:** 16.0 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 13 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.12)

Confidence is low (0.12). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 52 discovered page(s) and reached 2 of 25 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.12 | The page sample is small or one-sided: the crawl analyzed 6 of 52 discovered page(s) and reached 2 of 25 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.60 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 13 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 12 |
| Improvement suggestions (not defects) | 11 |
| Not enough evidence to judge | 0 |
| Recommendations | 12 |

## Start here

**F-001: Links or buttons have no accessible name**

Name every icon-only link and button

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Links or buttons have no accessible name | Name every icon-only link and button | medium | medium | low | yes | developer, seo |
| 2 | F-003: Data tables have no header cells on 1/6 sampled pages | Mark the header row and header column of each data table with &lt;th&gt; | low | low | low | no | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Links or buttons have no accessible name.** Name every icon-only link and button (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Links or buttons have no accessible name | 6 |
| F-002 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 6 |
| F-003 | Defect | low | confirmed | Data tables have no header cells on 1/6 sampled pages | 1 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 6/6 sampled pages | 6 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 5/6 sampled pages, og:image on 5/6 sampled pages, og:title on 5/6 sampled pages, og:url on 5/6 sampled pages | 5 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 1/6 sampled pages but stated in no structured data | 1 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Images have no text alternative: no alt text, caption or link text says what they show | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Pages lack a descriptive primary heading (H1) that says what the page is about | 1 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | No main or article landmark on 6/6 sampled pages | 6 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 6/6 sampled pages | 6 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 5/6 sampled pages | 5 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | Most images have no width and height on 1/6 sampled pages | 1 |

## Finding details

### F-001: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://www.donorschoose.org/>
- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- 2 unnamed control(s): &lt;a href=https://secure.donorschoose.org/donors/givingCart.html&gt; with only an icon, &lt;a href=https://secure.donorschoose.org/common/myaccount.html&gt; with only an icon
  - <https://www.donorschoose.org/>
- 2 unnamed control(s): &lt;a href=https://secure.donorschoose.org/donors/givingCart.html&gt; with only an icon, &lt;a href=https://secure.donorschoose.org/common/myaccount.html&gt; with only an icon
  - <https://www.donorschoose.org/about>
- 2 unnamed control(s): &lt;a href=https://secure.donorschoose.org/donors/givingCart.html&gt; with only an icon, &lt;a href=https://secure.donorschoose.org/common/myaccount.html&gt; with only an icon
  - <https://www.donorschoose.org/about/accessibility.html>
- 2 unnamed control(s): &lt;a href=https://secure.donorschoose.org/donors/givingCart.html&gt; with only an icon, &lt;a href=https://secure.donorschoose.org/common/myaccount.html&gt; with only an icon
  - <https://www.donorschoose.org/about/finance.html>
- 2 unnamed control(s): &lt;a href=https://secure.donorschoose.org/donors/givingCart.html&gt; with only an icon, &lt;a href=https://secure.donorschoose.org/common/myaccount.html&gt; with only an icon
  - <https://www.donorschoose.org/about/impact.html>
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

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 6 of 52 discovered pages that were actually crawled)

**Pages:**

- <https://www.donorschoose.org/>
- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- 0/6 pages contain JSON-LD
  - <https://www.donorschoose.org/>
  - <https://www.donorschoose.org/about>
  - <https://www.donorschoose.org/about/accessibility.html>
  - <https://www.donorschoose.org/about/finance.html>
  - <https://www.donorschoose.org/about/impact.html>
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
<!-- Home page https://www.donorschoose.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.donorschoose.org/#organization",
      "name": "DonorsChoose",
      "url": "https://www.donorschoose.org/",
      "logo": "https://www.donorschoose.org/apple-touch-icon.png?v=wAdEE3G333",
      "description": "DonorsChoose connects teachers in high-need communities with donors who want to help.",
      "sameAs": [
        "https://instagram.com/donorschoose",
        "https://www.linkedin.com/company/donorschoose",
        "https://www.facebook.com/DonorsChoose",
        "https://www.tiktok.com/@donorschoose"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.donorschoose.org/#website",
      "name": "DonorsChoose",
      "url": "https://www.donorschoose.org/",
      "publisher": {
        "@id": "https://www.donorschoose.org/#organization"
      }
    }
  ]
}
</script>

<!-- About page https://www.donorschoose.org/about -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://www.donorschoose.org/about",
  "name": "Partner with us",
  "description": "DonorsChoose is an online charity on a mission to make it easy for anyone to help a classroom in need by allowing people to donate directly to classrooms.",
  "about": {
    "@id": "https://www.donorschoose.org/#organization"
  }
}
</script>
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-003: Data tables have no header cells on 1/6 sampled pages

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `table-headers-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A parser maps each table value to its meaning through &lt;th&gt; header cells; a table built only from &lt;td&gt; cells leaves values such as prices or limits without a label

**Pages:**

- <https://www.donorschoose.org/about/finance.html>

**Evidence:**

- 1 data table(s) without &lt;th&gt;: 12 rows x 2 columns
  - <https://www.donorschoose.org/about/finance.html>

**What to do:** Mark the header row and header column of each data table with &lt;th&gt;

**Suggested roles:** developer, seo

1. Change the first row's cells to &lt;th scope="col"&gt; and any row labels to &lt;th scope="row"&gt;
2. Add a &lt;caption&gt; that says what the table compares
3. Keep layout tables out of content, or mark them role="presentation"

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Assistants can lift a complete, correctly labelled answer from the page

**How to check the fix:** Re-run the audit and confirm the listed passages are reported as answerable

### F-004: Heading levels are skipped on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.donorschoose.org/>
- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2\]
  - <https://www.donorschoose.org/>
- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 3, 2\]
  - <https://www.donorschoose.org/about>
- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 5, 5, 5, 5, 5\]
  - <https://www.donorschoose.org/about/accessibility.html>
- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3\]
  - <https://www.donorschoose.org/about/finance.html>
- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 2, 3\]
  - <https://www.donorschoose.org/about/impact.html>
- and 1 more observations in the JSON report

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-005: Open Graph tags missing: og:description on 5/6 sampled pages, og:image on 5/6 sampled pages, og:title on 5/6 sampled pages, og:url on 5/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.donorschoose.org/about>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.donorschoose.org/about/accessibility.html>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.donorschoose.org/about/finance.html>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.donorschoose.org/about/impact.html>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.donorschoose.org/about/media.html>

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

**Suggested roles:** developer, seo

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.donorschoose.org/about -->
<meta property="og:title" content="About us | DonorsChoose">
<meta property="og:description" content="DonorsChoose is an online charity on a mission to make it easy for anyone to help a classroom in need by allowing people to donate directly to classrooms.">
<meta property="og:image" content="https://www.donorschoose.org/apple-touch-icon.png?v=wAdEE3G333">
<meta property="og:url" content="https://www.donorschoose.org/about">

<!-- https://www.donorschoose.org/about/accessibility.html -->
<meta property="og:title" content="Accessibility | DonorsChoose">
<meta property="og:description" content="DonorsChoose is committed to making our website accessible to teachers and donors in the U.S., regardless of technology or ability.">
<meta property="og:image" content="https://www.donorschoose.org/apple-touch-icon.png?v=wAdEE3G333">
<meta property="og:url" content="https://www.donorschoose.org/about/accessibility.html">

<!-- https://www.donorschoose.org/about/finance.html -->
<meta property="og:title" content="Financials | DonorsChoose">
<meta property="og:description" content="Financial and legal information about DonorsChoose, online school donations, and supporting teachers.">
<meta property="og:image" content="https://www.donorschoose.org/apple-touch-icon.png?v=wAdEE3G333">
<meta property="og:url" content="https://www.donorschoose.org/about/finance.html">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-006: Email or phone shown on 1/6 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- email: media@donorschoose.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.donorschoose.org/about/media.html>

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
<!-- https://www.donorschoose.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.donorschoose.org/#organization",
  "name": "DonorsChoose",
  "url": "https://www.donorschoose.org/",
  "logo": "https://www.donorschoose.org/apple-touch-icon.png?v=wAdEE3G333",
  "description": "DonorsChoose connects teachers in high-need communities with donors who want to help.",
  "sameAs": [
    "https://instagram.com/donorschoose",
    "https://www.linkedin.com/company/donorschoose",
    "https://www.facebook.com/DonorsChoose",
    "https://www.tiktok.com/@donorschoose"
  ],
  "email": "media@donorschoose.org",
  "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "media@donorschoose.org",
      "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`, `REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://www.donorschoose.org/about/impact.html>

**Evidence:**

- First content image https://secure.donorschoose.org/images/impact/projects.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.donorschoose.org/about/impact.html>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-008: Images have no text alternative: no alt text, caption or link text says what they show

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `missing-alt`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.

**Pages:**

- <https://www.donorschoose.org/about/impact.html>

**Evidence:**

- At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.
  - <https://www.donorschoose.org/about/impact.html>
- 13 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://secure.donorschoose.org/images/impact/projects.png, https://secure.donorschoose.org/images/impact/teachers.png, https://secure.donorschoose.org/images/impact/heart.png
  - <https://www.donorschoose.org/about/impact.html>

**What to do:** Describe informative images and keep decorative alt text empty

**Suggested roles:** developer, seo

1. Describe informative images and keep decorative alt text empty
2. Repeat essential image-only facts in nearby text

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-009: Pages lack a descriptive primary heading (H1) that says what the page is about

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `h1`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No H1 was found on these sampled pages.

**Pages:**

- <https://www.donorschoose.org/about/impact.html>

**Evidence:**

- No H1 was found on these sampled pages.
  - <https://www.donorschoose.org/about/impact.html>
- Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.
  - <https://www.donorschoose.org/about/impact.html>

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

- <https://www.donorschoose.org/>
- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- No main or article landmark observed on a page with substantial text.
  - <https://www.donorschoose.org/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.donorschoose.org/about>
- No main or article landmark observed on a page with substantial text.
  - <https://www.donorschoose.org/about/accessibility.html>
- No main or article landmark observed on a page with substantial text.
  - <https://www.donorschoose.org/about/finance.html>
- No main or article landmark observed on a page with substantial text.
  - <https://www.donorschoose.org/about/impact.html>
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

- <https://www.donorschoose.org/>
- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.donorschoose.org/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.donorschoose.org/about>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.donorschoose.org/about/accessibility.html>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.donorschoose.org/about/finance.html>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.donorschoose.org/about/impact.html>
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
<!-- https://www.donorschoose.org/ -->
<link rel="canonical" href="https://www.donorschoose.org/">

<!-- https://www.donorschoose.org/about -->
<link rel="canonical" href="https://www.donorschoose.org/about">

<!-- https://www.donorschoose.org/about/accessibility.html -->
<link rel="canonical" href="https://www.donorschoose.org/about/accessibility.html">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-012: No valid twitter:card tag on 5/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.donorschoose.org/about>
- <https://www.donorschoose.org/about/accessibility.html>
- <https://www.donorschoose.org/about/finance.html>
- <https://www.donorschoose.org/about/impact.html>
- <https://www.donorschoose.org/about/media.html>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.donorschoose.org/about>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.donorschoose.org/about/accessibility.html>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.donorschoose.org/about/finance.html>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.donorschoose.org/about/impact.html>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.donorschoose.org/about/media.html>

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.donorschoose.org/about -->
<meta name="twitter:card" content="summary">

<!-- https://www.donorschoose.org/about/accessibility.html -->
<meta name="twitter:card" content="summary">

<!-- https://www.donorschoose.org/about/finance.html -->
<meta name="twitter:card" content="summary">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-013: Most images have no width and height on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `image-sizing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Images without dimensions may lack reserved space unless CSS already supplies it.

**Pages:**

- <https://www.donorschoose.org/about/impact.html>

**Evidence:**

- 13/13 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://www.donorschoose.org/about/impact.html>

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
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page has a meta description.** All 6 pages checked have a meta description.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 6 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
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

- 46 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 52 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 2 of 25 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.

## Notes from the run

- No dated facts found; freshness cannot be assessed (absence is not proof of staleness).
- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
