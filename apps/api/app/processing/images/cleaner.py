from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageSequence

from .scanner import scan_image

GPS_DELETE_ARGS = [
    "-GPS:all=",
    "-XMP-exif:GPSLatitude=",
    "-XMP-exif:GPSLongitude=",
    "-XMP-exif:GPSAltitude=",
    "-XMP-exif:GPSMapDatum=",
    "-XMP-exif:GPSVersionID=",
    "-XMP-exif:GPSDateTime=",
    "-XMP-exif:GPSDestLatitude=",
    "-XMP-exif:GPSDestLongitude=",
    "-XMP-exif:GPSProcessingMethod=",
    "-XMP-exif:GPSAreaInformation=",
]


def _run_exiftool(args: list[str], path: Path) -> str:
    if not shutil.which("exiftool"):
        raise RuntimeError("ExifTool is not installed in this runtime image.")
    result = subprocess.run(["exiftool", "-overwrite_original", *args, str(path)], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "ExifTool cleanup failed").strip())
    return result.stdout


def _pillow_reencode(src: Path, dst: Path) -> None:
    """Fallback sanitizer that writes fresh pixel data with no EXIF/XMP chunks.

    It is used only when ExifTool cannot fully remove embedded private metadata from a supported raster file.
    """
    suffix = dst.suffix.lower()
    with Image.open(src) as im:
        frames = [frame.copy() for frame in ImageSequence.Iterator(im)]
        fmt = im.format or ("JPEG" if suffix in {".jpg", ".jpeg"} else "PNG")
        save_kwargs: dict[str, Any] = {}
        if fmt.upper() == "JPEG":
            base = frames[0]
            if base.mode not in {"RGB", "L"}:
                base = base.convert("RGB")
            base.save(dst, format="JPEG", quality=95, optimize=True)
            return
        if fmt.upper() == "PNG":
            frames[0].save(dst, format="PNG", optimize=True)
            return
        if fmt.upper() == "WEBP":
            frames[0].save(dst, format="WEBP", quality=95, method=6)
            return
        if fmt.upper() in {"TIFF", "TIF"}:
            frames[0].save(dst, format="TIFF", compression="tiff_deflate")
            return
        frames[0].save(dst, format=fmt, **save_kwargs)


def _selected_categories(options: dict[str, Any] | None) -> set[str]:
    options = options or {}
    selected = options.get("selected_items") or []
    cats = set()
    if isinstance(selected, list):
        for item in selected:
            if isinstance(item, dict):
                raw = item.get("raw") if isinstance(item.get("raw"), dict) else item
                category = raw.get("category") or item.get("category")
                if category:
                    cats.add(str(category))
    return cats


def _args_for_selected(options: dict[str, Any] | None, gps_only: bool) -> list[str]:
    if gps_only:
        return GPS_DELETE_ARGS
    cats = _selected_categories(options)
    if not cats:
        # Full metadata cleaner. Preserve ICC/color-space tags where possible so colors do not shift.
        return ["-all=", "--ICC_Profile:all", "-tagsfromfile", "@", "-colorspacetags"]
    args: list[str] = []
    if "Location data" in cats or "Location metadata" in cats:
        args += GPS_DELETE_ARGS
    if "Device/camera data" in cats or "Device/camera metadata" in cats:
        args += ["-EXIF:Make=", "-EXIF:Model=", "-EXIF:Lens*=", "-EXIF:Serial*=", "-MakerNotes:all="]
    if "Author/creator data" in cats or "Author/creator metadata" in cats:
        args += ["-Artist=", "-Author=", "-Creator=", "-OwnerName=", "-Copyright=", "-XMP-dc:all=", "-IPTC:By-line=", "-IPTC:CopyrightNotice="]
    if "Software/application data" in cats or "Software/application metadata" in cats:
        args += ["-Software=", "-ProcessingSoftware=", "-XMP-xmp:CreatorTool=", "-XMP-xmpMM:all=", "-Photoshop:all="]
    if "Date/time metadata" in cats:
        args += ["-time:all=", "-XMP-xmp:CreateDate=", "-XMP-xmp:ModifyDate=", "-XMP-xmp:MetadataDate="]
    if "Other embedded metadata" in cats or "Embedded metadata" in cats or "Content Credentials / C2PA metadata" in cats or "Description/keyword metadata" in cats:
        args += ["-XMP:all=", "-IPTC:all=", "-Comment=", "-PNG:TextualData="]
    return args or ["-all=", "--ICC_Profile:all", "-tagsfromfile", "@", "-colorspacetags"]


def clean_image(src: Path, dst: Path, gps_only: bool = False, options: dict[str, Any] | None = None) -> dict[str, Any]:
    before = scan_image(src, gps_only=gps_only)
    shutil.copy2(src, dst)
    warnings: list[str] = []

    try:
        _run_exiftool(_args_for_selected(options, gps_only), dst)
    except Exception as exc:
        warnings.append(str(exc))
        if gps_only:
            raise RuntimeError(f"GPS cleanup failed: {exc}") from exc
        _pillow_reencode(src, dst)

    after = scan_image(dst, gps_only=gps_only)
    # If ExifTool succeeded but private metadata still remains in full-clean mode, rebuild pixels as a hard fallback.
    if not gps_only and after.get("findings"):
        try:
            _pillow_reencode(src, dst)
            after = scan_image(dst, gps_only=False)
            warnings.append("Used pixel re-encode fallback because embedded metadata remained after ExifTool cleanup.")
        except Exception as exc:
            raise RuntimeError(f"Image cleanup verification failed; metadata remains and fallback failed: {exc}") from exc

    if gps_only and any(f.get("category") in {"Location data", "Location metadata"} for f in after.get("findings", [])):
        raise RuntimeError("GPS cleanup verification failed; location metadata remains.")

    if not gps_only and after.get("findings"):
        remaining = ", ".join(sorted({f.get("category", "metadata") for f in after.get("findings", [])}))
        raise RuntimeError(f"Image cleanup verification failed; remaining private metadata: {remaining}")

    removed = sorted(set(before.get("categories", [])) - set(after.get("categories", [])))
    if int(before.get("risk_score", 0)) > int(after.get("risk_score", 0)) and "Risk score reduced" not in removed:
        removed.append("Risk score reduced")

    return {
        "report_type": "clean",
        "summary": after.get("summary", "Image cleanup verified."),
        "risk_score": after.get("risk_score", 0),
        "risk_level": after.get("risk_level", "low"),
        "before": before,
        "after": after,
        "removed_items": removed,
        "remaining_items": after.get("findings", []),
        "warnings": warnings + after.get("warnings", []),
        "limitations": after.get("limitations", []),
        "findings": after.get("findings", []),
        "technical_metadata": after.get("technical_metadata", []),
        "cleaned_file_size": dst.stat().st_size if dst.exists() else None,
    }
