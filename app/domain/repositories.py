from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from .models import Disponibilite, Plateau, Reservation, ReservationStatus


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
    def update_status(self, reservation_id: int, status: ReservationStatus) -> Reservation | None:
        raise NotImplementedError
