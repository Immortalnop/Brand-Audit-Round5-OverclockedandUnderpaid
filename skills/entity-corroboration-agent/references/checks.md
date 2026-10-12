# Agent-stage checks (AG-01 to AG-03)

These three checks are deliberately not automated. Each requires judging natural
language, which a fixed threshold cannot do without producing false positives on
unseen sites. The calling agent performs them and hands findings back; the
entrypoint ingests them in-process and reconstructs each through the shared finding
factory, so catalog wording and Invariant I-1 apply exactly as for script findings.

Catalog rule IDs used after ingest: AG-01 maps to about-concreteness, AG-02 to
no-independent-mention, AG-03 to independent-contradiction.

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
