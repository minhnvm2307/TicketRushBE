from datetime import date

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import Gender, UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.core.config import get_settings


class BootstrapService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def seed_admin(self) -> None:
        settings = get_settings()
        if self.repo.get_by_email(settings.default_admin_email):
            return

        admin = User(
            email=settings.default_admin_email,
            password_hash=hash_password(settings.default_admin_password),
            full_name=settings.default_admin_name,
            date_of_birth=date(2000, 1, 1),
            gender=Gender.OTHER,
            role=UserRole.ADMIN,
        )
        self.repo.create(admin)
        self.db.commit()
