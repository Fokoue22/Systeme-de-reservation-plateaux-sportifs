from datetime import date, timedelta

from app.application.m4_templates import ReservationNotificationContext, build_message
from app.domain.notifications import NotificationEventType


def test_reminder_message_says_aujourd_hui_for_today():
    ctx = ReservationNotificationContext(
        utilisateur="alice",
        reservation_id=10,
        plateau_label="M1",
        reservation_date=date.today(),
        heure_debut="10:00",
        heure_fin="10:30",
        statut="CONFIRMED",
        nb_personnes=3,
    )

    subject, body = build_message(NotificationEventType.REMINDER_24H, ctx)

    assert "aujourd'hui" in body
    assert "pour 3 personne(s)" in body
    assert "M1" in body
    assert subject == "Rappel J-1"


def test_reminder_message_says_demain_for_tomorrow():
    ctx = ReservationNotificationContext(
        utilisateur="bob",
        reservation_id=11,
        plateau_label="M2",
        reservation_date=date.today() + timedelta(days=1),
        heure_debut="14:00",
        heure_fin="14:30",
        statut="CONFIRMED",
        nb_personnes=1,
    )

    subject, body = build_message(NotificationEventType.REMINDER_24H, ctx)

    assert "demain" in body
    assert "pour 1 personne(s)" in body
    assert "M2" in body
    assert subject == "Rappel J-1"


def test_confirmed_message_includes_plateau_label_and_count():
    ctx = ReservationNotificationContext(
        utilisateur="charlie",
        reservation_id=12,
        plateau_label="M3",
        reservation_date=date.today(),
        heure_debut="09:00",
        heure_fin="09:30",
        statut="CONFIRMED",
        nb_personnes=4,
    )

    subject, body = build_message(NotificationEventType.RESERVATION_CONFIRMED, ctx)

    assert subject == "Reservation confirmee"
    assert "M3" in body
    assert "pour 4 personne(s)" in body
