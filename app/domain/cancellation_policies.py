from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from .models import Reservation


class CancellationPolicy(ABC):
    @abstractmethod
    def can_cancel(self, reservation: Reservation, requested_at: datetime) -> bool:
        raise NotImplementedError


class FlexibleCancellationPolicy(CancellationPolicy):
    def can_cancel(self, reservation: Reservation, requested_at: datetime) -> bool:
        return True


class Strict24hCancellationPolicy(CancellationPolicy):
    def can_cancel(self, reservation: Reservation, requested_at: datetime) -> bool:
        reservation_start = datetime.combine(reservation.date_reservation, reservation.creneau.debut)
        return reservation_start - requested_at >= timedelta(hours=24)
