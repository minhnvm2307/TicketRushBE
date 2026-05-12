from pydantic import BaseModel


class QueueStatus(BaseModel):
    position: int
    total_users: int
    is_in_queue: bool
    has_access: bool
    can_checkout: bool = False
    access_expires_in: int | None = None
    checkout_expires_in: int | None = None
