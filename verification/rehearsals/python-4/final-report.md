# Brand AI-Readiness Audit: https://www.python.org/

- **Audited at:** 2026-10-13T03:12:42.698940+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 77 discovered; 2 of 15 site sections reached
- **Run time:** 2.8 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 11 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.13)

Confidence is low (0.13). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 77 discovered page(s) and reached 2 of 15 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.13 | The page sample is small or one-sided: the crawl analyzed 6 of 77 discovered page(s) and reached 2 of 15 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.60 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 11 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 10 |
| Improvement suggestions (not defects) | 10 |
| Not enough evidence to judge | 0 |
| Recommendations | 11 |

## Start here

**F-003: Links or buttons have no accessible name**

Name every icon-only link and button

Impact low, effort low. Details are under F-003 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-003: Links or buttons have no accessible name | Name every icon-only link and button | low | low | low | no | developer, seo |

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Improvement opportunity | medium | suspected (likely, not proven) | About-page self-description is not concrete enough to quote | 1 |
| F-002 | Improvement opportunity | low | confirmed | About pages are missing Organization/AboutPage structured data | 5 |
| F-003 | Defect | low | confirmed | Links or buttons have no accessible name | 1 |
| F-004 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 3/6 sampled pages | 3 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 2/6 sampled pages but stated in no structured data | 2 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 3 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 6/6 sampled pages | 6 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 6/6 sampled pages | 6 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | No main or article landmark on 2/6 sampled pages | 2 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | No XML sitemap found | 1 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Physical location is shown on the page but stated in no structured data | 1 |

## Finding details

### F-001: About-page self-description is not concrete enough to quote

Type: Improvement opportunity; Severity: medium; Status: suspected (likely, not proven); Confidence: 0.65; Check: `about-concreteness`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, suspected status, confidence 0.65; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The passage read does not say category, offering: "Notice: This page displays a fallback because interactive scripts did not run. Possible causes include disabled JavaScript or failure to load scripts or stylesheets. Python can be easy to pick up whether you're a first time programmer or you're experienced with other languages. The following pages a"

**Pages:**

- <https://www.python.org/about/>

**Evidence:**

- The passage read does not say category, offering: "Notice: This page displays a fallback because interactive scripts did not run. Possible causes include disabled JavaScript or failure to load scripts or stylesheets. Python can be easy to pick up whether you're a first time programmer or you're experienced with other languages. The following pages a"
- About Python™ \| Python.org (raw\_html\_text)
  - <https://www.python.org/about/>

**What to do:** Rewrite the opening of the About page to name who the organization is, what it sells or does, and in which category.

**Suggested roles:** content, developer, seo

1. State plainly who the organization is in the first two sentences
2. Name the specific product or service and its market or category
3. Keep the wording factual and consistent with Organization markup

Effort: medium; Impact: medium; Major project: real value, plan the work.

**Expected benefit:** Improves identity clarity and independent corroboration

**How to check the fix:** Re-run the agent stage against the evidence packet of a new audit

### F-002: About pages are missing Organization/AboutPage structured data

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.90; Check: `page-type-schema-gap:about`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.9; 5 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** 5 page(s) classified as 'about' carry no Organization/AboutPage JSON-LD, so explicit machine-readable context may be improved

**Pages:**

- <https://www.python.org/about/>
- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>

**Evidence:**

- 5 'about' page(s) missing Organization/AboutPage markup
  - <https://www.python.org/about/>
  - <https://www.python.org/about/apps>
  - <https://www.python.org/about/gettingstarted/>
  - <https://www.python.org/about/help/>
  - <https://www.python.org/about/legal/>

**What to do:** Add Organization/AboutPage JSON-LD to about pages

**Suggested roles:** content, developer, seo

1. Add Organization/AboutPage schema.org JSON-LD matching each about page's content
2. Validate with a schema.org/Rich Results validator

