from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image

# ExifTool reports values from multiple places. Only embedded privacy-relevant
# groups should trigger a finding. Filesystem fields and derived image structure
# are diagnostics and must never make a cleaned upload look unsafe.
FILESYSTEM_GROUPS = {"file", "system"}
TECHNICAL_GROUPS = {"composite"}
COLOR_PROFILE_GROUPS = {"icc_profile", "icc-profile", "jfif"}
CONTAINER_STRUCTURE_GROUPS = {"png", "webp", "riff", "tiff"}
EMBEDDED_PRIVACY_GROUPS = {
    "exif",
    "xmp",
    "iptc",
    "photoshop",
    "makernotes",
    "maker_notes",
    "quicktime",
}

TECHNICAL_TAGS = {
    "ExifToolVersion", "SourceFile", "FileName", "Directory", "FileSize",
    "FileModifyDate", "FileAccessDate", "FileInodeChangeDate", "FilePermissions",
    "FileType", "FileTypeExtension", "MIMEType", "ImageWidth", "ImageHeight",
    "ExifByteOrder", "EncodingProcess", "BitsPerSample", "ColorComponents",
    "YCbCrSubSampling", "Megapixels", "ColorType", "BitDepth", "Compression",
    "Filter", "Interlace", "ImageSize", "ResolutionUnit", "XResolution", "YResolution",
    "CurrentIPTCDigest", "ProfileCMMType", "ProfileVersion", "ProfileClass",
    "ColorSpaceData", "ProfileConnectionSpace", "ProfileDateTime", "ProfileFileSignature",
    "PrimaryPlatform", "CMMFlags", "DeviceManufacturer", "DeviceModel", "DeviceAttributes",
    "RenderingIntent", "ConnectionSpaceIlluminant", "ProfileCreator", "ProfileID",
    "ProfileDescription", "ProfileCopyright", "Gamma", "PixelsPerUnitX", "PixelsPerUnitY",
    "PixelUnits", "SubfileType", "PhotometricInterpretation", "RowsPerStrip", "StripByteCounts",
    "PlanarConfiguration", "SamplesPerPixel", "ExtraSamples", "MediaWhitePoint", "MediaBlackPoint",
    "RedMatrixColumn", "GreenMatrixColumn", "BlueMatrixColumn", "RedTRC", "GreenTRC", "BlueTRC",
}

GPS_TOKENS = {"gps", "latitude", "longitude", "altitude", "geotag", "location", "geolocation"}
C2PA_TOKENS = {"c2pa", "jumbf", "contentcredentials", "contentauth", "manifest", "claim", "assertion"}
PRIVATE_TAG_TOKENS = {
    "author", "artist", "by-line", "byline", "creator", "credit", "copyright", "owner",
    "publisher", "contact", "email", "url", "username", "person", "people",
    "make", "model", "lens", "serial", "camera", "bodyserial", "lensserial", "makernotes",
    "software", "processingsoftware", "history", "documentid", "instanceid", "originaldocumentid",
    "datetime", "createdate", "modifydate", "metadatadate", "datecreated", "timecreated",
    "datetimeoriginal", "gps", "location", "latitude", "longitude", "altitude", "city", "state",
    "country", "headline", "caption", "description", "subject", "keywords", "comment",
    "imagedescription", "usercomment", "xpcomment", "xpkeywords", "xpauthor", "rating",
}

FRIENDLY_TAGS = {
    "make": "Camera make",
    "model": "Camera model",
    "lensmodel": "Lens model",
    "lensserialnumber": "Lens serial number",
    "bodyserialnumber": "Camera serial number",
    "serialnumber": "Serial number",
    "software": "Software used",
    "processingsoftware": "Processing software",
    "creatortool": "Creator tool",
    "artist": "Artist/author",
    "author": "Author",
    "creator": "Creator",
    "copyright": "Copyright notice",
    "datetimeoriginal": "Original capture date/time",
    "createdate": "Creation date/time",
    "modifydate": "Modified date/time",
    "metadatadate": "Metadata date/time",
    "gpslatitude": "GPS latitude",
    "gpslongitude": "GPS longitude",
    "gpsaltitude": "GPS altitude",
    "gpsposition": "GPS position",
    "gpsdatetime": "GPS date/time",
    "city": "City",
    "state": "State/region",
    "country": "Country",
    "description": "Description/caption",
    "imagedescription": "Image description",
    "caption-abstract": "Caption",
    "keywords": "Keywords",
    "subject": "Subject tags",
    "comment": "Comment",
    "usercomment": "User comment",
    "documentid": "Document ID",
    "instanceid": "Instance ID",
    "originaldocumentid": "Original document ID",
    "history": "Editing history",
}


