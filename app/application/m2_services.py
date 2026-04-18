from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from app.domain import CancellationPolicy, Creneau, Reservation, ReservationStatus, WeekDay
from app.domain.notifications import NotificationEventType
from app.domain.repositories import DisponibiliteRepository, PlateauRepository, ReservationRepository

from .m1_services import ConflictError, NotFoundError, _overlaps

if TYPE_CHECKING:
    from .m4_services import NotificationService


def _weekday_from_date(value: date) -> WeekDay:
    days = [
        WeekDay.MONDAY,
        WeekDay.TUESDAY,
        WeekDay.WEDNESDAY,
        WeekDay.THURSDAY,
        WeekDay.FRIDAY,
        WeekDay.SATURDAY,
        WeekDay.SUNDAY,
    ]
    return days[value.weekday()]


class ReservationService:
    def __init__(
        self,
        plateau_repo: PlateauRepository,
        disponibilite_repo: DisponibiliteRepository,
        reservation_repo: ReservationRepository,
        notification_service: NotificationService | None = None,
    ):
        self.plateau_repo = plateau_repo
        self.disponibilite_repo = disponibilite_repo
        self.reservation_repo = reservation_repo
        self.notification_service = notification_service

    def _ensure_half_hour_slot(self, slot: Creneau) -> None:
        valid_minutes = {0, 30}
        if slot.debut.minute not in valid_minutes or slot.fin.minute not in valid_minutes:
            raise ConflictError("Les reservations doivent respecter des creneaux de 30 minutes (08:00, 08:30, etc.).")

    def _ensure_availability(self, plateau_id: int, reservation_date: date, slot: Creneau) -> None:
        weekday = _weekday_from_date(reservation_date)
        disponibilites = self.disponibilite_repo.list_by_plateau(plateau_id)

        for disponibilite in disponibilites:
            if disponibilite.jour != weekday:
                continue
            if disponibilite.creneau.debut <= slot.debut and slot.fin <= disponibilite.creneau.fin:
                return

        raise ConflictError("Le creneau demande est hors disponibilite pour ce plateau.")

    def create_reservation(
        self,
        plateau_id: int,
        utilisateur: str,
        reservation_date: date,
        slot: Creneau,
        nb_personnes: int = 1,
    ) -> Reservation:
        plateau = self.plateau_repo.get_by_id(plateau_id)
        if plateau is None:
            raise NotFoundError("Le plateau cible n'existe pas.")

        min_capacite = 1
        max_capacite = plateau.capacite
        if nb_personnes < min_capacite or nb_personnes > max_capacite:
            raise ConflictError(
                f"Le nombre de personnes doit etre entre {min_capacite} et {max_capacite} pour ce plateau."
            )

        self._ensure_half_hour_slot(slot)
        self._ensure_availability(plateau_id, reservation_date, slot)

        existing = self.reservation_repo.list_by_plateau_and_date(plateau_id, reservation_date)
        has_overlap = any(
            item.statut == ReservationStatus.CONFIRMED and _overlaps(item.creneau, slot) for item in existing
        )

        status = ReservationStatus.WAITLISTED if has_overlap else ReservationStatus.CONFIRMED
        reservation = Reservation(
            id=None,
            plateau_id=plateau_id,
            utilisateur=utilisateur,
            date_reservation=reservation_date,
            creneau=slot,
            statut=status,
            nb_personnes=nb_personnes,
        )
        created = self.reservation_repo.create(reservation)
        if self.notification_service is not None:
            event_type = (
                NotificationEventType.RESERVATION_WAITLISTED
                if created.statut == ReservationStatus.WAITLISTED
                else NotificationEventType.RESERVATION_CONFIRMED
            )
            self.notification_service.notify_reservation_event(event_type, created.id or 0)
        return created

    def list_reservations(
        self,
        plateau_id: int | None = None,
        reservation_date: date | None = None,
    ) -> list[Reservation]:
        items = self.reservation_repo.list_all()
        if plateau_id is not None:
            items = [item for item in items if item.plateau_id == plateau_id]
        if reservation_date is not None:
            items = [item for item in items if item.date_reservation == reservation_date]
        return items

    def update_reservation(
        self,
        reservation_id: int,
        plateau_id: int,
        utilisateur: str,
        reservation_date: date,
        slot: Creneau,
        nb_personnes: int = 1,
    ) -> Reservation:
        current = self.reservation_repo.get_by_id(reservation_id)
        if current is None:
            raise NotFoundError("Reservation introuvable.")
        if current.statut == ReservationStatus.CANCELLED:
            raise ConflictError("Impossible de modifier une reservation annulee.")

        if current.utilisateur.strip().lower() != utilisateur.strip().lower():
            raise ConflictError("Seul l'utilisateur proprietaire peut modifier cette reservation.")

        plateau = self.plateau_repo.get_by_id(plateau_id)
        if plateau is None:
            raise NotFoundError("Le plateau cible n'existe pas.")

        min_capacite = 1
        max_capacite = plateau.capacite
        if nb_personnes < min_capacite or nb_personnes > max_capacite:
            raise ConflictError(
                f"Le nombre de personnes doit etre entre {min_capacite} et {max_capacite} pour ce plateau."
            )

        self._ensure_half_hour_slot(slot)
        self._ensure_availability(plateau_id, reservation_date, slot)

        existing = self.reservation_repo.list_by_plateau_and_date(plateau_id, reservation_date)
        has_overlap = any(
            item.id != reservation_id and item.statut == ReservationStatus.CONFIRMED and _overlaps(item.creneau, slot)
            for item in existing
        )
        new_status = ReservationStatus.WAITLISTED if has_overlap else ReservationStatus.CONFIRMED

        updated = self.reservation_repo.update_reservation(
            reservation_id=reservation_id,
            plateau_id=plateau_id,
            reservation_date=reservation_date,
            creneau_debut=slot.debut.isoformat(timespec="minutes"),
            creneau_fin=slot.fin.isoformat(timespec="minutes"),
            statut=new_status,
            nb_personnes=nb_personnes,
        )
        if updated is None:
            raise NotFoundError("Reservation introuvable.")
        if self.notification_service is not None:
            self.notification_service.notify_reservation_event(
                NotificationEventType.RESERVATION_UPDATED,
                updated.id or 0,
            )
        return updated

    def cancel_reservation(self, reservation_id: int, policy: CancellationPolicy) -> Reservation:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if reservation is None:
            raise NotFoundError("Reservation introuvable.")
        if reservation.statut == ReservationStatus.CANCELLED:
            raise ConflictError("La reservation est deja annulee.")

        requested_at = datetime.utcnow()
        if not policy.can_cancel(reservation, requested_at):
            raise ConflictError("Politique d'annulation non respectee.")

        updated = self.reservation_repo.update_status(reservation_id, ReservationStatus.CANCELLED)
        if updated is None:
            raise NotFoundError("Reservation introuvable.")

        if self.notification_service is not None:
            self.notification_service.notify_reservation_event(
                NotificationEventType.RESERVATION_CANCELLED,
                updated.id or 0,
            )

        if reservation.statut == ReservationStatus.CONFIRMED:
            self._promote_waitlist(
                plateau_id=reservation.plateau_id,
                reservation_date=reservation.date_reservation,
                slot=reservation.creneau,
            )

        return updated

    def _promote_waitlist(self, plateau_id: int, reservation_date: date, slot: Creneau) -> None:
        existing = self.reservation_repo.list_by_plateau_and_date(plateau_id, reservation_date)
        candidates = [
            item
            for item in existing
            if item.statut == ReservationStatus.WAITLISTED and _overlaps(item.creneau, slot)
        ]
        if not candidates:
            return
        next_item = candidates[0]
        promoted = self.reservation_repo.update_status(next_item.id or 0, ReservationStatus.CONFIRMED)
        if promoted is not None and self.notification_service is not None:
            self.notification_service.notify_reservation_event(
                NotificationEventType.WAITLIST_PROMOTED,
                promoted.id or 0,
            )
