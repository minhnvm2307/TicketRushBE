import uuid
from datetime import UTC, datetime, timedelta
from secrets import randbelow

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import RedisKey, get_redis_client, redis_is_enabled
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, RegisterRequest, ResetPasswordRequest, UpdateProfileRequest
from app.services.email import EmailService


_PASSWORD_RESET_CODES: dict[str, tuple[str, datetime]] = {}


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()
        self.redis = get_redis_client() if redis_is_enabled() else None
        self.email = EmailService()

    def register(self, payload: RegisterRequest) -> User:
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
        session_id = str(uuid.uuid4())
        token = create_access_token(subject=user.id, session_id=session_id)
        if self.redis:
            self.redis.set(
                RedisKey.auth_session(session_id),
                str(user.id),
                ex=self.settings.access_token_ttl_seconds,
            )
        return token

    def me(self, user_id: str) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise ValueError("user not found")
        return user
    
    def update_profile(self, user_id: str, payload: UpdateProfileRequest) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise ValueError("user not found")

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.date_of_birth is not None:
            user.date_of_birth = payload.date_of_birth
        if payload.gender is not None:
            user.gender = payload.gender

        self.db.commit()
        self.db.refresh(user)
        return user

    def request_password_reset(self, payload: ForgotPasswordRequest) -> None:
        email = self._normalize_email(payload.email)
        user = self.users.get_by_email(email)
        if not user:
            return

        code = self._generate_reset_code()
        self._store_password_reset_code(email, hash_password(code))
        self.email.send_password_reset_code(
            email,
            code,
            self.settings.password_reset_code_ttl_minutes,
        )

    def reset_password(self, payload: ResetPasswordRequest) -> User:
        email = self._normalize_email(payload.email)
        user = self.users.get_by_email(email)
        if not user or not self._verify_password_reset_code(email, payload.code):
            raise ValueError("invalid or expired verification code")

        user.password_hash = hash_password(payload.new_password)
        self._delete_password_reset_code(email)
        self.db.commit()
        self.db.refresh(user)
        return user

    @staticmethod
    def _normalize_email(email: str) -> str:
        return str(email).strip().lower()

    @staticmethod
    def _generate_reset_code() -> str:
        return f"{randbelow(1_000_000):06d}"

    def _store_password_reset_code(self, email: str, code_hash: str) -> None:
        if self.redis:
            self.redis.set(
                RedisKey.password_reset(email),
                code_hash,
                ex=self.settings.password_reset_code_ttl_seconds,
            )
            return

        expires_at = datetime.now(UTC) + timedelta(seconds=self.settings.password_reset_code_ttl_seconds)
        _PASSWORD_RESET_CODES[email] = (code_hash, expires_at)

    def _verify_password_reset_code(self, email: str, code: str) -> bool:
        code_hash = self._get_password_reset_code_hash(email)
        if not code_hash:
            return False
        return verify_password(code, code_hash)

    def _get_password_reset_code_hash(self, email: str) -> str | None:
        if self.redis:
            return self.redis.get(RedisKey.password_reset(email))

        stored = _PASSWORD_RESET_CODES.get(email)
        if not stored:
            return None
        code_hash, expires_at = stored
        if expires_at <= datetime.now(UTC):
            _PASSWORD_RESET_CODES.pop(email, None)
            return None
        return code_hash

    def _delete_password_reset_code(self, email: str) -> None:
        if self.redis:
            self.redis.delete(RedisKey.password_reset(email))
            return
        _PASSWORD_RESET_CODES.pop(email, None)
