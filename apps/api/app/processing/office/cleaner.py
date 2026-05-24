from __future__ import annotations

from pathlib import Path
import posixpath
import zipfile
from xml.etree import ElementTree as ET

from .scanner import COMMENT_PATTERNS, DOC_PROP_PARTS, PRIVATE_PART_PATTERNS, SUPPORTED_EXTENSIONS, _safe_zip_check, scan_office

CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("", CONTENT_TYPES_NS)
ET.register_namespace("", REL_NS)
ET.register_namespace("w", W_NS)

REL_REMOVE_TOKENS = (
    "metadata/core-properties",
    "extended-properties",
    "custom-properties",
    "comments",
    "commentAuthors",
    "threadedComment",
    "people",
    "person",
    "customXml",
    "revisions",
    "externalLink",
    "printerSettings",
    "notesSlide",
    "notesMaster",
)

REMOVE_TAGS = {
    f"{{{W_NS}}}del",
    f"{{{W_NS}}}moveFrom",
    f"{{{W_NS}}}moveFromRangeStart",
    f"{{{W_NS}}}moveFromRangeEnd",
    f"{{{W_NS}}}moveToRangeStart",
    f"{{{W_NS}}}moveToRangeEnd",
    f"{{{W_NS}}}commentRangeStart",
    f"{{{W_NS}}}commentRangeEnd",
    f"{{{W_NS}}}commentReference",
    f"{{{W_NS}}}annotationRef",
    f"{{{W_NS}}}rPrChange",
    f"{{{W_NS}}}pPrChange",
    f"{{{W_NS}}}tblPrChange",
    f"{{{W_NS}}}trPrChange",
    f"{{{W_NS}}}tcPrChange",
    f"{{{W_NS}}}sectPrChange",
}
UNWRAP_TAGS = {f"{{{W_NS}}}ins", f"{{{W_NS}}}moveTo"}
PRIVATE_ATTR_NAMES = {"author", "date", "id", "rsid", "rsidR", "rsidRDefault", "rsidP", "rsidRPr", "rsidDel"}


def _normal(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def _is_removed_part(name: str) -> bool:
    lname = _normal(name).lower()
    if _normal(name) in DOC_PROP_PARTS:
        return True
    if any(pattern.lower() in lname for pattern in COMMENT_PATTERNS):
        return True
    if any(pattern.lower() in lname for pattern in PRIVATE_PART_PATTERNS):
        return True
    return False


def _rels_base_dir(rels_name: str) -> str:
    rels_name = _normal(rels_name)
    if rels_name == "_rels/.rels":
        return ""
    folder = posixpath.dirname(rels_name)
    if folder.endswith("/_rels"):
        folder = posixpath.dirname(folder)
    return folder


def _relationship_target_path(rels_name: str, target: str) -> str:
    if ":" in target or target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(_rels_base_dir(rels_name), target)).lstrip("/")


def _rewrite_content_types(data: bytes, removed_parts: set[str]) -> bytes:
    try:
        root = ET.fromstring(data)
    except Exception:
        return data
    changed = False
    for child in list(root):
        part_name = child.attrib.get("PartName", "").lstrip("/")
        if part_name in removed_parts or _is_removed_part(part_name):
            root.remove(child)
            changed = True
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) if changed else data


def _rewrite_rels(name: str, data: bytes, removed_parts: set[str]) -> bytes:
    try:
        root = ET.fromstring(data)
    except Exception:
        return data
    changed = False
    for rel in list(root):
        rel_type = rel.attrib.get("Type", "")
        target = rel.attrib.get("Target", "")
        target_path = _relationship_target_path(name, target)
        if target_path in removed_parts or _is_removed_part(target_path) or any(token in rel_type for token in REL_REMOVE_TOKENS):
            root.remove(rel)
            changed = True
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) if changed else data


def _process_word_revision_xml(data: bytes) -> bytes:
    try:
        root = ET.fromstring(data)
    except Exception:
        return data

    changed = False

    def cleanse_attrs(el: ET.Element) -> None:
        nonlocal changed
        for attr in list(el.attrib):
            local = attr.split("}")[-1]
            if local in PRIVATE_ATTR_NAMES or local.startswith("rsid"):
                del el.attrib[attr]
                changed = True

    def walk(parent: ET.Element) -> None:
        nonlocal changed
        for child in list(parent):
            walk(child)
            cleanse_attrs(child)
            if child.tag in REMOVE_TAGS:
                parent.remove(child)
                changed = True
            elif child.tag in UNWRAP_TAGS:
                index = list(parent).index(child)
                parent.remove(child)
                for grand in list(child):
                    parent.insert(index, grand)
                    index += 1
                changed = True
        cleanse_attrs(parent)

    walk(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) if changed else data


def _should_process_xml(name: str) -> bool:
    lname = _normal(name).lower()
    return lname.endswith(".xml") and (lname.startswith("word/") or lname.startswith("xl/") or lname.startswith("ppt/"))


def clean_office(src: Path, dst: Path) -> dict:
    before = scan_office(src)
    if src.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported Office format. Use DOCX, XLSX, or PPTX.")

    removed_parts: set[str] = set()
    with zipfile.ZipFile(src, "r") as zin:
        _safe_zip_check(zin)
        for item in zin.infolist():
            name = _normal(item.filename)
            if _is_removed_part(name):
                removed_parts.add(name)

        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                name = _normal(item.filename)
                if name in removed_parts:
                    continue
                data = zin.read(item.filename)
                if name == "[Content_Types].xml":
                    data = _rewrite_content_types(data, removed_parts)
                elif name.endswith(".rels"):
                    data = _rewrite_rels(name, data, removed_parts)
                elif _should_process_xml(name):
                    data = _process_word_revision_xml(data)
                new_info = zipfile.ZipInfo(filename=name, date_time=item.date_time)
                new_info.compress_type = zipfile.ZIP_DEFLATED
                new_info.external_attr = item.external_attr
                zout.writestr(new_info, data)

    after = scan_office(dst)
    if after.get("findings"):
        remaining = ", ".join(sorted({f.get("category", "metadata") for f in after.get("findings", [])}))
        raise RuntimeError(f"Office cleanup verification failed; remaining private indicators: {remaining}")

    removed = sorted(set(before.get("categories", [])) - set(after.get("categories", [])))
    if int(before.get("risk_score", 0)) > int(after.get("risk_score", 0)) and "Risk score reduced" not in removed:
        removed.append("Risk score reduced")

    return {
        "report_type": "clean",
        "summary": after.get("summary", "Office cleanup verified."),
        "risk_score": after.get("risk_score", 0),
        "risk_level": after.get("risk_level", "low"),
        "before": before,
        "after": after,
        "removed_items": removed,
        "remaining_items": after.get("findings", []),
        "warnings": after.get("warnings", []),
        "limitations": after.get("limitations", []),
        "findings": after.get("findings", []),
        "technical_metadata": after.get("technical_metadata", []),
        "cleaned_file_size": dst.stat().st_size if dst.exists() else None,
    }
