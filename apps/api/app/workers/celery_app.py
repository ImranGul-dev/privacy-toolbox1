from __future__ import annotations

from celery import Celery
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
    task_time_limit=20 * 60,
    task_soft_time_limit=18 * 60,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_transport_options={'visibility_timeout': 60 * 60},
    beat_schedule={
        'cleanup-expired-uploads-and-jobs-every-minute': {
            'task': 'cleanup_temp',
            'schedule': 60.0,
        }
    },
)
