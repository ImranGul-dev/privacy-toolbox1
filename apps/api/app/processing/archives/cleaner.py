from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

from app.processing.archives.scanner import classify_zip_entries, scan_zip


def _selected_candidates(options: dict | None) -> set[str] | None:
    options = options or {}
    items = options.get('selected_items') or []
    selected: set[str] = set()
    for item in items:
        raw = item.get('raw') if isinstance(item, dict) else None
        if isinstance(raw, dict):
            for name in raw.get('candidates') or []:
                selected.add(str(name))
        for name in item.get('candidates', []) if isinstance(item, dict) else []:
            selected.add(str(name))
    return selected or None


def clean_zip(src: Path, dst: Path, options: dict | None = None) -> dict:
    data = classify_zip_entries(src)
    removable_defaults = set(data['risky_paths']) | set(data['macos_artifacts']) | set(data['metadata_files']) | set(data['sensitive_files'])
    selected = _selected_candidates(options)
    remove_names = removable_defaults if selected is None else removable_defaults.intersection(selected)

    if not remove_names:
        shutil.copy2(src, dst)
    else:
        with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(dst, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                name = info.filename.replace('\\', '/')
                if name in remove_names:
                    continue
                # Do not preserve unsafe absolute/path traversal names.
                if name.startswith('/') or '..' in name.split('/'):
                    continue
                if info.is_dir():
                    zout.writestr(info, b'')
                else:
                    with zin.open(info, 'r') as src_entry, zout.open(info, 'w') as dst_entry:
                        shutil.copyfileobj(src_entry, dst_entry, length=1024 * 1024)

    before = scan_zip(src)
    after = scan_zip(dst)
    remaining = [f for f in after.get('findings', []) if f.get('removable')]
    if remaining:
        raise RuntimeError('ZIP cleanup could not verify removal of selected archive privacy risks.')
    removed_count = len(remove_names)
    return {
        'report_type': 'clean',
        'risk_score': after.get('risk_score', 0),
        'risk_level': after.get('risk_level', 'low'),
        'summary': f'Removed {removed_count} risky ZIP entr{"y" if removed_count == 1 else "ies"}.',
        'before': before,
        'after': after,
        'findings': after.get('findings', []),
        'technical_metadata': after.get('technical_metadata', []),
        'warnings': after.get('warnings', []),
        'limitations': after.get('limitations', []),
    }
