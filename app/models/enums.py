from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class EventStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class SeatStatus(StrEnum):
    AVAILABLE = "available"
    LOCKED = "locked"
    SOLD = "sold"


class TicketStatus(StrEnum):
    VALID = "valid"
    USED = "used"
    REFUNDED = "refunded"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class InteractionType(StrEnum):
    VIEW = "view"
    HOLD = "hold"
    PURCHASE = "purchase"
