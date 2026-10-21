from fastapi.testclient import TestClient

from app.main import app


def test_analyze_valid_payload(monkeypatch):
    from app.api import routes
    async def fake_analyze(payload):
        from app.schemas.contract import AnalysisResult
        return AnalysisResult(risk_level="low", risk_score=1, summary="Sin señales claras.")
    async def no_database(*args, **kwargs):
        return None
    monkeypatch.setattr(routes, "analyze_with_ollama", fake_analyze)
    monkeypatch.setattr(routes, "SessionLocal", None)
    response = TestClient(app).post("/api/v1/analyze", json={"text":"Hola"})
    assert response.status_code == 200
    assert response.json()["risk_level"] == "low"


def test_analyze_rejects_empty_and_over_limit():
    client = TestClient(app)
    assert client.post("/api/v1/analyze", json={"text":""}).status_code == 422
    assert client.post("/api/v1/analyze", json={"text":"x" * 4001}).status_code == 422
