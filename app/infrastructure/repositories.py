from __future__ import annotations

import sqlite3
from datetime import date, datetime, time

from app.domain.models import Creneau, Disponibilite, Plateau, Reservation, ReservationStatus, UserAccount, UserSession, WeekDay
from app.domain.notifications import (
    NotificationChannel,
    NotificationEventType,
    NotificationMessage,
    NotificationPreference,
    NotificationStatus,
    ReminderTask,
)
from app.domain.repositories import (
    DisponibiliteRepository,
    NotificationPreferenceRepository,
    NotificationRepository,
    PlateauRepository,
    ReminderTaskRepository,
    ReservationRepository,
    UserAccountRepository,
    UserSessionRepository,
)

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


class SQLiteNotificationPreferenceRepository(NotificationPreferenceRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def get_by_user(self, utilisateur: str) -> NotificationPreference | None:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT utilisateur, email, telephone, email_enabled, sms_enabled,
                       weekly_summary_enabled, is_admin, created_at, updated_at
                FROM notification_preferences
                WHERE utilisateur = ?
                """,
                (utilisateur,),
            ).fetchone()
        if row is None:
            return None
        return NotificationPreference(
            utilisateur=row["utilisateur"],
            email=row["email"],
            telephone=row["telephone"],
            email_enabled=bool(row["email_enabled"]),
            sms_enabled=bool(row["sms_enabled"]),
            weekly_summary_enabled=bool(row["weekly_summary_enabled"]),
            is_admin=bool(row["is_admin"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def upsert(self, preference: NotificationPreference) -> NotificationPreference:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO notification_preferences (
                    utilisateur, email, telephone, email_enabled, sms_enabled,
                    weekly_summary_enabled, is_admin, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(utilisateur) DO UPDATE SET
                    email=excluded.email,
                    telephone=excluded.telephone,
                    email_enabled=excluded.email_enabled,
                    sms_enabled=excluded.sms_enabled,
                    weekly_summary_enabled=excluded.weekly_summary_enabled,
                    is_admin=excluded.is_admin,
                    updated_at=excluded.updated_at
                """,
                (
                    preference.utilisateur,
                    preference.email,
                    preference.telephone,
                    int(preference.email_enabled),
                    int(preference.sms_enabled),
                    int(preference.weekly_summary_enabled),
                    int(preference.is_admin),
                    preference.created_at.isoformat(),
                    preference.updated_at.isoformat(),
                ),
            )
        return self.get_by_user(preference.utilisateur) or preference

    def list_admins_with_weekly_summary_enabled(self) -> list[NotificationPreference]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT utilisateur, email, telephone, email_enabled, sms_enabled,
                       weekly_summary_enabled, is_admin, created_at, updated_at
                FROM notification_preferences
                WHERE is_admin = 1 AND weekly_summary_enabled = 1
                ORDER BY utilisateur
                """
            ).fetchall()
        return [
            NotificationPreference(
                utilisateur=row["utilisateur"],
                email=row["email"],
                telephone=row["telephone"],
                email_enabled=bool(row["email_enabled"]),
                sms_enabled=bool(row["sms_enabled"]),
                weekly_summary_enabled=bool(row["weekly_summary_enabled"]),
                is_admin=bool(row["is_admin"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]


class SQLiteNotificationRepository(NotificationRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def create(self, message: NotificationMessage) -> NotificationMessage:
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notifications (
                    utilisateur, channel, event_type, subject, body, status, error, created_at, sent_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.utilisateur,
                    message.channel.value,
                    message.event_type.value,
                    message.subject,
                    message.body,
                    message.status.value,
                    message.error,
                    message.created_at.isoformat(),
                    message.sent_at.isoformat() if message.sent_at else None,
                ),
            )
            created_id = int(cursor.lastrowid)
        return NotificationMessage(
            id=created_id,
            utilisateur=message.utilisateur,
            channel=message.channel,
            event_type=message.event_type,
            subject=message.subject,
            body=message.body,
            status=message.status,
            error=message.error,
            created_at=message.created_at,
            sent_at=message.sent_at,
        )

    def list_by_user(self, utilisateur: str, limit: int = 100) -> list[NotificationMessage]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, utilisateur, channel, event_type, subject, body, status, error, created_at, sent_at
                FROM notifications
                WHERE utilisateur = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (utilisateur, limit),
            ).fetchall()
        return [
            NotificationMessage(
                id=int(row["id"]),
                utilisateur=row["utilisateur"],
                channel=NotificationChannel(row["channel"]),
                event_type=NotificationEventType(row["event_type"]),
                subject=row["subject"],
                body=row["body"],
                status=NotificationStatus(row["status"]),
                error=row["error"],
                created_at=datetime.fromisoformat(row["created_at"]),
                sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
            )
            for row in rows
        ]


class SQLiteReminderTaskRepository(ReminderTaskRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def upsert_task(self, task: ReminderTask) -> ReminderTask:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO reminder_tasks (reservation_id, utilisateur, reminder_type, scheduled_for, sent_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(reservation_id, reminder_type) DO UPDATE SET
                    utilisateur=excluded.utilisateur,
                    scheduled_for=excluded.scheduled_for,
                    sent_at=excluded.sent_at
                """,
                (
                    task.reservation_id,
                    task.utilisateur,
                    task.reminder_type,
                    task.scheduled_for.isoformat(),
                    task.sent_at.isoformat() if task.sent_at else None,
                ),
            )
            row = conn.execute(
                """
                SELECT id, reservation_id, utilisateur, reminder_type, scheduled_for, sent_at
                FROM reminder_tasks
                WHERE reservation_id = ? AND reminder_type = ?
                """,
                (task.reservation_id, task.reminder_type),
            ).fetchone()
        return ReminderTask(
            id=int(row["id"]),
            reservation_id=int(row["reservation_id"]),
            utilisateur=row["utilisateur"],
            reminder_type=row["reminder_type"],
            scheduled_for=datetime.fromisoformat(row["scheduled_for"]),
            sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
        )

    def list_due_tasks(self, now_utc: str) -> list[ReminderTask]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, reservation_id, utilisateur, reminder_type, scheduled_for, sent_at
                FROM reminder_tasks
                WHERE sent_at IS NULL AND scheduled_for <= ?
                ORDER BY scheduled_for, id
                """,
                (now_utc,),
            ).fetchall()
        return [
            ReminderTask(
                id=int(row["id"]),
                reservation_id=int(row["reservation_id"]),
                utilisateur=row["utilisateur"],
                reminder_type=row["reminder_type"],
                scheduled_for=datetime.fromisoformat(row["scheduled_for"]),
                sent_at=None,
            )
            for row in rows
        ]

    def mark_sent(self, task_id: int, sent_at_utc: str) -> ReminderTask | None:
        with self.db.connection() as conn:
            cursor = conn.execute(
                "UPDATE reminder_tasks SET sent_at = ? WHERE id = ?",
                (sent_at_utc, task_id),
            )
            if cursor.rowcount == 0:
                return None
            row = conn.execute(
                """
                SELECT id, reservation_id, utilisateur, reminder_type, scheduled_for, sent_at
                FROM reminder_tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        return ReminderTask(
            id=int(row["id"]),
            reservation_id=int(row["reservation_id"]),
            utilisateur=row["utilisateur"],
            reminder_type=row["reminder_type"],
            scheduled_for=datetime.fromisoformat(row["scheduled_for"]),
            sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
        )


