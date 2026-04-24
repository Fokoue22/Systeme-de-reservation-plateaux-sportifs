import pytest
from datetime import datetime, time, date
from app.application.m4_services import NotificationService
from app.domain.notifications import NotificationEvent, NotificationType, NotificationPreferences
from app.domain.models import Reservation, Plateau, Creneau, UserAccount
from app.infrastructure.repositories import InMemoryNotificationRepository
from app.infrastructure.notifications import DummyEmailSender, DummySmsSender


class TestNotificationService:
    def setup_method(self):
        self.notification_repo = InMemoryNotificationRepository()
        self.email_sender = DummyEmailSender()
        self.sms_sender = DummySmsSender()
        self.service = NotificationService(
            notification_repo=self.notification_repo,
            email_sender=self.email_sender,
            sms_sender=self.sms_sender
        )

    def test_notify_reservation_event_sends_email(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date.today(),
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=True, sms=False)

        # When
        self.service.notify_reservation_event(
            event=NotificationEvent.RESERVATION_CONFIRMED,
            user=user,
            reservation=reservation,
            preferences=preferences
        )

        # Then
        assert len(self.email_sender.sent_emails) == 1
        email = self.email_sender.sent_emails[0]
        assert email['to'] == "test@example.com"
        assert "confirmed" in email['subject'].lower()
        assert "reservation" in email['body'].lower()

    def test_notify_reservation_event_sends_sms(self):
        # Given
        user = UserAccount(id=1, username="testuser", email=None, phone="1234567890")
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date.today(),
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=False, sms=True)

        # When
        self.service.notify_reservation_event(
            event=NotificationEvent.RESERVATION_CONFIRMED,
            user=user,
            reservation=reservation,
            preferences=preferences
        )

        # Then
        assert len(self.sms_sender.sent_sms) == 1
        sms = self.sms_sender.sent_sms[0]
        assert sms['to'] == "1234567890"
        assert "confirmed" in sms['message'].lower()

    def test_notify_reservation_event_no_preferences(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone="1234567890")
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date.today(),
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=False, sms=False)

        # When
        self.service.notify_reservation_event(
            event=NotificationEvent.RESERVATION_CONFIRMED,
            user=user,
            reservation=reservation,
            preferences=preferences
        )

        # Then
        assert len(self.email_sender.sent_emails) == 0
        assert len(self.sms_sender.sent_sms) == 0

    def test_schedule_24h_reminder_for_future_date(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date(2024, 12, 25),
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=True, sms=False)

        # When
        self.service.schedule_reminder(
            user=user,
            reservation=reservation,
            preferences=preferences,
            hours_before=24
        )

        # Then
        notifications = self.notification_repo.get_pending_notifications()
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.user_id == 1
        assert notification.type == NotificationType.REMINDER
        assert notification.scheduled_for.date() == date(2024, 12, 24)  # 24h before
        assert notification.scheduled_for.time() == time(10, 0)

    def test_schedule_reminder_past_date_raises_error(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date(2020, 1, 1),  # Past date
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=True, sms=False)

        # When/Then
        with pytest.raises(ValueError, match="Cannot schedule reminder for past date"):
            self.service.schedule_reminder(
                user=user,
                reservation=reservation,
                preferences=preferences,
                hours_before=24
            )

    def test_send_daily_summary_no_reservations(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        preferences = NotificationPreferences(email=True, sms=False)

        # When
        self.service.send_daily_summary(user=user, preferences=preferences, reservations=[])

        # Then
        assert len(self.email_sender.sent_emails) == 1
        email = self.email_sender.sent_emails[0]
        assert "daily summary" in email['subject'].lower()
        assert "no reservations" in email['body'].lower()

    def test_send_daily_summary_with_reservations(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservations = [
            Reservation(
                id=1,
                plateau_id=1,
                user_id=1,
                date=date.today(),
                creneau=Creneau(start=time(10, 0), end=time(11, 0)),
                person_count=4,
                status="confirmed"
            ),
            Reservation(
                id=2,
                plateau_id=1,
                user_id=1,
                date=date.today(),
                creneau=Creneau(start=time(14, 0), end=time(15, 0)),
                person_count=2,
                status="confirmed"
            )
        ]
        preferences = NotificationPreferences(email=True, sms=False)

        # When
        self.service.send_daily_summary(
            user=user,
            preferences=preferences,
            reservations=reservations
        )

        # Then
        assert len(self.email_sender.sent_emails) == 1
        email = self.email_sender.sent_emails[0]
        assert "daily summary" in email['subject'].lower()
        assert "2 reservations" in email['body']

    def test_send_weekly_summary_no_reservations(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        preferences = NotificationPreferences(email=True, sms=False)

        # When
        self.service.send_weekly_summary(user=user, preferences=preferences, reservations=[])

        # Then
        assert len(self.email_sender.sent_emails) == 1
        email = self.email_sender.sent_emails[0]
        assert "weekly summary" in email['subject'].lower()
        assert "no reservations" in email['body'].lower()

    def test_send_weekly_summary_with_reservations(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservations = [
            Reservation(
                id=1,
                plateau_id=1,
                user_id=1,
                date=date(2024, 12, 23),
                creneau=Creneau(start=time(10, 0), end=time(11, 0)),
                person_count=4,
                status="confirmed"
            ),
            Reservation(
                id=2,
                plateau_id=1,
                user_id=1,
                date=date(2024, 12, 24),
                creneau=Creneau(start=time(14, 0), end=time(15, 0)),
                person_count=2,
                status="confirmed"
            )
        ]
        preferences = NotificationPreferences(email=True, sms=False)

        # When
        self.service.send_weekly_summary(
            user=user,
            preferences=preferences,
            reservations=reservations
        )

        # Then
        assert len(self.email_sender.sent_emails) == 1
        email = self.email_sender.sent_emails[0]
        assert "weekly summary" in email['subject'].lower()
        assert "2 reservations" in email['body']

    def test_process_pending_notifications_sends_scheduled(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date.today(),
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=True, sms=False)

        # Schedule a reminder
        self.service.schedule_reminder(
            user=user,
            reservation=reservation,
            preferences=preferences,
            hours_before=24
        )

        # When - Process notifications (simulate current time being the scheduled time)
        self.service.process_pending_notifications(current_time=datetime.combine(date.today(), time(10, 0)))

        # Then
        assert len(self.email_sender.sent_emails) == 1
        email = self.email_sender.sent_emails[0]
        assert "reminder" in email['subject'].lower()

        # Notification should be marked as sent
        pending = self.notification_repo.get_pending_notifications()
        assert len(pending) == 0

    def test_process_pending_notifications_ignores_future(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com", phone=None)
        reservation = Reservation(
            id=1,
            plateau_id=1,
            user_id=1,
            date=date.today(),
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4,
            status="confirmed"
        )
        preferences = NotificationPreferences(email=True, sms=False)

        # Schedule a future reminder
        self.service.schedule_reminder(
            user=user,
            reservation=reservation,
            preferences=preferences,
            hours_before=24
        )

        # When - Process notifications before scheduled time
        self.service.process_pending_notifications(current_time=datetime.combine(date.today(), time(9, 0)))

        # Then
        assert len(self.email_sender.sent_emails) == 0

        # Notification should still be pending
        pending = self.notification_repo.get_pending_notifications()
        assert len(pending) == 1