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
    nb_personnes: int = 1


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
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} est confirmee ({slot}, pour {ctx.nb_personnes} personne(s)).",
        )
    if event_type == NotificationEventType.RESERVATION_WAITLISTED:
        return (
            "Reservation en attente",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} est en liste d'attente ({slot}, pour {ctx.nb_personnes} personne(s)).",
        )
    if event_type == NotificationEventType.RESERVATION_CANCELLED:
        return (
            "Reservation annulee",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} a ete annulee ({slot}, pour {ctx.nb_personnes} personne(s)).",
        )
    if event_type == NotificationEventType.RESERVATION_UPDATED:
        return (
            "Reservation modifiee",
            f"Bonjour {ctx.utilisateur}, votre reservation #{ctx.reservation_id} a ete mise a jour ({slot}, pour {ctx.nb_personnes} personne(s)).",
        )
    if event_type == NotificationEventType.WAITLIST_PROMOTED:
        return (
            "Promotion depuis la liste d'attente",
            f"Bonne nouvelle {ctx.utilisateur}, votre reservation #{ctx.reservation_id} a ete promue en confirmee ({slot}, pour {ctx.nb_personnes} personne(s)).",
        )
    if event_type == NotificationEventType.REMINDER_24H:
        from datetime import date
        when = "aujourd'hui" if ctx.reservation_date == date.today() else "demain"
        return (
            "Rappel J-1",
            f"Rappel: votre reservation #{ctx.reservation_id} aura lieu {when} ({slot}, pour {ctx.nb_personnes} personne(s)).",
        )

    return (
        "Notification",
        f"Mise a jour sur votre reservation #{ctx.reservation_id} ({slot}).",
    )
