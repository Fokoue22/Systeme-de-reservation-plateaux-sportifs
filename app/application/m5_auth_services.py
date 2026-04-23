from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from app.domain import UserAccount, UserSession
from app.domain.repositories import UserAccountRepository, UserSessionRepository


class AuthConflictError(ValueError):
    pass


class AuthNotFoundError(ValueError):
    pass


class AuthUnauthorizedError(ValueError):
    pass


class AuthService:
    def __init__(
        self,
        account_repo: UserAccountRepository,
        session_repo: UserSessionRepository,
        session_ttl_days: int = 14,
    ):
        self.account_repo = account_repo
        self.session_repo = session_repo
        self.session_ttl_days = session_ttl_days

    @staticmethod
    def _normalize_username(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _normalize_email(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return f"scrypt${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            algorithm, salt_hex, digest_hex = password_hash.split("$", 2)
        except ValueError:
            return False
        if algorithm != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return secrets.compare_digest(actual, expected)

    def register(
        self,
        full_name: str | None,
        username: str,
        password: str,
        email: str | None = None,
        telephone: str | None = None,
        is_admin: bool = False,
    ) -> tuple[UserAccount, UserSession]:
        normalized_username = self._normalize_username(username)
        normalized_email = self._normalize_email(email)
        if len(normalized_username) < 3:
            raise AuthConflictError("Le nom d'utilisateur doit contenir au moins 3 caracteres.")
        if len(password) < 6:
            raise AuthConflictError("Le mot de passe doit contenir au moins 6 caracteres.")

        existing = self.account_repo.get_by_username(normalized_username)
        if existing is not None:
            raise AuthConflictError("Ce nom d'utilisateur est deja utilise.")
        if normalized_email is not None and self.account_repo.get_by_email(normalized_email) is not None:
            raise AuthConflictError("Cette adresse e-mail est deja utilisee.")

        now = datetime.utcnow()
        account = UserAccount(
            id=None,
            full_name=(full_name.strip() if full_name and full_name.strip() else normalized_username),
            username=normalized_username,
            password_hash=self.hash_password(password),
            email=normalized_email,
            telephone=(telephone or None),
            is_admin=is_admin,
            created_at=now,
            updated_at=now,
        )
        created = self.account_repo.create(account)
        session = self._create_session(created.id or 0)
        return created, session

    def login(self, username: str, password: str) -> tuple[UserAccount, UserSession]:
        normalized_username = self._normalize_username(username)
        account = self.account_repo.get_by_username(normalized_username)
        if account is None or not self.verify_password(password, account.password_hash):
            raise AuthUnauthorizedError("Identifiants invalides.")
        session = self._create_session(account.id or 0)
        return account, session

    def update_profile(
        self,
        user_id: int,
        full_name: str,
        email: str | None,
        telephone: str | None,
    ) -> UserAccount:
        account = self.account_repo.get_by_id(user_id)
        if account is None:
            raise AuthNotFoundError("Compte introuvable.")

        normalized_email = self._normalize_email(email)
        if normalized_email is not None:
            existing = self.account_repo.get_by_email(normalized_email)
            if existing is not None and existing.id != user_id:
                raise AuthConflictError("Cette adresse e-mail est deja utilisee.")

        updated = UserAccount(
            id=account.id,
            full_name=full_name.strip() or account.full_name or account.username,
            username=account.username,
            password_hash=account.password_hash,
            email=normalized_email,
            telephone=telephone or None,
            is_admin=account.is_admin,
            created_at=account.created_at,
            updated_at=datetime.utcnow(),
        )
        return self.account_repo.update(updated)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> UserAccount:
        account = self.account_repo.get_by_id(user_id)
        if account is None:
            raise AuthNotFoundError("Compte introuvable.")
        if not self.verify_password(current_password, account.password_hash):
            raise AuthUnauthorizedError("Mot de passe actuel invalide.")
        if len(new_password) < 6:
            raise AuthConflictError("Le nouveau mot de passe doit contenir au moins 6 caracteres.")

        updated = UserAccount(
            id=account.id,
            full_name=account.full_name,
            username=account.username,
            password_hash=self.hash_password(new_password),
            email=account.email,
            telephone=account.telephone,
            is_admin=account.is_admin,
            created_at=account.created_at,
            updated_at=datetime.utcnow(),
        )
        return self.account_repo.update(updated)

    def delete_account(self, user_id: int, current_password: str) -> None:
        account = self.account_repo.get_by_id(user_id)
        if account is None:
            raise AuthNotFoundError("Compte introuvable.")
        if not self.verify_password(current_password, account.password_hash):
            raise AuthUnauthorizedError("Mot de passe actuel invalide.")

        self.session_repo.delete_by_user(user_id)
        self.account_repo.delete(user_id)

    def get_user_from_session(self, token: str | None) -> UserAccount | None:
        if not token:
            return None
        session = self.session_repo.get_by_token(token)
        if session is None:
            return None
        if session.expires_at < datetime.utcnow():
            self.session_repo.delete(token)
            return None
        return self.account_repo.get_by_id(session.user_id)

    def require_user_from_session(self, token: str | None) -> UserAccount:
        user = self.get_user_from_session(token)
        if user is None:
            raise AuthUnauthorizedError("Session invalide ou expiree.")
        return user

    def logout(self, token: str | None) -> None:
        if token:
            self.session_repo.delete(token)

    def _create_session(self, user_id: int) -> UserSession:
        now = datetime.utcnow()
        session = UserSession(
            token=secrets.token_urlsafe(48),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(days=self.session_ttl_days),
        )
        return self.session_repo.create(session)
