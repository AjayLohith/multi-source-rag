import asyncio
import sys
from pathlib import Path

# Ensure project root is importable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.contracts import SourceDescriptor, SourceType
from app.sources import (
    PDFSource,
    CSVSource,
    SQLSource,
    TextSource,
    MarkdownSource,
    JSONSource,
)


async def test_all_sources():
    print("=== Testing All Source Adapters ===")
    fixtures_dir = project_root / "tests" / "fixtures"

    # 1. PDF Text
    pdf_desc = SourceDescriptor(
        source_type=SourceType.PDF,
        name="pdf-text-test",
        config={"path": str(fixtures_dir / "sample_text_5page.pdf")},
    )
    pdf_docs = [d async for d in PDFSource(pdf_desc).fetch()]
    print(f"[OK] PDF Adapter: Extracted {len(pdf_docs)} doc(s), {pdf_docs[0].metadata['total_pages']} pages")

    # 2. PDF Scanned OCR
    scan_desc = SourceDescriptor(
        source_type=SourceType.PDF,
        name="pdf-ocr-test",
        config={"path": str(fixtures_dir / "scanned_image.pdf")},
    )
    scan_docs = [d async for d in PDFSource(scan_desc).fetch()]
    print(f"[OK] PDF OCR Fallback: Read {len(scan_docs)} doc(s), OCR used: {scan_docs[0].metadata['pages'][0]['ocr_used']}")

    # 3. CSV
    csv_desc = SourceDescriptor(
        source_type=SourceType.CSV,
        name="csv-order-test",
        config={"path": str(fixtures_dir / "changed_order.csv")},
    )
    csv_docs = [d async for d in CSVSource(csv_desc).fetch()]
    print(f"[OK] CSV Adapter: Extracted {len(csv_docs)} rows")

    # 4. SQL
    db_file = fixtures_dir / "test_records.db"
    sql_desc = SourceDescriptor(
        source_type=SourceType.SQL,
        name="sql-test",
        config={
            "connection_url": f"sqlite:///{db_file.as_posix()}",
            "table_name": "employees",
        },
    )
    sql_docs = [d async for d in SQLSource(sql_desc).fetch()]
    print(f"[OK] SQL Adapter: Extracted {len(sql_docs)} rows from employees table")

    print("\nAll tested source adapters functioning successfully!")


if __name__ == "__main__":
    asyncio.run(test_all_sources())
