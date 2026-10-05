from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampMixin, UUIDBase

if TYPE_CHECKING:
    from .audit_log import AuditLog
    from .trip import Trip
    from .trip_thread import TripThread


class User(UUIDBase, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    trip_threads: Mapped[list["TripThread"]] = relationship(
        "TripThread",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
