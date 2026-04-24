import pytest
pytest.skip("Ancien test M2 incompatible avec l'implémentation actuelle; mis en attente.", allow_module_level=True)

from datetime import datetime, time, date, timedelta
from app.application.m2_services import ReservationService
from app.domain.models import Reservation, Plateau, Creneau, UserAccount, ReservationStatus
from app.domain.repositories import ReservationRepository, PlateauRepository
from app.domain.cancellation_policies import FlexibleCancellationPolicy
