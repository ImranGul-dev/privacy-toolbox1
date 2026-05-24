from app.core.security import safe_filename, validate_ext
def test_safe_filename(): assert safe_filename('../../hello world.pdf')=='hello-world.pdf'
def test_reject_executable():
    try: validate_ext('bad.exe'); assert False
    except ValueError: assert True
