# Brand AI-Readiness Audit: https://svelte.dev

- **Audited at:** 2026-10-12T16:55:11.475593+00:00
- **Run:** Completed
- **Pages:** 49 analyzed of 571 discovered; 7 of 11 site sections reached
- **Run time:** 68.9 seconds
- **Time limits:** audit worker stopped at 270 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 73 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** medium (0.64)

Confidence is medium (0.64). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 49 of 571 discovered page(s) and reached 7 of 11 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.64 | The page sample is small or one-sided: the crawl analyzed 49 of 571 discovered page(s) and reached 7 of 11 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.00 | No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 22 |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 22 |
| Improvement suggestions (not defects) | 20 |
| Not enough evidence to judge | 1 |
| Recommendations | 20 |

## Start here

**F-001: Images are heavier than they need to be**

Compress, resize and convert the listed images

Impact low, effort medium. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings.

| # | Finding | Action | Priority | Impact | Effort | Quick win |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Images are heavier than they need to be | Compress, resize and convert the listed images | low | low | medium | no |
| 2 | F-003: Form fields have no label | Give every form field a visible label tied to it | low | low | low | no |

## Quick wins

Valuable changes that take little work:

- **F-006: Article authors lack a Person profile or credentials.** State each article author as a Person with a profile and credentials (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | low | confirmed | Images are heavier than they need to be | 2 |
| F-002 | Improvement opportunity | low | confirmed | No structured data (JSON-LD) found on any crawled page | 49 |
| F-003 | Defect | low | confirmed | Form fields have no label | 1 |
| F-004 | Improvement opportunity | low | confirmed | Video or audio is embedded without complete VideoObject or AudioObject markup | 9 |
| F-005 | Improvement opportunity | low | confirmed | Some pages lack semantic headings | 1 |
| F-006 | Improvement opportunity | low | confirmed | Article authors lack a Person profile or credentials | 33 |
| F-007 | Improvement opportunity | low | confirmed | Video or audio has no transcript that crawlers can read | 8 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Open Graph tags missing: og:description on 49/49 sampled pages, og:title on 48/49 sampled pages, og:url on 48/49 sampled pages | 49 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 4/49 sampled pages | 4 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | No meta description on 3/49 sampled pages | 3 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | The main image of a page has no responsive variants | 3 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | Likely Cumulative Layout Shift (CLS) risk, estimated from markup and not measured | 1 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | Visible text is under 3% of the HTML on 6/49 sampled pages | 6 |
| F-014 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 3/49 sampled pages | 3 |
| F-015 | Improvement opportunity | low | suspected (likely, not proven) | Pages lack a descriptive primary heading (H1) that says what the page is about | 3 |
| F-016 | Improvement opportunity | low | suspected (likely, not proven) | Visible breadcrumbs lack matching BreadcrumbList structured data | 5 |
| F-017 | Improvement opportunity | low | suspected (likely, not proven) | No rel=canonical tag on 49/49 sampled pages | 49 |
| F-018 | Improvement opportunity | low | suspected (likely, not proven) | Pages show questions, steps or ratings without matching markup | 5 |
| F-019 | Improvement opportunity | low | suspected (likely, not proven) | Most images have no width and height on 1/49 sampled pages | 1 |
| F-020 | Improvement opportunity | low | suspected (likely, not proven) | No XML sitemap found | 1 |
| F-021 | Improvement opportunity | low | suspected (likely, not proven) | No review or directory profile is linked from the site | 3 |
| F-022 | Improvement opportunity | low | not enough evidence to judge | Some near-empty pages could not be confirmed as rendering gaps | 1 |

## Finding details

### F-001: Images are heavier than they need to be

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.90; Check: `image-weight`; Seen on 2 of 49 analyzed page(s)

**Why it matters:** Large, oversized or legacy-format image files delay the largest paint and cost mobile visitors data, so visitors arriving from search or an AI answer wait longer

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/blog/svelte-and-typescript>

**Evidence:**

- https://svelte.dev/\_app/immutable/assets/svelte-machine-mobile.DtvNEgov.png: the file is 314 KB; it is served as PNG although the request accepted AVIF and WebP (likely the largest image on the page)
  - <https://svelte.dev/>
- https://svelte.dev/media/svelte-ts.png: it is served as PNG although the request accepted AVIF and WebP (likely the largest image on the page)
  - <https://svelte.dev/blog/svelte-and-typescript>

**What to do:** Compress, resize and convert the listed images

1. Serve AVIF or WebP, with JPEG or PNG only as a fallback in &lt;picture&gt;
2. Resize each image to the largest size it is displayed at and add srcset and sizes for smaller screens
3. Compress photos, aiming for under 200 KB for the largest image of a page

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Faster largest paint and less data for visitors on mobile

**How to check the fix:** Re-run the audit and confirm the listed images are smaller

### F-002: No structured data (JSON-LD) found on any crawled page

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.85; Check: `no-jsonld`; Seen on 49 of 49 analyzed page(s)

**Why it matters:** Pages lack schema.org JSON-LD markup (observed on the 49 of 571 discovered pages that were actually crawled)

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/apps>
- <https://svelte.dev/blog>
- <https://svelte.dev/blog/accelerating-sveltes-development>
- <https://svelte.dev/blog/advent-of-svelte>
- <https://svelte.dev/blog/advent-of-svelte-is-back>
- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/cves-affecting-the-svelte-ecosystem>
- <https://svelte.dev/blog/frameworks-without-the-framework>
- <https://svelte.dev/blog/hacktoberfest>
- and 39 more

**Evidence:**

- 0/49 pages contain JSON-LD
  - <https://svelte.dev/>
  - <https://svelte.dev/blog>
  - <https://svelte.dev/docs>
  - <https://svelte.dev/docs/ai>
  - <https://svelte.dev/docs/cli>
  - and 5 more

**What to do:** Add Organization/Product/Article JSON-LD to key pages

1. Identify page types
2. Add matching schema.org JSON-LD blocks

Effort: medium; Impact: medium; Major project: real value, plan the work.

**Expected benefit:** Key facts are also stated as explicit structured data; no ranking or citation gain is implied

**How to check the fix:** Validate JSON-LD with a schema.org validator

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- Home page https://svelte.dev/ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://svelte.dev/#organization",
      "name": "Svelte",
      "url": "https://svelte.dev/",
      "logo": "https://svelte.dev/favicon.png",
      "description": "Web development for the rest of us",
      "sameAs": [
        "https://bsky.app/profile/svelte.dev",
        "https://github.com/sveltejs",
        "https://github.com/Rich-Harris",
        "https://github.com/benmccann",
        "https://github.com/jycouet",
        "https://github.com/dummdidumm",
        "https://github.com/paoloricciuti",
        "https://github.com/Conduitry",
        "https://github.com/teemingc",
        "https://github.com/manuel3108"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://svelte.dev/#website",
      "name": "Svelte",
      "url": "https://svelte.dev/",
      "publisher": {
        "@id": "https://svelte.dev/#organization"
      }
    }
  ]
}
</script>

