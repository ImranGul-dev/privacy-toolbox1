from __future__ import annotations

from pathlib import Path
import fitz


def _finding(category: str, key: str, value: str, severity: str = "medium") -> dict:
    return {
        "category": category,
        "key": key,
        "label": f"{category}: {key}",
        "value_preview": value[:140],
        "severity": severity,
        "removable": False,
        "selected_by_default": False,
    }


def scan_pdf_redactions(path: Path) -> dict:
    findings: list[dict] = []
    technical: list[dict] = []
    warnings: list[str] = []
    try:
        doc = fitz.open(path)
        try:
            for page_index in range(doc.page_count):
                page = doc[page_index]
                text_len = len(page.get_text("text") or "")
                drawings = page.get_drawings()
                dark_rects = 0
                for drawing in drawings:
                    fill = drawing.get("fill")
                    rect = drawing.get("rect")
                    if fill and rect:
                        # PyMuPDF fill components are floats 0..1. Dark filled rectangles often indicate visual redaction boxes.
                        try:
                            if max(fill[:3]) < 0.12 and rect.width > 20 and rect.height > 5:
                                dark_rects += 1
                        except Exception:
                            pass
                redaction_annots = 0
                annot = page.first_annot
                while annot:
                    if (annot.type[1] or "").lower() == "redact":
                        redaction_annots += 1
                    annot = annot.next
                if redaction_annots:
                    findings.append(_finding("PDF redaction annotations", f"page {page_index+1}", f"{redaction_annots} unapplied redaction annotation(s)", "high"))
                if dark_rects and text_len:
                    findings.append(_finding("Possible visual-only redaction", f"page {page_index+1}", f"{dark_rects} dark rectangle(s) with selectable page text present", "high"))
                if text_len:
                    technical.append(_finding("Technical PDF data", f"page {page_index+1} text layer", f"{text_len} extracted text character(s)", "low"))
        finally:
            doc.close()
    except Exception as exc:
        raise RuntimeError(f"PDF redaction check failed: {exc}") from exc

    score = min(100, sum(35 if f.get("severity") == "high" else 15 for f in findings))
    return {
        "report_type": "scan",
        "risk_score": score,
        "risk_level": "high" if score >= 70 else "medium" if score >= 30 else "low",
        "summary": "Possible redaction privacy risks found." if findings else "No obvious redaction risk indicators found by current scanners.",
        "categories": sorted({f["category"] for f in findings}),
        "findings": findings,
        "technical_metadata": technical,
        "warnings": warnings,
        "limitations": [
            "This scanner detects common redaction risk indicators, not a legal guarantee.",
            "Visual black boxes may be safe or unsafe depending on whether underlying text remains selectable.",
        ],
    }
