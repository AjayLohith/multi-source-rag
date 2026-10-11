import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator

from app.contracts import RawDocument, SourceType
from app.extraction.sql_extractor import extract_sql
from app.sources.base import SourceAdapter


class SQLSource(SourceAdapter):
    """
    config: {
        "connection_url": "sqlite:///... or postgresql://...",
        "table_name": "<table_name>",  # or "query": "<SELECT ...>"
        "limit": 1000
    }
    """

    def validate(self) -> None:
        if "connection_url" not in self.descriptor.config:
            raise ValueError("Missing 'connection_url' in descriptor.config")
        if "table_name" not in self.descriptor.config and "query" not in self.descriptor.config:
            raise ValueError("Either 'table_name' or 'query' must be provided in descriptor.config")

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        connection_url = self.descriptor.config["connection_url"]
        table_name = self.descriptor.config.get("table_name")
        query = self.descriptor.config.get("query")
        limit = self.descriptor.config.get("limit", 1000)

        records = await asyncio.to_thread(
            extract_sql,
            connection_url=connection_url,
            table_name=table_name,
            query=query,
            limit=limit,
        )

        for row_rec in records:
            yield RawDocument(
                source_id=self.descriptor.source_id,
                source_type=SourceType.SQL,
                raw_content=row_rec["text"],
                content_type="application/sql",
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "table_name": table_name,
                    "row_index": row_rec["row_index"],
                    "columns": row_rec["columns"],
                    "row_data": row_rec["row_data"],
                },
            )
