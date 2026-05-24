from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.images.scanner import scan_image
from app.processing.office.scanner import scan_office
from app.processing.pdf.scanner import scan_pdf
from app.processing.media.scanner import scan_media, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS
from app.processing.archives.scanner import scan_zip
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition

VERIFY_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic", ".pdf", ".docx", ".xlsx", ".pptx", ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".mp3", ".m4a", ".wav", ".flac", ".ogg", ".zip"]


class VerifyFileMetadataTool(ToolPlugin):
    definition = ToolDefinition(
        id="metadata.verifier",
        slug="verify-file-metadata",
        title="Verify File Metadata Removal",
        kind="verify",
        description="Re-scan supported images, PDFs, Office files, media, and ZIP archives to verify remaining metadata indicators.",
        supported_extensions=VERIFY_EXTENSIONS,
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        ext = path.suffix.lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}:
            return scan_image(path)
        if ext == ".pdf":
            return scan_pdf(path)
        if ext in {".docx", ".xlsx", ".pptx"}:
            return scan_office(path)
        if ext in VIDEO_EXTENSIONS:
            return scan_media(path, media_kind="video")
        if ext in AUDIO_EXTENSIONS:
            return scan_media(path, media_kind="audio")
        if ext == ".zip":
            return scan_zip(path)
        raise ValueError("Unsupported verification file type")
