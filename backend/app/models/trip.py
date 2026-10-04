import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampMixin, UUIDBase

if TYPE_CHECKING:
    from .trip_thread import TripThread
    from .user import User


class Trip(UUIDBase, TimestampMixin):
    __tablename__ = "trips"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    destination: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    budget_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="planning",
        index=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="trips",
    )
    thread: Mapped["TripThread | None"] = relationship(
        "TripThread",
        back_populates="trip",
        uselist=False,
        cascade="all, delete-orphan",
    )
