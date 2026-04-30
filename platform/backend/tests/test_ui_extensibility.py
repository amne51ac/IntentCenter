from fastapi.testclient import TestClient

from nims.main import app


def test_page_registry_requires_auth() -> None:
    client = TestClient(app)
    res = client.get("/v1/ui/page-registry")
    assert res.status_code == 401


def test_placements_requires_auth() -> None:
    client = TestClient(app)
    res = client.get("/v1/ui/placements", params={"pageId": "inventory.objectView"})
    assert res.status_code == 401
