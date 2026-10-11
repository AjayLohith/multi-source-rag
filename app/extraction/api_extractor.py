from typing import Any, Dict, List, Optional, Union
import json
import httpx

from app.extraction.errors import APIExtractionError


def extract_api(
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Extracts structured JSON payload from a REST API endpoint.
    Emits schema-agnostic records formatted as text and raw payloads.
    """
    try:
        response = httpx.get(
            endpoint,
            headers=headers or {},
            params=params or {},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise APIExtractionError(
            message=f"Failed to query API endpoint {endpoint}: {exc}",
            source_ref=endpoint,
            error_code="API_REQUEST_FAILED",
        ) from exc

    # Normalize data into a list of records
    items: List[Any] = data if isinstance(data, list) else [data]

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
