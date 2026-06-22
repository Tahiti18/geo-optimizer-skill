"""Local LIVE_ONLY diagnostics history — EVAL TOOLING ONLY (operator/internal).

Persists one summary file per ``_demo_live`` run into a gitignored folder so we
can track reliability over time and decide, with data, whether golden fallback
is ever needed. Pure/derived from the run report — no network, no engine touch,
nothing committed.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
_DEFAULT_DIR = Path(__file__).parent / ".diagnostics_history"


def history_dir() -> Path:
    """Gitignored storage dir; overridable via GR_DIAG_HISTORY_DIR (tests use tmp)."""
    override = os.environ.get("GR_DIAG_HISTORY_DIR")
    return Path(override) if override else _DEFAULT_DIR


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(Path(__file__).resolve().parent),
        )
        return out.stdout.strip() or None if out.returncode == 0 else None
    except Exception:  # noqa: BLE001 — git absence must never break recording
        return None


def _safe_rate(numer: int, denom: int) -> float:
    return round(numer / denom, 4) if denom else 0.0


def build_record(report: dict) -> dict:
    """Derive a flat summary record from a _demo_live report dict.

    Derives timeout_rate/error_rate from per-run diagnostics so no new
    measurement is needed elsewhere.
    """
    businesses = report.get("businesses", {})
    agg = report.get("aggregate", {})

    total_prompts = timeouts = errors = 0
    som_stddevs: list[float] = []
    per_business_variance: dict[str, float | None] = {}
    for bid, b in businesses.items():
        for run in b.get("runs", []):
            d = run.get("diagnostics", {})
            total_prompts += int(d.get("prompt_count") or 0)
            timeouts += int(d.get("timeout_count") or 0)
            errors += int(d.get("error_count") or 0)
        sd = (b.get("variance") or {}).get("som_stddev")
        per_business_variance[bid] = sd
        if isinstance(sd, (int, float)):
            som_stddevs.append(float(sd))

    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": report.get("mode", "LIVE_ONLY"),
        "model": report.get("model", ""),
        "business_ids": list(businesses.keys()),
        "repeats": report.get("repeats"),
        "total_runs": agg.get("total_runs", 0),
        "would_fallback_rate": agg.get("would_fallback_rate", 0.0),
        "timeout_rate": _safe_rate(timeouts, total_prompts),
        "error_rate": _safe_rate(errors, total_prompts),
        "citation_gap_run_rate": agg.get("citation_gap_run_rate", 0.0),
        "avg_call_latency_ms": agg.get("avg_call_latency_ms", 0),
        "median_call_latency_ms": agg.get("median_call_latency_ms", 0),
        "total_cost_usd": agg.get("total_cost_usd"),
        "cost_reported": agg.get("cost_reported", False),
        "som_variance": {"per_business": per_business_variance,
                         "mean_som_stddev": round(statistics.mean(som_stddevs), 4) if som_stddevs else None},
        "git_commit": _git_commit(),
    }


def record_run(report: dict, *, directory: Path | None = None) -> Path:
    """Write one summary JSON file for this run. Returns the path."""
    directory = directory or history_dir()
    directory.mkdir(parents=True, exist_ok=True)
    record = build_record(report)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{ts}-{uuid.uuid4().hex[:6]}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


def load_runs(directory: Path | None = None) -> list[dict]:
    """Load all recorded runs, sorted ascending by timestamp."""
    directory = directory or history_dir()
    if not directory.exists():
        return []
    runs = []
    for p in directory.glob("*.json"):
        try:
            runs.append(json.loads(p.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            continue
    runs.sort(key=lambda r: r.get("timestamp_utc", ""))
    return runs


def _mean(xs: list[float]) -> float:
    return round(statistics.mean(xs), 4) if xs else 0.0


def summarize(runs: list[dict], *, last_n: int | None = None) -> dict:
    """Roll up recent runs into a trend + a plain fallback recommendation."""
    window = runs[-last_n:] if last_n else runs
    if not window:
        return {"runs_analyzed": 0, "fallback_indicated": False, "reason": "no runs recorded"}

    wf = [r.get("would_fallback_rate", 0.0) for r in window]
    to = [r.get("timeout_rate", 0.0) for r in window]
    er = [r.get("error_rate", 0.0) for r in window]
    cg = [r.get("citation_gap_run_rate", 0.0) for r in window]
    lat = [r.get("median_call_latency_ms", 0) for r in window]
    costs = [r["total_cost_usd"] for r in window if r.get("total_cost_usd") is not None]
    sds = [r["som_variance"]["mean_som_stddev"] for r in window
           if (r.get("som_variance") or {}).get("mean_som_stddev") is not None]

    mean_wf, max_wf = _mean(wf), round(max(wf), 4)
    fallback_indicated = max_wf > 0.0
    reason = (f"would_fallback observed (max {max_wf}) over {len(window)} run(s)"
              if fallback_indicated else
              f"would_fallback_rate 0 across {len(window)} run(s)")

    return {
        "runs_analyzed": len(window),
        "time_span": {"from": window[0].get("timestamp_utc"), "to": window[-1].get("timestamp_utc")},
        "would_fallback_rate": {"mean": mean_wf, "max": max_wf},
        "timeout_rate": {"mean": _mean(to), "max": round(max(to), 4)},
        "error_rate": {"mean": _mean(er), "max": round(max(er), 4)},
        "citation_gap_run_rate": {"mean": _mean(cg), "max": round(max(cg), 4)},
        "median_call_latency_ms": {"mean": int(_mean(lat)), "max": max(lat) if lat else 0},
        "cost_usd": {"sum": round(sum(costs), 6) if costs else None, "mean": round(_mean(costs), 6) if costs else None},
        "mean_som_stddev": _mean(sds) if sds else None,
        "fallback_indicated": fallback_indicated,
        "reason": reason,
    }
