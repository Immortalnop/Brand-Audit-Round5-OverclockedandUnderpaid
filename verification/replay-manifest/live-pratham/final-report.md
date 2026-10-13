# Brand AI-Readiness Audit: https://www.pratham.org/

- **Audited at:** 2026-10-13T13:38:45.995678+00:00
- **Run:** Completed
- **Pages:** 5 analyzed of 78 discovered; 2 of 26 site sections reached
- **Run time:** 11.3 seconds
- **Time limits:** audit worker stopped at 120 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 25 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.08)

Confidence is low (0.08). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 5 of 78 discovered page(s) and reached 2 of 26 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.08 | The page sample is small or one-sided: the crawl analyzed 5 of 78 discovered page(s) and reached 2 of 26 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.50 | No Organization markup was found; the brand name was read from the site's own metadata (site name, title suffix or copyright line), which is less certain. Adding Organization markup confirms it. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 17 |
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 15 |
| Improvement suggestions (not defects) | 15 |
| Not enough evidence to judge | 1 |
| Recommendations | 16 |

## Start here

**F-001: Links or buttons have no accessible name**

Name every icon-only link and button

Impact medium, effort low. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Links or buttons have no accessible name | Name every icon-only link and button | medium | medium | low | yes | developer, seo |
| 2 | F-002: Image alt text is a file name, placeholder or repeated label that describes nothing | Replace placeholder alt text with a short description of each image | medium | medium | low | yes | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-001: Links or buttons have no accessible name.** Name every icon-only link and button (impact medium, effort low)
- **F-002: Image alt text is a file name, placeholder or repeated label that describes nothing.** Replace placeholder alt text with a short description of each image (impact medium, effort low)
- **F-004: Video or audio is embedded without complete VideoObject or AudioObject markup.** Describe each video and audio clip with VideoObject or AudioObject JSON-LD (impact medium, effort low)
- **F-005: Video or audio has no transcript that crawlers can read.** Publish a transcript with each video and audio clip (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | medium | confirmed | Links or buttons have no accessible name | 5 |
| F-002 | Defect | medium | confirmed | Image alt text is a file name, placeholder or repeated label that describes nothing | 1 |
| F-003 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 5 |
| F-004 | Improvement opportunity | low | confirmed | Video or audio is embedded without complete VideoObject or AudioObject markup | 3 |
| F-005 | Improvement opportunity | low | confirmed | Video or audio has no transcript that crawlers can read | 3 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Email or phone shown on 5/5 sampled pages but stated in no structured data | 5 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 5/5 sampled pages | 5 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 5/5 sampled pages, og:image on 5/5 sampled pages, og:title on 5/5 sampled pages, og:url on 5/5 sampled pages | 5 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 5 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 4/5 sampled pages | 4 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Visible text is under 3% of the HTML on 4/5 sampled pages | 4 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | Images have no text alternative: no alt text, caption or link text says what they show | 5 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | No valid twitter:card tag on 5/5 sampled pages | 5 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | Six or more render-blocking head scripts on 5/5 sampled pages | 5 |
| F-015 | Improvement opportunity | low | suspected (likely, not proven) | 2 question heading(s) are not followed by a direct answer on 2/5 sampled pages | 2 |
| F-016 | Improvement opportunity | low | suspected (likely, not proven) | Physical location is shown on the page but stated in no structured data | 5 |
| F-017 | Improvement opportunity | low | not enough evidence to judge | Acquisition could not assess a URL | 1 |

## Finding details

### F-001: Links or buttons have no accessible name

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `control-name-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A link or button with no text, no image alt text and no aria-label is announced only as 'link' or 'button', so screen-reader users and AI agents cannot tell where it leads

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- 16 unnamed control(s): &lt;button&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=https://www.pratham.org:443/2026/09/24/lata/&gt; with only an icon, &lt;a href=https://www.pratham.org:443/2026/07/24/shabana/&gt; with only an icon
  - <https://www.pratham.org/>
- 18 unnamed control(s): &lt;button&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=https://www.pratham.org:443/2020/10/20/banmali-agrawala/&gt; with only an icon, &lt;a href=https://www.pratham.org:443/2019/05/04/dinyar-s-devitre/&gt; with only an icon
  - <https://www.pratham.org:443/about/board/>
- 8 unnamed control(s): &lt;button&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=\#page&gt; with only an icon, &lt;a href=https://www.facebook.com/sharer.php?u=https://pratham.org/shuruaat-aapse/&gt; with only an icon
  - <https://www.pratham.org:443/about/financials/>
- 11 unnamed control(s): &lt;button&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=https://www.pratham.org:443/2019/05/21/dr-rukmini-banerji-3/&gt; with only an icon, &lt;a href=https://www.pratham.org:443/2019/05/07/ms-farida-lambay/&gt; with only an icon
  - <https://www.pratham.org:443/about/leadership/>
- 8 unnamed control(s): &lt;button&gt; with only an icon, &lt;button&gt; with only an icon, &lt;a href=\#page&gt; with only an icon, &lt;a href=https://www.facebook.com/sharer.php?u=https://pratham.org/shuruaat-aapse/&gt; with only an icon
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Name every icon-only link and button

**Suggested roles:** developer, seo

1. Add an aria-label that says what the control does, such as aria-label="Open cart"
2. Or add visually hidden text inside the control
3. Mark the icon itself aria-hidden="true"

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-002: Image alt text is a file name, placeholder or repeated label that describes nothing

Type: Defect; Severity: medium; Status: confirmed; Confidence: 0.85; Check: `alt-text-quality`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** medium severity, confirmed status, confidence 0.85; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Alt text such as a file name or a word like 'banner' gives crawlers, assistants and screen readers no description of the image

**Pages:**

- <https://www.pratham.org/>

**Evidence:**

- 34 image(s) with uninformative alt text, for example alt="34" (a code or number) on https://www.pratham.org:443/wp-content/uploads/2020/01/34-160x100.jpg; alt="9" (a single character or punctuation) on https://www.pratham.org:443/wp-content/uploads/2020/01/9-160x100.jpg; alt="33" (a code or number) on https://www.pratham.org:443/wp-content/uploads/2020/01/33-160x100.jpg
  - <https://www.pratham.org/>

**What to do:** Replace placeholder alt text with a short description of each image

**Suggested roles:** developer, seo

1. Write alt text that says what each informative image shows, in a short phrase
2. Use an empty alt="" for purely decorative images instead of a placeholder word
3. Fix the CMS or template default that fills alt text with the file name

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Crawlers, assistants and screen readers can tell what each image shows

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-003: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.85; 5 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 5 of 78 discovered pages that were actually crawled)

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- 0/5 pages contain JSON-LD
  - <https://www.pratham.org/>
  - <https://www.pratham.org:443/about/board/>
  - <https://www.pratham.org:443/about/financials/>
  - <https://www.pratham.org:443/about/leadership/>
  - <https://www.pratham.org:443/about/partners/>

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
<!-- Home page https://www.pratham.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.pratham.org/#organization",
      "name": "Pratham",
      "url": "https://www.pratham.org/",
      "logo": "https://www.pratham.org:443/wp-content/uploads/2019/04/favicon.png",
      "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION",
      "sameAs": [
        "https://www.facebook.com/PrathamEducationFoundation/",
        "https://www.linkedin.com/company/pratham",
        "https://www.youtube.com/user/prathamfoundation",
        "https://instagram.com/prathameducation",
        "https://twitter.com/Pratham_India",
        "https://www.youtube.com/watch?v=eXtnrNfPYDE",
        "https://www.instagram.com/prathameducation"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.pratham.org/#website",
      "name": "Pratham",
      "url": "https://www.pratham.org/",
      "publisher": {
        "@id": "https://www.pratham.org/#organization"
      }
    }
  ]
}
</script>

<!-- About page https://www.pratham.org:443/about/board/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://www.pratham.org:443/about/board/",
  "name": "Board",
  "description": "REPLACE_WITH_PAGE_DESCRIPTION",
  "about": {
    "@id": "https://www.pratham.org/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`, `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-004: Video or audio is embedded without complete VideoObject or AudioObject markup

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `media-schema-missing`; Seen on 3 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without VideoObject or AudioObject markup, search engines and assistants have no machine-readable title, description, thumbnail or date for the media

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/leadership/>

**Evidence:**

- video with no VideoObject markup
  - <https://www.pratham.org/>
- video with no VideoObject markup
  - <https://www.pratham.org:443/about/board/>
- video with no VideoObject markup
  - <https://www.pratham.org:443/about/leadership/>

**What to do:** Describe each video and audio clip with VideoObject or AudioObject JSON-LD

**Suggested roles:** developer, seo

1. Add VideoObject markup with name, description, thumbnailUrl, uploadDate and duration
2. Use AudioObject or PodcastEpisode markup for audio
3. Add the transcript property where a transcript exists

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Media becomes eligible for video results and its details are quotable

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-005: Video or audio has no transcript that crawlers can read

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `media-transcript-missing`; Seen on 3 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.75; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Crawlers and assistants do not watch or listen, so what is said in a video or podcast is invisible to them unless a transcript is on or linked from the page

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/leadership/>

**Evidence:**

- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://www.pratham.org/>
- No transcript in the page text or links; native video player: no captions track
  - <https://www.pratham.org:443/about/board/>
- No transcript in the page text or links; native video player: no captions track
  - <https://www.pratham.org:443/about/leadership/>

**What to do:** Publish a transcript with each video and audio clip

**Suggested roles:** developer, seo

1. Add the full transcript as text on the page, or link to it from next to the player
2. Add a captions track (WebVTT) to native video players and enable captions on embeds
3. Include the transcript in the VideoObject or AudioObject transcript property

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** What the video or audio says becomes quotable text

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-006: Email or phone shown on 5/5 sampled pages but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `contact-markup-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer "how do I contact them?" from machine-readable email, telephone and contactPoint properties; contact details shown only as text or links are easy to miss or to attribute to the wrong organization

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- email: info@pratham.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.pratham.org/>
- email: info@pratham.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.pratham.org:443/about/board/>
- email: finance@pratham.org, info@pratham.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.pratham.org:443/about/financials/>
- email: info@pratham.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.pratham.org:443/about/leadership/>
- email: info@pratham.org. No email, telephone or contactPoint in any page's structured data
  - <https://www.pratham.org:443/about/partners/>

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
<!-- https://www.pratham.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.pratham.org/#organization",
  "name": "Pratham",
  "url": "https://www.pratham.org/",
  "logo": "https://www.pratham.org:443/wp-content/uploads/2019/04/favicon.png",
  "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION",
  "sameAs": [
    "https://www.facebook.com/PrathamEducationFoundation/",
    "https://www.linkedin.com/company/pratham",
    "https://www.youtube.com/user/prathamfoundation",
    "https://instagram.com/prathameducation",
    "https://twitter.com/Pratham_India",
    "https://www.youtube.com/watch?v=eXtnrNfPYDE",
    "https://www.instagram.com/prathameducation"
  ],
  "email": "info@pratham.org",
  "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT",
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "REPLACE_WITH_CONTACT_TYPE",
      "email": "info@pratham.org",
      "telephone": "REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT"
    }
  ]
}
</script>
```

Replace before publishing: `REPLACE_WITH_CONTACT_TYPE`, `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`, `REPLACE_WITH_PHONE_IN_INTERNATIONAL_FORMAT`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-007: No meta description on 5/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.pratham.org/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.pratham.org:443/about/board/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.pratham.org:443/about/financials/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.pratham.org:443/about/leadership/>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Write a concise page-specific meta description that matches visible content.

**Suggested roles:** developer, seo

1. Write a concise page-specific meta description that matches visible content.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides a summary candidate; search engines may choose other text.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: Open Graph tags missing: og:description on 5/5 sampled pages, og:image on 5/5 sampled pages, og:title on 5/5 sampled pages, og:url on 5/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.pratham.org/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.pratham.org:443/about/board/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.pratham.org:443/about/financials/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.pratham.org:443/about/leadership/>
- Missing nonempty fields: og:title, og:description, og:image, og:url
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

**Suggested roles:** developer, seo

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.pratham.org/ -->
<meta property="og:title" content="Pratham – Every Child In School and Learning Well">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png">
<meta property="og:url" content="https://www.pratham.org/">

<!-- https://www.pratham.org:443/about/board/ -->
<meta property="og:title" content="Board – Pratham">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png">
<meta property="og:url" content="https://www.pratham.org:443/about/board/">

<!-- https://www.pratham.org:443/about/financials/ -->
<meta property="og:title" content="Financials – Pratham">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:image" content="https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png">
<meta property="og:url" content="https://www.pratham.org:443/about/financials/">
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-009: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- First content image https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.pratham.org/>
- First content image https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.pratham.org:443/about/board/>
- First content image https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.pratham.org:443/about/financials/>
- First content image https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.pratham.org:443/about/leadership/>
- First content image https://www.pratham.org:443/wp-content/uploads/2026/03/pratham.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Add srcset and sizes to the main image of each page

**Suggested roles:** developer, seo

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-010: Heading levels are skipped on 4/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 4 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- Observed heading levels: \[1, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.pratham.org:443/about/board/>
- Observed heading levels: \[1, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.pratham.org:443/about/financials/>
- Observed heading levels: \[1, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.pratham.org:443/about/leadership/>
- Observed heading levels: \[1, 1, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-011: Visible text is under 3% of the HTML on 4/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `markup-ratio`; Seen on 4 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A small visible-text share in a large HTML document can indicate excess markup.

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- Visible text represents 2.8% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.pratham.org/>
- Visible text represents 1.2% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.pratham.org:443/about/financials/>
- Visible text represents 1.7% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.pratham.org:443/about/leadership/>
- Visible text represents 2.7% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Inspect inline assets and template boilerplate before trimming unnecessary HTML.

**Suggested roles:** developer, seo

1. Inspect inline assets and template boilerplate before trimming unnecessary HTML.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Reduces document overhead if the sampled ratio reflects avoidable markup.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-012: Images have no text alternative: no alt text, caption or link text says what they show

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `missing-alt`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- At least three images per affected page lack alt attributes; empty decorative alt attributes were not counted.
  - <https://www.pratham.org/>
  - <https://www.pratham.org:443/about/board/>
  - <https://www.pratham.org:443/about/financials/>
  - <https://www.pratham.org:443/about/leadership/>
  - <https://www.pratham.org:443/about/partners/>
- 9 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://www.pratham.org:443/wp-content/uploads/2026/05/Prathmic-Website.jpg, https://www.pratham.org:443/wp-content/uploads/2025/01/2.png, https://www.pratham.org:443/wp-content/uploads/2025/01/4.png
  - <https://www.pratham.org/>
- 5 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://pratham.org/wp-content/uploads/2024/09/facebook.png, https://pratham.org/wp-content/uploads/2024/09/twitter.png, https://pratham.org/wp-content/uploads/2024/09/linkedin.png
  - <https://www.pratham.org:443/about/board/>
- 5 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://pratham.org/wp-content/uploads/2024/09/facebook.png, https://pratham.org/wp-content/uploads/2024/09/twitter.png, https://pratham.org/wp-content/uploads/2024/09/linkedin.png
  - <https://www.pratham.org:443/about/financials/>
- 5 content image(s) with no usable alt text and no caption, title, aria-label or link text, for example https://pratham.org/wp-content/uploads/2024/09/facebook.png, https://pratham.org/wp-content/uploads/2024/09/twitter.png, https://pratham.org/wp-content/uploads/2024/09/linkedin.png
  - <https://www.pratham.org:443/about/leadership/>

**What to do:** Describe informative images and keep decorative alt text empty

**Suggested roles:** developer, seo

1. Describe informative images and keep decorative alt text empty
2. Repeat essential image-only facts in nearby text

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-013: No valid twitter:card tag on 5/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `twitter-card`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Absent or unsupported Twitter Card metadata may limit card selection.

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.pratham.org/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.pratham.org:443/about/board/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.pratham.org:443/about/financials/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.pratham.org:443/about/leadership/>
- No supported nonempty twitter:card declaration observed. Platform fallback was not tested.
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Choose an appropriate supported twitter:card value and verify the target platform preview.

**Suggested roles:** developer, seo

1. Choose an appropriate supported twitter:card value and verify the target platform preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides an explicit card hint, without guaranteeing a rendered card.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://www.pratham.org/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.pratham.org:443/about/board/ -->
<meta name="twitter:card" content="summary_large_image">

<!-- https://www.pratham.org:443/about/financials/ -->
<meta name="twitter:card" content="summary_large_image">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-014: Six or more render-blocking head scripts on 5/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `blocking-scripts`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Classic external head scripts without async or defer can block parser progress.

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- Observed 7 classic external head scripts without async/defer. First paint and execution costs were not measured.
  - <https://www.pratham.org/>
- Observed 7 classic external head scripts without async/defer. First paint and execution costs were not measured.
  - <https://www.pratham.org:443/about/board/>
- Observed 7 classic external head scripts without async/defer. First paint and execution costs were not measured.
  - <https://www.pratham.org:443/about/financials/>
- Observed 7 classic external head scripts without async/defer. First paint and execution costs were not measured.
  - <https://www.pratham.org:443/about/leadership/>
- Observed 7 classic external head scripts without async/defer. First paint and execution costs were not measured.
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Review script dependencies and defer or asynchronously load noncritical scripts where safe.

**Suggested roles:** developer, seo

1. Review script dependencies and defer or asynchronously load noncritical scripts where safe.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** May reduce parser blocking; no paint or Core Web Vitals improvement is measured here.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-015: 2 question heading(s) are not followed by a direct answer on 2/5 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `question-answer-indirect`; Seen on 2 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants quote the sentence right after a question heading; when that sentence is missing, very long or a filler opener, the answer is not liftable as one passage

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- "Universal Preschool: Is This a Dream or Can It Be a Reality for India?": opens with filler ("In this article, Rukmini Banerji highlig")
  - <https://www.pratham.org/>
- "HOW TO PARTNER WITH PRATHAM?": no text before the next heading
  - <https://www.pratham.org:443/about/partners/>

**What to do:** Open each answer with one sentence that answers the question directly

**Suggested roles:** content, developer, seo

1. Start the text under each listed question with a direct answer of 40 words or fewer
2. Put supporting detail, caveats and examples after that first sentence
3. Remove filler openers such as "Great question" or "In this article"

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Assistants can lift a complete, correctly labelled answer from the page

**How to check the fix:** Re-run the audit and confirm the listed passages are reported as answerable

### F-016: Physical location is shown on the page but stated in no structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `location-markup-missing`; Seen on 5 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.55; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Assistants answer location-dependent questions from machine-readable addresses, coordinates and service areas; a location shown only as text or a map is easy to miss

**Pages:**

- <https://www.pratham.org/>
- <https://www.pratham.org:443/about/board/>
- <https://www.pratham.org:443/about/financials/>
- <https://www.pratham.org:443/about/leadership/>
- <https://www.pratham.org:443/about/partners/>

**Evidence:**

- address: B- 4/59, Safdarjung Enclave 1st Floor, New Delhi - 110 029. No address, geo or areaServed in any page's JSON-LD
  - <https://www.pratham.org/>
- address: B- 4/59, Safdarjung Enclave 1st Floor, New Delhi - 110 029. No address, geo or areaServed in any page's JSON-LD
  - <https://www.pratham.org:443/about/board/>
- address: B- 4/59, Safdarjung Enclave 1st Floor, New Delhi - 110 029. No address, geo or areaServed in any page's JSON-LD
  - <https://www.pratham.org:443/about/financials/>
- address: B- 4/59, Safdarjung Enclave 1st Floor, New Delhi - 110 029. No address, geo or areaServed in any page's JSON-LD
  - <https://www.pratham.org:443/about/leadership/>
- address: B- 4/59, Safdarjung Enclave 1st Floor, New Delhi - 110 029. No address, geo or areaServed in any page's JSON-LD
  - <https://www.pratham.org:443/about/partners/>

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
<!-- https://www.pratham.org/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.pratham.org/#organization",
  "name": "Pratham",
  "url": "https://www.pratham.org/",
  "logo": "https://www.pratham.org:443/wp-content/uploads/2019/04/favicon.png",
  "description": "REPLACE_WITH_ONE_SENTENCE_DESCRIPTION",
  "sameAs": [
    "https://www.facebook.com/PrathamEducationFoundation/",
    "https://www.linkedin.com/company/pratham",
    "https://www.youtube.com/user/prathamfoundation",
    "https://instagram.com/prathameducation",
    "https://twitter.com/Pratham_India",
    "https://www.youtube.com/watch?v=eXtnrNfPYDE",
    "https://www.instagram.com/prathameducation"
  ],
  "address": "B- 4/59, Safdarjung Enclave 1st Floor, New Delhi - 110 029",
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "REPLACE_WITH_LATITUDE",
    "longitude": "REPLACE_WITH_LONGITUDE"
  },
  "areaServed": "REPLACE_WITH_AREA_SERVED"
}
</script>
```

