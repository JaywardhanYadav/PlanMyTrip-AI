import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampMixin, UUIDBase

if TYPE_CHECKING:
    from .trip import Trip
    from .user import User


class TripThread(UUIDBase, TimestampMixin):
    __tablename__ = "trip_threads"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    langgraph_thread_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="thread",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="trip_threads",
    )
