from pathlib import Path
import pytest

from app.contracts import SourceDescriptor, SourceType
from app.extraction.errors import CSVExtractionError
from app.extraction.csv_extractor import extract_csv
from app.sources.csv import CSVSource

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_csv_changed_column_order():
    """CSV: Changed column order -> Extraction succeeds; order does not matter."""
    csv_path = FIXTURES_DIR / "changed_order.csv"
    records = extract_csv(str(csv_path))

    assert len(records) == 2
    first_row = records[0]
    assert first_row["row_index"] == 0
    # Columns appear in whatever order exists in the file
    assert set(first_row["columns"]) == {"department", "name", "id", "salary"}
    assert first_row["row_data"]["name"] == "Alice"
    assert "Alice" in first_row["text"]
    assert "Engineering" in first_row["text"]


def test_csv_unexpected_column():
    """CSV: New unexpected column -> Raw extraction succeeds; later normalization handles it."""
    csv_path = FIXTURES_DIR / "unexpected_column.csv"
    records = extract_csv(str(csv_path))

    assert len(records) == 2
    first_row = records[0]
    assert "clearance_level" in first_row["columns"]
    assert first_row["row_data"]["clearance_level"] == "TopSecret"
    assert "clearance_level: TopSecret" in first_row["text"]


def test_csv_missing_file_raises_typed_error():
    """CSV missing/corrupt: raises CSVExtractionError."""
    with pytest.raises(CSVExtractionError) as exc_info:
        extract_csv("non_existent_file.csv")

    assert exc_info.value.error_code == "CSV_NOT_FOUND"


@pytest.mark.asyncio
async def test_csv_source_adapter_fetch_changed_order():
    """CSVSource yields valid RawDocument per row."""
    csv_path = FIXTURES_DIR / "changed_order.csv"
    desc = SourceDescriptor(
        source_type=SourceType.CSV,
        name="test-csv-source",
        config={"path": str(csv_path)},
    )
    adapter = CSVSource(desc)
    docs = [doc async for doc in adapter.fetch()]

    assert len(docs) == 2
    assert docs[0].source_type == SourceType.CSV
    assert docs[0].metadata["row_index"] == 0
    assert docs[0].metadata["row_data"]["name"] == "Alice"
    assert docs[1].metadata["row_index"] == 1
    assert docs[1].metadata["row_data"]["name"] == "Bob"


@pytest.mark.asyncio
async def test_csv_source_adapter_fetch_unexpected_column():
    """CSVSource yields RawDocuments with new unexpected columns intact."""
    csv_path = FIXTURES_DIR / "unexpected_column.csv"
    desc = SourceDescriptor(
        source_type=SourceType.CSV,
        name="test-csv-extra-col",
        config={"path": str(csv_path)},
    )
    adapter = CSVSource(desc)
    docs = [doc async for doc in adapter.fetch()]

    assert len(docs) == 2
    assert docs[0].metadata["row_data"]["clearance_level"] == "TopSecret"
    assert docs[0].metadata["row_data"]["notes"] == "Active badge"
