from __future__ import annotations

import pytest
from datetime import datetime, date, time, timedelta

from app.application.m4_services import NotificationService
from app.application.m4_delivery import DeliveryPayload
from app.application.m4_delivery import EmailSender, SmsSender
from app.application.m1_services import NotFoundError
from app.domain.models import Plateau, Reservation, Creneau, ReservationStatus
from app.domain.notifications import (
    NotificationChannel,
    NotificationEventType,
    NotificationMessage,
    NotificationPreference,
    NotificationStatus,
    ReminderTask,
)
from app.domain.repositories import (
    NotificationPreferenceRepository,
    NotificationRepository,
    ReminderTaskRepository,
    ReservationRepository,
    PlateauRepository,
)


class DummyEmailSender(EmailSender):
    def __init__(self):
        self.sent = []

    def send(self, payload: DeliveryPayload) -> None:
        self.sent.append(payload)


class DummySmsSender(SmsSender):
    def __init__(self):
        self.sent = []

    def send(self, payload: DeliveryPayload) -> None:
        self.sent.append(payload)


class InMemoryNotificationPreferenceRepository(NotificationPreferenceRepository):
    def __init__(self):
        self.preferences: dict[str, NotificationPreference] = {}

    def get_by_user(self, utilisateur: str) -> NotificationPreference | None:
        return self.preferences.get(utilisateur)

    def upsert(self, preference: NotificationPreference) -> NotificationPreference:
        self.preferences[preference.utilisateur] = preference
        return preference

    def list_admins_with_weekly_summary_enabled(self) -> list[NotificationPreference]:
        return [pref for pref in self.preferences.values() if pref.is_admin and pref.weekly_summary_enabled]


class InMemoryNotificationRepository(NotificationRepository):
    def __init__(self):
        self.notifications: list[NotificationMessage] = []
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
        self.notifications.append(created)
        self._next_id += 1
        return created

    def list_by_user(self, utilisateur: str, limit: int = 100) -> list[NotificationMessage]:
        return [n for n in self.notifications if n.utilisateur == utilisateur][:limit]


class InMemoryReminderTaskRepository(ReminderTaskRepository):
    def __init__(self):
        self.tasks: dict[int, ReminderTask] = {}
        self._next_id = 1

    def upsert_task(self, task: ReminderTask) -> ReminderTask:
        if task.id is None:
            task_id = self._next_id
            self._next_id += 1
        else:
            task_id = task.id
        created = ReminderTask(
            id=task_id,
            reservation_id=task.reservation_id,
            utilisateur=task.utilisateur,
            reminder_type=task.reminder_type,
            scheduled_for=task.scheduled_for,
            sent_at=task.sent_at,
        )
        self.tasks[task_id] = created
        return created

    def list_due_tasks(self, now_utc: str) -> list[ReminderTask]:
        now = datetime.fromisoformat(now_utc)
        return [task for task in self.tasks.values() if task.sent_at is None and task.scheduled_for <= now]

    def mark_sent(self, task_id: int, sent_at_utc: str) -> ReminderTask | None:
        task = self.tasks.get(task_id)
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
        self.tasks[task_id] = updated
        return updated


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
        return [res for res in self.reservations.values() if res.plateau_id == plateau_id and res.date_reservation == reservation_date]

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


