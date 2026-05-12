from pydantic import BaseModel


class QueueStatus(BaseModel):
    active_users: int
    max_active_users: int
    has_access: bool
    notice: str | None = None
    session_expires_in: int | None = None
