from __future__ import annotations

from datetime import time

import pytest

from app.application import ConflictError, DisponibiliteService, NotFoundError, PlateauService
from app.domain.models import Creneau, Disponibilite, Plateau, WeekDay
from app.domain.repositories import DisponibiliteRepository, PlateauRepository


class InMemoryPlateauRepository(PlateauRepository):
    def __init__(self) -> None:
        self._items: dict[int, Plateau] = {}
        self._next_id = 1

    def create(self, plateau: Plateau) -> Plateau:
        created = Plateau(
            id=self._next_id,
            nom=plateau.nom,
            type_sport=plateau.type_sport,
            capacite=plateau.capacite,
            emplacement=plateau.emplacement,
        )
        self._items[self._next_id] = created
        self._next_id += 1
        return created

    def get_by_id(self, plateau_id: int) -> Plateau | None:
        return self._items.get(plateau_id)

    def list_all(self) -> list[Plateau]:
        return list(self._items.values())

    def update(self, plateau: Plateau) -> Plateau:
        if plateau.id is None or plateau.id not in self._items:
            raise KeyError("Plateau introuvable")
        self._items[plateau.id] = plateau
        return plateau

    def delete(self, plateau_id: int) -> bool:
        return self._items.pop(plateau_id, None) is not None


class InMemoryDisponibiliteRepository(DisponibiliteRepository):
    def __init__(self) -> None:
        self._items: dict[int, Disponibilite] = {}
        self._next_id = 1

    def create(self, disponibilite: Disponibilite) -> Disponibilite:
        created = Disponibilite(
            id=self._next_id,
            plateau_id=disponibilite.plateau_id,
            jour=disponibilite.jour,
            creneau=disponibilite.creneau,
        )
        self._items[self._next_id] = created
        self._next_id += 1
        return created

    def list_by_plateau(self, plateau_id: int) -> list[Disponibilite]:
        return [item for item in self._items.values() if item.plateau_id == plateau_id]


@pytest.fixture
def plateau_repo() -> InMemoryPlateauRepository:
    return InMemoryPlateauRepository()


@pytest.fixture
def disponibilite_repo() -> InMemoryDisponibiliteRepository:
    return InMemoryDisponibiliteRepository()


@pytest.fixture
def plateau_service(plateau_repo: InMemoryPlateauRepository) -> PlateauService:
    return PlateauService(plateau_repo)


@pytest.fixture
def disponibilite_service(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
) -> DisponibiliteService:
    return DisponibiliteService(plateau_repo, disponibilite_repo)


def test_create_plateau_assigns_id(plateau_service: PlateauService) -> None:
    created = plateau_service.create_plateau("Gymnase A", "Basketball", 20, "Campus Nord")
    assert created.id == 1
    assert created.nom == "Gymnase A"


def test_get_plateau_raises_when_missing(plateau_service: PlateauService) -> None:
    with pytest.raises(NotFoundError):
        plateau_service.get_plateau(999)


def test_delete_plateau_raises_when_missing(plateau_service: PlateauService) -> None:
    with pytest.raises(NotFoundError):
        plateau_service.delete_plateau(404)


def test_add_disponibilite_requires_existing_plateau(
    disponibilite_service: DisponibiliteService,
) -> None:
    with pytest.raises(NotFoundError):
        disponibilite_service.add_disponibilite(
            plateau_id=1,
            jour=WeekDay.MONDAY,
            creneau=Creneau(debut=time(9, 0), fin=time(10, 0)),
        )


def test_add_disponibilite_rejects_overlapping_slot(
    plateau_service: PlateauService,
    disponibilite_service: DisponibiliteService,
) -> None:
    plateau = plateau_service.create_plateau("Terrain A", "Tennis", 4, "Bloc Ouest")

    disponibilite_service.add_disponibilite(
        plateau_id=plateau.id or 0,
        jour=WeekDay.MONDAY,
        creneau=Creneau(debut=time(9, 0), fin=time(11, 0)),
    )

    with pytest.raises(ConflictError):
        disponibilite_service.add_disponibilite(
            plateau_id=plateau.id or 0,
            jour=WeekDay.MONDAY,
            creneau=Creneau(debut=time(10, 0), fin=time(12, 0)),
        )


def test_add_disponibilite_allows_non_overlapping_slot(
    plateau_service: PlateauService,
    disponibilite_service: DisponibiliteService,
) -> None:
    plateau = plateau_service.create_plateau("Piscine 1", "Natation", 12, "Centre")

    first = disponibilite_service.add_disponibilite(
        plateau_id=plateau.id or 0,
        jour=WeekDay.TUESDAY,
        creneau=Creneau(debut=time(8, 0), fin=time(10, 0)),
    )
    second = disponibilite_service.add_disponibilite(
        plateau_id=plateau.id or 0,
        jour=WeekDay.TUESDAY,
        creneau=Creneau(debut=time(10, 0), fin=time(12, 0)),
    )

    assert first.id == 1
    assert second.id == 2


def test_list_disponibilites_returns_items_for_plateau(
    plateau_service: PlateauService,
    disponibilite_service: DisponibiliteService,
) -> None:
    plateau = plateau_service.create_plateau("Gymnase B", "Volleyball", 16, "Campus Sud")
    disponibilite_service.add_disponibilite(
        plateau_id=plateau.id or 0,
        jour=WeekDay.FRIDAY,
        creneau=Creneau(debut=time(14, 0), fin=time(16, 0)),
    )

    result = disponibilite_service.list_disponibilites(plateau.id or 0)

    assert len(result) == 1
    assert result[0].jour == WeekDay.FRIDAY
