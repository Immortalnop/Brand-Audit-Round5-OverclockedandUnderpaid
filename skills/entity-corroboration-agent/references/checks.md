# Agent-stage checks (AG-01 to AG-06)

These checks are deliberately not automated. Each requires judging natural
language, viewing an image or searching sites that block scripts. The calling
agent performs them from the audit's evidence packet and hands back one outcome
per check (the outcome envelope, see SKILL.md); the entrypoint validates the
evidence each check needs, caps severity at the ceiling below, and rebuilds each
finding through the shared finding factory, so catalog wording and Invariant I-1
apply exactly as for script findings. No agent check is critical.

Catalog rule IDs used after ingest: AG-01 maps to about-concreteness, AG-02 to
no-independent-mention, AG-03 to independent-contradiction, AG-04 to
facts-in-images, AG-05 to kg-namesake-ambiguity, AG-06 to review-platform-missing.

- AG-01 (medium) About-page self-description is not concrete enough to quote.
  Fires when the opening of the About page (or homepage, if there is no About page)
  leaves any of these unanswerable: who the organization is, what it specifically
  does or sells, in what category or market. Mechanism: assistants lift the About
  passage for identity questions; text that names no product and no category gives
  them nothing quotable, so they paraphrase from elsewhere and the description
  drifts. Register is not a defect; only missing substance fires.

- AG-02 (low, scoped to the searches run) No independent mention of the brand found.
  Fires only when a search actually ran and returned no independent mention.
  Mechanism: corroboration across unrelated sources is what makes a fact safe for
  an assistant to repeat; a brand discussed nowhere but its own site is a single
  fragile assertion. Severity stays low because absence of community discussion is
  normal for smaller and younger organizations, and is an opportunity rather than a
  fault.

- AG-03 (high only for a material conflict with an inspected source, else medium;
  confirmed with two or more inspected source domains, else suspected)
  Independent sources contradict the site.
  Fires when a specific independent source states something incompatible with the
  site claims: a different category, ownership, location, or a same-named different
  entity dominating results. Mechanism: when sources disagree, retrieval surfaces
  the discrepancy and confidence drops across every fact associated with the
  entity, including the ones that were correct. This is the most damaging of the
  three and the most frequently missed, because the site itself looks healthy.
  A conflict does not show which source is wrong, so the action is to reconcile
  it, not to change the site to match the external source.

- AG-04 (medium, confirmed) Facts are drawn inside an image instead of stated in
  text. Fires when the agent views an image and sees a concrete fact (price,
  opening hours, phone number, specification) that the page text does not state.
  Mechanism: crawlers and assistants read HTML text, not pixels, so a fact that
  exists only inside an image is invisible to them. The scripts read SVG text and
  flag raster images by name; only this vision step can confirm what a raster
  image shows. Supply affected_pages so the finding merges with the script
  finding for the same pages.

- AG-05 (medium, confirmed) Other knowledge-graph entities share the brand name.
  Fires when a search of Wikidata and Wikipedia finds an entity with the same or a
  near-identical name that is a different organization, person, place or product,
  and the site does not declare its own entity in Organization sameAs.
  Mechanism: knowledge graphs are the main signal assistants use to tell
  same-named entities apart; without a declared entity, facts about the namesake
  can be merged into the brand. The scripts only verify a declared entity
  (kg-link-missing, kg-entity-mismatch); robots.txt for both hosts disallows their
  search endpoints, so the name lookup is this agent step. Having no Wikidata entry
  at all is not a defect and records nothing.

- AG-06 (low, confirmed) The brand has no profile on the review platforms that
  fit its business. Fires when searches of the fitting review and directory
  platforms (Trustpilot, G2, Capterra, Google Business Profile, Yelp,
  Tripadvisor, Crunchbase and similar) ran and found no profile of the brand;
  status suspected when a profile exists but the site does not link it.
  Mechanism: assistants judge a brand partly from independent ratings and
  reviews; profiles the site does not link are harder to tie to the brand, and
  missing ones leave nothing to corroborate. The scripts only see linked
  profiles, because review sites block automated clients, so the name search is
  this agent step.

## Outcomes

Every check resolves to exactly one outcome: pass (assessed, nothing to report),
finding (assessed, with the evidence the check needs), not_assessed (the
capability was missing or the check was not run) or error. Corroboration
searches map as: agrees (AG-02 and AG-03 pass), absent (AG-02 finding),
contradicts (AG-03 finding). Could not check is not_assessed, never a pass and
never absent. A check left out of the envelope is recorded as not_assessed.

Collapsing could not check into absent is the single most common way an audit
manufactures a false positive, because the search tool availability has nothing to
do with the site being audited.
