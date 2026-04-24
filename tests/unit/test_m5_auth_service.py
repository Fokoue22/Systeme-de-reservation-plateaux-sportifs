from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.application.m5_auth_services import AuthService, AuthConflictError, AuthNotFoundError, AuthUnauthorizedError
from app.domain.models import UserAccount, UserSession
from app.domain.repositories import UserAccountRepository, UserSessionRepository


class InMemoryUserAccountRepository(UserAccountRepository):
    def __init__(self):
        self.accounts: dict[int, UserAccount] = {}
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
        self.accounts[self._next_id] = created
        self._next_id += 1
        return created

    def get_by_username(self, username: str) -> UserAccount | None:
        return next((acc for acc in self.accounts.values() if acc.username == username), None)

    def get_by_email(self, email: str) -> UserAccount | None:
        return next((acc for acc in self.accounts.values() if acc.email == email), None)

    def get_by_id(self, user_id: int) -> UserAccount | None:
        return self.accounts.get(user_id)

    def update(self, account: UserAccount) -> UserAccount:
        if account.id is None or account.id not in self.accounts:
            raise ValueError("Account not found")
        self.accounts[account.id] = account
        return account

    def delete(self, user_id: int) -> bool:
        return self.accounts.pop(user_id, None) is not None


class InMemorySessionRepository(UserSessionRepository):
    def __init__(self):
        self.sessions: dict[str, UserSession] = {}

    def create(self, session: UserSession) -> UserSession:
        self.sessions[session.token] = session
        return session

    def get_by_token(self, token: str) -> UserSession | None:
        return self.sessions.get(token)

    def delete(self, token: str) -> bool:
        return self.sessions.pop(token, None) is not None

    def delete_by_user(self, user_id: int) -> int:
        tokens = [token for token, session in self.sessions.items() if session.user_id == user_id]
        for token in tokens:
            del self.sessions[token]
        return len(tokens)


class TestAuthService:
    def setup_method(self):
        self.account_repo = InMemoryUserAccountRepository()
        self.session_repo = InMemorySessionRepository()
        self.service = AuthService(
            account_repo=self.account_repo,
            session_repo=self.session_repo,
        )

    def test_register_creates_account_and_session(self):
        account, session = self.service.register(
            full_name="Test User",
            username="TestUser",
            password="password123",
            email="USER@example.com",
            telephone="0123456789",
        )

        assert account.username == "testuser"
        assert account.email == "user@example.com"
        assert account.full_name == "Test User"
        assert account.id is not None
        assert account.password_hash != "password123"
        assert session.user_id == account.id
        assert session.token
        assert session.expires_at > datetime.utcnow()

    def test_register_rejects_duplicate_username(self):
        self.service.register(full_name="First", username="duplicate", password="password123", email="first@example.com")

        with pytest.raises(AuthConflictError, match="Ce nom d'utilisateur est deja utilise"):
            self.service.register(full_name="Second", username="duplicate", password="password123", email="second@example.com")

    def test_register_rejects_duplicate_email(self):
        self.service.register(full_name="First", username="user1", password="password123", email="same@example.com")

        with pytest.raises(AuthConflictError, match="Cette adresse e-mail est deja utilisee"):
            self.service.register(full_name="Second", username="user2", password="password123", email="same@example.com")

    def test_login_with_correct_credentials(self):
        self.service.register(full_name="Test User", username="loginuser", password="password123", email="login@example.com")
        account, session = self.service.login(username="loginuser", password="password123")

        assert account.username == "loginuser"
        assert session.user_id == account.id
        assert session.token

    def test_login_with_wrong_password_raises_unauthorized(self):
        self.service.register(full_name="Test User", username="loginuser", password="password123", email="login@example.com")

        with pytest.raises(AuthUnauthorizedError):
            self.service.login(username="loginuser", password="wrongpass")

    def test_login_with_nonexistent_user_raises_unauthorized(self):
        with pytest.raises(AuthUnauthorizedError):
            self.service.login(username="nouser", password="password123")

    def test_update_profile_changes_information(self):
        account, _ = self.service.register(full_name="Test User", username="profileuser", password="password123", email="profile@example.com")

        updated = self.service.update_profile(
            user_id=account.id or 0,
            full_name="Updated Name",
            email="updated@example.com",
            telephone="0987654321",
        )

        assert updated.full_name == "Updated Name"
        assert updated.email == "updated@example.com"
        assert updated.telephone == "0987654321"

    def test_update_profile_rejects_duplicate_email(self):
        self.service.register(full_name="First", username="user1", password="password123", email="first@example.com")
        account, _ = self.service.register(full_name="Second", username="user2", password="password123", email="second@example.com")

        with pytest.raises(AuthConflictError):
            self.service.update_profile(
                user_id=account.id or 0,
                full_name="Second",
                email="first@example.com",
                telephone=None,
            )

    def test_change_password_allows_login_with_new_password(self):
        account, _ = self.service.register(full_name="Test User", username="changepw", password="password123", email="pw@example.com")

        updated = self.service.change_password(
            user_id=account.id or 0,
            current_password="password123",
            new_password="newpassword456",
        )

        assert updated.password_hash != account.password_hash

        with pytest.raises(AuthUnauthorizedError):
            self.service.login(username="changepw", password="password123")

        _, new_session = self.service.login(username="changepw", password="newpassword456")
        assert new_session.token

    def test_change_password_with_wrong_current_password_raises(self):
        account, _ = self.service.register(full_name="Test User", username="changepw", password="password123", email="pw@example.com")

        with pytest.raises(AuthUnauthorizedError):
            self.service.change_password(
                user_id=account.id or 0,
                current_password="wrongpassword",
                new_password="newpassword456",
            )

    def test_change_password_with_short_new_password_raises(self):
        account, _ = self.service.register(full_name="Test User", username="changepw", password="password123", email="pw@example.com")

        with pytest.raises(AuthConflictError):
            self.service.change_password(
                user_id=account.id or 0,
                current_password="password123",
                new_password="123",
            )

    def test_delete_account_removes_account_and_sessions(self):
        account, session = self.service.register(full_name="Test User", username="deleteuser", password="password123", email="delete@example.com")

        self.service.delete_account(user_id=account.id or 0, current_password="password123")

        assert self.account_repo.get_by_id(account.id or 0) is None
        assert self.session_repo.get_by_token(session.token) is None

    def test_get_user_from_session_returns_none_for_expired_token(self):
        account, session = self.service.register(full_name="Test User", username="sessionuser", password="password123", email="session@example.com")
        expired = UserSession(
            token=session.token,
            user_id=account.id or 0,
            created_at=datetime.utcnow() - timedelta(days=30),
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        self.session_repo.create(expired)

        assert self.service.get_user_from_session(session.token) is None
        assert self.session_repo.get_by_token(session.token) is None

    def test_require_user_from_session_raises_for_invalid_token(self):
        with pytest.raises(AuthUnauthorizedError):
            self.service.require_user_from_session("invalidtoken")

    def test_logout_deletes_token(self):
        _, session = self.service.register(full_name="Test User", username="logoutuser", password="password123", email="logout@example.com")

        self.service.logout(session.token)

        assert self.session_repo.get_by_token(session.token) is None

    def test_verify_password_rejects_invalid_hash(self):
        assert self.service.verify_password("password123", "invalid-hash") is False