def _preview(value: Any, limit: int = 160) -> str:
    text = "" if value is None else str(value).replace("\x00", "")
    text = " ".join(text.split())
    if text.lower().startswith("(binary data") or len(text) > 500:
        return "Binary embedded metadata block detected"
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _split_key(raw_key: str) -> tuple[str, str]:
    if ":" in raw_key:
        group, tag = raw_key.split(":", 1)
        return group.strip().strip("[]"), tag.strip()
    return "", raw_key


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _humanize(tag: str) -> str:
    normalized = _norm(tag)
    if normalized in FRIENDLY_TAGS:
        return FRIENDLY_TAGS[normalized]
    words = re.sub(r"(?<!^)(?=[A-Z])", " ", tag).replace("_", " ").replace("-", " ")
    return " ".join(words.split()).strip() or tag


def _category(tag: str, group: str = "") -> str:
    text = f"{group}:{tag}".lower().replace("_", "")
    if any(token in text for token in C2PA_TOKENS):
        return "Content Credentials / C2PA metadata"
    if any(token in text for token in GPS_TOKENS):
        return "Location metadata"
    if any(token in text for token in ["make", "model", "lens", "serial", "camera", "makernotes"]):
        return "Device/camera metadata"
    if any(token in text for token in ["creatortool", "software", "processingsoftware", "photoshop", "documentid", "instanceid", "history"]):
        return "Software/application metadata"
    if any(token in text for token in ["artist", "owner", "author", "creator", "copyright", "contact", "byline"]):
        return "Author/creator metadata"
    if any(token in text for token in ["date", "time"]):
        return "Date/time metadata"
    if any(token in text for token in ["caption", "description", "comment", "keyword", "subject", "headline"]):
        return "Description/keyword metadata"
    return "Embedded metadata"


def _severity(tag: str, group: str = "") -> str:
    text = f"{group}:{tag}".lower().replace("_", "")
    if any(token in text for token in GPS_TOKENS):
        return "high"
    if any(token in text for token in ["serial", "owner", "author", "creator", "contact", "email", "c2pa", "jumbf"]):
        return "medium"
    return "medium"


def _finding(raw_key: str, value: Any, *, group: str, tag: str) -> dict[str, Any]:
    category = _category(tag, group)
    key = _humanize(tag)
    preview = _preview(value)
    if category == "Content Credentials / C2PA metadata":
        preview = "Embedded provenance / content-credentials metadata detected"
    return {
        "id": f"{group}:{tag}".lower().replace(" ", "-"),
        "category": category,
        "key": key,
        "raw_key": raw_key,
        "group": group or "Embedded",
        "value_preview": preview,
        "severity": _severity(tag, group),
        "removable": True,
        "selected_by_default": True,
    }


def _c2pa_group_finding(items: list[dict[str, Any]]) -> dict[str, Any]:
    raw_keys = [str(item.get("raw_key") or item.get("key") or "") for item in items]
    sample = ", ".join(raw_keys[:5])
    more = "" if len(raw_keys) <= 5 else f" and {len(raw_keys) - 5} more internal field(s)"
    return {
        "id": "content-credentials-c2pa-metadata",
        "category": "Content Credentials / C2PA metadata",
        "key": "Content Credentials / C2PA manifest",
        "raw_key": "C2PA/JUMBF",
        "group": "C2PA",
        "value_preview": f"C2PA/Content Credentials provenance metadata detected ({len(items)} internal field(s): {sample}{more}).",
        "severity": "medium",
        "removable": True,
        "selected_by_default": True,
        "raw_fields": raw_keys,
    }


def _technical(raw_key: str, value: Any, *, group: str, tag: str, detail: str = "") -> dict[str, Any]:
    return {
        "category": "Technical image data",
        "key": _humanize(tag),
        "raw_key": raw_key,
        "group": group or "Technical",
        "value_preview": _preview(value),
        "severity": "low",
        "detail": detail,
        "removable": False,
        "selected_by_default": False,
    }


