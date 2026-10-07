import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from ..core.money import parse_indian_budget_decimal


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    departure_station: str = Field(default="", max_length=255)
    destination: str = Field(default="", max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    budget_total: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("budget_total", mode="before")
    @classmethod
    def parse_budget(cls, value: object) -> Decimal:
        if isinstance(value, (str, int, float, Decimal)):
            return parse_indian_budget_decimal(value)
        return Decimal("0.00")


class TripResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    departure_station: str
    destination: str
    start_date: date | None
    end_date: date | None
    budget_total: Decimal
    currency: str
    status: str
    created_at: datetime
    thread_id: str | None = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ConversationIntakeResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    departure_station: str
    destination: str
    start_date: date | None
    end_date: date | None
    budget_amount: Decimal
    currency: str
    created_at: datetime


class ConversationIntakeUpdate(BaseModel):
    departure_station: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: Decimal | None = None
    currency: str = "INR"

    @field_validator("budget_amount", mode="before")
    @classmethod
    def parse_budget_update(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, (str, int, float, Decimal)):
            return parse_indian_budget_decimal(value)
        return Decimal("200000.00")

