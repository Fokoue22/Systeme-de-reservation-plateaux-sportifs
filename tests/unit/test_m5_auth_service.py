from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.application.m5_auth_services import AuthConflictError, AuthNotFoundError, AuthService, AuthUnauthorizedError
from app.domain.models import UserAccount, UserSession


class InMemoryUserAccountRepository:
    def __init__(self) -> None:
        self._accounts: dict[int, UserAccount] = {}
        self._next_id = 1

    def create(self, account: UserAccount) -> UserAccount:
        created = UserAccount(
            id=self._next_id,
            full_name=account.full_name,
            username=account.username,
            password_hash=account.password_hash,
            email=account.email,
            telephone=account.telephone,
            is_admin=account.is_admin,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
        self._accounts[self._next_id] = created
        self._next_id += 1
        return created

    def get_by_username(self, username: str) -> UserAccount | None:
        return next((account for account in self._accounts.values() if account.username == username), None)

    def get_by_email(self, email: str | None) -> UserAccount | None:
        if email is None:
            return None
        return next((account for account in self._accounts.values() if account.email == email), None)

    def get_by_id(self, user_id: int) -> UserAccount | None:
        return self._accounts.get(user_id)

    def update(self, account: UserAccount) -> UserAccount:
        if account.id is None or account.id not in self._accounts:
            raise KeyError("Compte introuvable")
        self._accounts[account.id] = account
        return account

    def delete(self, user_id: int) -> bool:
        return self._accounts.pop(user_id, None) is not None


class InMemoryUserSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, UserSession] = {}

    def create(self, session: UserSession) -> UserSession:
        self._sessions[session.token] = session
        return session

    def get_by_token(self, token: str) -> UserSession | None:
        return self._sessions.get(token)

    def delete(self, token: str) -> bool:
        return self._sessions.pop(token, None) is not None

    def delete_by_user(self, user_id: int) -> int:
        keys = [token for token, session in self._sessions.items() if session.user_id == user_id]
        for token in keys:
            del self._sessions[token]
        return len(keys)


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(
        account_repo=InMemoryUserAccountRepository(),
        session_repo=InMemoryUserSessionRepository(),
    )


def test_register_rejects_short_username(auth_service: AuthService) -> None:
    with pytest.raises(AuthConflictError, match="au moins 3 caracteres"):
        auth_service.register(
            full_name="A",
            username="ab",
            password="secret12",
            email="ab@example.com",
            telephone=None,
        )


def test_register_rejects_duplicate_username(auth_service: AuthService) -> None:
    auth_service.register(
        full_name="User One",
        username="duplicate",
        password="secret12",
        email="one@example.com",
    )

    with pytest.raises(AuthConflictError, match="deja utilise"):
        auth_service.register(
            full_name="User Two",
            username="duplicate",
            password="secret12",
            email="two@example.com",
        )


def test_login_rejects_invalid_credentials(auth_service: AuthService) -> None:
    auth_service.register(
        full_name="Login User",
        username="loginuser",
        password="secret12",
        email="login@example.com",
    )

    with pytest.raises(AuthUnauthorizedError, match="Identifiants invalides"):
        auth_service.login(username="loginuser", password="badpass")


def test_change_password_rejects_invalid_current_password(auth_service: AuthService) -> None:
    user, _ = auth_service.register(
        full_name="Password User",
        username="passworduser",
        password="secret12",
        email="password@example.com",
    )

    with pytest.raises(AuthUnauthorizedError, match="Mot de passe actuel invalide"):
        auth_service.change_password(
            user_id=user.id or 0,
            current_password="wrongpass",
            new_password="newsecret12",
        )


def test_delete_account_rejects_invalid_password(auth_service: AuthService) -> None:
    user, _ = auth_service.register(
        full_name="Delete User",
        username="deleteuser",
        password="secret12",
        email="delete@example.com",
    )

    with pytest.raises(AuthUnauthorizedError, match="Mot de passe actuel invalide"):
        auth_service.delete_account(user_id=user.id or 0, current_password="wrongpass")


def test_get_user_from_session_returns_none_when_expired(auth_service: AuthService) -> None:
    user, session = auth_service.register(
        full_name="Expire User",
        username="expireuser",
        password="secret12",
        email="expire@example.com",
    )

    expired_session = UserSession(
        token=session.token,
        user_id=user.id or 0,
        created_at=datetime.utcnow() - timedelta(days=10),
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    auth_service.session_repo.create(expired_session)

    assert auth_service.get_user_from_session(expired_session.token) is None
