from __future__ import annotations

from pathlib import Path
from typing import Any

from app.processing.c2pa.detector import detect_c2pa
from app.tools.base import ToolPlugin
from app.tools.schemas import ToolDefinition


def _first_manifest(manifest: Any) -> dict[str, Any] | None:
    if not isinstance(manifest, dict):
        return None
    if isinstance(manifest.get("manifests"), dict) and manifest["manifests"]:
        active = manifest.get("active_manifest")
        if active and isinstance(manifest["manifests"].get(active), dict):
            return manifest["manifests"][active]
        for value in manifest["manifests"].values():
            if isinstance(value, dict):
                return value
    return manifest


def _manifest_summary(manifest: Any) -> str:
    m = _first_manifest(manifest)
    if not m:
        return "C2PA manifest data present."
    parts: list[str] = []
    for key in ("claim_generator", "format", "title"):
        value = m.get(key)
        if value:
            parts.append(f"{key.replace('_', ' ')}: {value}")
    assertions = m.get("assertions")
    if isinstance(assertions, list):
        parts.append(f"assertions: {len(assertions)}")
    ingredients = m.get("ingredients")
    if isinstance(ingredients, list):
        parts.append(f"ingredients: {len(ingredients)}")
    return "; ".join(parts) or "C2PA manifest data present."


class C2paDetectorTool(ToolPlugin):
    definition = ToolDefinition(
        id="content.credentials.detector",
        slug="detect-content-credentials",
        title="Detect Content Credentials",
        kind="ai",
        description="Detect C2PA/content-credentials manifest indicators where c2patool is available.",
        supported_extensions=[".jpg", ".jpeg", ".png", ".webp", ".pdf", ".mp4", ".mov"],
        supported_actions=["scan", "verify"],
    )

    def scan(self, path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
        result = detect_c2pa(path)
        present = bool(result.get("present"))
        manifest = result.get("manifest")
        summary = _manifest_summary(manifest)
        return {
            "report_type": "scan",
            "risk_score": 20 if present else 0,
            "risk_level": "medium" if present else "low",
            "summary": "Content Credentials/C2PA manifest detected." if present else "No C2PA manifest detected by the current scanner.",
            "categories": ["Content Credentials / C2PA metadata"] if present else [],
            "findings": [
                {
                    "id": "content-credentials-c2pa-manifest",
                    "category": "Content Credentials / C2PA metadata",
                    "key": "C2PA manifest",
                    "value_preview": summary[:220],
                    "severity": "medium",
                    "removable": False,
                    "selected_by_default": False,
                    "raw": {"manifest_summary": summary, "tool": "c2patool"},
                }
            ] if present else [],
            "technical_metadata": [
                {
                    "category": "C2PA raw output",
                    "key": "c2patool JSON preview",
                    "value_preview": result.get("raw_preview", "")[:500],
                    "severity": "low",
                    "removable": False,
                    "selected_by_default": False,
                }
            ] if present and result.get("raw_preview") else [],
            "warnings": [result.get("warning")] if result.get("warning") else [],
            "limitations": [
                "C2PA detection depends on the c2patool runtime installed in the API and worker images.",
                "No C2PA manifest does not prove a file is human-made or AI-free; it only means no detectable C2PA manifest was found.",
            ],
        }
