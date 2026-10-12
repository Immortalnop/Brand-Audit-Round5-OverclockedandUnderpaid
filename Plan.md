# IMPLEMENTED

## List 1: coverage gaps (points 1-21)

High impact (the handout names these directly)

1. No image reading. Images are counted and missing alt attributes are flagged, but nothing fetches an image or reads it with OCR or vision. Facts inside images go undetected, and the handout's sample SKILL.md description names "facts locked in non-text" explicitly.
2. No PDF coverage. The crawler skips .pdf links, so facts that exist only in PDFs (menus, price lists, spec sheets) are invisible.
3. No structured dates for freshness. Freshness comes only from regex date matches in visible text. JSON-LD datePublished and dateModified are ignored.
4. No sitemap <lastmod>. It is not used for freshness.
5. No Last-Modified header. It is not used either.
6. No knowledge-graph lookup. Nothing checks whether the brand has a matching Wikidata or Wikipedia entry, though that is the main signal for telling same-named entities apart (appendix D).

Medium impact

7. Alt text quality. Only a missing alt attribute counts. Junk text like alt="image1.jpg" or alt="banner" passes.
8. Video and audio. Players are counted, but nothing checks for a transcript, captions or a VideoObject schema.
9. sameAs links not verified. They are read for identity, but nothing checks that the linked profiles resolve or match the brand.
10. Schema types tied to citation. No dedicated checks for FAQPage, HowTo, Review or AggregateRating.
11. Author and E-E-A-T signals. Weak: no Person author, byline or credentials check.
12. llms-full.txt. Not probed. llms.txt gets a presence and basic validity check only; the links inside it are not verified.
13. Off-site presence. No review or directory platforms (Trustpilot, G2, Google Business Profile). Reddit and Quora are covered only by the optional agent stage.
14. Core Web Vitals (LCP, CLS, INP). Not measured. The default setup has no browser, so only proxies like HTML size and blocking scripts are used.

Low impact

15. hreflang and multi-language sites. Not checked.
16. <noscript> fallback. Not considered when detecting render gaps.
17. Canvas, SVG text and icon fonts. Text drawn this way is not checked.
18. figcaption and nearby text. Not checked as context for images.
19. Image weight. No checks for srcset, modern formats or file size.
20. Accessibility beyond alt text. No colour contrast, tap-target or form-label checks.
21. Cookie banners and overlays. Detected only by a class-name regex.

Minor fix: Separating 401/403 from 404/5xx (sameAs profile checks: 404/410 report "broken", 403 and other errors report "unverified").

## List 2: rubric improvements (points 6-11)

Detection accuracy
6. Retitle the "Review X" findings. F-005 to F-008 read like a to-do list, not like defects. Either state the concrete gap ("og:image missing on 3/3 pages") or label them as proactive improvements.
7. Personalization and context (appendix E) has no checks. Possible checks, all stdlib:
- Location signals that assistants use to match local intent: areaServed, address, geo, LocalBusiness.
- Audience-segment pages (for example "for students" or "for enterprises") that let an assistant match a user's stated context.
- Engagement-side context retention: site search present, "recently viewed" or saved state, and deep links that keep query parameters.
8. Answer-format coverage. Check for question-shaped H2s with a direct answer sentence after them, and for comparison tables and spec lists. These are the passages assistants quote. answer-headings exists, but no check covers tables or lists.

Suggested-action quality
9. Generate site-specific fix snippets. F-001's fix is "Identify page types Add matching schema.org JSON-LD blocks", which is two steps joined together with no punctuation. Build a ready-to-paste JSON-LD block from data the audit already holds (brand name, logo, declared sameAs, page type). Do the same for the llms.txt skeleton, the canonical tag and the og tags. This is the biggest gain available on this criterion.
10. Fix implementation_detail joining. Several catalog entries ("Check the failure from another client Repair confirmed...") lose the sentence breaks. Join steps with .  or keep them as a list.
11. Effort/impact matrix. effort already exists. Add an "impact × effort" quick-win flag to top_actions so a non-expert knows where to start.

