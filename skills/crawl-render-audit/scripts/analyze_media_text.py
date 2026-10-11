"""analyze_media_text.py -- text alternatives for images, video and audio.

Crawlers and assistants read text. An image is understood through its alt text,
and spoken content in a video or podcast through a transcript, captions and
VideoObject or AudioObject markup. This check reads the acquisition snapshot only
(no requests) and reports three things:

  - alt-text-quality: alt text that is present but says nothing, such as a file
    name (alt="image1.jpg"), a placeholder word (alt="banner", alt="photo") or a
    camera file name (alt="IMG_2041"). An empty alt="" marks a decorative image
    and is correct, so it is never counted; a missing alt attribute is the
    separate missing-alt check.
  - media-transcript-missing: a page plays video or audio but neither its text
    nor its links offer a transcript, and native players carry no captions track.
  - media-schema-missing: a page plays video or audio without VideoObject or
    AudioObject markup, or with VideoObject markup missing the properties search
    engines require (name, thumbnailUrl, uploadDate).

Embedded players (YouTube, Vimeo and similar) may provide captions inside the
player; that cannot be seen from the page HTML, so it is reported as not checked
rather than missing.
"""
import re
from collections.abc import Mapping
from urllib.parse import urlsplit, parse_qs

from check_helpers import eligible_pages
from models import make_finding, skill_result
from platforms import audio_platform, video_platform
from structured_data import iter_nodes, types_of

_IMAGE_EXT = r"(?:jpe?g|png|gif|webp|svg|avif|bmp|tiff?|ico|heic)"
_FILE_NAME = re.compile(r"[\w\-. ()]+\." + _IMAGE_EXT, re.I)
_CAMERA_NAME = re.compile(r"(?:img|dsc|dscn|dscf|dcim|pxl|mvimg|gopr|screenshot|screen shot|photo|image)"
                          r"[\s_-]?\d{2,}[\w-]*", re.I)
_NUMBERED_PLACEHOLDER = re.compile(r"(?:image|img|photo|picture|pic|banner|slide|graphic|icon|figure|"
                                   r"thumbnail|thumb|untitled|placeholder|hero|header|item|product)"
                                   r"[\s_-]*\d{0,4}", re.I)
_PLACEHOLDER_WORDS = frozenset({
    "image", "img", "photo", "photograph", "picture", "pic", "graphic", "banner", "icon", "logo",
    "thumbnail", "thumb", "hero", "header", "background", "bg", "placeholder", "untitled", "spacer",
    "alt", "alt text", "alt tag", "image description", "default", "null", "undefined", "none", "n/a",
    "na", "todo", "tbd", "test", "blank", "screenshot", "slide", "slider", "carousel", "gallery",
    "figure", "illustration", "avatar", "profile", "product", "product image", "featured image",
    "hero image", "banner image", "main image", "header image", "stock photo", "image placeholder",
    "click here", "more", "read more", "learn more", "image alt", "alt image",
})
_TRANSCRIPT = re.compile(r"\btranscri(?:pt|ption|pci[o\u00f3]n)|\btranskript", re.I)
_VIDEO_SCHEMA = frozenset({"VideoObject", "Clip", "Movie", "Episode", "TVEpisode"})
_AUDIO_SCHEMA = frozenset({"AudioObject", "PodcastEpisode", "PodcastSeries", "RadioEpisode", "MusicRecording"})
_VIDEO_REQUIRED = ("name", "thumbnailUrl", "uploadDate")
_TINY_PX = 2


def _int(value):
    return int(value) if isinstance(value, str) and re.fullmatch(r"[0-9]{1,6}", value.strip()) else None


def _stem(src):
    try:
        name = urlsplit(src).path.rsplit("/", 1)[-1]
    except ValueError:
        return ""
    return name.rsplit(".", 1)[0] if "." in name else name


def junk_alt_reason(alt, src=""):
    """Why an alt text says nothing about its image, or None when it is usable.
    Empty alt (decorative image) and missing alt are not judged here."""
    if not isinstance(alt, str):
        return None
    text = " ".join(alt.split())
    if not text:
        return None
    lowered = text.lower()
    if _FILE_NAME.fullmatch(text) or re.search(r"\." + _IMAGE_EXT + r"$", lowered):
        return "a file name"
    if _CAMERA_NAME.fullmatch(text):
        return "a camera or screenshot file name"
    stem = _stem(src)
    if stem and text == stem and re.search(r"[-_0-9]", stem):
        return "a copy of the file name"
    if lowered in _PLACEHOLDER_WORDS or _NUMBERED_PLACEHOLDER.fullmatch(text):
        return "a placeholder word"
    if len(text) == 1 or re.fullmatch(r"[\W_]+", text):
        return "a single character or punctuation"
    if re.fullmatch(r"[0-9a-f]{12,}", lowered) or re.fullmatch(r"[\d\s_-]+", text):
        return "a code or number"
    return None


