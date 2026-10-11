1. Previous always 50 page crawl cap vs. now smart 50 page selection[See point A. in plan.md]
2. Wrong brand name in snippets
3. svg and ICO files are skipped?
4. false positives in question heading checks
5. The email-summary check still fires on any signup form (gating it was point 5, not requested). : How to fix it (not applied; read-only):
In html_features.py, record each form's own text: button labels, its action URL, and the id, class and name values.
Count a form as a newsletter signup only if it has an email input and words like subscribe, newsletter or sign up, and no password field.
In analyze_experience.py:26, use that signup flag instead of email_capture and forms.
Add tests: a contact form with an email field must not fire, and a newsletter form must fire.

❯ 
1. Pick 10-15 new sites. Don't reuse the 7 we tuned on (snu, python.org, stripe, allbirds, bbc, notion, joespizza). Mix the kinds: a shop, a SaaS company, a news site, a local business, a university, a single-page app. Put one per line in urls.txt, starting each with dev or holdout:
dev https://site-a.com
holdout https://site-b.com
2. Run the audits.
LIVE_BENCHMARK=1 python tests/live_benchmark.py urls.txt
   This writes benchmark_runs/findings.csv, with one row per finding
3. Label each row. Open the site, check the finding, and fill in one of:
   - tp: real problem, correctly reported
   - fp: wrong; the problem isn't there
   - irrelevant: true, but not worth reporting for this kind of site
4. Score it.
python tests/score_benchmark.py benchmark_runs/findings.csv --split
   You get precision, high-severity precision and calibration error as real numbers.

The dev/holdout split matters. Use the dev sites to find and fix rules that misfire. Score the holdout sites only once, at the end. If you tune on the same sites you score, the number looks better than it really is. That's exactly the since I checked against the same 7 sites I fixed things on.
