from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Gender, UserRole
from app.schemas.common import APIModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    date_of_birth: date
    gender: Gender


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(APIModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
