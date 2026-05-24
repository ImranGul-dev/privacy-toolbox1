from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.images.cleaner import clean_image
from app.processing.images.scanner import scan_image
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"]


class RemoveImageMetadataTool(ToolPlugin):
    definition = ToolDefinition(
        id="image.metadata.cleaner",
        slug="remove-image-metadata",
        title="Remove Image Metadata",
        kind="image",
        description="Scan and clean EXIF, XMP, IPTC, author, software, camera, and location metadata from images.",
        supported_extensions=IMAGE_EXTENSIONS,
        supported_actions=["scan", "clean", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_image(path, gps_only=False)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_image(src, dst, gps_only=False, options=options)


class RemoveExifDataTool(RemoveImageMetadataTool):
    definition = ToolDefinition(
        id="image.exif.cleaner",
        slug="remove-exif-data",
        title="Remove EXIF Data",
        kind="image",
        description="Scan and clean camera, device, GPS, timestamp, and software EXIF fields from images.",
        supported_extensions=IMAGE_EXTENSIONS,
        supported_actions=["scan", "clean", "verify"],
    )


class RemoveGpsFromPhotoTool(RemoveImageMetadataTool):
    definition = ToolDefinition(
        id="image.gps.cleaner",
        slug="remove-gps-from-photo",
        title="Remove GPS from Photo",
        kind="image",
        description="Scan images for location metadata and remove GPS-related fields from photos.",
        supported_extensions=IMAGE_EXTENSIONS,
        supported_actions=["scan", "clean", "verify"],
        options_schema={"gps_only": True},
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_image(path, gps_only=True)

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_image(src, dst, gps_only=True, options=options)
