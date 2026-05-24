from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.routes.auth import current_user
from app.core.plans import family_for_path, get_plan, limit_exceeded_message, limit_mb_for, plan_dict
from app.schemas.jobs import JobCreate
from app.services import quota_service
from app.services import storage_service as st
from app.services import analytics_service, admin_config_service
from app.tools.registry import get_tool, list_tools
from app.tools.schemas import ToolAction
from app.workers.tasks.common import make_job
from app.workers.tasks.process_tool_job import process_tool_job

router = APIRouter(prefix="/api", tags=["tools"])


@router.get("/tools")
def get_tools():
    return {"tools": [plugin.definition.model_dump() for plugin in list_tools()]}


@router.get("/tools/{tool_id}")
def get_tool_definition(tool_id: str):
    try:
        return get_tool(tool_id).definition.model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get('/plans')
def get_plans():
    return admin_config_service.public_config()


def _plan_name_for(user: dict | None, options: dict | None) -> str:
    # The active plan comes from the authenticated account. Guests are always Free.
    # Stripe subscription synchronization can update the stored user plan after webhooks are connected.
    return (user or {}).get('plan') or 'free'


@router.post("/tools/{tool_id}/{action}")
def create_tool_job(tool_id: str, action: str, payload: JobCreate, request: Request, user: dict | None = Depends(current_user)):
    if action not in {"scan", "clean", "verify"}:
        raise HTTPException(status_code=400, detail="Action must be scan, clean, or verify.")
    tool_action = cast(ToolAction, action)
    try:
        plugin = get_tool(tool_id)
        meta = st.assert_can_access_upload(payload.file_id, user, request)
        file_path = st.find_upload(payload.file_id)
        plugin.validate(tool_action, file_path)

        family = family_for_path(file_path)
        size = int(meta.get('file_size') or file_path.stat().st_size)
        plan_name = _plan_name_for(user, payload.options)
        limit_mb = limit_mb_for(plan_name, family)
        if size > limit_mb * 1024 * 1024:
            raise ValueError(limit_exceeded_message(plan_name=plan_name, family=family, size_bytes=size, limit_mb=limit_mb))

        if tool_action == 'clean' and plugin.definition.slug == 'remove-pdf-hidden-data' and not get_plan(plan_name).advanced_pdf:
            raise ValueError('Advanced PDF hidden-data cleanup is a Pro feature. Use the standard PDF metadata cleaner or upgrade to Pro.')

        usage = quota_service.check_and_consume(user, plan_name, tool_action, actor_override=str(meta.get('owner_id') or ''))
        job = make_job(
            f"{plugin.definition.slug}:{tool_action}",
            str(file_path),
            original_filename=st.original_filename(payload.file_id, file_path),
        )
        job['owner_id'] = meta.get('owner_id') or st.owner_id_for(user, request)
        job['file_id'] = payload.file_id
        job['plan'] = plan_name
        job['usage'] = usage
        st.save_job(job)
        try:
            analytics_service.record_event({'event': 'tool_job_created', 'path': request.url.path, 'tool_slug': plugin.definition.slug, 'source': (payload.options or {}).get('source', '')}, request, user)
        except Exception:
            pass
        options = dict(payload.options or {})
        options['plan'] = plan_name
        options['user_id'] = user.get('id') if user else None
        process_tool_job.delay(job["id"], plugin.definition.slug, tool_action, str(file_path), options)
        return job
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
