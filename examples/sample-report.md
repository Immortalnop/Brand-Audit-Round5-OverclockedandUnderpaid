# AI-readiness audit: https://shop.example/

Audited 2026-10-12T08:27:36.358949+00:00 | status **completed** | report confidence **0.4**

Sample: 8 content page(s) across 8 page template(s); 8 URL(s) discovered; 0 bot-challenged.
Confidence method: min(sample_quality, access_quality, execution_penalty); sample_quality = min(1, pages/20) x min(1, templates/5). Identity confidence limits only off-site findings.

## Top actions

| # | Action | Severity | Effort | Owner | Finding |
|---|---|---|---|---|---|
| 1 | Serve the public site over verified HTTPS; verify the canonical HTTPS URL and redirect policy before deployment. | high | medium | infra | F-001 |
| 2 | Update or remove expired offers and validity dates | high | low | content | F-002 |
| 3 | Add Product/Offer JSON-LD to product pages | high | medium | developer | F-003 |
| 4 | Add an appropriate responsive viewport declaration | medium | low | developer | F-004 |
| 5 | Complete the required properties on each listed JSON-LD node | medium | low | developer | F-005 |

## Summary

14 finding(s): 0 critical, 3 high, 5 medium, 6 low. 5 SEO-hygiene item(s) in the appendix. Agent corroboration stage: not_supplied.

## Findings

### F-001 - Sampled content was retrieved over HTTP
**HIGH** | status: confirmed | confidence: 0.95 | owner: infra | effort: medium
*Why this severity:* gate **access**, scope site-wide (8/8 sampled content pages)

**What we found.** Sampled content was retrieved over HTTP on 8 sampled page(s); e.g. Retrieved URL: https://shop.example/about

**Why it matters.** HTTP does not encrypt the fetched connection.

