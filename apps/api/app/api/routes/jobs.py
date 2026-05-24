from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from app.api.routes.auth import current_user
from app.services import storage_service as st

router = APIRouter(prefix='/api')

@router.get('/jobs/{job_id}')
def get_job(job_id: str, request: Request, user: dict | None = Depends(current_user)):
    try:
        return st.assert_can_access_job(job_id, user, request)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(404, str(e))

@router.get('/downloads/{token}')
def download(token: str, request: Request, user: dict | None = Depends(current_user)):
    try:
        path, filename = st.resolve_download_for_request(token, user, request)
        return FileResponse(path, filename=filename, media_type=st.media_type_for(path, filename))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(404, str(e))

@router.delete('/jobs/{job_id}/files')
def delete(job_id: str, request: Request, user: dict | None = Depends(current_user)):
    try:
        st.assert_can_access_job(job_id, user, request)
        st.delete_job_files(job_id)
        return {'deleted': True}
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(404, str(e))
