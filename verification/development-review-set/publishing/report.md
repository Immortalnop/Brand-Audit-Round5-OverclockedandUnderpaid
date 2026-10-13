# Brand AI-Readiness Audit: https://www.propublica.org/

- **Audited at:** 2026-10-13T03:15:19.373212+00:00
- **Run:** Completed
- **Pages:** 6 analyzed of 163 discovered; 2 of 37 site sections reached
- **Run time:** 10.3 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 17 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.05)

Confidence is low (0.05). The weakest of its parts sets the score, here the page sample. The page sample is small or one-sided: the crawl analyzed 6 of 163 discovered page(s) and reached 2 of 37 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). Brand identity (reported separately, not part of the score): The brand identity is clear: the Organization markup names one brand. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.05 | The page sample is small or one-sided: the crawl analyzed 6 of 163 discovered page(s) and reached 2 of 37 site section(s); the crawl is known to have missed URLs (a crawl or sitemap read limit, or URLs left unfetched). |
| Brand identity (not in the score) | 0.92 | The brand identity is clear: the Organization markup names one brand. |
| Audit run | 1.00 | The audit run completed normally. |

## Summary

| | Count |
| --- | --- |
| Findings | 13 |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 13 |
| Improvement suggestions (not defects) | 12 |
| Not enough evidence to judge | 0 |
| Recommendations | 13 |

## Start here

**F-001: Images are heavier than they need to be**

Compress, resize and convert the listed images

Impact low, effort medium. Details are under F-001 below.

## Top actions

Defects only; improvement opportunities are listed with the findings. Roles are suggestions.

| # | Finding | Action | Priority | Impact | Effort | Quick win | Suggested roles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-001: Images are heavier than they need to be | Compress, resize and convert the listed images | low | low | medium | no | developer, seo |

## Quick wins

Valuable changes that take little work:

- **F-002: Organization markup does not link the brand to a knowledge-graph entity.** Link the brand to its Wikidata item in Organization sameAs (impact medium, effort low)
- **F-004: Article authors lack a Person profile or credentials.** State each article author as a Person with a profile and credentials (impact medium, effort low)

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Defect | low | confirmed | Images are heavier than they need to be | 2 |
| F-002 | Improvement opportunity | low | confirmed | Organization markup does not link the brand to a knowledge-graph entity | 6 |
| F-003 | Improvement opportunity | low | confirmed | Video or audio is embedded without complete VideoObject or AudioObject markup | 2 |
| F-004 | Improvement opportunity | low | confirmed | Article authors lack a Person profile or credentials | 5 |
| F-005 | Improvement opportunity | low | confirmed | Video or audio has no transcript that crawlers can read | 2 |
| F-006 | Improvement opportunity | low | suspected (likely, not proven) | Likely Interaction to Next Paint (INP) risk, estimated from markup and not measured | 6 |
| F-007 | Improvement opportunity | low | suspected (likely, not proven) | Heading levels are skipped on 2/6 sampled pages | 2 |
| F-008 | Improvement opportunity | low | suspected (likely, not proven) | Likely Largest Contentful Paint (LCP) risk, estimated from markup and not measured | 1 |
| F-009 | Improvement opportunity | low | suspected (likely, not proven) | Title shorter than 15 or longer than 70 characters on 4/6 sampled pages | 4 |
| F-010 | Improvement opportunity | low | suspected (likely, not proven) | Visible text is under 3% of the HTML on 1/6 sampled pages | 1 |
| F-011 | Improvement opportunity | low | suspected (likely, not proven) | Content pages lack a clear orientation heading above the fold | 1 |
| F-012 | Improvement opportunity | low | suspected (likely, not proven) | No question-shaped headings on 3/3 content pages | 3 |
| F-013 | Improvement opportunity | low | suspected (likely, not proven) | Canonical tag points to another site on 1/6 sampled pages | 1 |

## Finding details

### F-001: Images are heavier than they need to be

