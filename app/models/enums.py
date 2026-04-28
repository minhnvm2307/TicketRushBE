from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class EventStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CANCELLED = "CANCELLED"


class TicketType(StrEnum):
    FREE = "FREE"
    PAID = "PAID"


class SeatingType(StrEnum):
    ASSIGNED = "ASSIGNED"
    GENERAL_ADMISSION = "GENERAL_ADMISSION"


class ZoneType(StrEnum):
    ASSIGNED = "ASSIGNED"
    GENERAL_ADMISSION = "GENERAL_ADMISSION"


class SeatStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    SOLD = "SOLD"


class TicketStatus(StrEnum):
    VALID = "VALID"
    USED = "USED"
    REFUNDED = "REFUNDED"


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class InteractionType(StrEnum):
    VIEW = "VIEW"
    HOLD = "HOLD"
    PURCHASE = "PURCHASE"