Effort: medium; Impact: medium; Major project: real value, plan the work.

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

### F-003: Links or buttons have no accessible name

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

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

### F-004: Heading levels are skipped on 3/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>

**Evidence:**

- Observed heading levels: \[1, 1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/apps>
- Observed heading levels: \[1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/gettingstarted/>
- Observed heading levels: \[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3\]
  - <https://www.python.org/about/help/>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-005: Email or phone shown on 2/6 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>

**Evidence:**

- email: psf@python.org, python-announce@python.org, webmaster@python.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/about/help/>
- email: legal@python.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.python.org/about/legal/>

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
  "email": "legal@python.org",
  "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "legal@python.org",
      "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`, `REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-006: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>

**Evidence:**

- Visible breadcrumb without schema
  - <https://www.python.org/about/apps>
  - <https://www.python.org/about/gettingstarted/>
  - <https://www.python.org/about/help/>

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-007: No rel=canonical tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <https://www.python.org/>
- <https://www.python.org/about/>
- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>

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
<!-- https://www.python.org/ -->
<link rel="canonical" href="https://www.python.org/">

<!-- https://www.python.org/about/ -->
<link rel="canonical" href="https://www.python.org/about/">

<!-- https://www.python.org/about/apps/ -->
<link rel="canonical" href="https://www.python.org/about/apps/">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-008: No valid twitter:card tag on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.python.org/>
- <https://www.python.org/about/>
- <https://www.python.org/about/apps>
- <https://www.python.org/about/gettingstarted/>
- <https://www.python.org/about/help/>
- <https://www.python.org/about/legal/>

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
<!-- https://www.python.org/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.python.org/about/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.python.org/about/apps/ -->
<meta name="twitter:card" content="summary_large_image">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-009: No main or article landmark on 2/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-landmarks`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Content without a main or article landmark may be harder to distinguish from boilerplate.

**Pages:**

- <https://www.python.org/>
- <https://www.python.org/about/>

**Evidence:**

- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/>
- No main or article landmark observed on a page with substantial text.
  - <https://www.python.org/about/>

**What to do:** Mark the main content semantically and keep navigation outside it when appropriate.

**Suggested roles:** developer, seo

1. Mark the main content semantically and keep navigation outside it when appropriate.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves structural clarity for supporting readers and extractors.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-010: No XML sitemap found

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-unavailable`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

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

### F-011: Physical location is shown on the page but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `location-markup-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

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
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page has a meta description.** All 6 pages checked have a meta description.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 6 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Structured data parses cleanly.** JSON-LD structured data is on 6 of the 6 pages checked, and every block parsed.
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 6 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 6 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
- **Every page links onward.** Each of the 6 pages crawled links to at least one other page on the site.

## Agent checks

Received: outcome envelope. Assessed: 1 of 6 (partial). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | finding reported | The selected acquired raw opening describes who can start with Python but leaves the offering and programming-language category implicit. This scoped review includes the leading fallback notice and makes no full-site claim. |
| AG-02 Independent mentions | not assessed | External search was not performed. |
| AG-03 Independent contradiction | not assessed | External search was not performed. |
| AG-04 Facts drawn inside images | not assessed | No image was viewed; visual facts are unassessed. |
| AG-05 Namesake ambiguity | not assessed | External search was not performed. |
| AG-06 Review and profile opportunity | not assessed | External search was not performed. |

## What this audit could not check

- 70 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 77 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 2 of 15 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- Agent check AG-02 (Independent mentions) was not assessed: External search was not performed.
- Agent check AG-03 (Independent contradiction) was not assessed: External search was not performed.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No image was viewed; visual facts are unassessed.
- Agent check AG-05 (Namesake ambiguity) was not assessed: External search was not performed.
- Agent check AG-06 (Review and profile opportunity) was not assessed: External search was not performed.

## Notes from the run

- No dated facts found; freshness cannot be assessed (absence is not proof of staleness).
- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
