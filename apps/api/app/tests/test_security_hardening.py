from pathlib import Path
import tempfile
import zipfile

from app.core.security import validate_file_signature
from app.services import storage_service as st
from app.services.user_service import create_user


def test_fake_pdf_rejected_by_magic_bytes():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'fake.pdf'
        p.write_bytes(b'not a pdf')
        try:
            validate_file_signature(p, 'fake.pdf')
            assert False, 'fake PDF should not pass magic-byte validation'
        except ValueError:
            assert True


def test_zip_slip_rejected_by_upload_validation():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'evil.zip'
        with zipfile.ZipFile(p, 'w') as zf:
            zf.writestr('../evil.txt', 'owned')
        try:
            validate_file_signature(p, 'evil.zip')
            assert False, 'ZIP-slip archive should not pass validation'
        except ValueError:
            assert True


def test_first_public_user_is_not_auto_admin(tmp_path, monkeypatch):
    users_file = st.BASE / 'users' / 'users.json'
    old = users_file.read_text() if users_file.exists() else None
    users_file.unlink(missing_ok=True)
    try:
        user = create_user('first-user@example.com', 'LongSafePassword123', 'First User')
        assert user['role'] == 'user'
    finally:
        if old is not None:
            users_file.write_text(old)
        else:
            users_file.unlink(missing_ok=True)
