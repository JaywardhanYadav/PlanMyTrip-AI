import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampMixin, UUIDBase

if TYPE_CHECKING:
    from .trip import Trip
    from .user import User


class ConversationIntake(UUIDBase, TimestampMixin):
    __tablename__ = "conversation_intakes"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    departure_station: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Delhi (DEL)",
    )
    destination: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    travelers_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    budget_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("200000.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="intake")
    user: Mapped["User"] = relationship("User")
