from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .models import DomainValidationError


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"


class NotificationEventType(str, Enum):
    RESERVATION_CONFIRMED = "RESERVATION_CONFIRMED"
    RESERVATION_WAITLISTED = "RESERVATION_WAITLISTED"
    RESERVATION_CANCELLED = "RESERVATION_CANCELLED"
    RESERVATION_UPDATED = "RESERVATION_UPDATED"
    WAITLIST_PROMOTED = "WAITLIST_PROMOTED"
    REMINDER_24H = "REMINDER_24H"
    WEEKLY_SUMMARY = "WEEKLY_SUMMARY"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass(frozen=True)
class NotificationPreference:
    utilisateur: str
    email: str | None = None
    telephone: str | None = None
    email_enabled: bool = True
    sms_enabled: bool = False
    weekly_summary_enabled: bool = False
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.utilisateur.strip():
            raise DomainValidationError("L'utilisateur est obligatoire pour les preferences de notification.")


@dataclass(frozen=True)
class NotificationMessage:
    id: int | None
    utilisateur: str
    channel: NotificationChannel
    event_type: NotificationEventType
    subject: str
    body: str
    status: NotificationStatus = NotificationStatus.PENDING
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.utilisateur.strip():
            raise DomainValidationError("L'utilisateur est obligatoire.")
        if not self.subject.strip():
            raise DomainValidationError("Le sujet de notification est obligatoire.")
        if not self.body.strip():
            raise DomainValidationError("Le contenu de notification est obligatoire.")


@dataclass(frozen=True)
class ReminderTask:
    id: int | None
    reservation_id: int
    utilisateur: str
    reminder_type: str
    scheduled_for: datetime
    sent_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.reservation_id <= 0:
            raise DomainValidationError("L'identifiant de reservation est invalide.")
        if not self.utilisateur.strip():
            raise DomainValidationError("L'utilisateur est obligatoire pour un rappel.")