**Evidence.**
- 2 page(s): Retrieved URL: https://shop.example/about (https://shop.example/about, https://shop.example/redirect)
- Retrieved URL: https://shop.example/ (https://shop.example/)
- Retrieved URL: https://shop.example/cluster-a (https://shop.example/cluster-a)
- Retrieved URL: https://shop.example/cluster-b (https://shop.example/cluster-b)
- Retrieved URL: https://shop.example/js-heavy (https://shop.example/js-heavy)

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
- visible '2020-06-15' (.99. Offer last updated 2019-03-01. Promotion valid through . Stock refreshed 20) is in the past (https://shop.example/product)
- page states it was updated 2021-11-20 (59 months ago) (https://shop.example/product)

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
- 1 'product' page(s) missing Product/Offer markup (https://shop.example/product)

**How to fix.** Add Product/Offer JSON-LD to product pages
1. Add Product/Offer schema.org JSON-LD matching each product page's content
2. Validate with a schema.org/Rich Results validator

Draft JSON-LD for https://shop.example/product (review values before use):
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
    "url": "https://shop.example/product"
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
- 8 page(s): No viewport declaration was observed; actual layout behavior requires visual verification. (https://shop.example/about, https://shop.example/, https://shop.example/cluster-a)

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
- Organization: missing url or @id on 1 page(s) (https://shop.example/)
- Organization: no logo on 1 page(s) (https://shop.example/)

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

**Why it matters.** One or more sampled pages contain JSON-LD that could not be parsed, so structured facts may be discarded by automated readers

**Evidence.**
- 1 sampled page(s) contain malformed JSON-LD (https://shop.example/malformed)

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
- Isolated cluster of 2 page(s) (https://shop.example/cluster-a, https://shop.example/cluster-b)

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
- empty JavaScript mount node / noscript asks for JavaScript (https://shop.example/js-heavy)

**How to fix.** Server-side render or pre-render key content
1. Add SSR or static generation for the affected templates
2. Keep the strings listed in the evidence in the initial HTML
3. Re-run this audit with ENABLE_RENDERING=1 to confirm with a real browser

**How to verify.** Confirm raw HTML (curl) contains the key facts

### F-009 - Pages omit an explicit document language
**LOW** | status: confirmed | confidence: 0.95 | owner: developer | effort: low
*Why this severity:* gate **extractability**, scope site-wide (8/8 sampled content pages)

**What we found.** Pages omit an explicit document language on 8 sampled page(s); e.g. The html lang attribute is absent or empty.

**Why it matters.** A missing document language can impede assistive pronunciation and language interpretation.

**Evidence.**
- 8 page(s): The html lang attribute is absent or empty. (https://shop.example/about, https://shop.example/, https://shop.example/cluster-a)

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
- No form, button or internal next-step link was observed on these commercial pages. (https://shop.example/product)
- 5 dead-end pages found (https://shop.example/about, https://shop.example/js-heavy, https://shop.example/malformed)

**How to fix.** Add a relevant purchase, inquiry or comparison route if missing
1. Add a relevant purchase, inquiry or comparison route if missing
2. Add related-content links
3. Add a clear next-step call-to-action

**How to verify.** Inspect the affected pages on mobile and desktop; re-crawl after changes

### F-011 - No llms.txt file found
**LOW** | status: confirmed | confidence: 0.6 | owner: seo | effort: low
*Why this severity:* gate **extractability**, scope site-wide (1/8 sampled content pages)

**What we found.** Site does not publish an llms.txt guidance file

**Why it matters.** Site does not publish an llms.txt guidance file

**Evidence.**
- /llms.txt returned 404 (https://shop.example/llms.txt)

**How to fix.** Publish an llms.txt summarizing key pages for AI assistants
1. Create /llms.txt
2. List key pages and a short site summary

**How to verify.** Confirm /llms.txt is reachable and valid

### F-012 - Some pages have very little server-rendered text
**LOW** | status: insufficient_evidence | confidence: 0.3 | owner: developer | effort: low
*Why this severity:* gate **readability**, scope site-wide (7/8 sampled content pages)

**What we found.** These pages return little visible text but show no JavaScript-shell signal; they may be genuinely short, so no rendering defect is asserted without a browser comparison

**Why it matters.** Headless rendering also returned little content, or failed, for these pages -- could be genuinely thin content rather than a JS dependency

**Evidence.**
- Thin server HTML without SPA signals (https://shop.example/about, https://shop.example/, https://shop.example/cluster-a)

**How to fix.** Check these pages in a browser against their raw HTML
1. Compare the page in a browser with curl output
2. Re-run with ENABLE_RENDERING=1 to confirm automatically

**How to verify.** Manual inspection

### F-013 - Some pages lack semantic headings
**LOW** | status: confirmed | confidence: 0.56 | owner: content | effort: low
*Why this severity:* gate **extractability**, scope page (1/8 sampled content pages), single non-key page: one tier lower

**What we found.** Pages have no h1-h6 elements

**Why it matters.** Pages have no h1-h6 elements

**Evidence.**
- 1 pages have no headings (https://shop.example/js-heavy)

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
- 1 'about' page(s) missing Organization/AboutPage markup (https://shop.example/about)

**How to fix.** Add Organization/AboutPage JSON-LD to about pages
1. Add Organization/AboutPage schema.org JSON-LD matching each about page's content
2. Validate with a schema.org/Rich Results validator

Draft JSON-LD for https://shop.example/about (review values before use):
```json
{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://shop.example/about",
  "mainEntity": {
    "@type": "Organization",
    "name": "About",
    "telephone": "<phone>",
    "address": "<postal address>"
  }
}
```

**How to verify.** Re-crawl and confirm the expected @type is present

## Recommendations beyond the defects

### R-001 - Continue building independent, identity-matched off-site mentions
Off-site presence is cumulative; even a well-corroborated brand benefits from continued, diverse independent mentions.
1. List the brand on relevant, reputable directories
2. Keep sameAs and social profiles active and identity-consistent
3. Encourage independent, identity-matched mentions over time

## Limitations

- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").

## Appendix: SEO hygiene

| Id | Item | Pages | Fix |
|---|---|---|---|
| H-001 | Review incomplete Open Graph preview metadata | 8 | Set accurate og:title, og:description, og:image and og:url values on shareable pages; verify the actual preview. |
| H-002 | Review unusually short or long titles | 8 | Review outlier titles for clarity; place distinguishing terms early rather than enforcing a character quota. |
| H-003 | Review missing page descriptions | 8 | Write a concise page-specific meta description that matches visible content. |
| H-004 | Review preferred URL declarations | 8 | Assess real duplicates before declaring the correct absolute canonical URL. |
| H-005 | Different sampled URLs share page titles | 2 | Give distinct content pages descriptive, distinct titles |

