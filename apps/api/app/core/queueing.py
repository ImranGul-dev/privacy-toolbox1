from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.plans import family_for_path, get_plan

HEAVY_TOOL_KINDS = {"pdf", "office", "media", "archive"}
HEAVY_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx", ".zip",
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm",
    ".mp3", ".m4a", ".wav", ".flac", ".ogg",
}


def queue_for_job(plugin: Any, action: str, file_path: Path, options: dict | None = None) -> str:
    """Choose the Celery queue for a job.

    This keeps the current Lightsail deployment safe because its single worker
    listens to all queues. In ECS, run separate services with -Q light and -Q heavy
    so image/EXIF jobs do not wait behind large PDF/video/Office jobs.
    """
    options = options or {}
    kind = getattr(plugin.definition, "kind", "")
    ext = file_path.suffix.lower()
    family = family_for_path(file_path)
    if options.get("force_queue") in {settings.celery_light_queue, settings.celery_heavy_queue}:
        return str(options["force_queue"])
    if kind in HEAVY_TOOL_KINDS or family in {"pdf", "office", "zip", "audio", "video"} or ext in HEAVY_EXTENSIONS:
        return settings.celery_heavy_queue
    return settings.celery_light_queue


def priority_for_plan(plan_name: str | None) -> int:
    """Return a conservative Redis/Celery priority hint from 0-9.

    Redis priority support is approximate, but this still lets paid plans receive
    better ordering once production workers are separated.
    """
    priority = int(get_plan(plan_name).priority)
    return max(0, min(9, priority * 3))
