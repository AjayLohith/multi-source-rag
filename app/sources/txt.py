import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, List

from app.contracts import RawDocument, SourceType
from app.extraction.text_extractor import extract_text
from app.sources.base import SourceAdapter


class TextSource(SourceAdapter):
    """config: {"path": "<file.txt or directory of .txt files>"}"""

    def validate(self) -> None:
        if "path" not in self.descriptor.config:
            raise ValueError("Missing 'path' in descriptor.config")
        path = Path(self.descriptor.config["path"])
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

    def _list_files(self) -> List[Path]:
        path = Path(self.descriptor.config["path"])
        if path.is_dir():
            return sorted(path.glob("*.txt"))
        return [path]

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        for file_path in self._list_files():
            data = await asyncio.to_thread(extract_text, str(file_path))
            yield RawDocument(
                source_id=self.descriptor.source_id,
                source_type=SourceType.TEXT,
                raw_content=data["text"],
                content_type="text/plain",
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "source_file": str(file_path),
                    "char_count": data["char_count"],
                    "line_count": data["line_count"],
                },
            )
