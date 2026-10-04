import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from ..core.money import parse_indian_budget_decimal


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    budget_total: Decimal = Field(default=Decimal("200000.00"), ge=Decimal("0.00"))
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("budget_total", mode="before")
    @classmethod
    def parse_budget(cls, value: object) -> Decimal:
        if isinstance(value, (str, int, float, Decimal)):
            return parse_indian_budget_decimal(value)
        return Decimal("200000.00")



class TripResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    destination: str
    start_date: date | None
    end_date: date | None
    budget_total: Decimal
    currency: str
    status: str
    created_at: datetime
    thread_id: str | None = None
