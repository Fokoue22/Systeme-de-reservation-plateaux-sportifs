from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

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
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(plateau_id) REFERENCES plateaux(id) ON DELETE CASCADE
                )
                """
            )
