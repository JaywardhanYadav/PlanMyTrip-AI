from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from ..core.money import Money
from ..core.state import FlightOption, HotelOption

CENT = Decimal("0.01")


class TierCostBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tier_name: str = Field(description="Name of the budget tier: Budget, Mid-Range, or Luxury.")
    description: str = Field(description="Description of the tier travel style.")
    hotel_tier_name: str = Field(description="Accommodation tier name.")
    hotel_nightly_rate: Money = Field(description="Deterministic nightly hotel rate.")
    total_hotel_cost: Money = Field(description="Nightly hotel rate times nights.")
    flights_per_person_roundtrip: Money = Field(description="Roundtrip flight rate per traveler.")
    total_flights_cost: Money = Field(description="Roundtrip flight rate times travelers count.")
    daily_transit_cost: Money = Field(description="Daily local transit cost.")
    total_transit_cost: Money = Field(description="Daily transit cost times trip days.")
    daily_dining_cost: Money = Field(description="Daily dining and activity cost per traveler.")
    total_dining_cost: Money = Field(description="Daily dining times days times travelers.")
    total_trip_cost: Money = Field(description="Deterministic total cost for this tier.")


class MultiTierTripBudget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    budget_tier_specified: Literal["budget", "mid_range", "luxury", "unspecified"]
    travelers_count: int
    duration_days: int
    duration_nights: int
    budget_tier: TierCostBreakdown
    mid_range_tier: TierCostBreakdown
    luxury_tier: TierCostBreakdown
    recommended_tier: TierCostBreakdown


def compute_tier_breakdown(
    tier_name: str,
    description: str,
    hotel_tier_name: str,
    default_nightly: Decimal,
    default_flight_per_person: Decimal,
    default_daily_transit: Decimal,
    default_daily_dining: Decimal,
    travelers_count: int,
    duration_days: int,
    duration_nights: int,
    matched_hotel_nightly: Decimal | None = None,
    matched_flight_roundtrip: Decimal | None = None,
) -> TierCostBreakdown:
    nightly = (matched_hotel_nightly or default_nightly).quantize(CENT, rounding=ROUND_HALF_UP)
    total_hotel = (nightly * Decimal(duration_nights)).quantize(CENT, rounding=ROUND_HALF_UP)

    flight_roundtrip = (matched_flight_roundtrip or default_flight_per_person).quantize(CENT, rounding=ROUND_HALF_UP)
    total_flights = (flight_roundtrip * Decimal(travelers_count)).quantize(CENT, rounding=ROUND_HALF_UP)

    daily_transit = default_daily_transit.quantize(CENT, rounding=ROUND_HALF_UP)
    total_transit = (daily_transit * Decimal(duration_days)).quantize(CENT, rounding=ROUND_HALF_UP)

    daily_dining = default_daily_dining.quantize(CENT, rounding=ROUND_HALF_UP)
    total_dining = (daily_dining * Decimal(duration_days) * Decimal(travelers_count)).quantize(CENT, rounding=ROUND_HALF_UP)

    total_trip = (total_flights + total_hotel + total_transit + total_dining).quantize(CENT, rounding=ROUND_HALF_UP)

    return TierCostBreakdown(
        tier_name=tier_name,
        description=description,
        hotel_tier_name=hotel_tier_name,
        hotel_nightly_rate=Money(amount=nightly, currency="INR"),
        total_hotel_cost=Money(amount=total_hotel, currency="INR"),
        flights_per_person_roundtrip=Money(amount=flight_roundtrip, currency="INR"),
        total_flights_cost=Money(amount=total_flights, currency="INR"),
        daily_transit_cost=Money(amount=daily_transit, currency="INR"),
        total_transit_cost=Money(amount=total_transit, currency="INR"),
        daily_dining_cost=Money(amount=daily_dining, currency="INR"),
        total_dining_cost=Money(amount=total_dining, currency="INR"),
        total_trip_cost=Money(amount=total_trip, currency="INR"),
    )