Type: Defect; Severity: low; Status: confirmed; Confidence: 0.90; Check: `image-weight`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.9; 2 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Large, oversized or legacy-format image files delay the largest paint and cost mobile visitors data, so visitors arriving from search or an AI answer wait longer

**Pages:**

- <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>

**Evidence:**

- https://www.propublica.org/wp-content/uploads/2026/10/D5612E06-F25D-4891-8753-A68B9ABB663C\_d64c8e.jpg: the file is 479 KB (likely the largest image on the page)
  - <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>
- https://www.propublica.org/wp-content/uploads/2026/09/20260507-Sanchez-Family-Homelessness-106.jpg?w=2560: the file is 303 KB (likely the largest image on the page)
  - <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>

**What to do:** Compress, resize and convert the listed images

**Suggested roles:** developer, seo

1. Serve AVIF or WebP, with JPEG or PNG only as a fallback in &lt;picture&gt;
2. Resize each image to the largest size it is displayed at and add srcset and sizes for smaller screens
3. Compress photos, aiming for under 200 KB for the largest image of a page

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Faster largest paint and less data for visitors on mobile

**How to check the fix:** Re-run the audit and confirm the listed images are smaller

### F-002: Organization markup does not link the brand to a knowledge-graph entity

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `kg-link-missing`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 6 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** No Wikidata or Wikipedia link is declared, so nothing ties the brand to one knowledge-graph entity

**Pages:**

- <https://www.propublica.org/>
- <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>
- <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
- <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>

**Evidence:**

- Organization markup on 6 page(s) declares sameAs: https://www.facebook.com/propublica, https://x.com/propublica, https://newsie.social/@ProPublica; none names a Wikidata item or Wikipedia article
  - <https://www.propublica.org/>
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
  - <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>
  - <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>
  - and 1 more

**What to do:** Link the brand to its Wikidata item in Organization sameAs

**Suggested roles:** developer, seo

1. Find the brand's Wikidata item, or create one if the organization meets Wikidata's notability policy (public, serious references)
2. Add the item URL (and the Wikipedia article, if one exists) to Organization sameAs
3. Make sure the item lists this site as its official website (P856)

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** Assistants can tell the brand apart from same-named entities

**How to check the fix:** Re-run the audit after the markup or the knowledge-graph entry changes

### F-003: Video or audio is embedded without complete VideoObject or AudioObject markup

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.80; Check: `media-schema-missing`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.8; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Without VideoObject or AudioObject markup, search engines and assistants have no machine-readable title, description, thumbnail or date for the media

**Pages:**

- <https://www.propublica.org/>
- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**Evidence:**

- video with no VideoObject markup
  - <https://www.propublica.org/>
- video with no VideoObject markup
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**What to do:** Describe each video and audio clip with VideoObject or AudioObject JSON-LD

**Suggested roles:** developer, seo

1. Add VideoObject markup with name, description, thumbnailUrl, uploadDate and duration
2. Use AudioObject or PodcastEpisode markup for audio
3. Add the transcript property where a transcript exists

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Media becomes eligible for video results and its details are quotable

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-004: Article authors lack a Person profile or credentials

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `author-credentials-weak`; Seen on 5 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.75; 5 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** The article author is not stated as a Person with a profile and credentials, so the expertise behind the content cannot be checked

**Pages:**

- <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>
- <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
- <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>

**Evidence:**

- author Jake Pearson has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential); author Lisa Riordan Seville has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential)
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
- author Ryan Devereaux has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential)
  - <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>
- author Nicole Santa Cruz has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential); author Zaydee Sanchez has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential)
  - <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- author Zach Despart has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential)
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- author Aaron Davis has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential); author Robert Faturechi has no credentials in markup (jobTitle, description, knowsAbout, alumniOf, award or hasCredential)
  - <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>

**What to do:** State each article author as a Person with a profile and credentials

**Suggested roles:** content, developer, seo

1. Type the Article author as a Person, not a plain string or the Organization
2. Give the Person a url to an author page and sameAs links to professional profiles
3. Add jobTitle, description or knowsAbout that state the author's expertise
4. Show the same author name in the visible byline

