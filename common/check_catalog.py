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
 'independent-contradiction': {'expected_outcome': 'The site and the independent sources state one value for '
                                                  'the fact; how assistants then answer is not measured here.',
                              'implementation_detail': 'Reconcile the conflicting fact: confirm which '
                                                       'version is accurate, correct whichever source is '
                                                       'wrong, and state the accurate version on-site and in '
                                                       'Organization markup.',
                              'mechanism': 'When independent sources describe the brand differently from the '
                                           'site, retrieval surfaces the discrepancy and confidence drops '
                                           'across every associated fact.'},
 'ai-crawler-blocked': {'expected_outcome': 'The search crawlers the site wants to be cited by can fetch it '
                                            'again, while deliberate training opt-outs stay in place. Access '
                                            'makes citation possible, not certain.',
                        'implementation_detail': 'Compare each disallowed user-agent with the intended policy: '
                                                 'remove or narrow the Disallow rule for search crawlers that '
                                                 'should cite the site (OAI-SearchBot, Claude-SearchBot, '
                                                 'PerplexityBot, Googlebot), and keep deliberate training '
                                                 'opt-outs (GPTBot, ClaudeBot, Google-Extended, CCBot) as they '
                                                 'are.',
                        'mechanism': 'A robots.txt Disallow for an AI search crawler keeps the whole site out '
                                     'of that assistant\'s search index, so it cannot be retrieved or cited '
                                     'there. A Disallow for a training or user-fetch crawler only withholds '
                                     'the content from model training or on-demand fetches.'},
 'ai-crawler-section-blocked': {'expected_outcome': 'Content sections become readable by the AI crawlers that '
                                                    'cite sources, where that is the intended policy.',
                                'implementation_detail': 'Remove or narrow the Disallow rules for the listed AI '
                                                         'user-agents on the listed sections, or keep them if the '
                                                         'exclusion is deliberate.',
                                'mechanism': 'An AI crawler that robots.txt disallows on a section never reads its '
                                             'pages, so assistants that rely on that crawler cannot quote them.'},
 'ai-crawler-unchecked': {'expected_outcome': 'Crawlers, and the next audit, get a definite answer on '
                                              'which AI crawlers may fetch the site.',
                          'implementation_detail': 'Serve /robots.txt as plain text with a 200 status (or a '
                                                   'clean 404 when there are no rules), without a timeout, a '
                                                   'server error or a bot challenge, then re-run the audit.',
                          'mechanism': 'Without a readable robots.txt the audit cannot tell which AI crawlers '
                                       'the site admits, and crawlers that cannot read the file may hold back '
                                       'from the whole site.'},
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
                  'implementation_detail': 'List the URLs that answer with an error. Restore the content, or '
                                           'add a 301 redirect to the closest live page, and update the links '
                                           'that point at the old URL.',
                  'mechanism': 'A page that answers 404 or 5xx returns no content, so crawlers drop it and '
                               'visitors who follow a link to it leave.'},
 'contradicted-claim': {'expected_outcome': 'Reduces risk of assistants surfacing conflicting facts',
                        'implementation_detail': 'Compare the on-site value to the external source. Correct '
                                                 'whichever is stale, or ask the other listing to update.',
                        'mechanism': 'When the site and an independent source state different values, '
                                     'assistants cannot tell which is right and may repeat the wrong one.'},
 'cross-origin-canonical': {'expected_outcome': 'Avoids unintended consolidation while preserving legitimate '
                                                'syndication.',
                            'implementation_detail': 'Verify ownership and content equivalence; correct the '
                                                     'URL only if the external canonical is unintended.',
                            'mechanism': 'An external canonical can nominate another origin as the preferred '
                                         'copy.'},
 'dead-ends': {'expected_outcome': 'Each listed page offers at least one link to another page of the site; '
                                    'the effect on visitor behaviour is not measured here.',
               'implementation_detail': 'Add related-content links. Add a clear next-step call to action.',
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
                   'implementation_detail': 'Check the failure from another client. Repair confirmed '
                                            'certificate or server failures.',
                   'mechanism': 'A fetch failure limits this audit; it does not establish a permanent '
                                'site-wide outage.'},
 'fetch-latency': {'expected_outcome': 'Can improve retrieval reliability; audit pacing and retries are '
                                       'excluded from this observation.',
                   'implementation_detail': 'Repeat timings from representative clients and investigate '
                                            'network or server delays before applying caching or backend '
                                            'changes.',
                   'mechanism': 'Slow observed HTML retrieval reduces the amount of evidence available '
                                'within a deadline.'},
 'expired-offer': {'expected_outcome': 'Assistants and visitors see only offers that are still valid.',
                   'implementation_detail': 'Remove or update each offer whose end date has passed, correct the '
                                            'matching Offer priceValidUntil or validThrough, and give every '
                                            'promotion a step that takes it down when it ends.',
                   'mechanism': 'An offer whose stated end date has passed still reads as current: an assistant '
                                'that quotes the page repeats a deal that no longer applies, and a visitor who '
                                'acts on it is turned away.'},
 'fact-inconsistent-across-pages': {'expected_outcome': 'Every page states the same value, which removes one '
                                                        'source of conflicting answers.',
                                    'implementation_detail': 'Decide which value is current for each listed '
                                                             'property, correct the pages that state the other '
                                                             'one, and emit organization and product markup '
                                                             'from one shared source.',
                                    'mechanism': 'When one organization or product has two values for the same '
                                                 'property on different pages, an assistant cannot tell which is '
                                                 'current and may repeat either, or trust neither.'},
 'fact-markup-mismatch': {'expected_outcome': 'Assistants and visitors get one answer for each fact.',
                          'implementation_detail': 'Make the JSON-LD and the visible text state the same '
                                                   'telephone, postal code, opening hours and price, ideally by '
                                                   'generating both from one data source.',
                          'mechanism': 'Assistants read structured data and visible text; when the markup states '
                                       'a telephone, postal code, opening time or price the page contradicts, '
                                       'they meet two answers and may quote the wrong one.'},
 'footprint-signal': {'expected_outcome': 'More independent domains name the brand consistently, giving '
                                          'assistants sources that corroborate what the site says.',
                      'implementation_detail': 'List the brand under its exact site name on relevant '
                                               'directories and review platforms, link those profiles from '
                                               'Organization sameAs, and pursue press or partner coverage on '
                                               'independent domains.',
                      'mechanism': 'Assistants corroborate a brand through independent sources: a brand '
                                   'named on few domains other than its own rests on its own claims, while '
                                   'mentions spread across several independent domains make its facts easier '
                                   'to confirm.'},
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
 'homepage-orientation': {'expected_outcome': 'The homepage opens with a short heading that says what the '
                                              'organization offers; the rendered first screen and visitor '
                                              'behaviour are not measured here.',
                          'implementation_detail': 'State what the organization offers and for whom in the '
                                                   'first viewport. Use a descriptive H1 and scannable H2 '
                                                   'sections. Place one relevant call to action near the '
                                                   'opening content.',
                          'mechanism': 'The sampled homepage contains substantial text but none of its first '
                                       'headings, in source order, is a short statement of what it offers. '
                                       'Source order does not establish what appears above the fold.'},
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
                       'implementation_detail': 'Identify which clusters contain valuable content. Add '
                                                'navigation or contextual links that connect them to the main '
                                                'site.',
                       'mechanism': 'A group of pages that links only to itself cannot be reached from the rest '
                                    'of the site, so crawlers and visitors rarely find it.'},
 'llms-txt-unchecked': {'expected_outcome': 'Tools that read llms.txt get the file or a clear absence, '
                                            'and the next audit can say whether it is present and valid.',
                        'implementation_detail': 'Serve /llms.txt as a plain-text Markdown file at that exact '
                                                 'path with a 200 status, or answer 404 when the site has '
                                                 'none; do not redirect it or answer with an HTML page. Then '
                                                 're-run the audit.',
                        'mechanism': '/llms.txt answered with an error, a block, a redirect or an HTML page '
                                     'instead of a text file, so tools that look for it find no usable guide '
                                     'and the audit cannot tell whether one is meant to exist.'},
 'long-paragraphs': {'expected_outcome': 'Improves readability of the observed long passages.',
                     'implementation_detail': 'Split dense passages by topic and use appropriate lists or '
                                              'tables.',
                     'mechanism': 'Dense paragraphs can hide important answers.'},
 'malformed-jsonld': {'expected_outcome': 'Prevents parsers from dropping important entity and product facts',
                      'implementation_detail': 'Validate each JSON-LD block as strict JSON. Preserve valid '
                                               '@graph nodes and required properties. Re-run a '
                                               'structured-data validator after deployment.',
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
                 'implementation_detail': 'Add one h1 per page. Structure sections with h2 and h3.',
                 'mechanism': 'Pages have no h1-h6 elements'},
 'no-internal-navigation': {'expected_outcome': 'Reduces dead ends and helps both visitors and crawlers '
                                                'discover deeper content',
                            'implementation_detail': 'Expose primary destinations in a semantic nav '
                                                     'landmark. Link related pages from body content. Give '
                                                     'every important landing page a clear next step.',
                            'mechanism': 'Visitors landing on the sampled pages have no observed internal '
                                         'link path to related content'},
 'no-jsonld': {'expected_outcome': 'Key facts are also stated as explicit structured data that parsers can '
                                    'read without inferring them from layout; no ranking, rich-result or '
                                    'citation gain is implied.',
               'implementation_detail': 'Identify the type of each key page. Add a matching schema.org '
                                        'JSON-LD block (Organization and WebSite on the home page; Product, '
                                        'Article or Service on inner pages) and validate it.',
               'mechanism': 'Without JSON-LD or other structured markup, consumers must infer names, prices '
                            'and dates from visible text and layout. Search engines do not require it for '
                            'indexing, so its absence is an improvement opportunity, not a defect.'},
 'no-llms-txt': {'expected_outcome': 'Offers an optional guide to tools that support this convention; not a '
                                     'search eligibility requirement',
                 'implementation_detail': 'Create /llms.txt. List the key pages and a short site summary.',
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
                  'implementation_detail': 'Identify the high-value orphan pages. Link them from navigation '
                                           'or related content.',
                  'mechanism': 'A page no other page links to is found only through the sitemap, so crawlers '
                               'treat it as unimportant and visitors cannot reach it.'},
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
                                                           'markup only where applicable and validate '
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
                'implementation_detail': 'Add server-side rendering or static generation for key pages, so '
                                         'the facts are in the HTML response.',
                'mechanism': 'Most AI crawlers do not run JavaScript, so content that appears only after scripts '
                             'run is invisible to them.'},
 'render-gap-unconfirmed': {'expected_outcome': 'Clarifies whether a real rendering fix is needed',
                            'implementation_detail': 'Open the page in a browser and compare to the raw HTML',
                            'mechanism': 'The raw HTML carries little text, but nothing confirms that a script '
                                         'adds the content: headless rendering also returned little content or '
                                         'failed, or the page shows no sign of client-side rendering. It may be '
                                         'a genuinely short page rather than a JS dependency'},
 'render-subprocess-timeout': {'expected_outcome': 'Restores confirmed (not just suspected) rendering-gap '
                                                   'findings',
                               'implementation_detail': 'Re-run the audit. Check for bot detection on the '
                                                        'target site.',
                               'mechanism': 'The isolated rendering subprocess exceeded its wall-clock '
                                            'deadline and was terminated; rendering-gap pages fall back to '
                                            'the static-only heuristic'},
 'robots-block': {'expected_outcome': 'Permits the intended compliant crawler where the policy is '
                                      'deliberately changed.',
                  'implementation_detail': 'Confirm the intended public crawling policy; narrow exclusions '
                                           'only if unintended, preserving private paths.',
                  'mechanism': 'The observed robots policy disallows this audit crawler for the evaluated '
                               'URL.'},
 'robots-unreachable': {'expected_outcome': 'Crawlers read a definite crawl policy, and the next audit '
                                            'can assess the site\'s pages.',
                        'implementation_detail': 'Make /robots.txt answer quickly with a 200 and a plain-text '
                                                 'body (or a clean 404 when there are no rules), with no '
                                                 'server error, timeout or bot challenge. Re-run the audit '
                                                 'once it does.',
                        'mechanism': 'Crawlers that cannot read robots.txt cannot learn their permissions: '
                                     'a server error or timeout makes major search crawlers pause crawling '
                                     'until the file can be read, and this audit fetched no page without '
                                     'known permission.'},
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
 'page-orientation': {'expected_outcome': 'Substantial content pages open with a short descriptive heading; '
                                          'the rendered first screen is not measured here.',
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
 'kg-link-missing': {'expected_outcome': 'The site names the one knowledge-graph entity that is the brand, '
                                         'an explicit signal that separates it from same-named entities.',
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
 'kg-namesake-ambiguity': {'expected_outcome': 'The site gives explicit signals that separate the brand from '
                                               'same-named entities; whether assistants confuse them is not '
                                               'measured here.',
                           'implementation_detail': 'Declare the brand knowledge-graph entity in '
                                                    'Organization sameAs and state distinguishing facts '
                                                    '(category, location, founding year) on the site.',
                           'mechanism': 'When other knowledge-graph entities share the brand name, '
                                        'assistants can merge their facts into the brand unless the site '
                                        'states clearly which entity it is.'},
 'alt-text-quality': {'expected_outcome': 'Crawlers, assistants and screen readers can tell what each '
                                          'informative image shows.',
                      'implementation_detail': 'Replace file names and placeholder words in alt text with a '
                                               'short description of the image, use an empty alt for '
                                               'decorative images, and fix the template default that fills '
                                               'alt text automatically.',
                      'mechanism': 'Alt text is the only description of an image that text-based crawlers, '
                                   'assistants and screen readers receive; a file name or a word such as '
                                   'banner describes nothing.'},
 'media-transcript-missing': {'expected_outcome': 'What is said in videos and podcasts becomes quotable text.',
                              'implementation_detail': 'Publish a transcript on the page or link it next to '
                                                       'the player, add a captions track to native players and '
                                                       'enable captions on embeds.',
                              'mechanism': 'Crawlers and assistants do not watch video or listen to audio, so '
                                           'spoken content is invisible to them unless it is also text.'},
 'media-schema-missing': {'expected_outcome': 'Each video and audio clip has a machine-readable title, '
                                              'description, thumbnail and date.',
                          'implementation_detail': 'Add VideoObject markup with name, description, '
                                                   'thumbnailUrl, uploadDate and duration, or AudioObject or '
                                                   'PodcastEpisode markup for audio.',
                          'mechanism': 'Search engines and assistants rely on VideoObject and AudioObject '
                                       'markup to identify and describe embedded media.'},
 'citation-schema-invalid': {'expected_outcome': 'Questions, steps and ratings are reliably read as explicit '
                                                 'facts.',
                             'implementation_detail': 'Complete the FAQPage, HowTo, Review and AggregateRating '
                                                      'markup: questions with accepted answers that are shown '
                                                      'on the page, steps with text, ratings with a value, a '
                                                      'count and an item they rate.',
                             'mechanism': 'Parsers discard FAQ, HowTo and rating markup that is missing '
                                          'required parts or contradicts the page, so the facts it states are '
                                          'lost.'},
 'citation-schema-opportunity': {'expected_outcome': 'Visible questions, steps and ratings are also stated as '
                                                     'explicit structured facts.',
                                 'implementation_detail': 'Add FAQPage, HowTo or AggregateRating markup only '
                                                          'where the page really shows that content. FAQ rich '
                                                          'results no longer appear in Google Search and HowTo '
                                                          'rich results were retired, so the gain is machine '
                                                          'readability, not a search feature.',
                                 'mechanism': 'Question-and-answer pairs, numbered steps and ratings are passages '
                                              'an answer can quote directly; markup states them as explicit '
                                              'structure.'},
 'author-missing': {'expected_outcome': 'Each article has a named author that assistants can credit and '
                                        'check.',
                    'implementation_detail': 'Show a byline on every article and add the author to the Article '
                                             'markup as a Person with name and url.',
                    'mechanism': 'Assistants and search engines weigh who wrote a page (experience, expertise, '
                                 'authority and trust); an unattributed article gives them nothing to weigh.'},
 'author-credentials-weak': {'expected_outcome': 'The expertise behind each article is explicit and '
                                                 'checkable.',
                             'implementation_detail': 'Type the Article author as a Person with a url to an '
                                                      'author page, sameAs profile links and jobTitle, '
                                                      'description or knowsAbout, and show the same name in the '
                                                      'byline.',
                             'mechanism': 'An author given only as a plain name or as the organization, '
                                          'without a profile or credentials, cannot be connected to real '
                                          'expertise.'},
 'llms-txt-invalid': {'expected_outcome': 'Tools that support llms.txt can follow it to the key pages.',
                      'implementation_detail': 'Start llms.txt with one H1 title, add a short summary, list '
                                               'key pages as Markdown links under H2 sections, and serve '
                                               'llms-full.txt as plain text or not at all.',
                      'mechanism': 'Tools that read llms.txt expect its Markdown structure; a file without a '
                                   'title or links, or an HTML page served as llms-full.txt, cannot be '
                                   'followed.'},
 'llms-txt-broken-links': {'expected_outcome': 'Every page llms.txt lists can be read.',
                           'implementation_detail': 'Update or remove each llms.txt entry that answers 404 or '
                                                    '410, and regenerate the file when pages move.',
                           'mechanism': 'llms.txt is a map for assistants; entries that lead to missing pages '
                                        'send them to dead ends instead of the promised content.'},
 'profile-link-broken': {'expected_outcome': 'Every sameAs and profile link resolves to a live profile the '
                                             'brand owns.',
                         'implementation_detail': 'Replace invalid, deleted or share links in sameAs and on '
                                                  'the site with full addresses of the brand\'s own profile '
                                                  'pages.',
                         'mechanism': 'Assistants follow sameAs and profile links to confirm who a brand is; a '
                                      'link that is not a profile or leads to a missing page breaks that '
                                      'chain.'},
 'profile-identity-mismatch': {'expected_outcome': 'Linked profiles and the site confirm each other.',
                               'implementation_detail': 'Confirm the brand owns each listed profile, replace '
                                                        'links to other accounts, and name the brand and the '
                                                        'site on each profile.',
                               'mechanism': 'A profile linked as the brand\'s that names neither the brand '
                                            'nor the site can lead assistants to attribute another account\'s '
                                            'content to the brand.'},
 'review-platform-missing': {'expected_outcome': 'Independent review profiles exist and are linked, so readers '
                                                 'and assistants can check them; their use in answers is not '
                                                 'measured here.',
                             'implementation_detail': 'Claim profiles on review and directory platforms that '
                                                      'fit the business, link them from the site and list them '
                                                      'in Organization sameAs.',
                             'mechanism': 'Assistants judge a brand partly from review and directory '
                                          'platforms; profiles the site does not link are harder to tie to '
                                          'the brand, and missing ones leave nothing to corroborate.'},
 'cwv-field-poor': {'expected_outcome': 'Pages load fast, stay stable and respond quickly for real '
                                        'visitors.',
                    'implementation_detail': 'Fix the Core Web Vitals that field data rates below good, '
                                             'starting with the worst, then recheck the field data after 28 '
                                             'days.',
                    'mechanism': 'Chrome UX Report field data shows real visitors waiting for content, seeing '
                                 'layout shift or waiting for input responses; Google uses these metrics as a '
                                 'page experience signal.'},
 'cwv-risk': {'expected_outcome': 'Lower risk of poor Core Web Vitals; confirm with a browser or field data.',
              'implementation_detail': 'Remove the listed markup patterns (lazy-loaded first image, '
                                       'render-blocking resources, unsized embeds, heavy scripts) and measure '
                                       'the page with PageSpeed Insights.',
              'mechanism': 'Some markup patterns reliably worsen LCP, CLS or INP; without a browser the audit '
                           'can only estimate the risk from them, not measure it.'},
 'hreflang-invalid': {'expected_outcome': 'Each language version is shown and cited to readers of that language.',
                      'implementation_detail': 'Use language or language-REGION codes with absolute URLs, list every '
                                               'version including the page itself, and make every alternate link back.',
                      'mechanism': 'Search engines drop hreflang annotations that are malformed, relative or not '
                                   'confirmed by a return link, so the wrong language version can be served or cited.'},
 'hreflang-missing': {'expected_outcome': 'Readers are sent to and quoted from the version in their language.',
                      'implementation_detail': 'Add reciprocal hreflang annotations for every language version, '
                                               'plus an x-default alternate.',
                      'mechanism': 'Without hreflang, search engines and assistants guess which language version '
                                   'to show and may cite one the reader cannot read.'},
 'canvas-text': {'expected_outcome': 'What each canvas shows is available as text.',
                 'implementation_detail': 'Add fallback text or a data table inside or next to the canvas, '
                                          'role="img" with an aria-label for informative canvases, and aria-hidden '
                                          'for decorative ones.',
                 'mechanism': 'Script-drawn canvas content exists only as pixels, so chart values and labels on it '
                              'are invisible to crawlers, assistants and screen readers.'},
 'svg-inline-facts': {'expected_outcome': 'Facts shown in graphics are also readable as page text.',
                      'implementation_detail': 'Repeat the values drawn in inline SVG as HTML text near the graphic '
                                               'and give the SVG a title.',
                      'mechanism': 'Some text extractors drop inline SVG, so facts that exist only as SVG text may '
                                   'never reach an assistant.'},
 'icon-font-text': {'expected_outcome': 'Extracted page text carries no stray glyphs or icon names.',
                    'implementation_detail': 'Mark icon elements aria-hidden="true", label icon-only controls, and '
                                             'prefer inline SVG icons with a title.',
                    'mechanism': 'Icon fonts draw icons from private-use characters or ligature words that leak '
                                 'into extracted text as meaningless symbols or stray words.'},
 'image-context-missing': {'expected_outcome': 'Every informative image has text that says what it shows.',
                           'implementation_detail': 'Write descriptive alt text, add a figcaption where context is '
                                                    'needed, and use alt="" for decorative images.',
                           'mechanism': 'Crawlers, assistants and screen readers learn what an image shows only from '
                                        'alt text, captions or nearby link text; an image with none says nothing.'},
 'image-weight': {'expected_outcome': 'Images load faster, especially the largest image of each page.',
                  'implementation_detail': 'Serve AVIF or WebP, resize each image to its displayed size with srcset, '
                                           'and compress large photos.',
                  'mechanism': 'Large, oversized or legacy-format image files delay the largest paint and cost '
                               'mobile visitors data.'},
 'responsive-images': {'expected_outcome': 'Each screen downloads an image no larger than it needs.',
                       'implementation_detail': 'Add srcset and sizes, or picture sources, to the main image of '
                                                'each page.',
                       'mechanism': 'Without responsive variants, phones download the same large file as desktops.'},
 'form-label-missing': {'expected_outcome': 'Every form field can be identified and filled in with assistive '
                                            'technology or by an AI agent.',
                        'implementation_detail': 'Tie a visible label element to every field, or use aria-label '
                                                 'where a visible label is impossible.',
                        'mechanism': 'A field with no label has no name in the accessibility tree, so screen-reader '
                                     'users and AI agents cannot tell what it asks for.'},
 'control-name-missing': {'expected_outcome': 'Every link and button says where it leads or what it does.',
                          'implementation_detail': 'Add an aria-label or visually hidden text to icon-only links and '
                                                   'buttons, and hide the icon itself.',
                          'mechanism': 'A link or button with no text or label is announced only as "link" or '
                                       '"button", so it cannot be understood or chosen reliably.'},
 'low-contrast-text': {'expected_outcome': 'Text is readable for visitors with low vision and on bright screens.',
                       'implementation_detail': 'Adjust the listed colour pairs to at least 4.5:1, or 3:1 for large '
                                                'text.',
                       'mechanism': 'Text below the WCAG AA contrast ratio is hard to read for many visitors.'},
 'tap-target-small': {'expected_outcome': 'Controls are easy to hit on a touch screen.',
                      'implementation_detail': 'Make each control at least 24 by 24 CSS pixels or give it enough '
                                               'space from its neighbours.',
                      'mechanism': 'Targets smaller than 24 by 24 CSS pixels are easy to miss on touch screens.'},
 'consent-text-leak': {'expected_outcome': 'Previews, results and assistants describe the page, not the cookie '
                                           'notice.',
                       'implementation_detail': 'Write page-specific descriptions and place consent banner markup '
                                                'after the main content.',
                       'mechanism': 'Cookie-consent wording in the description or at the start of the HTML is read '
                                    'and quoted as if it summarised the page.'},
 'question-answer-indirect': {'expected_outcome': 'The sentence under each question heading can be quoted as '
                                                  'a complete answer.',
                              'implementation_detail': 'Open the text under each question heading with a direct '
                                                       'answer of 40 words or fewer, then add detail and caveats.',
                              'mechanism': 'Assistants lift the passage right after a question heading; a missing, '
                                           'very long or filler first sentence is not a liftable answer.'},
 'table-headers-missing': {'expected_outcome': 'Every value in a data table is tied to a labelled row and column.',
                           'implementation_detail': 'Use th cells with scope for the header row and row labels, '
                                                    'and add a caption that says what the table compares.',
                           'mechanism': 'Parsers map table values to their meaning through th header cells; a '
                                        'table of td cells only leaves values without labels.'},
 'comparison-table-missing': {'expected_outcome': 'Comparison questions can be answered from labelled rows.',
                              'implementation_detail': 'Summarize each comparison in an HTML table with one column '
                                                       'per option and one row per attribute, above the prose.',
                              'mechanism': 'Comparison answers pair each attribute with each option; prose forces '
                                           'the assistant to rebuild that pairing and invites errors.'},
 'spec-list-missing': {'expected_outcome': 'Each product specification is stated once, with its label.',
                       'implementation_detail': 'List key specifications as a definition list or two-column table '
                                                'and mirror them in Product JSON-LD.',
                       'mechanism': 'Specification questions are answered from labelled facts; prose spreads a '
                                    'fact across sentences where it is easy to miss.'},
 'location-markup-missing': {'expected_outcome': 'The brand can be matched to questions about a place.',
                             'implementation_detail': 'Add a PostalAddress, geo coordinates and areaServed to the '
                                                      'Organization or LocalBusiness JSON-LD, matching the '
                                                      'visible address.',
                             'mechanism': 'Assistants tailor answers to the asker\'s location using '
                                          'machine-readable addresses and service areas; a location shown only '
                                          'as text or a map is easy to miss.'},
 'local-business-incomplete': {'expected_outcome': 'The LocalBusiness markup carries the address and location '
                                                   'properties local consumers read; each platform decides its '
                                                   'own eligibility.',
                               'implementation_detail': 'Give every LocalBusiness node an address, plus geo for a '
                                                        'storefront or areaServed for a service-area business.',
                               'mechanism': 'Google requires an address on LocalBusiness markup, and without geo '
                                            'or areaServed it cannot be matched to where the asker is.'},
 'audience-segment-missing': {'expected_outcome': 'Assistants have a page to match to the asker\'s stated '
                                                  'role or need.',
                              'implementation_detail': 'Publish one page per main audience, naming it in the '
                                                       'title and H1, and link those pages from the navigation.',
                              'mechanism': 'Assistants weight answers toward who is asking; without pages for named '
                                           'audiences there is nothing to match that context to.'},
 'contact-markup-missing': {'expected_outcome': 'The brand\'s own email and phone number are stated as '
                                                'explicit structured facts.',
                            'implementation_detail': 'Add email, telephone and a contactPoint to the Organization '
                                                     'JSON-LD, matching the contact page.',
                            'mechanism': 'Assistants read contact details from email, telephone and contactPoint '
                                         'properties; details shown only as text or links are easy to miss or to '
                                         'attribute to another organization.'},
 'site-search-missing': {'expected_outcome': 'Visitors can restate their need in one step on a large site.',
                         'implementation_detail': 'Add a labelled search form to the shared header, with linkable '
                                                  'result URLs and a WebSite SearchAction.',
                         'mechanism': 'Visitors arriving from an AI answer often have a follow-up need; on a large '
                                      'site without search they must browse menus or leave.'},
 'context-retention-missing': {'expected_outcome': 'The site offers a way to save and resume a task; visitor '
                                                   'behaviour is not measured here.',
                               'implementation_detail': 'Add save-for-later or wishlist controls and a recently '
                                                        'viewed list that persists across visits.',
                               'mechanism': 'Without saved state each visit starts from zero, so a returning '
                                            'visitor must find the same items again.'},
 'deep-link-params-dropped': {'expected_outcome': 'Deep links land visitors on the exact view they promise.',
                              'implementation_detail': 'Make each redirect append the original query string, and '
                                                       'link to final URLs with their parameters.',
                              'mechanism': 'A redirect that strips query parameters turns a link to a filtered '
                                           'or preselected view into a link to a generic page.'},
 'viewport': {'expected_outcome': 'Improves responsive layout configuration; actual layout still requires '
                                  'testing.',
              'implementation_detail': 'Add a responsive viewport declaration and verify real mobile layout.',
              'mechanism': 'Missing viewport configuration can impair responsive layout on mobile.'},
 'zoom': {'expected_outcome': 'Allows users to enlarge text where supported.',
          'implementation_detail': 'Remove unnecessary user-scalable=no and maximum-scale restrictions; test '
                                   'zoom.',
          'mechanism': 'A restrictive viewport declaration can impede user zoom.'}} .items()})

