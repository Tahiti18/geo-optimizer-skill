"""Celery application.

Broker/backend default to Redis. ``task_always_eager`` is driven by
``GR_CELERY_EAGER`` so tests and single-process dev can run tasks inline with
no broker. Production runs ``celery -A geoready_platform.workers.celery_app worker``.
"""

from __future__ import annotations

from celery import Celery

from geoready_platform.config import get_settings

settings = get_settings()

celery_app = Celery(
    "geoready_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["geoready_platform.workers.audit_task"],
)

celery_app.conf.update(
    task_always_eager=settings.celery_eager,
    task_eager_propagates=settings.celery_eager,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # I/O-bound audits: fair dispatch
    task_track_started=True,
)
