"""Parser for the llms.txt convention (https://llmstxt.org).

An llms.txt file is Markdown with, in order: one H1 with the site or project name
(required), an optional blockquote summary, optional free text, and H2 sections
whose bodies are lists of Markdown links, "- [name](url): notes". llms-full.txt
is the companion file that inlines the full text of those pages.
"""
import re
from urllib.parse import urljoin, urlsplit

_LINK = re.compile(r"\[([^\]\n]{0,300})\]\(\s*<?([^)\s>]{1,2000})>?(?:\s+\"[^\"]*\")?\s*\)")
_BARE_URL = re.compile(r"(?<![(<\[])\bhttps?://[^\s)>\]]{1,2000}")
MAX_LINKS = 100


def parse_llms_txt(text, base_url):
    """Structure of an llms.txt file: title, summary, sections, absolute link URLs
    (Markdown links first, then bare URLs) and format problems."""
    lines = (text or "").lstrip('\ufeff').splitlines()
    content = [line.strip() for line in lines if line.strip()]
    title = None
    if content and re.match(r"#\s+\S", content[0]) and not content[0].startswith("##"):
        title = content[0].lstrip("#").strip()[:200]
    h1_count = sum(1 for line in content if re.match(r"#\s+\S", line) and not line.startswith("##"))
    summary = any(line.startswith(">") for line in content[1:4])
    sections = [line.lstrip("#").strip()[:120] for line in content if re.match(r"##\s+\S", line)
                and not line.startswith("###")][:40]
    links, markdown_links = [], 0
    for line in lines:
        for match in _LINK.finditer(line):
            markdown_links += 1
            _add(links, match.group(2), base_url)
    if not markdown_links:
        for line in lines:
            for match in _BARE_URL.finditer(line):
                _add(links, match.group(0), base_url)
    issues = []
    if title is None:
        issues.append("the file does not start with an H1 title ('# Name')")
    elif h1_count > 1:
        issues.append(f"the file has {h1_count} H1 titles; the format allows one")
    advice = []
    if not links:
        advice.append("the file links to no pages (file lists are optional)")
    elif not markdown_links:
        advice.append("pages are listed as bare URLs, not as Markdown links ('- [name](url)')")
    elif not sections:
        advice.append("links are not grouped under optional H2 sections ('## Section')")
    return {"title": title, "has_summary": summary, "sections": sections, "links": links[:MAX_LINKS],
            "link_count": len(links), "markdown_links": markdown_links, "structure_issues": issues, 'format_advice': advice}


def _add(links, raw, base_url):
    if len(links) >= MAX_LINKS * 2:
        return
    try:
        url = urljoin(base_url, raw.strip())
        parts = urlsplit(url)
    except ValueError:
        return
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return
    url = url.split("#", 1)[0]
    if url not in links:
        links.append(url)
