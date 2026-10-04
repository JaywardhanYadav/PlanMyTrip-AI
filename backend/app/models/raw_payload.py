from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import TimestampMixin, UUIDBase


class RawPayload(UUIDBase, TimestampMixin):
    __tablename__ = "raw_payloads"

    option_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )
