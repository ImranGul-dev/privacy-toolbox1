from __future__ import annotations

from pathlib import Path
from typing import Any
import zipfile
import xml.etree.ElementTree as ET

SUPPORTED_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
MAX_ZIP_ENTRIES = 10000
MAX_UNCOMPRESSED = 250 * 1024 * 1024
DOC_PROP_PARTS = {"docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"}

COMMENT_PATTERNS = (
    "comments.xml",
    "/comments/",
    "commentsExtended.xml",
    "threadedComments",
    "commentAuthors.xml",
)
TRACKED_CHANGE_TAGS = {
    "ins",
    "del",
    "moveFrom",
    "moveTo",
    "moveFromRangeStart",
    "moveFromRangeEnd",
    "moveToRangeStart",
    "moveToRangeEnd",
    "rPrChange",
    "pPrChange",
    "tblPrChange",
    "trPrChange",
    "tcPrChange",
    "sectPrChange",
}
PRIVATE_PART_PATTERNS = (
    "customXml/",
    "/people",
    "person.xml",
    "persons/",
    "revisions/",
    "revisionLog",
    "externalLinks/",
    "printerSettings/",
    "notesSlides/",
    "notesMasters/",
)


def _safe_zip_check(z: zipfile.ZipFile) -> None:
    infos = z.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        raise ValueError("Office archive contains too many entries")
    total = sum(i.file_size for i in infos)
    if total > MAX_UNCOMPRESSED:
        raise ValueError("Office archive expands beyond configured safety limit")
    for info in infos:
        name = info.filename.replace("\\", "/")
        if name.startswith("/") or ".." in name.split("/"):
            raise ValueError("Office archive contains an unsafe path")


def _preview(value: Any, limit: int = 140) -> str:
    text = "" if value is None else str(value).replace("\x00", "")
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _finding(category: str, key: str, value: Any = "", severity: str = "medium", detail: str = "") -> dict[str, Any]:
    return {
        "id": f"{category}:{key}".lower().replace(" ", "-"),
        "category": category,
        "key": key,
        "value_preview": _preview(value),
        "severity": severity,
        "detail": detail,
        "removable": True,
        "selected_by_default": True,
    }


def _technical(category: str, key: str, value: Any = "", detail: str = "") -> dict[str, Any]:
    return {
        "category": category,
        "key": key,
        "value_preview": _preview(value),
        "severity": "low",
        "detail": detail,
        "removable": False,
        "selected_by_default": False,
    }


def _local_name(tag: str) -> str:
    return tag.split("}")[-1]


def _scan_docprops(z: zipfile.ZipFile, names: set[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for name in DOC_PROP_PARTS:
        if name not in names:
            continue
        data = z.read(name)
        found_text = False
        try:
            root = ET.fromstring(data)
            for el in root.iter():
                text = (el.text or "").strip()
                if text:
                    found_text = True
                    findings.append(_finding("Document properties", _local_name(el.tag), text, "medium"))
        except Exception:
            pass
        if not found_text:
            findings.append(_finding("Document properties", name, "metadata part present", "low"))
    return findings


def _has_tracked_changes(data: bytes) -> bool:
    try:
        root = ET.fromstring(data)
    except Exception:
        return False
    for el in root.iter():
        if _local_name(el.tag) in TRACKED_CHANGE_TAGS:
            return True
    return False


def scan_office(path: Path) -> dict[str, Any]:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported Office format. Use DOCX, XLSX, or PPTX.")

    findings: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        with zipfile.ZipFile(path) as z:
            _safe_zip_check(z)
            names = {n.replace("\\", "/") for n in z.namelist()}
            lower_names = {n.lower() for n in names}

            findings.extend(_scan_docprops(z, names))

            comment_parts = sorted(n for n in names if any(pattern.lower() in n.lower() for pattern in COMMENT_PATTERNS))
            if comment_parts:
                findings.append(_finding("Comments/annotations", "comment parts", f"{len(comment_parts)} comment-related part(s)", "medium"))

            private_parts = sorted(n for n in names if any(pattern.lower() in n.lower() for pattern in PRIVATE_PART_PATTERNS))
            if private_parts:
                findings.append(_finding("Office hidden package parts", "private package parts", f"{len(private_parts)} removable hidden/private part(s)", "medium"))

            tracked_locations = []
            for name in sorted(names):
                lname = name.lower()
                if not lname.endswith(".xml"):
                    continue
                if not (lname.startswith("word/") or lname.startswith("xl/") or lname.startswith("ppt/")):
                    continue
                if name in DOC_PROP_PARTS or any(pattern.lower() in lname for pattern in COMMENT_PATTERNS):
                    continue
                try:
                    if _has_tracked_changes(z.read(name)):
                        tracked_locations.append(name)
                except Exception:
                    continue
            if tracked_locations:
                findings.append(_finding("Tracked changes/revisions", "revision markup", f"{len(tracked_locations)} XML part(s) contain revision markup", "high"))

            # Non-sensitive package facts for diagnostics only.
            technical.append(_technical("Office package structure", "Parts", f"{len(names)} package part(s)", "Normal OOXML ZIP package structure"))
            rels = [n for n in lower_names if n.endswith(".rels")]
            if rels:
                technical.append(_technical("Office package structure", "Relationships", f"{len(rels)} relationship part(s)", "Normal OOXML relationships"))
    except Exception as exc:
        raise RuntimeError(f"OOXML scan failed: {exc}") from exc

    score = min(100, sum({"high": 30, "medium": 14, "low": 5}.get(f.get("severity"), 10) for f in findings))
    return {
        "risk_score": score,
        "risk_level": "high" if score >= 70 else "medium" if score >= 30 else "low",
        "summary": "Office private metadata or collaboration data found." if findings else "No removable Office metadata found.",
        "categories": sorted({f["category"] for f in findings}),
        "findings": findings,
        "technical_metadata": technical,
        "warnings": warnings,
        "limitations": [
            "This scanner targets modern OOXML files: DOCX, XLSX, and PPTX.",
            "Visible document content, text, images, headers, footers, and watermarks are not removed by metadata cleanup.",
            "Accepting/removing tracked changes can change the editable document state.",
        ],
    }
