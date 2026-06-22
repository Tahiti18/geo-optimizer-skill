r"""LIVE_ONLY demo-readiness runner — EVAL TOOLING ONLY (operator-run).

Purpose: measure, without hiding anything, how often a LIVE probe run fails or
degrades — failure rate, latency, citation/competitor gaps, cost, and run-to-run
variance — BEFORE deciding whether external demos need a golden fallback.

- LIVE_ONLY: always calls the live web model; NO fallback is executed. When a run
  would have needed fallback, that is LOGGED only (see diagnostics.would_fallback
  and the unimplemented fallback.load_golden hook).
- Small/controlled by default: a few curated businesses, 2 prompts each (one
  discovery + one factual), 2 repeats, 20s per-call timeout.
- No secrets printed; no fixtures written; engine untouched; no new providers.

Run from repo root (operator session with OPENROUTER_API_KEY set):
    $env:PYTHONPATH = "$PWD\platform;$PWD\src"
    python -m probe_eval._demo_live
"""

from __future__ import annotations

import json
import statistics
import sys

from geoready_platform.services.probe import prompt_generator
from geoready_platform.services.probe.taxonomy import CATEGORY_BY_KEY

from probe_eval import diagnostics, metrics, openrouter_client
from probe_eval.harness import business_by_id, score_business

MODE = diagnostics.MODE_LIVE_ONLY
MODEL = "perplexity/sonar"      # web-grounded (returns citations) — single model, no abstraction
WEB_MODEL = True                # perplexity/sonar performs web search
DEMO_IDS = ["slack", "notion", "zephyrline-plumbing-austin"]  # strong, strong, fictional
DEFAULT_REPEATS = 2
TIMEOUT_SECONDS = 20.0


def _say(msg: str) -> None:
    print(msg, flush=True)


def _two_prompts(biz: dict) -> list:
    """One discovery (SoM) prompt + one factual prompt."""
    allp = prompt_generator.generate_prompts(
        name=biz["name"], category=biz.get("category"), city=biz.get("city"), max_prompts=8
    )
    discovery = next((p for p in allp if CATEGORY_BY_KEY[p.category].counts_for_share), None)
    factual = next((p for p in allp if CATEGORY_BY_KEY[p.category].counts_for_factual), None)
    return [p for p in (discovery, factual) if p is not None]


def _run_once(biz: dict, repeat: int) -> dict:
    responses = []
    latencies: list[int] = []
    costs: list[float] = []
    timeouts = errors = answered = citations = 0
    error_reasons: list[str] = []

    for gp in _two_prompts(biz):
        _say(f"    request [{gp.category}] (timeout {int(TIMEOUT_SECONDS)}s)...")
        pr, meta = openrouter_client.run_prompt_with_meta(gp.text, model=MODEL, timeout=TIMEOUT_SECONDS)
        latencies.append(meta.latency_ms)
        if meta.cost is not None:
            costs.append(meta.cost)
        if meta.timeout:
            timeouts += 1
        if meta.error:
            errors += 1
            error_reasons.append(meta.error)
            _say(f"      ERROR: {meta.error} ({meta.latency_ms}ms)")
        else:
            answered += 1 if (pr.text or "").strip() else 0
            citations += len(pr.citations)
            _say(f"      ok: {len(pr.text)} chars, {len(pr.citations)} citations, {meta.latency_ms}ms")
        responses.append(
            {"category_key": gp.category, "prompt": gp.text, "text": pr.text, "citations": pr.citations}
        )

    scored = score_business(biz, {"business_id": biz["id"], "responses": responses})
    wf, reason = diagnostics.would_fallback(
        errored=errors > 0 and timeouts == 0,
        timed_out=timeouts > 0,
        answered_count=answered,
        web_model=WEB_MODEL,
        competitor_count=len(scored["predicted_competitors"]),
        som_denominator=scored["share_denominator"],
    )

    diag = diagnostics.RunDiagnostics(
        mode=MODE, business_id=biz["id"], repeat=repeat, provider="openrouter", model=MODEL,
        prompt_count=len(responses), answered_count=answered, citation_count=citations,
        total_latency_ms=sum(latencies), per_prompt_latency_ms=latencies,
        timeout_count=timeouts, error_count=errors, error_reasons=error_reasons,
        total_cost=(round(sum(costs), 6) if costs else None),
        would_fallback=wf, would_fallback_reason=reason,
    )

    _say("    --- diagnostics ---")
    _say(json.dumps(diag.to_dict(), indent=2))
    _say(f"    result: SoM={scored['share_of_model']} (denom {scored['share_denominator']}), "
         f"competitors={scored['predicted_competitors']}, flags={scored['flags']}")
    if wf:
        _say(f"    would_fallback=TRUE ({reason}) — LIVE_ONLY: not falling back (hook unimplemented)")

    return {
        "diagnostics": diag.to_dict(),
        "share_of_model": scored["share_of_model"],
        "competitors": scored["predicted_competitors"],
        "flags": scored["flags"],
    }


def main() -> int:
    _say(f"=== LIVE_ONLY demo-readiness run | model={MODEL} | repeats={DEFAULT_REPEATS} ===")
    if not openrouter_client.available():
        _say("ERROR: OPENROUTER_API_KEY not set in this process environment.")
        return 2

    report = {"mode": MODE, "model": MODEL, "repeats": DEFAULT_REPEATS, "businesses": {}}
    all_runs: list[dict] = []

    for bid in DEMO_IDS:
        biz = business_by_id(bid)
        if biz is None:
            _say(f"skip: {bid} not found")
            continue
        _say(f"\n--- {biz['name']} ({biz['prominence_tier']}) ---")
        runs = [_run_once(biz, r + 1) for r in range(DEFAULT_REPEATS)]
        all_runs.extend(runs)
        stab = metrics.stability([
            {"share_of_model": r["share_of_model"], "competitors": r["competitors"], "flags": r["flags"]}
            for r in runs
        ])
        report["businesses"][bid] = {
            "tier": biz["prominence_tier"],
            "runs": runs,
            "variance": {
                "som_stddev": stab.som_stddev,
                "som_mean": stab.som_mean,
                "competitor_jaccard_median": stab.competitor_jaccard_median,
                "flag_persistence": stab.flag_persistence,
            },
        }

    # ── Aggregate (the actual goal: how often does LIVE fail/degrade?) ───────
    total = len(all_runs)
    fallback_needed = sum(1 for r in all_runs if r["diagnostics"]["would_fallback"])
    all_latencies = [lat for r in all_runs for lat in r["diagnostics"]["per_prompt_latency_ms"]]
    citation_gap = sum(1 for r in all_runs if r["diagnostics"]["citation_count"] == 0)
    costs = [r["diagnostics"]["total_cost"] for r in all_runs if r["diagnostics"]["total_cost"] is not None]

    report["aggregate"] = {
        "total_runs": total,
        "would_fallback_rate": round(fallback_needed / total, 4) if total else 0.0,
        "avg_call_latency_ms": int(statistics.mean(all_latencies)) if all_latencies else 0,
        "median_call_latency_ms": int(statistics.median(all_latencies)) if all_latencies else 0,
        "citation_gap_run_rate": round(citation_gap / total, 4) if total else 0.0,
        "total_cost_usd": round(sum(costs), 6) if costs else None,
        "cost_reported": bool(costs),
    }

    _say("\n=== AGGREGATE ===")
    _say(json.dumps(report["aggregate"], indent=2))
    _say("\n=== FULL REPORT (JSON) ===")
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
