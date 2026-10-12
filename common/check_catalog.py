"""Single source of truth for check mechanisms, implementation details and outcomes.

Stable check IDs are distinct from per-report finding IDs. This catalog contains
implemented checks only. Observed evidence, scope and status stay with detectors.
Unknown IDs fail validation on the public audit path rather than silently acquiring
empty enrichment. Donor IDs are aliases for traceability, never duplicate jobs.
"""
from types import MappingProxyType

_BASE = {'about-concreteness': {'expected_outcome': 'Identity answers can be composed from the brand own concrete wording '
                                            'rather than paraphrased from elsewhere.',
                        'implementation_detail': 'Rewrite the opening of the About page to state who the '
                                                 'organization is, what it sells or does, and in which '
                                                 'category or market.',
                        'mechanism': 'Assistants lift the About passage for identity questions; wording that '
                                     'names no product and no category gives them nothing quotable.'},
 'no-independent-mention': {'expected_outcome': 'Independent third-party mentions accumulate as corroborating '
                                               'sources over time.',
                           'implementation_detail': 'Participate authentically where the brand category is '
                                                    'discussed and keep the off-site name identical to the '
                                                    'site.',
                           'mechanism': 'A brand discussed nowhere but its own site is a single fragile '
                                        'assertion that retrieval systems cannot corroborate.'},
 'independent-contradiction': {'expected_outcome': 'Independent sources and the site agree, so the fact is '
                                                  'repeated confidently by assistants.',
                              'implementation_detail': 'Reconcile the conflicting fact: correct it at the '
                                                       'wrong source and state the accurate version on-site '
                                                       'and in Organization markup.',
                              'mechanism': 'When independent sources describe the brand differently from the '
                                           'site, retrieval surfaces the discrepancy and confidence drops '
                                           'across every associated fact.'},
 'ai-crawler-blocked': {'expected_outcome': 'Improves the affected sampled pages when the observed condition '
                                            'is confirmed.',
                        'implementation_detail': 'Review the affected evidence and apply the page-specific '
                                                 'action steps; verify the change by repeating the audit.',
                        'mechanism': 'The observed condition can limit retrieval or visitor access on '
                                     'sampled pages.'},
 'ai-crawler-unchecked': {'expected_outcome': 'Enables a real verdict',
                          'implementation_detail': 'Re-run once reachable',
                          'mechanism': 'The observed condition can limit retrieval or visitor access on '
                                       'sampled pages.'},
 'answer-headings': {'expected_outcome': 'May improve answer readability; questions are not required for '
                                         'retrieval or citation.',
                     'implementation_detail': 'Review audience questions and add useful question headings '
                                              'with concise answers; do not add empty FAQs or inappropriate '
                                              'schema.',
                     'mechanism': 'Question-shaped sections may help readers locate direct answers where '
                                  'that format fits the content.'},
 'app-identity': {'expected_outcome': 'Improves web software identity markup; app-store rankings are not '
                                      'assessed.',
                  'implementation_detail': 'Verify SoftwareApplication name, applicationCategory and '
                                           'operatingSystem against visible product facts; do not invent '
                                           'app-store claims.',
                  'mechanism': 'Observed application markup may omit useful software identity details.'},
 'baseline:ai_discoverability': {'expected_outcome': 'Discoverability regressions are caught close to the '
                                                     'change that caused them rather than months later.',
                                 'implementation_detail': 'Schedule a periodic re-audit and re-validate '
                                                          'structured data and crawler directives after '
                                                          'template, CMS or policy changes.',
                                 'mechanism': 'Crawlers, robots policies and structured-data conventions '
                                              'change independently of visible site content.'},
 'baseline:engagement': {'expected_outcome': 'Pages stay reachable and hand visitors a relevant next step '
                                             'as the site grows, instead of accumulating orphans.',
                         'implementation_detail': 'Link new pages inbound and outbound with descriptive '
                                                  'anchors as they launch, treating internal linking as '
                                                  'part of publishing.',
                         'mechanism': 'New pages commonly launch without inbound links or a clear next step.'},
 'baseline:off_site_presence': {'expected_outcome': 'Corroboration of the brand identity grows more robust '
                                                    'and less dependent on any single source.',
                                'implementation_detail': 'Maintain a small set of authoritative, '
                                                         'identity-consistent off-site profiles and pursue '
                                                         'diverse independent mentions over time.',
                                'mechanism': 'Off-site presence is cumulative, so it benefits from continued '
                                             'diverse independent mentions.'},
 'blocking-scripts': {'expected_outcome': 'May reduce parser blocking; no paint or Core Web Vitals '
                                          'improvement is measured here.',
                      'implementation_detail': 'Review script dependencies and defer or asynchronously load '
                                               'noncritical scripts where safe.',
                      'mechanism': 'Classic external head scripts without async or defer can block parser '
                                   'progress.'},
 'brand-definition': {'expected_outcome': 'Provides clearer identity wording without guaranteeing citation.',
                      'implementation_detail': 'Write a factual description of what the brand does and for '
                                               'whom, consistent with visible organization facts.',
                      'mechanism': 'An explicit short description can reduce ambiguity about an '
                                   'organization.'},
 'breadcrumb-mismatch': {'expected_outcome': 'Improves machine understanding of site structure',
                         'implementation_detail': 'Add BreadcrumbList schema to pages with visible '
                                                  'breadcrumbs',
                         'mechanism': 'Breadcrumb navigation is visible but not machine-readable'},
 'broken-pages': {'expected_outcome': 'Improves crawl completeness',
                  'implementation_detail': 'Audit error pages Add 301 redirects or restore content',
                  'mechanism': 'The observed condition can limit retrieval or visitor access on sampled '
                               'pages.'},
 'contradicted-claim': {'expected_outcome': 'Reduces risk of assistants surfacing conflicting facts',
                        'implementation_detail': 'Compare the on-site value to the external source Correct '
                                                 'whichever is stale or update the other listing',
                        'mechanism': 'The observed condition can limit retrieval or visitor access on '
                                     'sampled pages.'},
 'cross-origin-canonical': {'expected_outcome': 'Avoids unintended consolidation while preserving legitimate '
                                                'syndication.',
                            'implementation_detail': 'Verify ownership and content equivalence; correct the '
                                                     'URL only if the external canonical is unintended.',
                            'mechanism': 'An external canonical can nominate another origin as the preferred '
                                         'copy.'},
 'dead-ends': {'expected_outcome': 'Keeps visitors engaged longer',
               'implementation_detail': 'Add related-content links Add a clear next-step call-to-action',
               'mechanism': 'Pages provide no next step for the visitor'},
 'duplicate-titles': {'expected_outcome': 'Helps readers distinguish the sampled pages.',
                     'implementation_detail': 'Give distinct content pages descriptive titles; retain '
                                              'intentional duplicates where justified.',
                     'mechanism': 'Repeated titles can obscure differences between pages.'},
 'email-summary': {'expected_outcome': 'Improves message readability if gaps are confirmed.',
                   'implementation_detail': 'Review actual outbound messages for useful plain text and '
                                            'multipart alternatives.',
                   'mechanism': 'An email capture form does not reveal the readability of outbound '
                                'messages.'},
 'fetch-failure': {'expected_outcome': 'Restores reliable access when the failure is reproducible',
                   'implementation_detail': 'Check the failure from another client Repair confirmed '
                                            'certificate or server failures',
                   'mechanism': 'A fetch failure limits this audit; it does not establish a permanent '
                                'site-wide outage.'},
 'fetch-latency': {'expected_outcome': 'Can improve retrieval reliability; audit pacing and retries are '
                                       'excluded from this observation.',
                   'implementation_detail': 'Repeat timings from representative clients and investigate '
                                            'network or server delays before applying caching or backend '
                                            'changes.',
                   'mechanism': 'Slow observed HTML retrieval reduces the amount of evidence available '
                                'within a deadline.'},
 'footprint-signal': {'expected_outcome': 'Improves the affected sampled pages when the observed condition '
                                          'is confirmed.',
                      'implementation_detail': 'Review the affected evidence and apply the page-specific '
                                               'action steps; verify the change by repeating the audit.',
                      'mechanism': 'The observed condition can limit retrieval or visitor access on sampled '
                                   'pages.'},
 'h1': {'expected_outcome': 'Makes the page topic easier to identify.',
        'implementation_detail': 'Add a descriptive page heading when the template lacks an equivalent '
                                 'accessible title.',
        'mechanism': 'An absent primary heading can weaken page orientation.'},
 'hash-routing': {'expected_outcome': 'Makes route-specific content retrievable without assuming browser '
                                      'deep links are broken.',
                  'implementation_detail': 'Verify each destination by direct arrival and raw HTML; use '
                                           'server-resolvable paths where needed.',
                  'mechanism': 'Hash route fragments are absent from the HTTP request path.'},
 'heading-hierarchy': {'expected_outcome': 'Improves outline consistency without requiring an arbitrary '
                                           'visual style.',
                       'implementation_detail': 'Review the outline and nest headings according to the '
                                                'document hierarchy.',
                       'mechanism': 'Skipped heading levels can make section relationships less clear.'},
 'heavy-html': {'expected_outcome': 'Reduces bytes required to retrieve the primary document.',
                'implementation_detail': 'Trim unnecessary inline payloads and paginate only where useful; '
                                         'retain essential content.',
                'mechanism': 'Large HTML bodies consume the bounded retrieval budget.'},
 'homepage-orientation': {'expected_outcome': 'Visitors arriving from an AI answer can orient quickly and '
                                              'continue to a relevant action',
                          'implementation_detail': 'State what the organization offers and for whom in the '
                                                   'first viewport Use a descriptive H1 and scannable H2 '
                                                   'sections Place one relevant CTA near the opening content',
                          'mechanism': 'The sampled homepage contains substantial text but no short heading '
                                       'signal was observed in its first heading entries'},
 'http-transport': {'expected_outcome': 'Protects transport confidentiality and integrity; ranking gains are '
                                        'not asserted.',
                    'implementation_detail': 'Serve the public site over verified HTTPS; verify the '
                                             'canonical HTTPS URL and redirect policy before deployment.',
                    'mechanism': 'HTTP does not encrypt the fetched connection.'},
 'image-sizing': {'expected_outcome': 'Can reduce layout movement and unnecessary loading; layout shift is '
                                      'not measured.',
                  'implementation_detail': 'Check CSS sizing and aspect-ratio before adding width and '
                                           'height; lazy-load only suitable below-fold images.',
                  'mechanism': 'Images without dimensions may lack reserved space unless CSS already '
                               'supplies it.'},
 'invalid-canonical': {'expected_outcome': 'Provides a consistent preferred-URL hint without proving index '
                                           'selection.',
                       'implementation_detail': 'Publish one valid HTTP(S) canonical pointing to the '
                                                'intended equivalent page; avoid fragments and conflicting '
                                                'declarations.',
                       'mechanism': 'An unusable or conflicting canonical declaration weakens the '
                                    'preferred-URL hint.'},
 'isolated-clusters': {'expected_outcome': 'Makes an entire section reachable instead of one page at a time',
                       'implementation_detail': 'Identify which cluster(s) contain valuable content Add '
                                                'navigation or contextual links connecting them to the main '
                                                'site',
                       'mechanism': 'The observed condition can limit retrieval or visitor access on sampled '
                                    'pages.'},
 'llms-txt-unchecked': {'expected_outcome': 'Enables a real presence/absence verdict',
                        'implementation_detail': 'Check that /llms.txt responds Re-run the audit',
                        'mechanism': 'The observed condition can limit retrieval or visitor access on '
                                     'sampled pages.'},
 'long-paragraphs': {'expected_outcome': 'Improves readability of the observed long passages.',
                     'implementation_detail': 'Split dense passages by topic and use appropriate lists or '
                                              'tables.',
                     'mechanism': 'Dense paragraphs can hide important answers.'},
 'malformed-jsonld': {'expected_outcome': 'Prevents parsers from dropping important entity and product facts',
                      'implementation_detail': 'Validate each JSON-LD block as strict JSON Preserve valid '
                                               '@graph nodes and required properties Re-run a '
                                               'structured-data validator after deployment',
                      'mechanism': 'One or more sampled pages contain JSON-LD that could not be parsed, so '
                                   'structured facts may be discarded by automated readers'},
 'markup-ratio': {'expected_outcome': 'Reduces document overhead if the sampled ratio reflects avoidable '
                                      'markup.',
                  'implementation_detail': 'Inspect inline assets and template boilerplate before trimming '
                                           'unnecessary HTML.',
                  'mechanism': 'A small visible-text share in a large HTML document can indicate excess '
                               'markup.'},
 'missing-alt': {'expected_outcome': 'Improves accessible alternatives without treating decorative images as '
                                     'missing content.',
                 'implementation_detail': 'Describe informative images; use empty alt for decorative images '
                                          'and preserve equivalent nearby text.',
                 'mechanism': 'Missing alt attributes can omit informative image meaning from text '
                              'alternatives.'},
 'missing-canonical': {'expected_outcome': 'Helps supporting consumers consolidate duplicate URLs when '
                                           'applicable.',
                       'implementation_detail': 'Assess real duplicates before declaring the correct '
                                                'absolute canonical URL.',
                       'mechanism': 'A missing canonical declaration provides no explicit preferred-URL '
                                    'hint.'},
 'missing-description': {'expected_outcome': 'Provides a summary candidate; search engines may choose other '
                                             'text.',
                         'implementation_detail': 'Write a concise page-specific meta description that '
                                                  'matches visible content.',
                         'mechanism': 'An absent description removes an optional page summary hint.'},
 'missing-landmarks': {'expected_outcome': 'Improves structural clarity for supporting readers and '
                                           'extractors.',
                       'implementation_detail': 'Mark the main content semantically and keep navigation '
                                                'outside it when appropriate.',
                       'mechanism': 'Content without a main or article landmark may be harder to distinguish '
                                    'from boilerplate.'},
 'missing-language': {'expected_outcome': 'Gives consumers an explicit language hint.',
                      'implementation_detail': 'Set an accurate BCP 47 lang attribute on the html element; '
                                               'verify multilingual sections separately.',
                      'mechanism': 'A missing document language can impede assistive pronunciation and '
                                   'language interpretation.'},
 'missing-title': {'expected_outcome': 'Improves identification in browser tabs and supporting search '
                                       'surfaces.',
                   'implementation_detail': 'Add a unique descriptive title identifying the actual page '
                                            'topic.',
                   'mechanism': 'A missing document title omits a primary page label.'},
 'next-step': {'expected_outcome': 'Makes the appropriate next step clearer.',
               'implementation_detail': 'Add a relevant purchase, inquiry or comparison route if no '
                                        'equivalent path exists.',
               'mechanism': 'Commercial pages without an observed action path can leave visitors unsure how '
                            'to proceed.'},
 'no-headings': {'expected_outcome': 'Improves text extraction quality',
                 'implementation_detail': 'Add an h1 per page Structure sections with h2/h3',
                 'mechanism': 'Pages have no h1-h6 elements'},
 'no-internal-navigation': {'expected_outcome': 'Reduces dead ends and helps both visitors and crawlers '
                                                'discover deeper content',
                            'implementation_detail': 'Expose primary destinations in a semantic nav landmark '
                                                     'Link related pages from body content Ensure every '
                                                     'important landing page has a clear next step',
                            'mechanism': 'Visitors landing on the sampled pages have no observed internal '
                                         'link path to related content'},
 'no-jsonld': {'expected_outcome': 'Facts become machine-extractable',
               'implementation_detail': 'Identify page types Add matching schema.org JSON-LD blocks',
               'mechanism': 'The observed condition can limit retrieval or visitor access on sampled pages.'},
 'no-llms-txt': {'expected_outcome': 'Offers an optional guide to tools that support this convention; not a '
                                     'search eligibility requirement',
                 'implementation_detail': 'Create /llms.txt List key pages and a short site summary',
                 'mechanism': 'Site does not publish an llms.txt guidance file'},
 'noindex': {'expected_outcome': 'Restores indexing eligibility for the specified crawler, without '
                                 'guaranteeing indexing.',
             'implementation_detail': 'Confirm indexing is intended before removing noindex or none from '
                                      'meta and response headers.',
             'mechanism': 'A scoped noindex instruction can exclude a page from the affected search index.'},
 'nosnippet': {'expected_outcome': 'Restores snippet eligibility where the consumer supports this directive.',
               'implementation_detail': 'Keep intentional controls; remove an unintended nosnippet directive '
                                        'from meta or response headers.',
               'mechanism': 'A scoped nosnippet instruction restricts snippet use by supporting consumers.'},
 'snippet-suppression': {'expected_outcome': 'Restores text-snippet and image-preview eligibility for supporting consumers, so a clear fact can be quoted.',
                         'implementation_detail': 'Remove max-snippet:0 or raise it to a positive value, and restore max-image-preview from none, only where the suppression is unintended; keep deliberate controls.',
                         'mechanism': 'max-snippet:0 and max-image-preview:none keep a page indexed but remove the snippet or preview an assistant or search result would quote, so a plainly visible fact is far less likely to be surfaced.'},
 'orphan-pages': {'expected_outcome': 'Improves discoverability and visitor navigation',
                  'implementation_detail': 'Identify high-value orphan pages Link them from navigation or '
                                           'related content',
                  'mechanism': 'The observed condition can limit retrieval or visitor access on sampled '
                               'pages.'},
 'overlay': {'expected_outcome': 'Reduces interference only if confirmed in a browser.',
             'implementation_detail': 'Inspect actual behavior and provide a dismiss control if the overlay '
                                      'obstructs content.',
             'mechanism': 'Overlay-related markup may indicate an obstruction, but static HTML cannot '
                          'establish visibility or timing.'},
 'page-type-schema-gap:about': {'expected_outcome': 'Improves explicit context without asserting that schema '
                                                    'is mandatory for indexing or citations.',
                                'implementation_detail': 'Review the about classification, then add truthful '
                                                         'AboutPage or Organization markup only where '
                                                         'applicable and validate it.',
                                'mechanism': 'Page-appropriate structured data can make visible facts more '
                                             'explicit to supporting consumers.'},
 'page-type-schema-gap:article': {'expected_outcome': 'Improves explicit context without asserting that '
                                                      'schema is mandatory for indexing or citations.',
                                  'implementation_detail': 'Review the article classification, then add '
                                                           'truthful Article, BlogPosting or NewsArticle '
                                                           'markup only where applicable and validate it.',
                                  'mechanism': 'Page-appropriate structured data can make visible facts more '
                                               'explicit to supporting consumers.'},
 'page-type-schema-gap:contact': {'expected_outcome': 'Improves explicit context without asserting that '
                                                      'schema is mandatory for indexing or citations.',
                                  'implementation_detail': 'Review the contact classification, then add '
                                                           'truthful ContactPage or applicable organization '
                                                           'markup markup only where applicable and validate '
                                                           'it.',
                                  'mechanism': 'Page-appropriate structured data can make visible facts more '
                                               'explicit to supporting consumers.'},
 'page-type-schema-gap:home': {'expected_outcome': 'Improves explicit context without asserting that schema '
                                                   'is mandatory for indexing or citations.',
                               'implementation_detail': 'Review the home classification, then add truthful '
                                                        'Organization, WebSite or the applicable '
                                                        'LocalBusiness subtype markup only where applicable '
                                                        'and validate it.',
                               'mechanism': 'Page-appropriate structured data can make visible facts more '
                                            'explicit to supporting consumers.'},
 'page-type-schema-gap:product': {'expected_outcome': 'Improves explicit context without asserting that '
                                                      'schema is mandatory for indexing or citations.',
                                  'implementation_detail': 'Review the product classification, then add '
                                                           'truthful Product or Offer markup only where '
                                                           'applicable and validate it.',
                                  'mechanism': 'Page-appropriate structured data can make visible facts more '
                                               'explicit to supporting consumers.'},
 'page-type-schema-gap:service': {'expected_outcome': 'Improves explicit context without asserting that '
                                                      'schema is mandatory for indexing or citations.',
                                  'implementation_detail': 'Review the service classification, then add '
                                                           'truthful Service markup only where applicable '
                                                           'and validate it.',
                                  'mechanism': 'Page-appropriate structured data can make visible facts more '
                                               'explicit to supporting consumers.'},
 'page-type-schema-gap:software': {'expected_outcome': 'Improves explicit context without asserting that '
                                                       'schema is mandatory for indexing or citations.',
                                   'implementation_detail': 'Review the software classification, then add '
                                                            'truthful SoftwareApplication markup only where '
                                                            'applicable and validate it.',
                                   'mechanism': 'Page-appropriate structured data can make visible facts '
                                                'more explicit to supporting consumers.'},
 'redirect-chain': {'expected_outcome': 'Reduces requests needed to reach content.',
                    'implementation_detail': 'Point internal links to the final intended URL and collapse '
                                             'unnecessary redirect hops.',
                    'mechanism': 'Multiple redirect hops consume request budget and add latency.'},
 'render-gap': {'expected_outcome': 'Content becomes machine-readable without JS',
                'implementation_detail': 'Add SSR or static generation for key pages',
                'mechanism': 'The observed condition can limit retrieval or visitor access on sampled '
                             'pages.'},
 'render-gap-unconfirmed': {'expected_outcome': 'Clarifies whether a real rendering fix is needed',
                            'implementation_detail': 'Open the page in a browser and compare to the raw HTML',
                            'mechanism': 'Headless rendering also returned little content, or failed, for '
                                         'these pages -- could be genuinely thin content rather than a JS '
                                         'dependency'},
 'render-subprocess-timeout': {'expected_outcome': 'Restores confirmed (not just suspected) rendering-gap '
                                                   'findings',
                               'implementation_detail': 'Re-run the audit Check for bot-detection on the '
                                                        'target site',
                               'mechanism': 'The isolated rendering subprocess exceeded its wall-clock '
                                            'deadline and was terminated; rendering-gap pages fall back to '
                                            'the static-only heuristic'},
 'robots-block': {'expected_outcome': 'Permits the intended compliant crawler where the policy is '
                                      'deliberately changed.',
                  'implementation_detail': 'Confirm the intended public crawling policy; narrow exclusions '
                                           'only if unintended, preserving private paths.',
                  'mechanism': 'The observed robots policy disallows this audit crawler for the evaluated '
                               'URL.'},
 'robots-unreachable': {'expected_outcome': 'Enables a real crawl-permission verdict',
                        'implementation_detail': 'Check robots.txt responds quickly with a 200 or a clean '
                                                 '404 Re-run the audit once robots.txt is reachable',
                        'mechanism': 'The observed condition can limit retrieval or visitor access on '
                                     'sampled pages.'},
 'scannability': {'expected_outcome': 'Makes individual topics easier to locate and summarize.',
                  'implementation_detail': 'Divide long content into meaningful sections with descriptive '
                                           'headings.',
                  'mechanism': 'Long unsectioned content can be difficult to scan and extract.'},
 'sitemap-unavailable': {'expected_outcome': 'Improves inventory discovery; absence is not a universal '
                                             'indexing defect.',
                         'implementation_detail': 'If appropriate, publish a valid sitemap of canonical '
                                                  'public pages and reference it in robots.txt.',
                         'mechanism': 'Without a discovered sitemap, this audit relies more heavily on '
                                      'sampled links.'},
 'social-metadata': {'expected_outcome': 'Provides preview candidates; image availability and platform '
                                         'rendering still need verification.',
                     'implementation_detail': 'Set accurate og:title, og:description, og:image and og:url '
                                              'values on shareable pages; verify the actual preview.',
                     'mechanism': 'Incomplete Open Graph metadata limits available shared-link preview '
                                  'hints.'},
 'social-url': {'expected_outcome': 'Supplies usable preview URLs without claiming the assets were fetched.',
                'implementation_detail': 'Use valid absolute HTTP(S) og:url and og:image URLs consistent '
                                         'with the intended page and asset.',
                'mechanism': 'A malformed social URL cannot reliably identify its intended page or image.'},
 'stale-dates:commercial': {'expected_outcome': 'Corrects outdated facts only where independently confirmed.',
                            'implementation_detail': 'Review the dated commercial facts against current '
                                                     'authoritative records; retain valid historical dates.',
                            'mechanism': 'An old date may warrant review but does not prove the associated '
                                         'fact is stale.'},
 'stale-dates:contact': {'expected_outcome': 'Corrects outdated facts only where independently confirmed.',
                         'implementation_detail': 'Review the dated contact facts against current '
                                                  'authoritative records; retain valid historical dates.',
                         'mechanism': 'An old date may warrant review but does not prove the associated fact '
                                      'is stale.'},
 'stale-dates:editorial': {'expected_outcome': 'Corrects outdated facts only where independently confirmed.',
                           'implementation_detail': 'Review the dated editorial facts against current '
                                                    'authoritative records; retain valid historical dates.',
                           'mechanism': 'An old date may warrant review but does not prove the associated '
                                        'fact is stale.'},
 'stale-dates:legal': {'expected_outcome': 'Corrects outdated facts only where independently confirmed.',
                       'implementation_detail': 'Review the dated legal facts against current authoritative '
                                                'records; retain valid historical dates.',
                       'mechanism': 'An old date may warrant review but does not prove the associated fact '
                                    'is stale.'},
 'stale-dates:operational': {'expected_outcome': 'Corrects outdated facts only where independently '
                                                 'confirmed.',
                             'implementation_detail': 'Review the dated operational facts against current '
                                                      'authoritative records; retain valid historical dates.',
                             'mechanism': 'An old date may warrant review but does not prove the associated '
                                          'fact is stale.'},
 'term-repetition': {'expected_outcome': 'Improves natural wording when repetition is excessive.',
                     'implementation_detail': 'Review repetition in context, retaining necessary technical '
                                              'names and avoiding unnatural keyword quotas.',
                     'mechanism': 'High observed term repetition can reduce readability but is not proof of '
                                  'spam.'},
 'title-body-alignment': {'expected_outcome': 'Improves topic consistency if the lexical mismatch reflects a '
                                              'real problem.',
                          'implementation_detail': 'Review semantics and synonyms before revising the title '
                                                   'or content to describe the same topic.',
                          'mechanism': 'Little literal overlap between a title and substantial body copy can '
                                       'signal mismatched topics.'},
 'title-length': {'expected_outcome': 'Improves title usefulness; pixel width and platform behavior vary.',
                  'implementation_detail': 'Review outlier titles for clarity; place distinguishing terms '
                                           'early rather than enforcing a character quota.',
                  'mechanism': 'Unusually short or long titles may be uninformative or truncated on some '
                               'displays.'},
 'tls-health': {'expected_outcome': 'Restores trustworthy audit evidence after a verified local or server correction.',
                'implementation_detail': 'Inspect the exact verification code and Python trust roots, compare with the working client, '
                                         'and configure AUDIT_CA_BUNDLE only with an administrator-approved CA if needed. '
                                         'Retain hostname and chain verification; repair only an independently confirmed server issue.',
                'mechanism': 'Certificate verification failure prevents this client from establishing a '
                             'trusted TLS connection.'},
 'twitter-card': {'expected_outcome': 'Provides an explicit card hint, without guaranteeing a rendered card.',
                  'implementation_detail': 'Choose an appropriate supported twitter:card value and verify '
                                           'the target platform preview.',
                  'mechanism': 'Absent or unsupported Twitter Card metadata may limit card selection.'},
 'generic-anchor-text': {'expected_outcome': 'Improves how visitors and machines interpret link destinations '
                                             'when anchor wording is vague.',
                         'implementation_detail': 'Rewrite generic link text to name the destination; keep '
                                                  'anchors meaningful when read out of context.',
                         'mechanism': 'Generic anchor text conveys nothing about the target page to readers '
                                      'or retrieval systems.'},
 'page-orientation': {'expected_outcome': 'Improves above-the-fold orientation on substantial content pages.',
                      'implementation_detail': 'Lead each content page with a descriptive short H1 and '
                                               'follow with scannable H2 sections.',
                      'mechanism': 'A substantial page without a clear primary heading gives arriving '
                                   'visitors no immediate sense of its topic.'},
 'internal-discoverability': {'expected_outcome': 'Improves onward paths for visitors and crawlers where '
                                                  'internal linking is sparse.',
                              'implementation_detail': 'Add contextual links to related pages within body '
                                                       'content and ensure primary destinations are '
                                                       'reachable from substantial pages.',
                              'mechanism': 'Substantial pages exposing almost no internal links leave no '
                                           'observed path onward from that page.'},
 'email-summary-readable': {'expected_outcome': 'Improves the chance that inbox AI summaries retain the key '
                                                'message when substance is currently image-carried.',
                            'implementation_detail': 'Provide the key message as real text near the top and '
                                                     'put the important lines first in outbound emails.',
                            'mechanism': 'Inbox summaries are built from readable text, so substance carried '
                                         'only in images can be dropped.'},
 'viewport': {'expected_outcome': 'Improves responsive layout configuration; actual layout still requires '
                                  'testing.',
              'implementation_detail': 'Add a responsive viewport declaration and verify real mobile layout.',
              'mechanism': 'Missing viewport configuration can impair responsive layout on mobile.'},
 'zoom': {'expected_outcome': 'Allows users to enlarge text where supported.',
          'implementation_detail': 'Remove unnecessary user-scalable=no and maximum-scale restrictions; test '
                                   'zoom.',
          'mechanism': 'A restrictive viewport declaration can impede user zoom.'}}


