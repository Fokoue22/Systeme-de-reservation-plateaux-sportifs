from __future__ import annotations

from datetime import date, datetime, timedelta, time

from app.application.m4_delivery import DeliveryPayload, EmailSender, SmsSender
from app.application.m4_services import NotificationService
from app.domain.models import Creneau, Plateau, Reservation, ReservationStatus
from app.domain.notifications import (
    NotificationChannel,
    NotificationEventType,
    NotificationMessage,
    NotificationPreference,
    NotificationStatus,
    ReminderTask,
)


class FakeEmailSender(EmailSender):
    def __init__(self) -> None:
        self.sent: list[DeliveryPayload] = []

    def send(self, payload: DeliveryPayload) -> None:
        self.sent.append(payload)


class FakeSmsSender(SmsSender):
    def __init__(self) -> None:
        self.sent: list[DeliveryPayload] = []

    def send(self, payload: DeliveryPayload) -> None:
        self.sent.append(payload)


class InMemoryNotificationPreferenceRepository:
    def __init__(self) -> None:
        self._preferences: dict[str, NotificationPreference] = {}

    def get_by_user(self, utilisateur: str) -> NotificationPreference | None:
        return self._preferences.get(utilisateur)

    def upsert(self, preference: NotificationPreference) -> NotificationPreference:
        self._preferences[preference.utilisateur] = preference
        return preference

    def list_admins_with_weekly_summary_enabled(self) -> list[NotificationPreference]:
        return [
            pref
            for pref in self._preferences.values()
            if pref.is_admin and pref.weekly_summary_enabled
        ]


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._items: list[NotificationMessage] = []
        self._next_id = 1

    def create(self, message: NotificationMessage) -> NotificationMessage:
        created = NotificationMessage(
            id=self._next_id,
            utilisateur=message.utilisateur,
            channel=message.channel,
            event_type=message.event_type,
            subject=message.subject,
            body=message.body,
            status=message.status,
            error=message.error,
            created_at=message.created_at,
            sent_at=message.sent_at,
        )
        self._items.append(created)
        self._next_id += 1
        return created

    def list_by_user(self, utilisateur: str, limit: int = 100) -> list[NotificationMessage]:
        return [item for item in self._items if item.utilisateur == utilisateur][:limit]


class InMemoryReminderTaskRepository:
    def __init__(self) -> None:
        self._items: dict[int, ReminderTask] = {}
        self._next_id = 1

    def upsert_task(self, task: ReminderTask) -> ReminderTask:
        created = ReminderTask(
            id=self._next_id,
            reservation_id=task.reservation_id,
            utilisateur=task.utilisateur,
            reminder_type=task.reminder_type,
            scheduled_for=task.scheduled_for,
            sent_at=task.sent_at,
        )
        self._items[self._next_id] = created
        self._next_id += 1
        return created

    def list_due_tasks(self, now_utc: str) -> list[ReminderTask]:
        now = datetime.fromisoformat(now_utc)
        return [task for task in self._items.values() if task.sent_at is None and task.scheduled_for <= now]

    def mark_sent(self, task_id: int, sent_at_utc: str) -> ReminderTask | None:
        task = self._items.get(task_id)
        if task is None:
            return None
        updated = ReminderTask(
            id=task.id,
            reservation_id=task.reservation_id,
            utilisateur=task.utilisateur,
            reminder_type=task.reminder_type,
            scheduled_for=task.scheduled_for,
            sent_at=datetime.fromisoformat(sent_at_utc),
        )
        self._items[task_id] = updated
        return updated


class InMemoryReservationRepository:
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
            reservation
            for reservation in self._items.values()
            if reservation.plateau_id == plateau_id and reservation.date_reservation == reservation_date
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
        reservation = self._items.get(reservation_id)
        if reservation is None:
            return None
        updated = Reservation(
            id=reservation.id,
            plateau_id=plateau_id,
            utilisateur=reservation.utilisateur,
            date_reservation=reservation_date,
            creneau=Creneau(debut=time.fromisoformat(creneau_debut), fin=time.fromisoformat(creneau_fin)),
            statut=statut,
            nb_personnes=nb_personnes,
        )
        self._items[reservation_id] = updated
        return updated

    def update_status(self, reservation_id: int, status: ReservationStatus) -> Reservation | None:
        reservation = self._items.get(reservation_id)
        if reservation is None:
            return None
        updated = Reservation(
            id=reservation.id,
            plateau_id=reservation.plateau_id,
            utilisateur=reservation.utilisateur,
            date_reservation=reservation.date_reservation,
            creneau=reservation.creneau,
            statut=status,
            nb_personnes=reservation.nb_personnes,
        )
        self._items[reservation_id] = updated
        return updated


class InMemoryPlateauRepository:
    def __init__(self) -> None:
        self._items: dict[int, Plateau] = {}

    def create(self, plateau: Plateau) -> Plateau:
        created = Plateau(
            id=plateau.id,
            nom=plateau.nom,
            type_sport=plateau.type_sport,
            capacite=plateau.capacite,
            emplacement=plateau.emplacement,
        )
        self._items[plateau.id or 0] = created
        return created

    def get_by_id(self, plateau_id: int) -> Plateau | None:
        return self._items.get(plateau_id)

    def list_all(self) -> list[Plateau]:
        return list(self._items.values())

    def update(self, plateau: Plateau) -> Plateau:
        self._items[plateau.id or 0] = plateau
        return plateau

    def delete(self, plateau_id: int) -> bool:
        return self._items.pop(plateau_id, None) is not None


