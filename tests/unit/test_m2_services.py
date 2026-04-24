from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest

from app.application.m2_services import ConflictError, NotFoundError, ReservationService
from app.domain import CancellationPolicy, Creneau, Disponibilite, Plateau, Reservation, ReservationStatus, WeekDay
from app.domain.cancellation_policies import FlexibleCancellationPolicy, Strict24hCancellationPolicy
from app.domain.repositories import (
    DisponibiliteRepository,
    PlateauRepository,
    ReservationRepository,
)


def _weekday_for_date(value: date) -> WeekDay:
    return [
        WeekDay.MONDAY,
        WeekDay.TUESDAY,
        WeekDay.WEDNESDAY,
        WeekDay.THURSDAY,
        WeekDay.FRIDAY,
        WeekDay.SATURDAY,
        WeekDay.SUNDAY,
    ][value.weekday()]


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
        raise NotImplementedError

    def delete(self, plateau_id: int) -> bool:
        raise NotImplementedError


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


class InMemoryReservationRepository(ReservationRepository):
    def __init__(self) -> None:
        self._items: dict[int, Reservation] = {}
        self._next_id = 1

    def create(self, reservation: Reservation) -> Reservation:
        created = Reservation(
            id=self._next_id,
            plateau_id=reservation.plateau_id,
            utilisateur=reservation.utilisateur,
            date_reservation=reservation.date_reservation,
            creneau=reservation.creneau,
            statut=reservation.statut,
            nb_personnes=reservation.nb_personnes,
            created_at=reservation.created_at,
        )
        self._items[self._next_id] = created
        self._next_id += 1
        return created

    def get_by_id(self, reservation_id: int) -> Reservation | None:
        return self._items.get(reservation_id)

    def list_all(self) -> list[Reservation]:
        return list(self._items.values())

    def list_by_plateau_and_date(self, plateau_id: int, reservation_date: date) -> list[Reservation]:
        return [
            item for item in self._items.values()
            if item.plateau_id == plateau_id and item.date_reservation == reservation_date
        ]

    def update_reservation(
        self,
        reservation_id: int,
        plateau_id: int,
        reservation_date: date,
        creneau_debut: str,
        creneau_fin: str,
        statut: ReservationStatus,
        nb_personnes: int,
    ) -> Reservation | None:
        current = self._items.get(reservation_id)
        if current is None:
            return None
        updated = Reservation(
            id=current.id,
            plateau_id=plateau_id,
            utilisateur=current.utilisateur,
            date_reservation=reservation_date,
            creneau=Creneau(debut=time.fromisoformat(creneau_debut), fin=time.fromisoformat(creneau_fin)),
            statut=statut,
            nb_personnes=nb_personnes,
            created_at=current.created_at,
        )
        self._items[reservation_id] = updated
        return updated

    def update_status(self, reservation_id: int, status: ReservationStatus) -> Reservation | None:
        current = self._items.get(reservation_id)
        if current is None:
            return None
        updated = Reservation(
            id=current.id,
            plateau_id=current.plateau_id,
            utilisateur=current.utilisateur,
            date_reservation=current.date_reservation,
            creneau=current.creneau,
            statut=status,
            nb_personnes=current.nb_personnes,
            created_at=current.created_at,
        )
        self._items[reservation_id] = updated
        return updated


@pytest.fixture
def plateau_repo() -> InMemoryPlateauRepository:
    return InMemoryPlateauRepository()


@pytest.fixture
def disponibilite_repo() -> InMemoryDisponibiliteRepository:
    return InMemoryDisponibiliteRepository()


@pytest.fixture
def reservation_repo() -> InMemoryReservationRepository:
    return InMemoryReservationRepository()


@pytest.fixture
def reservation_service(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_repo: InMemoryReservationRepository,
) -> ReservationService:
    return ReservationService(plateau_repo, disponibilite_repo, reservation_repo)