Effort: low; Impact: medium; Quick win: real value for little work; start here.

**Expected benefit:** The expertise behind each article becomes explicit and checkable

**How to check the fix:** Validate the Article markup and re-run the audit

### F-005: Video or audio has no transcript that crawlers can read

Type: Improvement opportunity; Severity: low; Status: confirmed; Confidence: 0.75; Check: `media-transcript-missing`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, confirmed status, confidence 0.75; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Crawlers and assistants do not watch or listen, so what is said in a video or podcast is invisible to them unless a transcript is on or linked from the page

**Pages:**

- <https://www.propublica.org/>
- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**Evidence:**

- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://www.propublica.org/>
- No transcript in the page text or links; YouTube embed: captions inside the player not checked
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**What to do:** Publish a transcript with each video and audio clip

**Suggested roles:** developer, seo

1. Add the full transcript as text on the page, or link to it from next to the player
2. Add a captions track (WebVTT) to native video players and enable captions on embeds
3. Include the transcript in the VideoObject or AudioObject transcript property

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** What the video or audio says becomes quotable text

**How to check the fix:** Re-run the audit and confirm the affected pages are no longer listed

### F-006: Likely Interaction to Next Paint (INP) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 6 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 6 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Markup patterns that load heavy JavaScript were observed: the page may respond slowly to input

**Pages:**

- <https://www.propublica.org/>
- <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>
- <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
- <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>

**Evidence:**

- Estimate, not a measurement: 68 external scripts
  - <https://www.propublica.org/>
- Estimate, not a measurement: 70 external scripts
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
- Estimate, not a measurement: 68 external scripts
  - <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>
- Estimate, not a measurement: 71 external scripts
  - <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- Estimate, not a measurement: 70 external scripts
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- and 1 more observations in the JSON report

**What to do:** Check INP in a browser or with field data, and remove the listed patterns

**Suggested roles:** developer, seo

1. Remove unused scripts and third-party tags
2. Split long JavaScript tasks and defer work that is not needed for the first interaction
3. Move large inline scripts to cached external files loaded with defer
4. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Interaction to Next Paint score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-007: Heading levels are skipped on 2/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `heading-hierarchy`; Seen on 2 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 2 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Skipped heading levels can make section relationships less clear.

**Pages:**

- <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>
- <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>

**Evidence:**

- Observed heading levels: \[1, 3, 2, 2, 3, 2, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3\]
  - <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>
- Observed heading levels: \[1, 3, 3, 3, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3\]
  - <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>

**What to do:** Review the outline and nest headings according to the document hierarchy.

**Suggested roles:** developer, seo

1. Review the outline and nest headings according to the document hierarchy.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves outline consistency without requiring an arbitrary visual style.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-008: Likely Largest Contentful Paint (LCP) risk, estimated from markup and not measured

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.90; Check: `cwv-risk`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.9; 1 supported page(s), medium effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Markup patterns that delay the largest paint were observed: the main content may appear slowly

**Pages:**

- <https://www.propublica.org/>

**Evidence:**

- Estimate, not a measurement: the first content image is lazy-loaded in the HTML; 13 render-blocking scripts and stylesheets in the head
  - <https://www.propublica.org/>

**What to do:** Check LCP in a browser or with field data, and remove the listed patterns

**Suggested roles:** developer, seo

1. Do not lazy-load the first large image; give it fetchpriority="high" or preload it
2. Defer or async non-critical scripts and inline only critical CSS
3. Reduce server response time with caching
4. Confirm with PageSpeed Insights or the Chrome UX Report

Effort: medium; Impact: low; Deprioritize: more work than the value it brings for now.

**Expected benefit:** Lower risk of a poor Largest Contentful Paint score

**How to check the fix:** Measure the page with PageSpeed Insights and re-run the audit

### F-009: Title shorter than 15 or longer than 70 characters on 4/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `title-length`; Seen on 4 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 4 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Unusually short or long titles may be uninformative or truncated on some displays.

