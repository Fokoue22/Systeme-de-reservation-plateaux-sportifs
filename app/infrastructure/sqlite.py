from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.infrastructure.seeds import PLATEAUX_DATA, create_plateau_from_data

DEFAULT_DB_PATH = Path("reservation.db")


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
