# Brand AI-Readiness Audit: https://www.python.org/

- **Audited at:** 2026-10-13T13:10:12.463114+00:00
- **Run:** Completed
- **Pages:** 49 analyzed of 897 discovered; 12 of 19 site sections reached
- **Run time:** 39.1 seconds
- **Time limits:** audit worker stopped at 270 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 64 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** medium (0.63)

Confidence is medium (0.63). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 49 of 897 discovered page(s) and reached 12 of 19 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.63 | The page sample is small or one-sided: the crawl analyzed 49 of 897 discovered page(s) and reached 12 of 19 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.60 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 19 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 18 |
| Improvement suggestions (not defects) | 16 |
| Not enough evidence to judge | 0 |
| Recommendations | 17 |

## Start here

**F-001: Form fields have no label**

Give every form field a visible label tied to it

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Form fields have no label | Give every form field a visible label tied to it | medium | medium | low | yes | developer, seo |
| 2 | F-003: Image alt text is a file name, placeholder or repeated label that describes nothing | Replace placeholder alt text with a short description of each image | low | low | low | no | developer, seo |
| 3 | F-004: Links or buttons have no accessible name | Name every icon-only link and button | low | low | low | no | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Form fields have no label.** Give every form field a visible label tied to it (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Form fields have no label | 5 |
| F-002 | Improvement opportunity | low | confirmed | About pages are missing Organization/AboutPage structured data | 6 |
| F-003 | Defect | low | confirmed | Image alt text is a file name, placeholder or repeated label that describes nothing | 1 |
| F-004 | Defect | low | confirmed | Links or buttons have no accessible name | 1 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 23/49 sampled pages | 23 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 8/49 sampled pages but stated in no structured data | 8 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 1/49 sampled pages | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Pages lack a descriptive primary heading (H1) that says what the page is about | 6 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Different sampled URLs share page titles | 5 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 25 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 49/49 sampled pages | 49 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 49/49 sampled pages | 49 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | No main or article landmark on 13/49 sampled pages | 13 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | Content images have no alt text, caption or other text saying what they show | 1 |
| F-015 | Improvement opportunity | low | suspected (likely, not proven) | Most images have no width and height on 1/49 sampled pages | 1 |
| F-016 | Improvement opportunity | low | suspected (likely, not proven) | No XML sitemap found | 1 |
| F-017 | Improvement opportunity | low | suspected (likely, not proven) | One word makes up more than 6% of the text on 1/46 sampled pages | 1 |
| F-018 | Improvement opportunity | low | suspected (likely, not proven) | HTML response larger than 400 KB on 1/49 sampled pages | 1 |
| F-019 | Improvement opportunity | low | suspected (likely, not proven) | Physical location is shown on the page but stated in no structured data | 1 |

## Finding details

### F-001: Form fields have no label

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `form-label-missing`; Seen on 5 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A field with no label, aria-label or title has no name in the accessibility tree, so screen-reader users and AI agents filling the form cannot tell what it asks for

**Pages:**

- <https://www.python.org/events/python-events/2169/>
- <https://www.python.org/events/python-events/2183/>
- <https://www.python.org/events/python-events/2189/>
- <https://www.python.org/events/python-events/2203/>
- <https://www.python.org/events/python-events/2211/>

**Evidence:**

- 1 unlabeled field(s): &lt;select name=dataRangeSelect&gt;
  - <https://www.python.org/events/python-events/2169/>
- 1 unlabeled field(s): &lt;select name=dataRangeSelect&gt;
  - <https://www.python.org/events/python-events/2183/>
- 1 unlabeled field(s): &lt;select name=dataRangeSelect&gt;
  - <https://www.python.org/events/python-events/2189/>
- 1 unlabeled field(s): &lt;select name=dataRangeSelect&gt;
  - <https://www.python.org/events/python-events/2203/>
- 1 unlabeled field(s): &lt;select name=dataRangeSelect&gt;
  - <https://www.python.org/events/python-events/2211/>

**What to do:** Give every form field a visible label tied to it

**Suggested roles:** developer, seo

1. Add &lt;label for="field-id"&gt; with visible text for each field, or wrap the field in &lt;label&gt;
2. Use aria-label only where a visible label is impossible; a placeholder is not a label

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: About pages are missing Organization/AboutPage structured data

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.90; Check: `page-type-schema-gap:about`; Seen on 6 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.9; 6 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** 6 page(s) classified as 'about' carry no Organization/AboutPage JSON-LD, so explicit machine-readable context may be improved

**Pages:**

- <https://www.python.org/about/>
- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>
- <https://www.python.org/about/quotes/>

**Evidence:**

- 6 'about' page(s) missing Organization/AboutPage markup
  - <https://www.python.org/about/>
  - <https://www.python.org/about/apps>
  - <https://www.python.org/about/gettingstarted/>
  - <https://www.python.org/about/help/>
  - <https://www.python.org/about/legal/>
  - and 1 more

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
<!-- https://www.python.org/about/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://www.python.org/about/",
  "name": "Python is powerful... and fast; plays well with others; runs everywhere; is friendly & easy to learn; is Open.",
  "description": "The official home of the Python Programming Language",
  "about": {
    "@id": "https://www.python.org/#organization"
  }
}
</script>
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-003: Image alt text is a file name, placeholder or repeated label that describes nothing

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `alt-text-quality`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Alt text such as a file name or a word like 'banner' gives crawlers, assistants and screen readers no description of the image

