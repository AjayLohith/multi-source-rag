import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, List

from app.contracts import RawDocument, SourceType
from app.extraction.csv_extractor import extract_csv
from app.sources.base import SourceAdapter


class CSVSource(SourceAdapter):
    """config: {"path": "<file.csv or directory of .csv files>"}"""

    def validate(self) -> None:
        if "path" not in self.descriptor.config:
            raise ValueError("Missing 'path' in descriptor.config")
        path = Path(self.descriptor.config["path"])
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

    def _list_csv_files(self) -> List[Path]:
        path = Path(self.descriptor.config["path"])
        if path.is_dir():
            return sorted(path.glob("*.csv"))
        return [path]

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        for csv_path in self._list_csv_files():
            records = await asyncio.to_thread(extract_csv, str(csv_path))
            for row_rec in records:
                yield RawDocument(
                    source_id=self.descriptor.source_id,
                    source_type=SourceType.CSV,
                    raw_content=row_rec["text"],
                    content_type="text/csv",
                    fetched_at=datetime.now(timezone.utc),
                    metadata={
                        "source_file": str(csv_path),
                        "row_index": row_rec["row_index"],
                        "columns": row_rec["columns"],
                        "row_data": row_rec["row_data"],
                        "inferred_types": row_rec["inferred_types"],
                    },
                )
