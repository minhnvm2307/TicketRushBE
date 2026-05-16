from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=255)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return str(value).strip()


class UserResponse(APIModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