def reconcile_multi_tier_budget(
    budget_tier: Literal["budget", "mid_range", "luxury", "unspecified"] = "unspecified",
    travelers_count: int = 1,
    duration_days: int = 3,
    duration_nights: int | None = None,
    flight_options: list[FlightOption] | None = None,
    return_flight_options: list[FlightOption] | None = None,
    hotel_options: list[HotelOption] | None = None,
) -> MultiTierTripBudget:
    travelers = max(1, travelers_count)
    days = max(1, duration_days)
    nights = duration_nights if duration_nights is not None and duration_nights >= 0 else max(1, days - 1)

    matched_budget_hotel: Decimal | None = None
    matched_mid_hotel: Decimal | None = None
    matched_lux_hotel: Decimal | None = None

    if hotel_options:
        for h in hotel_options:
            amt = h.nightly_rate.amount
            if amt <= Decimal("4500.00") and matched_budget_hotel is None:
                matched_budget_hotel = amt
            elif amt <= Decimal("10000.00") and matched_mid_hotel is None:
                matched_mid_hotel = amt
            elif amt > Decimal("10000.00") and matched_lux_hotel is None:
                matched_lux_hotel = amt

    budget_flight_roundtrip: Decimal | None = None
    mid_flight_roundtrip: Decimal | None = None
    lux_flight_roundtrip: Decimal | None = None

    if flight_options:
        out_fares = sorted([f.fare.amount / Decimal(travelers) for f in flight_options])
        ret_fares = sorted([rf.fare.amount / Decimal(travelers) for rf in return_flight_options]) if return_flight_options else out_fares

        budget_out = out_fares[0]
        budget_ret = ret_fares[0]
        budget_flight_roundtrip = (budget_out + budget_ret).quantize(CENT, rounding=ROUND_HALF_UP)

        mid_out_idx = min(1, len(out_fares) - 1)
        mid_ret_idx = min(1, len(ret_fares) - 1)
        mid_flight_roundtrip = (out_fares[mid_out_idx] + ret_fares[mid_ret_idx]).quantize(CENT, rounding=ROUND_HALF_UP)

        lux_out_idx = len(out_fares) - 1
        lux_ret_idx = len(ret_fares) - 1
        lux_flight_roundtrip = (out_fares[lux_out_idx] + ret_fares[lux_ret_idx]).quantize(CENT, rounding=ROUND_HALF_UP)

    budget_breakdown = compute_tier_breakdown(
        tier_name="Budget Tier",
        description="Smart 3-star stays, auto-rickshaws & app cabs, local dining and cafes",
        hotel_tier_name="3-Star & Smart Boutique Stay",
        default_nightly=Decimal("3200.00"),
        default_flight_per_person=Decimal("8000.00"),
        default_daily_transit=Decimal("800.00"),
        default_daily_dining=Decimal("700.00"),
        travelers_count=travelers,
        duration_days=days,
        duration_nights=nights,
        matched_hotel_nightly=matched_budget_hotel,
        matched_flight_roundtrip=budget_flight_roundtrip,
    )

    mid_breakdown = compute_tier_breakdown(
        tier_name="Mid-Range Tier",
        description="4-star comfort / boutique resorts, private chauffeur cab, casual restaurants",
        hotel_tier_name="4-Star Comfort & Boutique Resort",
        default_nightly=Decimal("6200.00"),
        default_flight_per_person=Decimal("10000.00"),
        default_daily_transit=Decimal("2500.00"),
        default_daily_dining=Decimal("1500.00"),
        travelers_count=travelers,
        duration_days=days,
        duration_nights=nights,
        matched_hotel_nightly=matched_mid_hotel,
        matched_flight_roundtrip=mid_flight_roundtrip,
    )

    lux_breakdown = compute_tier_breakdown(
        tier_name="Luxury Tier",
        description="5-star heritage palaces / luxury suites, private luxury transfers, fine dining",
        hotel_tier_name="5-Star Heritage Palace & Luxury Suites",
        default_nightly=Decimal("18500.00"),
        default_flight_per_person=Decimal("14500.00"),
        default_daily_transit=Decimal("5000.00"),
        default_daily_dining=Decimal("3500.00"),
        travelers_count=travelers,
        duration_days=days,
        duration_nights=nights,
        matched_hotel_nightly=matched_lux_hotel,
        matched_flight_roundtrip=lux_flight_roundtrip,
    )

    if budget_tier == "budget":
        recommended = budget_breakdown
    elif budget_tier == "luxury":
        recommended = lux_breakdown
    else:
        recommended = mid_breakdown

    return MultiTierTripBudget(
        budget_tier_specified=budget_tier,
        travelers_count=travelers,
        duration_days=days,
        duration_nights=nights,
        budget_tier=budget_breakdown,
        mid_range_tier=mid_breakdown,
        luxury_tier=lux_breakdown,
        recommended_tier=recommended,
    )
