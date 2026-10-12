"""test_corroboration_quality.py -- Priority item 4: external corroboration must
compare claim VALUES against results (not just "a search returned something"),
must never conflate "not checked" with "not found", must record the actual
queries issued, and must represent conflicting claims explicitly rather than as
a vague generic warning.

search_provider.search is monkeypatched directly (no real network call), since
corroborate_claims.py depends on it via `from search_provider import search`.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _rel in (
    "common", "skills/audit-orchestrator/scripts", "skills/crawl-render-audit/scripts",
    "skills/freshness-corroboration/scripts", "skills/engagement-audit/scripts",
):
    sys.path.insert(0, os.path.join(_ROOT, _rel))

from constants import DEFAULT_LIMITS
from models import AuditArtifacts, make_deadline, intermediate_artifact
import corroborate_claims as cc_module
from corroborate_claims import corroborate_claims, _compare_claim_to_results

_LIMITS = DEFAULT_LIMITS


def _empty_artifacts():
    return AuditArtifacts(
        site_url="https://example.com/", normalized_origin="https://example.com",
        pages=(), robots_data={}, llms_txt_data={}, sitemap_data={},
        acquisition_metadata={}, warnings=(),
    )


def _identity(confidence=0.9):
    return intermediate_artifact("entity_identity", status="success",
                                  data={"confidence": confidence, "canonical_name": "Example Brand"})


# ---------------------------------------------------------------------------
# Direct unit tests of the comparison function -- no search provider needed
# ---------------------------------------------------------------------------

def test_matching_phone_number_is_corroborated_regardless_of_formatting():
    fact = {"type": "contact", "value": "(555) 123-4567"}
    results = [{"title": "Contact us", "snippet": "Call 555-123-4567 for support", "url": "https://x.com"}]
    outcome, detail = _compare_claim_to_results(fact, results)
    assert outcome == "corroborated"


def test_different_phone_number_is_contradicted_not_confirmed_defect():
    fact = {"type": "contact", "value": "555-123-4567"}
    results = [{"title": "Old listing", "snippet": "Reach us at 555-999-0000", "url": "https://y.com"}]
    outcome, detail = _compare_claim_to_results(fact, results)
    assert outcome == "contradicted"
    assert detail["claim_value"] == "555-123-4567"
    assert detail["other_value"].strip() == "555-999-0000"


def test_no_matching_or_conflicting_value_is_not_found_not_contradicted():
    fact = {"type": "contact", "value": "555-123-4567"}
    results = [{"title": "Unrelated", "snippet": "This page has no phone numbers at all", "url": "https://z.com"}]
    outcome, detail = _compare_claim_to_results(fact, results)
    assert outcome == "not_found"
    assert detail is None


def test_empty_results_is_not_found_never_a_fabricated_contradiction():
    fact = {"type": "price", "value": "$49.99"}
    outcome, detail = _compare_claim_to_results(fact, [])
    assert outcome == "not_found"


# ---------------------------------------------------------------------------
# Full corroborate_claims(): not-checked vs not-found, query recording,
# explicit conflict representation
# ---------------------------------------------------------------------------

def test_unconfigured_provider_is_not_checked_never_not_found(monkeypatch):
    monkeypatch.delenv("SEARCH_API_URL", raising=False)
    facts = intermediate_artifact("important_facts", data={"facts": [
        {"type": "contact", "value": "555-123-4567", "source": "https://example.com/"}
    ]})
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(_LIMITS), _LIMITS)
    assert result["status"] == "insufficient_evidence"
    assert result["metrics"]["provider_configured"] is False
    # Explicitly zero claims_not_found -- nothing was actually searched, so
    # "not found" would be a false claim here.
    assert result["metrics"]["claims_checked"] == 0


def test_configured_provider_records_actual_queries_issued(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "https://fake-search.example/api")
    facts = intermediate_artifact("important_facts", data={"facts": [
        {"type": "contact", "value": "555-123-4567", "source": "https://example.com/"},
    ]})

    def fake_search(query, max_results, timeout_s):
        return [{"title": "Contact", "snippet": "Call 555-123-4567", "url": "https://example.com/contact"}]

    monkeypatch.setattr(cc_module, "search", fake_search)
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(_LIMITS), _LIMITS)
    assert result["metrics"]["claims_corroborated"] == 1
    queries = result["metrics"]["queries_issued"]
    assert len(queries) == 1
    assert "Example Brand" in queries[0]["query"] and "555-123-4567" in queries[0]["query"]
    assert queries[0]["outcome"] == "corroborated"


def test_conflicting_claim_is_represented_explicitly_as_suspected_not_confirmed(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "https://fake-search.example/api")
    facts = intermediate_artifact("important_facts", data={"facts": [
        {"type": "contact", "value": "555-123-4567", "source": "https://example.com/"},
    ]})

    def fake_search(query, max_results, timeout_s):
        return [{"title": "Old directory listing", "snippet": "Phone: 555-999-0000",
                  "url": "https://directory.example/old"}]

    monkeypatch.setattr(cc_module, "search", fake_search)
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(_LIMITS), _LIMITS)
    assert result["metrics"]["claims_contradicted"] == 1
    finding = result["findings"][0]
    assert finding["status"] == "suspected"  # never "confirmed" from a single external mismatch
    assert "555-123-4567" in finding["evidence"][0]["description"]
    assert "555-999-0000" in finding["evidence"][0]["description"]
    assert finding["evidence"][0]["urls"] == ["https://directory.example/old"]


def test_not_found_is_tracked_distinctly_from_corroborated_and_contradicted(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "https://fake-search.example/api")
    facts = intermediate_artifact("important_facts", data={"facts": [
        {"type": "contact", "value": "555-123-4567", "source": "https://example.com/"},
    ]})

    def fake_search(query, max_results, timeout_s):
        return [{"title": "Unrelated page", "snippet": "No contact info here", "url": "https://other.example/"}]

    monkeypatch.setattr(cc_module, "search", fake_search)
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(_LIMITS), _LIMITS)
    assert result["metrics"]["claims_not_found"] == 1
    assert result["metrics"]["claims_corroborated"] == 0
    assert result["metrics"]["claims_contradicted"] == 0
    assert result["findings"] == []  # "not found" alone is not a defect


def test_provider_failure_mid_run_is_insufficient_evidence_not_a_confirmed_absence(monkeypatch):
    monkeypatch.setenv("SEARCH_API_URL", "https://fake-search.example/api")
    facts = intermediate_artifact("important_facts", data={"facts": [
        {"type": "contact", "value": "555-123-4567", "source": "https://example.com/"},
    ]})

    def failing_search(query, max_results, timeout_s):
        from search_provider import SearchProviderError
        raise SearchProviderError("simulated outage")

    monkeypatch.setattr(cc_module, "search", failing_search)
    result = corroborate_claims(facts, _identity(), _empty_artifacts(), make_deadline(_LIMITS), _LIMITS)
    assert result["status"] == "insufficient_evidence"


if __name__ == "__main__":
    import pytest
    ran = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "monkeypatch" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
                mp = pytest.MonkeyPatch()
                try:
                    fn(mp)
                finally:
                    mp.undo()
            else:
                fn()
            ran += 1
            print(f"OK: {name}")
    print(f"{ran} tests passed")
