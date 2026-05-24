from __future__ import annotations

from pathlib import Path
import re
import secrets
import zipfile
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.core.config import settings

ALLOWED = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff', '.heic', '.pdf', '.docx', '.xlsx', '.pptx', '.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm', '.mp3', '.m4a', '.wav', '.flac', '.ogg', '.zip'}
FILENAME_RE = re.compile(r'[^A-Za-z0-9._-]+')
ID_RE = re.compile(r'^[A-Za-z0-9_-]{8,96}$')


def random_id(prefix: str) -> str:
    return f'{prefix}_{secrets.token_urlsafe(16)}'


def validate_id(value: str, *, label: str = 'id') -> str:
    value = str(value or '')
    if not ID_RE.fullmatch(value):
        raise ValueError(f'Invalid {label}.')
    return value


def safe_filename(name: str, max_length: int = 140) -> str:
    original = Path(name or 'file').name
    clean = FILENAME_RE.sub('-', original).strip('.-_') or 'file'
    suffix = Path(clean).suffix.lower()
    stem = Path(clean).stem or 'file'

    if suffix and len(suffix) <= 12:
        available = max(20, max_length - len(suffix))
        stem = stem[:available].rstrip('.-_') or 'file'
        return f'{stem}{suffix}'[:max_length]

    return clean[:max_length].rstrip('.-_') or 'file'


def validate_ext(name: str) -> None:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError(f'Unsupported file type: {ext or "unknown"}')


def _starts(data: bytes, *prefixes: bytes) -> bool:
    return any(data.startswith(p) for p in prefixes)


def _has_box(data: bytes, marker: bytes) -> bool:
    return marker in data[:64]


def _validate_ooxml(path: Path, ext: str) -> None:
    expected_root = {'.docx': 'word/', '.xlsx': 'xl/', '.pptx': 'ppt/'}[ext]
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if '[Content_Types].xml' not in names or not any(n.startswith(expected_root) for n in names):
                raise ValueError(f'The uploaded {ext} file is not a valid Office Open XML document.')
            for info in zf.infolist():
                # ZIP-slip and basic ZIP-bomb checks for Office packages.
                parts = Path(info.filename).parts
                if info.filename.startswith('/') or '..' in parts:
                    raise ValueError('Unsafe Office package path detected.')
                if info.file_size > settings.zip_max_entry_mb * 1024 * 1024:
                    raise ValueError('Office package contains an unexpectedly large internal file.')
                if info.compress_size and info.file_size / max(info.compress_size, 1) > settings.zip_max_compression_ratio:
                    raise ValueError('Office package looks suspiciously compressed.')
    except zipfile.BadZipFile as exc:
        raise ValueError(f'The uploaded {ext} file is not a valid ZIP-based Office document.') from exc


def _validate_zip(path: Path) -> None:
    try:
        total_uncompressed = 0
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                parts = Path(info.filename).parts
                if info.filename.startswith('/') or '..' in parts:
                    raise ValueError('Unsafe ZIP path detected.')
                total_uncompressed += info.file_size
                if info.file_size > settings.zip_max_entry_mb * 1024 * 1024:
                    raise ValueError('ZIP contains an entry larger than the configured safety limit.')
                if info.compress_size and info.file_size / max(info.compress_size, 1) > settings.zip_max_compression_ratio:
                    raise ValueError('ZIP looks like a possible ZIP bomb because the compression ratio is too high.')
                if len(parts) > settings.zip_max_depth:
                    raise ValueError('ZIP nesting depth exceeds the configured safety limit.')
            if total_uncompressed > settings.zip_max_total_uncompressed_mb * 1024 * 1024:
                raise ValueError('ZIP total uncompressed size exceeds the configured safety limit.')
    except zipfile.BadZipFile as exc:
        raise ValueError('The uploaded ZIP is not valid.') from exc


def validate_file_signature(path: Path, filename: str) -> None:
    """Validate extension and common magic bytes before parser tools touch user files."""
    validate_ext(filename)
    ext = Path(filename).suffix.lower()
    data = path.read_bytes()[:4096]
    if not data:
        raise ValueError('Uploaded file is empty.')

    ok = True
    if ext in {'.jpg', '.jpeg'}:
        ok = _starts(data, b'\xff\xd8\xff')
    elif ext == '.png':
        ok = _starts(data, b'\x89PNG\r\n\x1a\n')
    elif ext == '.webp':
        ok = data.startswith(b'RIFF') and data[8:12] == b'WEBP'
    elif ext in {'.tif', '.tiff'}:
        ok = _starts(data, b'II*\x00', b'MM\x00*')
    elif ext in {'.heic', '.mp4', '.mov', '.m4v'}:
        ok = _has_box(data, b'ftyp')
    elif ext == '.pdf':
        ok = data.lstrip().startswith(b'%PDF-')
    elif ext in {'.docx', '.xlsx', '.pptx'}:
        ok = _starts(data, b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')
        if ok:
            _validate_ooxml(path, ext)
    elif ext == '.zip':
        ok = _starts(data, b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')
        if ok:
            _validate_zip(path)
    elif ext == '.mp3':
        ok = _starts(data, b'ID3') or (len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0)
    elif ext == '.wav':
        ok = data.startswith(b'RIFF') and data[8:12] == b'WAVE'
    elif ext == '.flac':
        ok = _starts(data, b'fLaC')
    elif ext == '.ogg':
        ok = _starts(data, b'OggS')
    elif ext in {'.mkv', '.webm'}:
        ok = _starts(data, b'\x1a\x45\xdf\xa3')
    elif ext == '.avi':
        ok = data.startswith(b'RIFF') and data[8:12] == b'AVI '
    elif ext == '.m4a':
        ok = _has_box(data, b'ftyp')

    if not ok:
        raise ValueError(f'File content does not match the {ext or "declared"} file type.')


def serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt='privacy-toolbox-downloads')


def token_for(value):
    return serializer().dumps(value)


def verify_token(token: str, max_age: int):
    try:
        return serializer().loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise ValueError('Download link expired') from exc
    except BadSignature as exc:
        raise ValueError('Invalid download link') from exc
