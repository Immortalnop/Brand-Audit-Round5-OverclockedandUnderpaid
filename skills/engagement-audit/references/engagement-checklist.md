# Engagement checklist

- Orphan pages (no inbound internal links) and isolated page clusters. Graph
  nodes are pages at their final URL: a crawled URL that redirected is the page
  it lands on, URLs redirecting to one page are one node, and a trailing slash
  does not hide a link. Both are reported only when the crawl reached every
  discovered URL. On a sampled crawl a page the sample does not link to may be
  linked from a page that was not fetched (a section index often lists only its
  newest items), so they are counted in metrics and the report says they were
  not assessed. A start page that reaches no other sampled page (a splash or
  language chooser) never makes the rest of the site an isolated cluster.
- Dead-end pages (no outbound internal links; a link to the page itself does
  not count)
- Navigation/breadcrumb consistency: visible breadcrumbs vs BreadcrumbList
  JSON-LD
- Rendering-gap pages (from crawl-render-audit's rendering_result) as context
  for engagement, not duplicated as a separate finding
- Generic internal anchor text (for example "read more", "click here") when a
  meaningful sample of internal anchors is available
- Weak page orientation on substantial non-home pages with no H1, or whose
  first headings are all empty or longer than 14 words (a short H1 such as
  "About us" orients a visitor)
- Internal discoverability gaps: substantial pages that expose almost no
  internal links onward
- Email-summary-friendly formatting (Appendix Concept F): email-capture pages
  whose substance is carried in images rather than readable text. A newsletter
  signup on its own is named in the report warnings, not reported as a finding:
  the emails it sends cannot be checked from the site

- Accessibility beyond alt text (`analyze_accessibility.py`): unlabeled form
  fields (`form-label-missing`), links and buttons with no accessible name
  (`control-name-missing`), inline colour pairs below WCAG AA
  (`low-contrast-text`) and inline-sized targets under 24 by 24 px
  (`tap-target-small`, suspected). Stylesheet colours and sizes need a browser
  and are stated as a limitation.
- Overlays (`analyze_overlays.py`): aria-modal dialogs, full-screen fixed
  layers, scroll locks, consent-platform markup and scripts, and overlay class
  names (`overlay`, suspected; medium only with a scroll lock). A non-blocking
  consent banner is never reported. Cookie wording in the meta description,
  og:description or title is `consent-text-leak` (confirmed); at the start of
  the page text it is suspected. Cookie and privacy policy pages are skipped.
- Context retention (`analyze_context_retention.py`, handout appendix E):
  - `site-search-missing` (low, suspected): the sitemap or crawl lists 50 or
    more URLs, and no sampled page has a search input, a `role="search"` form,
    a search-named field, a WebSite SearchAction, or a hint that JavaScript
    builds one (an id, class or aria-label starting with "search",
    `<link rel="search">`, a relative link to /search).
  - `context-retention-missing` (low, suspected, confidence 0.4): two or more
    product or category pages with no wishlist, save-for-later, compare or
    recently viewed control in the HTML, and no trace of a widget that
    JavaScript fills in (a mount point, data attribute, script or stylesheet
    URL, or inline configuration naming a wishlist, recently viewed or
    save-for-later list). A widget with no trace at all is still missed.
  - Pages built by JavaScript (raw-HTML text below the render-gap threshold for
    their page type) are not judged by these two checks; the report warns how
    many were skipped.
  - `deep-link-params-dropped` (low, confirmed): a crawled URL whose redirect
    removed content query parameters. Tracking parameters (utm_*, gclid,
    fbclid and similar) are ignored.
