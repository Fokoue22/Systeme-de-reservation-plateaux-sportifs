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
        Populate initial plateau data if tables are empty.
        
        Uses Factory Pattern to create domain objects from PLATEAUX_DATA.
        Only seeds if plateaux table is empty (idempotent operation).
        Respects OCP: extend PLATEAUX_DATA to add new sports without modifying code.
        """
        with self.connection() as conn:
            # Check if plateaux table already has data
            count = conn.execute("SELECT COUNT(*) as cnt FROM plateaux").fetchone()["cnt"]
            
            if count > 0:
                # Already seeded; don't duplicate data
                return
            
            # Insert seed data using factory method
            for data in PLATEAUX_DATA:
                plateau = create_plateau_from_data(data)
                conn.execute(
                    "INSERT INTO plateaux (nom, type_sport, capacite, emplacement) VALUES (?, ?, ?, ?)",
                    (plateau.nom, plateau.type_sport, plateau.capacite, plateau.emplacement),
                )
