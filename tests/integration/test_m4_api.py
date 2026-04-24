from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.api.deps import (
    get_disponibilite_service,
    get_notification_service,
    get_plateau_service,
    get_reservation_service,
)
from app.application import DisponibiliteService, NotificationService, PlateauService, ReservationService
from app.application.m4_delivery import ConsoleEmailSender, ConsoleSmsSender
from app.infrastructure.repositories import (
    SQLiteDisponibiliteRepository,
    SQLiteNotificationPreferenceRepository,
    SQLiteNotificationRepository,
    SQLitePlateauRepository,
    SQLiteReminderTaskRepository,
    SQLiteReservationRepository,
)
from app.infrastructure.sqlite import SQLiteManager
from app.main import app


def _build_client(tmp_path) -> TestClient:
    db = SQLiteManager(tmp_path / "m4_api.db")
    db.initialize_schema()
    db.seed_initial_data()

    plateau_repo = SQLitePlateauRepository(db)
    disponibilite_repo = SQLiteDisponibiliteRepository(db)
    reservation_repo = SQLiteReservationRepository(db)
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

    app.dependency_overrides[get_plateau_service] = lambda: plateau_service
    app.dependency_overrides[get_disponibilite_service] = lambda: disponibilite_service
    app.dependency_overrides[get_reservation_service] = lambda: reservation_service
    app.dependency_overrides[get_notification_service] = lambda: notification_service

    return TestClient(app)


def test_m4_preferences_upsert_and_get(tmp_path) -> None:
    client = _build_client(tmp_path)

    get_resp = client.get("/m4/preferences/alice")
    assert get_resp.status_code == 200
    assert get_resp.json()["utilisateur"] == "alice"

    update_resp = client.put(
        "/m4/preferences/alice",
        json={
            "email": "alice@example.com",
            "telephone": "+15145550001",
            "email_enabled": True,
            "sms_enabled": True,
            "weekly_summary_enabled": False,
            "is_admin": False,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["email"] == "alice@example.com"
    assert update_resp.json()["sms_enabled"] is True

    app.dependency_overrides.clear()


def test_m4_create_reservation_emits_notification(tmp_path) -> None:
    client = _build_client(tmp_path)

    plateaux = client.get("/m1/plateaux").json()
    plateau_id = plateaux[0]["id"]

    create_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "bob",
            "date_reservation": (date.today() + timedelta(days=1)).isoformat(),
            "creneau": {"debut": "09:00:00", "fin": "09:30:00"},
            "nb_personnes": 1,
        },
    )
    assert create_res.status_code == 201

    notifications = client.get("/m4/notifications", params={"utilisateur": "bob"})
    assert notifications.status_code == 200
    payload = notifications.json()
    assert len(payload) >= 1
    assert any(item["event_type"] in {"RESERVATION_CONFIRMED", "RESERVATION_WAITLISTED"} for item in payload)

    app.dependency_overrides.clear()


def test_m4_process_due_reminders(tmp_path) -> None:
    client = _build_client(tmp_path)

    plateaux = client.get("/m1/plateaux").json()
    plateau_id = plateaux[0]["id"]

    create_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "carol",
            "date_reservation": (date.today() - timedelta(days=1)).isoformat(),  # Yesterday
            "creneau": {"debut": "10:00:00", "fin": "10:30:00"},
            "nb_personnes": 1,
        },
    )
    assert create_res.status_code == 201

    run_resp = client.post("/m4/reminders/run")
    assert run_resp.status_code == 200
    assert run_resp.json()["processed"] >= 1

    notifications = client.get("/m4/notifications", params={"utilisateur": "carol"}).json()
    assert any(item["event_type"] == "REMINDER_24H" for item in notifications)

    app.dependency_overrides.clear()


def test_m4_weekly_summary_for_admins(tmp_path) -> None:
    client = _build_client(tmp_path)

    pref_resp = client.put(
        "/m4/preferences/admin_user",
        json={
            "email": "admin@example.com",
            "telephone": None,
            "email_enabled": True,
            "sms_enabled": False,
            "weekly_summary_enabled": True,
            "is_admin": True,
        },
    )
    assert pref_resp.status_code == 200

    plateaux = client.get("/m1/plateaux").json()
    plateau_id = plateaux[0]["id"]

    create_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "eve",
            "date_reservation": (date.today() + timedelta(days=2)).isoformat(),
            "creneau": {"debut": "11:00:00", "fin": "11:30:00"},
            "nb_personnes": 1,
        },
    )
    assert create_res.status_code == 201

    run_summary = client.post("/m4/weekly-summary/run")
    assert run_summary.status_code == 200
    assert run_summary.json()["sent"] >= 1

    admin_notifications = client.get("/m4/notifications", params={"utilisateur": "admin_user"}).json()
    assert any(item["event_type"] == "WEEKLY_SUMMARY" for item in admin_notifications)

    app.dependency_overrides.clear()
