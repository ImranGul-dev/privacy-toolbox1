from app.workers.celery_app import celery_app
from app.processing.c2pa.detector import detect_c2pa
@celery_app.task(name='detect_c2pa')
def detect_c2pa_task(path:str): return detect_c2pa(path)
