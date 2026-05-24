from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import importlib.util
import json
import shutil

from app.core.config import settings

METRICS_DIR = settings.storage_dir / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_FILE = METRICS_DIR / "tool_metrics.json"
MAX_RECENT = 100


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read() -> dict[str, Any]:
    if not METRICS_FILE.exists():
        return {"tools": {}, "recent_jobs": []}
    try:
        return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"tools": {}, "recent_jobs": []}


def _write(data: dict[str, Any]) -> None:
    tmp = METRICS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(METRICS_FILE)


def _tool_record(data: dict[str, Any], tool_slug: str) -> dict[str, Any]:
    tools = data.setdefault("tools", {})
    return tools.setdefault(
        tool_slug,
        {
            "tool_slug": tool_slug,
            "total_jobs": 0,
            "scan_jobs": 0,
            "clean_jobs": 0,
            "verify_jobs": 0,
            "success_jobs": 0,
            "failed_jobs": 0,
            "total_processing_ms": 0,
            "average_processing_ms": 0,
            "bytes_processed": 0,
            "last_status": "untested",
            "last_error": None,
            "last_used_at": None,
            "last_success_at": None,
            "last_failure_at": None,
        },
    )


def record_job_created(job: dict[str, Any]) -> None:
    tool_type = str(job.get("tool_type") or "unknown:unknown")
    tool_slug, _, action = tool_type.partition(":")
    action = action or "unknown"
    data = _read()
    rec = _tool_record(data, tool_slug)
    rec["total_jobs"] = int(rec.get("total_jobs", 0)) + 1
    if action == "scan":
        rec["scan_jobs"] = int(rec.get("scan_jobs", 0)) + 1
    elif action == "clean":
        rec["clean_jobs"] = int(rec.get("clean_jobs", 0)) + 1
    elif action == "verify":
        rec["verify_jobs"] = int(rec.get("verify_jobs", 0)) + 1
    rec["bytes_processed"] = int(rec.get("bytes_processed", 0)) + int(job.get("file_size") or 0)
    rec["last_status"] = "queued"
    rec["last_used_at"] = _now()
    recent = data.setdefault("recent_jobs", [])
    recent.insert(
        0,
        {
            "id": job.get("id"),
            "tool_slug": tool_slug,
            "action": action,
            "status": "queued",
            "file_type": job.get("file_type"),
            "file_size": job.get("file_size"),
            "created_at": job.get("created_at") or _now(),
            "updated_at": job.get("updated_at") or _now(),
            "error_message": None,
            "processing_ms": None,
        },
    )
    data["recent_jobs"] = recent[:MAX_RECENT]
    _write(data)


def record_job_finished(job: dict[str, Any], *, status: str, error_message: str | None = None) -> None:
    tool_type = str(job.get("tool_type") or "unknown:unknown")
    tool_slug, _, action = tool_type.partition(":")
    created_at = job.get("created_at")
    processing_ms = 0
    try:
        start = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        processing_ms = max(0, int((datetime.now(timezone.utc) - start).total_seconds() * 1000))
    except Exception:
        processing_ms = 0

    data = _read()
    rec = _tool_record(data, tool_slug)
    rec["last_status"] = status
    rec["last_used_at"] = _now()
    if status == "completed":
        rec["success_jobs"] = int(rec.get("success_jobs", 0)) + 1
        rec["last_success_at"] = _now()
        rec["last_error"] = None
    elif status == "failed":
        rec["failed_jobs"] = int(rec.get("failed_jobs", 0)) + 1
        rec["last_failure_at"] = _now()
        rec["last_error"] = error_message or job.get("error_message")
    if processing_ms:
        rec["total_processing_ms"] = int(rec.get("total_processing_ms", 0)) + processing_ms
        completed = max(1, int(rec.get("success_jobs", 0)) + int(rec.get("failed_jobs", 0)))
        rec["average_processing_ms"] = int(rec["total_processing_ms"] / completed)

    for item in data.setdefault("recent_jobs", []):
        if item.get("id") == job.get("id"):
            item.update({"status": status, "updated_at": _now(), "error_message": error_message, "processing_ms": processing_ms})
            break
    else:
        data["recent_jobs"].insert(
            0,
            {
                "id": job.get("id"),
                "tool_slug": tool_slug,
                "action": action,
                "status": status,
                "file_type": job.get("file_type"),
                "file_size": job.get("file_size"),
                "created_at": job.get("created_at"),
                "updated_at": _now(),
                "error_message": error_message,
                "processing_ms": processing_ms,
            },
        )
    data["recent_jobs"] = data.get("recent_jobs", [])[:MAX_RECENT]
    _write(data)