def _examples(issues, count=3):
    """Up to count issues, one per distinct reason first, so the evidence shows
    the variety of problems rather than three of the same kind."""
    seen, first, rest = set(), [], []
    for issue in issues:
        (rest if issue[2] in seen else first).append(issue)
        seen.add(issue[2])
    return (first + rest)[:count]


def _alt_issues(page):
    """[(src, alt, reason)] for images on the page whose alt text says nothing."""
    issues, by_alt = [], {}
    records = [r for r in (page.features or {}).get("image_records", ())
               if (r.get("role") or "") not in ("presentation", "none")]
    for record in records:
        width, height = _int(record.get("width")), _int(record.get("height"))
        if (width is not None and width <= _TINY_PX) or (height is not None and height <= _TINY_PX):
            continue  # tracking pixel
        alt = record.get("alt")
        reason = junk_alt_reason(alt, record.get("src", ""))
        if reason:
            issues.append((record["src"], alt, reason))
        elif isinstance(alt, str) and alt.strip():
            by_alt.setdefault(" ".join(alt.split()).lower(), set()).add(record["src"])
    # The same short alt text on four or more different images is a template label
    # ("Acme product", "thumbnail") that describes none of them. A descriptive alt
    # of four or more words repeated across a product gallery (every view shows the
    # same item) is not reported.
    for alt, srcs in by_alt.items():
        if len(srcs) >= 4 and len(alt.split()) < 4:
            for src in sorted(srcs)[:4]:
                issues.append((src, alt, f"the same alt text on {len(srcs)} different images"))
    described = sum(1 for r in records if isinstance(r.get("alt"), str) and r["alt"].strip())
    return issues, described


def _media_items(page):
    """Video and audio on the page: (kind, label, record)."""
    items = []
    for record in (page.features or {}).get("media_records", ()):
        tag, src = record.get("tag"), record.get("src") or ""
        if tag == "video":
            items.append(("video", "native video player", record))
        elif tag == "audio":
            items.append(("audio", "native audio player", record))
        elif src:
            platform = video_platform(src)
            if platform:
                items.append(("video", f"{platform} embed", record))
                continue
            platform = audio_platform(src)
            # A Spotify embed is spoken audio only when it is a podcast episode or show.
            if platform and (platform != "Spotify" or re.search(r"/(?:episode|show)/", src)):
                items.append(("audio", f"{platform} embed", record))
    return items


def _schema_nodes(page, names):
    return [n for n in iter_nodes(page.jsonld_blocks) if isinstance(n, Mapping) and types_of(n) & names]


def _has_value(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_has_value(v) for k, v in value.items() if not str(k).startswith("@"))
    if isinstance(value, (list, tuple)):
        return any(_has_value(v) for v in value)
    return value is not None


def _captions_state(record):
    if record.get("tag") in ("video", "audio"):
        tracks = record.get("tracks") or ()
        return "captions track present" if any(t in ("captions", "subtitles") for t in tracks) else "no captions track"
    src = record.get("src") or ""
    try:
        query = parse_qs(urlsplit(src).query)
    except ValueError:
        query = {}
    if query.get("cc_load_policy") == ["1"]:
        return "captions switched on in the embed URL"
    return "captions inside the player not checked"


def _transcript_on_page(page, video_nodes, audio_nodes):
    if _TRANSCRIPT.search(page.visible_text or ""):
        return True
    for href, text in (page.features or {}).get("anchors", ()):
        if _TRANSCRIPT.search(href or "") or _TRANSCRIPT.search(text or ""):
            return True
    return any(_has_value(n.get("transcript")) for n in list(video_nodes) + list(audio_nodes))


def _action(summary, steps, priority, benefit):
    return {"summary": summary, "steps": steps, "priority": priority, "effort": "low",
            "expected_benefit": benefit,
            "verification": "Re-run the audit and confirm the affected pages are no longer listed"}


