from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app


def _next_weekday(target_weekday: int) -> date:
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def test_m2_reservation_conflict_waitlist_and_promotion() -> None:
    client = TestClient(app)

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

    add_dispo = client.post(
        f"/m1/plateaux/{plateau_id}/disponibilites",
        json={"jour": "MONDAY", "creneau": {"debut": "09:00:00", "fin": "12:00:00"}},
    )
    assert add_dispo.status_code == 201

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


def test_m2_reservation_rejects_outside_availability() -> None:
    client = TestClient(app)

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

    add_dispo = client.post(
        f"/m1/plateaux/{plateau_id}/disponibilites",
        json={"jour": "TUESDAY", "creneau": {"debut": "14:00:00", "fin": "16:00:00"}},
    )
    assert add_dispo.status_code == 201

    invalid_res = client.post(
        "/m2/reservations",
        json={
            "plateau_id": plateau_id,
            "utilisateur": "charlie",
            "date_reservation": tuesday.isoformat(),
            "creneau": {"debut": "09:00:00", "fin": "10:00:00"},
        },
    )
    assert invalid_res.status_code == 409
