"""Fix adapter: expose the engine's structured fixes as ``FixProposal`` dicts.

Phase 0 finding: ``geo_optimizer.core.fixer`` ALREADY returns structured
``FixPlan``/``FixItem`` dataclasses and does NOT write to disk (disk writing
lives in the CLI layer). The roadmap's planned "refactor fixer to stop writing
files" is therefore unnecessary — we adapt the existing structured output here
instead of modifying the engine, honoring the "do not rewrite working
components" rule.

This adapter is intentionally minimal in Phase 0: the AI fix *engine* that
fills these proposals arrives in Phase 1. Here we only normalize the engine's
deterministic fixes into the platform's proposal shape so the data contract is
fixed early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FixProposal:
    """Platform-shaped fix proposal (superset of the engine's FixItem)."""

    category: str
    description: str
    content: str
    file_name: str
    action: str  # create | append | snippet
    ai_generated: bool = False  # always False in Phase 0 (deterministic engine fixes)


@dataclass
class FixProposalSet:
    url: str
    score_before: int
    score_estimated_after: int
    proposals: list[FixProposal] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def build_fix_proposals(url: str, audit_result: Any | None = None, only: set[str] | None = None) -> FixProposalSet:
    """Run the engine's fix generator and map FixItems -> FixProposals.

    ``audit_result`` may be a pre-computed engine ``AuditResult`` to avoid a
    second audit. Passing ``None`` lets the engine audit internally.
    """
    from geo_optimizer.core.fixer import run_all_fixes

    plan = run_all_fixes(url, audit_result=audit_result, only=only)
    proposals = [
        FixProposal(
            category=item.category,
            description=item.description,
            content=item.content,
            file_name=item.file_name,
            action=item.action,
            ai_generated=False,
        )
        for item in plan.fixes
    ]
    return FixProposalSet(
        url=plan.url,
        score_before=plan.score_before,
        score_estimated_after=plan.score_estimated_after,
        proposals=proposals,
        skipped=list(plan.skipped),
    )
