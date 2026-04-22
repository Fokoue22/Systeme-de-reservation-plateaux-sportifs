from __future__ import annotations

from datetime import datetime, timedelta

from app.domain import PlateauRepository, ReservationRepository
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
)

from .m1_services import NotFoundError
from .m4_delivery import DeliveryPayload, EmailSender, SmsSender
from .m4_templates import ReservationNotificationContext, build_message


class NotificationService:
    def __init__(
        self,
        preference_repo: NotificationPreferenceRepository,
        notification_repo: NotificationRepository,
        reminder_task_repo: ReminderTaskRepository,
        reservation_repo: ReservationRepository,
        plateau_repo: PlateauRepository,
        email_sender: EmailSender,
        sms_sender: SmsSender,
    ):
        self.preference_repo = preference_repo
        self.notification_repo = notification_repo
        self.reminder_task_repo = reminder_task_repo
        self.reservation_repo = reservation_repo
        self.plateau_repo = plateau_repo
        self.email_sender = email_sender
        self.sms_sender = sms_sender

    def get_or_create_preferences(self, utilisateur: str) -> NotificationPreference:
        existing = self.preference_repo.get_by_user(utilisateur)
        if existing is not None:
            return existing

        now = datetime.utcnow()
        default_pref = NotificationPreference(
            utilisateur=utilisateur,
            email=f"{utilisateur}@local.invalid",
            telephone=None,
            email_enabled=True,
            sms_enabled=False,
            weekly_summary_enabled=False,
            is_admin=False,
            created_at=now,
            updated_at=now,
        )
        return self.preference_repo.upsert(default_pref)

    def update_preferences(
        self,
        utilisateur: str,
        email: str | None,
        telephone: str | None,
        email_enabled: bool,
        sms_enabled: bool,
        weekly_summary_enabled: bool,
        is_admin: bool,
    ) -> NotificationPreference:
        current = self.get_or_create_preferences(utilisateur)
        updated = NotificationPreference(
            utilisateur=utilisateur,
            email=email,
            telephone=telephone,
            email_enabled=email_enabled,
            sms_enabled=sms_enabled,
            weekly_summary_enabled=weekly_summary_enabled,
            is_admin=is_admin,
            created_at=current.created_at,
            updated_at=datetime.utcnow(),
        )
        return self.preference_repo.upsert(updated)

    def list_notifications_for_user(self, utilisateur: str, limit: int = 100) -> list[NotificationMessage]:
        return self.notification_repo.list_by_user(utilisateur, limit=limit)

    def notify_reservation_event(self, event_type: NotificationEventType, reservation_id: int) -> list[NotificationMessage]:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if reservation is None:
            raise NotFoundError("Reservation introuvable pour notification.")

        plateau = self.plateau_repo.get_by_id(reservation.plateau_id)
        plateau_label = (
            f"{plateau.type_sport} - {plateau.emplacement}"
            if plateau is not None
            else f"Plateau #{reservation.plateau_id}"
        )

        context = ReservationNotificationContext(
            utilisateur=reservation.utilisateur,
            reservation_id=reservation.id or 0,
            plateau_label=plateau_label,
            reservation_date=reservation.date_reservation,
            heure_debut=reservation.creneau.debut.isoformat(timespec="minutes"),
            heure_fin=reservation.creneau.fin.isoformat(timespec="minutes"),
            statut=reservation.statut.value,
            nb_personnes=reservation.nb_personnes,
        )
        subject, body = build_message(event_type, context)

        preference = self.get_or_create_preferences(reservation.utilisateur)
        created_messages: list[NotificationMessage] = []

        if preference.email_enabled:
            email_destination = preference.email or f"{reservation.utilisateur}@local.invalid"
            created_messages.append(
                self._create_and_send(
                    utilisateur=reservation.utilisateur,
                    channel=NotificationChannel.EMAIL,
                    destination=email_destination,
                    event_type=event_type,
                    subject=subject,
                    body=body,
                )
            )

        if preference.sms_enabled and preference.telephone:
            created_messages.append(
                self._create_and_send(
                    utilisateur=reservation.utilisateur,
                    channel=NotificationChannel.SMS,
                    destination=preference.telephone,
                    event_type=event_type,
                    subject=subject,
                    body=body,
                )
            )

        if not created_messages:
            created_messages.append(
                self._persist_only(
                    utilisateur=reservation.utilisateur,
                    channel=NotificationChannel.EMAIL,
                    event_type=event_type,
                    subject=subject,
                    body=body,
                    status=NotificationStatus.FAILED,
                    error="Aucun canal actif pour cet utilisateur.",
                )
            )

        if event_type in {
            NotificationEventType.RESERVATION_CONFIRMED,
            NotificationEventType.RESERVATION_UPDATED,
            NotificationEventType.WAITLIST_PROMOTED,
        }:
            self.schedule_24h_reminder(reservation_id)

        return created_messages

    def schedule_24h_reminder(self, reservation_id: int) -> ReminderTask:
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if reservation is None:
            raise NotFoundError("Reservation introuvable pour planifier un rappel.")

        scheduled_for = datetime.combine(reservation.date_reservation, reservation.creneau.debut) - timedelta(hours=24)
        task = ReminderTask(
            id=None,
            reservation_id=reservation_id,
            utilisateur=reservation.utilisateur,
            reminder_type="REMINDER_24H",
            scheduled_for=scheduled_for,
            sent_at=None,
        )
        return self.reminder_task_repo.upsert_task(task)

    def process_due_reminders(self, now_utc: datetime | None = None) -> list[NotificationMessage]:
        now = now_utc or datetime.utcnow()
        due_tasks = self.reminder_task_repo.list_due_tasks(now.isoformat())
        sent_messages: list[NotificationMessage] = []

        for task in due_tasks:
            try:
                sent_messages.extend(
                    self.notify_reservation_event(
                        event_type=NotificationEventType.REMINDER_24H,
                        reservation_id=task.reservation_id,
                    )
                )
                self.reminder_task_repo.mark_sent(task.id or 0, now.isoformat())
            except Exception:
                # Keep task pending if notification fails; retry in next scheduler pass.
                continue

        return sent_messages

    def send_weekly_summary_for_admins(self) -> list[NotificationMessage]:
        admins = self.preference_repo.list_admins_with_weekly_summary_enabled()
        if not admins:
            return []

        now = datetime.utcnow()
        week_end = now.date() + timedelta(days=7)
        reservations = self.reservation_repo.list_all()
        upcoming = [
            item
            for item in reservations
            if now.date() <= item.date_reservation <= week_end
        ]
        confirmed = [item for item in upcoming if item.statut.value == "CONFIRMED"]
        waitlisted = [item for item in upcoming if item.statut.value == "WAITLISTED"]
        cancelled = [item for item in upcoming if item.statut.value == "CANCELLED"]

        subject = "Recapitulatif hebdomadaire des reservations"
        body = (
            f"Periode: {now.date().isoformat()} -> {week_end.isoformat()}\n"
            f"Total reservations: {len(upcoming)}\n"
            f"Confirmees: {len(confirmed)}\n"
            f"En attente: {len(waitlisted)}\n"
            f"Annulees: {len(cancelled)}"
        )

        messages: list[NotificationMessage] = []
        for admin in admins:
            if admin.email_enabled:
                destination = admin.email or f"{admin.utilisateur}@local.invalid"
                messages.append(
                    self._create_and_send(
                        utilisateur=admin.utilisateur,
                        channel=NotificationChannel.EMAIL,
                        destination=destination,
                        event_type=NotificationEventType.WEEKLY_SUMMARY,
                        subject=subject,
                        body=body,
                    )
                )

        return messages

    def _create_and_send(
        self,
        utilisateur: str,
        channel: NotificationChannel,
        destination: str,
        event_type: NotificationEventType,
        subject: str,
        body: str,
    ) -> NotificationMessage:
        message = NotificationMessage(
            id=None,
            utilisateur=utilisateur,
            channel=channel,
            event_type=event_type,
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        try:
            payload = DeliveryPayload(
                utilisateur=utilisateur,
                destination=destination,
                subject=subject,
                body=body,
            )
            if channel == NotificationChannel.EMAIL:
                self.email_sender.send(payload)
            else:
                self.sms_sender.send(payload)

            message = NotificationMessage(
                id=None,
                utilisateur=utilisateur,
                channel=channel,
                event_type=event_type,
                subject=subject,
                body=body,
                status=NotificationStatus.SENT,
                created_at=message.created_at,
                sent_at=datetime.utcnow(),
            )
        except Exception as exc:
            message = NotificationMessage(
                id=None,
                utilisateur=utilisateur,
                channel=channel,
                event_type=event_type,
                subject=subject,
                body=body,
                status=NotificationStatus.FAILED,
                error=str(exc),
                created_at=message.created_at,
                sent_at=None,
            )

        return self.notification_repo.create(message)

    def _persist_only(
        self,
        utilisateur: str,
        channel: NotificationChannel,
        event_type: NotificationEventType,
        subject: str,
        body: str,
        status: NotificationStatus,
        error: str,
    ) -> NotificationMessage:
        message = NotificationMessage(
            id=None,
            utilisateur=utilisateur,
            channel=channel,
            event_type=event_type,
            subject=subject,
            body=body,
            status=status,
            error=error,
            created_at=datetime.utcnow(),
            sent_at=None,
        )
        return self.notification_repo.create(message)
