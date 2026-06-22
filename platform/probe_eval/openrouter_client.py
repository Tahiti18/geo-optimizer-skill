"""Minimal OpenRouter client — EVAL TOOLING ONLY.

Not part of the product and not a provider abstraction. It exists so the
evaluation harness can record real responses for live testing. OpenRouter is
OpenAI-compatible, so this is a single chat-completions POST.

SECURITY: the API key is read from OPENROUTER_API_KEY at call time and used only
in the Authorization header. It is never printed, logged, returned, or written
to any fixture. Do not change that.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from geoready_platform.core_bridge.probe_adapter import ProbeResponse

_URL = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT = 60


@dataclass
class RunMeta:
    """Per-call diagnostics. No secrets. Used by the LIVE_ONLY demo runner."""

    latency_ms: int = 0
    timeout: bool = False
    status_code: int | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float | None = None  # USD, only when OpenRouter returns it
    error: str | None = None
    extra: dict = field(default_factory=dict)


def available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _extract_citations(data: dict, message: dict) -> list[str]:
    citations: list[str] = list(data.get("citations") or [])
    for ann in message.get("annotations") or []:
        url = (ann.get("url_citation") or {}).get("url") if isinstance(ann, dict) else None
        if url and url not in citations:
            citations.append(url)
    for sr in data.get("search_results") or []:
        url = sr.get("url") if isinstance(sr, dict) else None
        if url and url not in citations:
            citations.append(url)
    return citations


def run_prompt_with_meta(prompt: str, *, model: str, timeout: float = _TIMEOUT) -> tuple[ProbeResponse, RunMeta]:
    """Query OpenRouter and return (ProbeResponse, RunMeta).

    Captures latency, timeout status, HTTP status, token usage, and cost (when
    available). Requests ``usage.include`` so OpenRouter returns cost. Never
    leaks the key — error strings carry only exception type/message.
    """
    import httpx

    meta = RunMeta()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        meta.error = "OPENROUTER_API_KEY not set"
        return ProbeResponse(prompt=prompt, provider="openrouter", model=model, text="", error=meta.error), meta

    t0 = time.perf_counter()
    try:
        resp = httpx.post(
            _URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "usage": {"include": True},  # ask OpenRouter to return cost
            },
            timeout=httpx.Timeout(timeout),
        )
        meta.latency_ms = int((time.perf_counter() - t0) * 1000)
        meta.status_code = resp.status_code
        resp.raise_for_status()
        data = resp.json()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        usage = data.get("usage") or {}
        meta.prompt_tokens = int(usage.get("prompt_tokens") or 0)
        meta.completion_tokens = int(usage.get("completion_tokens") or 0)
        cost = usage.get("cost")
        meta.cost = float(cost) if isinstance(cost, (int, float)) else None
        pr = ProbeResponse(
            prompt=prompt,
            provider="openrouter",
            model=data.get("model", model),
            text=message.get("content") or "",
            citations=_extract_citations(data, message),
        )
        return pr, meta
    except httpx.TimeoutException as exc:
        meta.latency_ms = int((time.perf_counter() - t0) * 1000)
        meta.timeout = True
        meta.error = f"{type(exc).__name__}: {exc}"
        return ProbeResponse(prompt=prompt, provider="openrouter", model=model, text="", error=meta.error), meta
    except Exception as exc:  # noqa: BLE001 — never leak key; report type/message only
        meta.latency_ms = int((time.perf_counter() - t0) * 1000)
        meta.error = f"{type(exc).__name__}: {exc}"
        return ProbeResponse(prompt=prompt, provider="openrouter", model=model, text="", error=meta.error), meta


def run_prompt(prompt: str, *, model: str, timeout: float = _TIMEOUT) -> ProbeResponse:
    """Backward-compatible wrapper returning only the ProbeResponse."""
    pr, _meta = run_prompt_with_meta(prompt, model=model, timeout=timeout)
    return pr
