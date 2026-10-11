import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, List

from app.contracts import RawDocument, SourceType
from app.extraction.json_extractor import extract_json
from app.sources.base import SourceAdapter


class JSONSource(SourceAdapter):
    """config: {"path": "<file.json or directory of .json files>"}"""

    def validate(self) -> None:
        if "path" not in self.descriptor.config:
            raise ValueError("Missing 'path' in descriptor.config")
        path = Path(self.descriptor.config["path"])
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

    def _list_files(self) -> List[Path]:
        path = Path(self.descriptor.config["path"])
        if path.is_dir():
            return sorted(path.glob("*.json"))
        return [path]

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        for file_path in self._list_files():
            records = await asyncio.to_thread(extract_json, str(file_path))
            for rec in records:
                yield RawDocument(
                    source_id=self.descriptor.source_id,
                    source_type=SourceType.JSON,
                    raw_content=rec["text"],
                    content_type="application/json",
                    fetched_at=datetime.now(timezone.utc),
                    metadata={
                        "source_file": str(file_path),
                        "record_index": rec["record_index"],
                        "raw_data": rec["raw_data"],
                    },
                )
