from typing import Any, Dict, Optional
from app.contracts import SourceType


class RetrievalFilter:
    """Builder for metadata-based retrieval constraints."""

    def __init__(
        self,
        source_type: Optional[SourceType] = None,
        source_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ):
        self.source_type = source_type
        self.source_id = source_id
        self.document_id = document_id

    def to_dict(self) -> Dict[str, Any]:
        filters = {}
        if self.source_type:
            filters["source_type"] = self.source_type.value
        if self.source_id:
            filters["source_id"] = self.source_id
        if self.document_id:
            filters["document_id"] = self.document_id
        return filters
