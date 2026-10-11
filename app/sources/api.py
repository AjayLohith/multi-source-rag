import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator, List

from app.contracts import RawDocument, SourceType
from app.extraction.api_extractor import extract_api
from app.sources.base import SourceAdapter


class APISource(SourceAdapter):
    """
    config: {
        "endpoint": "<https://api.example.com/...>",
        "headers": {...},
        "params": {...}
    }
    """

    def validate(self) -> None:
        if "endpoint" not in self.descriptor.config:
            raise ValueError("Missing 'endpoint' in descriptor.config")

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        endpoint = self.descriptor.config["endpoint"]
        headers = self.descriptor.config.get("headers")
        params = self.descriptor.config.get("params")

        records = await asyncio.to_thread(
            extract_api,
            endpoint=endpoint,
            headers=headers,
            params=params,
        )

        for rec in records:
            yield RawDocument(
                source_id=self.descriptor.source_id,
                source_type=SourceType.API,
                raw_content=rec["text"],
                content_type="application/json",
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "endpoint": endpoint,
                    "record_index": rec["record_index"],
                    "raw_data": rec["raw_data"],
                },
            )
