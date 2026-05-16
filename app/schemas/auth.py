from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.enums import Gender, UserRole
from app.schemas.common import APIModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    date_of_birth: date
    gender: Gender

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("full_name must be at least 2 characters")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    date_of_birth: date | None = None
    gender: Gender | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def reject_null_full_name(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("full_name cannot be null")
        return value

    @field_validator("date_of_birth", "gender", mode="before")
    @classmethod
    def reject_null_profile_fields(cls, value):
        if value is None:
            raise ValueError("profile fields cannot be null")
        return value

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if len(value) < 2:
            raise ValueError("full_name must be at least 2 characters")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        if value is not None and value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if self.full_name is None and self.date_of_birth is None and self.gender is None:
            raise ValueError("at least one profile field is required")
        return self


class UserResponse(APIModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole


class UserProfileResponse(UserResponse):
    date_of_birth: date
    gender: Gender


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
