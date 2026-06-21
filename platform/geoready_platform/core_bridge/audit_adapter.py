"""Audit adapter: run the engine, return a JSON-safe payload + signal rows.

Wraps ``geo_optimizer.core.audit.run_full_audit_async`` (async, parallel fetch)
and serializes the returned ``AuditResult`` dataclass with ``dataclasses.asdict``
(all nested results are dataclasses, so this is total and lossless).

The audit's per-category breakdown is mapped to ``entity_signal`` rows: the
audit is demoted to *one signal source* feeding the entity, per the roadmap.
"""

from __future__ import annotations

import asyncio
import dataclasses
from dataclasses import dataclass, field
from typing import Any

from geoready_platform.config import get_settings


@dataclass
class AuditPayload:
    """Normalized, JSON-safe result of one audit run."""

    url: str
    score: int
    band: str
    score_breakdown: dict[str, int]
    full_result: dict[str, Any]
    signals: list[dict[str, Any]] = field(default_factory=list)


def _to_jsonable(value: Any) -> Any:
    """Best-effort conversion of engine objects to JSON-safe primitives."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)  # datetimes, enums, etc. — degrade gracefully


def _build_signals(breakdown: dict[str, int], result_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Map the audit's category breakdown into entity-signal rows."""
    signals: list[dict[str, Any]] = []
    for category, score in (breakdown or {}).items():
        detail = result_dict.get(category)
        signals.append(
            {
                "source": "website_audit",
                "signal_type": category,
                "value": {"score": score, "detail": detail if isinstance(detail, dict) else None},
            }
        )
    return signals


async def run_audit_async(url: str) -> AuditPayload:
    """Run the engine audit with a hard timeout and return a normalized payload."""
    from geo_optimizer.core.audit import run_full_audit_async

    settings = get_settings()
    result = await asyncio.wait_for(run_full_audit_async(url), timeout=settings.audit_timeout_seconds)

    result_dict = _to_jsonable(result)
    breakdown = result_dict.get("score_breakdown") or {}
    return AuditPayload(
        url=getattr(result, "url", url),
        score=int(getattr(result, "score", 0) or 0),
        band=str(getattr(result, "band", "critical") or "critical"),
        score_breakdown=breakdown,
        full_result=result_dict,
        signals=_build_signals(breakdown, result_dict),
    )


def run_audit(url: str) -> AuditPayload:
    """Synchronous convenience wrapper around :func:`run_audit_async`."""
    return asyncio.run(run_audit_async(url))
