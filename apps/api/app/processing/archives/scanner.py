from __future__ import annotations

from pathlib import Path
import zipfile

from app.core.config import settings

MAX_ZIP_ENTRIES = 5000
SUSPICIOUS_PREFIXES = ("__MACOSX/",)
METADATA_NAMES = (".DS_Store", "Thumbs.db", "desktop.ini")
SENSITIVE_NAMES = ('.env', '.npmrc', '.pypirc', 'id_rsa', 'id_dsa')
SENSITIVE_WORDS = ('password', 'secret', 'token', 'apikey', 'api-key', 'credentials')
PRIVATE_EXTENSIONS = {".docx", ".xlsx", ".pptx", ".pdf", ".jpg", ".jpeg", ".png", ".mp4", ".mov", ".mp3", ".m4a"}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar", ".tar", ".gz"}


def _finding(category: str, key: str, value: str, severity: str = "medium", removable: bool = False, candidates: list[str] | None = None) -> dict:
    return {
        "category": category,
        "key": key,
        "label": f"{category}: {key}",
        "value_preview": value[:140],
        "severity": severity,
        "removable": removable,
        "selected_by_default": removable,
        "raw": {"candidates": candidates or [], "cleanup_category": category},
    }


def _technical(key: str, value: str) -> dict:
    return _finding("Technical archive data", key, value, "low", False)


def classify_zip_entries(path: Path) -> dict[str, list[str] | int]:
    if path.suffix.lower() != ".zip":
        raise ValueError("Unsupported archive format. Use ZIP.")
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if len(infos) > MAX_ZIP_ENTRIES:
            raise ValueError("ZIP contains too many entries to scan safely.")
        total_uncompressed = sum(i.file_size for i in infos)
        if total_uncompressed > settings.zip_max_total_uncompressed_mb * 1024 * 1024:
            raise ValueError("ZIP expands beyond the configured safety limit.")

        risky_paths: list[str] = []
        macos_artifacts: list[str] = []
        metadata_files: list[str] = []
        sensitive_files: list[str] = []
        privacy_sensitive_contents: list[str] = []
        nested_archives: list[str] = []
        directories = 0
        files = 0
        for info in infos:
            name = info.filename.replace("\\", "/")
            if info.file_size > settings.zip_max_entry_mb * 1024 * 1024:
                raise ValueError("ZIP contains an entry larger than the configured safety limit.")
            if info.compress_size and info.file_size / max(info.compress_size, 1) > settings.zip_max_compression_ratio:
                raise ValueError("ZIP looks like a possible ZIP bomb because the compression ratio is too high.")
            lower = name.lower()
            if info.is_dir():
                directories += 1
            else:
                files += 1
            if name.startswith("/") or ".." in name.split("/"):
                risky_paths.append(name)
            if any(name.startswith(prefix) for prefix in SUSPICIOUS_PREFIXES):
                macos_artifacts.append(name)
            if any(lower.endswith(meta.lower()) for meta in METADATA_NAMES):
                metadata_files.append(name)
            base = Path(lower).name
            if base in SENSITIVE_NAMES or any(word in lower for word in SENSITIVE_WORDS):
                sensitive_files.append(name)
            suffix = Path(name).suffix.lower()
            if suffix in PRIVATE_EXTENSIONS:
                privacy_sensitive_contents.append(name)
            if (suffix in ARCHIVE_EXTENSIONS and suffix != '.zip') or (suffix == '.zip' and name != path.name):
                nested_archives.append(name)

    return {
        'entries': len(infos),
        'files': files,
        'directories': directories,
        'total_uncompressed': total_uncompressed,
        'risky_paths': risky_paths,
        'macos_artifacts': macos_artifacts,
        'metadata_files': metadata_files,
        'sensitive_files': sensitive_files,
        'privacy_sensitive_contents': privacy_sensitive_contents,
        'nested_archives': nested_archives,
    }


def scan_zip(path: Path) -> dict:
    try:
        data = classify_zip_entries(path)
    except zipfile.BadZipFile as exc:
        raise RuntimeError("ZIP scan failed: file is not a valid ZIP archive") from exc

    findings: list[dict] = []
    technical: list[dict] = [
        _technical("Entry count", str(data['entries'])),
        _technical("File count", str(data['files'])),
        _technical("Folder count", str(data['directories'])),
        _technical("Uncompressed size", str(data['total_uncompressed'])),
    ]
    warnings: list[str] = []

    risky_paths = list(data['risky_paths'])
    if risky_paths:
        findings.append(_finding("Archive safety", "Unsafe paths", f"{len(risky_paths)} unsafe path(s) detected", "high", True, risky_paths))

    artifacts = list(data['macos_artifacts']) + list(data['metadata_files'])
    if artifacts:
        findings.append(_finding("Archive metadata artifacts", "System metadata files", f"{len(artifacts)} system metadata/artifact file(s)", "medium", True, artifacts))

    sensitive = list(data['sensitive_files'])
    if sensitive:
        findings.append(_finding("Sensitive archive contents", "Secret/config filenames", f"{len(sensitive)} sensitive-looking filename(s)", "high", True, sensitive))

    inner = list(data['privacy_sensitive_contents'])
    if inner:
        findings.append(_finding("Metadata-bearing files inside ZIP", "Supported file types", f"{len(inner)} file(s) may contain their own metadata", "medium", False, inner))

    nested = list(data['nested_archives'])
    if nested:
        findings.append(_finding("Nested archives", "Nested compressed files", f"{len(nested)} nested archive(s) should be inspected separately", "medium", False, nested))

    score = min(100, sum(35 if f.get("severity") == "high" else 18 for f in findings))
    return {
        "report_type": "scan",
        "risk_score": score,
        "risk_level": "high" if score >= 70 else "medium" if score >= 30 else "low",
        "summary": "ZIP privacy risks found." if findings else "No obvious ZIP privacy risks found by current scanners.",
        "categories": sorted({f["category"] for f in findings}),
        "findings": findings,
        "technical_metadata": technical,
        "warnings": warnings,
        "limitations": [
            "ZIP scan mode inspects archive structure and filenames. It does not inspect full content inside each nested file.",
            "Metadata-bearing files inside the archive should be scanned separately with their matching tool.",
        ],
    }
