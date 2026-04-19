from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.application import AuthService
from app.infrastructure.repositories import SQLiteUserAccountRepository, SQLiteUserSessionRepository
from app.infrastructure.sqlite import SQLiteManager
from app.main import app


def _build_client(tmp_path) -> tuple[TestClient, AuthService]:
    db = SQLiteManager(tmp_path / "ui_auth_pages.db")
    db.initialize_schema()

    auth_service = AuthService(
        account_repo=SQLiteUserAccountRepository(db),
        session_repo=SQLiteUserSessionRepository(db),
    )

    app.dependency_overrides[get_auth_service] = lambda: auth_service
    return TestClient(app), auth_service


def test_home_shows_login_page_for_anonymous_user(tmp_path) -> None:
    client, _ = _build_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert "Service central d'authentification" in response.text

    app.dependency_overrides.clear()


def test_calendar_redirects_to_login_for_anonymous_user(tmp_path) -> None:
    client, _ = _build_client(tmp_path)

    response = client.get("/calendar", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers.get("location") == "/login"

    app.dependency_overrides.clear()


def test_calendar_displays_username_when_authenticated(tmp_path) -> None:
    client, auth_service = _build_client(tmp_path)

    _, session = auth_service.register(
        username="ui_user",
        password="secret12",
        email="ui@example.com",
        telephone=None,
    )

    response = client.get(
        "/calendar",
        cookies={"reservation_session": session.token},
    )

    assert response.status_code == 200
    assert "Planning des plateaux" in response.text
    assert "ui_user" in response.text

    app.dependency_overrides.clear()
