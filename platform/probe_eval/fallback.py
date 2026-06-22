"""Golden-fallback extension point — DELIBERATELY UNIMPLEMENTED.

LIVE_ONLY mode does not fall back. This module exists only as the clean hook for
a future "golden fixture" fallback (used to protect EXTERNAL demos once we know
the live failure rate). The demo runner may CHECK fallback availability and LOG
intent, but must never silently fall back while we are measuring live behavior.

To implement later: provide a GoldenFallback that loads a previously recorded
golden run for a business and returns its responses. Until then, load_golden
raises NotImplementedError so any accidental wiring fails loudly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class GoldenFallback(Protocol):
    """Future contract: return recorded responses for a business, or None."""

    def load(self, business_id: str) -> list[dict] | None:  # pragma: no cover - interface only
        ...


def load_golden(business_id: str) -> list[dict] | None:
    """Unimplemented on purpose (Phase: external-demo hardening).

    Raises NotImplementedError so LIVE_ONLY never accidentally falls back.
    """
    raise NotImplementedError(
        "Golden fallback is not implemented yet (LIVE_ONLY mode). "
        "This is the reserved extension point for external-demo hardening."
    )
