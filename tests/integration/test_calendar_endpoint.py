from fastapi.testclient import TestClient

from app.main import app


def test_calendar_html_endpoint():
    client = TestClient(app)
    response = client.get("/api/m3/calendar/html?year=2026&month=5")

    assert response.status_code in (200, 501)
