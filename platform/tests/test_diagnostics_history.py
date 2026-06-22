"""Offline tests for the LIVE_ONLY diagnostics history (record/load/summarize)."""

from __future__ import annotations

from probe_eval import history


def _report(*, would_fallback_rate=0.0, citation_gap=0.0, timeouts=0, errors=0,
            prompts=4, cost=0.05, som_sd=0.1, median_latency=3900):
    """Build a minimal _demo_live-shaped report for one business, one run."""
    return {
        "mode": "LIVE_ONLY",
        "model": "perplexity/sonar",
        "repeats": 2,
        "businesses": {
            "slack": {
                "tier": "high",
                "runs": [
                    {"diagnostics": {"prompt_count": prompts, "timeout_count": timeouts,
                                     "error_count": errors}},
                ],
                "variance": {"som_stddev": som_sd},
            }
        },
        "aggregate": {
            "total_runs": 2,
            "would_fallback_rate": would_fallback_rate,
            "citation_gap_run_rate": citation_gap,
            "avg_call_latency_ms": 4065,
            "median_call_latency_ms": median_latency,
            "total_cost_usd": cost,
            "cost_reported": cost is not None,
        },
    }


def test_build_record_derives_rates():
    rec = history.build_record(_report(timeouts=1, errors=1, prompts=4))
    assert rec["timeout_rate"] == 0.25
    assert rec["error_rate"] == 0.25
    assert rec["mode"] == "LIVE_ONLY"
    assert rec["model"] == "perplexity/sonar"
    assert rec["som_variance"]["mean_som_stddev"] == 0.1
    assert rec["schema_version"] == history.SCHEMA_VERSION


def test_record_and_load_roundtrip(tmp_path):
    p = history.record_run(_report(), directory=tmp_path)
    assert p.exists()
    runs = history.load_runs(tmp_path)
    assert len(runs) == 1
    assert runs[0]["would_fallback_rate"] == 0.0


def test_load_runs_sorted_and_empty(tmp_path):
    assert history.load_runs(tmp_path) == []
    history.record_run(_report(cost=0.01), directory=tmp_path)
    history.record_run(_report(cost=0.02), directory=tmp_path)
    runs = history.load_runs(tmp_path)
    assert len(runs) == 2
    assert runs[0]["timestamp_utc"] <= runs[1]["timestamp_utc"]


def test_summarize_no_fallback_when_all_zero():
    runs = [history.build_record(_report(would_fallback_rate=0.0)) for _ in range(3)]
    s = history.summarize(runs)
    assert s["runs_analyzed"] == 3
    assert s["would_fallback_rate"]["max"] == 0.0
    assert s["fallback_indicated"] is False


def test_summarize_flags_fallback_when_any_nonzero():
    runs = [
        history.build_record(_report(would_fallback_rate=0.0)),
        history.build_record(_report(would_fallback_rate=0.33)),
    ]
    s = history.summarize(runs)
    assert s["fallback_indicated"] is True
    assert s["would_fallback_rate"]["max"] == 0.33


def test_summarize_last_n_window():
    runs = [history.build_record(_report(citation_gap=float(i) / 10)) for i in range(5)]
    s = history.summarize(runs, last_n=2)
    assert s["runs_analyzed"] == 2


def test_summarize_empty():
    s = history.summarize([])
    assert s["runs_analyzed"] == 0
    assert s["fallback_indicated"] is False