<!-- Other page https://svelte.dev/apps -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://svelte.dev/apps",
  "name": "Your apps • Svelte",
  "description": "REPLACE_WITH_PAGE_DESCRIPTION",
  "about": {
    "@id": "https://svelte.dev/#organization"
  }
}
</script>

<!-- Listing page https://svelte.dev/blog -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "url": "https://svelte.dev/blog",
  "name": "Blog",
  "description": "Articles about Svelte and UI development",
  "about": {
    "@id": "https://svelte.dev/#organization"
  }
}
</script>

<!-- Article page https://svelte.dev/blog/accelerating-sveltes-development -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "url": "https://svelte.dev/blog/accelerating-sveltes-development",
  "headline": "Accelerating Svelte’s Development",
  "description": "Scaling the team, building partnerships, and growing the community",
  "image": "https://svelte.dev/blog/accelerating-sveltes-development/card.png",
  "author": {
    "@type": "Person",
    "name": "REPLACE_WITH_AUTHOR_NAME",
    "url": "REPLACE_WITH_AUTHOR_PAGE_URL"
  },
  "datePublished": "REPLACE_WITH_ISO_DATE",
  "dateModified": "REPLACE_WITH_ISO_DATE",
  "publisher": {
    "@id": "https://svelte.dev/#organization"
  }
}
</script>
```

Replace before publishing: `REPLACE_WITH_AUTHOR_NAME`, `REPLACE_WITH_AUTHOR_PAGE_URL`, `REPLACE_WITH_ISO_DATE`, `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-003: Form fields have no label

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.85; Check: `form-label-missing`; Seen on 1 of 49 analyzed page(s)

