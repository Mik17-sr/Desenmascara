from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.contract import AnalysisResult

# Without a "with" block TestClient skips the lifespan, so the tests never call Ollama.
client = TestClient(app)


def test_health():
    assert client.get("/health").status_code == 200


def test_blank_text_is_rejected():
    assert client.post("/api/v1/analyze", json={"text": "   "}).status_code == 422


def test_text_over_4000_characters_is_rejected():
    assert client.post("/api/v1/analyze", json={"text": "x" * 4001}).status_code == 422


def test_database_failure_does_not_break_the_response():
    result = AnalysisResult(risk_level="low", risk_score=10, summary="Mensaje normal.")
    with (
        patch("app.api.routes.analyze_with_ollama", AsyncMock(return_value=result)),
        patch("app.api.routes.SessionLocal", object()),
        patch("app.api.routes.repository.save_analysis", AsyncMock(side_effect=OSError("db down"))) as save,
    ):
        response = client.post("/api/v1/analyze", json={"text": "Hola"})
    assert response.status_code == 200
    assert response.json()["risk_level"] == "low"
    save.assert_awaited_once()
