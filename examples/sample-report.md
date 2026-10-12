# AI-readiness audit: http://shop.example/

Audited 2026-10-12T10:45:33.733092+00:00 | status **completed**

Sample: 8 content page(s) across 8 page template(s); 8 URL(s) discovered; 0 bot-challenged; 0 login page(s) kept out of scope. The audit reads the site from outside, the way a crawler does, and changes nothing.

## How far to trust this report

**Confidence: medium (0.4)**. Confidence is medium (0.40). It is limited by sample quality: 8 content page(s) across 8 distinct page template(s) were analysed; 20 pages across 5 templates counts as a full sample. Brand identity confidence is 0.92; it limits only the off-site findings, not this score.

| Part | Score | Why |
|---|---|---|
| sample quality | 0.4 | 8 content page(s) across 8 distinct page template(s) were analysed; 20 pages across 5 templates counts as a full sample. |
| access quality | 1.0 | 8 of 8 fetched page(s) returned real content. |
| execution penalty | 1.0 | The audit run completed normally. |

Method: min(sample\_quality, access\_quality, execution\_penalty); sample\_quality = min(1, pages/20) x min(1, templates/5). Identity confidence limits only off-site findings.

## Start here

**Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment.** (high severity, medium effort; details under F-001).

## Top actions

| # | Action | Severity | Effort | Quick win | Owner | Finding |
|---|---|---|---|---|---|---|
| 1 | Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment. | high | medium |  | infra | F-001 |
| 2 | Update or remove expired offers and validity dates | high | low | yes | content | F-002 |
| 3 | Add Product/Offer JSON-LD to product pages | high | medium |  | developer | F-003 |
| 4 | Add an appropriate responsive viewport declaration | medium | low | yes | developer | F-004 |
| 5 | Complete the required properties on each listed JSON-LD node | medium | low | yes | developer | F-005 |

Quick wins (medium impact or more, low effort, solid evidence): F-002, F-004, F-005, F-006.

## Summary

14 finding(s): 0 critical, 3 high, 5 medium, 6 low. 5 SEO-hygiene item(s) in the appendix. 8 check(s) passed. Agent corroboration stage: not_supplied.

## Findings

### F-001 - Sampled content was retrieved over HTTP
**HIGH** | status: confirmed | confidence: 0.95 | owner: infra | effort: medium
*Why this severity:* gate **access**, scope site-wide (8/8 sampled content pages)

**What we found.** Sampled content was retrieved over HTTP on 8 sampled page(s); e.g. Retrieved URL: http://shop.example/about

**Why it matters.** HTTP does not encrypt the fetched connection.

**Evidence.**
- 2 page(s): Retrieved URL: http://shop.example/about (<http://shop.example/about>, <http://shop.example/redirect>)
- Retrieved URL: http://shop.example/ (<http://shop.example/>)
- Retrieved URL: http://shop.example/cluster-a (<http://shop.example/cluster-a>)
- Retrieved URL: http://shop.example/cluster-b (<http://shop.example/cluster-b>)
- Retrieved URL: http://shop.example/js-heavy (<http://shop.example/js-heavy>)

**How to fix.** Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment.
1. Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment.

**How to verify.** Repeat the affected observation and verify the intended behavior.

### F-002 - Expired offers or validity dates are still published
**HIGH** | status: confirmed | confidence: 0.85 | owner: content | effort: low
*Why this severity:* gate **trust**, scope page (1/8 sampled content pages)
*Combines checks:* expired-offer, stale-update-claim

**What we found.** Live pages state offer, price-validity or event end dates that have already passed

**Why it matters.** An offer, price validity or event end date has passed but the page is still live. An assistant quoting it gives users wrong information, and a visible expiry date signals the page is unmaintained.

