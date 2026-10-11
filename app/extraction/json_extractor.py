import json
from pathlib import Path
from typing import Any, Dict, List

from app.extraction.errors import JSONExtractionError


def extract_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts structured JSON records from a file.
    Supports JSON arrays of objects or single dictionary structures.
    """
    path = Path(file_path)
    if not path.exists():
        raise JSONExtractionError(
            message=f"JSON file not found: {file_path}",
            source_ref=str(file_path),
            error_code="JSON_NOT_FOUND",
        )

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as exc:
        raise JSONExtractionError(
            message=f"Failed to parse JSON file: {exc}",
            source_ref=str(file_path),
            error_code="JSON_PARSE_ERROR",
        ) from exc

    items = data if isinstance(data, list) else [data]
    records: List[Dict[str, Any]] = []

    for idx, item in enumerate(items):
        if isinstance(item, dict):
            lines = [f"{k}: {v}" for k, v in item.items() if v is not None]
            text_repr = "\n".join(lines)
            row_dict = item
        else:
            text_repr = str(item)
            row_dict = {"value": item}

        records.append({
            "record_index": idx,
            "text": text_repr,
            "raw_data": row_dict,
        })

    return records