def _e(mechanism, implementation_detail, expected_outcome):
    return {'mechanism': mechanism, 'implementation_detail': implementation_detail,
            'expected_outcome': expected_outcome}


# A13: real mechanisms for the checks that previously carried a generic
# placeholder ("The observed condition can limit retrieval ..."). Each states the
# causal chain from the observed condition to lost discovery, citation or visits.
_BASE.update({
    'no-jsonld': _e('Without schema.org markup a machine has to infer entity type, prices, dates and ownership '
                    'from free text. Typed facts are extracted more reliably and tie each page to one '
                    'unambiguous entity.',
                    'Add JSON-LD matching each page type: Organization/WebSite on the homepage, Product/Offer on '
                    'product pages, Article/BlogPosting on articles, LocalBusiness on contact/location pages.',
                    'Key facts become machine-extractable without inference, and the brand is disambiguated.'),
    'render-gap': _e('Many AI fetchers store the raw HTML response without running JavaScript. Content '
                     'assembled client-side is missing from what they index and quote.',
                     'Server-side render or statically pre-render the affected templates so key text is in the '
                     'initial HTML response; keep client-side hydration for interactivity only.',
                     'The facts visible to a person are also present for clients that do not execute JavaScript.'),
    'ai-crawler-blocked': _e('Compliant crawlers check robots rules before every fetch. A disallowed AI search agent '
                             'never retrieves the page, so its assistant cannot quote or link it however good the '
                             'content is.',
                             'Remove or narrow the Disallow rule for the AI search agents you want to be cited by; '
                             'keep training-only exclusions separate if they are a deliberate policy.',
                             'AI search agents can retrieve the key pages, making them eligible to be cited.'),
    'ai-crawler-unchecked': _e('Without a readable robots.txt the audit cannot tell which AI agents are permitted. '
                               'This is a gap in evidence, not a confirmed block.',
                               'Make robots.txt reliably reachable (a fast 200, or a clean 404), then re-run the audit.',
                               'A real allow/disallow verdict becomes possible for every AI agent.'),
    'robots-unreachable': _e('Under RFC 9309 crawlers treat an unreachable robots.txt (5xx, 429 or timeout) as '
                             '"disallow everything" until it recovers, so a flaky robots file can silently remove the '
                             'whole site from crawling.',
                             'Serve robots.txt as a fast, cacheable 200 (or a clean 404); never route it through '
                             'rate limiting, authentication or bot challenges.',
                             'Crawlers get a stable, explicit permission verdict.'),
    'broken-pages': _e('URLs returning 4xx/5xx are dropped from indexes; links to them waste crawl budget, and any '
                       'facts they held can no longer be retrieved or cited.',
                       'Restore the content or 301-redirect each broken URL to its closest live equivalent, and '
                       'update internal links that point to it.',
                       'Every linked URL resolves to live content.'),
    'orphan-pages': _e('Pages with no internal links pointing to them are reached only via the sitemap or external '
                       'links; they receive no internal authority, and visitors browsing the site never find them.',
                       'Link each valuable orphan page from relevant navigation, hub or related-content sections.',
                       'Orphaned pages become reachable for both crawlers and visitors.'),
    'isolated-clusters': _e('Groups of pages linked only to each other are discovered only if a crawler already '
                            'knows an entry URL, so they are frequently missed as a whole.',
                            'Link the cluster entry page from the main navigation or a relevant hub page.',
                            'The whole section joins the main site graph.'),
    'contradicted-claim': _e('When independent sources state a different value for the same fact, retrieval '
                             'surfaces the conflict or prefers the more widely repeated version, which may not be '
                             'the site\'s.',
                             'Identify the conflicting source, correct whichever side is wrong, and state the correct '
                             'value explicitly on-site and in structured data.',
                             'Independent sources and the site agree on the fact.'),
    'footprint-signal': _e('Assistants trust facts repeated by many independent sources; a thin off-site footprint '
                           'leaves the brand\'s own site as the only witness.',
                           'Build identity-consistent profiles and independent mentions where the category is '
                           'discussed (directories, review sites, community platforms).',
                           'More independent sources corroborate the brand\'s identity and claims.'),
    'llms-txt-unchecked': _e('The llms.txt endpoint could not be read, so whether a curated AI-facing summary exists '
                             'is unknown. This is not evidence of absence.',
                             'Make /llms.txt reachable (200 or clean 404) and re-run the audit.',
                             'The presence or absence of llms.txt can be assessed.'),
})

