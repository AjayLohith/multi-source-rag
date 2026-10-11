from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text

from app.extraction.errors import SQLExtractionError


def extract_sql(
    connection_url: str,
    table_name: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Extracts structured rows from a SQL database table or query using SQLAlchemy.
    Emits schema-agnostic 'column: value' text representations per row.
    Explicit limits prevent uncontrolled memory growth.

    Returns a list of dicts:
    [
        {
            "row_index": int,
            "text": str,
            "columns": list[str],
            "row_data": dict[str, Any],
        },
        ...
    ]
    Raises SQLExtractionError on connection or query failure.
    """
    if not table_name and not query:
        raise SQLExtractionError(
            message="Either table_name or query must be provided",
            source_ref=connection_url,
            error_code="SQL_CONFIG_MISSING",
        )

    target_ref = table_name or "custom_query"

    try:
        engine = create_engine(connection_url)
        with engine.connect() as conn:
            if query:
                stmt = text(query)
                result = conn.execute(stmt)
            else:
                # Read configured table with explicit limit
                stmt = text(f"SELECT * FROM {table_name} LIMIT :limit")
                result = conn.execute(stmt, {"limit": limit})

            rows = result.mappings().all()
            columns = list(result.keys())

            records: List[Dict[str, Any]] = []
            for idx, row in enumerate(rows):
                row_dict = dict(row)
                lines = [f"{col}: {val}" for col, val in row_dict.items() if val is not None]
                text_repr = "\n".join(lines)
                records.append(
                    {
                        "row_index": idx,
                        "text": text_repr,
                        "columns": columns,
                        "row_data": row_dict,
                    }
                )

            return records
    except SQLExtractionError:
        raise
    except Exception as exc:
        raise SQLExtractionError(
            message=f"Failed to extract SQL data: {exc}",
            source_ref=target_ref,
            error_code="SQL_QUERY_FAILED",
        ) from exc
