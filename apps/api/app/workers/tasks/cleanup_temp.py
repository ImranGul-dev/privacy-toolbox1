from app.workers.celery_app import celery_app
from app.services.storage_service import cleanup_expired
@celery_app.task(name='cleanup_temp')
def cleanup_temp_task(): cleanup_expired(); return True