# A2 / A12 / A7 / A9 / A10 / A11: checks added in Round 5.
_BASE.update({
    'bot-challenge-sitewide': _e('A bot-management firewall answers automated clients with a challenge page instead of '
                                 'content. Crawlers and AI fetchers cannot solve challenges, so unless they are '
                                 'explicitly allowlisted they store the interstitial, not the site.',
                                 'Allow verified search and AI crawlers in the bot-management/WAF settings and exempt '
                                 '/robots.txt, /sitemap*.xml and /llms.txt from challenges; confirm in WAF logs that '
                                 'Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User and PerplexityBot receive 200s.',
                                 'Automated readers receive the real content, so the site can be indexed and cited.'),
    'bot-challenge-robots': _e('robots.txt, the sitemap or llms.txt is served behind a bot challenge. Crawlers read '
                               'these files before anything else; a challenged robots.txt is "unreachable", which '
                               'compliant crawlers treat as "disallow everything".',
                               'Exempt /robots.txt, /sitemap*.xml and /llms.txt from every challenge, rate-limit and '
                               'authentication rule.',
                               'Crawlers can read the site\'s permission and discovery files.'),
    'bot-challenge-rate': _e('After a few requests the firewall starts challenging or rate-limiting the client. '
                             'Crawlers that fetch several pages in a row (the normal case) then receive interstitials '
                             'for deeper pages, which drop out of indexes.',
                             'Relax per-client rate rules for verified crawlers, or serve them with a higher '
                             'threshold; never return 200 with challenge HTML -- use 429 with Retry-After.',
                             'Deeper pages are fetched successfully by crawlers that respect crawl-delay.'),
    'search-crawler-blocked': _e('Googlebot and Bingbot build the indexes behind classic search, Google AI Overviews/AI '
                                 'Mode, and (via Bing) ChatGPT search and Copilot. A page they cannot crawl is '
                                 'invisible to all of those surfaces.',
                                 'Remove the Disallow rule for Googlebot/Bingbot on public pages; use noindex only for '
                                 'pages that must stay out of search.',
                                 'The site is eligible for classic and AI-assisted search results again.'),
    'user-fetch-blocked': _e('ChatGPT-User, Claude-User and Perplexity-User fetch a page live when a user asks about '
                             'it. Blocking them means the assistant cannot read the page at the moment of the '
                             'question and answers from other sources instead.',
                             'Allow the user-triggered fetch agents on public pages; they act on behalf of a person '
                             'and are not training crawlers.',
                             'Assistants can read the page when a user explicitly asks about it.'),
    'training-crawler-blocked': _e('Training crawlers (GPTBot, ClaudeBot, Google-Extended, CCBot ...) only affect model '
                                   'training; blocking them does not remove the site from AI search, which uses '
                                   'separate agents.',
                                   'Keep the exclusion if it is deliberate; make sure the search and user-fetch agents '
                                   'of the same vendors are still allowed.',
                                   'Training policy and search visibility are controlled independently.'),
    'identity-not-declared': _e('With no Organization/WebSite markup, the brand name had to be inferred from titles, '
                                'footer or domain. Assistants doing the same may merge the brand with same-named '
                                'entities or describe it inconsistently.',
                                'Add Organization JSON-LD on the homepage with name, url, logo and sameAs links to the '
                                'official profiles, and a WebSite node with the site name.',
                                'The brand identity is declared once, explicitly, in machine-readable form.'),
    'schema-missing-required': _e('Structured data that lacks the properties consumers require (for example an Offer '
                                  'without price/priceCurrency) is ignored or only partly used, so the fact it was '
                                  'meant to carry is lost.',
                                  'Add the missing required properties to each listed node, using values that match '
                                  'the visible page.',
                                  'Markup is complete enough to be used by search and AI consumers.'),
    'schema-missing-recommended': _e('Recommended properties (dateModified, sameAs, logo, image ...) are what let a '
                                     'consumer judge freshness and identity; without them the markup is valid but '
                                     'thin.',
                                     'Add the listed recommended properties where the information exists.',
                                     'Markup carries freshness and identity signals.'),
    'schema-invalid-value': _e('Values in the wrong format (a non-numeric price, a currency that is not an ISO 4217 '
                               'code, a relative URL, a non-ISO date) fail validation and the whole node can be '
                               'discarded.',
                               'Correct each listed value to the schema.org/ISO format shown in the evidence.',
                               'The structured data validates and is used.'),
    'schema-visible-mismatch': _e('The markup states a different fact than the visible page (for example a different '
                                  'price). Machines read the markup, people read the page, so the brand publishes two '
                                  'versions of one fact and assistants may quote the wrong one.',
                                  'Generate the markup from the same source as the visible value, or correct whichever '
                                  'of the two is wrong.',
                                  'Markup and visible content state the same fact.'),
    'facts-in-pdf': _e('Key facts (prices, menus, fees, specifications) are published only as a linked document. AI '
                       'fetchers extract text from HTML pages; a separately-fetched binary is often skipped or cited '
                       'without page context, and image-only PDFs have no text at all.',
                       'Publish the facts as HTML text (a table or list) on the linking page and keep the document as '
                       'an optional download.',
                       'The facts are readable and quotable from the page itself.'),
    'facts-in-images': _e('Facts carried inside images (a price list, menu, timetable or table rendered as a picture) '
                          'are pixels to a text extractor and are invisible to most AI fetchers.',
                          'Publish the same facts as HTML text next to or instead of the image, and give the image '
                          'alt text that states its content.',
                          'The facts exist as text that machines can extract.'),
    'facts-in-iframe': _e('Facts embedded through a third-party document viewer or widget iframe live on another '
                          'origin; a crawler reading this page does not see them as part of it.',
                          'Render the key facts as HTML on the page itself; keep the embed only as an enhancement.',
                          'The facts belong to the page that crawlers read.'),
    'expired-offer': _e('An offer, price validity or event end date has passed but the page is still live. An '
                        'assistant quoting it gives users wrong information, and a visible expiry date signals the '
                        'page is unmaintained.',
                        'Update or remove the expired offer, and set priceValidUntil/validThrough to the real end '
                        'date.',
                        'Live pages only state current offers.'),
    'date-contradiction': _e('The page states different dates in different places (markup vs. visible "updated" date '
                             'vs. sitemap lastmod, or modified before published). Freshness is a ranking and '
                             'selection signal; contradictory dates make it unreliable.',
                             'Derive dateModified, the visible "updated" date and sitemap lastmod from one source of '
                             'truth (the CMS last-modified time).',
                             'All freshness signals agree.'),
    'stale-update-claim': _e('The page explicitly says when it was last updated, and that date is old. Assistants and '
                             'readers use that statement to judge whether facts like prices or policies still hold.',
                             'Review the content, then update the facts and the "last updated" date together.',
                             'The stated update date reflects a real recent review.'),
    'stale-copyright': _e('A footer copyright year that is several years old is a visible sign of an unmaintained '
                          'site to readers and to models judging source reliability.',
                          'Render the copyright year from the current date (or the last real content update).',
                          'The site no longer looks abandoned.'),
    'missing-article-dates': _e('Articles without machine-readable datePublished/dateModified give consumers no '
                                'freshness signal, so time-sensitive answers prefer sources that state one.',
                                'Add datePublished and dateModified to Article/BlogPosting markup and show the same '
                                'dates visibly.',
                                'Articles carry an explicit, consistent freshness signal.'),
    'beyond:search-action': _e('The site has on-site search but does not declare it. A WebSite SearchAction tells '
                               'agents how to query the site directly, which is how agentic assistants complete '
                               'tasks on a brand\'s own pages.',
                               'Add a WebSite node with a potentialAction SearchAction whose urlTemplate matches the '
                               'site search URL.',
                               'Agents can send visitors straight to relevant on-site results.'),
    'beyond:ai-landing-pages': _e('Visitors arriving from an AI answer land deep, on the page the assistant cited, '
                                  'already holding context. Pages that open with a short, direct answer and one clear '
                                  'next step keep them; pages that make them re-orient lose them.',
                                  'On each listed landing page add a 2-3 sentence answer-first summary at the top that '
                                  'restates the key facts, and one primary next step (compare, buy, book, contact).',
                                  'AI-referred visitors find the answer immediately and continue on-site.'),
})
# A13: each page-type gap states why THAT type's markup matters.
_PAGE_TYPE_MECHANISMS = {
    'home': 'The homepage is where machines look for who the site belongs to; Organization/WebSite markup '
            'declares the name, logo and official profiles once, which disambiguates the brand from same-named '
            'entities.',
    'product': 'Product/Offer markup is how price, currency and availability become exact, extractable facts; '
               'without it a machine has to guess them from layout text and often quotes them wrongly or not at all.',
    'article': 'Article markup carries headline, author and publish/modify dates, the signals assistants use to judge '
               'whether a piece is authoritative and current enough to cite.',
    'contact': 'Contact and location pages answer "where/how do I reach them" questions; LocalBusiness or '
               'Organization markup turns address, phone and hours into unambiguous facts.',
    'about': 'The About page is the main source for identity questions; Organization/AboutPage markup ties its '
             'description to one declared entity.',
    'service': 'Service markup names what is offered, by whom and where, so service questions can be answered from '
               'explicit facts rather than marketing prose.',
    'software': 'SoftwareApplication markup states category, platform and price, the facts assistants need to '
                'recommend or compare an app.',
}
for _t, _mech in _PAGE_TYPE_MECHANISMS.items():
    _key = 'page-type-schema-gap:' + _t
    if _key in _BASE:
        _BASE[_key] = dict(_BASE[_key], mechanism=_mech)

