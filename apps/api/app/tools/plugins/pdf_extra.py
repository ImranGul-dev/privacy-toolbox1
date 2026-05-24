from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.pdf.cleaner import clean_pdf
from app.processing.pdf.scanner import scan_pdf
from app.processing.pdf.redaction import scan_pdf_redactions
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition


class PdfRedactionCheckerTool(ToolPlugin):
    definition = ToolDefinition(
        id="pdf.redaction.checker",
        slug="pdf-redaction-checker",
        title="PDF Redaction Checker",
        kind="pdf",
        description="Scan PDFs for unapplied redaction annotations, visual black-box redaction risks, selectable text layers, and hidden content indicators.",
        supported_extensions=[".pdf"],
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_pdf_redactions(path)


class RemovePdfHiddenDataTool(ToolPlugin):
    definition = ToolDefinition(
        id="pdf.hidden_data.cleaner",
        slug="remove-pdf-hidden-data",
        title="Remove PDF Hidden Data",
        kind="pdf",
        description="Aggressively clean PDF metadata, annotations, attachments, forms, JavaScript/action indicators, and hidden-data structures where practical.",
        supported_extensions=[".pdf"],
        supported_actions=["scan", "clean", "verify"],
        options_schema={"hard": {"type": "boolean", "default": True}},
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_pdf(path)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_pdf(src, dst, hard=True, remove_annotations=True, remove_forms=True)
