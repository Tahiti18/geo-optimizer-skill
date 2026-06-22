r"""Summarize recent LIVE_ONLY diagnostics runs — EVAL TOOLING ONLY (operator).

Reads the gitignored history folder written by _demo_live and prints a trend +
a plain fallback recommendation.

Run from repo root:
    $env:PYTHONPATH = "$PWD\platform;$PWD\src"
    python -m probe_eval._diagnostics_history --last 10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from probe_eval import history


def main() -> int:
    ap = argparse.ArgumentParser(description="Summarize recent LIVE_ONLY diagnostics runs")
    ap.add_argument("--last", type=int, default=None, help="only summarize the most recent N runs")
    ap.add_argument("--dir", type=str, default=None, help="history dir (default: gitignored .diagnostics_history)")
    args = ap.parse_args()

    directory = Path(args.dir) if args.dir else history.history_dir()
    runs = history.load_runs(directory)
    summary = history.summarize(runs, last_n=args.last)

    print(f"history dir: {directory}", flush=True)
    print(f"runs on disk: {len(runs)}", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    if summary.get("runs_analyzed", 0) == 0:
        print("No runs recorded yet — run `python -m probe_eval._demo_live` first.", flush=True)
    else:
        verdict = "INDICATED" if summary["fallback_indicated"] else "not indicated"
        print(f"\nGolden fallback: {verdict} — {summary['reason']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
