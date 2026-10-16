"""test_dev_calibration_fixes.py -- rules corrected after labelling the dev benchmark sites.

Each group pins one mechanism that produced false or empty findings on real
pages, together with the case the rule must still catch:
  - page-orientation: a short H1 ("About us") orients a visitor; a missing H1
    still counts.
  - teaser headings: a question heading whose text a link to another page
    repeats (a news card with an empty overlay link labelled with the headline)
    is not a question the page answers.
  - decorative video: a muted autoplay video with no controls is a background,
    not media that needs a transcript or VideoObject markup.
  - noscript images: an image inside <noscript> (a tracking pixel, a fallback
    copy) is not a content image.
  - term-repetition: only running text counts; list items and card labels
    repeat a word by design.
  - markup-ratio: reported below 3% visible text, not at framework-typical 3-8%.
  - Google Maps place links: the page names only the map application, so the
    profile is unverified, never a mismatch.
  - email signup: stated in the warnings, never a finding.

Every rule is a mechanism (what a page shape means), never a site or brand name.
Nothing here touches the network.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
             "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts", "tests"):
    if os.path.join(_ROOT, _rel) not in sys.path:
        sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import Limits
from models import make_deadline
from test_precision_traps import SITE, page, snapshot
from transport import Response

LIMITS = Limits()
# 400 distinct made-up words in sentences of 16, so no word dominates the text.
_SYLLABLES = ("ba", "ko", "ri", "mu", "te", "lo", "vi", "sa")
_VOCAB = [a + b + c for a in _SYLLABLES for b in _SYLLABLES for c in _SYLLABLES][:400]
WORDS = "".join("<p>" + " ".join(_VOCAB[i:i + 16]).capitalize() + ".</p>" for i in range(0, 400, 16))


def deadline():
    return make_deadline(LIMITS)


def rule_ids(result):
    return {f["provenance"]["rule_id"] for f in result["findings"]}


# ---------------------------------------------------------------------------
# page-orientation
# ---------------------------------------------------------------------------

def test_short_descriptive_h1_orients_the_page():
    from analyze_experience import analyze_experience
    short = page("<main><h1>About us</h1>" + WORDS + "</main>", head="<title>About us</title>", url=SITE + "/about")
    three = page("<main><h1>Ian Berry obituary</h1>" + WORDS + "</main>", url=SITE + "/obituary")
    assert "page-orientation" not in rule_ids(analyze_experience(snapshot(short, three), deadline()))


def test_page_with_no_h1_or_only_overlong_headings_still_lacks_orientation():
    from analyze_experience import analyze_experience
    none = page("<main>" + WORDS + "</main>", url=SITE + "/a")
    long_heading = "<h1>" + "word " * 20 + "</h1>"
    overlong = page("<main>" + long_heading + "<h2>" + "other " * 18 + "</h2>" + WORDS + "</main>", url=SITE + "/b")
    result = analyze_experience(snapshot(none, overlong), deadline())
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "page-orientation")
    assert set(finding["evidence"][0]["urls"]) == {SITE + "/a", SITE + "/b"}


# ---------------------------------------------------------------------------
# teaser headings
# ---------------------------------------------------------------------------

_CARD = ('<div class="card"><a href="/2026/story-{n}" aria-label="{q}"></a>'
         '<h3><span>Kicker</span>{q}</h3></div>')
_QUESTIONS = ("Is the city ready for the coming storm season?", "Why are rents still rising in the north?",
              "Can small farms survive another dry summer?")


def test_question_teaser_with_overlay_link_is_marked_and_not_judged():
    from analyze_answer_format import analyze_answer_format
    from analyze_citation_schema import analyze_citation_schema
    cards = "".join(_CARD.format(n=n, q=q) + "<p>12 comments</p>" for n, q in enumerate(_QUESTIONS))
    front = page("<main><h1>News</h1>" + cards + WORDS + "</main>", url=SITE + "/news")
    qas = front.features["question_answers"]
    assert len(qas) == 3 and all(qa["teaser"] for qa in qas)
    assert "question-answer-indirect" not in rule_ids(analyze_answer_format(snapshot(front), deadline()))
    citation = analyze_citation_schema(snapshot(front), deadline())
    assert not any("FAQPage" in e["description"] for f in citation["findings"] for e in f["evidence"])


def test_real_questions_on_the_page_are_still_judged():
    from analyze_answer_format import analyze_answer_format
    from analyze_citation_schema import analyze_citation_schema
    # An in-page table of contents links with "#" and does not make a teaser.
    toc = "".join(f'<a href="#q{n}">{q}</a> ' for n, q in enumerate(_QUESTIONS))
    faq = "".join(f'<h2 id="q{n}">{q}</h2><p>Yes. The short answer comes first here.</p>'
                  for n, q in enumerate(_QUESTIONS))
    unanswered = f"<h2>{_QUESTIONS[0].replace('city', 'town')}</h2><h2>Next section</h2>"
    p = page("<main><h1>Questions</h1>" + toc + faq + unanswered + WORDS + "</main>", url=SITE + "/faq")
    assert not any(qa["teaser"] for qa in p.features["question_answers"])
    assert "question-answer-indirect" in rule_ids(analyze_answer_format(snapshot(p), deadline()))
    citation = analyze_citation_schema(snapshot(p), deadline())
    assert not citation["findings"]  # missing optional FAQPage is no website defect


# ---------------------------------------------------------------------------
# decorative video
# ---------------------------------------------------------------------------

def test_muted_autoplay_background_video_needs_no_transcript_or_markup():
    from analyze_media_text import analyze_media_text
    background = page('<main><h1>Our story</h1><video autoplay muted loop playsinline '
                      'poster="/a.jpg"><source src="/loop.mp4"></video>' + WORDS + "</main>", url=SITE + "/story")
    assert background.features["media_records"][0]["decorative"] is True
    found = rule_ids(analyze_media_text(snapshot(background), deadline()))
    assert not {"media-transcript-missing", "media-schema-missing"} & found


def test_video_a_visitor_plays_is_still_checked():
    from analyze_media_text import analyze_media_text
    for tag in ('<video controls src="/talk.mp4"></video>', '<video autoplay muted controls src="/talk.mp4"></video>',
                '<video src="/talk.mp4"></video>'):
        p = page("<main><h1>Talk</h1>" + tag + WORDS + "</main>", url=SITE + "/talk")
        assert p.features["media_records"][0]["decorative"] is False, tag
        assert {"media-transcript-missing", "media-schema-missing"} <= rule_ids(
            analyze_media_text(snapshot(p), deadline())), tag


# ---------------------------------------------------------------------------
# noscript images
# ---------------------------------------------------------------------------

def test_noscript_pixel_is_not_a_content_image():
    p = page('<main><h1>Home</h1><noscript><img src="https://beacon.example/p?c=1"></noscript>'
             '<img src="/hero.jpg" alt="A red bicycle">' + WORDS + "</main>")
    assert [r["src"] for r in p.features["image_records"]] == ["https://fixture.example/hero.jpg"]
    assert p.features["missing_alt"] == 0
    bare = page('<main><h1>Home</h1><img src="/a.jpg"><img src="/b.jpg"><img src="/c.jpg">' + WORDS + "</main>")
    assert bare.features["missing_alt"] == 3 and len(bare.features["image_records"]) == 3


# ---------------------------------------------------------------------------
# term-repetition
# ---------------------------------------------------------------------------

def test_repeated_labels_in_short_blocks_are_not_stuffing():
    from analyze_answer_content import analyze_answer_content
    identity = {"data": {"canonical_name": "Fixture", "confidence": 0.9}}
    listing = "".join(f"<li><a href='/post-{n}'>Post number {n}</a> <span>{n} years ago</span></li>"
                      for n in range(150))
    p = page("<main><h1>Blog</h1><ul>" + listing + "</ul>" + WORDS + "</main>", url=SITE + "/blog")
    assert "term-repetition" not in rule_ids(analyze_answer_content(snapshot(p), identity, deadline()))


def test_a_word_stuffed_into_sentences_is_still_reported():
    from analyze_answer_content import analyze_answer_content
    identity = {"data": {"canonical_name": "Fixture", "confidence": 0.9}}
    stuffed = "<p>" + "Cheap widgets ship fast because our widgets beat other widgets for widgets buyers. " * 30 + "</p>"
    p = page("<main><h1>Widgets</h1>" + stuffed + "</main>", url=SITE + "/w")
    result = analyze_answer_content(snapshot(p), identity, deadline())
    assert "term-repetition" in rule_ids(result)
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "term-repetition")
    assert "words of running text" in finding["evidence"][0]["description"]


# ---------------------------------------------------------------------------
# markup-ratio
# ---------------------------------------------------------------------------

def test_markup_ratio_reports_below_three_percent_only():
    from analyze_performance import analyze_performance
    text = "<p>" + "readable " * 100 + "</p>"
    typical = page("<div>" + "<span class='x'></span>" * 700 + "</div>" + text, url=SITE + "/typical")
    bloated = page("<div>" + "<span class='x'></span>" * 3000 + "</div>" + text, url=SITE + "/bloated")
    ratio = {p.url: p.features["full_visible_bytes"] / p.features["html_bytes"] for p in (typical, bloated)}
    assert 0.03 < ratio[SITE + "/typical"] < 0.08 and ratio[SITE + "/bloated"] < 0.03
    result = analyze_performance(snapshot(typical, bloated), deadline())
    finding = next(f for f in result["findings"] if f["provenance"]["rule_id"] == "markup-ratio")
    assert finding["affected_pages"] == [SITE + "/bloated"]
    assert finding["title"].startswith("Visible text is under 3% of the HTML")


# ---------------------------------------------------------------------------
# Google Maps place links
# ---------------------------------------------------------------------------

def test_google_maps_place_page_is_unverified_not_a_mismatch():
    from check_off_site_profiles import evaluate_profile
    url = "https://www.google.com/maps/place/Fixture+College/@42.36,-71.09,15z/data=!4m5"
    resp = Response(200, {"Content-Type": "text/html"},
                    b"<html><head><title>Google Maps</title></head><body>maps</body></html>", url)
    assert evaluate_profile(url, resp, "ok", "fixture.example", ["Fixture College"]) == (
        "unverified", "map_place_not_readable")


# ---------------------------------------------------------------------------
# email signup
# ---------------------------------------------------------------------------

def test_signup_form_is_a_warning_not_a_finding():
    from analyze_experience import analyze_experience
    signup = ('<form action="/newsletter/subscribe"><input type="email" name="email">'
              '<button>Subscribe</button></form>')
    p = page("<main><h1>Shop</h1>" + WORDS + "</main><footer>" + signup + "</footer>")
    result = analyze_experience(snapshot(p), deadline())
    assert "email-summary" not in rule_ids(result)
    assert result["warnings"] == ["An email signup form appears on 1/1 sampled page. A site audit cannot see the "
                                  "emails the site sends, so whether inbox assistants can summarize them was not "
                                  "checked."]
    contact = page('<main><h1>Contact</h1><form action="/contact/send"><input type="email" name="email">'
                   '<textarea name="message"></textarea><button>Send</button></form>' + WORDS + "</main>")
    assert analyze_experience(snapshot(contact), deadline())["warnings"] == []


# ---------------------------------------------------------------------------
# URLs that redirect to one page
# ---------------------------------------------------------------------------

def test_urls_redirecting_to_one_page_analyze_it_once():
    from archetype_sites import ALLOW_ALL, serve
    from run_audit import run_audit
    from test_precision_traps import _OFFLINE_ENV
    body = ("<!doctype html><html lang='en'><head><title>{t}</title></head><body><main><h1>{t}</h1>"
            + WORDS + "{links}</main></body></html>")
    links = '<a href="/br/">Brasil</a> <a href="/ach/">Acholi</a> <a href="/about/">About</a>'
    site = {"robots": ALLOW_ALL, "sitemap": None,
            "pages": {"/en/": body.format(t="Fixture home page", links=links),
                      "/about/": body.format(t="About the fixture", links='<a href="/en/">Home</a>')},
            # The start URL and two locale URLs all land on /en/.
            "responses": {"/": (302, "", "text/html", (("Location", "/en/"),)),
                          "/br/": (302, "", "text/html", (("Location", "/en/"),)),
                          "/ach/": (302, "", "text/html", (("Location", "/en/"),))}}
    saved = {k: os.environ.get(k) for k in _OFFLINE_ENV}
    os.environ.update(_OFFLINE_ENV)
    base, stop, seen = serve(site)
    try:
        report = run_audit(base + "/", limits=LIMITS, allow_private_targets=True)
    finally:
        stop()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    assert report["execution_status"] == "completed"
    # /en/ (reached three ways) and /about/: two pages, not four.
    assert report["coverage"]["pages_analyzed"] == 2
    assert {"/br/", "/ach/"} <= {path for _, path in seen}
    # The skipped copies were requested: the crawl is still complete, so orphan
    # and cluster checks still run.
    assert report["coverage"]["pages_never_attempted"] == 0
    titles = {c for f in report["findings"] for c in (f.get("check_ids") or [f["check_id"]])}
    assert "duplicate-titles" not in titles


# ---------------------------------------------------------------------------
# question heading over a table or list
# ---------------------------------------------------------------------------

def test_question_heading_over_a_table_is_not_judged_by_sentence_length():
    from analyze_answer_format import analyze_answer_format
    rows = "".join(f"<tr><td>Article</td><td>Author {n}</td><td>Topic {n} about open tools and research</td></tr>"
                   for n in range(12))
    table = page("<main><h1>Library</h1><h2>What is really going on with open tools?</h2>"
                 "<table><tr><th>Type</th><th>Author</th><th>Topic</th></tr>" + rows + "</table>" + WORDS
                 + "</main>", url=SITE + "/library")
    assert table.features["question_answers"][0]["starts_in"] == "table"
    assert "question-answer-indirect" not in rule_ids(analyze_answer_format(snapshot(table), deadline()))
    long_sentence = "<p>" + " ".join(_VOCAB[:60]) + ".</p>"
    prose = page("<main><h1>Guide</h1><h2>What is really going on with open tools?</h2>" + long_sentence + WORDS
                 + "</main>", url=SITE + "/guide")
    assert prose.features["question_answers"][0]["starts_in"] == "text"
    assert "question-answer-indirect" in rule_ids(analyze_answer_format(snapshot(prose), deadline()))


# ---------------------------------------------------------------------------
# duplicate titles
# ---------------------------------------------------------------------------

def test_query_variants_and_language_alternates_are_not_duplicate_titles():
    from analyze_experience import shared_title_pages
    plain = page("<main><h1>Search</h1>" + WORDS + "</main>", head="<title>Search</title>", url=SITE + "/search")
    query = page("<main><h1>Search</h1>" + WORDS + "</main>", head="<title>Search</title>",
                 url=SITE + "/search/?tab=directory")
    alts = ('<link rel="alternate" hreflang="en-CA" href="/en-CA/">'
            '<link rel="alternate" hreflang="en-GB" href="/en-GB/">')
    ca = page("<main><h1>Home</h1>" + WORDS + "</main>", head="<title>Fixture home</title>" + alts, url=SITE + "/en-CA/")
    gb = page("<main><h1>Home</h1>" + WORDS + "</main>", head="<title>Fixture home</title>" + alts, url=SITE + "/en-GB/")
    assert shared_title_pages([plain, query, ca, gb]) == []


def test_two_different_pages_with_one_title_are_still_reported():
    from analyze_experience import shared_title_pages
    a = page("<main><h1>A</h1>" + WORDS + "</main>", head="<title>Products</title>", url=SITE + "/bags")
    b = page("<main><h1>B</h1>" + WORDS + "</main>", head="<title>Products</title>", url=SITE + "/wallets")
    c = page("<main><h1>C</h1>" + WORDS + "</main>", head="<title>Other</title>", url=SITE + "/other")
    assert [p.url for p in shared_title_pages([a, b, c])] == [SITE + "/bags", SITE + "/wallets"]


# ---------------------------------------------------------------------------
# calibrated base confidences
# ---------------------------------------------------------------------------

def test_calibrated_confidences_are_catalogued_steps_and_used():
    from analyze_metadata import analyze_metadata
    from check_catalog import CALIBRATED_CONFIDENCE, CATALOG, calibrated_confidence
    for check_id, value in CALIBRATED_CONFIDENCE.items():
        assert check_id in CATALOG
        # --suggest steps: 0.5 to 0.9 in tenths, never more than measured.
        assert value in (0.5, 0.6, 0.7, 0.8, 0.9), (check_id, value)
    assert calibrated_confidence("not-a-calibrated-check", 0.42) == 0.42
    bare = page("<main><h1>Plain page heading</h1>" + WORDS + "</main>", head="<title>A plain fixture page</title>")
    found = {f["provenance"]["rule_id"]: f for f in analyze_metadata(snapshot(bare), deadline())["findings"]}
    assert found["missing-description"]["confidence"] == CALIBRATED_CONFIDENCE["missing-description"]
