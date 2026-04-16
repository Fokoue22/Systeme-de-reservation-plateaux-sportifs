from __future__ import annotations

import sqlite3
from datetime import date, datetime, time

from app.domain.models import Creneau, Disponibilite, Plateau, Reservation, ReservationStatus, WeekDay
from app.domain.repositories import DisponibiliteRepository, PlateauRepository, ReservationRepository

from .sqlite import SQLiteManager


class SQLitePlateauRepository(PlateauRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def create(self, plateau: Plateau) -> Plateau:
        with self.db.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO plateaux (nom, type_sport, capacite, emplacement) VALUES (?, ?, ?, ?)",
                (plateau.nom, plateau.type_sport, plateau.capacite, plateau.emplacement),
            )
            created_id = int(cursor.lastrowid)
        return Plateau(
            id=created_id,
            nom=plateau.nom,
            type_sport=plateau.type_sport,
            capacite=plateau.capacite,
            emplacement=plateau.emplacement,
        )

    def get_by_id(self, plateau_id: int) -> Plateau | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT id, nom, type_sport, capacite, emplacement FROM plateaux WHERE id = ?",
                (plateau_id,),
            ).fetchone()
        if row is None:
            return None
        return Plateau(
            id=int(row["id"]),
            nom=row["nom"],
            type_sport=row["type_sport"],
            capacite=int(row["capacite"]),
            emplacement=row["emplacement"],
        )

    def list_all(self) -> list[Plateau]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, nom, type_sport, capacite, emplacement FROM plateaux ORDER BY id"
            ).fetchall()
        return [
            Plateau(
                id=int(row["id"]),
                nom=row["nom"],
                type_sport=row["type_sport"],
                capacite=int(row["capacite"]),
                emplacement=row["emplacement"],
            )
            for row in rows
        ]

    def update(self, plateau: Plateau) -> Plateau:
        if plateau.id is None:
            raise ValueError("Un identifiant est requis pour la mise a jour.")
        with self.db.connection() as conn:
            conn.execute(
                """
                UPDATE plateaux
                SET nom = ?, type_sport = ?, capacite = ?, emplacement = ?
                WHERE id = ?
                """,
                (plateau.nom, plateau.type_sport, plateau.capacite, plateau.emplacement, plateau.id),
            )
        return plateau

    def delete(self, plateau_id: int) -> bool:
        with self.db.connection() as conn:
            cursor = conn.execute("DELETE FROM plateaux WHERE id = ?", (plateau_id,))
        return cursor.rowcount > 0


class SQLiteDisponibiliteRepository(DisponibiliteRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def create(self, disponibilite: Disponibilite) -> Disponibilite:
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO disponibilites (plateau_id, jour, heure_debut, heure_fin)
                VALUES (?, ?, ?, ?)
                """,
                (
                    disponibilite.plateau_id,
                    disponibilite.jour.value,
                    disponibilite.creneau.debut.isoformat(timespec="minutes"),
                    disponibilite.creneau.fin.isoformat(timespec="minutes"),
                ),
            )
            created_id = int(cursor.lastrowid)
        return Disponibilite(
            id=created_id,
            plateau_id=disponibilite.plateau_id,
            jour=disponibilite.jour,
            creneau=disponibilite.creneau,
        )

    def list_by_plateau(self, plateau_id: int) -> list[Disponibilite]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, plateau_id, jour, heure_debut, heure_fin
                FROM disponibilites
                WHERE plateau_id = ?
                ORDER BY jour, heure_debut
                """,
                (plateau_id,),
            ).fetchall()
        return [
            Disponibilite(
                id=int(row["id"]),
                plateau_id=int(row["plateau_id"]),
                jour=WeekDay(row["jour"]),
                creneau=Creneau(
                    debut=time.fromisoformat(row["heure_debut"]),
                    fin=time.fromisoformat(row["heure_fin"]),
                ),
            )
            for row in rows
        ]


