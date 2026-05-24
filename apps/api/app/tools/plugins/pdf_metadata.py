from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.pdf.cleaner import clean_pdf
from app.processing.pdf.scanner import scan_pdf
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition


class RemovePdfMetadataTool(ToolPlugin):
    definition = ToolDefinition(
        id="pdf.metadata.cleaner",
        slug="remove-pdf-metadata",
        title="Remove PDF Metadata",
        kind="pdf",
        description="Scan and clean PDF document properties, XMP metadata, annotations, embedded files, forms, and active-content indicators.",
        supported_extensions=[".pdf"],
        supported_actions=["scan", "clean", "verify"],
        options_schema={
            "hard": {"type": "boolean", "default": False},
            "remove_annotations": {"type": "boolean", "default": True},
            "remove_forms": {"type": "boolean", "default": True},
        },
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_pdf(path)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        options = options or {}
        return clean_pdf(
            src,
            dst,
            hard=bool(options.get("hard", False)),
            remove_annotations=bool(options.get("remove_annotations", True)),
            remove_forms=bool(options.get("remove_forms", True)),
        )


class PdfPrivacyScannerTool(ToolPlugin):
    definition = ToolDefinition(
        id="pdf.privacy.scanner",
        slug="pdf-privacy-scanner",
        title="PDF Privacy Scanner",
        kind="pdf",
        description="Scan PDFs for privacy-risk indicators without modifying the file.",
        supported_extensions=[".pdf"],
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_pdf(path)
