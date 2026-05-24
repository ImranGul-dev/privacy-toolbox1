from pathlib import Path
from app.workers.celery_app import celery_app
from app.workers.tasks.common import load, update, output_for
from app.services import storage_service as st
from app.processing.images.cleaner import clean_image
@celery_app.task(name='clean_image')
def clean_image_task(job_id:str, file_path:str, options:dict|None=None):
    options=options or {}; path=Path(file_path); job=load(job_id)
    try:
        update(job,status='processing',progress=35,current_step='Processing')
        out=output_for(job); report=clean_image(path,out,gps_only=options.get("gps_only",False)); token=st.make_download_token(out); update(job,status="completed",progress=100,current_step="Verified cleaned output",report=report,output_filename=out.name,download_token=token)
    except Exception as e:
        update(job,status='failed',progress=100,current_step='Failed',error_message=str(e))
    return job_id
