"""dates.py -- date extraction for freshness checks.

Parses the formats real sites use in visible text (ISO, "Mar 5, 2024",
"5 March 2024", "March 2024", unambiguous DD/MM/YYYY, copyright years) and
classifies each visible date by the words around it, because "an old date" only
means something in context:

  update_claim  "last updated", "reviewed", "as of", "revised"
  expiry        "valid until", "offer ends", "expires", "deadline", "last date"
  historical    "founded", "since", "established", "history"   (never stale)
  copyright     "(c)" / "copyright"
  editorial     "posted", "published", "by <name>"
  unclassified  anything else -- never produces a staleness finding on its own
"""
import re
from datetime import date

_MONTHS = {m: i for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
PATTERNS = (
    ("iso", re.compile(r"\b((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})\b")),
    ("mdy", re.compile(r"\b" + _MON + r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+((?:19|20)\d{2})\b", re.I)),
    ("dmy", re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + _MON + r",?\s+((?:19|20)\d{2})\b", re.I)),
    ("my", re.compile(r"\b" + _MON + r",?\s+((?:19|20)\d{2})\b", re.I)),
    ("slash", re.compile(r"\b(\d{1,2})/(\d{1,2})/((?:19|20)\d{2})\b")),
)
COPYRIGHT = re.compile(r"(?:\u00a9|&copy;|\(c\)|copyright)\s*((?:19|20)\d{2})(?:\s*[-\u2013]\s*((?:19|20)?\d{2}))?", re.I)

CONTEXT = (
    ("update_claim", re.compile(r"(last\s+)?(updated|reviewed|revised|modified|refreshed|verified)|as of|current as", re.I)),
    ("expiry", re.compile(r"valid (until|till|through|thru)|offer ends|ends on|expir(es|y|ing)|deadline|last date|"
                          r"until stocks|sale ends|available until|closes on|apply by|register by", re.I)),
    ("historical", re.compile(r"founded|since|established|est\.|history|incorporated|began|started in|launched in|"
                              r"in business since|anniversary", re.I)),
    ("editorial", re.compile(r"posted|published|written|\bby\s+[A-Z]|min read|comments?", re.I)),
)


def _mk(y, m, d):
    try:
        return date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return None


def _parse(kind, m):
    g = m.groups()
    if kind == "iso":
        return _mk(g[0], g[1], g[2]), "day"
    if kind == "mdy":
        return _mk(g[2], _MONTHS.get(g[0][:3].lower()), g[1]), "day"
    if kind == "dmy":
        return _mk(g[2], _MONTHS.get(g[1][:3].lower()), g[0]), "day"
    if kind == "my":
        return _mk(g[1], _MONTHS.get(g[0][:3].lower()), 1), "month"
    if kind == "slash":
        a, b, y = int(g[0]), int(g[1]), int(g[2])
        if a > 12 and b <= 12:
            return _mk(y, b, a), "day"      # unambiguous DD/MM
        if b > 12 and a <= 12:
            return _mk(y, a, b), "day"      # unambiguous MM/DD
        return None, None                    # ambiguous: skipped
    return None, None


def classify(window):
    for label, rx in CONTEXT:
        if rx.search(window):
            return label
    return "unclassified"


def extract_visible_dates(text, limit=60):
    """[{date, precision, context, raw, window}] from visible text, deduplicated by span."""
    out, taken = [], []
    text = text or ""
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            if any(m.start() < e and m.end() > s for s, e in taken):
                continue
            d, precision = _parse(kind, m)
            if not d:
                continue
            taken.append((m.start(), m.end()))
            window = text[max(0, m.start() - 60):m.start()] + " " + text[m.end():m.end() + 25]
            # Nearest words win: "Offer last updated 2019. Promotion valid through
            # 2020" -- the 2020 date is an expiry, not an update.
            near = text[max(0, m.start() - 30):m.start()]
            near = near.split(".")[-1] if "." in near else near
            context = classify(near)
            if context == "unclassified":
                context = classify(window)
            out.append({"date": d, "precision": precision, "context": context,
                        "raw": m.group(0), "window": " ".join(window.split())[:120]})
            if len(out) >= limit:
                return out
    return out


def copyright_years(text):
    """Latest year in each copyright statement ('(c) 2019-2023' -> 2023)."""
    years = []
    for m in COPYRIGHT.finditer(text or ""):
        start = int(m.group(1))
        end = m.group(2)
        if end:
            end = int(end) if len(end) == 4 else int(str(start)[:2] + end)
            years.append(max(start, end))
        else:
            years.append(start)
    return years


def parse_machine_date(value):
    """ISO-8601 or RFC-1123 (HTTP Last-Modified) -> date."""
    if not isinstance(value, str) or not value.strip():
        return None
    v = value.strip()
    m = re.match(r"((?:19|20)\d{2})-(\d{2})-(\d{2})", v)
    if m:
        return _mk(*m.groups())
    m = re.match(r"\w{3},\s+(\d{1,2})\s+(\w{3})\s+(\d{4})", v)
    if m:
        return _mk(m.group(3), _MONTHS.get(m.group(2)[:3].lower()), m.group(1))
    return None
