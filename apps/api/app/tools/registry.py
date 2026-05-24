from __future__ import annotations

from app.tools.base import ToolPlugin
from app.tools.plugins.c2pa_metadata import C2paDetectorTool
from app.tools.plugins.archive_privacy import ZipPrivacyScannerTool, RemoveZipPrivacyRisksTool
from app.tools.plugins.media_metadata import RemoveAudioMetadataTool, RemoveVideoMetadataTool
from app.tools.plugins.pdf_extra import PdfRedactionCheckerTool, RemovePdfHiddenDataTool
from app.tools.plugins.image_metadata import RemoveExifDataTool, RemoveGpsFromPhotoTool, RemoveImageMetadataTool
from app.tools.plugins.office_metadata import RemoveOfficeMetadataTool, DocxHiddenDataScannerTool, XlsxHiddenDataScannerTool, PptxNotesHiddenSlidesCleanerTool
from app.tools.plugins.pdf_metadata import PdfPrivacyScannerTool, RemovePdfMetadataTool
from app.tools.plugins.verify_metadata import VerifyFileMetadataTool

_REGISTRY: dict[str, ToolPlugin] = {}
_ALIASES: dict[str, str] = {
    "clean-image": "remove-image-metadata",
    "remove-gps": "remove-gps-from-photo",
    "scan-image": "remove-image-metadata",
    "clean-pdf": "remove-pdf-metadata",
    "scan-pdf": "pdf-privacy-scanner",
    "clean-office": "remove-docx-metadata",
    "verify": "verify-file-metadata",
    "scan-video": "remove-video-metadata",
    "clean-video": "remove-video-metadata",
    "scan-audio": "remove-audio-metadata",
    "clean-audio": "remove-audio-metadata",
    "scan-zip": "zip-privacy-scanner",
    "clean-zip": "remove-zip-privacy-risks",
}


def register_tool(plugin: ToolPlugin) -> ToolPlugin:
    _REGISTRY[plugin.definition.slug] = plugin
    _REGISTRY[plugin.definition.id] = plugin
    return plugin


def get_tool(tool_id: str) -> ToolPlugin:
    key = _ALIASES.get(tool_id, tool_id)
    try:
        return _REGISTRY[key]
    except KeyError as exc:
        raise KeyError(f"Unknown tool '{tool_id}'.") from exc


def list_tools() -> list[ToolPlugin]:
    # Return each plugin once, keyed by slug.
    seen: set[int] = set()
    tools: list[ToolPlugin] = []
    for plugin in _REGISTRY.values():
        marker = id(plugin)
        if marker in seen:
            continue
        seen.add(marker)
        tools.append(plugin)
    return sorted(tools, key=lambda item: item.definition.slug)


for _plugin in [
    RemoveImageMetadataTool(),
    RemoveExifDataTool(),
    RemoveGpsFromPhotoTool(),
    RemovePdfMetadataTool(),
    PdfPrivacyScannerTool(),
    RemovePdfHiddenDataTool(),
    PdfRedactionCheckerTool(),
    RemoveOfficeMetadataTool(),
    DocxHiddenDataScannerTool(),
    XlsxHiddenDataScannerTool(),
    PptxNotesHiddenSlidesCleanerTool(),
    RemoveVideoMetadataTool(),
    RemoveAudioMetadataTool(),
    ZipPrivacyScannerTool(),
    RemoveZipPrivacyRisksTool(),
    VerifyFileMetadataTool(),
    C2paDetectorTool(),
]:
    register_tool(_plugin)