def analyze_media_text(artifacts, deadline):
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Media text-alternative checks skipped: deadline reached."])
    pages = eligible_pages(artifacts)
    findings = []

    # --- alt text quality -------------------------------------------------
    alt_pages, total_issues, total_described = [], 0, 0
    for page in pages:
        issues, described = _alt_issues(page)
        total_described += described
        if issues:
            alt_pages.append((page, issues, described))
            total_issues += len(issues)
    if alt_pages:
        share = total_issues / max(1, total_described + total_issues)
        severity = "medium" if total_issues >= 5 and share >= 0.3 else "low"
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity=severity,
            status="confirmed", confidence=0.85,
            title="Image alt text is a file name, placeholder or repeated label that describes nothing",
            root_cause="Alt text such as a file name or a word like 'banner' gives crawlers, assistants "
                       "and screen readers no description of the image",
            affected_pages=[p.url for p, _, _ in alt_pages],
            evidence=[{"type": "image_alt",
                       "description": f"{len(issues)} image(s) with uninformative alt text, for example "
                                      + "; ".join(f"alt=\"{alt[:60]}\" ({reason}) on {src[:120]}"
                                                  for src, alt, reason in _examples(issues)),
                       "urls": [page.url]}
                      for page, issues, _ in alt_pages[:10]],
            suggested_action=_action(
                "Replace placeholder alt text with a short description of each image",
                ["Write alt text that says what each informative image shows, in a short phrase",
                 "Use an empty alt=\"\" for purely decorative images instead of a placeholder word",
                 "Fix the CMS or template default that fills alt text with the file name"],
                severity, "Crawlers, assistants and screen readers can tell what each image shows"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_media_text.py",
                        "rule_id": "alt-text-quality"},
        ))

    # --- video and audio ---------------------------------------------------
    no_transcript, schema_gaps = [], []
    media_pages = video_count = audio_count = 0
    for page in pages:
        items = _media_items(page)
        if not items:
            continue
        media_pages += 1
        video_count += sum(1 for kind, _, _ in items if kind == "video")
        audio_count += sum(1 for kind, _, _ in items if kind == "audio")
        video_nodes = _schema_nodes(page, _VIDEO_SCHEMA)
        audio_nodes = _schema_nodes(page, _AUDIO_SCHEMA)
        microdata = set((page.features or {}).get("microdata_types", ()))
        transcript = _transcript_on_page(page, video_nodes, audio_nodes)
        states = [(label, _captions_state(record)) for _, label, record in items]
        captioned = all(state in ("captions track present", "captions switched on in the embed URL")
                        for _, state in states)
        if not transcript and not captioned:
            no_transcript.append((page, states))
        problems = []
        kinds = {kind for kind, _, _ in items}
        if "video" in kinds:
            if not video_nodes and not microdata & _VIDEO_SCHEMA:
                problems.append("video with no VideoObject markup")
            else:
                for node in video_nodes[:3]:
                    missing = [k for k in _VIDEO_REQUIRED if not _has_value(node.get(k))]
                    if missing:
                        problems.append("VideoObject without " + ", ".join(missing))
        if "audio" in kinds and not audio_nodes and not microdata & _AUDIO_SCHEMA:
            problems.append("audio with no AudioObject or PodcastEpisode markup")
        if problems:
            schema_gaps.append((page, problems))

    if no_transcript:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.75,
            title="Video or audio has no transcript that crawlers can read",
            root_cause="Crawlers and assistants do not watch or listen, so what is said in a video or "
                       "podcast is invisible to them unless a transcript is on or linked from the page",
            affected_pages=[p.url for p, _ in no_transcript],
            evidence=[{"type": "media",
                       "description": "No transcript in the page text or links; "
                                      + "; ".join(f"{label}: {state}" for label, state in states[:4]),
                       "urls": [page.url]}
                      for page, states in no_transcript[:10]],
            suggested_action=_action(
                "Publish a transcript with each video and audio clip",
                ["Add the full transcript as text on the page, or link to it from next to the player",
                 "Add a captions track (WebVTT) to native video players and enable captions on embeds",
                 "Include the transcript in the VideoObject or AudioObject transcript property"],
                "low", "What the video or audio says becomes quotable text"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_media_text.py",
                        "rule_id": "media-transcript-missing"},
        ))

    if schema_gaps:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="confirmed", confidence=0.8,
            title="Video or audio is embedded without complete VideoObject or AudioObject markup",
            root_cause="Without VideoObject or AudioObject markup, search engines and assistants have no "
                       "machine-readable title, description, thumbnail or date for the media",
            affected_pages=[p.url for p, _ in schema_gaps],
            evidence=[{"type": "structured_data", "description": "; ".join(problems[:4]), "urls": [page.url]}
                      for page, problems in schema_gaps[:10]],
            suggested_action=_action(
                "Describe each video and audio clip with VideoObject or AudioObject JSON-LD",
                ["Add VideoObject markup with name, description, thumbnailUrl, uploadDate and duration",
                 "Use AudioObject or PodcastEpisode markup for audio",
                 "Add the transcript property where a transcript exists"],
                "low", "Media becomes eligible for video results and its details are quotable"),
            provenance={"skill": "crawl-render-audit", "script": "analyze_media_text.py",
                        "rule_id": "media-schema-missing"},
        ))

    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"media_text_pages_analyzed": len(pages), "images_with_uninformative_alt": total_issues,
                 "images_with_alt_text": total_described, "pages_with_video_or_audio": media_pages,
                 "videos_observed": video_count, "audio_players_observed": audio_count,
                 "media_pages_without_transcript": len(no_transcript),
                 "media_pages_with_schema_gaps": len(schema_gaps),
                 "embedded_player_captions_checked": False},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0},
    )
