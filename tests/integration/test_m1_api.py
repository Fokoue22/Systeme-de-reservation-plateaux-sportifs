from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.deps import get_disponibilite_service, get_plateau_service
from app.application import DisponibiliteService, PlateauService
from app.infrastructure.repositories import SQLiteDisponibiliteRepository, SQLitePlateauRepository
from app.infrastructure.sqlite import SQLiteManager
from app.main import app


def _build_client(tmp_path) -> TestClient:
    db = SQLiteManager(tmp_path / "m1_api.db")
    db.initialize_schema()

    plateau_repo = SQLitePlateauRepository(db)
    disponibilite_repo = SQLiteDisponibiliteRepository(db)

    plateau_service = PlateauService(plateau_repo)
    disponibilite_service = DisponibiliteService(plateau_repo, disponibilite_repo)

    app.dependency_overrides[get_plateau_service] = lambda: plateau_service
    app.dependency_overrides[get_disponibilite_service] = lambda: disponibilite_service

    return TestClient(app)


def test_plateau_crud_and_disponibilite_flow(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_response = client.post(
        "/m1/plateaux",
        json={
            "nom": "Gymnase Nord",
            "type_sport": "Volleyball",
            "capacite": 18,
            "emplacement": "Campus Nord",
        },
    )
    assert create_response.status_code == 201
    plateau_id = create_response.json()["id"]

    list_response = client.get("/m1/plateaux")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/m1/plateaux/{plateau_id}")
    assert get_response.status_code == 200
    assert get_response.json()["nom"] == "Gymnase Nord"

    update_response = client.put(
        f"/m1/plateaux/{plateau_id}",
        json={
            "nom": "Gymnase Nord Plus",
            "type_sport": "Volleyball",
            "capacite": 20,
            "emplacement": "Campus Nord",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["capacite"] == 20

    add_dispo_response = client.post(
        f"/m1/plateaux/{plateau_id}/disponibilites",
        json={
            "jour": "MONDAY",
            "creneau": {"debut": "09:00:00", "fin": "11:00:00"},
        },
    )
    assert add_dispo_response.status_code == 201

    conflict_response = client.post(
        f"/m1/plateaux/{plateau_id}/disponibilites",
        json={
            "jour": "MONDAY",
            "creneau": {"debut": "10:00:00", "fin": "12:00:00"},
        },
    )
    assert conflict_response.status_code == 409

    list_dispo_response = client.get(f"/m1/plateaux/{plateau_id}/disponibilites")
    assert list_dispo_response.status_code == 200
    assert len(list_dispo_response.json()) == 1

    delete_response = client.delete(f"/m1/plateaux/{plateau_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/m1/plateaux/{plateau_id}")
    assert missing_response.status_code == 404

    app.dependency_overrides.clear()


def test_not_found_routes_for_missing_plateau(tmp_path) -> None:
    client = _build_client(tmp_path)

    get_response = client.get("/m1/plateaux/999")
    assert get_response.status_code == 404

    list_dispo_response = client.get("/m1/plateaux/999/disponibilites")
    assert list_dispo_response.status_code == 404

    create_dispo_response = client.post(
        "/m1/plateaux/999/disponibilites",
        json={
            "jour": "TUESDAY",
            "creneau": {"debut": "08:00:00", "fin": "09:00:00"},
        },
    )
    assert create_dispo_response.status_code == 404

    app.dependency_overrides.clear()
