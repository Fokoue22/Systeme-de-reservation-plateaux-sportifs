import pytest
from datetime import datetime, time, date, timedelta
from app.application.m2_services import ReservationService
from app.domain.models import Reservation, Plateau, Creneau, UserAccount, ReservationStatus
from app.domain.repositories import ReservationRepository, PlateauRepository
from app.domain.cancellation_policies import StandardCancellationPolicy


class InMemoryReservationRepository(ReservationRepository):
    def __init__(self):
        self.reservations = {}
        self._next_id = 1

    def create(self, reservation: Reservation) -> Reservation:
        created = Reservation(
            id=self._next_id,
            plateau_id=reservation.plateau_id,
            user_id=reservation.user_id,
            date=reservation.date,
            creneau=reservation.creneau,
            person_count=reservation.person_count,
            status=reservation.status,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
        )
        self.reservations[self._next_id] = created
        self._next_id += 1
        return created

    def get_by_id(self, reservation_id: int) -> Reservation | None:
        return self.reservations.get(reservation_id)

    def list_by_user(self, user_id: int) -> list[Reservation]:
        return [r for r in self.reservations.values() if r.user_id == user_id]

    def list_by_plateau_and_date(self, plateau_id: int, date: date) -> list[Reservation]:
        return [r for r in self.reservations.values() if r.plateau_id == plateau_id and r.date == date]

    def update(self, reservation: Reservation) -> Reservation:
        if reservation.id and reservation.id in self.reservations:
            self.reservations[reservation.id] = reservation
            return reservation
        raise ValueError("Reservation not found")

    def delete(self, reservation_id: int) -> bool:
        return self.reservations.pop(reservation_id, None) is not None


class InMemoryPlateauRepository(PlateauRepository):
    def __init__(self):
        self.plateaux = {}

    def create(self, plateau: Plateau) -> Plateau:
        created = Plateau(
            id=plateau.id,
            name=plateau.name,
            sport_type=plateau.sport_type,
            capacity=plateau.capacity,
            location=plateau.location,
        )
        self.plateaux[plateau.id or 0] = created
        return created

    def get_by_id(self, plateau_id: int) -> Plateau | None:
        return self.plateaux.get(plateau_id)

    def list_all(self) -> list[Plateau]:
        return list(self.plateaux.values())

    def update(self, plateau: Plateau) -> Plateau:
        if plateau.id and plateau.id in self.plateaux:
            self.plateaux[plateau.id] = plateau
            return plateau
        raise ValueError("Plateau not found")

    def delete(self, plateau_id: int) -> bool:
        return self.plateaux.pop(plateau_id, None) is not None


