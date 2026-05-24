from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services import storage_service as st
from app.services import metrics_service, quota_service
from app.tools.registry import get_tool
from app.tools.schemas import ToolAction
from app.workers.celery_app import celery_app
from app.workers.tasks.common import cleaned_display_name, load, output_for, update


@celery_app.task(name="process_tool_job")
def process_tool_job(job_id: str, tool_id: str, action: ToolAction, file_path: str, options: dict[str, Any] | None = None):
    """Generic Celery worker for all plugin-based tools."""
    options = options or {}
    path = Path(file_path)
    job = load(job_id)

    try:
        plugin = get_tool(tool_id)
        action_label = {"scan": "Scanning", "clean": "Cleaning", "verify": "Verifying"}.get(action, "Processing")
        update(job, status="processing", progress=35, current_step=action_label)

        if action == "scan":
            report = plugin.run_scan(path, options)
            update(job, status="completed", progress=100, current_step="Scan complete", report=report)
            metrics_service.record_job_finished(job, status="completed")
        elif action == "verify":
            report = plugin.run_verify(path, options)
            update(job, status="completed", progress=100, current_step="Verification complete", report=report)
            metrics_service.record_job_finished(job, status="completed")
        elif action == "clean":
            display_filename = cleaned_display_name(job, suffix=plugin.definition.output_suffix)
            out = output_for(job, suffix=plugin.definition.output_suffix)
            report = plugin.run_clean(path, out, options)
            token = st.make_download_token(out, filename=display_filename, owner_id=str(job.get('owner_id') or ''), job_id=job_id)
            update(
                job,
                status="completed",
                progress=100,
                current_step="Verified cleaned output",
                report=report,
                output_filename=out.name,
                download_filename=display_filename,
                download_token=token,
            )
            metrics_service.record_job_finished(job, status="completed")
        else:
            raise ValueError(f"Unsupported tool action: {action}")
    except Exception as exc:
        update(job, status="failed", progress=100, current_step="Failed", error_message=str(exc))
        try:
            usage = job.get('usage') or {}
            quota_service.refund(str(usage.get('actor') or ''), action, str(job.get('plan') or 'free'))
        except Exception:
            pass
        metrics_service.record_job_finished(job, status="failed", error_message=str(exc))
    return job_id
