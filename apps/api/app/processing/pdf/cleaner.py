from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

import fitz
import pikepdf

from .scanner import scan_pdf


def _pikepdf_cleanup(src: Path, dst: Path, remove_forms: bool = True) -> None:
    with pikepdf.open(src, allow_overwriting_input=False) as pdf:
        try:
            if "/Metadata" in pdf.Root:
                del pdf.Root.Metadata
        except Exception:
            try:
                del pdf.Root["/Metadata"]
            except Exception:
                pass
        try:
            del pdf.docinfo
        except Exception:
            try:
                pdf.docinfo.clear()
            except Exception:
                pass

        for key in ["/OpenAction", "/AA"]:
            try:
                if key in pdf.Root:
                    del pdf.Root[key]
            except Exception:
                pass

        try:
            names = pdf.Root.get("/Names", None)
            if names:
                for subkey in ["/EmbeddedFiles", "/JavaScript"]:
                    if subkey in names:
                        del names[subkey]
                if len(names.keys()) == 0 and "/Names" in pdf.Root:
                    del pdf.Root["/Names"]
        except Exception:
            try:
                if "/Names" in pdf.Root:
                    del pdf.Root["/Names"]
            except Exception:
                pass

        if remove_forms:
            try:
                if "/AcroForm" in pdf.Root:
                    del pdf.Root["/AcroForm"]
            except Exception:
                pass

        pdf.remove_unreferenced_resources()
        pdf.save(dst, linearize=True, fix_metadata_version=False)


def _pymupdf_cleanup(src: Path, dst: Path, remove_annotations: bool = True) -> None:
    doc = fitz.open(src)
    try:
        doc.set_metadata({})
        # PyMuPDF documents its XML metadata deletion helper as camelCase in current versions.
        for helper in ("del_xml_metadata", "_delXmlMetadata"):
            if hasattr(doc, helper):
                try:
                    getattr(doc, helper)()
                except Exception:
                    pass
        if remove_annotations:
            for page_index in range(doc.page_count):
                page = doc[page_index]
                annot = page.first_annot
                while annot:
                    nxt = annot.next
                    page.delete_annot(annot)
                    annot = nxt
        doc.save(dst, garbage=4, deflate=True, clean=True)
    finally:
        doc.close()


def _ghostscript_hard_sanitize(src: Path, dst: Path) -> bool:
    result = subprocess.run(
        [
            "gs",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.7",
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            f"-sOutputFile={dst}",
            str(src),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0 and dst.exists() and dst.stat().st_size > 0


def _categories(report: dict) -> set[str]:
    return {f.get("category", "") for f in report.get("findings", []) if f.get("category")}


def clean_pdf(src: Path, dst: Path, hard: bool = False, remove_annotations: bool = True, remove_forms: bool = True) -> dict:
    before = scan_pdf(src)
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pt-pdf-") as td:
        td_path = Path(td)
        current = src
        try:
            if hard:
                gs_out = td_path / "ghostscript.pdf"
                if _ghostscript_hard_sanitize(current, gs_out):
                    current = gs_out
                else:
                    warnings.append("Ghostscript hard-sanitize pass failed or was unavailable; continued with standard cleanup.")

            stage1 = td_path / "stage-pikepdf.pdf"
            _pikepdf_cleanup(current, stage1, remove_forms=remove_forms)
            current = stage1

            stage2 = td_path / "stage-pymupdf.pdf"
            _pymupdf_cleanup(current, stage2, remove_annotations=remove_annotations)
            current = stage2

            stage3 = td_path / "stage-final.pdf"
            _pikepdf_cleanup(current, stage3, remove_forms=remove_forms)
            shutil.copy2(stage3, dst)
        except Exception as exc:
            raise RuntimeError(f"PDF cleanup failed: {exc}") from exc

    after = scan_pdf(dst)
    if after.get("findings"):
        remaining = ", ".join(sorted({f.get("category", "metadata") for f in after.get("findings", [])}))
        raise RuntimeError(f"PDF cleanup verification failed; remaining private indicators: {remaining}")

    removed = sorted(_categories(before) - _categories(after))
    if int(before.get("risk_score", 0)) > int(after.get("risk_score", 0)) and "Risk score reduced" not in removed:
        removed.append("Risk score reduced")

    return {
        "report_type": "clean",
        "summary": after.get("summary") or "PDF cleanup verified.",
        "risk_score": after.get("risk_score", 0),
        "risk_level": after.get("risk_level", "low"),
        "before": before,
        "after": after,
        "removed_items": removed,
        "remaining_items": after.get("findings", []),
        "warnings": warnings + after.get("warnings", []) + (["Hard sanitize mode may alter document structure or behavior."] if hard else []),
        "limitations": after.get("limitations", []),
        "findings": after.get("findings", []),
        "technical_metadata": after.get("technical_metadata", []),
        "cleaned_file_size": dst.stat().st_size if dst.exists() else None,
    }