class TestReservationService:
    def setup_method(self):
        self.reservation_repo = InMemoryReservationRepository()
        self.plateau_repo = InMemoryPlateauRepository()
        self.cancellation_policy = StandardCancellationPolicy()
        self.service = ReservationService(
            reservation_repo=self.reservation_repo,
            plateau_repo=self.plateau_repo,
            cancellation_policy=self.cancellation_policy
        )

        # Setup test data
        self.plateau = self.plateau_repo.create(Plateau(
            id=1,
            name="Gymnase A",
            sport_type="Basketball",
            capacity=10,
            location="Centre-ville"
        ))

    def test_create_reservation_confirms_when_slot_available(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        # When
        reservation = self.service.create_reservation(
            user_id=user.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # Then
        assert reservation.id is not None
        assert reservation.status == ReservationStatus.CONFIRMED
        assert reservation.user_id == user.id
        assert reservation.plateau_id == self.plateau.id
        assert reservation.date == reservation_date
        assert reservation.creneau == creneau
        assert reservation.person_count == 4

    def test_create_reservation_rejects_when_person_count_exceeds_capacity(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        # When/Then
        with pytest.raises(ValueError, match="Person count exceeds plateau capacity"):
            self.service.create_reservation(
                user_id=user.id,
                plateau_id=self.plateau.id,
                date=reservation_date,
                creneau=creneau,
                person_count=15  # Exceeds capacity of 10
            )

    def test_create_reservation_rejects_overlapping_slot(self):
        # Given
        user1 = UserAccount(id=1, username="user1", email="user1@example.com")
        user2 = UserAccount(id=2, username="user2", email="user2@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        # Create first reservation
        self.service.create_reservation(
            user_id=user1.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # When/Then - Try to create overlapping reservation
        with pytest.raises(ValueError, match="Time slot is not available"):
            self.service.create_reservation(
                user_id=user2.id,
                plateau_id=self.plateau.id,
                date=reservation_date,
                creneau=creneau,
                person_count=4
            )

    def test_create_reservation_adds_to_waitlist_when_slot_unavailable(self):
        # Given
        user1 = UserAccount(id=1, username="user1", email="user1@example.com")
        user2 = UserAccount(id=2, username="user2", email="user2@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        # Fill the slot
        self.service.create_reservation(
            user_id=user1.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=10  # Full capacity
        )

        # When - Try to create another reservation for same slot
        reservation = self.service.create_reservation(
            user_id=user2.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # Then
        assert reservation.status == ReservationStatus.WAITLISTED

    def test_cancel_reservation_promotes_waitlist(self):
        # Given
        user1 = UserAccount(id=1, username="user1", email="user1@example.com")
        user2 = UserAccount(id=2, username="user2", email="user2@example.com")
        user3 = UserAccount(id=3, username="user3", email="user3@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        # Create confirmed reservation
        confirmed_reservation = self.service.create_reservation(
            user_id=user1.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=10
        )

        # Create waitlisted reservations
        waitlist_reservation1 = self.service.create_reservation(
            user_id=user2.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )
        waitlist_reservation2 = self.service.create_reservation(
            user_id=user3.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # When - Cancel the confirmed reservation
        self.service.cancel_reservation(confirmed_reservation.id, user1.id)

        # Then - First waitlist should be promoted
        updated_waitlist1 = self.reservation_repo.get_by_id(waitlist_reservation1.id)
        updated_waitlist2 = self.reservation_repo.get_by_id(waitlist_reservation2.id)

        assert updated_waitlist1.status == ReservationStatus.CONFIRMED
        assert updated_waitlist2.status == ReservationStatus.WAITLISTED

    def test_cancel_reservation_with_penalty(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        reservation = self.service.create_reservation(
            user_id=user.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # When - Cancel with penalty (less than 24h before)
        penalty = self.service.cancel_reservation(reservation.id, user.id)

        # Then
        assert penalty > 0

    def test_update_reservation_rejects_invalid_person_count(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        reservation = self.service.create_reservation(
            user_id=user.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # When/Then
        with pytest.raises(ValueError, match="Person count exceeds plateau capacity"):
            self.service.update_reservation(
                reservation_id=reservation.id,
                user_id=user.id,
                person_count=15  # Exceeds capacity
            )

    def test_update_reservation_changes_person_count(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        reservation = self.service.create_reservation(
            user_id=user.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # When
        updated = self.service.update_reservation(
            reservation_id=reservation.id,
            user_id=user.id,
            person_count=6
        )

        # Then
        assert updated.person_count == 6

    def test_list_user_reservations(self):
        # Given
        user1 = UserAccount(id=1, username="user1", email="user1@example.com")
        user2 = UserAccount(id=2, username="user2", email="user2@example.com")
        reservation_date = date.today() + timedelta(days=1)

        # Create reservations for both users
        self.service.create_reservation(
            user_id=user1.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=Creneau(start=time(10, 0), end=time(11, 0)),
            person_count=4
        )
        self.service.create_reservation(
            user_id=user1.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=Creneau(start=time(14, 0), end=time(15, 0)),
            person_count=2
        )
        self.service.create_reservation(
            user_id=user2.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=Creneau(start=time(16, 0), end=time(17, 0)),
            person_count=3
        )

        # When
        user1_reservations = self.service.list_user_reservations(user1.id)
        user2_reservations = self.service.list_user_reservations(user2.id)

        # Then
        assert len(user1_reservations) == 2
        assert len(user2_reservations) == 1
        assert all(r.user_id == user1.id for r in user1_reservations)
        assert all(r.user_id == user2.id for r in user2_reservations)

    def test_get_reservation_details(self):
        # Given
        user = UserAccount(id=1, username="testuser", email="test@example.com")
        reservation_date = date.today() + timedelta(days=1)
        creneau = Creneau(start=time(10, 0), end=time(11, 0))

        reservation = self.service.create_reservation(
            user_id=user.id,
            plateau_id=self.plateau.id,
            date=reservation_date,
            creneau=creneau,
            person_count=4
        )

        # When
        details = self.service.get_reservation_details(reservation.id)

        # Then
        assert details.id == reservation.id
        assert details.user_id == user.id
        assert details.plateau_id == self.plateau.id
        assert details.date == reservation_date
        assert details.creneau == creneau
        assert details.person_count == 4
        assert details.status == ReservationStatus.CONFIRMED