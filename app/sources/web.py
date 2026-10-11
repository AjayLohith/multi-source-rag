import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator, List, Union

from app.contracts import RawDocument, SourceType
from app.extraction.web_extractor import extract_web
from app.sources.base import SourceAdapter


class WebSource(SourceAdapter):
    """config: {"url": "<url>"} or {"urls": ["<url1>", "<url2>"]}"""

    def validate(self) -> None:
        if "url" not in self.descriptor.config and "urls" not in self.descriptor.config:
            raise ValueError("Missing 'url' or 'urls' in descriptor.config")

    def _get_urls(self) -> List[str]:
        if "urls" in self.descriptor.config:
            return list(self.descriptor.config["urls"])
        return [self.descriptor.config["url"]]

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        for url in self._get_urls():
            data = await asyncio.to_thread(extract_web, url)
            yield RawDocument(
                source_id=self.descriptor.source_id,
                source_type=SourceType.WEB,
                raw_content=data["text"],
                content_type="text/html",
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "url": data["url"],
                    "title": data["title"],
                    "status_code": data["status_code"],
                },
            )
