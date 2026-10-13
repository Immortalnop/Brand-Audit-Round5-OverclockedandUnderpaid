# Brand AI-Readiness Audit: https://www.npr.org/

- **Audited at:** 2026-10-13T03:29:17.176108+00:00
- **Run:** No page could be analyzed, so the site's pages were not assessed
- **Pages:** 0 analyzed of 1 discovered; 0 of 1 site sections reached
- **Run time:** 10.2 seconds
- **Time limits:** audit worker stopped at 200 seconds (enforced); 55 seconds left for the optional agent stage (not enforced by the audit)
- **Requests to the site:** 2 of at most 90

This report checks a sample of pages from outside, the way an AI assistant or crawler sees the site. It changes nothing on the site.

## How far to trust this report

**Confidence:** low (0.00)

Confidence is low (0.00). The weakest of its parts sets the score, here the audit run. No page could be analyzed: a connection to the server could not be made (while reading robots.txt). Also weak: No page could be analyzed, so the site's content was not assessed. Brand identity (reported separately, not part of the score): No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. The score rates how far the report speaks for the whole site; each finding has its own confidence and status, and a problem seen on a page is still real on that page.

| Part | Score | Why |
| --- | --- | --- |
| Page sample | 0.00 | No page could be analyzed, so the site's content was not assessed. |
| Brand identity (not in the score) | 0.00 | No Organization or Product JSON-LD was found on the analyzed pages, so the audit could not confirm which brand the site belongs to. Adding Organization markup raises this part. |
| Audit run | 0.00 | No page could be analyzed: a connection to the server could not be made (while reading robots.txt). |

## Summary

**Why this report is short:** No page could be analyzed: a connection to the server could not be made (while reading robots.txt).

| | Count |
| --- | --- |
| Findings | 1 |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 1 |
| Improvement suggestions (not defects) | 1 |
| Not enough evidence to judge | 1 |
| Recommendations | 3 |

## All findings

| ID | Type | Severity | Status | Finding | Pages |
| --- | --- | --- | --- | --- | --- |
| F-001 | Improvement opportunity | low | not enough evidence to judge | robots.txt could not be retrieved or parsed | 1 |

## Finding details

### F-001: robots.txt could not be retrieved or parsed

Type: Improvement opportunity; Severity: low; Status: not enough evidence to judge; Confidence: 0.30; Check: `robots-unreachable`; Rule assessed-page denominator: unavailable

**Priority basis:** low severity, insufficient\_evidence status, confidence 0.3; 1 supported page(s), low effort. Ties use title, URLs, cause and stable ID. Provenance explains confidence; no extra score is applied.

**Why it matters:** robots.txt fetch/parse status was 'inaccessible'; no page was fetched, since crawl permission was unknown, rather than assuming unrestricted access

**Pages:**

- <https://www.npr.org/>

**Evidence:**

- robots.txt status: inaccessible
  - <https://www.npr.org/>
- robots.txt status: inaccessible

**What to do:** Confirm robots.txt is reliably reachable and well-formed

**Suggested roles:** infrastructure, seo

1. Check robots.txt responds quickly with a 200 or a clean 404
2. Re-run the audit once robots.txt is reachable

Effort: low; Impact: low; Fill-in: small value, small work; do when convenient.

**Expected benefit:** Enables a real crawl-permission verdict

**How to check the fix:** Re-run and confirm robots\_data.status is 'ok' or 'absent'

## Other recommendations

Good practice to keep, beyond the findings above:

- **Keep internal linking intentional as the site grows.** Keep internal linking intentional as the site grows
- **Continue building independent, identity-matched off-site mentions.** Continue building independent, identity-matched off-site mentions

## Agent checks

Received: not supplied. Assessed: 0 of 6 (not\_run). A check that was not assessed is not a pass.

| Check | Outcome | Reason |
| --- | --- | --- |
| AG-01 About-page concreteness | not assessed | The agent stage was not supplied. |
| AG-02 Independent mentions | not assessed | The agent stage was not supplied. |
| AG-03 Independent contradiction | not assessed | The agent stage was not supplied. |
| AG-04 Facts drawn inside images | not assessed | The agent stage was not supplied. |
| AG-05 Namesake ambiguity | not assessed | The agent stage was not supplied. |
| AG-06 Review and profile opportunity | not assessed | The agent stage was not supplied. |

## What this audit could not check

- No page could be analyzed: a connection to the server could not be made (while reading robots.txt). Only checks that read robots.txt, llms.txt, the sitemap or the TLS connection are reported; nothing on the pages was assessed, and nothing unassessed has passed.
- robots.txt could not be reliably retrieved or parsed (status: 'inaccessible'); no pages were fetched without known permission, so most on-site checks in this report are insufficient\_evidence rather than confirmed.
- 1 discovered URL(s) were never fetched (permission, acquisition failure, or budget constraints; out of 1 discovered); findings reflect only the 0 page(s) actually crawled, not the whole site. The sample reached 0 of 1 site sections (first path segment).
- Headless browser rendering was not available in this environment; rendering-gap findings are based on a static-content heuristic only and are reported as suspected/insufficient\_evidence rather than confirmed.
- No external search provider was configured; claim corroboration and off-site footprint assessment were not checked this run (not the same as "nothing found").
- Review and directory platforms (Trustpilot, G2, Google Business Profile and others) were not searched for the brand: they block automated clients, no search provider was configured, and the agent stage (AG-06) was not supplied. Only profiles linked from the site were considered.
- Core Web Vitals (LCP, CLS, INP) were not measured: the audit runs no browser and no PAGESPEED\_API\_KEY is configured. Web-vitals findings are estimates from markup patterns, not measurements.
- sitemap.xml could not be checked (status: 'not\_checked'); crawl coverage may be incomplete relative to a site that publishes one.
- No eligible page was analyzed for the agent evidence packet.

## Notes from the run

- robots\_txt\_inaccessible\_conservative\_crawl
- No pages were acquired; rendering cannot be assessed.
- No dated facts found; freshness cannot be assessed (absence is not proof of staleness).
- Entity identity unresolved; corroboration suppressed.
- External footprint not assessed: identity unresolved or below confidence threshold.
- No Organization markup on the crawled pages; the knowledge-graph link was not assessed.
- Agent corroboration stage not supplied (no AGENT\_FINDINGS\_PATH); the qualitative About-concreteness and cross-web corroboration checks were not run this audit (not checked, not "no corroboration found"). See skills/entity-corroboration-agent/SKILL.md.

---

Generated from the JSON audit report by common/report_markdown.py. Findings describe the sampled pages; the JSON report holds every detail.
