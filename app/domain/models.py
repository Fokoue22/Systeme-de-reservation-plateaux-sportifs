from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum


class DomainValidationError(ValueError):
    """Raised when domain invariants are violated."""


class WeekDay(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


@dataclass(frozen=True)
class Plateau:
    id: int | None
    nom: str
    type_sport: str
    capacite: int
    emplacement: str

    def __post_init__(self) -> None:
        if not self.nom.strip():
            raise DomainValidationError("Le nom du plateau est obligatoire.")
        if not self.type_sport.strip():
            raise DomainValidationError("Le type de sport est obligatoire.")
        if self.capacite <= 0:
            raise DomainValidationError("La capacite doit etre superieure a 0.")
        if not self.emplacement.strip():
            raise DomainValidationError("L'emplacement est obligatoire.")


@dataclass(frozen=True)
class Creneau:
    debut: time
    fin: time

    def __post_init__(self) -> None:
        if self.debut >= self.fin:
            raise DomainValidationError("L'heure de debut doit etre avant l'heure de fin.")


@dataclass(frozen=True)
class Disponibilite:
    id: int | None
    plateau_id: int
    jour: WeekDay
    creneau: Creneau

    def __post_init__(self) -> None:
        if self.plateau_id <= 0:
            raise DomainValidationError("L'identifiant du plateau est invalide.")


class ReservationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Reservation:
    id: int | None
    plateau_id: int
    utilisateur: str
    date_reservation: date
    creneau: Creneau
    statut: ReservationStatus
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.plateau_id <= 0:
            raise DomainValidationError("L'identifiant du plateau est invalide.")
        if not self.utilisateur.strip():
            raise DomainValidationError("L'utilisateur est obligatoire.")
