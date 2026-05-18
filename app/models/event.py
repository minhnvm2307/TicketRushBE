import uuid
from datetime import datetime
import numpy as np
from pgvector.sqlalchemy import Vector

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import EventStatus, SeatingType, TicketType


event_categories = Table(
    "event_categories",
    Base.metadata,
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "category_id",
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    short_description: Mapped[str] = mapped_column(String(500), default="")
    embedding: Mapped[np.ndarray] = mapped_column(Vector(384))
    is_private: Mapped[bool] = mapped_column(default=False)
    theme: Mapped[str] = mapped_column(String(50), default="minimal")
    venue: Mapped[str] = mapped_column(String(255))
    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus, name="event_status_enum"), default=EventStatus.DRAFT)
    ticket_type: Mapped[TicketType] = mapped_column(
        Enum(TicketType, name="ticket_type_enum"),
        default=TicketType.PAID,
    )
    seating_type: Mapped[SeatingType] = mapped_column(
        Enum(SeatingType, name="seating_type_enum"),
        default=SeatingType.ASSIGNED,
    )
    max_capacity: Mapped[int | None]
    seat_map_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seat_map_cols: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    zones = relationship("SeatZone", back_populates="event", cascade="all, delete-orphan")
    categories = relationship("Category", secondary=event_categories, lazy="selectin")
    order_items = relationship("OrderItem", back_populates="event")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_category_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
