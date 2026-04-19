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
    nb_personnes: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.plateau_id <= 0:
            raise DomainValidationError("L'identifiant du plateau est invalide.")
        if not self.utilisateur.strip():
            raise DomainValidationError("L'utilisateur est obligatoire.")
        if self.nb_personnes <= 0:
            raise DomainValidationError("Le nombre de personnes doit etre superieur a 0.")


@dataclass(frozen=True)
class UserAccount:
    id: int | None
    username: str
    password_hash: str
    email: str | None
    telephone: str | None
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise DomainValidationError("Le nom d'utilisateur est obligatoire.")
        if not self.password_hash.strip():
            raise DomainValidationError("Le hash du mot de passe est obligatoire.")


@dataclass(frozen=True)
class UserSession:
    token: str
    user_id: int
    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.token.strip():
            raise DomainValidationError("Le token de session est obligatoire.")
        if self.user_id <= 0:
            raise DomainValidationError("L'identifiant utilisateur est invalide.")
