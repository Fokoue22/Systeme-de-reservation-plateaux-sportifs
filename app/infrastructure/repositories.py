from __future__ import annotations

from datetime import time

from app.domain.models import Creneau, Disponibilite, Plateau, WeekDay
from app.domain.repositories import DisponibiliteRepository, PlateauRepository

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
