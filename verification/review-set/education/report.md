# Brand AI-Readiness Audit: https://www.mit.edu/

- **Audited at:** 2026-10-13T03:29:51.821548+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 24 discovered; 6 of 16 site sections reached
- **Run time:** 10.6 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 19 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.25)

Confidence is low (0.25). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 24 discovered page(s) and reached 6 of 16 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.25 | The page sample is small or one-sided: the crawl analyzed 6 of 24 discovered page(s) and reached 6 of 16 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.60 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 15 |
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 12 |
| Improvement suggestions (not defects) | 12 |
| Not enough evidence to judge | 0 |
| Recommendations | 13 |

## Start here

**F-002: Physical location is shown on the page but stated in no structured data**

State the address, coordinates and service area in Organization or LocalBusiness JSON-LD

Impact medium, effort low. Details are under F-002 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Images are heavier than they need to be | Compress, resize and convert the listed images | medium | medium | medium | no | developer, seo |
| 2 | F-002: Physical location is shown on the page but stated in no structured data | State the address, coordinates and service area in Organization or LocalBusiness JSON-LD | medium | medium | low | yes | content, developer, seo |
| 3 | F-003: Links or buttons have no accessible name | Name every icon-only link and button | medium | medium | low | yes | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-002: Physical location is shown on the page but stated in no structured data.** State the address, coordinates and service area in Organization or LocalBusiness JSON-LD (impact medium, effort low)
- **F-003: Links or buttons have no accessible name.** Name every icon-only link and button (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Images are heavier than they need to be | 3 |
| F-002 | Defect | medium | confirmed | Physical location is shown on the page but stated in no structured data | 6 |
| F-003 | Defect | medium | confirmed | Links or buttons have no accessible name | 1 |
| F-004 | Improvement opportunity | low | confirmed | About pages are missing Organization/AboutPage structured data | 1 |
| F-005 | Improvement opportunity | low | confirmed | Contact pages are missing LocalBusiness/Organization/ContactPage structured data | 1 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:image on 6/6 sampled pages, og:description on 5/6 sampled pages, og:title on 5/6 sampled pages, og:url on 5/6 sampled pages | 6 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 4/6 sampled pages | 4 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 3 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Likely Cumulative Layout Shift (CLS) risk, estimated from markup and not measured | 2 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 1/6 sampled pages but stated in no structured data | 1 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 5 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | Canonical tag points to another site on 6/6 sampled pages | 6 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 5/6 sampled pages | 5 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | Most images have no width and height on 2/6 sampled pages | 2 |
| F-015 | Improvement opportunity | low | suspected (likely, not proven) | No XML sitemap found | 1 |

## Finding details

### F-001: Images are heavier than they need to be

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.90; Check: `image-weight`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.9; 3 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Large, oversized or legacy-format image files delay the largest paint and cost mobile visitors data, so visitors arriving from search or an AI answer wait longer

**Pages:**

- <https://www.mit.edu/>
- <https://www.mit.edu/about>
- <https://www.mit.edu/alumni>

**Evidence:**

- https://www.mit.edu/files/images/202610/MIT-Sensing-Sheets-SL.jpg: the file is 437 KB; it is served as JPEG although the request accepted AVIF and WebP (likely the largest image on the page)
  - <https://www.mit.edu/>
- https://www.mit.edu/files/images/201804/key-facts-1.jpg: it is served as JPEG although the request accepted AVIF and WebP (likely the largest image on the page)
  - <https://www.mit.edu/about>
- https://www.mit.edu/files/images/202308/community-service-project.jpeg: the file is 832 KB; it is served as JPEG although the request accepted AVIF and WebP (likely the largest image on the page)
  - <https://www.mit.edu/alumni>

**What to do:** Compress, resize and convert the listed images

**Suggested roles:** developer, seo

1. Serve AVIF or WebP, with JPEG or PNG only as a fallback in &lt;picture&gt;
2. Resize each image to the largest size it is displayed at and add srcset and sizes for smaller screens
3. Compress photos, aiming for under 200 KB for the largest image of a page

Effort: medium; Impact: medium; Major project: real value, plan the work.

**Expected benefit:** Faster largest paint and less data for visitors on mobile

**How to check the fix:** Re-run the audit and confirm the listed images are smaller

### F-002: Physical location is shown on the page but stated in no structured data

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `location-markup-missing`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer location-dependent questions from machine-readable addresses, coordinates and service areas; a location shown only as text or a map is easy to miss

**Pages:**

- <https://www.mit.edu/>
- <https://www.mit.edu/about>
- <https://www.mit.edu/accessibility>
- <https://www.mit.edu/admissions-aid>
- <https://www.mit.edu/alumni>
- <https://www.mit.edu/contact>

**Evidence:**

- address: 77 Massachusetts Avenue, Cambridge; map link: https://www.google.com/maps/place/Massachusetts+Institute+of+Technology/@42.360091,-71.09416,15z/data=!4m5!3m4!1s0x0:0xd. No address, geo or areaServed in any page's JSON-LD
  - <https://www.mit.edu/>
- address: 77 Massachusetts Avenue, Cambridge; map link: https://www.google.com/maps/place/Massachusetts+Institute+of+Technology/@42.360091,-71.09416,15z/data=!4m5!3m4!1s0x0:0xd. No address, geo or areaServed in any page's JSON-LD
  - <https://www.mit.edu/about>
- address: 77 Massachusetts Avenue Cambridge, MA 02139; map link: https://www.google.com/maps/place/Massachusetts+Institute+of+Technology/@42.360091,-71.09416,15z/data=!4m5!3m4!1s0x0:0xd. No address, geo or areaServed in any page's JSON-LD
  - <https://www.mit.edu/contact>
- address: 77 Massachusetts Avenue, Cambridge; map link: https://www.google.com/maps/place/Massachusetts+Institute+of+Technology/@42.360091,-71.09416,15z/data=!4m5!3m4!1s0x0:0xd. No address, geo or areaServed in any page's JSON-LD
  - <https://www.mit.edu/accessibility>
- address: 77 Massachusetts Avenue, Cambridge; map link: https://www.google.com/maps/place/Massachusetts+Institute+of+Technology/@42.360091,-71.09416,15z/data=!4m5!3m4!1s0x0:0xd. No address, geo or areaServed in any page's JSON-LD
  - <https://www.mit.edu/admissions-aid>
- and 1 more observations in the JSON report

**What to do:** State the address, coordinates and service area in Organization or LocalBusiness JSON-LD

**Suggested roles:** content, developer, seo

1. Add a PostalAddress (streetAddress, addressLocality, postalCode, addressCountry) to the Organization or LocalBusiness markup
2. Add geo coordinates for each physical location, and areaServed for the regions served
3. Keep the visible address, the markup and the business profile identical

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** The brand can be matched to location-specific questions

**How to check the fix:** Validate the markup and confirm the address matches the visible text

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.mit.edu/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.mit.edu/#organization",
  "name": "Massachusetts Institute of Technology",
  "url": "https://www.mit.edu/",
  "logo": "https://www.mit.edu/themes/mit/assets/favicon/apple-touch-icon.png",
  "description": "The mission of MIT is to advance knowledge and educate students in science, technology and other areas of scholarship that will best serve the nation and the world in the 21st century.",
  "sameAs": [
    "https://twitter.com/mit",
    "https://www.facebook.com/MITnews",
    "https://www.youtube.com/mit",
    "https://www.instagram.com/mit/"
  ],
  "address": "77 Massachusetts Avenue, Cambridge",
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

### F-003: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://www.mit.edu/contact>

**Evidence:**

- 4 unnamed control(s): &lt;a href=https://twitter.com/mit&gt; with only an icon, &lt;a href=https://www.facebook.com/MITnews&gt; with only an icon, &lt;a href=https://www.instagram.com/mit/&gt; with only an icon, &lt;a href=https://www.youtube.com/mit&gt; with only an icon
  - <https://www.mit.edu/contact>

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-004: About pages are missing Organization/AboutPage structured data

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.90; Check: `page-type-schema-gap:about`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.9; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** 1 page(s) classified as 'about' carry no Organization/AboutPage JSON-LD, so explicit machine-readable context may be improved

**Pages:**

- <https://www.mit.edu/about>

**Evidence:**

- 1 'about' page(s) missing Organization/AboutPage markup
  - <https://www.mit.edu/about>

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
<!-- https://www.mit.edu/about/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://www.mit.edu/about/",
  "name": "Massachusetts Institute of Technology",
  "description": "Founded to accelerate the nation’s industrial revolution, MIT is profoundly American. With ingenuity and drive, our graduates have invented fundamental technologies, launched new industries, and created millions of American jobs. At the same time, and without the slightest sense of contradiction, MI",
  "about": {
    "@id": "https://www.mit.edu/#organization"
  }
}
</script>
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-005: Contact pages are missing LocalBusiness/Organization/ContactPage structured data

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `page-type-schema-gap:contact`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** 1 page(s) classified as 'contact' carry no LocalBusiness/Organization/ContactPage JSON-LD, so explicit machine-readable context may be improved

