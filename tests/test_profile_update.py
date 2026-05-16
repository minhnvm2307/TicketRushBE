from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.enums import Gender
from app.schemas.auth import UpdateProfileRequest
from app.services.auth import AuthService


class DummyDB:
    def __init__(self) -> None:
        self.committed = False
        self.refreshed = None

    def commit(self) -> None:
        self.committed = True

    def refresh(self, obj) -> None:
        self.refreshed = obj


class DummyUsers:
    def __init__(self, user) -> None:
        self.user = user

    def get_by_id(self, user_id: str):
        if str(self.user.id) == str(user_id):
            return self.user
        return None


def _make_service(user):
    db = DummyDB()
    service = AuthService.__new__(AuthService)
    service.db = db
    service.users = DummyUsers(user)
    return service, db


def test_update_profile_request_trims_full_name() -> None:
    payload = UpdateProfileRequest(full_name="  Nguyen Van A  ")

    assert payload.full_name == "Nguyen Van A"


def test_update_profile_request_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError, match="at least one profile field is required"):
        UpdateProfileRequest()


def test_update_profile_request_rejects_future_birth_date() -> None:
    with pytest.raises(ValidationError, match="date_of_birth must be in the past"):
        UpdateProfileRequest(date_of_birth=date.today() + timedelta(days=1))


def test_update_profile_changes_only_editable_profile_fields() -> None:
    user = SimpleNamespace(
        id="user-1",
        email="old@example.com",
        password_hash="secret",
        role="CUSTOMER",
        full_name="Old Name",
        date_of_birth=date(1999, 1, 1),
        gender=Gender.MALE,
    )
    service, db = _make_service(user)

    updated = service.update_profile(
        "user-1",
        UpdateProfileRequest(
            full_name="  New Name  ",
            date_of_birth=date(2000, 2, 2),
            gender=Gender.FEMALE,
        ),
    )

    assert updated.full_name == "New Name"
    assert updated.date_of_birth == date(2000, 2, 2)
    assert updated.gender == Gender.FEMALE
    assert updated.email == "old@example.com"
    assert updated.password_hash == "secret"
    assert updated.role == "CUSTOMER"
    assert db.committed is True
    assert db.refreshed is user