**Pages:**

- <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>
- <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>

**Evidence:**

- Title has 88 characters: DHS Border Wall Construction Leads to Surveillance of Tohono O’odham Nation — ProPublica. Display width was not measured.
  - <https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall>
- Title has 78 characters: Maricopa County’s Housing Hub Is a Dead End for Homeless Families — ProPublica. Display width was not measured.
  - <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- Title has 72 characters: Ken Paxton’s Travel Security Detail Cost Taxpayers Millions — ProPublica. Display width was not measured.
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- Title has 118 characters: The Pentagon Gave Contracts to Alvarez &amp; Marsal Federal, a Firm Closely Tied to a Senior Defense Off. Display width was not measured.
  - <https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal>

**What to do:** Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

**Suggested roles:** developer, seo

1. Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves title usefulness; pixel width and platform behavior vary.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-010: Visible text is under 3% of the HTML on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.80; Check: `markup-ratio`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.8; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** A small visible-text share in a large HTML document can indicate excess markup.

**Pages:**

- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**Evidence:**

- Visible text represents 2.6% of decoded HTML body bytes. This is not a ranking metric.
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**What to do:** Inspect inline assets and template boilerplate before trimming unnecessary HTML.

**Suggested roles:** developer, seo

1. Inspect inline assets and template boilerplate before trimming unnecessary HTML.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Reduces document overhead if the sampled ratio reflects avoidable markup.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-011: Content pages lack a clear orientation heading above the fold

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.70; Check: `page-orientation`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.7; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.

**Pages:**

- <https://www.propublica.org/article/ken-paxton-travel-security-costs>

**Evidence:**

- Substantial pages were sampled with no descriptive short primary heading in their first headings, so an arriving visitor has no immediate orientation.
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>

**What to do:** Lead each content page with a descriptive H1 that names the topic

**Suggested roles:** developer, seo

1. Lead each content page with a descriptive H1 that names the topic
2. Follow with scannable H2 sections so the page structure is clear at a glance

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Improves orientation, readability or the relevant next step when the observed issue affects visitors

**How to check the fix:** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-012: No question-shaped headings on 3/3 content pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `answer-headings`; Seen on 3 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 3 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** Question-shaped sections may help readers locate direct answers where that format fits the content.

**Pages:**

- <https://www.propublica.org/article/ken-paxton-travel-security-costs>
- <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>

**Evidence:**

- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel>
- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters>
- No question-shaped H2/H3 headings observed in this English content-page sample. Direct answers can still exist without question headings.
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>

**What to do:** Review audience questions and add useful question headings with concise answers; do not add empty FAQs or inappropriate schema.

**Suggested roles:** content, developer, seo

1. Review audience questions and add useful question headings with concise answers; do not add empty FAQs or inappropriate schema.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** May improve answer readability; questions are not required for retrieval or citation.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

### F-013: Canonical tag points to another site on 1/6 sampled pages

Type: Improvement opportunity; Severity: low; Status: suspected (likely, not proven); Confidence: 0.60; Check: `cross-origin-canonical`; Seen on 1 of 6 analyzed page(s); Rule assessed-page denominator: unavailable

**Priority basis:** low severity, suspected status, confidence 0.6; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** An external canonical can nominate another origin as the preferred copy.

**Pages:**

- <https://www.propublica.org/article/ken-paxton-travel-security-costs>

**Evidence:**

- External canonical hint: https://www.texastribune.org/2026/10/09/ken-paxton-travel-costs/
  - <https://www.propublica.org/article/ken-paxton-travel-security-costs>

**What to do:** Verify ownership and content equivalence; correct the URL only if the external canonical is unintended.

**Suggested roles:** developer, seo

1. Verify ownership and content equivalence; correct the URL only if the external canonical is unintended.

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Avoids unintended consolidation while preserving legitimate syndication.

**How to check the fix:** Repeat the affected observation and verify the intended behavior.

## Other recommendations

Good practice to keep, beyond the findings above:

- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## What's working

Checks that ran and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **AI and search crawlers may fetch the site.** robots.txt lets all 18 AI and search crawlers checked fetch the site, and closes no discovered site section to them (AI search: OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Applebot; user-requested fetch: ChatGPT-User, Claude-User, Perplexity-User, Meta-ExternalFetcher, MistralAI-User; model training: GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, Amazonbot, Meta-ExternalAgent, CCBot, Bytespider).
- **An XML sitemap is available.** An XML sitemap was read; it lists at least 9 URLs.
- **Pages are served over HTTPS.** All 6 pages checked were served over HTTPS.
- **Fetched pages load without HTTP errors.** None of the 6 pages fetched answered with an HTTP error (4xx or 5xx).
- **Every page has a title.** All 6 pages checked have a document title.
- **Every page has a meta description.** All 6 pages checked have a meta description.
- **Every page declares its language.** All 6 pages checked declare their language (html lang).
- **Pages are open to indexing and snippets.** None of the 6 pages checked carries a noindex, nosnippet or max-snippet:0 directive (meta robots or X-Robots-Tag).
- **Structured data parses cleanly.** JSON-LD structured data is on 6 of the 6 pages checked, and every block parsed.
- **Content is in the raw HTML.** All 6 pages checked carry their text in the raw HTML, so crawlers that do not run JavaScript can read it.
- **Mobile viewport is declared and zoom is allowed.** All 6 pages checked declare a mobile viewport, and none blocks zooming.
- **Images carry alt attributes.** All 165 images on the pages checked carry an alt attribute, and none was flagged as a file name or placeholder.
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

- 157 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 163 discovered); findings reflect only the 6 page(s) actually crawled, not the whole site. The sample reached 2 of 37 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- No search for same-named knowledge-graph entities was run: robots.txt for Wikidata and Wikipedia disallows their search endpoints, so only the agent stage (AG-05) can look the brand name up; namesake ambiguity is unassessed.
- Linked sameAs and review profiles were not fetched (OFF\_SITE\_LOOKUP=0), so whether they resolve and belong to the brand was not checked.
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- Colour contrast and tap-target size were judged only where inline styles set them; colours and sizes from stylesheets need a browser to compute and were not assessed.
- 32 same-origin content image(s) were not measured for file size (per-audit cap of 4 or remaining budget); cross-origin images are never requested, so their weight is unassessed.

## Notes from the run

- English lexical checks skipped on pages with unknown/non-English language or truncated retained text.
- https://www.propublica.org/: Unsupported IRI value/context form for logo
- https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal: Unsupported IRI value/context form for image
- https://www.propublica.org/article/george-kollitides-pentagon-contracts-alvarez-marsal: Unsupported IRI value/context form for logo
- https://www.propublica.org/article/ken-paxton-travel-security-costs: Unsupported IRI value/context form for logo
- https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters: Unsupported IRI value/context form for image
- https://www.propublica.org/article/maricopa-county-homeless-hub-hotline-shelters: Unsupported IRI value/context form for logo
- https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel: Unsupported IRI value/context form for image
- https://www.propublica.org/article/sports-betting-problem-gambling-draftkings-fanduel: Unsupported IRI value/context form for logo
- https://www.propublica.org/article/tohono-oodham-nation-arizona-border-wall: Unsupported IRI value/context form for logo
- No external search provider configured (SEARCH\_API\_URL unset); corroboration is an optional capability in this deployment (not checked, not "not found").
- No external search provider configured (SEARCH\_API\_URL unset); footprint assessment is an optional capability in this deployment (not checked, not "no presence found").
- Off-site profile lookup disabled (OFF\_SITE\_LOOKUP=0); linked profiles were not fetched or verified.
- An email signup form appears on 6/6 sampled pages. A site audit cannot see the emails the site sends, so whether inbox assistants can summarize them was not checked.
- Orphan pages and isolated page clusters were not assessed: the crawl analyzed a sample, and a page the sample does not link to may be linked from a page that was not fetched.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
