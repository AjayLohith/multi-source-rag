import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from app.contracts import RawDocument, SourceType
from app.extraction.pdf_extractor import extract_pdf
from app.sources.base import SourceAdapter


class PDFSource(SourceAdapter):
    """config: {"path": "<file.pdf or a directory of .pdf files>"}"""

    def validate(self) -> None:
        if "path" not in self.descriptor.config:
            raise ValueError("Missing 'path' in descriptor.config")
        path = Path(self.descriptor.config["path"])
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

    def _list_pdf_files(self) -> list[Path]:
        path = Path(self.descriptor.config["path"])
        if path.is_dir():
            return sorted(path.glob("*.pdf"))
        return [path]

    async def fetch(self) -> AsyncIterator[RawDocument]:
        self.validate()
        for pdf_path in self._list_pdf_files():
            pages = await asyncio.to_thread(extract_pdf, str(pdf_path))

            full_text = "\n\n".join(
                f"[PAGE {p['page_number']}]\n{p['text']}" for p in pages
            )
            yield RawDocument(
                source_id=self.descriptor.source_id,
                source_type=SourceType.PDF,
                raw_content=full_text,
                content_type="application/pdf",
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "source_file": str(pdf_path),
                    "total_pages": len(pages),
                    # Page numbers preserved here, not flattened away
                    "pages": [
                        {
                            "page_number": p["page_number"],
                            "char_count": p["char_count"],
                            "ocr_used": p["ocr_used"],
                        }
                        for p in pages
                    ],
                },
            )
