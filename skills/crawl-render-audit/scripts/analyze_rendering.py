"""analyze_rendering.py -- raw vs rendered content gaps.

Two tiers, matching common/capabilities.py:
  - "rendering_gap_heuristic" (executable, always runs): flags pages that run
    scripts and whose raw HTML shows near-zero visible text -- a real,
    evidence-backed signal that needs no browser, but on its own can't distinguish
    "needs JS" from "genuinely thin page". A page with no script at all is never
    flagged: nothing can add content to it after load.
  - "rendering_headless_browser" (fallback/optional): when a real headless browser
    is available (see capabilities.detect_capabilities), every heuristic-flagged page
    is actually re-rendered and compared against the static fetch. A page is only a
    *confirmed* defect when rendering reveals substantial content the raw HTML
    lacked; if rendering also comes back thin (or fails), that page is not a
    confirmed gap -- it's insufficient evidence, not a fabricated defect. Bounded by
    MAX_RENDERED_PAGES and PER_FETCH_TIMEOUT_MS; a single page's render failure
    never aborts the batch.

<noscript> fallback: text inside <noscript> is excluded from the raw-text count,
because a visitor whose browser runs scripts never sees it. Substantial fallback
text still counts as content for crawlers that do not run scripts, so such a page
is not a gap. A <noscript> that only says JavaScript is required is the page's own
statement that it depends on scripts; it is cited in the evidence and raises the
heuristic's confidence.

Returns gap pages only via SkillResult.metrics; never writes back into PageArtifact.
"""
from models import (skill_result, make_finding, insufficient_evidence_result, apply_invariant_i1,
                     coverage_ratio, scale_confidence, step_down_severity)
# The per-page-type thresholds and the <noscript> reading live in check_helpers.py,
# so the checks that skip pages built by JavaScript use the same test as this one.
from check_helpers import (MIN_SUBSTANTIAL_CHARS as _MIN_SUBSTANTIAL_CHARS,
                           MIN_SUBSTANTIAL_CHARS_BY_TYPE as _MIN_SUBSTANTIAL_CHARS_BY_TYPE,
                           substantial_threshold as _threshold_for, noscript_state as _noscript_state,
                           script_dependent)


def _heuristic_gap_pages(pages):
    """Executable today: raw HTML with very little visible text, judged against a
    page-type-appropriate threshold rather than one flat number. <noscript> text
    does not count as content, unless it is a real fallback of substantial size."""
    return [p.url for p in pages
            if p.status_code == 200 and "non_html_content" not in p.warnings and script_dependent(p)]


# Independent signs, in the raw HTML, that a script builds the page content.
_SIGN_TEXT = {
    "app_shell": "An empty application mount point (id root, app, __next...) holds the page",
    "framework_bundle": "A client-side framework bundle or framework attribute is present",
    "serialized_state": "Page data is serialized in a script for the browser to render",
    "noscript": "The page's <noscript> text says JavaScript is required and offers no fallback content",
    "state_content": "The serialized page data holds more readable text than the page's HTML shows: the content "
                     "exists, but only for a script to render",
}
_SIGN_LABEL = {"app_shell": "an empty app mount point", "framework_bundle": "a framework bundle",
               "serialized_state": "serialized page state", "noscript": "a JavaScript-required notice",
               "state_content": "page text held only in script data"}


def _link_hub(page):
    """True when most of a thin page's visible text is the text of real links: a
    splash page, a site or campus chooser, a page of links. Its content is in the
    raw HTML; it is short, not built by a script."""
    anchors = [(h or "", (t or "").strip()) for h, t in (page.features or {}).get("anchors") or ()]
    linked = [t for h, t in anchors if t and not h.strip().lower().startswith(("#", "javascript:"))]
    text = len((page.visible_text or "").strip())
    return len(linked) >= 2 and text > 0 and sum(len(t) for t in linked) >= 0.3 * text


def _client_render_signs(page, js_required):
    """The set of _SIGN_TEXT kinds observed on one thin page. A link hub counts
    only when it also has an empty mount point or a JavaScript-required notice:
    a framework bundle or a state blob alone does not outweigh links that already
    carry the page's text."""
    f = page.features or {}
    if _link_hub(page) and not (f.get("spa_mount") or js_required):
        return set()
    signs = set()
    if f.get("spa_mount"):
        signs.add("app_shell")
    if f.get("framework_hint"):
        signs.add("framework_bundle")
    if f.get("state_blob"):
        signs.add("serialized_state")
        # Text for the page in the serialized data, at least as much as a page of
        # this type needs, while the HTML itself shows less: the gap is observed.
        state_text = int(f.get("state_text_chars") or 0)
        if state_text >= _threshold_for(page.page_type) and state_text > len((page.visible_text or "").strip()):
            # One blob is one sign: the stronger reading replaces the weaker one.
            signs.discard("serialized_state")
            signs.add("state_content")
    if js_required:
        signs.add("noscript")
    return signs


