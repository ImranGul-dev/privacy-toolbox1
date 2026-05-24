from pathlib import Path
from app.workers.celery_app import celery_app
from app.workers.tasks.common import load, update, output_for
from app.services import storage_service as st
from app.processing.pdf.scanner import scan_pdf
@celery_app.task(name='scan_pdf')
def scan_pdf_task(job_id:str, file_path:str, options:dict|None=None):
    options=options or {}; path=Path(file_path); job=load(job_id)
    try:
        update(job,status='processing',progress=35,current_step='Processing')
        report=scan_pdf(path); update(job,status="completed",progress=100,current_step="PDF scan complete",report=report)
    except Exception as e:
        update(job,status='failed',progress=100,current_step='Failed',error_message=str(e))
    return job_id
