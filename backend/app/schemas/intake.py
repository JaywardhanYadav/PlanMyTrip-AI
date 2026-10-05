from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class IntakeSupervisorEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    departure_station: str | None = Field(
        default=None,
        description="Boarding or departure city (e.g. 'Mumbai', 'Delhi').",
    )
    destination: str | None = Field(
        default=None,
        description="Travel destination city or region (e.g. 'Goa', 'Jaipur').",
    )
    duration_days: int | None = Field(
        default=None,
        description="Total duration of the trip in days (e.g. 3, 5).",
    )
    budget_inr: float | None = Field(
        default=None,
        description="Total estimated budget in Indian Rupees (INR).",
    )
    start_date: str | None = Field(
        default=None,
        description="Calculated or provided departure date in YYYY-MM-DD format.",
    )
    end_date: str | None = Field(
        default=None,
        description="Calculated return date in YYYY-MM-DD format if duration is known.",
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
        description="True if all 5 parameters are present and confirmed, ready to invoke booking agents.",
    )
    next_question_or_confirmation: str | None = Field(
        default=None,
        description="Concise, friendly message acknowledging provided details and asking for missing fields or date confirmation.",
    )
