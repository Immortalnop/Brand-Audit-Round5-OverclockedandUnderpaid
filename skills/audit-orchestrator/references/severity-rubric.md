# Severity rubric

Every finding's severity is set by the skill that raises it, from two things: how
much the problem stops an assistant or a visitor (impact), and how much of the
site it covers (reach). The entrypoint then applies one gate to every finding,
whatever skill raised it.

## Impact tiers

| Tier | Meaning | Example |
| --- | --- | --- |
| critical | The site cannot be read at all by the systems in question | robots.txt blocks every crawler from the whole site |
| high | A main path to being found, read or quoted is broken | AI search crawlers are disallowed; key pages are built only by JavaScript; JSON-LD on key pages does not parse |
| medium | Facts can be found but are easy to miss, misread or attribute to the wrong brand | product pages show a price but carry no Product/Offer markup; a linked profile names another business |
| low | A refinement, or a gap with a cheap and safe fix | missing Open Graph image; a long title |

## Reach

A defect seen on less than half of the relevant pages steps down one tier
(`models.step_down_severity`), and confidence is scaled by how much of the site was
analyzed (`models.scale_confidence`). A finding always says how many pages it was
seen on ("3/40 sampled pages").

## The severity gate (entrypoint, all skills)

A `high` or `critical` finding must be either:

- `confirmed`: directly observed, such as a robots.txt rule or a parse error, or
- backed by two independent kinds of evidence, such as near-empty raw HTML
  together with an empty app mount point and a framework bundle.

Otherwise its severity is lowered one tier at a time until the rule holds, the
action priority is lowered with it, and the finding records the change in
`severity_gate` (`from`, `to`, `reason`). The gate runs in
`prioritize_findings.py` and again in `validate_report.py`, so no skill, script or
agent stage can emit a top severity that one heuristic signal produced.

Worked example: a page has 40 characters of raw text and runs a script, and
nothing else is known. That is `render-gap-unconfirmed` (insufficient evidence,
low): it may be a short splash page. Add an empty `<div id="root">` and it is a
suspected `render-gap` at medium. Add a `__NEXT_DATA__` state blob as well and it
is high, because two independent signs of client-side rendering now agree.
Rendering the page in a headless browser that shows substantial content makes it
confirmed.

## Positive evidence before exemptions

Checks that apply only to some kinds of site (review platforms, saved items,
Product markup) are skipped only on positive evidence that they do not apply:
news markup for a publisher, nonprofit markup or a donation link for a
nonprofit, no price, buy control or Product markup for a "shop". A site with no
such evidence is checked.
