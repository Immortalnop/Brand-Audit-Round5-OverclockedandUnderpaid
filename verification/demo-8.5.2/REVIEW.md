# Inactive-template parser correction, October 14, 2026

The previous parser omitted template text but still observed descendant element
tags. A named button inside a template could therefore become an unnamed active
control. The same mismatch could affect headings, links, images, metadata,
structured data, form/authentication signals and inline stylesheet visibility.
Ordinary HTML template contents belong to an inert document fragment, as specified
by the [HTML Standard](https://html.spec.whatwg.org/multipage/scripting.html#the-template-element).

A shared TemplateScope now isolates these fragments in both Document extraction
and the inline-style prepass. No descendant observers run, and inner end tags
cannot close live ancestors. Nested templates, comments, escaped text, raw-text
and RCDATA strings, unclosed fragments, non-void self-closing syntax and chunked
input are covered. Ignored starts still count against the node budget; template
nesting counts against the depth budget. The prepass retains its existing CSS
size limit and conservative override handling. No JavaScript is executed and no
browser, dependency, target re-fetch or extra agent stage is added.

The final 68 regressions ran against a separate copy of release 8.5.1: 38 failed
and 30 passed. All 68 pass after the correction. Production-path cases compare
every retained acquisition observation with/without inserted templates, ensure
inactive labels cannot name real inputs, keep live CSS rules and genuine
accessibility/heading defects, and execute a complete offline audit. Inactive
links/assets are never requested; real defects retain their correct page scope.

The complete checkout suite passed 1,511 tests in 123.18 seconds. It includes
unrelated crawling, redirects, robots, challenges, transport/TLS/SSRF/budget
handling, schema/date/authorship checks, evidence/envelope validation, merge,
Markdown rendering, URL page overrides, output layout and complete repair export.
All 149 Python source files parse with the Python 3.10 syntax grammar; this is a
syntax check, not execution on every Python/OS combination. Actual Claude 2.1.299
plugin validation passed. Engine/plugin/catalog versions match at 8.5.2. The
canonical prompt still exactly matches its embedded replay; the workflow and
AG evidence contracts were not changed by this parser correction.

Before/after comparison against the same saved HTML keeps every observation on
44 fixture pages unchanged. Seven saved Fastmail/Bare Necessities pages were
also reparsed without website requests. Fastmail's beta download and older blog
pages lose the inactive unnamed-button signal (1 to 0); Fastmail About retains
its introductory opening and H1. The Bare Necessities book loses inactive control
counts, while its unnamed count stays zero. Its homepage retains three genuine
unnamed links. Other saved observations change only where inactive descendants
were previously counted; all seven AG-01 body openings remain identical.

These checks establish the behavior of the static extractor and the tested
pipeline. They do not certify every human judgment or every possible webpage.
Runtime template insertion and declarative shadow DOM still need browser
validation; no rendered state or complete accessibility tree is claimed. No
authenticated Claude demo run was performed here. Existing reports, packets,
user archives and source HTML remain unchanged; fresh acquisition is required
to obtain corrected report observations.

Package and extracted-release checks are recorded alongside this review after
building from the committed runtime source.
