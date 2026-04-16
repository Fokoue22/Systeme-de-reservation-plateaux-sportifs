from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.api.deps import (
    get_disponibilite_service,
    get_plateau_service,
    get_reservation_service,
)
from app.application import DisponibiliteService, PlateauService, ReservationService
from app.infrastructure.repositories import (
    SQLiteDisponibiliteRepository,
    SQLitePlateauRepository,
    SQLiteReservationRepository,
)
from app.infrastructure.sqlite import SQLiteManager
from app.main import app


def _next_weekday(target_weekday: int) -> date:
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def _weekday_name(value: date) -> str:
    names = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    return names[value.weekday()]


def _build_client(tmp_path) -> TestClient:
    db = SQLiteManager(tmp_path / "m2_api.db")
    db.initialize_schema()
    db.seed_initial_data()

    plateau_repo = SQLitePlateauRepository(db)
    disponibilite_repo = SQLiteDisponibiliteRepository(db)
    reservation_repo = SQLiteReservationRepository(db)

    plateau_service = PlateauService(plateau_repo)
    disponibilite_service = DisponibiliteService(plateau_repo, disponibilite_repo)
    reservation_service = ReservationService(plateau_repo, disponibilite_repo, reservation_repo)

    app.dependency_overrides[get_plateau_service] = lambda: plateau_service
    app.dependency_overrides[get_disponibilite_service] = lambda: disponibilite_service
    app.dependency_overrides[get_reservation_service] = lambda: reservation_service

    return TestClient(app)


def test_m2_reservation_conflict_waitlist_and_promotion(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_plateau = client.post(
        "/m1/plateaux",
        json={
            "nom": "Terrain M2",
            "type_sport": "Tennis",
            "capacite": 4,
            "emplacement": "Zone B",
        },
    )
    assert create_plateau.status_code == 201
    plateau_id = create_plateau.json()["id"]

    monday = _next_weekday(0)

    first_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "alice",
            "date_reservation": monday.isoformat(),
            "creneau": {"debut": "09:00:00", "fin": "10:00:00"},
        },
    )
    assert first_res.status_code == 201
    assert first_res.json()["statut"] == "CONFIRMED"
    first_id = first_res.json()["id"]

    second_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "bob",
            "date_reservation": monday.isoformat(),
            "creneau": {"debut": "09:30:00", "fin": "10:30:00"},
        },
    )
    assert second_res.status_code == 201
    assert second_res.json()["statut"] == "WAITLISTED"
    second_id = second_res.json()["id"]

    cancel_first = client.post(f"/m2/reservations/{first_id}/cancel?policy=FLEXIBLE")
    assert cancel_first.status_code == 200
    assert cancel_first.json()["statut"] == "CANCELLED"

    listed = client.get(f"/m2/reservations?plateau_id={plateau_id}&date_reservation={monday.isoformat()}")
    assert listed.status_code == 200

    by_id = {item["id"]: item for item in listed.json()}
    assert by_id[first_id]["statut"] == "CANCELLED"
    assert by_id[second_id]["statut"] == "CONFIRMED"

    app.dependency_overrides.clear()


def test_m2_reservation_exact_conflict_goes_to_waitlist(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_plateau = client.post(
        "/m1/plateaux",
        json={
            "nom": "Exact Conflict Court",
            "type_sport": "Tennis",
            "capacite": 4,
            "emplacement": "Zone X",
        },
    )
    assert create_plateau.status_code == 201
    plateau_id = create_plateau.json()["id"]

    monday = _next_weekday(0)
    first = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "exact_a",
            "date_reservation": monday.isoformat(),
            "creneau": {"debut": "10:00:00", "fin": "10:30:00"},
            "nb_personnes": 2,
        },
    )
    assert first.status_code == 201
    assert first.json()["statut"] == "CONFIRMED"

    second = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "exact_b",
            "date_reservation": monday.isoformat(),
            "creneau": {"debut": "10:00:00", "fin": "10:30:00"},
            "nb_personnes": 1,
        },
    )
    assert second.status_code == 201
    assert second.json()["statut"] == "WAITLISTED"

    app.dependency_overrides.clear()


def test_m2_reservation_rejects_outside_availability(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_plateau = client.post(
        "/m1/plateaux",
        json={
            "nom": "Piscine M2",
            "type_sport": "Natation",
            "capacite": 20,
            "emplacement": "Zone C",
        },
    )
    assert create_plateau.status_code == 201
    plateau_id = create_plateau.json()["id"]

    tuesday = _next_weekday(1)

    invalid_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "charlie",
            "date_reservation": tuesday.isoformat(),
            "creneau": {"debut": "07:00:00", "fin": "07:30:00"},
        },
    )
    assert invalid_res.status_code == 409

    app.dependency_overrides.clear()


def test_m2_reservation_rejects_when_capacity_exceeded(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_plateau = client.post(
        "/m1/plateaux",
        json={
            "nom": "Capacity Court",
            "type_sport": "Volleyball",
            "capacite": 6,
            "emplacement": "Zone Cap",
        },
    )
    assert create_plateau.status_code == 201
    plateau_id = create_plateau.json()["id"]

    wednesday = _next_weekday(2)
    invalid_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "too_many",
            "date_reservation": wednesday.isoformat(),
            "creneau": {"debut": "09:00:00", "fin": "09:30:00"},
            "nb_personnes": 7,
        },
    )
    assert invalid_res.status_code == 409
    assert "doit etre entre" in invalid_res.json()["detail"]

    app.dependency_overrides.clear()


def test_m2_cancel_strict_24h_rejects_short_notice(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_plateau = client.post(
        "/m1/plateaux",
        json={
            "nom": "Terrain Strict Refus",
            "type_sport": "Soccer",
            "capacite": 22,
            "emplacement": "Zone D",
        },
    )
    assert create_plateau.status_code == 201
    plateau_id = create_plateau.json()["id"]

    today = date.today()
    create_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "strict_refus",
            "date_reservation": today.isoformat(),
            "creneau": {"debut": "21:00:00", "fin": "21:30:00"},
        },
    )
    assert create_res.status_code == 201
    reservation_id = create_res.json()["id"]

    cancel_response = client.post(f"/m2/reservations/{reservation_id}/cancel?policy=STRICT_24H")
    assert cancel_response.status_code == 409

    app.dependency_overrides.clear()


def test_m2_cancel_strict_24h_allows_early_cancellation(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_plateau = client.post(
        "/m1/plateaux",
        json={
            "nom": "Terrain Strict OK",
            "type_sport": "Soccer",
            "capacite": 22,
            "emplacement": "Zone E",
        },
    )
    assert create_plateau.status_code == 201
    plateau_id = create_plateau.json()["id"]

    future_day = date.today() + timedelta(days=3)
    create_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "strict_ok",
            "date_reservation": future_day.isoformat(),
            "creneau": {"debut": "10:00:00", "fin": "11:00:00"},
        },
    )
    assert create_res.status_code == 201
    reservation_id = create_res.json()["id"]

    cancel_response = client.post(f"/m2/reservations/{reservation_id}/cancel?policy=STRICT_24H")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["statut"] == "CANCELLED"

    app.dependency_overrides.clear()
