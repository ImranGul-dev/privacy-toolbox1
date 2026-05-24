from pathlib import Path
from app.workers.celery_app import celery_app
from app.workers.tasks.common import load, update, output_for
from app.services import storage_service as st
from app.processing.office.cleaner import clean_office
@celery_app.task(name='clean_office')
def clean_office_task(job_id:str, file_path:str, options:dict|None=None):
    options=options or {}; path=Path(file_path); job=load(job_id)
    try:
        update(job,status='processing',progress=35,current_step='Processing')
        out=output_for(job); report=clean_office(path,out); token=st.make_download_token(out); update(job,status="completed",progress=100,current_step="Verified cleaned Office file",report=report,output_filename=out.name,download_token=token)
    except Exception as e:
        update(job,status='failed',progress=100,current_step='Failed',error_message=str(e))
    return job_id