**Pages:**

- <https://www.python.org/community/logos/>

**Evidence:**

- 2 image(s) with uninformative alt text, for example alt="/static/community\_logos/python-powered-w-100x40.png" (a file name) on https://www.python.org/static/community\_logos/python-powered-w-100x40.png; alt="/static/community\_logos/python-powered-h-50x65.png" (a file name) on https://www.python.org/static/community\_logos/python-powered-h-50x65.png
  - <https://www.python.org/community/logos/>

**What to do:** Replace placeholder alt text with a short description of each image

**Suggested roles:** developer, seo

1. Write alt text that says what each informative image shows, in a short phrase
2. Use an empty alt="" for purely decorative images instead of a placeholder word
3. Fix the CMS or template default that fills alt text with the file name

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Crawlers, assistants and screen readers can tell what each image shows

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-004: Links or buttons have no accessible name

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://www.python.org/about/>

**Evidence:**

- 1 unnamed control(s): &lt;a href=/community/lists&gt; with no content
  - <https://www.python.org/about/>

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-005: Heading levels are skipped on 23/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 23 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 23 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/quotes/>
- <https://www.python.org/community/>
- <https://www.python.org/community/diversity/>
- <https://www.python.org/community/irc/>
- <https://www.python.org/community/lists/>
- <https://www.python.org/community/logos/>
- <https://www.python.org/community/sigs/>
- and 13 more

**Evidence:**

