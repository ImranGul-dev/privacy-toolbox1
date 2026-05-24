from pathlib import Path

from app.core.security import safe_filename
from app.services import storage_service as st
from app.workers.tasks.common import cleaned_display_name


def test_safe_filename_preserves_long_extension():
    original = "job_84fwL1rfCghForILXfjGMg_file_z77XklSyCoVavJjU2uZxow_job_55Cl9teOK6nuDIyohMhSIg_file_NWIZYra_2iVv2gRcJdJ7FQ_ChatGPT-Image-May-21-2026-03_31_18-AM.png"
    cleaned = safe_filename(original)
    assert cleaned.endswith(".png")
    assert len(cleaned) <= 140


def test_cleaned_display_name_keeps_cleaned_suffix_and_extension():
    original = safe_filename("a" * 220 + ".png")
    name = cleaned_display_name({"input_filename": original, "file_type": ".png"})
    assert name.endswith("-cleaned.png")
    assert len(name) <= 140


def test_download_token_preserves_user_facing_filename(tmp_path: Path):
    out = st.OUTPUTS / "job_example_internal-name.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"test")
    try:
        token = st.make_download_token(out, "photo-cleaned.png")
        path, filename = st.resolve_download_info(token)
        assert path == out
        assert filename == "photo-cleaned.png"
    finally:
        out.unlink(missing_ok=True)
