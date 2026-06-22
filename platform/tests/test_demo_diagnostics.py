"""Offline tests for LIVE_ONLY diagnostics + the unimplemented fallback hook."""

from __future__ import annotations

import pytest

from probe_eval import fallback
from probe_eval.diagnostics import MODE_LIVE_ONLY, RunDiagnostics, would_fallback


def test_mode_is_live_only():
    assert MODE_LIVE_ONLY == "LIVE_ONLY"
    assert RunDiagnostics().mode == "LIVE_ONLY"


def test_would_fallback_timeout_takes_priority():
    wf, reason = would_fallback(errored=True, timed_out=True, answered_count=0,
                                web_model=True, competitor_count=0, som_denominator=0)
    assert wf is True and reason == "timeout"


def test_would_fallback_provider_error():
    wf, reason = would_fallback(errored=True, timed_out=False, answered_count=1,
                                web_model=True, competitor_count=2, som_denominator=1)
    assert wf is True and reason == "provider_error"


def test_would_fallback_no_answers():
    wf, reason = would_fallback(errored=False, timed_out=False, answered_count=0,
                                web_model=True, competitor_count=0, som_denominator=0)
    assert wf is True and reason == "no_answers"


def test_would_fallback_no_discovery_signal():
    wf, reason = would_fallback(errored=False, timed_out=False, answered_count=2,
                                web_model=True, competitor_count=1, som_denominator=0)
    assert wf is True and reason == "no_discovery_signal"


def test_would_fallback_citation_gap_only_for_web_model():
    wf, reason = would_fallback(errored=False, timed_out=False, answered_count=2,
                                web_model=True, competitor_count=0, som_denominator=2)
    assert wf is True and reason == "citation_gap_no_competitors"
    # Non-web model: empty competitors is expected, not a fallback trigger.
    wf2, _ = would_fallback(errored=False, timed_out=False, answered_count=2,
                            web_model=False, competitor_count=0, som_denominator=2)
    assert wf2 is False


def test_would_fallback_healthy_run():
    wf, reason = would_fallback(errored=False, timed_out=False, answered_count=2,
                                web_model=True, competitor_count=3, som_denominator=2)
    assert wf is False and reason == ""


def test_fallback_is_unimplemented_and_loud():
    with pytest.raises(NotImplementedError):
        fallback.load_golden("slack")