def _noscript_summary(pages):
    """Per-page noscript observations for evidence and metrics."""
    js_required, fallback = [], []
    for p in pages:
        if p.status_code != 200:
            continue
        script_on, chars, required = _noscript_state(p)
        threshold = _threshold_for(p.page_type)
        if required:
            js_required.append(p.url)
        elif script_on < threshold <= chars:
            fallback.append(p.url)
    return js_required, fallback


def _render_with_headless_browser(urls: list, limits, timeout_s: float = None) -> dict:
    """Tier 2 (optional): actually renders each URL with a real headless browser and
    returns {url: rendered_text_length_or_None}. A per-page failure degrades that
    page to None; it never raises out of this function. Bounded by MAX_RENDERED_PAGES
    (how many pages get rendered at all) -- retained evidence is further capped by
    MAX_RETAINED_RENDERED_PAGES by the caller.

    Runs inside a genuine child process (common/subprocess_isolation.py), not just
    inside Playwright's own cooperative per-navigation timeout: a real browser
    process (or something it spawns) can become unresponsive in ways Playwright's
    own timeout cannot always detect (e.g. a hung `browser.close()`), and a
    ThreadPoolExecutor future timeout can only abandon a hung thread, never kill
    it. The child process is hard-killed at the wall-clock deadline regardless of
    what is happening inside it, so this call can never block the orchestrator
    past its own timeout.
    """
    from subprocess_isolation import run_isolated
    timeout_s = timeout_s if timeout_s is not None else (limits.PER_FETCH_TIMEOUT_MS / 1000) * max(1, len(urls)) + 5
    result = run_isolated(_render_urls_in_child, args=(urls, limits.MAX_RENDERED_PAGES, limits.PER_FETCH_TIMEOUT_MS),
                           timeout_s=timeout_s)
    if not result.ok:
        # Killed, crashed, or errored -- never fabricate rendered content. The
        # caller treats an empty dict the same as "headless rendering unavailable
        # this run": pages fall back to insufficient_evidence, never a defect.
        return {}, result.timed_out, result.error
    return result.value, False, None


def _render_urls_in_child(urls: list, max_rendered_pages: int, per_fetch_timeout_ms: int) -> dict:
    """Runs in the child process spawned by run_isolated(). Must stay picklable-by-
    reference (top-level function, plain-type args/return) and must not touch
    anything from the parent's memory beyond its arguments."""
    urls = urls[:max_rendered_pages]
    rendered_lengths = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            from transport import Transport
            from constants import DEFAULT_LIMITS
            from dataclasses import replace
            from instrumentation import Instrumentation
            from robots_policy import RobotsPolicy
            from urllib.parse import urlsplit
            from time import monotonic
            part = urlsplit(urls[0])
            origin = f"{part.scheme}://{part.netloc}"
            tr = Transport(origin, monotonic() + 25, replace(DEFAULT_LIMITS, MAX_TOTAL_BYTES=4_000_000, MAX_TOTAL_HTTP_REQUESTS=20), Instrumentation())
            robots, status = tr.get(origin + "/robots.txt", robots_exempt=True)
            if status != "ok" or robots.status_code not in (200, 404) or robots.truncated:
                return {}
            if robots.status_code == 200:
                try:
                    robots_text = robots.content.decode("utf-8", "strict")
                    if robots_text.lstrip().lower().startswith(("<html", "<!doctype")):
                        return {}
                except UnicodeDecodeError:
                    return {}
            else:
                robots_text = ""
            tr.robots = RobotsPolicy(robots_text)
            tr.delay = max(tr.delay, tr.robots.crawl_delay("BrandAIReadinessAuditBot"))
            browser = p.chromium.launch()
            context = browser.new_context(service_workers="block", accept_downloads=False)
            # Browser requests never leave through Chromium's own networking stack.
            def route_request(route):
                if route.request.method != "GET" or route.request.resource_type not in ("document", "script", "stylesheet", "fetch", "xhr"):
                    route.abort(); return
                response, outcome = tr.get(route.request.url)
                if outcome != "ok" or not response.ok or response.truncated:
                    route.abort(); return
                route.fulfill(status=response.status_code, body=response.content,
                              headers={"Content-Type": response.headers.get("Content-Type", "text/plain")})
            context.route("**/*", route_request)
            if not hasattr(context, "route_web_socket"):
                browser.close(); return {}  # Older versions cannot enforce websocket isolation.
            context.route_web_socket("**/*", lambda ws: ws.close())
            page = context.new_page()
            for url in urls:
                try:
                    page.goto(url, timeout=per_fetch_timeout_ms, wait_until="networkidle")
                    text = page.inner_text("body")
                    rendered_lengths[url] = len((text or "").strip())
                except Exception:
                    rendered_lengths[url] = None
            browser.close()
    except Exception:
        return {}
    return rendered_lengths


