---
name: crawl-render-audit
description: >-
  Analyzes off-site AI discoverability mechanics of a crawled website: reachability; robots.txt with fetch-status calibration (ok, absent, timeout, inaccessible, malformed, blocked; never infers a disallow from a failed fetch) and AI-crawler access; raw-vs-rendered content gaps incl. <noscript> fallbacks; JSON-LD structured data; sitemap.xml discovery; llms.txt presence, format and links, plus llms-full.txt; facts locked in non-text media (SVG image text, raster images named as price lists or menus, linked PDFs); text drawn by canvas, inline SVG and icon fonts; media text alternatives (alt text quality, video and audio transcripts, captions, VideoObject markup); image captions and link text as image context; image weight (file size, format, srcset); FAQPage, HowTo, Review and AggregateRating markup; Core Web Vitals (field data with a PageSpeed Insights key, else markup estimates); hreflang on multi-language sites. Called by audit-orchestrator in its independent analysis batch; not for standalone use.
license: MIT
allowed-tools: Bash(python3:*) Read
---
# Crawl & Render Audit

## When to use
Called by audit-orchestrator. Not a standalone entrypoint.

## Dependencies
Pure-Python analysis over an already-acquired `AuditArtifacts` snapshot --
no network calls of its own. `analyze_rendering.py` additionally checks for
`playwright` (optional; degrades to a heuristic, `suspected` gap-detection
when absent, per `common/capabilities.py`). `analyze_web_vitals.py` reads
optional Core Web Vitals field data that the orchestrator requested at audit
start (`common/field_vitals.py`, only with `PAGESPEED_API_KEY`).

## Inputs
An `AuditArtifacts` snapshot produced by `acquire_site.py`.

## Procedure
Run `analyze_crawlability`, `analyze_rendering`, `analyze_machine_readability`,
`check_ai_crawler_access`, `check_llms_txt`, `analyze_non_text`,
`analyze_media_text`, `analyze_citation_schema`, `analyze_international`,
`analyze_graphics_text`, `analyze_image_context`, `analyze_image_weight`,
`analyze_answer_format` and `analyze_context_signals` in the independent batch, and
`analyze_web_vitals` in the dependent batch -- see
`references/crawl-render-checklist.md`.

## Output
One `SkillResult` per script: findings (evidence + severity) plus metrics.

## Example

Input: an `AuditArtifacts` with one page that has no JSON-LD.
`analyze_machine_readability` output:

```json
{"skill": "crawl-render-audit", "status": "success",
 "findings": [{"id": "F-002", "category": "ai_discoverability",
               "severity": "high", "status": "confirmed",
               "root_cause": "Home page has no Organization/WebSite JSON-LD"}],
 "metrics": {"pages_missing_jsonld": 1}}
```


## Additional snapshot analysis

The entrypoint invokes `analyze_metadata.py` and `analyze_performance.py` as
in-process functions consuming the shared AuditArtifacts snapshot and returning
SkillResult objects. They make no network requests. Metadata covers titles,
descriptions, canonical hints, language, landmarks, heading hierarchy and social
previews. Performance covers observed document bytes, synchronous head scripts,
image dimension hints and retrieval timing, never fabricated Core Web Vitals.
Use common/check_catalog.py for rule mechanisms and implementation guidance.

## Sitemaps and AI crawlers by section

Sitemaps are parsed incrementally: one larger than the 512 KB read budget, or a
gzipped one, still yields every complete `<url>` entry and is listed in
`sitemap_data.partial`, never reported as malformed. `sitemap-unavailable`
names the sitemap URLs it checked. `ai-crawler-section-blocked` reports AI
crawlers that robots.txt disallows on some site sections while leaving them open
to crawlers in general (one sample URL per section, judged from robots.txt with
no request): medium for search crawlers, low for training or user-fetch ones.

## Non-text media

`analyze_non_text.py` reads the image and PDF observations that acquisition
collected (`common/non_text.py` for SVG text and image headers,
`common/pdf_text.py` for standard-library PDF text extraction). It compares the
facts found in media with the facts stated in readable text and reports
`facts-in-images`, `pdf-only-facts` and `pdf-image-only`. It makes no network
requests of its own.

## Text alternatives for media