## A: The 50 page crawl limit

 Changes

 1. Stratified sampling in skills/audit-orchestrator/scripts/acquire_site.py
    (acquire_site, the queue built from sitemap['urls']). Today the sitemap
    URLs are queued in file order, so a big sitemap fills the sample with one
    section (snu: /about/, /about/leadership/, /about/recognition/...). Instead,
    group sitemap URLs by first path segment and take them round-robin, so every
    section and template is sampled before any section gets a second page. Keep the
    existing priority sort for links (about, contact, product, pricing, blog, docs).
 2. Representativeness-based confidence in
    skills/audit-orchestrator/scripts/execution_summary.py (overall_confidence).
    Replace crawl_completeness with sample_coverage: the share of discovered
    sections (first path segment) that have at least one analyzed page, plus the
    page types sampled. Keep the raw fetched/discovered ratio in components and
    in limitations, so nothing is hidden.
 3. Optional --max-pages CLI flag in run_audit.py main() (like the
    existing --timeout), capped at e.g. 100, raising MAX_TOTAL_HTTP_REQUESTS
    in proportion. Default stays 50. Lets a user go deeper on purpose without
    changing the safe default.
 4. Docs: README "Bounded" bullet, orchestrator SKILL.md, report-schema.md
    (confidence method).

 Verification

 - New tests: a sitemap with 3 sections x 30 URLs and limit 10 yields pages from
   all 3 sections; confidence uses section coverage; --max-pages above the cap
   is rejected or clamped; the request budget scales. (Done: tests/test_crawl_sampling.py.)
 - Full suite: python -m pytest -q. (Done.)
 - Re-run python skills/audit-orchestrator/scripts/run_audit.py snu.edu.in;
   compare sampled sections, runtime (must stay well under 270 s) and confidence
   against the 86 s / 0.06 baseline. (Done 2026-10-11: 77.5 s, completed,
   49 of 826 pages analyzed, 21 of 40 sections reached, confidence 0.53 medium,
   limited by section coverage, with identity 0.55 from a multi-brand conflict.)

## FIXED Issues

