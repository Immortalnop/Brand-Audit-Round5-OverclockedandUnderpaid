# Brand AI-Readiness Audit: https://barenecessities.in/

- **Audited at:** 2026-10-13T13:35:16.163439+00:00
- **Run:** Completed
- **Pages:** 5 analyzed of 140 discovered; 3 of 10 site sections reached
- **Run time:** 10.7 seconds
- **Time limits:** audit worker stopped at 120 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 17 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.17)

Confidence is low (0.17). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 5 of 140 discovered page(s) and reached 3 of 10 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.17 | The page sample is small or one-sided: the crawl analyzed 5 of 140 discovered page(s) and reached 3 of 10 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.50 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 19 |
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 17 |
| Improvement suggestions (not defects) | 17 |
| Not enough evidence to judge | 0 |
| Recommendations | 17 |

## Start here

**F-001: Links or buttons have no accessible name**

Name every icon-only link and button

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Links or buttons have no accessible name | Name every icon-only link and button | medium | medium | low | yes | developer, seo |
| 2 | F-002: Old dates found among contact facts without recent corroborating updates | Review and refresh outdated contact facts | high | medium | low | yes | content, developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Links or buttons have no accessible name.** Name every icon-only link and button (impact medium, effort low)
- **F-002: Old dates found among contact facts without recent corroborating updates.** Review and refresh outdated contact facts (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Links or buttons have no accessible name | 5 |
| F-002 | Defect | medium | suspected (likely, not proven) | Old dates found among contact facts without recent corroborating updates | 1 |
| F-003 | Improvement opportunity | low | confirmed | Video or audio is embedded without complete VideoObject or AudioObject markup | 2 |
| F-004 | Improvement opportunity | low | confirmed | Video or audio has no transcript that crawlers can read | 2 |
| F-005 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 2 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 1/5 sampled pages but stated in no structured data | 1 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 1/5 sampled pages | 1 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Likely Cumulative Layout Shift (CLS) risk, estimated from markup and not measured | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Visible text is under 3% of the HTML on 5/5 sampled pages | 5 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 2/5 sampled pages | 2 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Images have no text alternative: no alt text, caption or link text says what they show | 2 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | A dialog or overlay may cover the content on arrival | 5 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 2 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | HTML response larger than 400 KB on 3/5 sampled pages | 3 |
| F-015 | Improvement opportunity | low | suspected (likely, not proven) | Consider structured exports for existing steps or ratings | 2 |
| F-016 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 5 |
| F-017 | Improvement opportunity | low | suspected (likely, not proven) | Physical location is shown on the page but stated in no structured data | 1 |
| F-018 | Improvement opportunity | low | suspected (likely, not proven) | No page or link names an audience segment across 5 sampled pages | 1 |
| F-019 | Improvement opportunity | low | suspected (likely, not proven) | No saved or recently viewed items on 2/2 product pages | 2 |

## Finding details

### F-001: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/pages/contact-us>
- <https://barenecessities.in/pages/our-story>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- 4 unnamed control(s): &lt;a href=/cart&gt; with no content, &lt;a href=https://www.nykaa.com/brands/bare-necessities/c/75924&gt; with only an icon, &lt;a href=https://www.amazon.in/stores/Barenecessities/page/41701A58-F80A-462B-990B-2C04C1&gt; with only an icon, &lt;a href=https://www.breakfreefromplastic.org/&gt; with only an icon
  - <https://barenecessities.in/>
- 1 unnamed control(s): &lt;a href=/cart&gt; with no content
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- 1 unnamed control(s): &lt;a href=/cart&gt; with no content
  - <https://barenecessities.in/pages/contact-us>
- 1 unnamed control(s): &lt;a href=/cart&gt; with no content
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>
- 1 unnamed control(s): &lt;a href=/cart&gt; with no content
  - <https://barenecessities.in/pages/our-story>

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: Old dates found among contact facts without recent corroborating updates

Type: Defect; Severity: medium; Status: suspected (likely, not proven); Confidence: 0.31; Check: `stale-dates:contact`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, suspected status, confidence 0.311; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Dated content classified as 'contact' appears outdated relative to the current year (within the pages actually crawled; the rest of the site was not analyzed)

**Pages:**

- <https://barenecessities.in/pages/contact-us>

**Evidence:**

- sitemap lastmod 2022-11-08 (page last updated 2022-11-08)
  - <https://barenecessities.in/pages/contact-us>

**What to do:** Review and refresh outdated contact facts

**Suggested roles:** content, developer, seo

1. Audit pages with old contact facts
2. Update or remove stale references

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Reduces risk of assistants citing stale facts

**How to check the fix:** Re-check dates after the update

### F-003: Video or audio is embedded without complete VideoObject or AudioObject markup

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `media-schema-missing`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without VideoObject or AudioObject markup, search engines and assistants have no machine-readable title, description, thumbnail or date for the media

**Pages:**

- <https://barenecessities.in/pages/our-story>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>

**Evidence:**

- video with no VideoObject markup
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- video with no VideoObject markup
  - <https://barenecessities.in/pages/our-story>

**What to do:** Describe each video and audio clip with VideoObject or AudioObject JSON-LD

**Suggested roles:** developer, seo

1. Add VideoObject markup with name, description, thumbnailUrl, uploadDate and duration
2. Use AudioObject or PodcastEpisode markup for audio
3. Add the transcript property where a transcript exists

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Media becomes eligible for video results and its details are quotable

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-004: Video or audio has no transcript that crawlers can read

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `media-transcript-missing`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.75; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Crawlers and assistants do not watch or listen, so what is said in a video or podcast is invisible to them unless a transcript is on or linked from the page

**Pages:**

- <https://barenecessities.in/pages/our-story>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>

**Evidence:**

- No transcript in the page text or links; native video player: no captions track; native video player: no captions track; native video player: no captions track; native video player: no captions track
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- No transcript in the page text or links; YouTube embed: captions inside the player not checked; YouTube embed: captions inside the player not checked; YouTube embed: captions inside the player not checked; YouTube embed: captions inside the player not checked
  - <https://barenecessities.in/pages/our-story>

**What to do:** Publish a transcript with each video and audio clip

**Suggested roles:** developer, seo

1. Add the full transcript as text on the page, or link to it from next to the player
2. Add a captions track (WebVTT) to native video players and enable captions on embeds
3. Include the transcript in the VideoObject or AudioObject transcript property

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** What the video or audio says becomes quotable text

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-005: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/pages/contact-us>

**Evidence:**

- First content image https://barenecessities.in/cdn/shop/files/preview\_images/DSC08057\_800x.jpg?v=1788857712 has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://barenecessities.in/>
- First content image https://cdn.shopify.com/s/files/1/1770/7729/files/Screen\_Shot\_2017-02-12\_at\_7.55.05\_PM\_large.png?v=1486909583 has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://barenecessities.in/pages/contact-us>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-006: Email or phone shown on 1/5 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://barenecessities.in/pages/contact-us>

**Evidence:**

- email: info@barenecessities.in. No email, telephone or contactPoint in any page's structured data
  - <https://barenecessities.in/pages/contact-us>

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
<!-- https://barenecessities.in/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://barenecessities.in/#organization",
  "name": "Bare Necessities",
  "url": "https://barenecessities.in/",
  "logo": "https://barenecessities.in/cdn/shop/files/Bare_FinalLogo_1.png?crop=center&height=32&v=1784274344&width=32",
  "description": "Shop premium natural & zero waste gifts, sustainable, premium skincare, and eco-friendly personal care like natural deodorants. Curated luxury hampers for corporates, weddings & celebrations",
  "sameAs": [
    "https://www.youtube.com/watch?v=LR7dgOZ9OvA",
    "https://www.facebook.com/BareNecessitiesZeroWasteIndia",
    "https://www.instagram.com/barenecessities_zerowasteindia/",
    "https://www.youtube.com/@BareNecessitiesZeroWaste"
  ],
  "email": "info@barenecessities.in",
  "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "info@barenecessities.in",
      "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`, `REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: Heading levels are skipped on 1/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://barenecessities.in/>

**Evidence:**

- Observed heading levels: \[1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3\]
  - <https://barenecessities.in/>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: Likely Cumulative Layout Shift (CLS) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Markup patterns that let content move during loading were observed: layout may shift

**Pages:**

- <https://barenecessities.in/>

**Evidence:**

- Estimate, not a measurement: 13 video or iframe embed(s) without reserved size; the first content image has no width and height
  - <https://barenecessities.in/>

**What to do:** Check CLS in a browser or with field data, and remove the listed patterns

**Suggested roles:** developer, seo

1. Give every image, video and iframe width and height attributes or a CSS aspect-ratio
2. Reserve space for embeds, banners and late-loading content
3. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Cumulative Layout Shift score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-009: Visible text is under 3% of the HTML on 5/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `markup-ratio`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A small visible-text share in a large HTML document can indicate excess markup.

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/pages/contact-us>
- <https://barenecessities.in/pages/our-story>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- Visible text represents 2.5% of decoded HTML body bytes. This is not a ranking metric.
  - <https://barenecessities.in/>
- Visible text represents 2.6% of decoded HTML body bytes. This is not a ranking metric.
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- Visible text represents 1.7% of decoded HTML body bytes. This is not a ranking metric.
  - <https://barenecessities.in/pages/contact-us>
- Visible text represents 3.0% of decoded HTML body bytes. This is not a ranking metric.
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>
- Visible text represents 2.2% of decoded HTML body bytes. This is not a ranking metric.
  - <https://barenecessities.in/pages/our-story>

**What to do:** Inspect inline assets and template boilerplate before trimming unnecessary HTML.

**Suggested roles:** developer, seo

1. Inspect inline assets and template boilerplate before trimming unnecessary HTML.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Reduces document overhead if the sampled ratio reflects avoidable markup.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-010: Title shorter than 15 or longer than 70 characters on 2/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://barenecessities.in/pages/contact-us>
- <https://barenecessities.in/pages/our-story>

**Evidence:**

- Title has 10 characters: Contact Us. Display width was not measured.
  - <https://barenecessities.in/pages/contact-us>
- Title has 9 characters: Our Story. Display width was not measured.
  - <https://barenecessities.in/pages/our-story>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-011: Images have no text alternative: no alt text, caption or link text says what they show

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `missing-alt`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>

**Evidence:**

- At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.
  - <https://barenecessities.in/>
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- 3 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://barenecessities.in/cdn/shop/files/preview\_images/126e2d3bf8c54ff2b568693d56c3156e.thumbnail., https://barenecessities.in/cdn/shop/files/preview\_images/205b5b792be0437781d67f6c2f23ebec.thumbnail., https://barenecessities.in/cdn/shop/files/preview\_images/0df307e6fd9e4053ba33524b7af1b403.thumbnail.
  - <https://barenecessities.in/>
- 3 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://barenecessities.in/cdn/shop/files/preview\_images/31897027a9bd4b93b40e740d5956331c.thumbnail., https://barenecessities.in/cdn/shop/files/preview\_images/9e26c2dd6496423baf4ead817caf4455.thumbnail., https://barenecessities.in/cdn/shop/files/preview\_images/ff1f0ba5c596407787bc74f76bcd8fe0.thumbnail.
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>

**What to do:** Describe informative images and keep decorative alt text empty

**Suggested roles:** developer, seo

1. Describe informative images and keep decorative alt text empty
2. Repeat essential image-only facts in nearby text

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-012: A dialog or overlay may cover the content on arrival

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `overlay`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.65; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The delivered HTML contains a blocking dialog or full-screen layer; visitors arriving from an answer may meet it before the content. Timing and visibility were not measured

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/pages/contact-us>
- <https://barenecessities.in/pages/our-story>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- Likely dialog or overlay: 2 aria-modal dialog(s) in the delivered HTML
  - <https://barenecessities.in/>
- Likely dialog or overlay: 2 aria-modal dialog(s) in the delivered HTML
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- Likely dialog or overlay: 2 aria-modal dialog(s) in the delivered HTML
  - <https://barenecessities.in/pages/contact-us>
- Likely dialog or overlay: 2 aria-modal dialog(s) in the delivered HTML
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>
- Likely dialog or overlay: 2 aria-modal dialog(s) in the delivered HTML
  - <https://barenecessities.in/pages/our-story>

**What to do:** Make sure arriving visitors reach the content before any optional dialog

**Suggested roles:** developer, seo

1. Show cookie consent as a non-blocking banner where the law allows, not a full-screen wall
2. Delay newsletter or promotion dialogs until the visitor has engaged, and give each a visible close control
3. Do not lock page scrolling unless a dialog really requires an answer

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Visitors see the content they came for straight away

**How to check the fix:** Open the affected pages on a phone in a private window and check what appears first

### F-013: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Priority basis:** low severity, suspected status, confidence 0.65; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- Visible breadcrumb without schema
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

**Suggested roles:** developer, seo

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-014: HTML response larger than 400 KB on 3/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `heavy-html`; Seen on 3 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 3 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Large HTML bodies consume the bounded retrieval budget.

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- Retained 572537 HTML body bytes; truncated: False. Asset transfer sizes were not measured.
  - <https://barenecessities.in/>
- Retained 543713 HTML body bytes; truncated: False. Asset transfer sizes were not measured.
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- Retained 508473 HTML body bytes; truncated: False. Asset transfer sizes were not measured.
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>

**What to do:** Trim unnecessary inline payloads and paginate only where useful; retain essential content.

**Suggested roles:** developer, seo

1. Trim unnecessary inline payloads and paginate only where useful; retain essential content.

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Reduces bytes required to retrieve the primary document.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-015: Consider structured exports for existing steps or ratings

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `citation-schema-opportunity`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Numbered steps or ratings are visible; optional structured exports may suit an identified content reuse workflow

**Pages:**

- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- visible rating text ('112 reviews') with no AggregateRating or Review markup
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- visible rating text ('20 reviews') with no AggregateRating or Review markup
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>

**What to do:** Evaluate structured exports only for a consumer and content workflow you actually use

**Suggested roles:** developer, seo

1. Identify the intended structured-content consumer before adding optional markup
2. Add HowTo markup for real step-by-step instructions
3. Add AggregateRating to Product or Service markup only when the ratings shown are real customer ratings

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Optional structured facts support the identified export/reuse workflow; no ranking or citation gain is measured

**How to check the fix:** Validate the pages with a schema.org validator and re-run the audit

### F-016: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <https://barenecessities.in/>
- <https://barenecessities.in/pages/contact-us>
- <https://barenecessities.in/pages/our-story>
- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- None of the 5 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <https://barenecessities.in/>
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
  - <https://barenecessities.in/pages/contact-us>

**What to do:** Claim and link review profiles that fit the business, such as Trustpilot, the Better Business Bureau, Crunchbase or an industry directory

**Suggested roles:** content, developer, seo

1. Claim or create profiles on review platforms that fit the business (Trustpilot, the Better Business Bureau, Crunchbase or an industry directory)
2. Link them from the site footer and list them in Organization sameAs
3. Ask real customers for reviews and answer them publicly

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Independent ratings and reviews corroborate the brand in assistant answers

**How to check the fix:** Re-run the audit after the links or profiles change

### F-017: Physical location is shown on the page but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `location-markup-missing`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer location-dependent questions from machine-readable addresses, coordinates and service areas; a location shown only as text or a map is easy to miss

**Pages:**

- <https://barenecessities.in/pages/contact-us>

**Evidence:**

- address: 3rd Floor, 29 Maliks Complex, Bowring Hospital Rd, Bengaluru, Karnataka 560001. No address, geo or areaServed in any page's JSON-LD
  - <https://barenecessities.in/pages/contact-us>

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
<!-- https://barenecessities.in/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://barenecessities.in/#organization",
  "name": "Bare Necessities",
  "url": "https://barenecessities.in/",
  "logo": "https://barenecessities.in/cdn/shop/files/Bare_FinalLogo_1.png?crop=center&height=32&v=1784274344&width=32",
  "description": "Shop premium natural & zero waste gifts, sustainable, premium skincare, and eco-friendly personal care like natural deodorants. Curated luxury hampers for corporates, weddings & celebrations",
  "sameAs": [
    "https://www.youtube.com/watch?v=LR7dgOZ9OvA",
    "https://www.facebook.com/BareNecessitiesZeroWasteIndia",
    "https://www.instagram.com/barenecessities_zerowasteindia/",
    "https://www.youtube.com/@BareNecessitiesZeroWaste"
  ],
  "address": "3rd Floor, 29 Maliks Complex, Bowring Hospital Rd, Bengaluru, Karnataka 560001",
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

### F-018: No page or link names an audience segment across 5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.50; Check: `audience-segment-missing`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.5; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants weight answers toward the asker's stated role or need; a site with no page for a named audience gives them nothing to match "for small businesses" or "for students" to

**Pages:**

- <https://barenecessities.in/>

**Evidence:**

- Checked 5 page titles and headings and 268 internal links; none names an audience ("for teams", /industries/, /use-cases/)
  - <https://barenecessities.in/>

**What to do:** Publish one page per main audience and link it from the navigation

**Suggested roles:** content, developer, seo

1. List the two to four audiences the offer serves best
2. Give each a page that states the audience in its title and H1, with the use cases, proof and pricing that matter to it
3. Link those pages from the main navigation and the home page

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Assistants can match the brand to questions that state who is asking

**How to check the fix:** Re-run the audit and confirm audience pages are detected

### F-019: No saved or recently viewed items on 2/2 product pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.40; Check: `context-retention-missing`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.4; 2 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Returning visitors pick up where they left off only if the site keeps their state; without saved or recently viewed items, each visit starts from zero

**Pages:**

- <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
- <https://barenecessities.in/products/lavender-levilate-bath-salts>

**Evidence:**

- No wishlist, save-for-later, compare or recently viewed control in the HTML, and no mount point, data attribute or script for one. A widget that JavaScript adds without any trace in the raw HTML would be missed
  - <https://barenecessities.in/products/busy-bee-lip-balm-zero-waste-eco-friendly-natural>
  - <https://barenecessities.in/products/lavender-levilate-bath-salts>

**What to do:** Let visitors save items and see what they viewed recently

**Suggested roles:** developer, seo

1. Add a save-for-later or wishlist control to product pages
2. Show recently viewed items on product and category pages
3. Keep the saved list across visits without requiring an account

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Returning visitors resume their task instead of searching again

**How to check the fix:** Open a product page in a browser and confirm the control is present

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **An XML sitemap is available.** An XML sitemap was read; it lists 114 URLs.
- **llms.txt is present and well formed.** /llms.txt is present, follows the optional artifact format and lists 8 links. Google Search ignores it; visibility gains are unmeasured.
- **Pages are served over HTTPS.** All 5 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 5 pages checked have a document title.
- **Every page has a meta description.** All 5 pages checked have a meta description.
- **Every page declares its language.** All 5 pages checked declare their language (html lang).
- **Every page declares a canonical URL.** All 5 pages checked declare a canonical URL on this site.
- **Pages are open to indexing and snippets.** None of the 5 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Structured data parses cleanly.** JSON-LD structured data is on 2 of the 5 pages checked, and every block parsed.
- **Content is in the raw HTML.** All 5 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 5 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 5 pages checked declare a mobile viewport, and none blocks zooming.
- **Every page links onward.** Each of the 5 pages crawled links to at least one other page on the site.

## Agent checks

Received: outcome envelope. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The packet records a known About target not acquired within this bounded sample; no assessable complete opening was supplied. No homepage substitution or second fetch was performed. |
| AG-02 Independent mentions | not assessed | No independent-source query and inspection completed in the remaining host allowance. |
| AG-03 Independent contradiction | not assessed | No bound acquired claim was compared with independently inspected external evidence. |
| AG-04 Facts drawn inside images | not assessed | No full packet-listed image was viewed; no visual assessment is claimed. |
| AG-05 Namesake ambiguity | not assessed | No namesake query and distinguishing-source inspection completed in the remaining host allowance. |
| AG-06 Review and profile opportunity | not assessed | No applicable platform query and source inspection completed in the remaining host allowance. |

## What this audit could not check

- 134 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 140 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 3 of 10 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- 8 link(s) listed in llms.txt were not checked (another domain, robots rules, the per-audit cap or a fetch error; see coverage.llms\_txt).
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 77 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.
- Overlays were judged from the delivered HTML only; when and whether they appear on screen was not measured, so overlay findings are suspected.
- Agent check AG-01 (About-page concreteness) was not assessed: The packet records a known About target not acquired within this bounded sample; no assessable complete opening was supplied. No homepage substitution or second fetch was performed.
- Agent check AG-02 (Independent mentions) was not assessed: No independent-source query and inspection completed in the remaining host allowance.
- Agent check AG-03 (Independent contradiction) was not assessed: No bound acquired claim was compared with independently inspected external evidence.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No full packet-listed image was viewed; no visual assessment is claimed.
- Agent check AG-05 (Namesake ambiguity) was not assessed: No namesake query and distinguishing-source inspection completed in the remaining host allowance.
- Agent check AG-06 (Review and profile opportunity) was not assessed: No applicable platform query and source inspection completed in the remaining host allowance.

## Notes from the run

- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
