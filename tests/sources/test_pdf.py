from pathlib import Path
import pytest

from app.contracts import SourceDescriptor, SourceType
from app.extraction.errors import PDFExtractionError
from app.extraction.pdf_extractor import extract_pdf
from app.sources.pdf import PDFSource

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_pdf_text_5page_extraction():
    """PDF text: Extract a 5-page text PDF -> Text plus correct page metadata (no OCR)."""
    pdf_path = FIXTURES_DIR / "sample_text_5page.pdf"
    pages = extract_pdf(str(pdf_path))

    assert len(pages) == 5
    for idx, p in enumerate(pages):
        assert p["page_number"] == idx + 1
        assert "Orbital Robotics" in p["text"]
        assert p["char_count"] > 20
        assert p["ocr_used"] is False


def test_pdf_scan_image_only_ocr_fallback():
    """PDF scan: Extract image-only page -> OCR is invoked and text is returned."""
    pdf_path = FIXTURES_DIR / "scanned_image.pdf"
    pages = extract_pdf(str(pdf_path))

    assert len(pages) == 1
    page = pages[0]
    assert page["page_number"] == 1
    assert page["ocr_used"] is True
    assert "OCR fallback must extract this line" in page["text"]


def test_pdf_bad_corrupt_file_raises_typed_error():
    """PDF bad: Corrupt file -> Typed extraction failure, no silent drop."""
    pdf_path = FIXTURES_DIR / "corrupt.pdf"
    with pytest.raises(PDFExtractionError) as exc_info:
        extract_pdf(str(pdf_path))

    assert exc_info.value.error_code in ("PDF_CORRUPT", "PDF_PARSE_ERROR")
    assert exc_info.value.source_ref == str(pdf_path)


@pytest.mark.asyncio
async def test_pdf_source_adapter_fetch_text():
    """PDFSource yields valid RawDocument with rich page metadata."""
    pdf_path = FIXTURES_DIR / "sample_text_5page.pdf"
    desc = SourceDescriptor(
        source_type=SourceType.PDF,
        name="test-orbital-pdf",
        config={"path": str(pdf_path)},
    )
    adapter = PDFSource(desc)
    docs = [doc async for doc in adapter.fetch()]

    assert len(docs) == 1
    doc = docs[0]
    assert doc.source_id == desc.source_id
    assert doc.source_type == SourceType.PDF
    assert doc.content_type == "application/pdf"
    assert doc.metadata["total_pages"] == 5
    assert len(doc.metadata["pages"]) == 5
    assert "Orbital Robotics" in doc.raw_content


@pytest.mark.asyncio
async def test_pdf_source_adapter_fetch_scanned():
    """PDFSource yields RawDocument with OCR fallback metadata."""
    pdf_path = FIXTURES_DIR / "scanned_image.pdf"
    desc = SourceDescriptor(
        source_type=SourceType.PDF,
        name="test-scanned-pdf",
        config={"path": str(pdf_path)},
    )
    adapter = PDFSource(desc)
    docs = [doc async for doc in adapter.fetch()]

    assert len(docs) == 1
    doc = docs[0]
    assert doc.metadata["pages"][0]["ocr_used"] is True
    assert "OCR fallback must extract this line" in doc.raw_content
