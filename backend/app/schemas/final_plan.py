from pydantic import BaseModel, ConfigDict, Field


class DayActivityPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    day_number: int = Field(description="Sequential day number starting from 1.")
    day_theme: str = Field(description="Theme or focus region for the day.")
    morning: str = Field(description="Morning itinerary activities and visits.")
    afternoon: str = Field(description="Afternoon itinerary activities and lunch ideas.")
    evening: str = Field(description="Evening itinerary activities and dinner relaxation.")
    transport_mode: str = Field(description="Recommended local transport mode and advice.")
    stay_area: str = Field(description="Recommended neighborhood or hotel area to stay tonight.")


class FlightPlanItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    carrier: str = Field(description="Airline operating carrier name.")
    timing: str = Field(description="Departure and arrival timing window.")
    price_per_person_inr: float = Field(description="Indicative flight fare per traveler.")
    total_price_inr: float = Field(description="Total indicative flight fare for all travelers.")
    service_type: str = Field(description="Flight service window description.")


class HotelPlanItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Verified hotel name or chain brand.")
    location: str = Field(description="Hotel neighborhood and district.")
    nightly_rate_inr: float = Field(description="Indicative nightly rate in INR.")
    total_stay_inr: float = Field(description="Total stay cost for all nights in INR.")
    amenities: str = Field(description="Key amenities, features, and cancellation terms.")


class TierSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tier_name: str = Field(description="Name of the budget tier.")
    description: str = Field(description="Summary of the travel style.")
    flights_total_inr: float = Field(description="Total roundtrip flights cost.")
    accommodation_total_inr: float = Field(description="Total accommodation cost.")
    transit_total_inr: float = Field(description="Total local transit cost.")
    dining_total_inr: float = Field(description="Total dining and daily activities cost.")
    total_trip_inr: float = Field(description="Indicative average total cost for this tier.")
    notes: str = Field(default="", description="Summary notes.")


class CostBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    is_multi_tier: bool = Field(description="True if presenting multi-tier budget options.")
    budget_tier: TierSummary = Field(description="Budget tier summary.")
    mid_range_tier: TierSummary = Field(description="Mid-range tier summary.")
    luxury_tier: TierSummary = Field(description="Luxury tier summary.")
    recommended_tier_name: str = Field(description="Recommended tier for the user.")


class StructuredItinerary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    trip_title: str = Field(description="Engaging title for the trip itinerary.")
    dates_formatted: str = Field(description="Formatted travel dates range.")
    duration_label: str = Field(description="Trip duration label, e.g. '5 Days / 4 Nights'.")
    origin: str = Field(description="Departure city.")
    destination: str = Field(description="Destination city.")
    return_origin: str | None = Field(default=None, description="Return departure city.")
    gateway_note: str | None = Field(default=None, description="Internal gateway resolution notes.")
    flights: list[FlightPlanItem] = Field(description="Outbound flight options.")
    return_flights: list[FlightPlanItem] = Field(description="Return flight options.")
    hotels: list[HotelPlanItem] = Field(description="Handpicked hotel options.")
    day_plans: list[DayActivityPlan] = Field(description="Day-by-day activity plan for each day.")
    cost_breakdown: CostBreakdown = Field(description="Structured cost breakdown across tiers.")
    closing_note: str = Field(description="Warm concierge wishing note for their trip.")
