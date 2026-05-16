from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services import auth as auth_module
from app.services.auth import AuthService


class DummyDB:
    def __init__(self) -> None:
        self.committed = False
        self.refreshed = None

    def commit(self) -> None:
        self.committed = True

    def refresh(self, obj) -> None:
        self.refreshed = obj


class DummyEmail:
    def __init__(self) -> None:
        self.sent = []

    def send_password_reset_code(self, email: str, code: str, ttl_minutes: int) -> None:
        self.sent.append((email, code, ttl_minutes))


class DummyUsers:
    def __init__(self, user=None) -> None:
        self.user = user

    def get_by_email(self, email: str):
        if self.user and self.user.email == email:
            return self.user
        return None


def _make_service(user=None):
    service = AuthService.__new__(AuthService)
    service.db = DummyDB()
    service.users = DummyUsers(user)
    service.redis = None
    service.settings = SimpleNamespace(
        password_reset_code_ttl_minutes=10,
        password_reset_code_ttl_seconds=600,
    )
    service.email = DummyEmail()
    return service


@pytest.fixture(autouse=True)
def _clear_memory_codes():
    auth_module._PASSWORD_RESET_CODES.clear()
    yield
    auth_module._PASSWORD_RESET_CODES.clear()


def test_reset_password_request_requires_six_digit_code() -> None:
    with pytest.raises(ValidationError):
        ResetPasswordRequest(
            email="user@example.com",
            code="12ab56",
            new_password="Password123!",
        )


def test_request_password_reset_sends_code_for_existing_user(monkeypatch) -> None:
    user = SimpleNamespace(email="user@example.com")
    service = _make_service(user)
    monkeypatch.setattr(service, "_generate_reset_code", lambda: "123456")
    monkeypatch.setattr("app.services.auth.hash_password", lambda value: f"hashed:{value}")

    service.request_password_reset(ForgotPasswordRequest(email="USER@example.com"))

    assert service.email.sent == [("user@example.com", "123456", 10)]
    stored_hash, _ = auth_module._PASSWORD_RESET_CODES["user@example.com"]
    assert stored_hash == "hashed:123456"


def test_request_password_reset_does_not_reveal_missing_user(monkeypatch) -> None:
    service = _make_service(user=None)
    monkeypatch.setattr(service, "_generate_reset_code", lambda: "123456")

    service.request_password_reset(ForgotPasswordRequest(email="missing@example.com"))

    assert service.email.sent == []
    assert auth_module._PASSWORD_RESET_CODES == {}


def test_reset_password_updates_password_and_consumes_code(monkeypatch) -> None:
    user = SimpleNamespace(email="user@example.com", password_hash="old-hash")
    service = _make_service(user)
    monkeypatch.setattr("app.services.auth.hash_password", lambda value: f"hashed:{value}")
    monkeypatch.setattr(
        "app.services.auth.verify_password",
        lambda plain, hashed: hashed == f"hashed:{plain}",
    )
    service._store_password_reset_code("user@example.com", "hashed:654321")

    updated = service.reset_password(
        ResetPasswordRequest(
            email="user@example.com",
            code="654321",
            new_password="NewPassword123!",
        )
    )

    assert updated is user
    assert user.password_hash == "hashed:NewPassword123!"
    assert "user@example.com" not in auth_module._PASSWORD_RESET_CODES
    assert service.db.committed is True
    assert service.db.refreshed is user


def test_reset_password_rejects_invalid_code(monkeypatch) -> None:
    user = SimpleNamespace(email="user@example.com", password_hash="old-hash")
    service = _make_service(user)
    monkeypatch.setattr(
        "app.services.auth.verify_password",
        lambda plain, hashed: hashed == f"hashed:{plain}",
    )
    service._store_password_reset_code("user@example.com", "hashed:654321")

    with pytest.raises(ValueError, match="invalid or expired verification code"):
        service.reset_password(
            ResetPasswordRequest(
                email="user@example.com",
                code="111111",
                new_password="NewPassword123!",
            )
        )

    assert user.password_hash == "old-hash"
    assert service.db.committed is False