def test_create_reservation_confirms_when_slot_available(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Gymnase", type_sport="Basket", capacite=10, emplacement="Nord"))
    reservation_date = date.today() + timedelta(days=1)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(9, 0), fin=time(11, 0)),
        )
    )

    created = reservation_service.create_reservation(
        plateau_id=plateau.id or 0,
        utilisateur="bob",
        reservation_date=reservation_date,
        slot=Creneau(debut=time(9, 0), fin=time(9, 30)),
        nb_personnes=2,
    )

    assert created.id == 1
    assert created.statut == ReservationStatus.CONFIRMED


def test_create_reservation_waitlists_when_overlapping_confirmed_reservation(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Tennis", type_sport="Tennis", capacite=4, emplacement="Ouest"))
    reservation_date = date.today() + timedelta(days=2)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(10, 0), fin=time(12, 0)),
        )
    )
    reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="alice",
            date_reservation=reservation_date,
            creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )

    waitlisted = reservation_service.create_reservation(
        plateau_id=plateau.id or 0,
        utilisateur="bob",
        reservation_date=date.today() + timedelta(days=2),
        slot=Creneau(debut=time(10, 0), fin=time(10, 30)),
        nb_personnes=1,
    )

    assert waitlisted.statut == ReservationStatus.WAITLISTED


def test_create_reservation_rejects_invalid_slot(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Piscine", type_sport="Natation", capacite=8, emplacement="Centre"))
    reservation_date = date.today() + timedelta(days=3)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(8, 0), fin=time(12, 0)),
        )
    )

    with pytest.raises(ConflictError, match="30 minutes"):
        reservation_service.create_reservation(
            plateau_id=plateau.id or 0,
            utilisateur="charlie",
            reservation_date=reservation_date,
            slot=Creneau(debut=time(9, 15), fin=time(9, 45)),
            nb_personnes=1,
        )


def test_create_reservation_rejects_outside_availability(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Gymnase", type_sport="Basket", capacite=10, emplacement="Nord"))
    reservation_date = date.today() + timedelta(days=3)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(9, 0), fin=time(11, 0)),
        )
    )

    with pytest.raises(ConflictError, match="hors disponibilite"):
        reservation_service.create_reservation(
            plateau_id=plateau.id or 0,
            utilisateur="dave",
            reservation_date=reservation_date,
            slot=Creneau(debut=time(11, 0), fin=time(11, 30)),
            nb_personnes=1,
        )


def test_update_reservation_promotes_when_permitted(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Salle", type_sport="Handball", capacite=12, emplacement="Est"))
    reservation_date = date.today() + timedelta(days=4)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(14, 0), fin=time(16, 0)),
        )
    )
    original = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            date_reservation=date.today() + timedelta(days=4),
            creneau=Creneau(debut=time(14, 0), fin=time(14, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=2,
        )
    )

    updated = reservation_service.update_reservation(
        reservation_id=original.id or 0,
        plateau_id=plateau.id or 0,
        utilisateur="emma",
        reservation_date=date.today() + timedelta(days=4),
        slot=Creneau(debut=time(14, 30), fin=time(15, 0)),
        nb_personnes=2,
    )

    assert updated.statut == ReservationStatus.CONFIRMED
    assert updated.creneau.debut == time(14, 30)


def test_cancel_reservation_promotes_waitlist(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Dojo", type_sport="Judo", capacite=6, emplacement="Ouest"))
    reservation_date = date.today() + timedelta(days=5)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(10, 0), fin=time(12, 0)),
        )
    )
    confirmed = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="fiona",
            date_reservation=date.today() + timedelta(days=5),
            creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )
    waitlisted = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="george",
            date_reservation=date.today() + timedelta(days=5),
            creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
            statut=ReservationStatus.WAITLISTED,
            nb_personnes=1,
        )
    )

    cancelled = reservation_service.cancel_reservation(confirmed.id or 0, FlexibleCancellationPolicy())

    assert cancelled.statut == ReservationStatus.CANCELLED
    promoted = reservation_repo.get_by_id(waitlisted.id or 0)
    assert promoted is not None
    assert promoted.statut == ReservationStatus.CONFIRMED


