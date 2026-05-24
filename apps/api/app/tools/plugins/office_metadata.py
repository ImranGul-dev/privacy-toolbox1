from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.office.cleaner import clean_office
from app.processing.office.scanner import scan_office
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition

OFFICE_EXTENSIONS = [".docx", ".xlsx", ".pptx"]


class RemoveOfficeMetadataTool(ToolPlugin):
    definition = ToolDefinition(
        id="office.metadata.cleaner",
        slug="remove-docx-metadata",
        title="Remove Office Metadata",
        kind="office",
        description="Scan and clean core/custom document properties from DOCX, XLSX, and PPTX files.",
        supported_extensions=OFFICE_EXTENSIONS,
        supported_actions=["scan", "clean", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_office(path)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_office(src, dst)


class DocxHiddenDataScannerTool(ToolPlugin):
    definition = ToolDefinition(
        id="office.docx.hidden_data.scanner",
        slug="docx-hidden-data-scanner",
        title="DOCX Hidden Data Scanner",
        kind="office",
        description="Scan Word DOCX files for comments, tracked changes, author properties, people data, custom XML, and hidden package indicators.",
        supported_extensions=[".docx"],
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_office(path)


class XlsxHiddenDataScannerTool(ToolPlugin):
    definition = ToolDefinition(
        id="office.xlsx.hidden_data.scanner",
        slug="xlsx-hidden-data-scanner",
        title="Excel Hidden Data Scanner",
        kind="office",
        description="Scan Excel XLSX files for hidden sheets, external links, workbook properties, comments, custom XML, and privacy-risk workbook data.",
        supported_extensions=[".xlsx"],
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_office(path)


class PptxNotesHiddenSlidesCleanerTool(ToolPlugin):
    definition = ToolDefinition(
        id="office.pptx.notes_hidden.cleaner",
        slug="pptx-remove-notes-hidden-slides",
        title="Remove Speaker Notes and Hidden Slides",
        kind="office",
        description="Scan and clean PowerPoint speaker notes, comments, hidden slide indicators, document properties, and collaboration metadata before sharing.",
        supported_extensions=[".pptx"],
        supported_actions=["scan", "clean", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_office(path)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_office(src, dst)
