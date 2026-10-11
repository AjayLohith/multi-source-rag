from pathlib import Path
import pytest

from app.contracts import SourceDescriptor, SourceType
from app.extraction.errors import SQLExtractionError
from app.extraction.sql_extractor import extract_sql
from app.sources.sql import SQLSource

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
DB_PATH = FIXTURES_DIR / "test_records.db"
CONN_URL = f"sqlite:///{DB_PATH.as_posix()}"


def test_sql_read_small_test_table():
    """SQL: Read small test table -> Rows returned with stable source/table metadata."""
    records = extract_sql(connection_url=CONN_URL, table_name="employees")

    assert len(records) == 3
    first = records[0]
    assert first["row_index"] == 0
    assert first["row_data"]["name"] == "Elena Vance"
    assert "Elena Vance" in first["text"]
    assert "Lead Propulsion Engineer" in first["text"]


def test_sql_extractor_custom_query_with_limit():
    """SQL: Run custom query with explicit development limit."""
    query = "SELECT name, department FROM employees WHERE department = 'Robotics'"
    records = extract_sql(connection_url=CONN_URL, query=query, limit=1)

    assert len(records) == 1
    assert records[0]["row_data"]["name"] == "Alyx Vance"
    assert "Robotics" in records[0]["text"]


def test_sql_invalid_table_raises_typed_error():
    """SQL: Querying invalid table raises typed SQLExtractionError."""
    with pytest.raises(SQLExtractionError) as exc_info:
        extract_sql(connection_url=CONN_URL, table_name="non_existent_table")

    assert exc_info.value.error_code == "SQL_QUERY_FAILED"


@pytest.mark.asyncio
async def test_sql_source_adapter_fetch_table():
    """SQLSource adapter yields RawDocuments per row with table metadata."""
    desc = SourceDescriptor(
        source_type=SourceType.SQL,
        name="test-sqlite-source",
        config={"connection_url": CONN_URL, "table_name": "employees"},
    )
    adapter = SQLSource(desc)
    docs = [doc async for doc in adapter.fetch()]

    assert len(docs) == 3
    assert docs[0].source_type == SourceType.SQL
    assert docs[0].metadata["table_name"] == "employees"
    assert docs[0].metadata["row_index"] == 0
    assert docs[0].metadata["row_data"]["name"] == "Elena Vance"
    assert docs[1].metadata["row_data"]["name"] == "Gordon Freeman"
    assert docs[2].metadata["row_data"]["name"] == "Alyx Vance"


def test_sql_source_adapter_validation_missing_config():
    """SQLSource validate() raises ValueError if required keys are missing."""
    desc = SourceDescriptor(
        source_type=SourceType.SQL,
        name="incomplete-source",
        config={},
    )
    adapter = SQLSource(desc)
    with pytest.raises(ValueError):
        adapter.validate()