`analyze_media_text.py` reports `alt-text-quality` (alt text that is a file
name, a camera file name or a placeholder word such as "banner"; empty alt on a
decorative image is correct and never counted), `media-transcript-missing`
(video or audio with no transcript in the page text or links and no captions
track on native players; captions inside embedded players cannot be seen and are
reported as not checked) and `media-schema-missing` (no VideoObject or
AudioObject markup, or VideoObject without name, thumbnailUrl or uploadDate).

## Citation-oriented markup

`analyze_citation_schema.py` reports `citation-schema-invalid` when FAQPage,
HowTo, Review or AggregateRating markup is incomplete or contradicts the page
(questions without answers or not shown on the page, HowTo without steps,
ratings without a value or count, outside their scale or attached to nothing),
and `citation-schema-opportunity` when a page shows question headings, numbered
"how to" steps or rating text without matching markup.

## llms.txt

Acquisition parses llms.txt (`common/llms_txt.py`), checks the pages it lists
(crawled pages reuse the crawl result; at most 8 others get a same-origin,
robots-checked GET) and probes `/llms-full.txt`. `check_llms_txt.py` reports
`llms-txt-invalid` (no H1 title, no links, bare URLs, no sections, or an HTML
page served as llms-full.txt) and `llms-txt-broken-links` (listed pages that
answer 404 or 410). Links on other domains are listed, never requested.

## Core Web Vitals

`analyze_web_vitals.py` reports `cwv-field-poor` when Chrome UX Report field
data rates LCP, CLS or INP below good, and otherwise `cwv-risk` estimates from
markup patterns (slow HTML, a lazy-loaded first image, render-blocking head
resources, unsized embeds and images, heavy or third-party scripts). Estimates
are labelled as estimates and are dropped for a metric that field data rates
good.

## hreflang and multi-language sites

`analyze_international.py` reads hreflang from `<link rel="alternate">`, the HTTP
Link header and sitemap `xhtml:link` entries (no requests). `hreflang-invalid`
reports malformed codes (en_US, en-UK, a country used as a language), relative
URLs, one code pointing at two URLs, a missing self-reference, crawled alternates
that do not link back or answer 404/410, and a self code that differs from html
lang. `hreflang-missing` reports pages in two or more html languages with no
annotation anywhere. Codes are judged by shape and common mistakes, never by a
full registry, so a rare valid code is never reported.

## noscript fallback

`analyze_rendering.py` excludes `<noscript>` text from the raw-text count. Real
fallback text of substantial size still prevents a render-gap; a `<noscript>`
that only says JavaScript is required is cited as evidence and raises confidence.
A short page that loads no script and has no such `<noscript>` is never a
render-gap: nothing can add content to it after load, so its raw HTML is judged
like any other page.

Without a headless browser, a thin page that runs scripts is a suspected
render-gap only with a sign of client-side rendering in its raw HTML: an empty
app mount point, a framework bundle or attribute, page state serialized for a
script (`__NEXT_DATA__`, `window.__INITIAL_STATE__`), or a JavaScript-required
`<noscript>`. One sign makes it medium, two or more make it high. A thin page with
no sign, or a page whose text is mostly real links (a splash or chooser page), is
reported only as `render-gap-unconfirmed` (insufficient evidence).

## Text drawn in graphics

`analyze_graphics_text.py` reports `canvas-text` (a content-size canvas with no
fallback text, image alt, aria-label or title; suspected), `svg-inline-facts`
(prices, phones or specifications only inside inline SVG text; suspected) and
`icon-font-text` (private-use glyphs or ligature icon names in the page text).

## Image context and weight

`analyze_image_context.py` reports `image-context-missing`: content images with
no usable alt text and no figcaption, title, aria-label or link text. Images in
the header, navigation or footer, tiny images, logos and icons are skipped.

`analyze_image_weight.py` reads the up to 4 Range GETs acquisition made of the
largest same-origin content images (`Accept` lists AVIF and WebP). `image-weight`
reports files of 300 KB or more (medium at 1 MB, or 500 KB for the likely LCP
image), images twice their displayed width with no srcset, and 100 KB or larger
files still served as JPEG, PNG or GIF. `responsive-images` (suspected) reports a
page whose first content image has no srcset or `<picture>` source.
