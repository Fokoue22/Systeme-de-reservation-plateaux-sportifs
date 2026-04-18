from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from .models import Disponibilite, Plateau, Reservation, ReservationStatus
from .notifications import NotificationMessage, NotificationPreference, ReminderTask


class PlateauRepository(ABC):
    @abstractmethod
    def create(self, plateau: Plateau) -> Plateau:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, plateau_id: int) -> Plateau | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Plateau]:
        raise NotImplementedError

    @abstractmethod
    def update(self, plateau: Plateau) -> Plateau:
        raise NotImplementedError

    @abstractmethod
    def delete(self, plateau_id: int) -> bool:
        raise NotImplementedError


class DisponibiliteRepository(ABC):
    @abstractmethod
    def create(self, disponibilite: Disponibilite) -> Disponibilite:
        raise NotImplementedError

    @abstractmethod
    def list_by_plateau(self, plateau_id: int) -> list[Disponibilite]:
        raise NotImplementedError


class ReservationRepository(ABC):
    @abstractmethod
    def create(self, reservation: Reservation) -> Reservation:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, reservation_id: int) -> Reservation | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[Reservation]:
        raise NotImplementedError

    @abstractmethod
    def list_by_plateau_and_date(self, plateau_id: int, reservation_date: date) -> list[Reservation]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def update_status(self, reservation_id: int, status: ReservationStatus) -> Reservation | None:
        raise NotImplementedError


class NotificationPreferenceRepository(ABC):
    @abstractmethod
    def get_by_user(self, utilisateur: str) -> NotificationPreference | None:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, preference: NotificationPreference) -> NotificationPreference:
        raise NotImplementedError

    @abstractmethod
    def list_admins_with_weekly_summary_enabled(self) -> list[NotificationPreference]:
        raise NotImplementedError


class NotificationRepository(ABC):
    @abstractmethod
    def create(self, message: NotificationMessage) -> NotificationMessage:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, utilisateur: str, limit: int = 100) -> list[NotificationMessage]:
        raise NotImplementedError


class ReminderTaskRepository(ABC):
    @abstractmethod
    def upsert_task(self, task: ReminderTask) -> ReminderTask:
        raise NotImplementedError

    @abstractmethod
    def list_due_tasks(self, now_utc: str) -> list[ReminderTask]:
        raise NotImplementedError

    @abstractmethod
    def mark_sent(self, task_id: int, sent_at_utc: str) -> ReminderTask | None:
        raise NotImplementedError
