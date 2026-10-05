from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Protocol, TypeVar
from uuid import UUID

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import TypedDict

from .money import BudgetReconciliation, Money


class HasOptionId(Protocol):
    option_id: str


T = TypeVar("T", bound=HasOptionId)


def keyed_option_merge(
    existing: list[T] | None,
    incoming: list[T] | None,
) -> list[T]:
    if not existing:
        return list(incoming or [])

    if not incoming:
        return list(existing)

    indexed: dict[str, T] = {
        item.option_id: item
        for item in existing
    }

    for item in incoming:
        indexed[item.option_id] = item

    return list(indexed.values())


class FlightLeg(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    origin_iata: str = Field(
        min_length=3,
        max_length=3,
        description="IATA code (e.g. JFK).",
    )

    destination_iata: str = Field(
        min_length=3,
        max_length=3,
        description="IATA code (e.g. LHR).",
    )

    carrier_code: str = Field(
        min_length=2,
        max_length=3,
        description="Airline IATA (e.g. BA).",
    )

    flight_number: str = Field(
        description="Flight number string (e.g. '117')."
    )

    departure_time: datetime = Field(
        description="Timezone-aware departure timestamp."
    )

    arrival_time: datetime = Field(
        description="Timezone-aware arrival timestamp."
    )

    duration_minutes: int = Field(
        gt=0,
        description="Leg duration in minutes.",
    )

    @field_validator("departure_time", "arrival_time")
    @classmethod
    def assert_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                f"Datetime {value} must be timezone-aware."
            )

        return value


class FlightOption(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    option_id: str = Field(
        description="Stable deterministic hash of legs and route."
    )

    carrier: str = Field(
        description="Marketing carrier name (e.g. 'British Airways')."
    )

    legs: list[FlightLeg] = Field(min_length=1)

    fare: Money = Field(
        description="Auditable Decimal fare and currency."
    )

    is_estimate: bool = Field(
        default=True,
        description="True if price is benchmarked from web search rather than live GDS booking offer.",
    )

    source_provenance: Literal[
        "aviationstack",
        "tavily",
        "cached",
    ]

    source_citation: str | None = Field(
        default=None,
        description="Grounding URL from search results validating the indicative price.",
    )

    raw_payload_id: UUID | None = Field(
        default=None,
        description="Foreign key pointer to app.raw_payload table in PostgreSQL.",
    )


class HotelOption(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    option_id: str = Field(
        description="Deterministic hash of property name and location."
    )

    name: str = Field(
        description="Property name."
    )

    location: str = Field(
        description="Neighborhood or physical address."
    )

    nightly_rate: Money = Field(
        description="Base nightly room rate."
    )

    total_rate: Money = Field(
        description="Total stay cost including nights multiplier."
    )

    cancellation_terms: str = Field(
        description="Summary of refund/cancellation rules."
    )

    source_provenance: Literal[
        "tavily",
        "cached",
    ]

    source_citation: str | None = Field(
        default=None
    )

    raw_payload_id: UUID | None = Field(
        default=None
    )


class ActivityOption(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    option_id: str = Field(
        description="Deterministic hash of title and timing."
    )

    title: str = Field(
        description="Activity name."
    )

    location: str = Field(
        description="Address or venue coordinates."
    )

    timing: datetime = Field(
        description="Timezone-aware start timestamp."
    )

    duration_minutes: int = Field(
        gt=0
    )

    cost: Money = Field(
        description="Per-person cost (zero if free)."
    )

    is_free: bool = Field(
        default=False
    )

    weather_sensitive: bool = Field(
        description="True if rainy/stormy weather makes this activity unviable."
    )

    source_provenance: Literal[
        "tavily",
        "cached",
    ]

    source_citation: str | None = Field(
        default=None
    )

    raw_payload_id: UUID | None = Field(
        default=None
    )

    @field_validator("timing")
    @classmethod
    def assert_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                f"Activity timing {value} must be timezone-aware."
            )

        return value


class WeatherOutlook(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    destination: str
    target_date: date

    source: Literal[
        "forecast",
        "climate_normal",
    ]

    temp_high_celsius: Decimal = Field(
        decimal_places=1
    )

    temp_low_celsius: Decimal = Field(
        decimal_places=1
    )

    condition: str = Field(
        description="e.g. 'Partly Cloudy', 'Rain showers'."
    )

    precipitation_probability: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        decimal_places=2,
        description="Probability between 0.00 and 1.00.",
    )


def weather_merge_reducer(
    existing: list[WeatherOutlook] | None,
    incoming: list[WeatherOutlook] | None,
) -> list[WeatherOutlook]:

    if not existing:
        return list(incoming or [])

    if not incoming:
        return list(existing)

    indexed = {
        (weather.destination, weather.target_date): weather
        for weather in existing
    }

    for weather in incoming:
        indexed[
            (weather.destination, weather.target_date)
        ] = weather

    return list(indexed.values())


class GuardrailVerdict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    allowed: bool = Field(
        description="True if prompt/plan passes all security policies."
    )

    category: Literal[
        "clean",
        "injection",
        "off_topic",
        "budget_unviable",
        "pii",
    ]

    confidence: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        decimal_places=2,
        description="Confidence score between 0.00 and 1.00.",
    )

    reason: str = Field(
        description="Human-readable explanation of rejection or warning."
    )

    is_retryable: bool = Field(
        description="True if user can adjust prompt (e.g. raise budget) and retry."
    )


class PlanMyTripState(TypedDict, total=False):
    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    guardrail_verdict: GuardrailVerdict | None

    trip_budget: Money | None

    budget_reconciliation: BudgetReconciliation | None

    flight_options: Annotated[
        list[FlightOption],
        keyed_option_merge,
    ]

    hotel_options: Annotated[
        list[HotelOption],
        keyed_option_merge,
    ]

    activity_options: Annotated[
        list[ActivityOption],
        keyed_option_merge,
    ]

    weather_outlook: Annotated[
        list[WeatherOutlook],
        weather_merge_reducer,
    ]

    selected_flight_id: str | None
    selected_hotel_id: str | None
    selected_activity_ids: list[str]

    departure_station: str | None
    destination: str | None
    start_date: str | None
    end_date: str | None

    itinerary_draft: str | None
    human_feedback: dict[str, object] | None
    next_step: str | None


