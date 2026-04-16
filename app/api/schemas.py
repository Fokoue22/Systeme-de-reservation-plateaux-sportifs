from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.domain.models import ReservationStatus, WeekDay


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
