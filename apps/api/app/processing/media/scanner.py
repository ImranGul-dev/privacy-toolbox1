from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".flac", ".ogg"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

PRIVATE_TAGS = {
    "title", "artist", "album", "album_artist", "author", "composer", "comment", "description",
    "copyright", "creation_time", "date", "year", "genre", "location", "location-eng", "make", "model",
    "camera", "device", "encoded_by", "software", "com.apple.quicktime.location.iso6709",
    "com.apple.quicktime.make", "com.apple.quicktime.model", "com.apple.quicktime.software",
    "com.apple.quicktime.creationdate", "publisher", "producer", "director", "keywords", "lyrics",
}
TECHNICAL_TAGS = {
    "major_brand", "minor_version", "compatible_brands", "duration", "bit_rate", "format_name",
    "format_long_name", "nb_streams", "nb_programs", "size", "probe_score", "filename", "encoder", "language", "handler_name", "vendor_id",
}


def _preview(value: Any, limit: int = 140) -> str:
    text = "" if value is None else str(value).replace("\x00", "")
    return text if len(text) <= limit else f"{text[:limit-1]}…"


def _finding(category: str, key: str, value: Any, severity: str = "medium", removable: bool = True) -> dict[str, Any]:
    return {
        "id": f"{category}:{key}".lower().replace(" ", "-"),
        "category": category,
        "key": key,
        "label": f"{category}: {key}",
        "value_preview": _preview(value),
        "severity": severity,
        "removable": removable,
        "selected_by_default": removable,
    }


def _run_ffprobe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout or "{}")


def _collect_tags(data: dict[str, Any]) -> list[tuple[str, str, Any]]:
    tags: list[tuple[str, str, Any]] = []
    fmt = data.get("format") or {}
    for key, value in (fmt.get("tags") or {}).items():
        tags.append(("Container metadata", str(key), value))
    for idx, stream in enumerate(data.get("streams") or []):
        codec_type = stream.get("codec_type") or "stream"
        for key, value in (stream.get("tags") or {}).items():
            tags.append((f"{codec_type.title()} stream metadata", str(key), value))
    return tags


def scan_media(path: Path, *, media_kind: str = "media") -> dict[str, Any]:
    ext = path.suffix.lower()
    if ext not in MEDIA_EXTENSIONS:
        raise ValueError("Unsupported media format.")

    findings: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    warnings: list[str] = []
    try:
        data = _run_ffprobe(path)
    except Exception as exc:
        raise RuntimeError(f"Media scan failed: {exc}") from exc

    for group, key, value in _collect_tags(data):
        k = key.lower()
        if k in TECHNICAL_TAGS:
            technical.append(_finding("Technical media data", key, value, "low", removable=False))
        elif k in PRIVATE_TAGS or any(token in k for token in ["location", "author", "artist", "comment", "creation", "software", "make", "model"]):
            severity = "high" if "location" in k else "medium"
            findings.append(_finding(group, key, value, severity, removable=True))
        else:
            # Unknown user/container tags can still identify the creator or workflow, but keep severity moderate.
            findings.append(_finding("Other removable media metadata", key, value, "medium", removable=True))

    fmt = data.get("format") or {}
    technical.append(_finding("Technical media data", "Format", fmt.get("format_long_name") or fmt.get("format_name") or ext, "low", removable=False))
    if fmt.get("duration"):
        technical.append(_finding("Technical media data", "Duration", fmt.get("duration"), "low", removable=False))
    if fmt.get("bit_rate"):
        technical.append(_finding("Technical media data", "Bit rate", fmt.get("bit_rate"), "low", removable=False))

    score = min(100, sum(25 if f.get("severity") == "high" else 12 for f in findings))
    label = "Video" if media_kind == "video" else "Audio" if media_kind == "audio" else "Media"
    return {
        "report_type": "scan",
        "risk_score": score,
        "risk_level": "high" if score >= 70 else "medium" if score >= 30 else "low",
        "summary": f"{label} metadata found." if findings else f"No removable {label.lower()} metadata found by current scanners.",
        "categories": sorted({f["category"] for f in findings}),
        "findings": findings,
        "technical_metadata": technical,
        "warnings": warnings,
        "limitations": [
            "The scanner separates user/removable tags from normal codec and container data.",
            "Some media containers require technical fields to remain playable.",
        ],
    }
