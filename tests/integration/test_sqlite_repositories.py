from __future__ import annotations

from datetime import date
from datetime import time

from app.domain.models import Creneau, Disponibilite, Plateau, Reservation, ReservationStatus, WeekDay
from app.infrastructure.repositories import (
    SQLiteDisponibiliteRepository,
    SQLitePlateauRepository,
    SQLiteReservationRepository,
)
from app.infrastructure.sqlite import SQLiteManager


def test_sqlite_plateau_repository_crud(tmp_path) -> None:
    db = SQLiteManager(tmp_path / "m1_repo.db")
    db.initialize_schema()
    repo = SQLitePlateauRepository(db)

    created = repo.create(
        Plateau(
            id=None,
            nom="Gymnase Central",
            type_sport="Basketball",
            capacite=24,
            emplacement="Campus A",
        )
    )
    assert created.id is not None

    fetched = repo.get_by_id(created.id or 0)
    assert fetched is not None
    assert fetched.nom == "Gymnase Central"

    updated = repo.update(
        Plateau(
            id=created.id,
            nom="Gymnase Central 2",
            type_sport="Basketball",
            capacite=30,
            emplacement="Campus A",
        )
    )
    assert updated.capacite == 30

    all_items = repo.list_all()
    assert len(all_items) == 1

    deleted = repo.delete(created.id or 0)
    assert deleted is True
    assert repo.get_by_id(created.id or 0) is None


def test_sqlite_disponibilite_repository_create_and_list(tmp_path) -> None:
    db = SQLiteManager(tmp_path / "m1_dispo.db")
    db.initialize_schema()

    plateau_repo = SQLitePlateauRepository(db)
    dispo_repo = SQLiteDisponibiliteRepository(db)

    plateau = plateau_repo.create(
        Plateau(
            id=None,
            nom="Terrain Tennis 1",
            type_sport="Tennis",
            capacite=4,
            emplacement="Bloc Ouest",
        )
    )

    created = dispo_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=WeekDay.WEDNESDAY,
            creneau=Creneau(debut=time(9, 0), fin=time(11, 0)),
        )
    )

    items = dispo_repo.list_by_plateau(plateau.id or 0)
    assert len(items) == 1
    assert items[0].id == created.id
    assert items[0].jour == WeekDay.WEDNESDAY
    assert items[0].creneau.debut == time(9, 0)
    assert items[0].creneau.fin == time(11, 0)


def test_sqlite_reservation_exact_slot_conflict_falls_back_to_waitlist(tmp_path) -> None:
    db = SQLiteManager(tmp_path / "m2_repo.db")
    db.initialize_schema()

    plateau_repo = SQLitePlateauRepository(db)
    reservation_repo = SQLiteReservationRepository(db)

    plateau = plateau_repo.create(
        Plateau(
            id=None,
            nom="Court Exact",
            type_sport="Tennis",
            capacite=4,
            emplacement="Zone Test",
        )
    )

    first = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="alice",
            date_reservation=date(2026, 4, 20),
            creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )
    assert first.statut == ReservationStatus.CONFIRMED

    second = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="bob",
            date_reservation=date(2026, 4, 20),
            creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )
    assert second.statut == ReservationStatus.WAITLISTED
