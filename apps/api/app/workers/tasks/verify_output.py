from pathlib import Path
from app.workers.celery_app import celery_app
from app.workers.tasks.common import load, update
from app.processing.images.scanner import scan_image
from app.processing.pdf.scanner import scan_pdf
from app.processing.office.scanner import scan_office
@celery_app.task(name='verify_output')
def verify_output_task(job_id:str, file_path:str, options:dict|None=None):
    path=Path(file_path); job=load(job_id)
    try:
        ext=path.suffix.lower(); update(job,status='processing',progress=40,current_step='Verification scan')
        if ext in ['.jpg','.jpeg','.png','.webp','.heic','.tif','.tiff']: report=scan_image(path)
        elif ext=='.pdf': report=scan_pdf(path)
        elif ext in ['.docx','.xlsx','.pptx']: report=scan_office(path)
        else: raise ValueError('Unsupported verification file type')
        update(job,status='completed',progress=100,current_step='Verification complete',report=report)
    except Exception as e: update(job,status='failed',progress=100,current_step='Failed',error_message=str(e))
    return job_id