def analyze_rendering(artifacts, deadline, limits, capabilities=None):
    capabilities = capabilities or {}
    headless_available = bool(capabilities.get("headless_rendering"))

    if not artifacts.pages:
        return insufficient_evidence_result(
            "crawl-render-audit", "No pages were acquired; rendering cannot be assessed.",
            metrics={"rendered_pages": 0, "raw_rendered_gap_pages": [],
                     "rendering_mode": "headless_browser" if headless_available else "heuristic_only"},
        )

    heuristic_gap_pages = _heuristic_gap_pages(artifacts.pages)
    js_required_pages, noscript_fallback_pages = _noscript_summary(artifacts.pages)
    findings = []
    confirmed_gap_pages = []
    rendered_count = 0

    if headless_available and heuristic_gap_pages:
        rendered_lengths, subprocess_timed_out, subprocess_error = _render_with_headless_browser(
            heuristic_gap_pages, limits, timeout_s=max(.01, min(25., deadline.remaining_seconds())))
        if subprocess_timed_out:
            findings.append(apply_invariant_i1(make_finding(
                category="ai_discoverability", finding_type="proactive_improvement", severity="low",
                status="insufficient_evidence", confidence=0.2,
                title="Headless rendering did not complete within its time budget",
                root_cause="The isolated rendering subprocess exceeded its wall-clock deadline and was "
                           "terminated; rendering-gap pages fall back to the static-only heuristic",
                evidence=[{"type": "render_subprocess_timeout",
                           "description": subprocess_error or "subprocess killed on timeout",
                           "urls": heuristic_gap_pages[:10]}],
                suggested_action={"summary": "Re-run the audit; if this recurs, the target site may be slow "
                                              "or blocking headless browsers",
                                   "steps": ["Re-run the audit", "Check for bot-detection on the target site"],
                                   "priority": "low", "effort": "low",
                                   "expected_benefit": "Restores confirmed (not just suspected) rendering-gap findings",
                                   "verification": "Re-run and confirm rendering_mode reports headless_browser"},
                provenance={"skill": "crawl-render-audit", "script": "analyze_rendering.py",
                            "rule_id": "render-subprocess-timeout", "tier": "rendering_headless_browser"},
            )))
        page_type_by_url = {p.url: p.page_type for p in artifacts.pages}
        rendered_count = sum(1 for v in rendered_lengths.values() if v is not None)
        confirmed_gap_pages = [
            url for url, length in rendered_lengths.items()
            if length is not None and length >= _threshold_for(page_type_by_url.get(url))
        ]
        # Pages that still render thin (or failed to render) are NOT a confirmed
        # rendering gap -- they may just be genuinely thin pages. Report separately,
        # calibrated as insufficient evidence, never as a fabricated defect.
        unconfirmed = [u for u in heuristic_gap_pages if u not in confirmed_gap_pages]
        if unconfirmed:
            findings.append(make_finding(
                category="ai_discoverability", finding_type="proactive_improvement", severity="low",
                status="insufficient_evidence", confidence=0.3,
                title="Some near-empty pages could not be confirmed as rendering gaps",
                root_cause="Headless rendering also returned little content, or failed, "
                           "for these pages -- could be genuinely thin content rather than a JS dependency",
                evidence=[{"type": "render_gap_unconfirmed", "description": "Rendered content still thin or unavailable",
                           "urls": unconfirmed[:10]}],
                suggested_action={"summary": "Manually inspect these pages to confirm whether content is missing",
                                   "steps": ["Open the page in a browser and compare to the raw HTML"],
                                   "priority": "low", "effort": "low",
                                   "expected_benefit": "Clarifies whether a real rendering fix is needed",
                                   "verification": "Manual inspection"},
                provenance={"skill": "crawl-render-audit", "script": "analyze_rendering.py",
                            "rule_id": "render-gap-unconfirmed", "tier": "rendering_headless_browser"},
            ))

        if confirmed_gap_pages:
            # Evidence-completeness: confidence reflects how many of the CANDIDATE
            # gap pages we were actually able to render and confirm (bounded by
            # MAX_RENDERED_PAGES), not just how many came back confirmed among
            # those we could try (Round-3 review item 1).
            render_ratio = coverage_ratio(rendered_count, len(heuristic_gap_pages))
            findings.append(make_finding(
                category="ai_discoverability", finding_type="defect",
                severity=step_down_severity("high", render_ratio),
                status="confirmed", confidence=0.9,
                title="Content requires JavaScript rendering to appear",
                root_cause="Raw HTML is near-empty but headless rendering reveals substantial content"
                           + ("" if render_ratio >= 0.999 else
                              f" (confirmed via headless rendering on {rendered_count} of "
                              f"{len(heuristic_gap_pages)} candidate pages; the rest were not rendered "
                              "within this run's budget)"),
                evidence=[{"type": "render_gap", "description": "Rendered content is substantial; static fetch is not",
                           "urls": confirmed_gap_pages[: limits.MAX_RETAINED_RENDERED_PAGES]}],
                suggested_action={
                    "summary": "Server-side render or pre-render key content",
                    "steps": ["Add SSR or static generation for key pages"],
                    "priority": "high", "effort": "high",
                    "expected_benefit": "Content becomes machine-readable without JS",
                    "verification": "Confirm raw HTML contains key facts",
                },
                provenance={"skill": "crawl-render-audit", "script": "analyze_rendering.py",
                            "rule_id": "render-gap", "tier": "rendering_headless_browser"},
            ))
    elif heuristic_gap_pages:
        # No headless browser available: the heuristic alone can only suspect, not
        # confirm. A thin page that runs scripts may be built by JavaScript or may
        # simply be short (a splash page, a chooser, a page of links), so the raw
        # HTML is searched for independent signs of client-side rendering
        # (_client_render_signs). With none, the page is reported only as
        # insufficient evidence. With one, the gap is a suspected medium defect;
        # with two or more independent signs it is high, since each sign alone has
        # innocent explanations but together they describe an app shell.
        by_url = {p.url: p for p in artifacts.pages}
        signs = {u: _client_render_signs(by_url[u], u in js_required_pages) for u in heuristic_gap_pages}
        shells = [u for u in heuristic_gap_pages if signs[u]]
        thin = [u for u in heuristic_gap_pages if not signs[u]]
        if shells:
            evidence = [{"type": "render_gap", "description": "Static fetch returns near-empty content",
                         "urls": shells[:10]}]
            for kind, description in _SIGN_TEXT.items():
                urls = [u for u in shells if kind in signs[u]]
                if urls:
                    evidence.append({"type": kind, "description": description, "urls": urls[:10]})
            strongest = max(len(signs[u]) for u in shells)
            severity = "high" if strongest >= 2 else "medium"
            findings.append(make_finding(
                category="ai_discoverability", finding_type="defect", severity=severity,
                status="suspected", confidence=0.75 if strongest >= 2 else 0.6,
                title="Content appears to require JavaScript rendering",
                root_cause="Raw HTML shows near-empty visible content, and the page carries signs of client-side "
                           "rendering (" + ", ".join(sorted({_SIGN_LABEL[k] for u in shells for k in signs[u]})) + ")",
                evidence=evidence,
                suggested_action={
                    "summary": "Server-side render or pre-render key content",
                    "steps": ["Add SSR or static generation for key pages",
                              "Re-run this audit with a headless-rendering capability to confirm"],
                    "priority": severity, "effort": "high",
                    "expected_benefit": "Content becomes machine-readable without JS",
                    "verification": "Confirm raw HTML contains key facts",
                },
                provenance={"skill": "crawl-render-audit", "script": "analyze_rendering.py",
                            "rule_id": "render-gap", "tier": "rendering_gap_heuristic"},
            ))
        if thin:
            findings.append(apply_invariant_i1(make_finding(
                category="ai_discoverability", finding_type="proactive_improvement", severity="low",
                status="insufficient_evidence", confidence=0.3,
                title="Some near-empty pages could not be confirmed as rendering gaps",
                root_cause="These pages run scripts and carry little text in their raw HTML, but show no other sign "
                           "of client-side rendering (no app mount point, framework bundle, serialized page state "
                           "or JavaScript-required notice); they may simply be short pages",
                evidence=[{"type": "render_gap_unconfirmed",
                           "description": "Little raw-HTML text and no sign of client-side rendering",
                           "urls": thin[:10]}],
                suggested_action={"summary": "Open these pages with JavaScript turned off and check that the "
                                             "content visitors need is still there",
                                  "steps": ["Compare each page in a browser with and without JavaScript",
                                            "If content disappears, server-render or pre-render it"],
                                  "priority": "low", "effort": "low",
                                  "expected_benefit": "Clarifies whether a real rendering fix is needed",
                                  "verification": "Manual inspection"},
                provenance={"skill": "crawl-render-audit", "script": "analyze_rendering.py",
                            "rule_id": "render-gap-unconfirmed", "tier": "rendering_gap_heuristic"},
            )))

    return skill_result(
        "crawl-render-audit", findings=findings,
        metrics={"rendered_pages": rendered_count, "raw_rendered_gap_pages": confirmed_gap_pages or heuristic_gap_pages,
                 "rendering_mode": "headless_browser" if headless_available else "heuristic_only",
                 "noscript_js_required_pages": len(js_required_pages),
                 "noscript_fallback_pages": noscript_fallback_pages[:10]},
    )
