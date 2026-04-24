import pytest
from datetime import datetime, timedelta
from app.application.m5_auth_services import AuthService
from app.domain.models import UserAccount, UserSession
from app.domain.repositories import UserAccountRepository, UserSessionRepository


class InMemoryUserAccountRepository(UserAccountRepository):
    def __init__(self):
        self.accounts = {}
        self._next_id = 1

    def create(self, account: UserAccount) -> UserAccount:
        created = UserAccount(
            id=self._next_id,
            username=account.username,
            password_hash=account.password_hash,
            email=account.email,
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
        if account.id and account.id in self.accounts:
            self.accounts[account.id] = account
            return account
        raise ValueError("Account not found")

    def delete(self, user_id: int) -> bool:
        return self.accounts.pop(user_id, None) is not None


class InMemorySessionRepository(UserSessionRepository):
    def __init__(self):
        self.sessions = {}

    def create(self, session: UserSession) -> UserSession:
        self.sessions[session.token] = session
        return session

    def get_by_token(self, token: str) -> UserSession | None:
        return self.sessions.get(token)

    def delete(self, token: str) -> bool:
        return self.sessions.pop(token, None) is not None

    def delete_by_user(self, user_id: int) -> int:
        tokens_to_delete = [token for token, session in self.sessions.items() if session.user_id == user_id]
        for token in tokens_to_delete:
            del self.sessions[token]
        return len(tokens_to_delete)

    def update(self, session: UserSession) -> UserSession:
        if session.token in self.sessions:
            self.sessions[session.token] = session
            return session
        raise ValueError("Session not found")


class DummyPasswordHasher:
    def hash_password(self, password: str) -> str:
        return f"hashed_{password}"

    def verify_password(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed_{password}"


class TestAuthService:
    def setup_method(self):
        self.user_repo = InMemoryUserAccountRepository()
        self.session_repo = InMemorySessionRepository()
        self.password_hasher = DummyPasswordHasher()
        self.service = AuthService(
            user_repo=self.user_repo,
            session_repo=self.session_repo,
            password_hasher=self.password_hasher
        )

    def test_register_creates_user_with_hashed_password(self):
        # Given
        username = "newuser"
        password = "password123"
        email = "newuser@example.com"

        # When
        user = self.service.register(username=username, password=password, email=email)

        # Then
        assert user.username == username
        assert user.email == email
        assert user.id is not None
        # Password should be hashed
        assert user.password_hash != password
        assert user.password_hash == f"hashed_{password}"

    def test_register_rejects_short_username(self):
        # Given
        username = "ab"  # Too short
        password = "password123"
        email = "user@example.com"

        # When/Then
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            self.service.register(username=username, password=password, email=email)

    def test_register_rejects_existing_username(self):
        # Given
        username = "existinguser"
        password = "password123"
        email = "user@example.com"

        # Create existing user
        self.service.register(username=username, password="oldpass", email="old@example.com")

        # When/Then
        with pytest.raises(ValueError, match="Username already exists"):
            self.service.register(username=username, password=password, email=email)

    def test_login_with_correct_credentials_returns_session(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"

        # Register user
        self.service.register(username=username, password=password, email=email)

        # When
        session = self.service.login(username=username, password=password)

        # Then
        assert session is not None
        assert session.user_id is not None
        assert session.token is not None
        assert session.expires_at > datetime.now()

    def test_login_with_wrong_password_fails(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"

        # Register user
        self.service.register(username=username, password=password, email=email)

        # When/Then
        with pytest.raises(ValueError, match="Invalid username or password"):
            self.service.login(username=username, password="wrongpassword")

    def test_login_with_nonexistent_user_fails(self):
        # Given
        username = "nonexistent"
        password = "password123"

        # When/Then
        with pytest.raises(ValueError, match="Invalid username or password"):
            self.service.login(username=username, password=password)

    def test_change_password_updates_password(self):
        # Given
        username = "testuser"
        old_password = "password123"
        new_password = "newpassword456"
        email = "test@example.com"

        # Register and login
        self.service.register(username=username, password=old_password, email=email)
        session = self.service.login(username=username, password=old_password)

        # When
        self.service.change_password(user_id=session.user_id, old_password=old_password, new_password=new_password)

        # Then
        # Old password should no longer work
        with pytest.raises(ValueError, match="Invalid username or password"):
            self.service.login(username=username, password=old_password)

        # New password should work
        new_session = self.service.login(username=username, password=new_password)
        assert new_session is not None

    def test_change_password_with_wrong_old_password_fails(self):
        # Given
        username = "testuser"
        old_password = "password123"
        wrong_old_password = "wrongpassword"
        new_password = "newpassword456"
        email = "test@example.com"

        # Register and login
        self.service.register(username=username, password=old_password, email=email)
        session = self.service.login(username=username, password=old_password)

        # When/Then
        with pytest.raises(ValueError, match="Invalid old password"):
            self.service.change_password(
                user_id=session.user_id,
                old_password=wrong_old_password,
                new_password=new_password
            )

    def test_update_account_updates_user_info(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"
        new_email = "newemail@example.com"

        # Register and login
        self.service.register(username=username, password=password, email=email)
        session = self.service.login(username=username, password=password)

        # When
        updated_user = self.service.update_account(
            user_id=session.user_id,
            email=new_email
        )

        # Then
        assert updated_user.email == new_email
        assert updated_user.username == username

    def test_delete_account_removes_user_and_sessions(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"

        # Register and login
        self.service.register(username=username, password=password, email=email)
        session = self.service.login(username=username, password=password)

        # When
        self.service.delete_account(user_id=session.user_id)

        # Then
        # User should be gone
        with pytest.raises(ValueError, match="Invalid username or password"):
            self.service.login(username=username, password=password)

        # Session should be invalid
        with pytest.raises(ValueError, match="Invalid session"):
            self.service.validate_session(session.token)

    def test_validate_session_with_valid_token_returns_user(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"

        # Register and login
        self.service.register(username=username, password=password, email=email)
        session = self.service.login(username=username, password=password)

        # When
        user = self.service.validate_session(session.token)

        # Then
        assert user.username == username
        assert user.email == email

    def test_validate_session_with_invalid_token_fails(self):
        # Given
        invalid_token = "invalid_token_123"

        # When/Then
        with pytest.raises(ValueError, match="Invalid session"):
            self.service.validate_session(invalid_token)

    def test_validate_session_with_expired_token_fails(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"

        # Register and login
        self.service.register(username=username, password=password, email=email)
        session = self.service.login(username=username, password=password)

        # Manually expire the session
        expired_session = self.session_repo.get_by_token(session.token)
        if expired_session:
            expired_session.expires_at = datetime.now() - timedelta(hours=1)
            self.session_repo.update(expired_session)

        # When/Then
        with pytest.raises(ValueError, match="Session expired"):
            self.service.validate_session(session.token)

    def test_logout_invalidates_session(self):
        # Given
        username = "testuser"
        password = "password123"
        email = "test@example.com"

        # Register and login
        self.service.register(username=username, password=password, email=email)
        session = self.service.login(username=username, password=password)

        # When
        self.service.logout(session.token)

        # Then
        with pytest.raises(ValueError, match="Invalid session"):
            self.service.validate_session(session.token)