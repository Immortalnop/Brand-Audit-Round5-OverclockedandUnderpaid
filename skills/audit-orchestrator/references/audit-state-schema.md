# Audit state schema

`AuditArtifacts` (frozen, read-only): `site_url`, `normalized_origin`, `pages`
(tuple of `PageArtifact`), `robots_data` (status, RFC 9309 verdict, access
verdict, `ai_crawler_directives`, `ai_crawler_paths`), `llms_txt_data`,
`sitemap_data` (urls, lastmod), `acquisition_metadata` (coverage incl.
templates_sampled and urls_challenged, https_probe, asset_links, asset_probes,
challenged_probes, transport diagnostics), `warnings`.

`PageArtifact` (frozen): url, status_code, content_type, evidence_snippet,
visible_text, title, meta_description, canonical_url, headings, internal_links,
external_links, jsonld_blocks, page_type, fetch_duration_ms, render_status,
breadcrumb_visible, breadcrumb_schema, ai_crawler_directives, warnings
(incl. `bot_challenge` / `rate_limited`), features (parser observations incl.
`access`, `region_links`, `images_meta`, `iframes`, `time_values`,
`footer_text`, `hydration_strings`, `spa_mount_empty`), response_headers,
final_url.

No specialist may mutate, append to, or replace fields on either dataclass.
Content checks use `check_helpers.content_pages()`, which excludes challenged,
truncated, unparsed and non-HTML pages.
