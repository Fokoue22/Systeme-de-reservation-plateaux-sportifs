from __future__ import annotations

from datetime import datetime, date, time, timedelta

import pytest

from app.application.m2_services import ReservationService
from app.domain.cancellation_policies import FlexibleCancellationPolicy
from app.domain.models import Creneau, Disponibilite, Plateau, Reservation, ReservationStatus, WeekDay
from app.domain.repositories import DisponibiliteRepository, PlateauRepository, ReservationRepository
from app.domain.notifications import NotificationEventType


class DummyNotificationService:
    def __init__(self):
        self.events: list[tuple[NotificationEventType, int]] = []

    def notify_reservation_event(self, event_type: NotificationEventType, reservation_id: int):
        self.events.append((event_type, reservation_id))
        return []


class InMemoryReservationRepository(ReservationRepository):
    def __init__(self):
        self.reservations: dict[int, Reservation] = {}
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
        )
        self.reservations[self._next_id] = created
        self._next_id += 1
        return created

    def get_by_id(self, reservation_id: int) -> Reservation | None:
        return self.reservations.get(reservation_id)

    def list_all(self) -> list[Reservation]:
        return list(self.reservations.values())

    def list_by_plateau_and_date(self, plateau_id: int, reservation_date: date) -> list[Reservation]:
        return [
            item
            for item in self.reservations.values()
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
        existing = self.reservations.get(reservation_id)
        if existing is None:
            return None
        updated = Reservation(
            id=existing.id,
            plateau_id=plateau_id,
            utilisateur=existing.utilisateur,
            date_reservation=reservation_date,
            creneau=Creneau(debut=time.fromisoformat(creneau_debut), fin=time.fromisoformat(creneau_fin)),
            statut=statut,
            nb_personnes=nb_personnes,
        )
        self.reservations[reservation_id] = updated
        return updated

    def update_status(self, reservation_id: int, status: ReservationStatus) -> Reservation | None:
        existing = self.reservations.get(reservation_id)
        if existing is None:
            return None
        updated = Reservation(
            id=existing.id,
            plateau_id=existing.plateau_id,
            utilisateur=existing.utilisateur,
            date_reservation=existing.date_reservation,
            creneau=existing.creneau,
            statut=status,
            nb_personnes=existing.nb_personnes,
        )
        self.reservations[reservation_id] = updated
        return updated


class InMemoryPlateauRepository(PlateauRepository):
    def __init__(self):
        self.plateaux: dict[int, Plateau] = {}

    def create(self, plateau: Plateau) -> Plateau:
        created = Plateau(
            id=plateau.id,
            nom=plateau.nom,
            type_sport=plateau.type_sport,
            capacite=plateau.capacite,
            emplacement=plateau.emplacement,
        )
        self.plateaux[created.id or 0] = created
        return created

    def get_by_id(self, plateau_id: int) -> Plateau | None:
        return self.plateaux.get(plateau_id)

    def list_all(self) -> list[Plateau]:
        return list(self.plateaux.values())

    def update(self, plateau: Plateau) -> Plateau:
        if plateau.id is None:
            raise ValueError("Plateau id required")
        self.plateaux[plateau.id] = plateau
        return plateau

    def delete(self, plateau_id: int) -> bool:
        return self.plateaux.pop(plateau_id, None) is not None


class InMemoryDisponibiliteRepository(DisponibiliteRepository):
    def __init__(self):
        self.disponibilites: list[Disponibilite] = []

    def create(self, disponibilite: Disponibilite) -> Disponibilite:
        self.disponibilites.append(disponibilite)
        return disponibilite

    def list_by_plateau(self, plateau_id: int) -> list[Disponibilite]:
        return [d for d in self.disponibilites if d.plateau_id == plateau_id]


class TestReservationService:
    def setup_method(self):
        self.plateau_repo = InMemoryPlateauRepository()
        self.disponibilite_repo = InMemoryDisponibiliteRepository()
        self.reservation_repo = InMemoryReservationRepository()
        self.notification_service = DummyNotificationService()
        self.service = ReservationService(
            plateau_repo=self.plateau_repo,
            disponibilite_repo=self.disponibilite_repo,
            reservation_repo=self.reservation_repo,
            notification_service=self.notification_service,
        )

        self.plateau_repo.create(Plateau(id=1, nom="Gymnase A", type_sport="Basketball", capacite=10, emplacement="Centre-ville"))
        current_weekday = list(WeekDay)[date.today().weekday()]
        self.disponibilite_repo.create(Disponibilite(id=1, plateau_id=1, jour=current_weekday, creneau=Creneau(debut=time(8, 0), fin=time(22, 0))))

    def test_create_reservation_confirms_when_available(self):
        result = self.service.create_reservation(
            plateau_id=1,
            utilisateur="alice",
            reservation_date=date.today() + timedelta(days=7),
            slot=Creneau(debut=time(10, 0), fin=time(10, 30)),
            nb_personnes=2,
        )

        assert result.statut == ReservationStatus.CONFIRMED
        assert result.nb_personnes == 2
        assert self.notification_service.events == [(NotificationEventType.RESERVATION_CONFIRMED, result.id or 0)]

    def test_create_reservation_waitlists_when_overlap(self):
        existing = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=7),
                creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=1,
            )
        )

        waitlisted = self.service.create_reservation(
            plateau_id=1,
            utilisateur="alice",
            reservation_date=date.today() + timedelta(days=7),
            slot=Creneau(debut=time(10, 0), fin=time(10, 30)),
            nb_personnes=1,
        )

        assert waitlisted.statut == ReservationStatus.WAITLISTED
        assert waitlisted.id != existing.id

    def test_create_reservation_rejects_invalid_plateau(self):
        with pytest.raises(Exception):
            self.service.create_reservation(
                plateau_id=999,
                utilisateur="alice",
                reservation_date=date.today() + timedelta(days=7),
                slot=Creneau(debut=time(10, 0), fin=time(10, 30)),
                nb_personnes=2,
            )

    def test_create_reservation_enforces_half_hour_slot(self):
        with pytest.raises(Exception):
            self.service.create_reservation(
                plateau_id=1,
                utilisateur="alice",
                reservation_date=date.today() + timedelta(days=7),
                slot=Creneau(debut=time(10, 15), fin=time(10, 45)),
                nb_personnes=2,
            )

    def test_list_reservations_filters_by_plateau_and_date(self):
        self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=7),
                creneau=Creneau(debut=time(12, 0), fin=time(12, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=2,
            )
        )
        self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="bob",
                date_reservation=date.today() + timedelta(days=14),
                creneau=Creneau(debut=time(12, 0), fin=time(12, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=2,
            )
        )

        results = self.service.list_reservations(plateau_id=1, reservation_date=date.today() + timedelta(days=7))
        assert len(results) == 1
        assert results[0].utilisateur == "alice"

    def test_update_reservation_owner_mismatch_raises_conflict(self):
        existing = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=7),
                creneau=Creneau(debut=time(11, 0), fin=time(11, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=2,
            )
        )

        with pytest.raises(Exception):
            self.service.update_reservation(
                reservation_id=existing.id or 0,
                plateau_id=1,
                utilisateur="bob",
                reservation_date=date.today() + timedelta(days=7),
                slot=Creneau(debut=time(11, 0), fin=time(11, 30)),
                nb_personnes=2,
            )

    def test_update_reservation_succeeds_and_sends_notification(self):
        existing = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=7),
                creneau=Creneau(debut=time(11, 0), fin=time(11, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=2,
            )
        )

        updated = self.service.update_reservation(
            reservation_id=existing.id or 0,
            plateau_id=1,
            utilisateur="alice",
            reservation_date=date.today() + timedelta(days=7),
            slot=Creneau(debut=time(12, 0), fin=time(12, 30)),
            nb_personnes=3,
        )

        assert updated.statut == ReservationStatus.CONFIRMED
        assert updated.nb_personnes == 3
        assert updated.creneau.debut == time(12, 0)
        assert any(event[0] == NotificationEventType.RESERVATION_UPDATED for event in self.notification_service.events)

    def test_cancel_reservation_promotes_waitlist(self):
        confirmed = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=7),
                creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=2,
            )
        )
        waitlisted = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="bob",
                date_reservation=date.today() + timedelta(days=7),
                creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
                statut=ReservationStatus.WAITLISTED,
                nb_personnes=1,
            )
        )

        result = self.service.cancel_reservation(confirmed.id or 0, FlexibleCancellationPolicy())

        assert result.statut == ReservationStatus.CANCELLED
        promoted = self.reservation_repo.get_by_id(waitlisted.id or 0)
        assert promoted is not None
        assert promoted.statut == ReservationStatus.CONFIRMED
        assert any(event[0] == NotificationEventType.WAITLIST_PROMOTED for event in self.notification_service.events)

    def test_cancel_nonexistent_reservation_raises_not_found(self):
        with pytest.raises(Exception):
            self.service.cancel_reservation(999, FlexibleCancellationPolicy())
