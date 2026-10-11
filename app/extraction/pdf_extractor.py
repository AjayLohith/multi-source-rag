from pathlib import Path
from typing import Any, Dict, List
import pymupdf as fitz

from app.extraction.errors import PDFExtractionError
from app.extraction.ocr import extract_text_from_image

MIN_CHARS_BEFORE_OCR = 20


def extract_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from a PDF file page-by-page using PyMuPDF.
    If a page contains fewer than MIN_CHARS_BEFORE_OCR characters,
    fallback OCR is executed for that specific page.

    Returns a list of dicts:
    [
        {
            "page_number": int,
            "text": str,
            "char_count": int,
            "ocr_used": bool,
        },
        ...
    ]
    Raises PDFExtractionError on corrupt, missing, or invalid PDF files.
    """
    path = Path(file_path)
    if not path.exists():
        raise PDFExtractionError(
            message=f"PDF file not found: {file_path}",
            source_ref=str(file_path),
            error_code="PDF_NOT_FOUND",
        )

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise PDFExtractionError(
            message=f"Failed to open PDF (corrupt or unreadable): {exc}",
            source_ref=str(file_path),
            error_code="PDF_CORRUPT",
        ) from exc

    try:
        if doc.is_encrypted:
            raise PDFExtractionError(
                message="PDF is encrypted / password protected",
                source_ref=str(file_path),
                error_code="PDF_ENCRYPTED",
            )

        pages: List[Dict[str, Any]] = []
        for idx, page in enumerate(doc):
            page_num = idx + 1
            extracted_text = page.get_text() or ""
            cleaned_text = extracted_text.strip()
            ocr_used = False

            if len(cleaned_text) < MIN_CHARS_BEFORE_OCR:
                # Page has insufficient text layer -> trigger OCR fallback
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                ocr_text = extract_text_from_image(
                    img_bytes,
                    source_ref=f"{file_path}#page={page_num}",
                )
                cleaned_text = ocr_text.strip()
                ocr_used = True

            pages.append(
                {
                    "page_number": page_num,
                    "text": cleaned_text,
                    "char_count": len(cleaned_text),
                    "ocr_used": ocr_used,
                }
            )

        return pages
    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError(
            message=f"Error extracting pages from PDF: {exc}",
            source_ref=str(file_path),
            error_code="PDF_PARSE_ERROR",
        ) from exc
    finally:
        doc.close()