class SQLiteUserAccountRepository(UserAccountRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def create(self, account: UserAccount) -> UserAccount:
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO user_accounts (username, password_hash, email, telephone, is_admin, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account.username,
                    account.password_hash,
                    account.email,
                    account.telephone,
                    int(account.is_admin),
                    account.created_at.isoformat(),
                    account.updated_at.isoformat(),
                ),
            )
            created_id = int(cursor.lastrowid)
        return UserAccount(
            id=created_id,
            username=account.username,
            password_hash=account.password_hash,
            email=account.email,
            telephone=account.telephone,
            is_admin=account.is_admin,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    def get_by_username(self, username: str) -> UserAccount | None:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT id, username, password_hash, email, telephone, is_admin, created_at, updated_at
                FROM user_accounts
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        return self._row_to_account(row)

    def get_by_id(self, user_id: int) -> UserAccount | None:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT id, username, password_hash, email, telephone, is_admin, created_at, updated_at
                FROM user_accounts
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_account(row)

    @staticmethod
    def _row_to_account(row) -> UserAccount | None:
        if row is None:
            return None
        return UserAccount(
            id=int(row["id"]),
            username=row["username"],
            password_hash=row["password_hash"],
            email=row["email"],
            telephone=row["telephone"],
            is_admin=bool(row["is_admin"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


class SQLiteUserSessionRepository(UserSessionRepository):
    def __init__(self, db: SQLiteManager):
        self.db = db

    def create(self, session: UserSession) -> UserSession:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO user_sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session.token,
                    session.user_id,
                    session.created_at.isoformat(),
                    session.expires_at.isoformat(),
                ),
            )
        return session

    def get_by_token(self, token: str) -> UserSession | None:
        with self.db.connection() as conn:
            row = conn.execute(
                """
                SELECT token, user_id, created_at, expires_at
                FROM user_sessions
                WHERE token = ?
                """,
                (token,),
            ).fetchone()
        if row is None:
            return None
        return UserSession(
            token=row["token"],
            user_id=int(row["user_id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
        )

    def delete(self, token: str) -> bool:
        with self.db.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM user_sessions WHERE token = ?",
                (token,),
            )
        return cursor.rowcount > 0
