"""analyze_non_text.py -- facts locked in non-text media (images and PDFs).

A fact a person can read inside an image or a PDF is invisible to a crawler or
assistant that reads HTML text. This check compares the facts observed in media
with the facts stated in readable text and reports only what the snapshot shows:

  - facts-in-images (confirmed): a same-origin SVG draws prices, phone numbers or
    specifications that the embedding page states nowhere in its text, alt text,
    meta description or JSON-LD.
  - facts-in-images (suspected): an image whose filename, alt or title names
    facts (price list, menu, opening hours, spec sheet) sits on a page whose text
    carries no such facts. Raster pixels are never read here; the optional agent
    vision stage (AG-04) can confirm by looking at the listed images.
  - pdf-only-facts: a linked PDF states facts that no crawled HTML page states.
  - pdf-image-only: a linked PDF has no text layer at all (scanned pages).

Network-free: every observation was acquired by acquire_site.py. A PDF or image
that could not be fetched or read is a limitation of this audit, recorded in
metrics and warnings, never a finding about the site.
"""
import json
from non_text import (extract_facts, facts_missing_from, html_number_set, html_phone_set,
                      PRICE_RE, SPEC_RE, TIME_RE)
from models import (skill_result, make_finding, coverage_ratio, scale_confidence,
                    step_down_severity)

_PRICE_WORDS = ("price", "pricing", "menu", "tariff", "rates", "fees")
_TIME_WORDS = ("hours", "opening", "schedule", "timetable")
_SPEC_WORDS = ("spec", "specs", "specification", "datasheet", "chart", "sizechart", "infographic")
_MIN_PDF_ONLY_FACTS = 2


def _readable_texts(page):
    """Every machine-readable text channel of a page: body text, title, meta
    description, image alt text and JSON-LD values."""
    features = page.features or {}
    texts = [page.visible_text or "", page.title or "", page.meta_description or ""]
    texts.extend(r.get("alt") or "" for r in features.get("image_records", ()))
    for block in page.jsonld_blocks:
        try:
            texts.append(json.dumps(block, default=_plain, ensure_ascii=False))
        except (TypeError, ValueError):
            continue
    return texts


def _plain(value):
    if hasattr(value, "items"):
        return dict(value.items())
    if isinstance(value, tuple):
        return list(value)
    return str(value)


def _family_covered(word, text):
    if word.startswith(_PRICE_WORDS):
        return len(PRICE_RE.findall(text)) >= 3
    if word.startswith(_TIME_WORDS):
        return len(TIME_RE.findall(text)) >= 2
    if word.startswith(_SPEC_WORDS):
        return len(SPEC_RE.findall(text)) >= 3
    return False


def _page_complete(page):
    return bool((page.features or {}).get("visible_text_complete", True))


def _image_label(entry):
    if entry.get("width") and entry.get("height"):
        return f"{entry['width']}x{entry['height']} px, measured from the file header"
    if entry.get("width_attr") and entry.get("height_attr"):
        return f"{entry['width_attr']}x{entry['height_attr']} px per its HTML attributes"
    return "dimensions not measured"