**Pages:**

- <https://www.mit.edu/contact>

**Evidence:**

- 1 'contact' page(s) missing LocalBusiness/Organization/ContactPage markup
  - <https://www.mit.edu/contact>

**What to do:** Add LocalBusiness/Organization/ContactPage JSON-LD to contact pages

**Suggested roles:** developer, seo

1. Add LocalBusiness/Organization/ContactPage schema.org JSON-LD matching each contact page's content
2. Validate with a schema.org/Rich Results validator

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Contact facts are also stated as explicit structured data; no ranking, rich-result or citation gain is implied

**How to check the fix:** Re-crawl and confirm the expected @type is present

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.mit.edu/contact/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ContactPage",
  "url": "https://www.mit.edu/contact/",
  "name": "Massachusetts Institute of Technology",
  "description": "Contact Info Massachusetts Institute of Technology 77 Massachusetts Avenue Cambridge, MA 02139, USA 617-253-1000 TDD/TTY, use TRS (711) Undergraduate Admissions For questions about applying to MIT for undergraduate study, visit the Admissions Office or email admissions@mit.edu.",
  "about": {
    "@id": "https://www.mit.edu/#organization"
  }
}
</script>
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-006: Open Graph tags missing: og:image on 6/6 sampled pages, og:description on 5/6 sampled pages, og:title on 5/6 sampled pages, og:url on 5/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.mit.edu/>
- <https://www.mit.edu/about>
- <https://www.mit.edu/accessibility>
- <https://www.mit.edu/admissions-aid>
- <https://www.mit.edu/alumni>
- <https://www.mit.edu/contact>

