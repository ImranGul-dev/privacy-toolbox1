from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from .scanner import scan_media


def _categories(report: dict) -> set[str]:
    return {str(f.get("category", "")) for f in report.get("findings", []) if f.get("category")}


def clean_media(src: Path, dst: Path, *, media_kind: str = "media") -> dict:
    before = scan_media(src, media_kind=media_kind)
    with tempfile.TemporaryDirectory(prefix="pt-media-") as td:
        temp_out = Path(td) / f"cleaned{src.suffix.lower()}"
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-map", "0", "-map_metadata", "-1", "-map_chapters", "-1",
            "-c", "copy", str(temp_out),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            raise RuntimeError((result.stderr or "FFmpeg metadata cleanup failed").strip()[:500])
        shutil.copy2(temp_out, dst)

    after = scan_media(dst, media_kind=media_kind)
    if after.get("findings"):
        remaining = ", ".join(sorted({f.get("key", "metadata") for f in after.get("findings", [])})[:8])
        raise RuntimeError(f"Media cleanup verification failed; remaining removable metadata: {remaining}")

    removed = sorted(_categories(before) - _categories(after))
    if before.get("findings") and not removed:
        removed = ["Removable media metadata"]
    return {
        "report_type": "clean",
        "summary": after.get("summary") or "Media cleanup verified.",
        "risk_score": after.get("risk_score", 0),
        "risk_level": after.get("risk_level", "low"),
        "before": before,
        "after": after,
        "removed_items": removed,
        "remaining_items": after.get("findings", []),
        "warnings": after.get("warnings", []),
        "limitations": after.get("limitations", []) + ["Media streams are copied without re-encoding where FFmpeg can safely do so."],
        "findings": after.get("findings", []),
        "technical_metadata": after.get("technical_metadata", []),
        "cleaned_file_size": dst.stat().st_size if dst.exists() else None,
    }
