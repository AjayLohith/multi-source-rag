from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_api_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_api_ingest_and_search_and_chat():
    # 1. Ingest fixture via API
    ingest_payload = {
        "source_type": "csv",
        "name": "API Test Employees",
        "config": {"path": str(FIXTURES_DIR / "changed_order.csv")},
    }
    resp = client.post("/ingest", json=ingest_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert "status" in data

    # 2. Search endpoint
    search_payload = {"query": "Alice Engineering", "top_k": 2}
    search_resp = client.post("/search", json=search_payload)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert "citations" in search_data
    assert "assembled_context" in search_data

    # 3. Chat endpoint
    chat_payload = {"query": "What department is Alice in?", "top_k": 2}
    chat_resp = client.post("/chat", json=chat_payload)
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "answer" in chat_data
    assert "citations" in chat_data