**Why it matters:** A field with no label, aria-label or title has no name in the accessibility tree, so screen-reader users and AI agents filling the form cannot tell what it asks for

**Pages:**

- <https://svelte.dev/playground>

**Evidence:**

- 1 unlabeled field(s): &lt;input type=text&gt;
  - <https://svelte.dev/playground>

**What to do:** Give every form field a visible label tied to it

1. Add &lt;label for="field-id"&gt; with visible text for each field, or wrap the field in &lt;label&gt;
2. Use aria-label only where a visible label is impossible; a placeholder is not a label

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Visitors using assistive technology, and AI agents that act through the accessibility tree, can identify and use the affected elements

**How to check the fix:** Re-run the audit and check the pages with a screen reader or an accessibility checker

### F-004: Video or audio is embedded without complete VideoObject or AudioObject markup

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `media-schema-missing`; Seen on 9 of 49 analyzed page(s)

**Why it matters:** Without VideoObject or AudioObject markup, search engines and assistants have no machine-readable title, description, thumbnail or date for the media

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/runes>
- <https://svelte.dev/blog/sv-the-svelte-cli>
- <https://svelte.dev/blog/svelte-3-rethinking-reactivity>
- <https://svelte.dev/blog/svelte-5-release-candidate>
- <https://svelte.dev/blog/svelte-on-the-changelog>
- <https://svelte.dev/blog/the-zen-of-just-writing-css>
- <https://svelte.dev/blog/view-transitions>

**Evidence:**

- video with no VideoObject markup
  - <https://svelte.dev/>
- video with no VideoObject markup
  - <https://svelte.dev/blog/announcing-sveltekit-1.0>
- video with no VideoObject markup
  - <https://svelte.dev/blog/runes>
- video with no VideoObject markup
  - <https://svelte.dev/blog/sv-the-svelte-cli>
- video with no VideoObject markup
  - <https://svelte.dev/blog/svelte-3-rethinking-reactivity>
- and 4 more observations in the JSON report

**What to do:** Describe each video and audio clip with VideoObject or AudioObject JSON-LD

1. Add VideoObject markup with name, description, thumbnailUrl, uploadDate and duration
2. Use AudioObject or PodcastEpisode markup for audio
3. Add the transcript property where a transcript exists

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Media becomes eligible for video results and its details are quotable

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-005: Some pages lack semantic headings

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `no-headings`; Seen on 1 of 49 analyzed page(s)

**Why it matters:** Pages have no h1-h6 elements

**Pages:**

- <https://svelte.dev/playground>

**Evidence:**

- 1 pages have no headings
  - <https://svelte.dev/playground>

**What to do:** Add semantic heading structure

1. Add an h1 per page
2. Structure sections with h2/h3

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves text extraction quality

**How to check the fix:** Inspect DOM for heading tags

### F-006: Article authors lack a Person profile or credentials

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `author-credentials-weak`; Seen on 33 of 49 analyzed page(s)

**Why it matters:** The article author is not stated as a Person with a profile and credentials, so the expertise behind the content cannot be checked

**Pages:**

- <https://svelte.dev/blog/accelerating-sveltes-development>
- <https://svelte.dev/blog/advent-of-svelte>
- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/cves-affecting-the-svelte-ecosystem>
- <https://svelte.dev/blog/frameworks-without-the-framework>
- <https://svelte.dev/blog/runes>
- <https://svelte.dev/blog/sapper-towards-the-ideal-web-app-framework>
- <https://svelte.dev/blog/streaming-snapshots-sveltekit>
- <https://svelte.dev/blog/sv-the-svelte-cli>
- <https://svelte.dev/blog/svelte-3-rethinking-reactivity>
- and 23 more

**Evidence:**

- the byline is not stated in Article markup (no author property)
  - <https://svelte.dev/blog/accelerating-sveltes-development>
- the byline is not stated in Article markup (no author property)
  - <https://svelte.dev/blog/advent-of-svelte>
