1. Previous always 50 page crawl cap vs. now smart 50 page selection[See point A. in plan.md]
2. Wrong brand name in snippets
3. svg and ICO files are skipped?
4. false positives in question heading checks
5. The email-summary check still fires on any signup form (gating it was point 5, not requested). : How to fix it (not applied; read-only):
In html_features.py, record each form's own text: button labels, its action URL, and the id, class and name values.
Count a form as a newsletter signup only if it has an email input and words like subscribe, newsletter or sign up, and no password field.
In analyze_experience.py:26, use that signup flag instead of email_capture and forms.
Add tests: a contact form with an email field must not fire, and a newsletter form must fire.