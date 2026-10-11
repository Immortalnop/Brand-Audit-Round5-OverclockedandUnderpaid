"""Alt text quality, video and audio text alternatives, citation-oriented schema
(FAQPage, HowTo, Review, AggregateRating) and article authorship (E-E-A-T).

All checks here read the acquisition snapshot only, so every test builds pages
from HTML strings and never touches the network.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
            "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
            "skills/entity-corroboration-agent/scripts", "tests"):
    if str(ROOT / rel) not in sys.path:
        sys.path.insert(0, str(ROOT / rel))

from constants import Limits
from models import AuditArtifacts, freeze_value, make_deadline
from transport import Response
from acquire_site import _extract_page
from html_features import Document
from analyze_media_text import analyze_media_text, junk_alt_reason
from analyze_citation_schema import analyze_citation_schema, walk
from analyze_authorship import analyze_authorship, assess_page, is_article
from check_catalog import CATALOG, get_entry

LIMITS = Limits()
SITE = "https://fixture.example"


def page(body="", head="", url=SITE + "/", lang="en"):
    html = f'<html lang="{lang}"><head>{head}</head><body>{body}</body></html>'
    response = Response(200, {"Content-Type": "text/html"}, html.encode(), url)
    response.network_duration_ms = 50
    return _extract_page(url, response, 50, LIMITS)


def jsonld(data):
    return '<script type="application/ld+json">' + json.dumps(data) + "</script>"


def snapshot(*pages):
    coverage = {"urls_analyzed": len(pages), "urls_discovered": len(pages)}
    return AuditArtifacts(SITE + "/", SITE, tuple(pages), freeze_value({"status": "ok"}),
                          freeze_value({"present": False, "status": "absent"}), freeze_value({"status": "ok"}),
                          freeze_value({"coverage": coverage}), ())


def run(check, *pages):
    return check(snapshot(*pages), make_deadline(LIMITS))


def by_id(result, check_id):
    return [f for f in result["findings"] if f["check_id"] == check_id]


def parse(html):
    doc = Document()
    doc.feed(html)
    doc.close()
    return doc.features()


# ------------------------------------------------------------------ alt text

@pytest.mark.parametrize("alt,src,reason", [
    ("image1.jpg", "/img/image1.jpg", "a file name"),
    ("Team photo.PNG", "/x.png", "a file name"),
    ("Our team at the offsite.webp", "/x.webp", "a file name"),
    ("IMG_2041", "/x.jpg", "a camera or screenshot file name"),
    ("DSC0001", "/x.jpg", "a camera or screenshot file name"),
    ("Screenshot 2024-05-01", "/x.png", "a camera or screenshot file name"),
    ("hero-image-2", "/assets/hero-image-2.jpg", "a copy of the file name"),
    ("banner", "/x.jpg", "a placeholder word"),
    ("Image 3", "/x.jpg", "a placeholder word"),
    ("logo", "/x.svg", "a placeholder word"),
    ("  PHOTO  ", "/x.jpg", "a placeholder word"),
    ("123", "/x.jpg", "a code or number"),
    ("a3f9c2d1e4b5a6f7", "/x.jpg", "a code or number"),
    ("-", "/x.jpg", "a single character or punctuation"),
    ("x", "/x.jpg", "a single character or punctuation"),
    ("", "/x.jpg", None),
    ("   ", "/x.jpg", None),
    (None, "/x.jpg", None),
    ("Red bench vise clamped to an oak workbench", "/vise.jpg", None),
    ("Acme logo", "/logo.svg", None),
    ("Photo of the team at the 2023 offsite", "/team.jpg", None),
    ("team", "/assets/team.jpg", None),  # a plain word that is also the file name is not flagged
])
def test_junk_alt_reason(alt, src, reason):
    assert junk_alt_reason(alt, src) == reason


def test_alt_quality_reports_examples_and_ignores_decorative_missing_and_pixels():
    body = ('<img src="/a.jpg" alt="image1.jpg"><img src="/b.jpg" alt="banner">'
            '<img src="/c.jpg" alt=""><img src="/d.jpg">'
            '<img src="/e.jpg" alt="Bench vise on an oak workbench">'
            '<img src="/pixel.gif" alt="pixel" width="1" height="1">'
            '<img src="/f.jpg" alt="spacer" role="presentation">')
    result = run(analyze_media_text, page(body))
    (finding,) = by_id(result, "alt-text-quality")
    assert finding["status"] == "confirmed" and finding["severity"] == "low"
    assert 'alt="image1.jpg" (a file name)' in finding["evidence_text"]
    assert 'alt="banner" (a placeholder word)' in finding["evidence_text"]
    assert "pixel" not in finding["evidence_text"] and "spacer" not in finding["evidence_text"]
    assert result["metrics"]["images_with_uninformative_alt"] == 2


def test_alt_quality_flags_one_alt_repeated_on_many_images_and_escalates():
    body = "".join(f'<img src="/p{i}.jpg" alt="Acme product">' for i in range(5))
    body += "".join(f'<img src="/q{i}.jpg" alt="image{i}.png">' for i in range(4))
    (finding,) = by_id(run(analyze_media_text, page(body)), "alt-text-quality")
    assert "the same alt text on 5 different images" in finding["evidence_text"]
    assert finding["severity"] == "medium"


def test_alt_quality_quiet_on_good_alt_text():
    body = ('<img src="/a.jpg" alt="Two engineers testing a heater">'
            '<img src="/b.jpg" alt=""><img src="/c.jpg" alt="Workshop floor plan">')
    assert by_id(run(analyze_media_text, page(body)), "alt-text-quality") == []


# ------------------------------------------------------------- video, audio

def test_document_records_players_sources_and_tracks():
    features = parse('<video controls><source src="/v.mp4"><track kind="captions" src="/c.vtt">'
                     '<track src="/s.vtt"></video><audio src="/a.mp3"></audio>'
                     '<iframe src="https://player.vimeo.com/video/1" width="640" height="360"></iframe>'
                     '<iframe src="https://www.google.com/maps/embed?pb=1"></iframe>')
    video, audio, vimeo, maps = features["media_records"]
    assert video["src"] == "/v.mp4" and video["tracks"] == ["captions", "subtitles"]
    assert audio["tag"] == "audio" and audio["src"] == "/a.mp3"
    assert vimeo["sized"] is True and maps["sized"] is False
    assert features["embeds_missing_dims"] == 2  # the unsized video and the map iframe


def test_video_without_transcript_or_schema_is_reported():
    body = ('<h1>Tour</h1><iframe src="https://www.youtube.com/embed/x1"></iframe>'
            '<video src="/tour.mp4" width="640" height="360"></video>')
    result = run(analyze_media_text, page(body))
    (transcript,) = by_id(result, "media-transcript-missing")
    assert "YouTube embed: captions inside the player not checked" in transcript["evidence_text"]
    assert "native video player: no captions track" in transcript["evidence_text"]
    (schema,) = by_id(result, "media-schema-missing")
    assert "video with no VideoObject markup" in schema["evidence_text"]
    assert result["metrics"]["videos_observed"] == 2


@pytest.mark.parametrize("body", [
    '<iframe src="https://www.youtube.com/embed/x"></iframe><a href="/tour-transcript">Read the transcript</a>',
    '<iframe src="https://www.youtube.com/embed/x"></iframe><h2>Transcript</h2><p>Welcome to the tour.</p>',
    '<iframe src="https://www.youtube.com/embed/x?cc_load_policy=1"></iframe>',
    '<video src="/v.mp4"><track kind="subtitles" src="/s.vtt"></video>',
])
def test_transcript_or_captions_satisfy_the_transcript_check(body):
    assert by_id(run(analyze_media_text, page(body)), "media-transcript-missing") == []


def test_videoobject_transcript_property_counts_and_required_fields_are_checked():
    complete = jsonld({"@type": "VideoObject", "name": "Tour", "thumbnailUrl": "https://x/t.jpg",
                       "uploadDate": "2024-01-01", "transcript": "Welcome to the tour."})
    result = run(analyze_media_text, page('<iframe src="https://www.youtube.com/embed/x"></iframe>', complete))
    assert result["findings"] == []
    partial = jsonld({"@type": "VideoObject", "name": "Tour"})
    (schema,) = by_id(run(analyze_media_text, page('<video src="/v.mp4"></video>', partial)), "media-schema-missing")
    assert "VideoObject without thumbnailUrl, uploadDate" in schema["evidence_text"]


def test_audio_needs_spoken_audio_and_audio_markup():
    music = '<iframe src="https://open.spotify.com/embed/track/abc"></iframe>'
    assert run(analyze_media_text, page(music))["metrics"]["pages_with_video_or_audio"] == 0
    episode = '<iframe src="https://open.spotify.com/embed/episode/abc"></iframe>'
    (schema,) = by_id(run(analyze_media_text, page(episode)), "media-schema-missing")
    assert "audio with no AudioObject or PodcastEpisode markup" in schema["evidence_text"]
    marked = jsonld({"@type": "PodcastEpisode", "name": "Ep 1", "transcript": "Hello."})
    assert run(analyze_media_text, page(episode, marked))["findings"] == []


def test_non_media_iframes_are_ignored():
    body = '<iframe src="https://www.google.com/maps/embed?pb=1"></iframe><iframe src="/form"></iframe>'
    result = run(analyze_media_text, page(body))
    assert result["findings"] == [] and result["metrics"]["pages_with_video_or_audio"] == 0


# --------------------------------------------------------- citation schema

def faq(questions):
    return jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": questions})


def question(name, answer="An answer."):
    q = {"@type": "Question", "name": name}
    if answer is not None:
        q["acceptedAnswer"] = {"@type": "Answer", "text": answer}
    return q


def test_valid_visible_faq_passes():
    head = faq([question("Do you ship abroad?"), question("Can I return a tool?")])
    body = "<h2>Do you ship abroad?</h2><p>Yes.</p><h2>Can I return a tool?</h2><p>Yes.</p>"
    result = run(analyze_citation_schema, page(body, head))
    assert result["findings"] == []
    assert result["metrics"]["citation_schema_types_present"] == {"FAQPage": 1}


@pytest.mark.parametrize("head,body,text", [
    (faq([]), "", "FAQPage has no Question in mainEntity"),
    (faq([question("Do you ship?", None)]), "<p>Do you ship?</p>", "1 of 1 FAQ question(s) lack"),
    (faq([question("Is it hidden?"), question("Is this too?")]), "<p>Nothing here</p>",
     "only 0 of 2 FAQ questions in the markup appear"),
    (jsonld({"@type": "HowTo", "name": "Sharpen"}), "", "HowTo has no step"),
    (jsonld({"@type": "HowTo", "name": "Sharpen", "step": [{"@type": "HowToStep"}, "Hone it"]}), "",
     "1 of 2 HowTo step(s) have no text"),
    (jsonld({"@type": "Review", "author": "Ann"}), "", "Review has no numeric reviewRating.ratingValue"),
    (jsonld({"@type": "Review", "reviewRating": {"ratingValue": 4}, "itemReviewed": {"@type": "Product"}}), "",
     "Review has no author name"),
    (jsonld({"@type": "Review", "reviewRating": {"ratingValue": 4}, "author": "Ann"}), "",
     "Review is not attached to an item"),
    (jsonld({"@type": "Product", "name": "Vise", "review": {"@type": "Review", "author": "Ann",
                                                             "reviewRating": {"ratingValue": 9}}}), "",
     "Review rating 9 is outside its scale 1 to 5"),
    (jsonld({"@type": "Product", "name": "Vise", "aggregateRating": {"@type": "AggregateRating",
                                                                     "ratingValue": "4.5"}}), "",
     "AggregateRating has no ratingCount or reviewCount"),
    (jsonld({"@type": "Product", "name": "Vise", "aggregateRating": {"@type": "AggregateRating",
                                                                     "ratingValue": 4, "ratingCount": 0}}), "",
     "AggregateRating declares zero ratings"),
    (jsonld({"@type": "Product", "name": "Vise", "aggregateRating": {
        "@type": "AggregateRating", "ratingValue": 8, "bestRating": 10, "worstRating": 9, "reviewCount": 3}}), "",
     "AggregateRating 8 is outside its scale 9 to 10"),
    (jsonld({"@type": "AggregateRating", "ratingValue": 4, "ratingCount": 3}), "",
     "AggregateRating is not attached to an item"),
])
def test_invalid_citation_schema(head, body, text):
    (finding,) = by_id(run(analyze_citation_schema, page(body, head)), "citation-schema-invalid")
    assert finding["finding_type"] == "defect" and finding["severity"] == "medium"
    assert text in finding["evidence_text"]


def test_valid_nested_ratings_and_number_formats_pass():
    head = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "Product", "name": "Vise",
         "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4,5", "reviewCount": "1,234"},
         "review": [{"@type": "Review", "author": {"@type": "Person", "name": "Ann"},
                     "reviewRating": {"@type": "Rating", "ratingValue": "5"}}]},
        {"@type": "Review", "author": "Bo", "reviewRating": {"ratingValue": 4},
         "itemReviewed": {"@type": "Product", "name": "Vise"}}]})
    result = run(analyze_citation_schema, page("<p>Vise</p>", head))
    assert result["findings"] == []


def test_rating_referenced_by_id_counts_as_attached():
    head = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "Product", "name": "Vise", "aggregateRating": {"@id": "#rating"}},
        {"@type": "AggregateRating", "@id": "#rating", "ratingValue": 4.6, "reviewCount": 12}]})
    assert run(analyze_citation_schema, page("<p>Vise</p>", head))["findings"] == []


def test_walk_reports_parent_property():
    data = {"@graph": [{"@type": "Product", "review": {"@type": "Review"}}, {"@type": "Review"}]}
    pairs = [(sorted(n["@type"] if isinstance(n["@type"], list) else [n["@type"]]), key) for n, key in walk(data)]
    assert pairs == [(["Product"], "@graph"), (["Review"], "review"), (["Review"], "@graph")]


def test_citation_schema_opportunities():
    faq_page = page("<h2>What is it?</h2><p>A vise.</p><h2>How big is it?</h2><p>Small.</p>"
                    "<h3>Who makes it?</h3><p>Us.</p>", url=SITE + "/questions")
    how_to = page("<h1>How to sharpen a chisel</h1><ol><li>Flatten</li><li>Hone</li><li>Strop</li></ol>",
                  head="<title>How to sharpen a chisel</title>", url=SITE + "/guides/sharpen")
    rated = page("<h1>Vise</h1><p>Rated 4.7 out of 5 from 312 reviews.</p>", url=SITE + "/product/vise")
    (finding,) = by_id(run(analyze_citation_schema, faq_page, how_to, rated), "citation-schema-opportunity")
    assert finding["status"] == "suspected" and finding["severity"] == "low"
    text = finding["evidence_text"]
    assert "3 question-shaped H2/H3 headings with no FAQPage markup" in text
    assert "a 'How to' page with numbered steps and no HowTo markup" in text
    assert "visible rating text ('4.7 out of 5')" in text


def test_microdata_and_short_lists_do_not_count_as_opportunities():
    microdata = page('<div itemscope itemtype="https://schema.org/FAQPage"><h2>What?</h2><h2>Why?</h2>'
                     '<h2>How?</h2></div>')
    short_list = page("<h1>How to start</h1><ol><li>One</li><li>Two</li></ol>", url=SITE + "/start")
    blog_rating = page("<p>Rated 4 out of 5 by critics.</p>", url=SITE + "/blog/review")
    assert run(analyze_citation_schema, microdata, short_list, blog_rating)["findings"] == []


def test_document_counts_ordered_lists_with_unclosed_items():
    features = parse("<ol><li>a<li>b<li>c<li>d</ol><ol><li>x</li></ol><ul><li>1<li>2<li>3</ul>")
    assert features["ordered_lists"] == 1 and features["max_ordered_list_items"] == 4


# ---------------------------------------------------------------- authorship

LONG = "<p>" + "Workshop tools are tested on real benches before they ship. " * 40 + "</p>"


def article(author=None, body=LONG, extra=None, url=SITE + "/blog/post", head=""):
    data = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": "Post"}
    if author is not None:
        data["author"] = author
    blocks = [data] + list(extra or [])
    return page(body, jsonld({"@context": "https://schema.org", "@graph": blocks}) + head, url=url)


def test_is_article_rules():
    assert is_article(article())
    assert is_article(page(LONG, url=SITE + "/blog/my-post"))
    assert not is_article(page(LONG, url=SITE + "/blog"))  # section index
    assert not is_article(page("<p>Short.</p>", url=SITE + "/blog/short"))
    assert not is_article(page(LONG, url=SITE + "/about"))


def test_article_without_any_author_is_reported():
    result = run(analyze_authorship, article())
    (finding,) = by_id(result, "author-missing")
    assert finding["severity"] == "medium" and finding["finding_type"] == "proactive_improvement"
    assert result["metrics"]["articles_without_author"] == 1


def test_complete_person_author_passes():
    author = {"@type": "Person", "name": "Jane Doe", "url": SITE + "/authors/jane",
              "jobTitle": "Senior tool engineer"}
    body = '<p class="byline">By <a rel="author" href="/authors/jane">Jane Doe</a></p>' + LONG
    assert run(analyze_authorship, article(author, body))["findings"] == []


@pytest.mark.parametrize("author,body,text", [
    ("Jane Doe", "<p>By Jane Doe</p>" + LONG, "the Article author is a plain name string, not a Person"),
    ({"@type": "Organization", "name": "Acme"}, "<p>Acme team</p>" + LONG, "an Organization, not a Person"),
    ({"@type": "Person", "name": "Jane Doe"}, "<p>By Jane Doe</p>" + LONG,
     "author Jane Doe has no profile link (url or sameAs) and no author page is linked"),
    ({"@type": "Person", "name": "Jane Doe", "url": SITE + "/a/jane"}, "<p>By Jane Doe</p>" + LONG,
     "author Jane Doe has no credentials in markup"),
    ({"@type": "Person", "name": "Ghost Writer", "url": SITE + "/a/g", "jobTitle": "Editor"}, LONG,
     "the markup author (Ghost Writer) is not named anywhere on the page"),
    (None, '<div class="post-author">Jane Doe</div>' + LONG,
     "the byline is not stated in Article markup (no author property)"),
])
def test_weak_author_signals(author, body, text):
    (finding,) = by_id(run(analyze_authorship, article(author, body)), "author-credentials-weak")
    assert finding["severity"] == "low"
    assert text in finding["evidence_text"]


def test_author_reference_by_id_is_resolved():
    person = {"@type": "Person", "@id": "#jane", "name": "Jane Doe", "sameAs": ["https://github.com/jane"],
              "knowsAbout": "Metalworking"}
    result = run(analyze_authorship, article({"@id": "#jane"}, "<p>By Jane Doe</p>" + LONG, extra=[person]))
    assert result["findings"] == []
    # A reference that also repeats the name (the Yoast pattern) resolves the same way.
    result = run(analyze_authorship, article({"@id": "#jane", "name": "Jane Doe"}, "<p>By Jane Doe</p>" + LONG,
                                             extra=[person]))
    assert result["findings"] == []
    # An unresolvable untyped reference is still reported.
    (finding,) = by_id(run(analyze_authorship, article({"@id": "#nobody", "name": "Jane Doe"},
                                                       "<p>By Jane Doe</p>" + LONG)), "author-credentials-weak")
    assert "an untyped object, not a Person" in finding["evidence_text"]


def test_document_captures_bylines_author_links_and_meta_author():
    features = parse('<head><meta name="author" content="Jane Doe"><link rel="author" href="/humans.txt"></head>'
                     '<body><span class="author-name">Jane Doe</span><div class="authorization">no</div>'
                     '<span itemprop="author">Jo Bloggs</span></body>')
    assert features["bylines"] == ["Jane Doe", "Jo Bloggs"]
    assert features["author_links"] == ["/humans.txt"]
    assert features["meta"]["author"] == ["Jane Doe"]
    _, problems = assess_page(page('<span class="author-name">Jane Doe</span>' + LONG, url=SITE + "/blog/x"))
    assert problems == ["the byline is not stated in Article markup (no author property)"]


def test_new_catalog_entries_are_complete():
    for check_id in ("alt-text-quality", "media-transcript-missing", "media-schema-missing",
                     "citation-schema-invalid", "citation-schema-opportunity", "author-missing",
                     "author-credentials-weak"):
        assert check_id in CATALOG and get_entry(check_id)
