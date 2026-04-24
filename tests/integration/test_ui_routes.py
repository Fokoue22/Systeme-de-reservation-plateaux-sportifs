from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_home_page_returns_calendar_html() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "calendar" in response.text.lower()


def test_calendar_page_returns_calendar_html() -> None:
    client = TestClient(app)

    response = client.get("/calendar")

    assert response.status_code == 200
    assert "calendar" in response.text.lower()
