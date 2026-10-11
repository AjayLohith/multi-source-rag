import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, List

from app.contracts import RawDocument, SourceType
from app.extraction.doc_extractor import extract_docx
from app.sources.base import SourceAdapter


class DocSource(SourceAdapter):
    """config: {"path": "<file.docx or directory of .docx files>"}"""

    def validate(self) -> None:
        if "path" not in self.descriptor.config:
            raise ValueError("Missing 'path' in descriptor.config")
        path = Path(self.descriptor.config["path"])
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

    def _list_files(self) -> List[Path]:
        path = Path(self.descriptor.config["path"])
        if path.is_dir():
            return sorted(path.glob("*.docx"))
        return [path]

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        for file_path in self._list_files():
            data = await asyncio.to_thread(extract_docx, str(file_path))
            yield RawDocument(
                source_id=self.descriptor.source_id,
                source_type=SourceType.DOCX,
                raw_content=data["text"],
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "source_file": str(file_path),
                    "paragraph_count": data["paragraph_count"],
                    "table_count": data["table_count"],
                },
            )
