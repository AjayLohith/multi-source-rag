from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

from app.extraction.errors import CSVExtractionError


def extract_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts tabular rows from a CSV file using pandas.
    Schema-agnostic: emits 'column: value' text blobs from whatever columns
    actually exist. Normalization of columns/aliases is deferred to Day 3.

    Returns a list of dicts:
    [
        {
            "row_index": int,
            "text": str,
            "columns": list[str],
            "row_data": dict[str, Any],
            "inferred_types": dict[str, str],
        },
        ...
    ]
    Raises CSVExtractionError on failure.
    """
    path = Path(file_path)
    if not path.exists():
        raise CSVExtractionError(
            message=f"CSV file not found: {file_path}",
            source_ref=str(file_path),
            error_code="CSV_NOT_FOUND",
        )

    try:
        df = pd.read_csv(str(path))
    except pd.errors.EmptyDataError:
        return []
    except Exception as exc:
        raise CSVExtractionError(
            message=f"Failed to parse CSV file: {exc}",
            source_ref=str(file_path),
            error_code="CSV_PARSE_ERROR",
        ) from exc

    columns = [str(c) for c in df.columns]
    inferred_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    records: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        # Build humanized, schema-agnostic text: "col: val" for all non-null fields
        lines = []
        row_data = {}
        for col in columns:
            val = row[col]
            if pd.notna(val):
                lines.append(f"{col}: {val}")
                row_data[col] = val
            else:
                row_data[col] = None

        text_repr = "\n".join(lines)
        records.append(
            {
                "row_index": int(idx),
                "text": text_repr,
                "columns": columns,
                "row_data": row_data,
                "inferred_types": inferred_types,
            }
        )

    return records
