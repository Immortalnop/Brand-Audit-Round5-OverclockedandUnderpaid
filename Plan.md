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
22. IndexNow and Bing. Not covered, though ChatGPT search relies on Bing's index.