REQUIRED_FIELDS = ("mechanism", "implementation_detail", "expected_outcome")

# Check IDs that no script emits any more. Their entries stay so that a report
# saved by an earlier version still validates when the agent stage is merged in.
RETIRED_CHECK_IDS = frozenset({"email-summary"})

# Base confidence per check, proposed by tests/score_benchmark.py --suggest from
# labelled dev findings (measured precision rounded down to a 0.1 step, at most
# 0.9). A check not listed keeps the confidence its script states. Holdout sites
# were not used. The labels were made by an agent and have not been reviewed by a
# person, and no rule has more than 6 labelled findings (one per site), so every
# value is a heuristic, not an empirical probability: CALIBRATION_PROVENANCE
# records the basis of each one.
CALIBRATED_CONFIDENCE = MappingProxyType({
    "contact-markup-missing": 0.9,
    "cwv-risk": 0.9,
    "heading-hierarchy": 0.9,
    "markup-ratio": 0.8,
    "missing-description": 0.9,
    "no-llms-txt": 0.9,
    "page-type-schema-gap:about": 0.9,
    "responsive-images": 0.9,
    "social-metadata": 0.9,
    "title-length": 0.8,
})


# Dataset: benchmark_runs/dev/findings.csv (142 labelled dev findings, 7 sites),
# SHA-256 prefix 97807eaac874f7ea, scored 2026-10-12. evidence_class separates a
# directly observed local fact (the check reads a value that is or is not there)
# from a heuristic applicability judgement (a threshold or a page-type guess
# decides whether the observation matters).
_CALIBRATION_RUN = {"dataset": "benchmark_runs/dev/findings.csv", "dataset_sha256_prefix": "97807eaac874f7ea",
                    "scored_on": "2026-10-12", "split": "dev", "labels_reviewed_by_person": False,
                    "method": "heuristic"}