**Evidence.**
- visible '2020-06-15' (.99. Offer last updated 2019-03-01. Promotion valid through . Stock refreshed 20) is in the past (<http://shop.example/product>)
- page states it was updated 2021-11-20 (59 months ago) (<http://shop.example/product>)

**How to fix.** Update or remove expired offers and validity dates
1. Update the offer or remove it from the live page
2. Set priceValidUntil / validThrough to the real end date
3. Automate expiry so ended offers are unpublished on schedule
4. Review each fact on the page for accuracy
5. Update the content and the "last updated" date together

**How to verify.** Re-run the audit and confirm the dates listed in the evidence

### F-003 - Product pages are missing Product/Offer structured data
**HIGH** | status: confirmed | confidence: 0.8 | owner: developer | effort: medium
*Why this severity:* gate **extractability**, scope page (1/8 sampled content pages)

**What we found.** 1 page(s) classified as 'product' carry no Product/Offer JSON-LD, so explicit machine-readable context is missing

**Why it matters.** Product/Offer markup is how price, currency and availability become exact, extractable facts; without it a machine has to guess them from layout text and often quotes them wrongly or not at all.

**Evidence.**
- 1 'product' page(s) missing Product/Offer markup (<http://shop.example/product>)

**How to fix.** Add Product/Offer JSON-LD to product pages
1. Add Product/Offer schema.org JSON-LD matching each product page's content
2. Validate with a schema.org/Rich Results validator

Draft JSON-LD for <http://shop.example/product> (review values before use):
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Widget",
  "offers": {
    "@type": "Offer",
    "price": "<price as shown on page>",
    "priceCurrency": "<ISO 4217 code>",
    "availability": "https://schema.org/InStock",
    "url": "http://shop.example/product"
  }
}
```

**How to verify.** Re-crawl and confirm the expected @type is present

### F-004 - Pages lack a mobile viewport declaration
**MEDIUM** | status: confirmed | confidence: 0.95 | owner: developer | effort: low
*Why this severity:* gate **engagement**, scope site-wide (8/8 sampled content pages)

**What we found.** No viewport declaration was observed; actual layout behavior requires visual verification.

**Why it matters.** Missing viewport configuration can impair responsive layout on mobile.

**Evidence.**
- 8 page(s): No viewport declaration was observed; actual layout behavior requires visual verification. (<http://shop.example/about>, <http://shop.example/>, <http://shop.example/cluster-a>)

**How to fix.** Add an appropriate responsive viewport declaration
1. Add an appropriate responsive viewport declaration
2. Verify that layout reflows and remains readable

**How to verify.** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-005 - Structured data is missing required properties
**MEDIUM** | status: confirmed | confidence: 0.9 | owner: developer | effort: low
*Why this severity:* gate **extractability**, scope site-wide (1/8 sampled content pages)
*Combines checks:* schema-missing-recommended, schema-missing-required

**What we found.** Typed JSON-LD nodes lack the properties consumers need to use them: Organization: missing url or @id on 1 page(s)

**Why it matters.** Structured data that lacks the properties consumers require (for example an Offer without price/priceCurrency) is ignored or only partly used, so the fact it was meant to carry is lost.

**Evidence.**
- Organization: missing url or @id on 1 page(s) (<http://shop.example/>)
- Organization: no logo on 1 page(s) (<http://shop.example/>)

**How to fix.** Complete the required properties on each listed JSON-LD node
1. Organization: add url or @id
2. Fill values from the same source as the visible page
3. Re-validate with a schema.org validator
4. Organization: add logo

**How to verify.** Every listed node validates with its required properties

### F-006 - Malformed JSON-LD blocks prevent reliable fact extraction
**MEDIUM** | status: confirmed | confidence: 0.9 | owner: developer | effort: low
*Why this severity:* gate **extractability**, scope page (1/8 sampled content pages), single non-key page: one tier lower

**What we found.** One or more sampled pages contain JSON-LD that could not be parsed, so structured facts may be discarded by automated readers

**Why it matters.** A JSON-LD block that is not valid JSON is discarded whole by parsers, so every fact it carried (identity, prices, dates) is lost to machines.

**Evidence.**
- 1 sampled page(s) contain malformed JSON-LD (<http://shop.example/malformed>)

**How to fix.** Repair and validate every application/ld+json block
1. Validate each JSON-LD block as strict JSON
2. Preserve valid @graph nodes and required properties
3. Re-run a structured-data validator after deployment

**How to verify.** All sampled JSON-LD blocks parse successfully

### F-007 - Isolated page clusters not reachable from the main site structure
**MEDIUM** | status: confirmed | confidence: 0.7 | owner: content | effort: medium
*Why this severity:* gate **engagement**, scope template (2/8 sampled content pages)

**What we found.** 1 cluster(s) totalling 2 page(s) are internally linked to each other but have no path from the main navigation/homepage

**Why it matters.** Groups of pages linked only to each other are discovered only if a crawler already knows an entry URL, so they are frequently missed as a whole.

**Evidence.**
- Isolated cluster of 2 page(s) (<http://shop.example/cluster-a>, <http://shop.example/cluster-b>)

**How to fix.** Link isolated page clusters into the main navigation structure
1. Identify which cluster(s) contain valuable content
2. Add navigation or contextual links connecting them to the main site

**How to verify.** Re-run and confirm the cluster merges into the main component

### F-008 - Content appears to require JavaScript rendering
**MEDIUM** | status: suspected | confidence: 0.6 | owner: developer | effort: high
*Why this severity:* gate **readability**, scope page (1/8 sampled content pages), single non-key page: one tier lower

**What we found.** The server-sent HTML lacks content that the page assembles in the browser; clients that do not execute JavaScript (most AI fetchers) receive an incomplete page

**Why it matters.** Many AI fetchers store the raw HTML response without running JavaScript. Content assembled client-side is missing from what they index and quote.

**Evidence.**
- empty JavaScript mount node / noscript asks for JavaScript (<http://shop.example/js-heavy>)

**How to fix.** Server-side render or pre-render key content
1. Add SSR or static generation for the affected templates
2. Keep the strings listed in the evidence in the initial HTML
3. Re-run this audit with ENABLE\_RENDERING=1 to confirm with a real browser

**How to verify.** Confirm raw HTML (curl) contains the key facts

### F-009 - Pages omit an explicit document language
**LOW** | status: confirmed | confidence: 0.95 | owner: developer | effort: low
*Why this severity:* gate **extractability**, scope site-wide (8/8 sampled content pages)

**What we found.** Pages omit an explicit document language on 8 sampled page(s); e.g. The html lang attribute is absent or empty.

**Why it matters.** A missing document language can impede assistive pronunciation and language interpretation.

**Evidence.**
- 8 page(s): The html lang attribute is absent or empty. (<http://shop.example/about>, <http://shop.example/>, <http://shop.example/cluster-a>)

**How to fix.** Set an accurate BCP 47 lang attribute on the html element; verify multilingual sections separately.
1. Set an accurate BCP 47 lang attribute on the html element; verify multilingual sections separately.

**How to verify.** Repeat the affected observation and verify the intended behavior.

### F-010 - Review the next step on commercial landing pages
**LOW** | status: suspected | confidence: 0.7 | owner: content | effort: low
*Why this severity:* gate **engagement**, scope site-wide (5/8 sampled content pages)
*Combines checks:* dead-ends, next-step

**What we found.** No form, button or internal next-step link was observed on these commercial pages.

**Why it matters.** Commercial pages without an observed action path can leave visitors unsure how to proceed.

**Evidence.**
- No form, button or internal next-step link was observed on these commercial pages. (<http://shop.example/product>)
- 5 dead-end pages found (<http://shop.example/about>, <http://shop.example/js-heavy>, <http://shop.example/malformed>)

**How to fix.** Add a relevant purchase, inquiry or comparison route if missing
1. Add a relevant purchase, inquiry or comparison route if missing
2. Add related-content links
3. Add a clear next-step call-to-action

**How to verify.** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-011 - No llms.txt file found
**LOW** | status: confirmed | confidence: 0.6 | owner: seo | effort: low
*Why this severity:* gate **extractability**, scope site-wide (1/8 sampled content pages)

**What we found.** Site does not publish an llms.txt guidance file

**Why it matters.** llms.txt is an emerging convention: a short Markdown file at the site root that tells AI tools what the site is and which pages matter. Support is still limited, so it is a cheap, optional signal rather than a requirement.

**Evidence.**
- /llms.txt returned 404 (<http://shop.example/llms.txt>)

**How to fix.** Publish an llms.txt summarizing key pages for AI assistants
1. Create /llms.txt
2. List key pages and a short site summary

Ready-to-paste fix (markdown). Placement: Save as /llms.txt at the site root, served as text/plain.
```markdown
# Example Brand

> REPLACE_WITH_ONE_SENTENCE_DESCRIPTION

## Key pages

- [Example Brand](http://shop.example/)
- [About](http://shop.example/about)
- [Product](http://shop.example/product)
- [Cluster A](http://shop.example/cluster-a)
- [Cluster B](http://shop.example/cluster-b)
- [App](http://shop.example/js-heavy)
- [Bad JSON-LD](http://shop.example/malformed)

```
Filled from: name: Organization JSON-LD name; key pages: crawled pages, with their titles and meta descriptions.
Replace before publishing: `REPLACE_WITH_ONE_SENTENCE_DESCRIPTION`.

**How to verify.** Confirm /llms.txt is reachable and valid

### F-012 - Organization markup does not link the brand to a knowledge-graph entity
**LOW** | status: confirmed | confidence: 0.8 | owner: seo | effort: medium
*Why this severity:* gate **trust**, scope site-wide (1/8 sampled content pages)

**What we found.** No Wikidata or Wikipedia link is declared in Organization sameAs, so nothing ties the brand to one knowledge-graph entity.

**Why it matters.** Knowledge graphs (Wikidata, and Wikipedia through it) are the main signal assistants use to tell same-named entities apart. Organization markup without a sameAs link to the brand's knowledge-graph entity leaves that connection to guesswork.

**Evidence.**
- Organization markup on 1 page(s) declares sameAs: https://twitter.com/example; none names a Wikidata item or Wikipedia article (<http://shop.example/>)

**How to fix.** Link the brand to its Wikidata item in Organization sameAs
1. Find the brand's Wikidata item, or create one if the organization meets Wikidata's notability policy (serious, public references)
2. Add the item URL, and the Wikipedia article if one exists, to Organization sameAs
3. Make sure the item lists this site as its official website (P856)

**How to verify.** Organization sameAs contains https://www.wikidata.org/wiki/Q... for the brand

### F-013 - Some pages lack semantic headings
**LOW** | status: confirmed | confidence: 0.56 | owner: content | effort: low
*Why this severity:* gate **extractability**, scope page (1/8 sampled content pages), single non-key page: one tier lower

**What we found.** Pages have no h1-h6 elements

**Why it matters.** Extractors use headings to split a page into topics and to decide which passage answers a question; a page with none is one undifferentiated block.

**Evidence.**
- 1 pages have no headings (<http://shop.example/js-heavy>)

**How to fix.** Add semantic heading structure
1. Add an h1 per page
2. Structure sections with h2/h3

**How to verify.** Inspect DOM for heading tags

### F-014 - About pages are missing Organization/AboutPage structured data
**LOW** | status: confirmed | confidence: 0.8 | owner: developer | effort: medium
*Why this severity:* gate **extractability**, scope page (1/8 sampled content pages)

**What we found.** 1 page(s) classified as 'about' carry no Organization/AboutPage JSON-LD, so explicit machine-readable context is missing

**Why it matters.** The About page is the main source for identity questions; Organization/AboutPage markup ties its description to one declared entity.

**Evidence.**
- 1 'about' page(s) missing Organization/AboutPage markup (<http://shop.example/about>)

**How to fix.** Add Organization/AboutPage JSON-LD to about pages
1. Add Organization/AboutPage schema.org JSON-LD matching each about page's content
2. Validate with a schema.org/Rich Results validator

Draft JSON-LD for <http://shop.example/about> (review values before use):
```json
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "http://shop.example/about",
  "mainEntity": {
    "@type": "Organization",
    "name": "About",
    "telephone": "<phone>",
    "address": "<postal address>"
  }
}
```

**How to verify.** Re-crawl and confirm the expected @type is present

## What's working

Checks that ran to completion and found nothing to fix:

- **robots.txt allows crawling.** robots.txt was read and lets crawlers fetch the start URL.
- **Search and AI crawlers may fetch the site.** robots.txt lets all 18 search, AI search, user-fetch and training crawlers checked fetch the homepage and the key pages sampled.
- **Automated clients receive the real content.** None of the 8 pages fetched answered with a bot challenge or rate limit.
- **An XML sitemap is available.** An XML sitemap was read; it lists 4 URLs.
- **Fetched pages load without HTTP errors.** None of the 8 pages fetched answered with an HTTP error.
- **Every page has a title.** All 8 pages checked have a document title.
- **Pages are open to indexing and snippets.** None of the 8 pages checked carries noindex, nosnippet or max-snippet:0 (meta robots or X-Robots-Tag).
- **The brand identity is declared.** Organization markup declares the brand as 'Example Brand' with no conflicting name.

## Recommendations beyond the defects

### R-001 - Continue building independent, identity-matched off-site mentions
Off-site presence is cumulative; even a well-corroborated brand benefits from continued, diverse independent mentions.
1. List the brand on relevant, reputable directories
2. Keep sameAs and social profiles active and identity-consistent
3. Encourage independent, identity-matched mentions over time

## Limitations

- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").

## Appendix: SEO hygiene

| Id | Item | Pages | Fix |
|---|---|---|---|
| H-001 | Review incomplete Open Graph preview metadata | 8 | Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview. |
| H-002 | Review unusually short or long titles | 8 | Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota. |
| H-003 | Review missing page descriptions | 8 | Write a concise page-specific meta description that matches visible content. |
| H-004 | Review preferred URL declarations | 8 | Assess real duplicates before declaring the correct absolute canonical URL. |
| H-005 | Different sampled URLs share page titles | 2 | Give distinct content pages descriptive, distinct titles |

