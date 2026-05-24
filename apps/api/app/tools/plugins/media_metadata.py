from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.media.scanner import scan_media, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS
from app.processing.media.cleaner import clean_media
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition


class RemoveVideoMetadataTool(ToolPlugin):
    definition = ToolDefinition(
        id="media.video.metadata.cleaner",
        slug="remove-video-metadata",
        title="Remove Video Metadata",
        kind="media",
        description="Scan and remove creator, location, software, comments, and container metadata from video files while preserving media streams where possible.",
        supported_extensions=sorted(VIDEO_EXTENSIONS),
        supported_actions=["scan", "clean", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_media(path, media_kind="video")

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_media(src, dst, media_kind="video")


class RemoveAudioMetadataTool(ToolPlugin):
    definition = ToolDefinition(
        id="media.audio.metadata.cleaner",
        slug="remove-audio-metadata",
        title="Remove Audio Metadata",
        kind="media",
        description="Scan and remove artist, album, comments, copyright, cover-art related, and other user metadata from audio files.",
        supported_extensions=sorted(AUDIO_EXTENSIONS),
        supported_actions=["scan", "clean", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return scan_media(path, media_kind="audio")

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return clean_media(src, dst, media_kind="audio")
