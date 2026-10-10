"""Standard-library helpers for facts carried by non-text media (images, PDFs).

Network-free. Acquisition uses these helpers to decide which images are worth a
bounded fetch and to read what was fetched; analysis uses them to compare facts
found in media with facts present in readable HTML text. Nothing here guesses at
pixels: raster images are measured from their headers only, and reading the text
drawn inside a raster image is left to the optional agent vision stage (AG-04).
"""
import re
import struct
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET

# Fact shapes compared between media and HTML text. Prices and units require a
# currency symbol or a unit so that bare numbers never count as facts.
PRICE_RE = re.compile(r"(?:[$\u20ac\u00a3\u20b9]|\b(?:USD|EUR|GBP|INR|Rs\.?))\s?(\d[\d,]*(?:\.\d{1,2})?)", re.I)
# Phone numbers must carry a phone-style marker (leading +, parentheses or a
# hyphen) so that runs of table numbers such as "100 200 300" never match.
PHONE_RE = re.compile(r"(?<![\w.])(?:\+\d[\d\s().-]{7,}\d|\(\d{2,5}\)[\d\s.-]{6,}\d|\d{2,5}-\d{3,4}-\d{3,5})(?!\w)(?!\.\d)")
# Units chosen to avoid ordinary words: no bare "in", "l" or "g".
SPEC_RE = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s?(mm|cm|km|kg|mg|lbs?|oz|ml|w|kw|kwh|v|mah|gb|tb|mb|mhz|ghz|hz|rpm|psi|ft|sq\s?ft)\b",
    re.I)
TIME_RE = re.compile(r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm)\b|\b(?:[01]?\d|2[0-3]):[0-5]\d\b", re.I)
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

# Filename, alt and title tokens that suggest an image carries quotable facts.
_FACT_PREFIXES = ("price", "pricing", "menu", "tariff", "timetable", "datasheet",
                  "infographic", "specification", "schedule")
_FACT_EXACT = {"spec", "specs", "rates", "fees", "hours", "opening", "chart", "sizechart"}
# Tokens that mark decorative or interface images; any one of them excludes the image.
_EXCLUDE = {"logo", "icon", "icons", "favicon", "avatar", "sprite", "hamburger", "toggle",
            "arrow", "chevron", "caret", "close", "badge", "social", "share", "cart",
            "search", "bg", "background", "placeholder", "spinner", "loader", "pixel"}
_RASTER_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def normalize_number(text):
    """'1,299.00' -> '1299', '49.90' -> '49.9'. Used only for presence tests."""
    value = text.replace(",", "").strip().rstrip(".")
    whole, _, fraction = value.partition(".")
    fraction = fraction.rstrip("0")
    whole = whole.lstrip("0") or "0"
    return whole + ("." + fraction if fraction else "")


def html_number_set(texts):
    """Every number that appears anywhere in the given readable texts, normalized."""
    found = set()
    for text in texts:
        for match in _NUMBER_RE.finditer(text or ""):
            found.add(normalize_number(match.group(0)))
    return found


_DATE_LIKE_RE = re.compile(r"(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.](?:19|20)\d{2}")


def phone_digits(text):
    """Last ten digits of a phone-shaped match, or '' for dates and short runs."""
    if _DATE_LIKE_RE.fullmatch(text.strip()):
        return ""
    digits = re.sub(r"\D", "", text)
    return digits[-10:] if len(digits) >= 9 else ""


def html_phone_set(texts):
    return {d for text in texts for m in PHONE_RE.finditer(text or "") for d in [phone_digits(m.group(0))] if d}


def extract_facts(text):
    """Fact-shaped values in a block of text: list of (kind, shown, key) tuples.

    `key` is what presence is tested on: a normalized number for prices and specs,
    the last ten digits for phone numbers. Duplicates are removed in order."""
    out, seen = [], set()
    text = text or ""
    for match in PRICE_RE.finditer(text):
        item = ("price", match.group(0).strip(), normalize_number(match.group(1)))
        if item[2] not in ("0",) and ("price", item[2]) not in seen:
            seen.add(("price", item[2]))
            out.append(item)
    for match in SPEC_RE.finditer(text):
        key = normalize_number(match.group(1))
        if ("spec", key, match.group(2).lower()) not in seen:
            seen.add(("spec", key, match.group(2).lower()))
            out.append(("spec", match.group(0).strip(), key))
    for match in PHONE_RE.finditer(text):
        digits = phone_digits(match.group(0))
        if digits and ("phone", digits) not in seen:
            seen.add(("phone", digits))
            out.append(("phone", match.group(0).strip(), digits))
    return out


