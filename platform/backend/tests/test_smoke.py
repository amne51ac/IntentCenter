from fastapi.testclient import TestClient

from nims.main import app


def test_health() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_docs_json() -> None:
    client = TestClient(app)
    res = client.get("/docs/json")
    assert res.status_code == 200
    body = res.json()
    assert body["info"]["title"] == "NIMS Platform API"
