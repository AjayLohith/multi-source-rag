import uuid
import pytest

from app.contracts import SourceDescriptor, SourceType
from app.ingestion.pipeline import execute_ingestion_pipeline


@pytest.mark.asyncio
async def test_pipeline_execution_and_deduplication(tmp_path):
    # Create isolated unique test fixture
    unique_id = str(uuid.uuid4())[:8]
    csv_file = tmp_path / f"test_{unique_id}.csv"
    csv_file.write_text(f"id,name,role\n101,Worker_{unique_id},Technician\n", encoding="utf-8")

    desc = SourceDescriptor(
        source_type=SourceType.CSV,
        name=f"test-csv-{unique_id}",
        config={"path": str(csv_file)},
    )

    # 1. First ingestion: must be completed/succeeded
    res1 = await execute_ingestion_pipeline(desc)
    assert res1["status"] in ("completed", "succeeded")
    assert res1["processed_documents"] == 1
    assert res1["chunks_upserted"] >= 1
    assert res1["skipped_duplicates"] == 0

    # 2. Re-ingest the exact same fixture: deduplication must trigger!
    res2 = await execute_ingestion_pipeline(desc)
    assert res2["status"] == "skipped_duplicate"
    assert res2["skipped_duplicates"] == 1
    assert res2["processed_documents"] == 0
    assert res2["chunks_upserted"] == 0