def facts_missing_from(facts, numbers, phones):
    """Facts whose key never appears in the readable text sets. Conservative: a
    price or spec counts as present when its number appears anywhere in the text."""
    missing = []
    for kind, shown, key in facts:
        present = key in phones if kind == "phone" else key in numbers
        if not present:
            missing.append((kind, shown, key))
    return missing


def _tokens(text):
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t]


def image_tokens(src, alt, title):
    path = unquote(urlsplit(src).path) if src else ""
    name = path.rsplit("/", 1)[-1]
    return _tokens(name) + _tokens(alt) + _tokens(title)


def fact_keywords(tokens):
    """Fact keywords present in the tokens, or () when an exclusion token appears."""
    if any(t in _EXCLUDE for t in tokens):
        return ()
    hits = []
    for t in tokens:
        if t in _FACT_EXACT or t.startswith(_FACT_PREFIXES):
            if t not in hits:
                hits.append(t)
    return tuple(hits)


def is_excluded_image(tokens):
    return any(t in _EXCLUDE for t in tokens)


def image_kind(src, content_type=None):
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype == "image/svg+xml":
        return "svg"
    if ctype.startswith("image/"):
        return "raster"
    path = urlsplit(src).path.lower() if src else ""
    if path.endswith(".svg"):
        return "svg"
    if path.endswith(_RASTER_EXT):
        return "raster"
    return "unknown"


def raster_dimensions(data):
    """(format, width, height) read from the first bytes of a PNG, GIF, JPEG or
    WebP file, or None. Never decodes pixels; a truncated header returns None."""
    if not data or len(data) < 12:
        return None
    try:
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24 and data[12:16] == b"IHDR":
            width, height = struct.unpack(">II", data[16:24])
            return ("png", width, height)
        if data[:6] in (b"GIF87a", b"GIF89a"):
            width, height = struct.unpack("<HH", data[6:10])
            return ("gif", width, height)
        if data.startswith(b"\xff\xd8"):
            pos = 2
            while pos + 9 < len(data):
                if data[pos] != 0xFF:
                    pos += 1
                    continue
                marker = data[pos + 1]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
                    pos += 1 if marker == 0xFF else 2
                    continue
                length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
                    return ("jpeg", width, height)
                if length < 2:
                    return None
                pos += 2 + length
            return None
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
            chunk = data[12:16]
            if chunk == b"VP8X":
                width = 1 + int.from_bytes(data[24:27], "little")
                height = 1 + int.from_bytes(data[27:30], "little")
                return ("webp", width, height)
            if chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
                width, height = struct.unpack("<HH", data[26:30])
                return ("webp", width & 0x3FFF, height & 0x3FFF)
            if chunk == b"VP8L" and data[20] == 0x2F:
                bits = int.from_bytes(data[21:25], "little")
                return ("webp", (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
    except (struct.error, IndexError):
        return None
    return None


def svg_text(data, max_chars=4000):
    """(status, text) for an SVG document: the text drawn by <text> elements,
    including nested <tspan> and <textPath> content. DTDs and entities are
    refused before parsing, matching the sitemap parser's defense, so the XML
    parser never expands entities."""
    if not data:
        return ("empty", "")
    head = data[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in data.upper():
        return ("unsupported", "")
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return ("malformed", "")
    if root.tag.rsplit("}", 1)[-1] != "svg":
        return ("not_svg", "")
    # itertext() on each <text> element includes nested <tspan>/<textPath> text
    # and the text that follows them, so a value split across tspans stays whole.
    parts = [" ".join(element.itertext()) for element in root.iter()
             if isinstance(element.tag, str) and element.tag.rsplit("}", 1)[-1] == "text"]
    text = " ".join(" ".join(parts).split())[:max_chars]
    return ("ok", text)
