from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

NO_MANIFEST_MARKERS = (
    "no claim",
    "no c2pa",
    "manifest not found",
    "no manifest",
    "could not find a c2pa",
)


def detect_c2pa(path: Path) -> dict[str, Any]:
    """Detect C2PA / Content Credentials manifests with the official c2patool CLI."""
    if not shutil.which("c2patool"):
        raise RuntimeError("c2patool is not installed in this runtime image; Content Credentials detection cannot run.")

    result = subprocess.run(["c2patool", str(path)], capture_output=True, text=True, timeout=30)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    combined = f"{stdout}\n{stderr}".lower()

    if result.returncode != 0:
        if any(marker in combined for marker in NO_MANIFEST_MARKERS):
            return {"present": False, "manifest": None, "raw_preview": "", "warning": ""}
        raise RuntimeError(stderr or stdout or "c2patool failed")

    if not stdout:
        return {"present": False, "manifest": None, "raw_preview": "", "warning": ""}

    try:
        manifest = json.loads(stdout)
    except Exception:
        manifest = None
    return {"present": True, "manifest": manifest, "raw_preview": stdout[:1000], "warning": ""}
