from __future__ import annotations

from app.application import AuthService, DisponibiliteService, NotificationService, PlateauService, ReservationService
from app.application.m4_delivery import build_email_sender_from_env, build_sms_sender_from_env
from app.infrastructure import (
    SQLiteDisponibiliteRepository,
    SQLiteManager,
    SQLiteNotificationPreferenceRepository,
    SQLiteNotificationRepository,
    SQLitePlateauRepository,
    SQLiteReminderTaskRepository,
    SQLiteReservationRepository,
    SQLiteUserAccountRepository,
    SQLiteUserSessionRepository,
)

_db_manager = SQLiteManager()
_plateau_repo = SQLitePlateauRepository(_db_manager)
_disponibilite_repo = SQLiteDisponibiliteRepository(_db_manager)
_reservation_repo = SQLiteReservationRepository(_db_manager)
_notification_preference_repo = SQLiteNotificationPreferenceRepository(_db_manager)
_notification_repo = SQLiteNotificationRepository(_db_manager)
_reminder_task_repo = SQLiteReminderTaskRepository(_db_manager)
_user_account_repo = SQLiteUserAccountRepository(_db_manager)
_user_session_repo = SQLiteUserSessionRepository(_db_manager)
_email_sender = build_email_sender_from_env()
_sms_sender = build_sms_sender_from_env()


def init_schema() -> None:
    """Initialize database schema and seed initial data."""
    _db_manager.initialize_schema()
    _db_manager.seed_initial_data()


def get_plateau_service() -> PlateauService:
    return PlateauService(_plateau_repo)


def get_disponibilite_service() -> DisponibiliteService:
    return DisponibiliteService(
        plateau_repo=_plateau_repo,
        disponibilite_repo=_disponibilite_repo,
    )


def get_reservation_service() -> ReservationService:
    return ReservationService(
        plateau_repo=_plateau_repo,
        disponibilite_repo=_disponibilite_repo,
        reservation_repo=_reservation_repo,
        notification_service=get_notification_service(),
    )


def get_notification_service() -> NotificationService:
    return NotificationService(
        preference_repo=_notification_preference_repo,
        notification_repo=_notification_repo,
        reminder_task_repo=_reminder_task_repo,
        reservation_repo=_reservation_repo,
        plateau_repo=_plateau_repo,
        email_sender=_email_sender,
        sms_sender=_sms_sender,
    )


def get_auth_service() -> AuthService:
    return AuthService(
        account_repo=_user_account_repo,
        session_repo=_user_session_repo,
    )
