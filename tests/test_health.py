from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_tracking_disabled() -> None:
    with TestClient(app) as client:
        response = client.get("/status/example-request-id")

    assert response.status_code == 503
    assert response.json()["detail"] == "DynamoDB status tracking is disabled"


def test_summarize_attempts_status_tracking(monkeypatch) -> None:
    stored_items = []
    monkeypatch.setattr(main_module, "store_request_status", stored_items.append)

    with TestClient(app) as client:
        response = client.post(
            "/summarize",
            json={"user_id": "ci-user", "text": "Short CI fallback text."},
        )

    assert response.status_code == 200
    assert len(stored_items) == 1
    assert stored_items[0]["request_id"] == response.json()["request_id"]
    assert stored_items[0]["user_id"] == "ci-user"
    assert stored_items[0]["status"] == "completed"
