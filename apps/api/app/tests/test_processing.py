import importlib.util
import shutil
from PIL import Image
import pytest

from app.processing.images.scanner import scan_image
from app.processing.images.cleaner import clean_image


@pytest.mark.skipif(shutil.which('exiftool') is None, reason='ExifTool system dependency is not installed in this test runtime')
def test_image_scan_and_clean(tmp_path):
    p = tmp_path / 'sample.jpg'
    Image.new('RGB', (10, 10)).save(p)
    before = scan_image(p)
    out = tmp_path / 'clean.jpg'
    after = clean_image(p, out)
    assert out.exists()
    assert 'risk_score' in before and 'risk_score' in after


@pytest.mark.skipif(importlib.util.find_spec('pikepdf') is None, reason='pikepdf is not installed in this test runtime')
def test_malformed_pdf_handling(tmp_path):
    p = tmp_path / 'bad.pdf'
    p.write_bytes(b'not a real pdf')
    from app.processing.pdf.scanner import scan_pdf
    report = scan_pdf(p)
    assert 'warnings' in report
