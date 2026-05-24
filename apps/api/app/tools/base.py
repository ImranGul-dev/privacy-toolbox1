from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.tools.schemas import ToolDefinition, ToolAction, normalize_report


class ToolPlugin(ABC):
    """Base class every processing tool must follow.

    Add a new backend tool by creating one plugin class, registering it in
    app/tools/registry.py, and adding its frontend metadata in apps/web/lib/tools/registry.ts.
    """

    definition: ToolDefinition

    def supports_file(self, path: Path) -> bool:
        return path.suffix.lower() in self.definition.supported_extensions

    def supports_action(self, action: ToolAction) -> bool:
        return action in self.definition.supported_actions

    def validate(self, action: ToolAction, path: Path) -> None:
        if not self.supports_action(action):
            raise ValueError(f"Tool '{self.definition.slug}' does not support action '{action}'.")
        if not self.supports_file(path):
            allowed = ", ".join(self.definition.supported_extensions)
            raise ValueError(f"Unsupported file type '{path.suffix}'. Supported: {allowed}.")

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(f"Tool '{self.definition.slug}' does not implement scan().")

    def clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(f"Tool '{self.definition.slug}' does not implement clean().")

    def verify(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.scan(path, options)

    def run_scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate("scan", path)
        return normalize_report(self.scan(path, options or {}))

    def run_clean(self, src: Path, dst: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate("clean", src)
        return normalize_report(self.clean(src, dst, options or {}))

    def run_verify(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate("verify", path)
        return normalize_report(self.verify(path, options or {}))
