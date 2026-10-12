# Agent-stage checks (AG-01 to AG-06)

These checks are deliberately not automated. Each needs judgement over natural
language or pixels, or a lookup on third-party sites that a robots-respecting
script cannot make (Wikidata and Wikipedia disallow their search endpoints to
scripts; review platforms answer automated clients with challenges), so a fixed
script would produce false positives or nothing at all on unseen sites. The calling agent performs them and hands findings back; the
entrypoint ingests them in-process and reconstructs each through the shared finding
factory, so catalog wording and Invariant I-1 apply exactly as for script findings.

Catalog rule IDs used after ingest: AG-01 maps to about-concreteness, AG-02 to
no-independent-mention, AG-03 to independent-contradiction, AG-04 to
facts-in-images (the same check the script runs, so the two merge), AG-05 to
kg-namesake-ambiguity, AG-06 to review-platform-missing.

- AG-01 (medium) About-page self-description is not concrete enough to quote.
  Judged on `agent_brief.json -> ag01.opening_passage`, which the acquisition step
  extracts from the About page (or the homepage when the site links to no About
  page) with navigation removed. If `ag01.assessable` is false the check is
  recorded as insufficient_evidence, never judged on a substitute page. Fires when
  that opening leaves any of these unanswerable: who the organization is, what it specifically
  does or sells, in what category or market. Mechanism: assistants lift the About
  passage for identity questions; text that names no product and no category gives
  them nothing quotable, so they paraphrase from elsewhere and the description
  drifts. Register is not a defect; only missing substance fires.

- AG-02 (low, confirmed) No independent mention of the brand found.
  Fires only when a search actually ran and returned no independent mention.
  Mechanism: corroboration across unrelated sources is what makes a fact safe for
  an assistant to repeat; a brand discussed nowhere but its own site is a single
  fragile assertion. Severity stays low because absence of community discussion is
  normal for smaller and younger organizations, and is an opportunity rather than a
  fault.

- AG-03 (high, confirmed) Independent sources contradict the site.
  Fires when a specific independent source states something incompatible with the
  site claims: a different category, ownership, location, or a same-named different
  entity dominating results. Mechanism: when sources disagree, retrieval surfaces
  the discrepancy and confidence drops across every fact associated with the
  entity, including the ones that were correct. This is the most damaging of the
  three and the most frequently missed, because the site itself looks healthy.

- AG-04 (medium, confirmed) Facts are carried inside images. Judged by reading
  each image in `agent_brief.json -> ag04.images` with the agent's own vision.
  Fires only when the image shows concrete facts (prices, opening hours, menu
  items, specifications, dates) that the page's text does not state; name the
  facts in the evidence and pass the page URL in `affected_pages`. A decorative
  image, a screenshot of the interface or an image whose facts are also in the
  text does not fire. Mechanism: text extractors read pixels as nothing, so the
  facts are invisible to most AI fetchers.

- AG-05 (medium, confirmed) Namesakes and no distinguishing entity. Run the
  queries in `ag05.queries`. Fires when other organizations with the same name
  appear in the results (or in Wikidata) and the site gives no distinguishing
  link: `ag05.declared_wikidata` is empty, or the declared item is a different
  entity. Name the namesakes in the evidence. Mechanism: Appendix D's mistaken
  identity -- without a disambiguating entity link, assistants merge facts about
  different organizations.

- AG-06 (low, confirmed) No profile on the review or directory platforms the
  category uses. Run the queries in `ag06.queries` for the platforms in
  `ag06.platforms` (chosen by `ag06.business_kind`; public bodies get none and
  never fire). Fires only when the searches ran and found no profile for the
  brand. Mechanism: review and directory platforms are independent sources
  assistants use to corroborate a brand and to answer "is X any good?".

## The three-outcome rule

Every corroboration search resolves to exactly one of: agrees (record in notes, no
finding), absent (AG-02, confirmed), contradicts (AG-03, confirmed). A fourth
state, could not check, is not one of the three: it is either supplied with status
insufficient_evidence or not supplied at all, and the stage records not_supplied.
Invariant I-1 caps any insufficient_evidence entry at low severity and relabels it
advisory.

Collapsing could not check into absent is the single most common way an audit
manufactures a false positive, because the search tool availability has nothing to
do with the site being audited.