def build_notification_service() -> NotificationService:
    preference_repo = InMemoryNotificationPreferenceRepository()
    notification_repo = InMemoryNotificationRepository()
    reminder_task_repo = InMemoryReminderTaskRepository()
    reservation_repo = InMemoryReservationRepository()
    plateau_repo = InMemoryPlateauRepository()
    email_sender = FakeEmailSender()
    sms_sender = FakeSmsSender()

    return NotificationService(
        preference_repo=preference_repo,
        notification_repo=notification_repo,
        reminder_task_repo=reminder_task_repo,
        reservation_repo=reservation_repo,
        plateau_repo=plateau_repo,
        email_sender=email_sender,
        sms_sender=sms_sender,
    )


def test_get_or_create_preferences_creates_default() -> None:
    service = build_notification_service()

    preference = service.get_or_create_preferences("alice")

    assert preference.utilisateur == "alice"
    assert preference.email == "alice@local.invalid"
    assert preference.email_enabled is True
    assert preference.sms_enabled is False


def test_update_preferences_updates_existing() -> None:
    service = build_notification_service()

    service.get_or_create_preferences("bob")
    updated = service.update_preferences(
        utilisateur="bob",
        email="bob@example.com",
        telephone="+15551234567",
        email_enabled=True,
        sms_enabled=True,
        weekly_summary_enabled=True,
        is_admin=False,
    )

    assert updated.email == "bob@example.com"
    assert updated.sms_enabled is True
    assert updated.weekly_summary_enabled is True


def test_notify_reservation_event_sends_email_and_schedules_reminder() -> None:
    service = build_notification_service()
    service.plateau_repo.create(Plateau(id=1, nom="Gymnase A", type_sport="Basket", capacite=10, emplacement="Nord"))
    reservation = service.reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=1,
            utilisateur="carol",
            date_reservation=date.today() + timedelta(days=2),
            creneau=Creneau(debut=time(9, 0), fin=time(10, 0)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )

    messages = service.notify_reservation_event(NotificationEventType.RESERVATION_CONFIRMED, reservation.id or 0)

    assert len(messages) == 1
    assert messages[0].status == NotificationStatus.SENT
    assert messages[0].channel == NotificationChannel.EMAIL
    assert any(task for task in service.reminder_task_repo._items.values())


def test_notify_reservation_event_falls_back_when_no_channel_available() -> None:
    service = build_notification_service()
    service.plateau_repo.create(Plateau(id=1, nom="Gymnase B", type_sport="Tennis", capacite=6, emplacement="Ouest"))
    reservation = service.reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=1,
            utilisateur="dave",
            date_reservation=date.today() + timedelta(days=3),
            creneau=Creneau(debut=time(11, 0), fin=time(12, 0)),
            statut=ReservationStatus.WAITLISTED,
            nb_personnes=2,
        )
    )
    service.preference_repo.upsert(
        NotificationPreference(
            utilisateur="dave",
            email=None,
            telephone=None,
            email_enabled=False,
            sms_enabled=False,
            weekly_summary_enabled=False,
            is_admin=False,
        )
    )

    messages = service.notify_reservation_event(NotificationEventType.RESERVATION_WAITLISTED, reservation.id or 0)

    assert len(messages) == 1
    assert messages[0].status == NotificationStatus.FAILED
    assert "Aucun canal actif" in messages[0].error


def test_process_due_reminders_marks_task_sent() -> None:
    service = build_notification_service()
    service.plateau_repo.create(Plateau(id=1, nom="Piscine", type_sport="Natation", capacite=12, emplacement="Centre"))
    reservation = service.reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=1,
            utilisateur="emma",
            date_reservation=date.today(),
            creneau=Creneau(debut=time(8, 0), fin=time(9, 0)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=1,
        )
    )
    task = service.reminder_task_repo.upsert_task(
        ReminderTask(
            id=None,
            reservation_id=reservation.id or 0,
            utilisateur="emma",
            reminder_type="REMINDER_24H",
            scheduled_for=datetime.utcnow() - timedelta(minutes=1),
            sent_at=None,
        )
    )

    sent_messages = service.process_due_reminders(datetime.utcnow())

    assert any(msg.event_type == NotificationEventType.REMINDER_24H for msg in sent_messages)
    assert service.reminder_task_repo._items[task.id or 0].sent_at is not None


def test_send_weekly_summary_for_admins_sends_email() -> None:
    service = build_notification_service()
    service.preference_repo.upsert(
        NotificationPreference(
            utilisateur="admin",
            email="admin@example.com",
            telephone=None,
            email_enabled=True,
            sms_enabled=False,
            weekly_summary_enabled=True,
            is_admin=True,
        )
    )
    service.plateau_repo.create(Plateau(id=1, nom="Gymnase C", type_sport="Volley", capacite=8, emplacement="Est"))
    service.reservation_repo.create(
        Reservation(
            id=None,
            plateau_id=1,
            utilisateur="frank",
            date_reservation=date.today() + timedelta(days=4),
            creneau=Creneau(debut=time(15, 0), fin=time(16, 0)),
            statut=ReservationStatus.CONFIRMED,
            nb_personnes=3,
        )
    )

    messages = service.send_weekly_summary_for_admins()

    assert len(messages) == 1
    assert messages[0].event_type == NotificationEventType.WEEKLY_SUMMARY
    assert messages[0].channel == NotificationChannel.EMAIL
