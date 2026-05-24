from pathlib import Path
from app.workers.celery_app import celery_app
from app.workers.tasks.common import load, update, output_for
from app.services import storage_service as st
from app.processing.pdf.cleaner import clean_pdf
@celery_app.task(name='clean_pdf')
def clean_pdf_task(job_id:str, file_path:str, options:dict|None=None):
    options=options or {}; path=Path(file_path); job=load(job_id)
    try:
        update(job,status='processing',progress=35,current_step='Processing')
        out=output_for(job); report=clean_pdf(path,out,hard=options.get("hard",False)); token=st.make_download_token(out); update(job,status="completed",progress=100,current_step="Verified cleaned PDF",report=report,output_filename=out.name,download_token=token)
    except Exception as e:
        update(job,status='failed',progress=100,current_step='Failed',error_message=str(e))
    return job_id
