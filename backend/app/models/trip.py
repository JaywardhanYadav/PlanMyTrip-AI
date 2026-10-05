import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampMixin, UUIDBase

if TYPE_CHECKING:
    from .chat_message import ChatMessage
    from .conversation_intake import ConversationIntake
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
    departure_station: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Delhi (DEL)",
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
        default=Decimal("200000.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
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
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    intake: Mapped["ConversationIntake | None"] = relationship(
        "ConversationIntake",
        back_populates="trip",
        uselist=False,
        cascade="all, delete-orphan",
    )

