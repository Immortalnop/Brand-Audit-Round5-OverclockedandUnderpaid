"""Registries of third-party platforms the audit recognizes in links and embeds.

These name platform hosts (video players, podcast players, review sites, business
directories), never an audited brand or site, so no check keys off a specific
target. Matching is by host suffix: "player.vimeo.com" matches "vimeo.com".
"""
import re
from urllib.parse import urlsplit

# Embedded video players. A recognized host makes an iframe a video, not a map or
# a form, so it is held to the video checks.
VIDEO_HOSTS = {
    "youtube.com": "YouTube", "youtube-nocookie.com": "YouTube", "youtu.be": "YouTube",
    "vimeo.com": "Vimeo", "wistia.com": "Wistia", "wistia.net": "Wistia", "loom.com": "Loom",
    "vidyard.com": "Vidyard", "brightcove.net": "Brightcove", "dailymotion.com": "Dailymotion",
    "jwplayer.com": "JW Player", "jwplatform.com": "JW Player", "twitch.tv": "Twitch",
    "ted.com": "TED", "streamable.com": "Streamable",
}

# Embedded podcast and spoken-audio players. Music-first hosts are left out: a
# song needs no transcript.
AUDIO_HOSTS = {
    "spotify.com": "Spotify", "podcasts.apple.com": "Apple Podcasts",
    "anchor.fm": "Anchor", "buzzsprout.com": "Buzzsprout", "simplecast.com": "Simplecast",
    "libsyn.com": "Libsyn", "podbean.com": "Podbean", "transistor.fm": "Transistor",
    "megaphone.fm": "Megaphone", "captivate.fm": "Captivate", "spreaker.com": "Spreaker",
}

# Review and directory platforms. "kind" groups them for the advice text:
#   reviews   - general customer review sites
#   software  - software review and launch sites
#   local     - maps and local business listings
#   directory - company directories and employer profiles
REVIEW_PLATFORMS = {
    "trustpilot.com": ("Trustpilot", "reviews"), "sitejabber.com": ("Sitejabber", "reviews"),
    "bbb.org": ("Better Business Bureau", "reviews"), "reviews.io": ("REVIEWS.io", "reviews"),
    "feefo.com": ("Feefo", "reviews"), "consumeraffairs.com": ("ConsumerAffairs", "reviews"),
    "g2.com": ("G2", "software"), "capterra.com": ("Capterra", "software"),
    "getapp.com": ("GetApp", "software"), "softwareadvice.com": ("Software Advice", "software"),
    "trustradius.com": ("TrustRadius", "software"), "producthunt.com": ("Product Hunt", "software"),
    "yelp.com": ("Yelp", "local"), "tripadvisor.com": ("Tripadvisor", "local"),
    "tripadvisor.co.uk": ("Tripadvisor", "local"), "maps.apple.com": ("Apple Maps", "local"),
    "foursquare.com": ("Foursquare", "local"), "opentable.com": ("OpenTable", "local"),
    "yell.com": ("Yell", "local"), "angi.com": ("Angi", "local"), "houzz.com": ("Houzz", "local"),
    "thumbtack.com": ("Thumbtack", "local"), "zocdoc.com": ("Zocdoc", "local"),
    "healthgrades.com": ("Healthgrades", "local"),
    "clutch.co": ("Clutch", "directory"), "crunchbase.com": ("Crunchbase", "directory"),
    "glassdoor.com": ("Glassdoor", "directory"), "indeed.com": ("Indeed", "directory"),
}

# Consent-management platforms, recognized by the hosts their banner scripts load
# from. A match identifies a dialog or banner as a cookie-consent prompt.
CONSENT_HOSTS = (
    "cookielaw.org", "onetrust.com", "cookiebot.com", "privacy-center.org", "consensu.org",
    "cmp.quantcast.com", "trustarc.com", "usercentrics.eu", "osano.com", "termly.io",
    "cookieyes.com", "iubenda.com", "didomi.io", "cookie-script.com", "cookiefirst.com",
    "consentmanager.net", "cookiehub.net", "cookiepro.com",
)


def is_consent_host(host):
    host = (host or "").lower()
    return any(host == domain or host.endswith("." + domain) for domain in CONSENT_HOSTS)


# Google Business Profile has no single host: it is reached through Maps place
# links, short links, the business dashboard and review links.
_GOOGLE_HOST = re.compile(r"(?:^|\.)google\.(?:com|[a-z]{2,3}|co\.[a-z]{2}|com\.[a-z]{2})$")
_GOOGLE_PROFILE_HOSTS = ("g.page", "business.google.com", "maps.app.goo.gl")


def host_of(url):
    """Lower-case host without a leading 'www.', or '' for an unparseable URL."""
    try:
        host = (urlsplit(url.strip()).hostname or "").lower()
    except (ValueError, AttributeError):
        return ""
    return host[4:] if host.startswith("www.") else host


def _match(host, registry):
    for domain, value in registry.items():
        if host == domain or host.endswith("." + domain):
            return value
    return None


def video_platform(url):
    return _match(host_of(url), VIDEO_HOSTS)


def audio_platform(url):
    return _match(host_of(url), AUDIO_HOSTS)


def review_platform(url):
    """(name, kind) for a review or directory profile link, else None."""
    host = host_of(url)
    if not host:
        return None
    if host in _GOOGLE_PROFILE_HOSTS:
        return ("Google Business Profile", "local")
    try:
        path = urlsplit(url.strip()).path.lower()
    except ValueError:
        return None
    if host == "goo.gl" and path.startswith("/maps"):
        return ("Google Business Profile", "local")
    if _GOOGLE_HOST.search(host) and (host.startswith("maps.") or path.startswith(("/maps", "/local"))):
        return ("Google Business Profile", "local")
    if host == "search.google.com" and path.startswith("/local"):
        return ("Google Business Profile", "local")
    return _match(host, REVIEW_PLATFORMS)
