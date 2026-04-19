from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.api.deps import (
    get_auth_service,
    get_disponibilite_service,
    get_notification_service,
    get_plateau_service,
    get_reservation_service,
)
from app.application import AuthService, DisponibiliteService, NotificationService, PlateauService, ReservationService
from app.application.m4_delivery import ConsoleEmailSender, ConsoleSmsSender
from app.infrastructure.repositories import (
    SQLiteDisponibiliteRepository,
    SQLiteNotificationPreferenceRepository,
    SQLiteNotificationRepository,
    SQLitePlateauRepository,
    SQLiteReminderTaskRepository,
    SQLiteReservationRepository,
    SQLiteUserAccountRepository,
    SQLiteUserSessionRepository,
)
from app.infrastructure.sqlite import SQLiteManager
from app.main import app


def _build_client(tmp_path) -> TestClient:
    db = SQLiteManager(tmp_path / "m5_api.db")
    db.initialize_schema()
    db.seed_initial_data()

    plateau_repo = SQLitePlateauRepository(db)
    disponibilite_repo = SQLiteDisponibiliteRepository(db)
    reservation_repo = SQLiteReservationRepository(db)
    account_repo = SQLiteUserAccountRepository(db)
    session_repo = SQLiteUserSessionRepository(db)

    pref_repo = SQLiteNotificationPreferenceRepository(db)
    notification_repo = SQLiteNotificationRepository(db)
    reminder_repo = SQLiteReminderTaskRepository(db)

    plateau_service = PlateauService(plateau_repo)
    disponibilite_service = DisponibiliteService(plateau_repo, disponibilite_repo)
    notification_service = NotificationService(
        preference_repo=pref_repo,
        notification_repo=notification_repo,
        reminder_task_repo=reminder_repo,
        reservation_repo=reservation_repo,
        plateau_repo=plateau_repo,
        email_sender=ConsoleEmailSender(),
        sms_sender=ConsoleSmsSender(),
    )
    reservation_service = ReservationService(
        plateau_repo=plateau_repo,
        disponibilite_repo=disponibilite_repo,
        reservation_repo=reservation_repo,
        notification_service=notification_service,
    )
    auth_service = AuthService(account_repo=account_repo, session_repo=session_repo)

    app.dependency_overrides[get_plateau_service] = lambda: plateau_service
    app.dependency_overrides[get_disponibilite_service] = lambda: disponibilite_service
    app.dependency_overrides[get_reservation_service] = lambda: reservation_service
    app.dependency_overrides[get_notification_service] = lambda: notification_service
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    return TestClient(app)


def test_m5_register_login_me_logout_flow(tmp_path) -> None:
    client = _build_client(tmp_path)

    register = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "password": "secret12",
            "email": "alice@example.com",
            "telephone": "+15145550123",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == "alice"

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    logout = client.post("/auth/logout")
    assert logout.status_code == 204

    me_after = client.get("/auth/me")
    assert me_after.status_code == 401

    login = client.post(
        "/auth/login",
        json={"username": "alice", "password": "secret12"},
    )
    assert login.status_code == 200
    assert login.json()["username"] == "alice"

    app.dependency_overrides.clear()


def test_m5_authenticated_user_overrides_reservation_payload_user(tmp_path) -> None:
    client = _build_client(tmp_path)

    register = client.post(
        "/auth/register",
        json={
            "username": "owner_user",
            "password": "secret12",
            "email": "owner@example.com",
        },
    )
    assert register.status_code == 201

    plateaux = client.get("/m1/plateaux")
    assert plateaux.status_code == 200
    plateau_id = plateaux.json()[0]["id"]

    created = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "spoofed_user",
            "date_reservation": date.today().isoformat(),
            "creneau": {"debut": "09:00:00", "fin": "09:30:00"},
            "nb_personnes": 1,
        },
    )
    assert created.status_code == 201
    assert created.json()["utilisateur"] == "owner_user"

    app.dependency_overrides.clear()