def test_create_reservation_rejects_missing_plateau(
    reservation_service: ReservationService,
) -> None:
    with pytest.raises(NotFoundError, match="plateau cible n'existe pas"):
        reservation_service.create_reservation(
            plateau_id=999,
            utilisateur="bob",
            reservation_date=date.today() + timedelta(days=1),
            slot=Creneau(debut=time(9, 0), fin=time(9, 30)),
            nb_personnes=1,
        )


def test_create_reservation_rejects_invalid_person_count(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Gymnase", type_sport="Basket", capacite=3, emplacement="Nord"))
    reservation_date = date.today() + timedelta(days=1)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(9, 0), fin=time(11, 0)),
        )
    )

    with pytest.raises(ConflictError, match="entre 1 et 3"):
        reservation_service.create_reservation(
            plateau_id=plateau.id or 0,
            utilisateur="dave",
            reservation_date=reservation_date,
            slot=Creneau(debut=time(9, 0), fin=time(9, 30)),
            nb_personnes=4,
        )


def test_update_reservation_raises_when_not_found(
    reservation_service: ReservationService,
) -> None:
    with pytest.raises(NotFoundError, match="Reservation introuvable"):
        reservation_service.update_reservation(
            reservation_id=999,
            plateau_id=1,
            utilisateur="emma",
            reservation_date=date.today() + timedelta(days=1),
            slot=Creneau(debut=time(14, 0), fin=time(14, 30)),
            nb_personnes=1,
        )


def test_update_reservation_rejects_cancelled_reservation(
    plateau_repo: InMemoryPlateauRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Salle", type_sport="Handball", capacite=12, emplacement="Est"))
    cancelled = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            date_reservation=date.today() + timedelta(days=4),
            creneau=Creneau(debut=time(14, 0), fin=time(14, 30)),
            statut=ReservationStatus.CANCELLED,
            nb_personnes=2,
        )
    )

    with pytest.raises(ConflictError, match="annulee"):
        reservation_service.update_reservation(
            reservation_id=cancelled.id or 0,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            reservation_date=cancelled.date_reservation,
            slot=Creneau(debut=time(14, 30), fin=time(15, 0)),
            nb_personnes=2,
        )


