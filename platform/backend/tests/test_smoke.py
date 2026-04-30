from fastapi.testclient import TestClient

from nims.main import app


def test_health() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "intentcenter-api"


def test_docs_json() -> None:
    client = TestClient(app)
    res = client.get("/docs/json")
    assert res.status_code == 200
    body = res.json()
    assert body["info"]["title"] == "IntentCenter API"