- the byline is not stated in Article markup (no author property)
  - <https://svelte.dev/blog/announcing-sveltekit-1.0>
- the byline is not stated in Article markup (no author property)
  - <https://svelte.dev/blog/cves-affecting-the-svelte-ecosystem>
- the byline is not stated in Article markup (no author property)
  - <https://svelte.dev/blog/frameworks-without-the-framework>
- and 5 more observations in the JSON report

**What to do:** State each article author as a Person with a profile and credentials

1. Type the Article author as a Person, not a plain string or the Organization
2. Give the Person a url to an author page and sameAs links to professional profiles
3. Add jobTitle, description or knowsAbout that state the author's expertise
4. Show the same author name in the visible byline

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** The expertise behind each article becomes explicit and checkable

**How to check the fix:** Validate the Article markup and re-run the audit

### F-007: Video or audio has no transcript that crawlers can read

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `media-transcript-missing`; Seen on 8 of 49 analyzed page(s)

**Why it matters:** Crawlers and assistants do not watch or listen, so what is said in a video or podcast is invisible to them unless a transcript is on or linked from the page

**Pages:**

- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/runes>
- <https://svelte.dev/blog/sv-the-svelte-cli>
- <https://svelte.dev/blog/svelte-3-rethinking-reactivity>
- <https://svelte.dev/blog/svelte-5-release-candidate>
- <https://svelte.dev/blog/svelte-on-the-changelog>
- <https://svelte.dev/blog/the-zen-of-just-writing-css>
- <https://svelte.dev/blog/view-transitions>

**Evidence:**

- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://svelte.dev/blog/announcing-sveltekit-1.0>
- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://svelte.dev/blog/runes>
- No transcript in the page text or links; YouTube embed: captions inside the player not checked; YouTube embed: captions inside the player not checked
  - <https://svelte.dev/blog/sv-the-svelte-cli>
- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://svelte.dev/blog/svelte-3-rethinking-reactivity>
- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://svelte.dev/blog/svelte-5-release-candidate>
- and 3 more observations in the JSON report

**What to do:** Publish a transcript with each video and audio clip

1. Add the full transcript as text on the page, or link to it from next to the player
2. Add a captions track (WebVTT) to native video players and enable captions on embeds
3. Include the transcript in the VideoObject or AudioObject transcript property

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** What the video or audio says becomes quotable text

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-008: Open Graph tags missing: og:description on 49/49 sampled pages, og:title on 48/49 sampled pages, og:url on 48/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `social-metadata`; Seen on 49 of 49 analyzed page(s)

**Why it matters:** Incomplete Open Graph metadata limits available shared-link preview hints.

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/apps>
- <https://svelte.dev/blog>
- <https://svelte.dev/blog/accelerating-sveltes-development>
- <https://svelte.dev/blog/advent-of-svelte>
- <https://svelte.dev/blog/advent-of-svelte-is-back>
- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/cves-affecting-the-svelte-ecosystem>
- <https://svelte.dev/blog/frameworks-without-the-framework>
- <https://svelte.dev/blog/hacktoberfest>
- and 39 more

**Evidence:**

- Missing nonempty fields: og:title, og:description, og:url
  - <https://svelte.dev/>
- Missing nonempty fields: og:title, og:description, og:url
  - <https://svelte.dev/blog>
- Missing nonempty fields: og:title, og:description, og:url
  - <https://svelte.dev/docs>
- Missing nonempty fields: og:title, og:description, og:url
  - <https://svelte.dev/docs/ai>
- Missing nonempty fields: og:title, og:description, og:url
  - <https://svelte.dev/docs/cli>
- and 5 more observations in the JSON report

**What to do:** Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

1. Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides preview candidates; image availability and platform rendering still need verification.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://svelte.dev/ -->
<meta property="og:title" content="Svelte • Web development for the rest of us">
<meta property="og:description" content="Web development for the rest of us">
<meta property="og:url" content="https://svelte.dev/">

<!-- https://svelte.dev/apps -->
<meta property="og:title" content="Your apps • Svelte">
<meta property="og:description" content="REPLACE_WITH_PAGE_DESCRIPTION">
<meta property="og:url" content="https://svelte.dev/apps">

