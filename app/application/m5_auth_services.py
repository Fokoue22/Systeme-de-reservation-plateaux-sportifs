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
        username: str,
        password: str,
        email: str | None = None,
        telephone: str | None = None,
        is_admin: bool = False,
    ) -> tuple[UserAccount, UserSession]:
        normalized_username = self._normalize_username(username)
        if len(normalized_username) < 3:
            raise AuthConflictError("Le nom d'utilisateur doit contenir au moins 3 caracteres.")
        if len(password) < 6:
            raise AuthConflictError("Le mot de passe doit contenir au moins 6 caracteres.")

        existing = self.account_repo.get_by_username(normalized_username)
        if existing is not None:
            raise AuthConflictError("Ce nom d'utilisateur est deja utilise.")

        now = datetime.utcnow()
        account = UserAccount(
            id=None,
            username=normalized_username,
            password_hash=self.hash_password(password),
            email=(email or None),
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
