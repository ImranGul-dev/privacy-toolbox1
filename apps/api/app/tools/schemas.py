from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

ToolAction = Literal["scan", "clean", "verify"]
ToolKind = Literal["image", "pdf", "office", "media", "archive", "verify", "ai"]


class ToolDefinition(BaseModel):
    id: str
    slug: str
    title: str
    kind: ToolKind
    description: str
    supported_extensions: list[str]
    supported_actions: list[ToolAction]
    output_suffix: str | None = None
    options_schema: dict[str, Any] = Field(default_factory=dict)


class SelectableReportItem(BaseModel):
    id: str
    label: str
    detail: str = ""
    category: str = "Metadata"
    severity: str = "medium"
    removable: bool = True
    selected_by_default: bool = True
    raw: dict[str, Any] = Field(default_factory=dict)


def _preview(value: Any, limit: int = 140) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def selectable_items_from_report(report: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    """Return frontend-ready checkbox items from a scanner report.

    Every plugin can still return custom report data, but this helper gives the UI
    one consistent shape for the review/select/remove step.
    """
    raw_items = report.get("findings") or report.get("before", {}).get("findings") or []
    if not isinstance(raw_items, list):
        return []

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_items):
        if not isinstance(raw, dict):
            continue
        category = str(raw.get("category") or "Metadata")
        key = str(raw.get("key") or raw.get("label") or raw.get("raw_key") or f"Item {index + 1}")
        label = str(raw.get("label") or (f"{category}: {key}" if category and category != key else key))
        value = raw.get("value_preview") or raw.get("description") or raw.get("detail") or "Detected"
        group = raw.get("group") or raw.get("raw_key") or ""
        detail_prefix = f"{group} • " if group else ""
        detail = _preview(f"{detail_prefix}{value}")
        item_id = f"{category}:{key}:{index}".lower().replace(" ", "-")
        if item_id in seen:
            continue
        seen.add(item_id)
        items.append(
            {
                "id": item_id,
                "label": label,
                "detail": detail,
                "category": category,
                "severity": str(raw.get("severity") or "medium"),
                "removable": bool(raw.get("removable", True)),
                "selected_by_default": bool(raw.get("selected_by_default", True)),
                "raw": raw,
            }
        )
        if len(items) >= limit:
            break
    return items


def normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    report = dict(report or {})
    if "report_type" not in report:
        report["report_type"] = "clean" if report.get("before") or report.get("after") else "scan"
    report.setdefault("risk_score", 0)
    report.setdefault("risk_level", "low")
    report.setdefault("summary", "Scan complete.")
    report.setdefault("categories", [])
    report.setdefault("findings", [])
    report.setdefault("warnings", [])
    report.setdefault("limitations", [])
    report["selectable_items"] = report.get("selectable_items") or selectable_items_from_report(report)
    return report
