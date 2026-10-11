import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.contracts import SourceDescriptor, SourceType
from app.ingestion.pipeline import execute_ingestion_pipeline


async def ingest_all():
    print("=== Ingesting Available Raw Data Sources ===")
    fixtures_dir = project_root / "tests" / "fixtures"

    descriptors = [
        # PDF Source
        SourceDescriptor(
            source_type=SourceType.PDF,
            name="Orbital Engineering Manual",
            config={"path": str(fixtures_dir / "sample_text_5page.pdf")},
        ),
        # Scanned PDF Source
        SourceDescriptor(
            source_type=SourceType.PDF,
            name="Orbital Scanned Notice",
            config={"path": str(fixtures_dir / "scanned_image.pdf")},
        ),
        # CSV Sources
        SourceDescriptor(
            source_type=SourceType.CSV,
            name="Department Roster",
            config={"path": str(fixtures_dir / "changed_order.csv")},
        ),
        SourceDescriptor(
            source_type=SourceType.CSV,
            name="Clearance Manifest",
            config={"path": str(fixtures_dir / "unexpected_column.csv")},
        ),
        # SQL Source
        SourceDescriptor(
            source_type=SourceType.SQL,
            name="Internal Employee Database",
            config={
                "connection_url": f"sqlite:///{(fixtures_dir / 'test_records.db').as_posix()}",
                "table_name": "employees",
            },
        ),
    ]

    for desc in descriptors:
        print(f"\nProcessing {desc.name} ({desc.source_type.value})...")
        try:
            result = await execute_ingestion_pipeline(desc)
            print(f"-> Status: {result['status']}, Docs: {result['processed_documents']}, Chunks: {result['chunks_upserted']}")
        except Exception as exc:
            print(f"-> Failed: {exc}")

    print("\nIngestion run completed.")


if __name__ == "__main__":
    asyncio.run(ingest_all())
