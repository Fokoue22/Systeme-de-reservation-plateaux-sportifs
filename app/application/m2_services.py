from __future__ import annotations

from datetime import date, datetime

from app.domain import CancellationPolicy, Creneau, Reservation, ReservationStatus, WeekDay
from app.domain.repositories import DisponibiliteRepository, PlateauRepository, ReservationRepository

from .m1_services import ConflictError, NotFoundError, _overlaps


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
    ):
        self.plateau_repo = plateau_repo
        self.disponibilite_repo = disponibilite_repo
        self.reservation_repo = reservation_repo

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
    ) -> Reservation:
        if self.plateau_repo.get_by_id(plateau_id) is None:
            raise NotFoundError("Le plateau cible n'existe pas.")

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
        )
        return self.reservation_repo.create(reservation)

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
        self.reservation_repo.update_status(next_item.id or 0, ReservationStatus.CONFIRMED)
