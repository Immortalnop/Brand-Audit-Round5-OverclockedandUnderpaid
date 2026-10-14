# Content-header correction, October 14, 2026

The shared markup-context classifier treated every header as site chrome. That
excluded Fastmail's genuine introductory paragraph and H1 inside main content.
AG-01 therefore received a later recruitment paragraph, and the native H1 check
reported headings that were present as missing.

An ordinary header with a main, section or article ancestor now contributes to
body openings, body text, focused sections and main headings. A document header,
navigation, footer, custom site-header/announcement element, explicit banner /
navigation / contentinfo role or chrome ancestor remains excluded. Hidden content
continues to be excluded by the existing visibility checks. Auth-form and image
classification heuristics, acquisition limits, host timing and validation were
not changed. No brand-specific exception was introduced.

Fifteen production-path regressions cover content headers inside main and role
main, section/article headers without a main landmark, document/ancestor chrome,
explicit chrome roles, hidden headers, genuine outline skips and exact About
fragments. Eight regression cases failed before the correction. The full checkout
suite passed 1,403 tests; full-suite.txt records the result.

fastmail-same-html.json compares both parsers against the same complete 60,045-byte
Fastmail About HTML response saved during the earlier read-only verification. The
corrected opening starts with the site's email-service introduction and its H1
is retained. Broad packet text still declares partial comparison coverage. This
is a production-path reparse, not an edited historical report or a new Claude
assessment.

native-fastmail.json records a fresh default 50-page native audit: exit 0,
completed, 24.899 seconds wall time, 50 of 222 discovered pages and 13 of 15
sections. It exported the corrected complete AG-01 opening and no missing-H1
finding. Against the supplied 8.4.2 base, the missing-H1 check disappears; the
heading-hierarchy scope moves from the homepage to an article after retaining
content headers. Other common native findings preserve severity, status, type
and affected URLs. This development run correctly records a dirty code version.
The Claude host stage was not run; its outcomes are not fabricated.

The canonical prompt and embedded replay remain identical. They continue to use
default 50 pages, the existing shared clock and Opus launch. No target-HTML
re-fetch workaround, changed evidence threshold or new prompt instruction is
needed. Existing bound packets and agent outcomes retain their old observations;
a fresh intended-laptop Claude run is required to assess the corrected opening.

The separately identified inert-template control issue remains pending. This
release fixes the selected content-header problem; it does not certify every
existing Fastmail finding. Release archive metadata and extracted-suite validation
will be recorded alongside this review after the committed build.