<!-- https://svelte.dev/blog -->
<meta property="og:title" content="Blog • Svelte">
<meta property="og:description" content="Articles about Svelte and UI development">
<meta property="og:url" content="https://svelte.dev/blog">
```

Replace before publishing: `REPLACE_WITH_PAGE_DESCRIPTION`

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-009: Heading levels are skipped on 4/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 4 of 49 analyzed page(s)

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://svelte.dev/docs/ai>
- <https://svelte.dev/docs/cli>
- <https://svelte.dev/docs/kit>
- <https://svelte.dev/docs/svelte>

**Evidence:**

- Observed heading levels: \[3, 3, 3, 3, 3, 3, 1, 3\]
  - <https://svelte.dev/docs/ai>
- Observed heading levels: \[3, 3, 3, 3, 1, 3, 2, 2\]
  - <https://svelte.dev/docs/cli>
- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 2, 2, 2, 2\]
  - <https://svelte.dev/docs/kit>
- Observed heading levels: \[3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3\]
  - <https://svelte.dev/docs/svelte>

**What to do:** Review the outline and nest headings according to the document hierarchy.

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-010: No meta description on 3/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `missing-description`; Seen on 3 of 49 analyzed page(s)

**Why it matters:** An absent description removes an optional page summary hint.

**Pages:**

- <https://svelte.dev/apps>
- <https://svelte.dev/docs>
- <https://svelte.dev/tutorial>

**Evidence:**

- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://svelte.dev/docs>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://svelte.dev/apps>
- No nonempty meta description was observed; a search engine can still extract a summary.
  - <https://svelte.dev/tutorial>

**What to do:** Write a concise page-specific meta description that matches visible content.

1. Write a concise page-specific meta description that matches visible content.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Provides a summary candidate; search engines may choose other text.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-011: The main image of a page has no responsive variants

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `responsive-images`; Seen on 3 of 49 analyzed page(s)

**Why it matters:** Without srcset or &lt;picture&gt; sources, phones download the same large file as desktops, which delays the largest paint on mobile

**Pages:**

- <https://svelte.dev/blog/svelte-and-typescript>
- <https://svelte.dev/blog/sveltekit-2>
- <https://svelte.dev/blog/virtual-dom-is-pure-overhead>

**Evidence:**

- First content image https://svelte.dev/media/svelte-ts.png has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://svelte.dev/blog/svelte-and-typescript>
- First content image https://svelte.dev/media/framework-poll.webp has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://svelte.dev/blog/sveltekit-2>
- First content image https://svelte.dev/media/rethinking-best-practices.jpg has no srcset and no &lt;picture&gt; source; actual file size was not measured unless listed under image-weight
  - <https://svelte.dev/blog/virtual-dom-is-pure-overhead>

**What to do:** Add srcset and sizes to the main image of each page

1. Generate the image at several widths and list them in srcset with a sizes attribute
2. Use &lt;picture&gt; with AVIF or WebP sources where the format matters

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Each screen downloads an image no larger than it needs

**How to check the fix:** Re-run the audit and confirm the pages are no longer listed

### F-012: Likely Cumulative Layout Shift (CLS) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 1 of 49 analyzed page(s)

**Why it matters:** Markup patterns that let content move during loading were observed: layout may shift

**Pages:**

- <https://svelte.dev/>

**Evidence:**

- Estimate, not a measurement: 1 video or iframe embed(s) without reserved size; the first content image has no width and height
  - <https://svelte.dev/>

**What to do:** Check CLS in a browser or with field data, and remove the listed patterns

1. Give every image, video and iframe width and height attributes or a CSS aspect-ratio
2. Reserve space for embeds, banners and late-loading content
3. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Cumulative Layout Shift score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-013: Visible text is under 3% of the HTML on 6/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `markup-ratio`; Seen on 6 of 49 analyzed page(s)

**Why it matters:** A small visible-text share in a large HTML document can indicate excess markup.

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/blog/advent-of-svelte-is-back>
- <https://svelte.dev/blog/svelte-on-the-changelog>
- <https://svelte.dev/docs>
- <https://svelte.dev/docs/ai>
- <https://svelte.dev/docs/cli>

**Evidence:**

- Visible text represents 2.4% of decoded HTML body bytes. This is not a ranking metric.
  - <https://svelte.dev/>
- Visible text represents 2.8% of decoded HTML body bytes. This is not a ranking metric.
  - <https://svelte.dev/docs>
- Visible text represents 2.5% of decoded HTML body bytes. This is not a ranking metric.
  - <https://svelte.dev/docs/ai>
- Visible text represents 2.3% of decoded HTML body bytes. This is not a ranking metric.
  - <https://svelte.dev/docs/cli>
- Visible text represents 1.5% of decoded HTML body bytes. This is not a ranking metric.
  - <https://svelte.dev/blog/advent-of-svelte-is-back>
- and 1 more observations in the JSON report

**What to do:** Inspect inline assets and template boilerplate before trimming unnecessary HTML.

1. Inspect inline assets and template boilerplate before trimming unnecessary HTML.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Reduces document overhead if the sampled ratio reflects avoidable markup.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-014: Title shorter than 15 or longer than 70 characters on 3/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 3 of 49 analyzed page(s)

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://svelte.dev/blog>
- <https://svelte.dev/blog/the-omnisite>
- <https://svelte.dev/docs>

**Evidence:**

- Title has 13 characters: Blog • Svelte. Display width was not measured.
  - <https://svelte.dev/blog>
- Title has 13 characters: Docs • Svelte. Display width was not measured.
  - <https://svelte.dev/docs>
- Title has 12 characters: The Omnisite. Display width was not measured.
  - <https://svelte.dev/blog/the-omnisite>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-015: Pages lack a descriptive primary heading (H1) that says what the page is about

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `h1`; Seen on 3 of 49 analyzed page(s)

**Why it matters:** No H1 was found on these sampled pages.

**Pages:**

- <https://svelte.dev/apps>
- <https://svelte.dev/playground>
- <https://svelte.dev/tutorial>

**Evidence:**

- No H1 was found on these sampled pages.
  - <https://svelte.dev/apps>
  - <https://svelte.dev/playground>
  - <https://svelte.dev/tutorial>
- Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.
  - <https://svelte.dev/tutorial>

**What to do:** Add a descriptive primary heading where a clear page title is missing

1. Add a descriptive primary heading where a clear page title is missing

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-016: Visible breadcrumbs lack matching BreadcrumbList structured data

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.65; Check: `breadcrumb-mismatch`; Seen on 5 of 49 analyzed page(s)

Reported as suspected: its confidence (0.65) is below the 0.7 a confirmed finding needs.

**Why it matters:** Breadcrumb navigation is visible but not machine-readable

**Pages:**

- <https://svelte.dev/docs/ai>
- <https://svelte.dev/docs/cli>
- <https://svelte.dev/docs/kit>
- <https://svelte.dev/docs/svelte>
- <https://svelte.dev/tutorial>

**Evidence:**

- Visible breadcrumb without schema
  - <https://svelte.dev/docs/ai>
  - <https://svelte.dev/docs/cli>
  - <https://svelte.dev/docs/kit>
  - <https://svelte.dev/docs/svelte>
  - <https://svelte.dev/tutorial>

**What to do:** Add BreadcrumbList JSON-LD matching visible breadcrumbs

1. Add BreadcrumbList schema to pages with visible breadcrumbs

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves machine understanding of site structure

**How to check the fix:** Validate BreadcrumbList JSON-LD

### F-017: No rel=canonical tag on 49/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `missing-canonical`; Seen on 49 of 49 analyzed page(s)

**Why it matters:** A missing canonical declaration provides no explicit preferred-URL hint.

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/apps>
- <https://svelte.dev/blog>
- <https://svelte.dev/blog/accelerating-sveltes-development>
- <https://svelte.dev/blog/advent-of-svelte>
- <https://svelte.dev/blog/advent-of-svelte-is-back>
- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/cves-affecting-the-svelte-ecosystem>
- <https://svelte.dev/blog/frameworks-without-the-framework>
- <https://svelte.dev/blog/hacktoberfest>
- and 39 more

**Evidence:**

- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://svelte.dev/>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://svelte.dev/blog>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://svelte.dev/docs>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://svelte.dev/docs/ai>
- No rel=canonical declaration observed. Duplicate content was not established.
  - <https://svelte.dev/docs/cli>
- and 5 more observations in the JSON report

**What to do:** Assess real duplicates before declaring the correct absolute canonical URL.

1. Assess real duplicates before declaring the correct absolute canonical URL.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Helps supporting consumers consolidate duplicate URLs when applicable.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

**Ready-to-paste fix:**

Where: Inside &lt;head&gt; of each page named in the comments

```html
<!-- https://svelte.dev/ -->
<link rel="canonical" href="https://svelte.dev/">

