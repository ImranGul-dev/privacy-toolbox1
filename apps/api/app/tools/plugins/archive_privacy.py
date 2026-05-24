from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.archives.scanner import scan_zip
from app.processing.archives.cleaner import clean_zip
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition


class ZipPrivacyScannerTool(ToolPlugin):
    definition = ToolDefinition(
        id="archive.zip.privacy.scanner",
        slug="zip-privacy-scanner",
        title="ZIP Privacy Scanner",
        kind="archive",
        description="Scan ZIP archives for risky filenames, system metadata artifacts, nested archives, and metadata-bearing files before sharing.",
        supported_extensions=[".zip"],
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_zip(path)


class RemoveZipPrivacyRisksTool(ToolPlugin):
    definition = ToolDefinition(
        id="archive.zip.privacy.cleaner",
        slug="remove-zip-privacy-risks",
        title="Remove ZIP Privacy Risks",
        kind="archive",
        description="Remove unsafe paths, system metadata artifacts, and sensitive-looking config files from ZIP archives, then verify the cleaned archive.",
        supported_extensions=[".zip"],
        supported_actions=["scan", "clean", "verify"],
        output_suffix=".zip",
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_zip(path)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_zip(src, dst, options or {})
