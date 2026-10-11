from pathlib import Path
from typing import Any, Dict

from app.extraction.errors import TextExtractionError


def extract_text(file_path: str) -> Dict[str, Any]:
    """
    Extracts text content from plain text (.txt) or Markdown (.md) files.
    """
    path = Path(file_path)
    if not path.exists():
        raise TextExtractionError(
            message=f"File not found: {file_path}",
            source_ref=str(file_path),
            error_code="TEXT_FILE_NOT_FOUND",
        )

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1")
        except Exception as exc:
            raise TextExtractionError(
                message=f"Failed to decode text file: {exc}",
                source_ref=str(file_path),
                error_code="TEXT_DECODE_ERROR",
            ) from exc
    except Exception as exc:
        raise TextExtractionError(
            message=f"Failed to read file: {exc}",
            source_ref=str(file_path),
            error_code="TEXT_READ_ERROR",
        ) from exc

    return {
        "file_path": str(path),
        "text": content,
        "char_count": len(content),
        "line_count": len(content.splitlines()),
    }