def analyze_non_text(artifacts, deadline):
    media = artifacts.media_data
    if deadline.expired():
        return skill_result("crawl-render-audit", status="insufficient_evidence",
                            warnings=["Non-text media checks skipped: deadline reached."])
    if not media:
        return skill_result("crawl-render-audit", metrics={"non_text_media_assessed": False})

    pages = {p.url: p for p in artifacts.pages
             if p.status_code == 200 and p.features and "non_html_content" not in p.warnings}
    findings, warnings = [], []

    # --- images ----------------------------------------------------------
    svg_confirmed, raster_suspected = [], []
    for entry in media.get("images", ()):
        hosts = [pages[u] for u in entry.get("pages", ()) if u in pages]
        if not hosts:
            continue
        texts = [t for page in hosts for t in _readable_texts(page)]
        if entry.get("svg_status") == "ok":
            missing = facts_missing_from(extract_facts(entry.get("svg_text", "")),
                                         html_number_set(texts), html_phone_set(texts))
            if missing:
                svg_confirmed.append((entry, hosts, missing))
            continue
        keywords = entry.get("keywords") or ()
        if not keywords:
            continue
        width = entry.get("width") or entry.get("width_attr")
        height = entry.get("height") or entry.get("height_attr")
        if (width and width < 200) or (height and height < 100):
            continue
        if any(ch.isdigit() for ch in (entry.get("alt") or "")):
            continue
        joined = " ".join(texts)
        if all(_family_covered(word, joined) for word in keywords):
            continue
        raster_suspected.append((entry, hosts))

    if svg_confirmed:
        complete = all(_page_complete(page) for _, hosts, _ in svg_confirmed for page in hosts)
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="medium",
            status="confirmed" if complete else "suspected", confidence=0.9 if complete else 0.6,
            title="Facts are drawn inside images instead of stated in text",
            root_cause="Facts shown only inside an image are invisible to crawlers and assistants "
                       "that read HTML text.",
            affected_pages=sorted({page.url for _, hosts, _ in svg_confirmed for page in hosts}),
            evidence=[{"type": "image_text",
                       "description": f"SVG image {entry['url']} draws "
                                      + ", ".join(shown for _, shown, _ in missing[:6])
                                      + "; none of these values appear in the page text, alt text, "
                                        "meta description or JSON-LD.",
                       "urls": [page.url for page in hosts]}
                      for entry, hosts, missing in svg_confirmed[:10]],
            suggested_action={
                "summary": "State the facts shown in these images as real text on the page",
                "steps": ["Write the prices, phone numbers or specifications shown in each listed image "
                          "as HTML text near the image",
                          "Give each image alt text that says what it shows",
                          "Where the facts are structured, also state them in JSON-LD"],
                "priority": "medium", "effort": "low",
                "expected_benefit": "Crawlers and assistants that read text can quote these facts",
                "verification": "Re-run the audit and confirm the listed values appear in page text",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_non_text.py",
                        "rule_id": "facts-in-images"},
        ))

    if raster_suspected:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="proactive_improvement", severity="low",
            status="suspected", confidence=0.5,
            title="Images appear to carry facts that the page text does not state",
            root_cause="Facts shown only inside an image are invisible to crawlers and assistants "
                       "that read HTML text.",
            affected_pages=sorted({page.url for _, hosts in raster_suspected for page in hosts}),
            evidence=[{"type": "image_reference",
                       "description": f"Image {entry['url']} is named or labelled '"
                                      + ", ".join(entry["keywords"])
                                      + f"' ({_image_label(entry)}; fetch: {entry.get('fetch_status')}), "
                                        "but the page text states no matching facts. The pixels were not "
                                        "read; view the image or supply AG-04 to confirm.",
                       "urls": [page.url for page in hosts]}
                      for entry, hosts in raster_suspected[:10]],
            suggested_action={
                "summary": "Check whether these images contain prices, hours or specifications "
                           "that appear nowhere in text",
                "steps": ["Open each listed image and note any fact it shows",
                          "Write each such fact as HTML text on the same page",
                          "Give each image alt text that says what it shows"],
                "priority": "low", "effort": "low",
                "expected_benefit": "Facts that only appear in images become quotable",
                "verification": "Re-run the audit; the image should no longer be listed",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_non_text.py",
                        "rule_id": "facts-in-images"},
        ))

    # --- PDFs ------------------------------------------------------------
    site_texts = [t for page in pages.values() for t in _readable_texts(page)]
    site_numbers, site_phones = html_number_set(site_texts), html_phone_set(site_texts)
    acq = artifacts.acquisition_metadata.get("coverage", {})
    crawl_ratio = coverage_ratio(acq.get("urls_analyzed", len(artifacts.pages)),
                                 acq.get("urls_discovered", len(artifacts.pages)))
    text_complete = all(_page_complete(page) for page in pages.values())
    pdf_only, image_only, unread = [], [], []
    for doc in media.get("pdfs", ()):
        status = doc.get("extraction")
        if status == "ok":
            missing = facts_missing_from(extract_facts(doc.get("text", "")), site_numbers, site_phones)
            if len(missing) >= _MIN_PDF_ONLY_FACTS:
                pdf_only.append((doc, missing))
        elif status == "no_text_layer" and doc.get("has_images"):
            image_only.append(doc)
        elif doc.get("fetch_status") == "ok" and status in ("unsupported", "encrypted", "malformed", "deadline", "not_pdf"):
            unread.append(doc)
    for doc in unread:
        warnings.append(f"PDF {doc['url']} could not be read (status: {doc['extraction']}); "
                        "its contents were not assessed.")

    if pdf_only:
        ratio = crawl_ratio if text_complete else min(crawl_ratio, 0.49)
        complete = ratio >= 0.999
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect",
            severity=step_down_severity("medium", ratio),
            status="confirmed" if complete else "suspected",
            confidence=scale_confidence(0.85, ratio),
            title="Key facts are published only inside PDF files",
            root_cause="Facts that exist only in a PDF are less likely to be retrieved and quoted "
                       "than facts stated on an HTML page"
                       + ("" if complete else " (compared with the HTML pages actually crawled; "
                                                "the rest of the site was not analyzed)"),
            affected_pages=sorted({u for doc, _ in pdf_only for u in doc.get("linked_from", ())}),
            evidence=[{"type": "pdf_text",
                       "description": f"PDF {doc['url']} states {len(missing)} value(s) that no crawled "
                                      "HTML page states, for example "
                                      + ", ".join(shown for _, shown, _ in missing[:6]) + ".",
                       "urls": list(doc.get("linked_from", ()))}
                      for doc, missing in pdf_only[:10]],
            suggested_action={
                "summary": "Publish the key facts from these PDFs on an HTML page",
                "steps": ["Create or extend an HTML page that states the prices, specifications or "
                          "contact details found in each PDF",
                          "Link the PDF from that page as a download, not as the only source",
                          "Keep the HTML page and the PDF in sync when either changes"],
                "priority": step_down_severity("medium", ratio), "effort": "medium",
                "expected_benefit": "Assistants can quote the facts from a page they can read directly",
                "verification": "Re-run the audit and confirm the listed values appear on an HTML page",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_non_text.py",
                        "rule_id": "pdf-only-facts"},
        ))

    if image_only:
        findings.append(make_finding(
            category="ai_discoverability", finding_type="defect", severity="medium",
            status="confirmed", confidence=0.85,
            title="Linked PDFs contain scanned images with no readable text",
            root_cause="A PDF whose pages are images has no text layer, so nothing in it can be "
                       "extracted or quoted.",
            affected_pages=sorted({u for doc in image_only for u in doc.get("linked_from", ())}),
            evidence=[{"type": "pdf_text",
                       "description": f"PDF {doc['url']} has {doc.get('pages', 0)} page(s) that draw "
                                      "images and no text.",
                       "urls": list(doc.get("linked_from", ()))}
                      for doc in image_only[:10]],
            suggested_action={
                "summary": "Replace image-only PDFs with text-based PDFs and state the key facts in HTML",
                "steps": ["Export each PDF from its source document so the text is selectable, or "
                          "add a text layer with OCR",
                          "State the most important facts from each PDF on an HTML page"],
                "priority": "medium", "effort": "medium",
                "expected_benefit": "The PDF contents become extractable and quotable",
                "verification": "Open the PDF and confirm its text can be selected and copied",
            },
            provenance={"skill": "crawl-render-audit", "script": "analyze_non_text.py",
                        "rule_id": "pdf-image-only"},
        ))

    summary = dict(media.get("summary", {}))
    return skill_result(
        "crawl-render-audit", findings=findings, warnings=warnings,
        metrics={"non_text_media_assessed": True, **summary,
                 "svg_images_with_text_only_facts": len(svg_confirmed),
                 "images_suspected_to_carry_facts": len(raster_suspected),
                 "pdfs_with_pdf_only_facts": len(pdf_only),
                 "pdfs_image_only": len(image_only), "pdfs_unreadable": len(unread)},
        coverage={"pages_analyzed": len(pages), "pages_skipped": len(artifacts.pages) - len(pages),
                  "queries_attempted": 0, "queries_completed": 0},
    )