**Evidence:**

- Missing nonempty fields: og:image
  - <https://www.mit.edu/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.mit.edu/about>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.mit.edu/contact>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.mit.edu/accessibility>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.mit.edu/admissions-aid>
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
<!-- https://www.mit.edu/ -->
<meta property="og:image" content="https://www.mit.edu/files/images/202610/MIT-Sensing-Sheets-SL.jpg">

<!-- https://www.mit.edu/about/ -->
<meta property="og:title" content="About MIT | MIT - Massachusetts Institute of Technology">
<meta property="og:description" content="Founded to accelerate the nation’s industrial revolution, MIT is profoundly American. With ingenuity and drive, our graduates have invented fundamental technologies, launched new industries, and creat">
<meta property="og:image" content="https://www.mit.edu/files/images/201804/key-facts-1.jpg">
<meta property="og:url" content="https://www.mit.edu/about/">

<!-- https://www.mit.edu/accessibility/ -->
<meta property="og:title" content="Accessibility | MIT - Massachusetts Institute of Technology">
<meta property="og:description" content="MIT resources available to individuals with disabilities: MIT Campus Accessibility Map Includes locations of elevators, accessible parking, ramps, restrooms, and more. Disability and Access Services E">
<meta property="og:image" content="https://www.mit.edu/themes/mit/assets/favicon/apple-touch-icon.png">
<meta property="og:url" content="https://www.mit.edu/accessibility/">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: Heading levels are skipped on 4/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 4 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.mit.edu/>
- <https://www.mit.edu/about>
- <https://www.mit.edu/admissions-aid>
- <https://www.mit.edu/alumni>

**Evidence:**

- Observed heading levels: \[1, 2, 4, 4, 2, 3, 3, 3, 3, 3, 3\]
  - <https://www.mit.edu/>
- Observed heading levels: \[1, 2, 5, 2, 4, 4, 4, 4, 4, 2, 2, 5, 2, 4, 5, 2, 5\]
  - <https://www.mit.edu/about>
- Observed heading levels: \[1, 2, 2, 5, 2, 5, 2, 5\]
  - <https://www.mit.edu/admissions-aid>
- Observed heading levels: \[1, 2, 2, 5, 2, 5\]
  - <https://www.mit.edu/alumni>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://www.mit.edu/>
- <https://www.mit.edu/about>
- <https://www.mit.edu/alumni>

**Evidence:**

- First content image https://www.mit.edu/files/images/202610/MIT-Sensing-Sheets-SL.jpg has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.mit.edu/>
- First content image https://www.mit.edu/files/images/201804/key-facts-1.jpg has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.mit.edu/about>
- First content image https://www.mit.edu/files/images/202308/community-service-project.jpeg has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.mit.edu/alumni>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-009: Likely Cumulative Layout Shift (CLS) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Markup patterns that let content move during loading were observed: layout may shift

**Pages:**

- <https://www.mit.edu/about>
- <https://www.mit.edu/alumni>

**Evidence:**

- Estimate, not a measurement: 1 video or iframe embed(s) without reserved size; 16 of 16 images without width and height
  - <https://www.mit.edu/about>
- Estimate, not a measurement: 1 video or iframe embed(s) without reserved size; 12 of 12 images without width and height
  - <https://www.mit.edu/alumni>

**What to do:** Check CLS in a browser or with field data, and remove the listed patterns

**Suggested roles:** developer, seo

1. Give every image, video and iframe width and height attributes or a CSS aspect-ratio
2. Reserve space for embeds, banners and late-loading content
3. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Cumulative Layout Shift score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-010: Email or phone shown on 1/6 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://www.mit.edu/contact>

