"""Single source of truth for check mechanisms, implementation details and outcomes.

Stable check IDs are distinct from per-report finding IDs. This catalog contains
implemented checks only. Observed evidence, scope and status stay with detectors.
Unknown IDs fail validation on the public audit path rather than silently acquiring
empty enrichment. Donor IDs are aliases for traceability, never duplicate jobs.
"""
from types import MappingProxyType

CATALOG = MappingProxyType({key: MappingProxyType(value) for key, value in {'about-concreteness': {'expected_outcome': 'Identity answers can be composed from the brand own concrete wording '
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
 'facts-in-images': {'expected_outcome': 'Prices, hours and specifications shown in images become '
                                         'quotable text for crawlers and assistants.',
                     'implementation_detail': 'State each fact shown in the image as HTML text near the '
                                              'image, give the image descriptive alt text, and mirror '
                                              'structured facts in JSON-LD.',
                     'mechanism': 'Facts shown only inside an image are invisible to crawlers and '
                                  'assistants that read HTML text.'},
 'pdf-only-facts': {'expected_outcome': 'Key facts are retrievable from an HTML page, with the PDF kept '
                                        'as a supplementary download.',
                    'implementation_detail': 'Publish the prices, specifications or contact details from '
                                             'each PDF on an HTML page and link the PDF from it.',
                    'mechanism': 'Facts that exist only in a PDF are less likely to be retrieved and '
                                 'quoted than facts stated on an HTML page.'},
 'pdf-image-only': {'expected_outcome': 'The PDF contents become extractable and quotable.',
                    'implementation_detail': 'Export the PDF from its source document with selectable '
                                             'text or add a text layer with OCR, and state the key facts '
                                             'in HTML.',
                    'mechanism': 'A PDF whose pages are images has no text layer, so nothing in it can '
                                 'be extracted or quoted.'},
 'structured-date-invalid': {'expected_outcome': 'Structured publication and update dates are parsed '
                                                 'reliably and agree with each other.',
                             'implementation_detail': 'Emit datePublished and dateModified as ISO 8601 '
                                                      'dates, keep dateModified on or after '
                                                      'datePublished, and never set a future date.',
                             'mechanism': 'Unparseable, inverted or future JSON-LD dates give crawlers '
                                          'contradictory freshness signals, so the dates are ignored or '
                                          'distrusted.'},
 'sitemap-lastmod-unreliable': {'expected_outcome': 'Crawlers can rely on sitemap lastmod to find and '
                                                    'recrawl pages that actually changed.',
                                'implementation_detail': 'Set each sitemap lastmod from the date the page '
                                                         'content last changed, in W3C Datetime form, never '
                                                         'the build time and never a future date.',
                                'mechanism': 'Crawlers use sitemap lastmod to decide what to recrawl only '
                                             'while it is present and accurate; missing, invalid or '
                                             'build-stamped values are ignored, so updates are found late.'},
 'kg-link-missing': {'expected_outcome': 'Assistants can tie the brand to one knowledge-graph entity and '
                                         'tell it apart from same-named entities.',
                     'implementation_detail': 'Add the Wikidata item (and Wikipedia article, if one exists) '
                                              'to Organization sameAs, and make sure the Wikidata item '
                                              'lists this site as its official website (P856).',
                     'mechanism': 'Knowledge graphs are the main signal assistants use to tell same-named '
                                  'entities apart; without a two-way link between the site and its '
                                  'knowledge-graph entity, the brand can be confused with a namesake.'},
 'kg-entity-mismatch': {'expected_outcome': 'The declared knowledge-graph entity and the site describe the '
                                            'same organization.',
                        'implementation_detail': 'Point Organization sameAs at the correct Wikidata item and '
                                                 'Wikipedia article, or correct the official website and '
                                                 'name on the entity itself.',
                        'mechanism': 'A sameAs link to a knowledge-graph entity whose name or official '
                                     'website disagrees with the site tells assistants the brand is a '
                                     'different organization, which causes mistaken identity.'},
 'kg-namesake-ambiguity': {'expected_outcome': 'Assistants attribute facts to the right organization when '
                                               'other entities share its name.',
                           'implementation_detail': 'Declare the brand knowledge-graph entity in '
                                                    'Organization sameAs and state distinguishing facts '
                                                    '(category, location, founding year) on the site.',
                           'mechanism': 'When other knowledge-graph entities share the brand name, '
                                        'assistants can merge their facts into the brand unless the site '
                                        'states clearly which entity it is.'},
 'viewport': {'expected_outcome': 'Improves responsive layout configuration; actual layout still requires '
                                  'testing.',
              'implementation_detail': 'Add a responsive viewport declaration and verify real mobile layout.',
              'mechanism': 'Missing viewport configuration can impair responsive layout on mobile.'},
 'zoom': {'expected_outcome': 'Allows users to enlarge text where supported.',
          'implementation_detail': 'Remove unnecessary user-scalable=no and maximum-scale restrictions; test '
                                   'zoom.',
          'mechanism': 'A restrictive viewport declaration can impede user zoom.'}} .items()})

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
