from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Bid Document Agent API"
    assert payload["phase"] == "rag-mvp"


def test_health() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"] == "Bid Document Agent"
