from app.contracts import DocumentRecord, SourceType
from app.chunking.chunker import chunk_document


def test_chunking_tabular_single_record():
    doc = DocumentRecord(
        source_type=SourceType.CSV,
        source_id="csv-src",
        source_name="employees.csv",
        title="Employees",
        content="id: 101\nname: Alice\ndepartment: Engineering",
        content_hash="hash101",
        metadata={"row_index": 0},
    )
    chunks = chunk_document(doc, chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].document_id == doc.document_id
    assert chunks[0].metadata["row_index"] == 0


def test_chunking_pdf_with_page_markers():
    content = (
        "[PAGE 1]\nFirst page text with details.\n\n"
        "[PAGE 2]\nSecond page text with information.\n\n"
        "[PAGE 3]\nThird page text with summary."
    )
    doc = DocumentRecord(
        source_type=SourceType.PDF,
        source_id="pdf-src",
        source_name="manual.pdf",
        title="Manual",
        content=content,
        content_hash="hashpdf",
    )
    chunks = chunk_document(doc, chunk_size=500)
    assert len(chunks) == 3
    assert chunks[0].metadata["page_number"] == 1
    assert chunks[1].metadata["page_number"] == 2
    assert chunks[2].metadata["page_number"] == 3


def test_chunking_window_overlap():
    long_text = "Word " * 200  # ~1000 characters
    doc = DocumentRecord(
        source_type=SourceType.TEXT,
        source_id="txt-src",
        source_name="notes.txt",
        title="Notes",
        content=long_text,
        content_hash="hashlong",
    )
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 1
    for c in chunks:
        assert c.document_id == doc.document_id
        assert "char_length" in c.metadata