<!-- https://svelte.dev/apps -->
<link rel="canonical" href="https://svelte.dev/apps">

<!-- https://svelte.dev/blog -->
<link rel="canonical" href="https://svelte.dev/blog">
```

Generated from the audited pages. Check every value against the live page, replace each REPLACE\_WITH\_ placeholder, and validate before publishing.

### F-018: Pages show questions, steps or ratings without matching markup

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `citation-schema-opportunity`; Seen on 5 of 49 analyzed page(s)

**Why it matters:** Questions, numbered steps and ratings are visible on the page but are not stated as FAQPage, HowTo or AggregateRating markup

**Pages:**

- <https://svelte.dev/blog/announcing-sveltekit-1.0>
- <https://svelte.dev/blog/svelte-5-is-alive>
- <https://svelte.dev/blog/svelte-5-release-candidate>
- <https://svelte.dev/blog/svelte-and-typescript>
- <https://svelte.dev/blog/virtual-dom-is-pure-overhead>

**Evidence:**

- 5 question-shaped H2/H3 headings with no FAQPage markup
  - <https://svelte.dev/blog/announcing-sveltekit-1.0>
- 4 question-shaped H2/H3 headings with no FAQPage markup
  - <https://svelte.dev/blog/svelte-5-is-alive>
- 3 question-shaped H2/H3 headings with no FAQPage markup
  - <https://svelte.dev/blog/svelte-5-release-candidate>
- 4 question-shaped H2/H3 headings with no FAQPage markup
  - <https://svelte.dev/blog/svelte-and-typescript>
- 5 question-shaped H2/H3 headings with no FAQPage markup
  - <https://svelte.dev/blog/virtual-dom-is-pure-overhead>

**What to do:** Mark up visible questions, steps and ratings where the content really is that

1. Add FAQPage markup only for genuine question-and-answer sections shown on the page
2. Add HowTo markup for real step-by-step instructions
3. Add AggregateRating to Product or Service markup only when the ratings shown are real customer ratings

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Assistants can lift answers, steps and ratings as explicit facts

**How to check the fix:** Validate the pages with a schema.org validator and re-run the audit

### F-019: Most images have no width and height on 1/49 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `image-sizing`; Seen on 1 of 49 analyzed page(s)

**Why it matters:** Images without dimensions may lack reserved space unless CSS already supplies it.

**Pages:**

- <https://svelte.dev/packages>

**Evidence:**

- 11/11 images lack positive width/height attributes; no lazy hints. CSS dimensions and viewport positions were not measured.
  - <https://svelte.dev/packages>

**What to do:** Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

1. Check CSS sizing and aspect-ratio before adding width and height; lazy-load only suitable below-fold images.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Can reduce layout movement and unnecessary loading; layout shift is not measured.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-020: No XML sitemap found

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `sitemap-unavailable`; Seen on 1 of 49 analyzed page(s)

**Why it matters:** Without a discovered sitemap, this audit relies more heavily on sampled links.

**Pages:**

- <https://svelte.dev/>

**Evidence:**

- Sitemap probe status: absent; checked: https://svelte.dev/sitemap.xml (absent). No additional sitemap discovery was attempted by this check.
  - <https://svelte.dev/>

**What to do:** If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

1. If appropriate, publish a valid sitemap of canonical public pages and reference it in robots.txt.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves inventory discovery; absence is not a universal indexing defect.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-021: No review or directory profile is linked from the site

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.55; Check: `review-platform-missing`; Seen on 3 of 49 analyzed page(s)

**Why it matters:** Assistants answer 'is this brand any good?' from review and directory platforms; a brand with no linked review profile leaves them nothing to corroborate it with

**Pages:**

- <https://svelte.dev/>
- <https://svelte.dev/blog>
- <https://svelte.dev/docs>

**Evidence:**

- None of the 49 crawled page(s) or the sameAs links point to a review or directory profile; whether profiles exist off-site was not searched
  - <https://svelte.dev/>
  - <https://svelte.dev/blog>
  - <https://svelte.dev/docs>

**What to do:** Claim and link review profiles that fit the business, such as Trustpilot, the Better Business Bureau, Crunchbase or an industry directory

1. Claim or create profiles on review platforms that fit the business (Trustpilot, the Better Business Bureau, Crunchbase or an industry directory)
2. Link them from the site footer and list them in Organization sameAs
3. Ask real customers for reviews and answer them publicly

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Independent ratings and reviews corroborate the brand in assistant answers

**How to check the fix:** Re-run the audit after the links or profiles change

### F-022: Some near-empty pages could not be confirmed as rendering gaps

Type: Improvement opportunity; Severity: low; Status: not enough evidence to judge; Confidence: 0.30; Check: `render-gap-unconfirmed`; Seen on 1 of 49 analyzed page(s)

**Why it matters:** These pages run scripts and carry little text in their raw HTML, but show no other sign of client-side rendering (no app mount point, framework bundle, serialized page state or JavaScript-required notice); they may simply be short pages

**Pages:**

- <https://svelte.dev/apps>

**Evidence:**

- Little raw-HTML text and no sign of client-side rendering
  - <https://svelte.dev/apps>

**What to do:** Open these pages with JavaScript turned off and check that the content visitors need is still there

1. Compare each page in a browser with and without JavaScript
2. If content disappears, server-render or pre-render it

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Clarifies whether a real rendering fix is needed

**How to check the fix:** Manual inspection

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **llms.txt is present and well formed.** /llms.txt is present, follows the llms.txt format and lists 7 links.
- **Pages are served over HTTPS.** All 49 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 49 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 49 pages checked have a document title.
- **Every page declares its language.** All 49 pages checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 49 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Mobile viewport is declared and zoom is allowed.** All 49 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 35 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
- **Every page links onward.** Each of the 49 pages crawled links to at least one other page on the site.

## Agent checks

Received: outcome envelope. Assessed: 1 of 6 (partial). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | passed | The About page was not discovered, so the home page passage was judged. It names the project (Svelte), what it offers (a UI framework that uses a compiler to build components) and its category (web development framework). |
| AG-02 Independent mentions | not assessed | No search tool was run in this invocation. |
| AG-03 Independent contradiction | not assessed | No search tool was run in this invocation. |
| AG-04 Facts drawn inside images | not assessed | Image viewing was not used in this invocation. |
| AG-05 Namesake ambiguity | not assessed | No search tool was run in this invocation. |
| AG-06 Review and profile opportunity | not assessed | No search tool was run in this invocation. |

## What this audit could not check

- 515 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 571 discovered); findings reflect only the 50 page(s) actually crawled, not the whole site. The sample reached 7 of 11 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- 1 image(s) whose file name or alt text suggests prices, hours or specifications were not read: the scripts never interpret raster pixels, and the agent vision stage (AG-04) was not supplied, so facts inside those images are suspected, not confirmed.
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 2 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.
- Agent check AG-02 (Independent mentions) was not assessed: No search tool was run in this invocation.
- Agent check AG-03 (Independent contradiction) was not assessed: No search tool was run in this invocation.
- Agent check AG-04 (Facts drawn inside images) was not assessed: Image viewing was not used in this invocation.
- Agent check AG-05 (Namesake ambiguity) was not assessed: No search tool was run in this invocation.
- Agent check AG-06 (Review and profile opportunity) was not assessed: No search tool was run in this invocation.

## Notes from the run

- Entity identity unresolved; corroboration suppressed.
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- 1/49 sampled pages carry too little text in their raw HTML to judge comparison tables and specification lists: their content is probably built by JavaScript, so these checks did not assess them.
- 1/49 sampled pages carry too little text in their raw HTML to judge location and audience signals: their content is probably built by JavaScript, so these checks did not assess them.
- 1/49 sampled pages carry too little text in their raw HTML to judge site search and saved items: their content is probably built by JavaScript, so these checks did not assess them.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
