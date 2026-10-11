import io
import os
import shutil
from pathlib import Path
from typing import Union
from PIL import Image
import pytesseract

from app.extraction.errors import OCRError


def _configure_tesseract() -> None:
    possible_paths = [
        Path(os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")),
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for p in possible_paths:
        if p.exists():
            pytesseract.pytesseract.tesseract_cmd = str(p)
            tessdata = p.parent / "tessdata"
            if tessdata.exists():
                os.environ["TESSDATA_PREFIX"] = str(tessdata)
            return

    if shutil.which("tesseract"):
        pytesseract.pytesseract.tesseract_cmd = "tesseract"


_configure_tesseract()


def extract_text_from_image(image_data: Union[bytes, Image.Image], source_ref: str = "image") -> str:
    """
    Extracts text from an image (bytes or PIL Image) using pytesseract.
    Raises OCRError on failure.
    """
    _configure_tesseract()
    try:
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data

        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as exc:
        raise OCRError(
            message=f"OCR execution failed: {exc}",
            source_ref=source_ref,
            error_code="OCR_EXECUTION_FAILED",
        ) from exc