class TestNotificationService:
    def setup_method(self):
        self.preference_repo = InMemoryNotificationPreferenceRepository()
        self.notification_repo = InMemoryNotificationRepository()
        self.reminder_repo = InMemoryReminderTaskRepository()
        self.reservation_repo = InMemoryReservationRepository()
        self.plateau_repo = InMemoryPlateauRepository()
        self.email_sender = DummyEmailSender()
        self.sms_sender = DummySmsSender()
        self.service = NotificationService(
            preference_repo=self.preference_repo,
            notification_repo=self.notification_repo,
            reminder_task_repo=self.reminder_repo,
            reservation_repo=self.reservation_repo,
            plateau_repo=self.plateau_repo,
            email_sender=self.email_sender,
            sms_sender=self.sms_sender,
        )

        self.plateau = self.plateau_repo.create(Plateau(id=1, nom="Gymnase A", type_sport="Basketball", capacite=10, emplacement="Centre-ville"))
        self.reservation = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=2),
                creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=2,
            )
        )

    def test_get_or_create_preferences_creates_default(self):
        preference = self.service.get_or_create_preferences("bob")

        assert preference.utilisateur == "bob"
        assert preference.email == "bob@local.invalid"
        assert preference.email_enabled is True
        assert preference.sms_enabled is False

    def test_update_preferences_persists_changes(self):
        self.service.get_or_create_preferences("bob")

        updated = self.service.update_preferences(
            utilisateur="bob",
            email="bob@example.com",
            telephone="1234567890",
            email_enabled=False,
            sms_enabled=True,
            weekly_summary_enabled=True,
            is_admin=True,
        )

        assert updated.utilisateur == "bob"
        assert updated.email == "bob@example.com"
        assert updated.telephone == "1234567890"
        assert updated.email_enabled is False
        assert updated.sms_enabled is True
        assert updated.weekly_summary_enabled is True
        assert updated.is_admin is True

    def test_notify_reservation_event_sends_email_and_schedules_reminder(self):
        result = self.service.notify_reservation_event(NotificationEventType.RESERVATION_CONFIRMED, self.reservation.id or 0)

        assert len(self.email_sender.sent) == 1
        assert len(result) == 1
        assert result[0].status == NotificationStatus.SENT
        assert self.reservation.id in {task.reservation_id for task in self.reminder_repo.tasks.values()}

    def test_notify_reservation_event_sends_sms_when_enabled(self):
        self.preference_repo.upsert(
            NotificationPreference(
                utilisateur="alice",
                email=None,
                telephone="0678901234",
                email_enabled=False,
                sms_enabled=True,
            )
        )

        result = self.service.notify_reservation_event(NotificationEventType.RESERVATION_CONFIRMED, self.reservation.id or 0)

        assert len(self.sms_sender.sent) == 1
        assert result[0].status == NotificationStatus.SENT

    def test_notify_reservation_event_creates_failed_notification_without_channels(self):
        self.preference_repo.upsert(
            NotificationPreference(
                utilisateur="alice",
                email=None,
                telephone=None,
                email_enabled=False,
                sms_enabled=False,
            )
        )

        result = self.service.notify_reservation_event(NotificationEventType.RESERVATION_CONFIRMED, self.reservation.id or 0)

        assert len(result) == 1
        assert result[0].status == NotificationStatus.FAILED
        assert result[0].error is not None

    def test_notify_reservation_event_raises_when_reservation_not_found(self):
        with pytest.raises(NotFoundError):
            self.service.notify_reservation_event(NotificationEventType.RESERVATION_CONFIRMED, 999)

    def test_schedule_24h_reminder_for_today_uses_now(self):
        today_reservation = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today(),
                creneau=Creneau(debut=time(23, 0), fin=time(23, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=1,
            )
        )

        task = self.service.schedule_24h_reminder(today_reservation.id or 0)

        assert task.sent_at is None
        assert abs((task.scheduled_for - datetime.now()).total_seconds()) < 5

    def test_process_due_reminders_sends_reminder_and_marks_sent(self):
        due_reservation = self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today(),
                creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=1,
            )
        )
        task = self.reminder_repo.upsert_task(
            ReminderTask(
                id=None,
                reservation_id=due_reservation.id or 0,
                utilisateur="alice",
                reminder_type="REMINDER_24H",
                scheduled_for=datetime.utcnow() - timedelta(minutes=1),
                sent_at=None,
            )
        )

        self.service.notify_reservation_event(NotificationEventType.RESERVATION_CONFIRMED, due_reservation.id or 0)
        notifications_before = len(self.notification_repo.notifications)

        result = self.service.process_due_reminders(datetime.utcnow())

        assert len(result) >= 1
        assert self.reminder_repo.tasks[task.id].sent_at is not None
        assert len(self.notification_repo.notifications) > notifications_before

    def test_send_weekly_summary_for_admins_sends_email(self):
        self.preference_repo.upsert(
            NotificationPreference(
                utilisateur="bob",
                email="bob@example.com",
                telephone=None,
                email_enabled=True,
                sms_enabled=False,
                weekly_summary_enabled=True,
                is_admin=True,
            )
        )
        self.reservation_repo.create(
            Reservation(
                id=None,
                plateau_id=1,
                utilisateur="alice",
                date_reservation=date.today() + timedelta(days=3),
                creneau=Creneau(debut=time(10, 0), fin=time(10, 30)),
                statut=ReservationStatus.CONFIRMED,
                nb_personnes=1,
            )
        )

        result = self.service.send_weekly_summary_for_admins()

        assert len(result) == 1
        assert self.email_sender.sent[0].destination == "bob@example.com"
        assert result[0].event_type == NotificationEventType.WEEKLY_SUMMARY