def test_update_reservation_rejects_wrong_owner(
    plateau_repo: InMemoryPlateauRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Salle", type_sport="Handball", capacite=12, emplacement="Est"))
    original = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            date_reservation=date.today() + timedelta(days=4),
            creneau=Creneau(debut=time(14, 0), fin=time(14, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=2,
        )
    )

    with pytest.raises(ConflictError, match="proprietaire"):
        reservation_service.update_reservation(
            reservation_id=original.id or 0,
            plateau_id=plateau.id or 0,
            utilisateur="other",
            reservation_date=original.date_reservation,
            slot=Creneau(debut=time(14, 30), fin=time(15, 0)),
            nb_personnes=2,
        )


def test_update_reservation_rejects_missing_plateau(
    plateau_repo: InMemoryPlateauRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    original = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=1,
            utilisateur="emma",
            date_reservation=date.today() + timedelta(days=4),
            creneau=Creneau(debut=time(14, 0), fin=time(14, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=2,
        )
    )

    with pytest.raises(NotFoundError, match="plateau cible n'existe pas"):
        reservation_service.update_reservation(
            reservation_id=original.id or 0,
            plateau_id=999,
            utilisateur="emma",
            reservation_date=original.date_reservation,
            slot=Creneau(debut=time(14, 30), fin=time(15, 0)),
            nb_personnes=2,
        )


def test_update_reservation_rejects_invalid_person_count(
    plateau_repo: InMemoryPlateauRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Salle", type_sport="Handball", capacite=2, emplacement="Est"))
    original = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            date_reservation=date.today() + timedelta(days=4),
            creneau=Creneau(debut=time(14, 0), fin=time(14, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )

    with pytest.raises(ConflictError, match="entre 1 et 2"):
        reservation_service.update_reservation(
            reservation_id=original.id or 0,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            reservation_date=original.date_reservation,
            slot=Creneau(debut=time(14, 30), fin=time(15, 0)),
            nb_personnes=3,
        )


def test_update_reservation_waitlists_when_slot_conflicts(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Salle", type_sport="Handball", capacite=12, emplacement="Est"))
    reservation_date = date.today() + timedelta(days=4)
    disponibilite_repo.create(
        Disponibilite(
            id=None,
            plateau_id=plateau.id or 0,
            jour=_weekday_for_date(reservation_date),
            creneau=Creneau(debut=time(14, 0), fin=time(16, 0)),
        )
    )
    reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="other",
            date_reservation=reservation_date,
            creneau=Creneau(debut=time(14, 0), fin=time(14, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=2,
        )
    )
    original = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            date_reservation=reservation_date,
            creneau=Creneau(debut=time(15, 0), fin=time(15, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=2,
        )
    )

    updated = reservation_service.update_reservation(
        reservation_id=original.id or 0,
        plateau_id=plateau.id or 0,
        utilisateur="emma",
        reservation_date=reservation_date,
        slot=Creneau(debut=time(14, 0), fin=time(14, 30)),
        nb_personnes=2,
    )

    assert updated.statut == ReservationStatus.WAITLISTED


def test_cancel_reservation_rejects_missing_id(
    reservation_service: ReservationService,
) -> None:
    with pytest.raises(NotFoundError, match="Reservation introuvable"):
        reservation_service.cancel_reservation(999, FlexibleCancellationPolicy())


def test_cancel_reservation_rejects_already_cancelled(
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    cancelled = reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=1,
            utilisateur="emma",
            date_reservation=date.today() + timedelta(days=1),
            creneau=Creneau(debut=time(9, 0), fin=time(9, 30)),
            statut=ReservationStatus.CANCELLED,
            nb_personnes=1,
        )
    )

    with pytest.raises(ConflictError, match="deja annulee"):
        reservation_service.cancel_reservation(cancelled.id or 0, FlexibleCancellationPolicy())


def test_cancel_reservation_rejects_strict_policy(
    plateau_repo: InMemoryPlateauRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Salle", type_sport="Handball", capacite=12, emplacement="Est"))
    reservation_date = date.today() + timedelta(days=1)
    reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="emma",
            date_reservation=reservation_date,
            creneau=Creneau(debut=time(0, 0), fin=time(0, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )

    with pytest.raises(ConflictError, match="Politique d'annulation non respectee"):
        reservation_service.cancel_reservation(1, Strict24hCancellationPolicy())


def test_list_reservations_filters_by_plateau_and_date(
    plateau_repo: InMemoryPlateauRepository,
    disponibilite_repo: InMemoryDisponibiliteRepository,
    reservation_repo: InMemoryReservationRepository,
    reservation_service: ReservationService,
) -> None:
    plateau = plateau_repo.create(Plateau(id=None, nom="Court", type_sport="Squash", capacite=2, emplacement="Sud"))
    reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="henry",
            date_reservation=date.today() + timedelta(days=6),
            creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )
    reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=plateau.id or 0,
            utilisateur="ida",
            date_reservation=date.today() + timedelta(days=7),
            creneau=Creneau(debut=time(10, 30), fin=time(11, 0)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )

    filtered = reservation_service.list_reservations(
        plateau_id=plateau.id or 0,
        reservation_date=date.today() + timedelta(days=6),
    )

    assert len(filtered) == 1
    assert filtered[0].utilisateur == "henry"

