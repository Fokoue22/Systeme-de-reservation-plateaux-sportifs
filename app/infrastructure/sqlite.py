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
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    utilisateur TEXT PRIMARY KEY,
                    email TEXT,
                    telephone TEXT,
                    email_enabled INTEGER NOT NULL DEFAULT 1,
                    sms_enabled INTEGER NOT NULL DEFAULT 0,
                    weekly_summary_enabled INTEGER NOT NULL DEFAULT 0,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    utilisateur TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    sent_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminder_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id INTEGER NOT NULL,
                    utilisateur TEXT NOT NULL,
                    reminder_type TEXT NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    sent_at TEXT,
                    UNIQUE(reservation_id, reminder_type),
                    FOREIGN KEY(reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    telephone TEXT,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES user_accounts(id) ON DELETE CASCADE
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
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_notifications_user_created
                ON notifications (utilisateur, created_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_notifications_status_event
                ON notifications (status, event_type)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reminder_tasks_due
                ON reminder_tasks (scheduled_for, sent_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_notification_preferences_weekly
                ON notification_preferences (weekly_summary_enabled, is_admin)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_accounts_username
                ON user_accounts (username)
                """
            )
            duplicate_email_rows = conn.execute(
                """
                SELECT lower(email) AS normalized_email
                FROM user_accounts
                WHERE email IS NOT NULL AND trim(email) <> ''
                GROUP BY lower(email)
                HAVING COUNT(*) > 1
                """
            ).fetchall()
            for duplicate_row in duplicate_email_rows:
                normalized_email = duplicate_row["normalized_email"]
                duplicate_accounts = conn.execute(
                    """
                    SELECT id
                    FROM user_accounts
                    WHERE lower(email) = ?
                    ORDER BY created_at ASC, id ASC
                    """,
                    (normalized_email,),
                ).fetchall()
                for row in duplicate_accounts[1:]:
                    conn.execute(
                        "UPDATE user_accounts SET email = NULL WHERE id = ?",
                        (row["id"],),
                    )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_user_accounts_email_lower
                ON user_accounts (lower(email))
                WHERE email IS NOT NULL
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_expires
                ON user_sessions (user_id, expires_at)
                """
            )

            columns = {row["name"] for row in conn.execute("PRAGMA table_info(reservations)").fetchall()}
            if "nb_personnes" not in columns:
                conn.execute("ALTER TABLE reservations ADD COLUMN nb_personnes INTEGER NOT NULL DEFAULT 1")

            user_account_columns = {row["name"] for row in conn.execute("PRAGMA table_info(user_accounts)").fetchall()}
            if "full_name" not in user_account_columns:
                conn.execute("ALTER TABLE user_accounts ADD COLUMN full_name TEXT")

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
