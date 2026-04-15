from datetime import date

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> User:
        if payload.date_of_birth >= date.today():
            raise ValueError("date_of_birth must be in the past")
        if self.users.get_by_email(payload.email):
            raise ValueError("email already exists")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
        )
        self.users.create(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: LoginRequest) -> str:
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("invalid email or password")
        return create_access_token(subject=user.id, role=user.role.value)

    def me(self, user_id: str) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise ValueError("user not found")
        return user
