"""Keep the test suite offline.

Fixture sites declare real-looking sameAs profiles (twitter.com, linkedin.com).
An audit of them must never reach those hosts, nor the PageSpeed Insights API, so
both third-party lookups are switched off for every test. Tests of the lookups
themselves re-enable them with monkeypatch and inject a fake transport.
"""
import pytest


@pytest.fixture(autouse=True)
def _no_third_party_lookups(monkeypatch):
    monkeypatch.setenv("OFF_SITE_LOOKUP", "0")
    monkeypatch.setenv("FIELD_VITALS_LOOKUP", "0")
    monkeypatch.delenv("PAGESPEED_API_KEY", raising=False)
