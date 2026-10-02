from fastapi.testclient import TestClient

from app.main import app


def test_health_is_available_without_model():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "thunder-models"
    assert "model_ready" in body


def test_openai_models_endpoint():
    response = TestClient(app).get("/v1/models")
    assert response.status_code == 200
    assert response.json()["object"] == "list"
