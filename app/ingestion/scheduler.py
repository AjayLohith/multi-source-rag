from typing import List
from app.contracts import SourceDescriptor
from app.ingestion.pipeline import execute_ingestion_pipeline


class IngestionScheduler:
    """Orchestrates scheduled batch ingestion across multiple registered sources."""

    @staticmethod
    async def run_batch(descriptors: List[SourceDescriptor]):
        results = []
        for desc in descriptors:
            res = await execute_ingestion_pipeline(desc)
            results.append(res)
        return results