**Evidence:**

- email: aacomments@mit.edu, admissions@mit.edu, campus-map@mit.edu; phone: 617-253-1000. No email, telephone or contactPoint in any page's structured data
  - <https://www.mit.edu/contact>

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
<!-- https://www.mit.edu/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.mit.edu/#organization",
  "name": "Massachusetts Institute of Technology",
  "url": "https://www.mit.edu/",
  "logo": "https://www.mit.edu/themes/mit/assets/favicon/apple-touch-icon.png",
  "description": "The mission of MIT is to advance knowledge and educate students in science, technology and other areas of scholarship that will best serve the nation and the world in the 21st century.",
  "sameAs": [
    "https://twitter.com/mit",
    "https://www.facebook.com/MITnews",
    "https://www.youtube.com/mit",
    "https://www.instagram.com/mit/"
  ],
  "email": "admissions@mit.edu",
  "telephone": "617-253-1000",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "admissions@mit.edu",
      "telephone": "617-253-1000"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-011: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://www.mit.edu/about>
- <https://www.mit.edu/accessibility>
- <https://www.mit.edu/admissions-aid>
- <https://www.mit.edu/alumni>
- <https://www.mit.edu/contact>

**Evidence:**

- Visible breadcrumb without schema
  - <https://www.mit.edu/about>
  - <https://www.mit.edu/contact>
  - <https://www.mit.edu/accessibility>
  - <https://www.mit.edu/admissions-aid>
  - <https://www.mit.edu/alumni>

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-012: Canonical tag points to another site on 6/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `cross-origin-canonical`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An external canonical can nominate another origin as the preferred copy.

**Pages:**

- <https://www.mit.edu/>
- <https://www.mit.edu/about>
- <https://www.mit.edu/accessibility>
- <https://www.mit.edu/admissions-aid>
- <https://www.mit.edu/alumni>
- <https://www.mit.edu/contact>

**Evidence:**

- External canonical hint: https://tlecms.mit.edu/
  - <https://www.mit.edu/>
- External canonical hint: https://tlecms.mit.edu/about
  - <https://www.mit.edu/about>
- External canonical hint: https://tlecms.mit.edu/contact
  - <https://www.mit.edu/contact>
- External canonical hint: https://tlecms.mit.edu/accessibility
  - <https://www.mit.edu/accessibility>
- External canonical hint: https://tlecms.mit.edu/admissions-aid
  - <https://www.mit.edu/admissions-aid>
- and 1 more observations in the JSON report

**What to do:** Verify ownership and content equivalence; correct the URL only if the external canonical is unintended.

**Suggested roles:** developer, seo

1. Verify ownership and content equivalence; correct the URL only if the external canonical is unintended.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Avoids unintended consolidation while preserving legitimate syndication.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-013: No valid twitter:card tag on 5/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.mit.edu/about>
- <https://www.mit.edu/accessibility>
- <https://www.mit.edu/admissions-aid>
- <https://www.mit.edu/alumni>
- <https://www.mit.edu/contact>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.mit.edu/about>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.mit.edu/contact>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.mit.edu/accessibility>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.mit.edu/admissions-aid>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.mit.edu/alumni>

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.mit.edu/about/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.mit.edu/accessibility/ -->
<meta name="twitter:card" content="summary">

<!-- https://www.mit.edu/admissions-aid/ -->
<meta name="twitter:card" content="summary">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-014: Most images have no width and height on 2/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `image-sizing`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Images without dimensions may lack reserved space unless CSS already supplies it.

**Pages:**

- <https://www.mit.edu/about>
- <https://www.mit.edu/alumni>

**Evidence:**

- 16/16 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://www.mit.edu/about>
- 12/12 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://www.mit.edu/alumni>

**What to do:** Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

**Suggested roles:** developer, seo

1. Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Can reduce layout movement and unnecessary loading; layout shift is not measured.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-015: No XML sitemap found

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-unavailable`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without a discovered sitemap, this audit relies more heavily on sampled links.

**Pages:**

- <https://www.mit.edu/>

**Evidence:**

- Sitemap probe status: absent; checked: https://www.mit.edu/sitemap.xml (absent). No additional sitemap discovery was attempted by this check.
  - <https://www.mit.edu/>

**What to do:** If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

**Suggested roles:** infrastructure, seo

1. If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves inventory discovery; absence is not a universal indexing defect.

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
- **Every page has an H1 heading.** All 6 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 35 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
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

- 13 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 24 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 6 of 16 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Linked sameAs and review profiles were not fetched (OFF\_SITE\_LOOKUP=0), so whether they resolve and belong to the brand was not checked.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 24 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.

## Notes from the run

- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Off-site profile lookup disabled (OFF\_SITE\_LOOKUP=0); linked profiles were not fetched or verified.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
