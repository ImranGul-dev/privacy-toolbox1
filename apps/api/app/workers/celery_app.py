from __future__ import annotations

from celery import Celery
from kombu import Queue
from app.core.config import settings

celery_app = Celery(
    'privacy_toolbox',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        'app.workers.tasks.process_tool_job',
        'app.workers.tasks.cleanup_temp',
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=settings.worker_hard_time_limit_seconds,
    task_soft_time_limit=settings.worker_soft_time_limit_seconds,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,
    task_default_queue=settings.celery_default_queue,
    task_queues=(
        Queue(settings.celery_default_queue),
        Queue(settings.celery_light_queue),
        Queue(settings.celery_heavy_queue),
    ),
    task_routes={
        'process_tool_job': {'queue': settings.celery_default_queue},
        'cleanup_temp': {'queue': settings.celery_default_queue},
    },
    broker_transport_options={'visibility_timeout': max(settings.worker_hard_time_limit_seconds * 3, 60 * 60)},
    result_expires=settings.job_ttl_minutes * 60,
    beat_schedule={
        'cleanup-expired-uploads-and-jobs-every-minute': {
            'task': 'cleanup_temp',
            'schedule': 60.0,
        }
    },
)
