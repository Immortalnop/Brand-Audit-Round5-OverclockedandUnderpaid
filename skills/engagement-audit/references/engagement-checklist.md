# Engagement checklist

- Orphan pages (no inbound internal links)
- Dead-end pages (no outbound internal links)
- Navigation/breadcrumb consistency: visible breadcrumbs vs BreadcrumbList
  JSON-LD
- Rendering-gap pages (from crawl-render-audit's rendering_result) as context
  for engagement, not duplicated as a separate finding
- Generic internal anchor text (for example "read more", "click here") when a
  meaningful sample of internal anchors is available
- Weak page orientation on substantial non-home pages whose primary heading is
  missing, generic ("Home", "Welcome") or paragraph-length; a short clear H1 such
  as "API reference" passes
- Internal discoverability gaps: substantial pages that expose almost no
  internal links onward
- Email-summary-friendly formatting (Appendix Concept F): only when a real
  newsletter or mailing-list signup is present (email field, newsletter or
  subscribe wording, no password field). Contact, trial and login forms with an
  email field never count. email-summary-readable additionally needs the signup
  page's own message in images: under 60 words and most images without alt text
