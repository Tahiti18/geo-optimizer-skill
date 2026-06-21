"""Regression tests for competitor filtering (reference/social/directory sites)."""

from __future__ import annotations

from geoready_platform.services.probe.analysis import analyze_response
from geoready_platform.services.probe.non_competitor_domains import (
    filter_competitor_domains,
    is_non_competitor,
)


def test_known_reference_and_social_sites_are_not_competitors():
    for d in [
        "wikipedia.org", "en.wikipedia.org", "reddit.com", "yelp.com",
        "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
        "tripadvisor.com", "trustpilot.com", "amazon.com", "github.com",
        "g2.com", "bbb.org", "maps.google.com",
    ]:
        assert is_non_competitor(d), d


def test_institutional_tlds_are_not_competitors():
    assert is_non_competitor("austintexas.gov")
    assert is_non_competitor("mit.edu")
    assert is_non_competitor("army.mil")


def test_real_business_domains_pass_through():
    assert not is_non_competitor("globexplumbing.com")
    assert not is_non_competitor("joesplumbingaustin.com")


def test_filter_preserves_real_competitors_and_drops_references():
    domains = ["wikipedia.org", "globexplumbing.com", "yelp.com", "joesplumbing.com", "facebook.com"]
    assert filter_competitor_domains(domains) == ["globexplumbing.com", "joesplumbing.com"]


def test_analyze_response_excludes_reference_domains_from_competitors():
    sig = analyze_response(
        text="Top options include Globex Plumbing. See reviews on Yelp and their Facebook page.",
        citations=[
            "https://acme.com",
            "https://globexplumbing.com",
            "https://yelp.com/biz/globex",
            "https://facebook.com/globex",
            "https://en.wikipedia.org/wiki/Plumbing",
        ],
        name="Acme",
        domain="acme.com",
    )
    assert sig.competitor_domains == ["globexplumbing.com"]
    assert "yelp.com" not in sig.competitor_domains
    assert "facebook.com" not in sig.competitor_domains
    assert "en.wikipedia.org" not in sig.competitor_domains