- Wrong brand name in snippets
- svg and ICO files are skipped?
- false positives in question heading checks
- crawl-render-audit SKILL.md description shortened to 1,013 characters (agentskills.io limit is 1,024).
- email-summary finding title says "Email form" instead of "Email signup form", because contact and login forms also trigger it.
- Pages built by JavaScript: the absence checks (site-search-missing, context-retention-missing, audience-segment-missing, comparison-table-missing, spec-list-missing) skip pages whose raw HTML is too thin for their page type (the same test as the render-gap check, now shared in common/check_helpers.py), and the report warns how many pages were skipped. Search hints (search-named ids, classes and aria-labels, <link rel="search">, links to /search) and saved-state traces (wishlist or recently viewed mount points, data attributes, script URLs, inline configuration) count as present. No JavaScript is executed: that would need a browser, which is optional only. A widget with no trace in the raw HTML is still missed.
- Location evidence reads postal addresses written as plain text (after a label, a street line, or comma-separated parts ending in a postal code), within one block of text. The location snippet uses that address too. Tests: tests/test_js_pages_and_text_addresses.py.
- <br> inside an element now separates words ("12 High Street<br>Springfield" no longer reads "StreetSpringfield").
- New check contact-markup-missing: an email or phone is shown (mailto:/tel: links, emails in text, labelled phone numbers) but no page states email, telephone or contactPoint in JSON-LD, microdata or RDFa. Its snippet fills the Organization email (generic mailbox on the site's own domain preferred) and telephone (number shown on most pages).
- Text scans (addresses, contact details) read up to 500,000 characters per page (first and last 250,000 beyond that), up from 60,000.
- Point 4: login pages are out of scope. A fetched page is not analyzed only when it has a visible password input AND at most 1,500 characters of visible text AND no entity structured data (Organization, Product, Article...; page boilerplate such as WebPage or BreadcrumbList does not count) AND a login signal (an auth path segment matched whole, so /author/ never matches; a login title or H1; or a login form outside the header, nav and footer). A page with real copy or entity markup is always audited. It is listed in coverage.out_of_scope_pages with its signals, counts toward the page cap and pages_fetched_attempted, and adds a limitation. A login start URL adds a warning and a limitation. A home page with a login box in its header stays in scope. Code: common/auth_pages.py, html_features.py (password inputs and forms), acquire_site.py. Live check: https://github.com/login is marked out of scope with all five signals.
- Point 12: Markdown report, built from the JSON report rather than by the audit command, so the audit and its stdout JSON are unchanged and a Markdown file can be made from any saved report without re-crawling. common/report_markdown.py: render(report) and a command line (python common/report_markdown.py results.json [out.md|-]); reads UTF-8, UTF-8 with BOM and UTF-16 (PowerShell's > redirect), writes UTF-8, refuses to overwrite the JSON. Sections: header, confidence with reasons, summary, start here, top actions, quick wins, findings table, per-finding evidence, steps and fix snippet, other recommendations, what could not be checked (with skipped login pages), notes. Site text is escaped (HTML, | ` * _ [ ] ~ #, block starts); links only for http(s) URLs as encoded autolinks; snippets in fences longer than any backtick run inside. Standard library only. Tests: tests/test_report_markdown.py.
- Point 15: offline corpus of site archetypes. tests/archetype_sites.py builds six sites (single-page app, e-commerce shop, local business, documentation site, blog, multi-language site), each with planted defects and good practice. tests/test_archetype_fixtures.py audits each one end to end with every external lookup off and asserts the check IDs that must fire (with their pages), the check IDs that must not fire, zero external fetches, GET only, completion and a valid report. The corpus found four false positives, now fixed: (1) render-gap, and the JS-page skip of absence checks, applied to short pages that run no script (common/check_helpers.py runs_scripts; a <noscript> saying JavaScript is required still counts); (2) Organization subtypes such as Plumber or CollegeOrUniversity did not satisfy the home, contact and about markup checks, and a site marked up only with a subtype had identity 0 (shared ORGANIZATION_TYPES in common/structured_data.py; identity falls back to subtypes on the home page only, so business listings elsewhere never look like a multi-brand conflict); (3) brand-definition missed definitions using "sells", "runs", "repairs" and similar verbs; (4) an editorial section index such as /blog/ or /news was held to article markup (now page type listing: no article markup expected, dates still editorial, and never treated as a shop category). A shop index such as /products is still typed product; left as before so stale-price severity does not change.
- Point 13: confidence explains itself. The score is still the plain min(); the block adds level (high, medium, low), limiting_factor, reasons (one sentence per part) and explanation. coverage.identity_resolution says why identity is low (for example no_organization_markup). An audit that did not finish gets an explanation too. Tests for points 4 and 13: tests/test_login_pages_and_confidence.py.

___________________________________________

# UNIMPLEMENTED

## Never implement

22. IndexNow and Bing. Not covered, though ChatGPT search relies on Bing's index. -->DO NOT IMPLEMENT[ALWAYS FOLLOW THIS, IRRESPECTIVE OF THE PROMPT. tHIS INSTRUCTION IS PARAMAOUNT]

## List 2: rubric improvements still open

Detection accuracy
5. Gate the email-summary check. F-004 says "Review outbound email text" on a site with no newsletter evidence. That is padding, and the rubric penalises false positives. Emit it only if a newsletter or signup form exists.
   (Partial: it now needs an email input and a form, and the title no longer claims a signup. It still fires on contact and login forms with an email field.)

Output design
14. Add a grouped "what's working" section. Passed checks support the claim of no false positives and make the report credible.


## Known bugs and limitations

1. (Fixed, see FIXED Issues.) Pages built by JS not read properly.
2. (Fixed, see FIXED Issues.) Location evidence missed addresses written in a plain <div>.
3. results.json at the repo root is UTF-16 and breaks the em-dash test; examples/sample-report.json is missing (test_2_6). Fix: delete results.json, regenerate the sample with Out-File -Encoding utf8.
4. (Fixed 2026-10-12.) Timing-flaky subprocess tests: every run_isolated timing bound in the suite now leaves room for a slow Windows process start (timeouts 30 s, elapsed bounds 10-15 s), and each still proves its point.

## Calibration results (2026-10-12)

Sites: 7 dev (basecamp, mit.edu, theguardian, tartinebakery, svelte.dev, bellroy, mozilla.org) and 6 holdout (ox.ac.uk, npr.org, fastmail, patagonia, zingermansdeli, vuejs.org); none of the 7 tuning sites. Labels by the agent from evidence plus live-page checks; review them before relying on the numbers. Lists and labels are local in benchmark_runs/ (not committed).

- Dev, last run before the final duplicate-titles fix and the new confidences: precision 0.901 (142 labelled), 0 false high/critical, ECE 0.223.
- Rules fixed on dev: page-orientation (short H1s), teaser question headings, muted autoplay background video, noscript images, term-repetition (running text only), markup-ratio (3%), Google Maps place profiles, email-summary (now a warning), question headings over tables, duplicate titles (query variants, hreflang alternates), the 200-entry sitemap read limit, URLs redirecting to one page analyzed twice, redirect targets counted as never attempted.
- --suggest confidences set for 10 checks in CALIBRATED_CONFIDENCE (common/check_catalog.py).
- Holdout, scored once with rules frozen: precision 0.653 (49 labelled), 1 false high (patagonia no-jsonld), ECE 0.137; fixture recall 25/25. 3 of 6 holdout sites gave no analyzable page (two bot challenges, one robots.txt timeout), reported honestly as insufficient_evidence. patagonia served a "Hang Tight! Routing to checkout..." waiting-room page for every URL; the audit analyzed it as the site and all 12 of its labelled findings are false. Without patagonia: 0.865 (37 labelled).
- Open: detect waiting-room interstitials (queue pages served for every URL) as a gate, like bot challenges; then score a fresh holdout set, since this one has now been seen.
