from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.notifications import NotificationEventType


@dataclass(frozen=True)
class ReservationNotificationContext:
    utilisateur: str
    reservation_id: int
    plateau_label: str
    reservation_date: date
    heure_debut: str
    heure_fin: str
    statut: str


def _human_slot(ctx: ReservationNotificationContext) -> str:
    return (
        f"{ctx.reservation_date.isoformat()} de {ctx.heure_debut} a {ctx.heure_fin} "
        f"sur {ctx.plateau_label}"
    )


def build_message(event_type: NotificationEventType, ctx: ReservationNotificationContext) -> tuple[str, str]:
    slot = _human_slot(ctx)

    if event_type == NotificationEventType.RESERVATION_CONFIRMED:
        return (
            "Reservation confirmee",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} est confirmee ({slot}).",
        )
    if event_type == NotificationEventType.RESERVATION_WAITLISTED:
        return (
            "Reservation en attente",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} est en liste d'attente ({slot}).",
        )
    if event_type == NotificationEventType.RESERVATION_CANCELLED:
        return (
            "Reservation annulee",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} a ete annulee ({slot}).",
        )
    if event_type == NotificationEventType.RESERVATION_UPDATED:
        return (
            "Reservation modifiee",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} a ete mise a jour ({slot}).",
        )
    if event_type == NotificationEventType.WAITLIST_PROMOTED:
        return (
            "Promotion depuis la liste d'attente",
            f"Bonne nouvelle {ctx.utilisateur}, votre reservation #{ctx.reservation_id} a ete promue en confirmee ({slot}).",
        )
    if event_type == NotificationEventType.REMINDER_24H:
        return (
            "Rappel J-1",
            f"Rappel: votre reservation #{ctx.reservation_id} aura lieu demain ({slot}).",
        )

    return (
        "Notification",
        f"Mise a jour sur votre reservation #{ctx.reservation_id} ({slot}).",
    )