- Observed heading levels: \[1, 1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/apps>
- Observed heading levels: \[1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/gettingstarted/>
- Observed heading levels: \[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/help/>
- Observed heading levels: \[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/quotes/>
- Observed heading levels: \[1, 2, 2, 2, 2, 2, 2, 2, 2, 4\]
  - <https://www.python.org/community/>
- and 5 more observations in the JSON report

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-006: Email or phone shown on 8/49 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 8 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 8 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>
- <https://www.python.org/community/logos/>
- <https://www.python.org/community/sigs/>
- <https://www.python.org/dev/security/>
- <https://www.python.org/jobs/>
- <https://www.python.org/psf/donations/>
- <https://www.python.org/psf/get-involved/>

**Evidence:**

- email: psf@python.org, python-announce@python.org, webmaster@python.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/about/help/>
- email: legal@python.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/about/legal/>
- email: psf-trademarks@python.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/community/logos/>
- email: alexander.belopolsky@gmail.com, andy47@halfcooked.com, andy@robanal.demon.co.uk. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/community/sigs/>
- email: cna@python.org, security-announce@python.org, security@python.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/dev/security/>
- and 3 more observations in the JSON report

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
<!-- https://www.python.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.python.org/#organization",
  "name": "Python.org",
  "url": "https://www.python.org/",
  "logo": "https://www.python.org/static/apple-touch-icon-precomposed.png",
  "description": "The official home of the Python Programming Language",
  "sameAs": [
    "https://www.linkedin.com/company/python-software-foundation/",
    "https://twitter.com/ThePSF",
    "https://en.wikipedia.org/wiki/Tkinter",
    "https://github.com/python/cpython/issues",
    "https://github.com/python/pythondotorg/issues"
  ],
  "email": "psf-trademarks@python.org",
  "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "psf-trademarks@python.org",
      "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`, `REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: Title shorter than 15 or longer than 70 characters on 1/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://www.python.org/psf/donations/>

**Evidence:**

- Title has 96 characters: Support the PSF with a Donation or by becoming a Supporting Member! \| Python Software Foundation. Display width was not measured.
  - <https://www.python.org/psf/donations/>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: Pages lack a descriptive primary heading (H1) that says what the page is about

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `h1`; Seen on 6 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No H1 was found on these sampled pages.

**Pages:**

- <https://www.python.org/events/>
- <https://www.python.org/events/python-events/>
- <https://www.python.org/events/python-events/past/>
- <https://www.python.org/events/python-user-group/>
- <https://www.python.org/events/python-user-group/past/>
- <https://www.python.org/psf/community-stories/>

**Evidence:**

- No H1 was found on these sampled pages.
  - <https://www.python.org/events/>
  - <https://www.python.org/events/python-events/>
  - <https://www.python.org/events/python-events/past/>
  - <https://www.python.org/events/python-user-group/>
  - <https://www.python.org/events/python-user-group/past/>
  - and 1 more
- Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.
  - <https://www.python.org/events/>
  - <https://www.python.org/events/python-events/>
  - <https://www.python.org/events/python-events/past/>
  - <https://www.python.org/events/python-user-group/>
  - <https://www.python.org/events/python-user-group/past/>
  - and 1 more

**What to do:** Add a descriptive primary heading where a clear page title is missing

**Suggested roles:** developer, seo

1. Add a descriptive primary heading where a clear page title is missing

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-009: Different sampled URLs share page titles

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `duplicate-titles`; Seen on 5 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Multiple sampled URLs share the same title; verify canonical duplicates before editing.

**Pages:**

- <https://www.python.org/events/>
- <https://www.python.org/events/python-events/>
- <https://www.python.org/events/python-events/past/>
- <https://www.python.org/events/python-user-group/>
- <https://www.python.org/events/python-user-group/past/>

**Evidence:**

- Multiple sampled URLs share the same title; verify canonical duplicates before editing.
  - <https://www.python.org/events/>
  - <https://www.python.org/events/python-events/>
  - <https://www.python.org/events/python-events/past/>
  - <https://www.python.org/events/python-user-group/>
  - <https://www.python.org/events/python-user-group/past/>

**What to do:** Give distinct content pages descriptive, distinct titles

**Suggested roles:** developer, seo

1. Give distinct content pages descriptive, distinct titles
2. Preserve intentional canonical variants

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-010: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 25 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 25 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/quotes/>
- <https://www.python.org/community/awards>
- <https://www.python.org/community/diversity/>
- <https://www.python.org/community/forums/>
- <https://www.python.org/community/irc/>
- <https://www.python.org/community/lists/>
- <https://www.python.org/community/logos/>
- and 15 more

**Evidence:**

- Visible breadcrumb without schema
  - <https://www.python.org/about/apps>
  - <https://www.python.org/about/gettingstarted/>
  - <https://www.python.org/about/help/>
  - <https://www.python.org/about/quotes/>
  - <https://www.python.org/community/awards>
  - and 5 more

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-011: No rel=canonical tag on 49/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 49 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 49 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <https://www.python.org/>
- <https://www.python.org/about/>
- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>
- <https://www.python.org/about/quotes/>
- <https://www.python.org/blogs/>
- <https://www.python.org/community/>
- <https://www.python.org/community/awards>
- and 39 more

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.python.org/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.python.org/about/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.python.org/about/apps>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.python.org/about/gettingstarted/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://www.python.org/about/help/>
- and 5 more observations in the JSON report

**What to do:** Assess real duplicates before declaring the correct absolute canonical URL.

**Suggested roles:** developer, seo

1. Assess real duplicates before declaring the correct absolute canonical URL.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Helps supporting consumers consolidate duplicate URLs when applicable.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.python.org/ -->
<link rel="canonical" href="https://www.python.org/">

<!-- https://www.python.org/about/ -->
<link rel="canonical" href="https://www.python.org/about/">

<!-- https://www.python.org/about/apps/ -->
<link rel="canonical" href="https://www.python.org/about/apps/">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-012: No valid twitter:card tag on 49/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 49 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 49 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.python.org/>
- <https://www.python.org/about/>
- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>
- <https://www.python.org/about/quotes/>
- <https://www.python.org/blogs/>
- <https://www.python.org/community/>
- <https://www.python.org/community/awards>
- and 39 more

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.python.org/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.python.org/about/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.python.org/about/apps>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.python.org/about/gettingstarted/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.python.org/about/help/>
- and 5 more observations in the JSON report

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.python.org/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.python.org/about/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.python.org/about/apps/ -->
<meta name="twitter:card" content="summary_large_image">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-013: No main or article landmark on 13/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-landmarks`; Seen on 13 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 13 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Content without a main or article landmark may be harder to distinguish from boilerplate.

**Pages:**

- <https://www.python.org/>
- <https://www.python.org/about/>
- <https://www.python.org/blogs/>
- <https://www.python.org/community/>
- <https://www.python.org/doc/>
- <https://www.python.org/downloads/>
- <https://www.python.org/events/>
- <https://www.python.org/events/python-events/>
- <https://www.python.org/events/python-events/past/>
- <https://www.python.org/events/python-user-group/>
- and 3 more

**Evidence:**

- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/about/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/blogs/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/community/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/doc/>
- and 5 more observations in the JSON report

**What to do:** Mark the main content semantically and keep navigation outside it when appropriate.

**Suggested roles:** developer, seo

1. Mark the main content semantically and keep navigation outside it when appropriate.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves structural clarity for supporting readers and extractors.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-014: Content images have no alt text, caption or other text saying what they show

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `image-context-missing`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Text-based crawlers, assistants and screen readers learn what an image shows only from text tied to it; with no alt text, figcaption, title or link text, the image says nothing

**Pages:**

- <https://www.python.org/community/logos/>

**Evidence:**

- 2 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://www.python.org/static/community\_logos/python-powered-w-100x40.png, https://www.python.org/static/community\_logos/python-powered-h-50x65.png
  - <https://www.python.org/community/logos/>

**What to do:** Describe each informative image in its alt text, and caption images that need context

**Suggested roles:** developer, seo

1. Write a short alt text that says what each informative image shows
2. Wrap images that need explanation in &lt;figure&gt; with a &lt;figcaption&gt;
3. Mark purely decorative images with alt=""

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Crawlers, assistants and screen readers can tell what each image shows

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-015: Most images have no width and height on 1/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `image-sizing`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Images without dimensions may lack reserved space unless CSS already supplies it.

**Pages:**

- <https://www.python.org/jobs/>

**Evidence:**

- 19/19 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://www.python.org/jobs/>

**What to do:** Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

**Suggested roles:** developer, seo

1. Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Can reduce layout movement and unnecessary loading; layout shift is not measured.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-016: No XML sitemap found

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-unavailable`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without a discovered sitemap, this audit relies more heavily on sampled links.

**Pages:**

- <https://www.python.org/>

**Evidence:**

- Sitemap probe status: absent; checked: https://www.python.org/sitemap.xml (absent). No additional sitemap discovery was attempted by this check.
  - <https://www.python.org/>

**What to do:** If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

**Suggested roles:** infrastructure, seo

1. If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves inventory discovery; absence is not a universal indexing defect.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-017: One word makes up more than 6% of the text on 1/46 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `term-repetition`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** High observed term repetition can reduce readability but is not proof of spam.

**Pages:**

- <https://www.python.org/jobs/>

**Evidence:**

- Term 'end' occurs 26 times among 383 words of running text. Repetition alone is not proof of spam.
  - <https://www.python.org/jobs/>

**What to do:** Review repetition in context, retaining necessary technical names and avoiding unnatural keyword quotas.

**Suggested roles:** developer, seo

1. Review repetition in context, retaining necessary technical names and avoiding unnatural keyword quotas.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves natural wording when repetition is excessive.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-018: HTML response larger than 400 KB on 1/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `heavy-html`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Large HTML bodies consume the bounded retrieval budget.

**Pages:**

- <https://www.python.org/downloads/windows/>

**Evidence:**

- Retained 590865 HTML body bytes; truncated: False. Asset transfer sizes were not measured.
  - <https://www.python.org/downloads/windows/>

**What to do:** Trim unnecessary inline payloads and paginate only where useful; retain essential content.

**Suggested roles:** developer, seo

1. Trim unnecessary inline payloads and paginate only where useful; retain essential content.

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Reduces bytes required to retrieve the primary document.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-019: Physical location is shown on the page but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `location-markup-missing`; Seen on 1 of 49 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer location-dependent questions from machine-readable addresses, coordinates and service areas; a location shown only as text or a map is easy to miss

**Pages:**

- <https://www.python.org/about/legal/>

**Evidence:**

- address: 9450 SW Gemini Dr., ECM\# 90772, Beaverton, OR 97008. No address, geo or areaServed in any page's JSON-LD
  - <https://www.python.org/about/legal/>

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
<!-- https://www.python.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.python.org/#organization",
  "name": "Python.org",
  "url": "https://www.python.org/",
  "logo": "https://www.python.org/static/apple-touch-icon-precomposed.png",
  "description": "The official home of the Python Programming Language",
  "sameAs": [
    "https://www.linkedin.com/company/python-software-foundation/",
    "https://twitter.com/ThePSF",
    "https://en.wikipedia.org/wiki/Tkinter",
    "https://github.com/python/cpython/issues",
    "https://github.com/python/pythondotorg/issues"
  ],
  "address": "9450 SW Gemini Dr., ECM# 90772, Beaverton, OR 97008",
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

## Other recommendations

Good practice to keep, beyond the findings above:

- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **Pages are served over HTTPS.** All 49 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 49 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 49 pages checked have a document title.
- **Every page has a meta description.** All 49 pages checked have a meta description.
- **Every page declares its language.** All 49 pages checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 49 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Structured data parses cleanly.** JSON-LD structured data is on 49 of the 49 pages checked, and every block parsed.
- **Content is in the raw HTML.** All 49 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Mobile viewport is declared and zoom is allowed.** All 49 pages checked declare a mobile viewport, and none blocks zooming.
- **Every page links onward.** Each of the 49 pages crawled links to at least one other page on the site.

## Agent checks

Received: outcome envelope. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation. |
| AG-02 Independent mentions | not assessed | No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation. |
| AG-03 Independent contradiction | not assessed | No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation. |
| AG-04 Facts drawn inside images | not assessed | No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation. |
| AG-05 Namesake ambiguity | not assessed | No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation. |
| AG-06 Review and profile opportunity | not assessed | No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation. |

## What this audit could not check

- 842 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 897 discovered); findings reflect only the 51 page(s) actually crawled, not the whole site. The sample reached 12 of 19 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- 1 linked PDF(s) were not fetched (robots rules, a cross-origin redirect, the per-audit cap of 3, or remaining budget; see coverage.non\_text\_media.pdf\_outcomes); their contents were not assessed.
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- Agent check AG-01 (About-page concreteness) was not assessed: No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation.
- Agent check AG-02 (Independent mentions) was not assessed: No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation.
- Agent check AG-03 (Independent contradiction) was not assessed: No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation.
- Agent check AG-05 (Namesake ambiguity) was not assessed: No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation.
- Agent check AG-06 (Review and profile opportunity) was not assessed: No complete assessment was persisted before the actual packet deadline. Late host work is retained as a timing limitation.

## Notes from the run

- English lexical checks skipped on pages with unknown/non-English language or truncated retained text.
- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
