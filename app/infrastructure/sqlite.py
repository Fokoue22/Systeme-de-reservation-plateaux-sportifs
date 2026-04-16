from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.infrastructure.seeds import PLATEAUX_DATA, create_plateau_from_data

DEFAULT_DB_PATH = Path("reservation.db")

DEFAULT_AVAILABILITY_DAYS = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)
DEFAULT_AVAILABILITY_START = "08:00"
DEFAULT_AVAILABILITY_END = "22:00"


class SQLiteManager:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plateaux (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    type_sport TEXT NOT NULL,
                    capacite INTEGER NOT NULL,
                    emplacement TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS disponibilites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plateau_id INTEGER NOT NULL,
                    jour TEXT NOT NULL,
                    heure_debut TEXT NOT NULL,
                    heure_fin TEXT NOT NULL,
                    FOREIGN KEY(plateau_id) REFERENCES plateaux(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plateau_id INTEGER NOT NULL,
                    utilisateur TEXT NOT NULL,
                    date_reservation TEXT NOT NULL,
                    heure_debut TEXT NOT NULL,
                    heure_fin TEXT NOT NULL,
                    statut TEXT NOT NULL,
                    nb_personnes INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(plateau_id) REFERENCES plateaux(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_confirmed_exact_slot
                ON reservations (plateau_id, date_reservation, heure_debut, heure_fin)
                WHERE statut = 'CONFIRMED'
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reservations_plateau_date_slot_status
                ON reservations (plateau_id, date_reservation, heure_debut, heure_fin, statut)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reservations_created_at
                ON reservations (created_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_disponibilites_plateau_jour_slot
                ON disponibilites (plateau_id, jour, heure_debut, heure_fin)
                """
            )

            columns = {row["name"] for row in conn.execute("PRAGMA table_info(reservations)").fetchall()}
            if "nb_personnes" not in columns:
                conn.execute("ALTER TABLE reservations ADD COLUMN nb_personnes INTEGER NOT NULL DEFAULT 1")

    def seed_initial_data(self) -> None:
        """
        Populate initial plateau data.
        
        Uses Factory Pattern to create domain objects from PLATEAUX_DATA.
        Inserts only missing rows (idempotent operation).
        Respects OCP: extend PLATEAUX_DATA to add new sports without modifying code.
        """
        with self.connection() as conn:
            # Cleanup old seed names from previous versions when not referenced by reservations.
            # This keeps migration safe for active data while preventing duplicated series.
            legacy_seed_names = {
                "Tennis - Zone A",
                "Tennis - Zone B",
                "Gymnase M1",
                "Gymnase M2",
                "Gymnase M3",
                "Piscine",
                "Terrain Soccer",
                "Terrain Volleyball",
                "Piscine - Zone Est - M1",
                "Piscine - Zone Est - M2",
                "Piscine - Zone Est - M3",
                "Piscine - Zone Est - M4",
                "Piscine - Zone Est - M5",
                "Piscine - Zone Est - Olympique - M4",
                "Piscine - Zone Est - Olympique - M5",
                "Piscine - Zone Est - Semi-olympique - M4",
                "Piscine - Zone Est - Semi-olympique - M5",
            }
            for name in legacy_seed_names:
                rows = conn.execute(
                    "SELECT id FROM plateaux WHERE nom = ?",
                    (name,),
                ).fetchall()
                for row in rows:
                    reservation_count = conn.execute(
                        "SELECT COUNT(*) AS cnt FROM reservations WHERE plateau_id = ?",
                        (row["id"],),
                    ).fetchone()["cnt"]
                    if reservation_count == 0:
                        conn.execute("DELETE FROM plateaux WHERE id = ?", (row["id"],))

            # Insert only missing seed data using factory method.
            for data in PLATEAUX_DATA:
                plateau = create_plateau_from_data(data)
                exists = conn.execute(
                    """
                    SELECT 1
                    FROM plateaux
                    WHERE nom = ? AND type_sport = ? AND capacite = ? AND emplacement = ?
                    LIMIT 1
                    """,
                    (plateau.nom, plateau.type_sport, plateau.capacite, plateau.emplacement),
                ).fetchone()
                if exists:
                    continue
                conn.execute(
                    "INSERT INTO plateaux (nom, type_sport, capacite, emplacement) VALUES (?, ?, ?, ?)",
                    (plateau.nom, plateau.type_sport, plateau.capacite, plateau.emplacement),
                )

            # Ensure each plateau has a default weekly availability window.
            plateau_rows = conn.execute("SELECT id FROM plateaux").fetchall()
            for plateau_row in plateau_rows:
                plateau_id = int(plateau_row["id"])
                for day in DEFAULT_AVAILABILITY_DAYS:
                    exists = conn.execute(
                        """
                        SELECT 1
                        FROM disponibilites
                        WHERE plateau_id = ? AND jour = ? AND heure_debut = ? AND heure_fin = ?
                        LIMIT 1
                        """,
                        (plateau_id, day, DEFAULT_AVAILABILITY_START, DEFAULT_AVAILABILITY_END),
                    ).fetchone()
                    if exists:
                        continue
                    conn.execute(
                        """
                        INSERT INTO disponibilites (plateau_id, jour, heure_debut, heure_fin)
                        VALUES (?, ?, ?, ?)
                        """,
                        (plateau_id, day, DEFAULT_AVAILABILITY_START, DEFAULT_AVAILABILITY_END),
                    )