for _old in ('stale-dates:commercial', 'stale-dates:contact', 'stale-dates:editorial',
             'stale-dates:legal', 'stale-dates:operational'):
    _BASE.pop(_old, None)  # replaced by the context-classified date rules (A9)

CATALOG = MappingProxyType({key: MappingProxyType(value) for key, value in _BASE.items()})


# ---------------------------------------------------------------------------
# WP0: check metadata. Every check belongs to one gate of the
# reach -> read -> extract -> trust -> engage chain (Appendix A plus the trust
# and engagement halves of Round 2). The gate sets the typical base severity,
# group drives root-cause merging (A14), tier separates core findings from SEO
# hygiene (A17), owner says who fixes it, and the two flags tell the scorer
# (common/scoring.py, A4) how scope and sample size apply.
# ---------------------------------------------------------------------------
GATES = ('access', 'readability', 'extractability', 'trust', 'engagement')

def _m(gate, group=None, tier='core', owner='developer', category=None, scope_sensitive=True, absence_claim=False):
    return MappingProxyType({'gate': gate, 'group': group, 'tier': tier, 'owner': owner,
                             'category': category, 'scope_sensitive': scope_sensitive,
                             'absence_claim': absence_claim})

_META = {
    # access: can a crawler get in and receive the content?
    'robots-block': _m('access', 'robots', owner='seo', scope_sensitive=False),
    'robots-unreachable': _m('access', 'robots-inaccessible', owner='infra', scope_sensitive=False),
    'ai-crawler-unchecked': _m('access', 'robots-inaccessible', owner='infra', scope_sensitive=False),
    'fetch-failure': _m('access', 'robots-inaccessible', owner='infra', scope_sensitive=False),
    'tls-health': _m('access', 'robots-inaccessible', owner='infra', scope_sensitive=False),
    'bot-challenge-sitewide': _m('access', 'bot-wall', owner='infra', scope_sensitive=False),
    'bot-challenge-robots': _m('access', 'robots-inaccessible', owner='infra', scope_sensitive=False),
    'bot-challenge-rate': _m('access', 'bot-wall', owner='infra', scope_sensitive=False),
    'search-crawler-blocked': _m('access', 'robots', owner='seo', scope_sensitive=False),
    'ai-crawler-blocked': _m('access', 'robots', owner='seo', scope_sensitive=False),
    'user-fetch-blocked': _m('access', 'robots', owner='seo', scope_sensitive=False),
    'training-crawler-blocked': _m('access', 'robots', owner='seo', scope_sensitive=False),
    'broken-pages': _m('access', owner='developer'),
    'noindex': _m('access', 'indexing', owner='seo'),
    'nosnippet': _m('access', 'indexing', owner='seo'),
    'snippet-suppression': _m('access', 'indexing', owner='seo'),
    'http-transport': _m('access', owner='infra', scope_sensitive=False),
    'redirect-chain': _m('access', owner='developer'),
    'sitemap-unavailable': _m('access', owner='seo', scope_sensitive=False),
    'fetch-latency': _m('access', tier='hygiene', owner='infra'),
    # readability: once fetched, is the content present as text?
    'render-gap': _m('readability', 'render', owner='developer'),
    'render-gap-unconfirmed': _m('readability', 'render', owner='developer'),
    'render-subprocess-timeout': _m('readability', 'render', owner='developer'),
    'hash-routing': _m('readability', 'render', owner='developer', category='engagement'),
    'facts-in-pdf': _m('readability', 'non-text-facts', owner='content'),
    'facts-in-images': _m('readability', 'non-text-facts', owner='content'),
    'facts-in-iframe': _m('readability', 'non-text-facts', owner='content'),
    'missing-alt': _m('readability', owner='content', category='engagement'),
    # extractability: can a machine pick out the specific fact and the entity?
    'no-jsonld': _m('extractability', 'structured-data-presence', owner='developer', absence_claim=True),
    'malformed-jsonld': _m('extractability', 'structured-data-validity', owner='developer'),
    'schema-missing-required': _m('extractability', 'structured-data-validity', owner='developer'),
    'schema-invalid-value': _m('extractability', 'structured-data-validity', owner='developer'),
    'schema-missing-recommended': _m('extractability', 'structured-data-validity', tier='hygiene', owner='developer'),
    'identity-not-declared': _m('extractability', 'structured-data-presence', owner='seo', scope_sensitive=False),
    'no-headings': _m('extractability', 'heading-structure', owner='content', absence_claim=True),
    'h1': _m('extractability', 'heading-structure', owner='content', category='engagement'),
    'heading-hierarchy': _m('extractability', 'heading-structure', tier='hygiene', owner='content'),
    'missing-title': _m('extractability', owner='content'),
    'missing-description': _m('extractability', tier='hygiene', owner='content', absence_claim=True),
    'missing-canonical': _m('extractability', 'canonical', tier='hygiene', owner='seo', absence_claim=True),
    'invalid-canonical': _m('extractability', 'canonical', owner='seo'),
    'cross-origin-canonical': _m('extractability', 'canonical', owner='seo'),
    'missing-language': _m('extractability', owner='developer'),
    'missing-landmarks': _m('extractability', tier='hygiene', owner='developer'),
    'no-llms-txt': _m('extractability', owner='seo', scope_sensitive=False),
    'llms-txt-unchecked': _m('extractability', owner='seo', scope_sensitive=False),
    'answer-headings': _m('extractability', owner='content', category='answer_content'),
    'brand-definition': _m('extractability', owner='content', category='answer_content'),
    'about-concreteness': _m('extractability', owner='content'),
    'app-identity': _m('extractability', 'structured-data-validity', owner='developer'),
    'title-body-alignment': _m('extractability', owner='content'),
    'term-repetition': _m('extractability', tier='hygiene', owner='content'),
    'title-length': _m('extractability', tier='hygiene', owner='content'),
    'heavy-html': _m('extractability', tier='hygiene', owner='developer'),
    'markup-ratio': _m('extractability', tier='hygiene', owner='developer'),
    'blocking-scripts': _m('extractability', tier='hygiene', owner='developer'),
    'image-sizing': _m('extractability', tier='hygiene', owner='developer'),
    'social-metadata': _m('engagement', 'social', tier='hygiene', owner='seo', category='engagement'),
    'social-url': _m('engagement', 'social', tier='hygiene', owner='seo', category='engagement'),
    'twitter-card': _m('engagement', 'social', tier='hygiene', owner='seo', category='engagement'),
    'duplicate-titles': _m('extractability', tier='hygiene', owner='content', category='engagement'),
    # trust: are the facts consistent, current and corroborated?
    'schema-visible-mismatch': _m('trust', 'fact-consistency', owner='content'),
    'expired-offer': _m('trust', 'freshness', owner='content'),
    'date-contradiction': _m('trust', 'freshness', owner='developer'),
    'stale-update-claim': _m('trust', 'freshness', owner='content'),
    'stale-copyright': _m('trust', 'freshness', owner='developer', scope_sensitive=False),
    'missing-article-dates': _m('trust', 'freshness', owner='developer', absence_claim=True),
    'contradicted-claim': _m('trust', 'fact-consistency', owner='content'),
    'independent-contradiction': _m('trust', 'fact-consistency', owner='content', scope_sensitive=False),
    'no-independent-mention': _m('trust', 'off-site', owner='seo', scope_sensitive=False),
    'footprint-signal': _m('trust', 'off-site', owner='seo', scope_sensitive=False),
    # engagement: does the visitor who arrives stay and continue?
    'orphan-pages': _m('engagement', 'link-graph-inbound', owner='content'),
    'isolated-clusters': _m('engagement', 'link-graph-inbound', owner='content'),
    'dead-ends': _m('engagement', 'link-graph-outbound', owner='content'),
    'internal-discoverability': _m('engagement', 'link-graph-outbound', owner='content'),
    'next-step': _m('engagement', 'link-graph-outbound', owner='content'),
    'no-internal-navigation': _m('engagement', 'link-graph-outbound', owner='developer'),
    'page-orientation': _m('engagement', 'heading-structure', owner='content'),
    'homepage-orientation': _m('engagement', owner='content', scope_sensitive=False),
    'scannability': _m('engagement', 'heading-structure', owner='content'),
    'long-paragraphs': _m('engagement', owner='content'),
    'generic-anchor-text': _m('engagement', owner='content'),
    'breadcrumb-mismatch': _m('engagement', owner='developer'),
    'viewport': _m('engagement', owner='developer'),
    'zoom': _m('engagement', owner='developer'),
    'overlay': _m('engagement', owner='developer'),
    'email-summary': _m('engagement', 'email', owner='content'),
    'email-summary-readable': _m('engagement', 'email', owner='content'),
}

