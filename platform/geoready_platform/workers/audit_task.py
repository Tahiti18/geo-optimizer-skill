"""The audit Celery task.

Thin wrapper: all logic lives in ``services.audits.execute_audit_job`` so it can
be unit-tested without a broker. A hard time limit bounds runaway audits in
addition to the per-audit asyncio timeout in the bridge.
"""

from __future__ import annotations

import logging

from geoready_platform.config import get_settings
from geoready_platform.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
_settings = get_settings()


@celery_app.task(
    name="geoready_platform.run_audit_job",
    bind=True,
    max_retries=0,
    time_limit=_settings.audit_timeout_seconds + 15,
    soft_time_limit=_settings.audit_timeout_seconds + 5,
)
def run_audit_job(self, job_id: str) -> str:  # noqa: ANN001 — Celery self
    from geoready_platform.services.audits import execute_audit_job

    logger.info("Running audit job %s", job_id)
    execute_audit_job(job_id)
    return job_id
