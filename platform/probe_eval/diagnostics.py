"""Private diagnostics for LIVE_ONLY probe runs. Pure, no I/O.

The goal of LIVE_ONLY mode is to measure, without hiding anything, how often a
live run fails or degrades. ``would_fallback`` records *whether* a golden
fallback would have been used — but in LIVE_ONLY mode no fallback is executed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

MODE_LIVE_ONLY = "LIVE_ONLY"


@dataclass
class RunDiagnostics:
    """One probe run's diagnostics (a business at a given repeat)."""

    mode: str = MODE_LIVE_ONLY
    business_id: str = ""
    repeat: int = 1
    provider: str = ""
    model: str = ""
    prompt_count: int = 0
    answered_count: int = 0
    citation_count: int = 0
    total_latency_ms: int = 0
    per_prompt_latency_ms: list[int] = field(default_factory=list)
    timeout_count: int = 0
    error_count: int = 0
    error_reasons: list[str] = field(default_factory=list)
    total_cost: float | None = None  # None = cost not reported by provider
    would_fallback: bool = False
    would_fallback_reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def would_fallback(
    *,
    errored: bool,
    timed_out: bool,
    answered_count: int,
    web_model: bool,
    competitor_count: int,
    som_denominator: int,
) -> tuple[bool, str]:
    """Pure heuristic: would a golden fallback have been needed for this run?

    LOGGED ONLY — never acted upon in LIVE_ONLY mode. A run "would fall back" if
    it failed or degraded enough that an external demo couldn't rely on it.
    """
    if timed_out:
        return True, "timeout"
    if errored:
        return True, "provider_error"
    if answered_count == 0:
        return True, "no_answers"
    if som_denominator == 0:
        return True, "no_discovery_signal"  # no scoreable discovery prompts answered
    if web_model and competitor_count == 0:
        return True, "citation_gap_no_competitors"
    return False, ""
