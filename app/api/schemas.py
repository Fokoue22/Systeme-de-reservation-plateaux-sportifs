from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.domain.models import ReservationStatus, WeekDay
from app.domain.notifications import NotificationChannel, NotificationEventType, NotificationStatus


class PlateauCreate(BaseModel):
    nom: str = Field(min_length=1)
    type_sport: str = Field(min_length=1)
    capacite: int = Field(gt=0)
    emplacement: str = Field(min_length=1)


class PlateauUpdate(PlateauCreate):
    pass


class PlateauRead(BaseModel):
    id: int
    nom: str
    type_sport: str
    capacite: int
    emplacement: str


class CreneauInput(BaseModel):
    debut: time
    fin: time


class DisponibiliteCreate(BaseModel):
    jour: WeekDay
    creneau: CreneauInput


class DisponibiliteRead(BaseModel):
    id: int
    plateau_id: int
    jour: WeekDay
    creneau: CreneauInput


class ReservationCreate(BaseModel):
    plateau_id: int = Field(gt=0)
    utilisateur: str = Field(min_length=1)
    date_reservation: date
    creneau: CreneauInput
    nb_personnes: int = Field(default=1, gt=0)


class ReservationUpdate(ReservationCreate):
    pass


class ReservationRead(BaseModel):
    id: int
    plateau_id: int
    utilisateur: str
    date_reservation: date
    creneau: CreneauInput
    statut: ReservationStatus
    nb_personnes: int
    created_at: datetime


class NotificationPreferenceUpsert(BaseModel):
    email: str | None = None
    telephone: str | None = None
    email_enabled: bool = True
    sms_enabled: bool = False
    weekly_summary_enabled: bool = False
    is_admin: bool = False


class NotificationPreferenceRead(BaseModel):
    utilisateur: str
    email: str | None
    telephone: str | None
    email_enabled: bool
    sms_enabled: bool
    weekly_summary_enabled: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class NotificationRead(BaseModel):
    id: int
    utilisateur: str
    channel: NotificationChannel
    event_type: NotificationEventType
    subject: str
    body: str
    status: NotificationStatus
    error: str | None
    created_at: datetime
    sent_at: datetime | None


class ReminderRunResult(BaseModel):
    processed: int


class WeeklySummaryRunResult(BaseModel):
    sent: int


class AuthRegisterRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)
    email: str | None = None
    telephone: str | None = None
    is_admin: bool = False


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserAccountRead(BaseModel):
    id: int
    username: str
    email: str | None
    telephone: str | None
    is_admin: bool
    created_at: datetime