Replace before publishing: `REPLACE_WITH_AREA_SERVED`, `REPLACE_WITH_LATITUDE`, `REPLACE_WITH_LONGITUDE`, `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-017: Acquisition could not assess a URL

Type: Improvement opportunity; Severity: low; Status: not enough evidence to judge; Confidence: 0.30; Check: `fetch-failure`; Seen on 1 of 5 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, insufficient\_evidence status, confidence 0.3; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** This audit client encountered connection\_error. Local trust, network routing and server causes are not independently distinguished; crawler permission remains unknown when robots cannot be read.

**Pages:**

- <https://pratham.org/about/media-publications/>

**Evidence:**

- Acquisition outcome: connection\_error. Verified same-client attempt outcomes: \[\]. This is not independent reproduction of a site defect.
  - <https://pratham.org/about/media-publications/>

**What to do:** Compare the exact failure with the working client and repair the confirmed cause

**Suggested roles:** infrastructure, seo

1. Inspect coverage.transport\_diagnostics for verification code, phase and runtime details
2. Compare Python trust roots and direct routing with the successful client
3. If required, configure an administrator-approved CA bundle using AUDIT\_CA\_BUNDLE; never disable verification
4. Rerun the audit and inspect robots rules only after verified retrieval succeeds

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Restores reliable audit evidence when the local or remote cause is resolved

**How to check the fix:** A verified robots GET succeeds, or repeated exact failure remains an explicit limitation

## Other recommendations

Good practice to keep, beyond the findings above:

- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **Pages are served over HTTPS.** All 5 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 5 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 5 pages checked have a document title.
- **Every page declares its language.** All 5 pages checked declare their language (html lang).
- **Every page declares a canonical URL.** All 5 pages checked declare a canonical URL on this site.
- **Pages are open to indexing and snippets.** None of the 5 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Content is in the raw HTML.** All 5 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Every page has an H1 heading.** All 5 pages checked have an H1 heading.
- **Mobile viewport is declared and zoom is allowed.** All 5 pages checked declare a mobile viewport, and none blocks zooming.
- **Every page links onward.** Each of the 5 pages crawled links to at least one other page on the site.

## Agent checks

Received: outcome envelope. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The selected opening is homepage program teaser text at an empty About fragment; its representativeness as the organization About opening was not established. No missing-identity defect is inferred. |
| AG-02 Independent mentions | not assessed | No independent-source search was performed in this run. |
| AG-03 Independent contradiction | not assessed | No acquired claim was compared with inspected independent sources. |
| AG-04 Facts drawn inside images | not assessed | No full packet-listed image was viewed. |
| AG-05 Namesake ambiguity | not assessed | No namesake search or distinguishing-source inspection was performed. |
| AG-06 Review and profile opportunity | not assessed | No applicable platform-specific search was performed. |

## What this audit could not check

- 72 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 78 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 2 of 26 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- 17 linked PDF(s) were not fetched (robots rules, a cross-origin redirect, the per-audit cap of 3, or remaining budget; see coverage.non\_text\_media.pdf\_outcomes); their contents were not assessed.
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 133 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.
- sitemap.xml could not be checked (status: 'inaccessible'); crawl coverage may be incomplete relative to a site that publishes one.
- Agent check AG-01 (About-page concreteness) was not assessed: The selected opening is homepage program teaser text at an empty About fragment; its representativeness as the organization About opening was not established. No missing-identity defect is inferred.
- Agent check AG-02 (Independent mentions) was not assessed: No independent-source search was performed in this run.
- Agent check AG-03 (Independent contradiction) was not assessed: No acquired claim was compared with inspected independent sources.
- Agent check AG-04 (Facts drawn inside images) was not assessed: No full packet-listed image was viewed.
- Agent check AG-05 (Namesake ambiguity) was not assessed: No namesake search or distinguishing-source inspection was performed.
- Agent check AG-06 (Review and profile opportunity) was not assessed: No applicable platform-specific search was performed.

## Notes from the run

- No dated facts found; freshness cannot be assessed (absence is not proof of staleness).
- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