def _run_exiftool(path: Path) -> dict[str, Any]:
    if not shutil.which("exiftool"):
        raise RuntimeError("ExifTool is not installed in this runtime image.")
    result = subprocess.run(
        ["exiftool", "-j", "-a", "-G1", "-s", str(path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "ExifTool scan failed").strip())
    if not result.stdout.strip():
        return {}
    parsed = json.loads(result.stdout)
    return parsed[0] if parsed else {}


def _is_privacy_finding(group_l: str, tag_l: str) -> bool:
    search = f"{group_l}:{tag_l}".replace("_", "")
    if any(token in search for token in C2PA_TOKENS):
        return True
    if any(token in search for token in PRIVATE_TAG_TOKENS):
        return True
    if group_l in EMBEDDED_PRIVACY_GROUPS and tag_l not in {t.lower() for t in TECHNICAL_TAGS}:
        return True
    return False


def scan_image(path: Path, *, gps_only: bool = False) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    c2pa_items: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        meta = _run_exiftool(path)
        for raw_key, value in meta.items():
            if value in (None, "", []):
                continue
            group, tag = _split_key(raw_key)
            group_l = group.lower()
            tag_l = tag.lower()
            search = f"{group_l}:{tag_l}".replace("_", "")

            if group_l in FILESYSTEM_GROUPS or tag in TECHNICAL_TAGS:
                technical.append(_technical(raw_key, value, group=group, tag=tag, detail="Filesystem or derived file value"))
                continue

            if gps_only:
                if any(token in search for token in GPS_TOKENS):
                    findings.append(_finding(raw_key, value, group=group, tag=tag))
                elif group_l not in TECHNICAL_GROUPS:
                    technical.append(_technical(raw_key, value, group=group, tag=tag, detail="Non-location metadata ignored by GPS-only tool"))
                continue

            if group_l in TECHNICAL_GROUPS:
                technical.append(_technical(raw_key, value, group=group, tag=tag, detail="Derived ExifTool value"))
            elif group_l in COLOR_PROFILE_GROUPS:
                technical.append(_technical(raw_key, value, group=group, tag=tag, detail="Color/profile compatibility metadata"))
            elif group_l in CONTAINER_STRUCTURE_GROUPS and not _is_privacy_finding(group_l, tag_l):
                technical.append(_technical(raw_key, value, group=group, tag=tag, detail="Container structure metadata"))
            elif _is_privacy_finding(group_l, tag_l):
                item = _finding(raw_key, value, group=group, tag=tag)
                if item["category"] == "Content Credentials / C2PA metadata":
                    c2pa_items.append(item)
                else:
                    findings.append(item)
            else:
                technical.append(_technical(raw_key, value, group=group, tag=tag, detail="Unclassified non-private technical value"))
    except Exception as exc:
        raise RuntimeError(f"Image metadata scan failed: {exc}") from exc

    if c2pa_items:
        findings.insert(0, _c2pa_group_finding(c2pa_items))
        technical.extend({**item, "removable": False, "selected_by_default": False, "detail": "Grouped under the main C2PA finding"} for item in c2pa_items)

    try:
        with Image.open(path) as im:
            technical.append(
                {
                    "category": "Image structure",
                    "key": "Format and dimensions",
                    "value_preview": f"{im.format} {im.size[0]}×{im.size[1]}",
                    "severity": "low",
                    "detail": "Normal image structure value",
                    "removable": False,
                    "selected_by_default": False,
                }
            )
    except Exception as exc:
        warnings.append(f"Pillow could not inspect image structure: {exc}")

    weights = {"high": 30, "medium": 14, "low": 5}
    score = min(100, sum(weights.get(item.get("severity"), 10) for item in findings))
    if findings:
        summary = "Image private/provenance metadata found." if not gps_only else "Photo location metadata found."
    else:
        summary = "No removable private metadata found." if not gps_only else "No GPS/location metadata found."

    return {
        "report_type": "scan",
        "risk_score": score,
        "risk_level": "high" if score >= 70 else "medium" if score >= 30 else "low",
        "summary": summary,
        "categories": sorted({f["category"] for f in findings}),
        "findings": findings,
        "technical_metadata": technical,
        "warnings": warnings,
        "limitations": [
            "Filesystem timestamps and normal image structure values are shown as technical data, not private metadata.",
            "RAW camera formats are intentionally not supported for cleaning because some metadata can be required for rendering.",
            "Visible content, watermarks, faces, landmarks, and text inside the pixels are not changed.",
        ],
    }
