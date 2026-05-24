from __future__ import annotations

from pathlib import Path
from typing import Any
import re
import subprocess
import xml.etree.ElementTree as ET

import fitz
import pikepdf

# PDF Document Info fields that commonly expose private/document context.
PRIVATE_DOCINFO_KEYS = {"/Title", "/Author", "/Subject", "/Keywords", "/CreationDate", "/ModDate"}
# These fields are useful diagnostics but not private by themselves.
TECHNICAL_DOCINFO_KEYS = {"/Producer", "/Creator", "/Trapped"}
LOW_RISK_METADATA_KEYS = {"format", "encryption"}
PRIVATE_XMP_TOKENS = {
    "creator",
    "author",
    "title",
    "description",
    "subject",
    "keywords",
    "createdate",
    "modifydate",
    "metadatadate",
    "creatortool",
    "documentid",
    "instanceid",
    "originaldocumentid",
    "history",
    "marked",
    "owner",
    "producer",
}
TECHNICAL_XMP_TOKENS = {"pdfversion", "format", "conformance", "part", "trapped"}


def _preview(value: Any, limit: int = 140) -> str:
    text = "" if value is None else str(value).replace("\x00", "")
    text = " ".join(text.split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _finding(category: str, key: str, value: Any = "", severity: str = "medium", detail: str | None = None, removable: bool = True) -> dict[str, Any]:
    return {
        "id": f"{category}:{key}".lower().replace(" ", "-"),
        "category": category,
        "key": key,
        "value_preview": _preview(value),
        "severity": severity,
        "detail": detail or "",
        "removable": removable,
        "selected_by_default": removable,
    }


def _score(findings: list[dict[str, Any]]) -> int:
    weights = {"high": 28, "medium": 16, "low": 6}
    return min(100, sum(weights.get(f.get("severity"), 12) for f in findings))


def _has_javascript(obj: Any) -> bool:
    try:
        text = str(obj)
        return "/JavaScript" in text or "/JS" in text or "/Launch" in text or "/SubmitForm" in text
    except Exception:
        return False


def _read_xmp_bytes(pdf: pikepdf.Pdf) -> bytes | None:
    try:
        if "/Metadata" not in pdf.Root:
            return None
        metadata = pdf.Root["/Metadata"]
        return bytes(metadata.read_bytes())
    except Exception:
        return None


def _classify_xmp(xmp_bytes: bytes | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    if not xmp_bytes:
        return findings, technical
    text = xmp_bytes.decode("utf-8", errors="ignore")
    found_private: set[str] = set()
    found_technical: set[str] = set()

    # XML parse gives cleaner tag names when the packet is valid. Regex fallback catches malformed packets.
    try:
        root = ET.fromstring(text.strip().encode("utf-8"))
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            tag_l = tag.lower()
            value = " ".join("".join(el.itertext()).split())
            if not value:
                continue
            if any(token in tag_l for token in PRIVATE_XMP_TOKENS):
                found_private.add(tag)
            elif any(token in tag_l for token in TECHNICAL_XMP_TOKENS):
                found_technical.add(tag)
    except Exception:
        for match in re.finditer(r"<([a-zA-Z0-9:_-]+)[^>]*>(.{1,300}?)</\1>", text, flags=re.S):
            key = match.group(1).split(":")[-1]
            key_l = key.lower()
            if any(token in key_l for token in PRIVATE_XMP_TOKENS):
                found_private.add(match.group(1))
            elif any(token in key_l for token in TECHNICAL_XMP_TOKENS):
                found_technical.add(match.group(1))

    if found_private:
        # Keep the user-facing report compact. Full technical field list stays in Advanced details.
        findings.append(
            _finding(
                "XMP metadata",
                "XMP private packet",
                f"Private XMP field(s) present: {', '.join(sorted(found_private)[:8])}",
                "medium",
            )
        )
    else:
        technical.append(_finding("Technical PDF data", "XMP metadata stream", "Technical XMP packet present", "low", "No private XMP fields matched", removable=False))
    for key in sorted(found_technical)[:10]:
        technical.append(_finding("Technical PDF data", f"XMP:{key}", "Compatibility metadata", "low", removable=False))
    return findings, technical


def _names_tree_length(tree: Any) -> int:
    """Best-effort count of entries in a PDF names tree without flagging empty dictionaries."""
    try:
        names = tree.get("/Names", [])
        if names:
            return max(1, len(names) // 2)
        kids = tree.get("/Kids", [])
        return sum(_names_tree_length(kid) for kid in kids)
    except Exception:
        return 1


def _dedupe_findings(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (str(item.get("category")), str(item.get("key")))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def scan_pdf(path: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    warnings: list[str] = []
    structural_notes: list[str] = []

    try:
        with pikepdf.open(path) as pdf:
            for k, v in (pdf.docinfo or {}).items():
                key = str(k)
                if not str(v).strip():
                    continue
                if key in PRIVATE_DOCINFO_KEYS:
                    findings.append(_finding("Document properties", key, v, "medium"))
                elif key in TECHNICAL_DOCINFO_KEYS:
                    technical.append(_finding("Technical PDF data", key, v, "low", "PDF compatibility/prepress metadata", removable=False))
                else:
                    findings.append(_finding("Document properties", key, v, "low"))

            xmp_findings, xmp_technical = _classify_xmp(_read_xmp_bytes(pdf))
            findings.extend(xmp_findings)
            technical.extend(xmp_technical)

            names = pdf.Root.get("/Names", None)
            if names:
                try:
                    if "/EmbeddedFiles" in names:
                        count = _names_tree_length(names["/EmbeddedFiles"])
                        if count > 0:
                            findings.append(_finding("Attachments", "Embedded files", f"{count} embedded file reference(s)", "high"))
                        else:
                            structural_notes.append("Empty EmbeddedFiles names tree present")
                    if "/JavaScript" in names:
                        count = _names_tree_length(names["/JavaScript"])
                        if count > 0:
                            findings.append(_finding("Forms/scripts/active content", "JavaScript names", f"{count} named JavaScript action(s)", "high"))
                        else:
                            structural_notes.append("Empty JavaScript names tree present")
                    extra_names = [str(k) for k in names.keys() if str(k) not in {"/EmbeddedFiles", "/JavaScript"}]
                    if extra_names:
                        structural_notes.append(f"Names dictionary includes non-private entries: {', '.join(extra_names[:4])}")
                except Exception:
                    findings.append(_finding("Attachments", "Names dictionary", "Could not fully inspect Names dictionary", "low"))

            if "/OpenAction" in pdf.Root:
                sev = "high" if _has_javascript(pdf.Root["/OpenAction"]) else "medium"
                findings.append(_finding("Forms/scripts/active content", "OpenAction", "Automatic action present", sev))
            if "/AA" in pdf.Root:
                findings.append(_finding("Forms/scripts/active content", "Additional actions", "Automatic action dictionary present", "high"))
            if "/AcroForm" in pdf.Root:
                try:
                    fields = pdf.Root["/AcroForm"].get("/Fields", [])
                    if len(fields) > 0:
                        findings.append(_finding("Forms/scripts/active content", "AcroForm fields", f"{len(fields)} form field(s)", "medium"))
                    else:
                        structural_notes.append("Empty AcroForm dictionary present")
                except Exception:
                    findings.append(_finding("Forms/scripts/active content", "AcroForm", "Form dictionary present", "low"))
    except Exception as exc:
        warnings.append(f"pikepdf scan failed: {exc}")

    try:
        doc = fitz.open(path)
        try:
            for page_index in range(doc.page_count):
                page = doc[page_index]
                annot_count = 0
                annot = page.first_annot
                while annot:
                    annot_count += 1
                    annot = annot.next
                if annot_count:
                    findings.append(_finding("Comments/annotations", f"page {page_index + 1}", f"{annot_count} annotation(s)", "medium"))

            metadata = doc.metadata or {}
            for key, value in metadata.items():
                if not value or key in LOW_RISK_METADATA_KEYS:
                    continue
                key_l = key.lower()
                if key_l in {"title", "author", "subject", "keywords", "creationdate", "moddate"}:
                    findings.append(_finding("Document properties", key, value, "medium"))
                elif key_l in {"creator", "producer", "trapped"}:
                    technical.append(_finding("Technical PDF data", key, value, "low", "PDF writer/prepress compatibility metadata", removable=False))
                else:
                    findings.append(_finding("Document properties", key, value, "low"))
        finally:
            doc.close()
    except Exception as exc:
        warnings.append(f"PyMuPDF scan failed: {exc}")

    try:
        result = subprocess.run(["qpdf", "--check", str(path)], capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            warnings.append("qpdf reported structural warnings or parsing issues")
    except Exception as exc:
        warnings.append(f"qpdf unavailable or failed: {exc}")

    findings = _dedupe_findings(findings)
    risk_score = _score(findings)
    if findings:
        summary = "PDF private metadata or hidden-data indicators found."
    elif technical:
        summary = "No removable private metadata found. Low-risk technical PDF metadata may remain for compatibility."
    else:
        summary = "No removable metadata found."

    return {
        "report_type": "scan",
        "risk_score": risk_score,
        "risk_level": "high" if risk_score >= 70 else "medium" if risk_score >= 30 else "low",
        "summary": summary,
        "categories": sorted({f["category"] for f in findings}),
        "findings": findings,
        "technical_metadata": technical,
        "structural_notes": structural_notes,
        "warnings": warnings,
        "limitations": [
            "Routine producer/creator/trapped fields created by PDF writers are reported as low-risk technical metadata.",
            "Hard sanitize mode can alter PDF structure, forms, links, bookmarks, or interactive behavior.",
            "Visible page content is not redacted by metadata cleanup.",
        ],
    }
