from app.retrieval.retriever import default_retriever
from app.retrieval.filters import RetrievalFilter
from app.contracts import SourceType


def test_retriever_context_and_citation_builder():
    mock_results = [
        {
            "chunk_id": "chk-1",
            "document_id": "doc-1",
            "source_name": "leave_policy.pdf",
            "source_type": "pdf",
            "score": 0.88,
            "text": "Full-time employees receive 24 days annual paid leave.",
            "metadata": {"page_number": 3, "source_type": "pdf", "source_name": "leave_policy.pdf"},
        },
        {
            "chunk_id": "chk-2",
            "document_id": "doc-2",
            "source_name": "employees.csv",
            "source_type": "csv",
            "score": 0.75,
            "text": "id: 101, name: Alice, department: Engineering",
            "metadata": {"row_index": 12, "source_type": "csv", "source_name": "employees.csv"},
        },
    ]

    context, citations = default_retriever.build_context(mock_results, max_chars=1000)

    assert "[Source 1: leave_policy.pdf (pdf) | Page: 3]" in context
    assert "[Source 2: employees.csv (csv) | Row: 12]" in context
    assert len(citations) == 2
    assert citations[0]["citation_id"] == 1
    assert citations[0]["source_name"] == "leave_policy.pdf"
    assert citations[1]["citation_id"] == 2
    assert citations[1]["source_name"] == "employees.csv"


def test_retrieval_filter_builder():
    rf = RetrievalFilter(source_type=SourceType.PDF, source_id="src-100")
    d = rf.to_dict()
    assert d["source_type"] == "pdf"
    assert d["source_id"] == "src-100"
    assert "document_id" not in d
