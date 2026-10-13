from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class IntakeSupervisorEvaluation(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    intent: Literal["chit_chat", "off_topic", "travel_planning"] = Field(
        default="travel_planning",
        description="Classified user intent: chit_chat for greetings and pleasantries, off_topic for non-travel queries, travel_planning for vacations.",
    )
    departure_station: str | None = Field(
        default=None,
        description="Boarding or departure city (e.g. 'Mumbai', 'Delhi').",
    )
    destination: str | None = Field(
        default=None,
        description="Travel destination city or region (e.g. 'Goa', 'Jaipur', 'Rajasthan').",
    )
    destination_type: Literal["city", "state_region", "country"] = Field(
        default="city",
        description="Categorization of destination: city, state_region, or country.",
    )
    resolved_gateway: str | None = Field(
        default=None,
        description="Commercial gateway and IATA code if destination is a state or region (e.g. 'Jaipur (JAI)').",
    )
    route_circuits: list[str] = Field(
        default_factory=list,
        description="Proposed route circuits if destination is a state or region.",
    )
    gateway_note: str | None = Field(
        default=None,
        description="Explicit note explaining resolution of state/region to primary gateway hub.",
    )
    duration_days: int | None = Field(
        default=None,
        description="Total duration of the trip in days (e.g. 3, 5).",
    )
    trip_nights: int | None = Field(
        default=None,
        description="Calculated nights of stay as duration_days - 1.",
    )
    travelers_count: int | None = Field(
        default=None,
        description="Total number of people traveling (e.g. 1 for solo/alone, 2 for couple/partner/friend, 4 for family/group). Defaults to 1 if user indicates solo/alone.",
    )
    budget_inr: float | None = Field(
        default=None,
        description="Total estimated budget in Indian Rupees (INR) if specified by user.",
    )
    budget_tier: Literal["budget", "mid_range", "luxury", "unspecified"] = Field(
        default="unspecified",
        description="Classified budget tier: budget, mid_range, luxury, or unspecified.",
    )
    start_date: str | None = Field(
        default=None,
        description="Calculated or provided departure date in YYYY-MM-DD format.",
    )
    end_date: str | None = Field(
        default=None,
        description="Calculated return date in YYYY-MM-DD format as start_date + timedelta(days=duration_days - 1).",
    )
    relative_date_inferred: str | None = Field(
        default=None,
        description="Description of inferred relative date if user said 'next week', 'this weekend', etc.",
    )
    is_date_confirmed: bool = Field(
        default=False,
        description="True if user gave explicit calendar dates or confirmed an inferred date.",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of required fields still missing or requiring confirmation.",
    )
    is_complete: bool = Field(
        default=False,
        description="True if required parameters are present and confirmed, ready to invoke booking agents.",
    )
    next_question_or_confirmation: str | None = Field(
        default=None,
        description="Concise, friendly message acknowledging provided details and asking for missing fields or date confirmation.",
    )