class SQLiteReservationRepository(ReservationRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def create(self, reservation: Reservation) -> Reservation:
        with self.db.connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO reservations (
                        plateau_id, utilisateur, date_reservation, heure_debut, heure_fin, statut, nb_personnes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reservation.plateau_id,
                        reservation.utilisateur,
                        reservation.date_reservation.isoformat(),
                        reservation.creneau.debut.isoformat(timespec="minutes"),
                        reservation.creneau.fin.isoformat(timespec="minutes"),
                        reservation.statut.value,
                        reservation.nb_personnes,
                        reservation.created_at.isoformat(),
                    ),
                )
                created_id = int(cursor.lastrowid)
                created_status = reservation.statut
            except sqlite3.IntegrityError as exc:
                if reservation.statut != ReservationStatus.CONFIRMED:
                    raise
                cursor = conn.execute(
                    """
                    INSERT INTO reservations (
                        plateau_id, utilisateur, date_reservation, heure_debut, heure_fin, statut, nb_personnes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reservation.plateau_id,
                        reservation.utilisateur,
                        reservation.date_reservation.isoformat(),
                        reservation.creneau.debut.isoformat(timespec="minutes"),
                        reservation.creneau.fin.isoformat(timespec="minutes"),
                        ReservationStatus.WAITLISTED.value,
                        reservation.nb_personnes,
                        reservation.created_at.isoformat(),
                    ),
                )
                created_id = int(cursor.lastrowid)
                created_status = ReservationStatus.WAITLISTED

        return Reservation(
            id=created_id,
            plateau_id=reservation.plateau_id,
            utilisateur=reservation.utilisateur,
            date_reservation=reservation.date_reservation,
            creneau=reservation.creneau,
            statut=created_status,
            nb_personnes=reservation.nb_personnes,
            created_at=reservation.created_at,
        )

    def get_by_id(self, reservation_id: int) -> Reservation | None:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT id, plateau_id, utilisateur, date_reservation, heure_debut, heure_fin, statut, nb_personnes, created_at
                FROM reservations
                WHERE id = ?
                """,
                (reservation_id,),
            ).fetchone()
        return self._row_to_reservation(row)

    def list_all(self) -> list[Reservation]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, plateau_id, utilisateur, date_reservation, heure_debut, heure_fin, statut, nb_personnes, created_at
                FROM reservations
                ORDER BY created_at, id
                """
            ).fetchall()
        return [self._row_to_reservation(row) for row in rows if row is not None]

    def list_by_plateau_and_date(self, plateau_id: int, reservation_date: date) -> list[Reservation]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, plateau_id, utilisateur, date_reservation, heure_debut, heure_fin, statut, nb_personnes, created_at
                FROM reservations
                WHERE plateau_id = ? AND date_reservation = ?
                ORDER BY created_at, id
                """,
                (plateau_id, reservation_date.isoformat()),
            ).fetchall()
        return [self._row_to_reservation(row) for row in rows if row is not None]

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
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                UPDATE reservations
                SET plateau_id = ?, date_reservation = ?, heure_debut = ?, heure_fin = ?, statut = ?, nb_personnes = ?
                WHERE id = ?
                """,
                (
                    plateau_id,
                    reservation_date.isoformat(),
                    creneau_debut,
                    creneau_fin,
                    statut.value,
                    nb_personnes,
                    reservation_id,
                ),
            )
        if cursor.rowcount == 0:
            return None
        return self.get_by_id(reservation_id)

    def update_status(self, reservation_id: int, status: ReservationStatus) -> Reservation | None:
        with self.db.connection() as conn:
            cursor = conn.execute(
                "UPDATE reservations SET statut = ? WHERE id = ?",
                (status.value, reservation_id),
            )
        if cursor.rowcount == 0:
            return None
        return self.get_by_id(reservation_id)

    @staticmethod
    def _row_to_reservation(row) -> Reservation | None:
        if row is None:
            return None
        return Reservation(
            id=int(row["id"]),
            plateau_id=int(row["plateau_id"]),
            utilisateur=row["utilisateur"],
            date_reservation=date.fromisoformat(row["date_reservation"]),
            creneau=Creneau(
                debut=time.fromisoformat(row["heure_debut"]),
                fin=time.fromisoformat(row["heure_fin"]),
            ),
            statut=ReservationStatus(row["statut"]),
            nb_personnes=int(row["nb_personnes"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