def _basis(labelled, tp, fp, irrelevant, sites, evidence_class):
    return MappingProxyType(dict(_CALIBRATION_RUN, labelled=labelled, tp=tp, fp=fp, irrelevant=irrelevant,
                                 sites=sites, evidence_class=evidence_class))


CALIBRATION_PROVENANCE = MappingProxyType({
    "contact-markup-missing": _basis(6, 6, 0, 0, 6, "observed_fact"),
    "cwv-risk": _basis(5, 5, 0, 0, 5, "heuristic_applicability"),
    "heading-hierarchy": _basis(5, 5, 0, 0, 5, "observed_fact"),
    "markup-ratio": _basis(6, 5, 0, 1, 6, "heuristic_applicability"),
    "missing-description": _basis(6, 6, 0, 0, 6, "observed_fact"),
    "no-llms-txt": _basis(5, 5, 0, 0, 5, "observed_fact"),
    "page-type-schema-gap:about": _basis(5, 5, 0, 0, 5, "heuristic_applicability"),
    "responsive-images": _basis(5, 5, 0, 0, 5, "observed_fact"),
    "social-metadata": _basis(6, 6, 0, 0, 6, "observed_fact"),
    "title-length": _basis(6, 5, 0, 1, 6, "heuristic_applicability"),
})


def confidence_basis(check_id):
    """Where a finding's base confidence comes from: the dev labels behind a
    tabled value, or the script's own rule."""
    if check_id in CALIBRATION_PROVENANCE:
        return dict(CALIBRATION_PROVENANCE[check_id], base_value=CALIBRATED_CONFIDENCE[check_id])
    return {"method": "script_rule"}


def calibrated_confidence(check_id, default):
    """The measured base confidence of a check, or its script's default."""
    return CALIBRATED_CONFIDENCE.get(check_id, default)

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
    # An agent finding states its own heuristic (provenance.confidence_method).
    finding.setdefault("confidence_basis", confidence_basis(check_id))
    action = dict(finding["suggested_action"])
    action["implementation_detail"] = entry["implementation_detail"]
    action["expected_outcome"] = entry["expected_outcome"]
    finding["suggested_action"] = action
    return finding