def dependency_status() -> dict[str, Any]:
    commands = {
        "exiftool": shutil.which("exiftool"),
        "qpdf": shutil.which("qpdf"),
        "ghostscript": shutil.which("gs"),
        "ffmpeg": shutil.which("ffmpeg"),
        "libreoffice": shutil.which("soffice") or shutil.which("libreoffice"),
        "c2patool": shutil.which("c2patool"),
    }
    python_packages = {
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "pikepdf": importlib.util.find_spec("pikepdf") is not None,
        "PyMuPDF": importlib.util.find_spec("fitz") is not None,
        "lxml": importlib.util.find_spec("lxml") is not None,
    }
    return {
        "commands": {name: {"installed": bool(path), "path": path} for name, path in commands.items()},
        "python_packages": {name: {"installed": bool(ok)} for name, ok in python_packages.items()},
    }


def tool_requirements(tool_slug: str) -> list[str]:
    if tool_slug in {"remove-image-metadata", "remove-exif-data", "remove-gps-from-photo"}:
        return ["exiftool", "Pillow"]
    if tool_slug in {"remove-pdf-metadata", "pdf-privacy-scanner"}:
        return ["pikepdf", "PyMuPDF", "qpdf"]
    if tool_slug == "remove-docx-metadata":
        return ["python-zipfile"]
    if tool_slug == "detect-content-credentials":
        return ["c2patool"]
    if tool_slug == "verify-file-metadata":
        return ["exiftool", "Pillow", "pikepdf", "PyMuPDF", "qpdf", "python-zipfile"]
    return []


def _is_dependency_ready(dep: str, deps: dict[str, Any]) -> bool:
    if dep == "python-zipfile":
        return True
    if dep in deps.get("commands", {}):
        return bool(deps["commands"][dep].get("installed"))
    if dep in deps.get("python_packages", {}):
        return bool(deps["python_packages"][dep].get("installed"))
    return False


def admin_summary(tool_definitions: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = _read()
    deps = dependency_status()
    tools: list[dict[str, Any]] = []
    for definition in tool_definitions:
        slug = definition.get("slug")
        rec = dict(metrics.get("tools", {}).get(slug, {}))
        reqs = tool_requirements(str(slug))
        ready = all(_is_dependency_ready(dep, deps) for dep in reqs)
        success = int(rec.get("success_jobs", 0))
        failed = int(rec.get("failed_jobs", 0))
        finished = success + failed
        success_rate = round((success / finished) * 100, 1) if finished else None
        if not ready:
            health = "dependency-missing"
        elif failed and success_rate is not None and success_rate < 90:
            health = "degraded"
        elif rec.get("last_status") == "failed":
            health = "last-run-failed"
        elif finished:
            health = "healthy"
        else:
            health = "ready-untested"
        tools.append({**definition, **rec, "requirements": reqs, "dependencies_ready": ready, "success_rate": success_rate, "health": health})
    totals = {
        "total_jobs": sum(int(t.get("total_jobs", 0)) for t in tools),
        "success_jobs": sum(int(t.get("success_jobs", 0)) for t in tools),
        "failed_jobs": sum(int(t.get("failed_jobs", 0)) for t in tools),
        "bytes_processed": sum(int(t.get("bytes_processed", 0)) for t in tools),
    }
    return {"generated_at": _now(), "totals": totals, "dependencies": deps, "tools": tools, "recent_jobs": metrics.get("recent_jobs", [])}
