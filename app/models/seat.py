import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import SeatStatus


class SeatZone(Base):
    __tablename__ = "seat_zones"
    __table_args__ = (UniqueConstraint("event_id", "name", name="uq_event_zone_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    rows: Mapped[int]
    cols: Mapped[int]
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    capacity: Mapped[int]
    color: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="zones")
    seats = relationship("Seat", back_populates="zone", cascade="all, delete-orphan")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("zone_id", "row_index", "col_index", name="uq_zone_position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id: Mapped[str] = mapped_column(ForeignKey("seat_zones.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(30))
    row_index: Mapped[int]
    col_index: Mapped[int]
    status: Mapped[SeatStatus] = mapped_column(Enum(SeatStatus, name="seat_status_enum"), default=SeatStatus.AVAILABLE)
    locked_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    zone = relationship("SeatZone", back_populates="seats")
    ticket = relationship("Ticket", back_populates="seat", uselist=False)