_PREFIX_META = {
    'page-type-schema-gap:': _m('extractability', 'structured-data-presence', owner='developer'),
    'baseline:': _m('engagement', tier='core', owner='seo', scope_sensitive=False),
    'beyond:': _m('engagement', tier='core', owner='content', scope_sensitive=False),
}
_DEFAULT_META = _m('extractability')


def meta_for(check_id):
    """Metadata for a check id; prefix families share one entry."""
    if check_id in _META:
        return _META[check_id]
    for prefix, meta in _PREFIX_META.items():
        if str(check_id).startswith(prefix):
            return meta
    return _DEFAULT_META

REQUIRED_FIELDS = ("mechanism", "implementation_detail", "expected_outcome")

def get_entry(check_id):
    entry = CATALOG[check_id]
    if not all(isinstance(entry.get(k), str) and entry[k].strip() for k in REQUIRED_FIELDS):
        raise ValueError("Invalid check catalog entry: " + check_id)
    return entry

def enrich_finding(finding, strict=False):
    check_id = finding.get("check_id") or finding.get("provenance", {}).get("rule_id")
    if not check_id or check_id not in CATALOG:
        if strict:
            raise ValueError("Uncatalogued check ID: " + str(check_id))
        return finding
    entry = get_entry(check_id)
    finding["check_id"] = check_id
    finding["mechanism"] = entry["mechanism"]
    finding["implementation_detail"] = entry["implementation_detail"]
    finding["expected_outcome"] = entry["expected_outcome"]
    action = dict(finding["suggested_action"])
    action["implementation_detail"] = entry["implementation_detail"]
    action["expected_outcome"] = entry["expected_outcome"]
    finding["suggested_action"] = action
    return finding
