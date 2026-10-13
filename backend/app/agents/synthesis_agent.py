import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from langchain_core.messages import AIMessage
from pydantic import BaseModel, ConfigDict, Field
from ..core.config import get_openai_client, get_settings
from ..core.money import reconcile_trip_budget
from ..core.state import PlanMyTripState
from ..guardrails.output_guard import evaluate_output_guardrail
from ..services.budget_reconciler import MultiTierTripBudget, reconcile_multi_tier_budget
from ..services.circuit_planner import build_circuit_hub_schedule, sanitize_markdown_text


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


def render_itinerary_markdown(itinerary: StructuredItinerary, budget_data: MultiTierTripBudget) -> str:
    clean_origin = re.sub(r"\s*\([A-Z]{3}\)", "", itinerary.origin).strip()
    clean_dest = re.sub(r"\s*\([A-Z]{3}\)", "", itinerary.destination).strip()
    clean_ret_origin = re.sub(r"\s*\([A-Z]{3}\)", "", itinerary.return_origin or "").strip() or clean_dest

    parts: list[str] = []

    parts.append(f"**{itinerary.trip_title}**")
    parts.append(f"**Travel Dates:** {itinerary.dates_formatted} ({itinerary.duration_label})")
    if clean_ret_origin and clean_ret_origin.lower() != clean_dest.lower():
        parts.append(f"**Route:** {clean_origin} ➔ {clean_dest} (Return from {clean_ret_origin})")
    else:
        parts.append(f"**Route:** {clean_origin} ➔ {clean_dest}")
    parts.append("")
    parts.append("---")
    parts.append("")

    if itinerary.flights:
        parts.append(f"✈️ **Flight Options ({clean_origin} to {clean_dest}):**")
        for idx, f in enumerate(itinerary.flights, 1):
            parts.append(f"- **Option {idx}:** **{f.carrier}** ({f.service_type}) | Timings: {f.timing} | ₹{f.price_per_person_inr:,.0f} per person (Total: ₹{f.total_price_inr:,.0f} for {budget_data.travelers_count} travelers)")
        parts.append("")
        parts.append("---")
        parts.append("")

    if itinerary.hotels:
        parts.append("🏨 **Places to Stay (Hotels):**")
        for idx, h in enumerate(itinerary.hotels, 1):
            clean_loc = re.sub(r"\s*\([A-Z]{3}\)", "", h.location).strip()
            clean_hname = re.sub(r"\s*\([A-Z]{3}\)", "", h.name).strip()
            parts.append(f"- **Option {idx}:** **{clean_hname}** ({clean_loc}) | Nightly: ₹{h.nightly_rate_inr:,.0f} | Total Stay: ₹{h.total_stay_inr:,.0f} | {h.amenities}")
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append("📅 **Day-by-Day Plan:**")
    parts.append("")

    for plan in itinerary.day_plans:
        parts.append(f"**Day {plan.day_number}: {plan.day_theme}**")
        parts.append(f"🌅 **Morning:** {plan.morning}")
        parts.append(f"☀️ **Afternoon:** {plan.afternoon}")
        parts.append(f"🌆 **Evening:** {plan.evening}")
        parts.append(f"🚗 **Transport:** {plan.transport_mode}")
        parts.append(f"📍 **Stay Tonight:** {plan.stay_area}")
        parts.append("")
        parts.append("---")
        parts.append("")

    if itinerary.return_flights:
        parts.append(f"🛬 **Return Flights ({clean_ret_origin} to {clean_origin}):**")
        for idx, rf in enumerate(itinerary.return_flights, 1):
            parts.append(f"- **Return Option {idx}:** **{rf.carrier}** ({rf.service_type}) | Timings: {rf.timing} | ₹{rf.price_per_person_inr:,.0f} per person (Total: ₹{rf.total_price_inr:,.0f} for {budget_data.travelers_count} travelers)")
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append("💰 **Estimated Trip Cost:**")
    parts.append("")

    if budget_data.budget_tier_specified == "unspecified":
        parts.append("Here are realistic average cost estimates across 3 standard travel styles:")
        parts.append("")

        b_tier = budget_data.budget_tier
        parts.append("🏷️ **1. Budget (Economy):**")
        parts.append(f"- **Travel Style:** {b_tier.description}")
        parts.append(f"- **Roundtrip Flights:** ~{b_tier.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{b_tier.total_hotel_cost.to_formatted_str()} ({b_tier.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{b_tier.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{b_tier.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{b_tier.total_trip_cost.to_formatted_str()}")
        parts.append("")

        m_tier = budget_data.mid_range_tier
        parts.append("🏷️ **2. Mid-Range (Comfort):**")
        parts.append(f"- **Travel Style:** {m_tier.description}")
        parts.append(f"- **Roundtrip Flights:** ~{m_tier.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{m_tier.total_hotel_cost.to_formatted_str()} ({m_tier.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{m_tier.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{m_tier.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{m_tier.total_trip_cost.to_formatted_str()}")
        parts.append("")

        l_tier = budget_data.luxury_tier
        parts.append("🏷️ **3. Luxury (5-Star & Premium):**")
        parts.append(f"- **Travel Style:** {l_tier.description}")
        parts.append(f"- **Roundtrip Flights:** ~{l_tier.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{l_tier.total_hotel_cost.to_formatted_str()} ({l_tier.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{l_tier.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{l_tier.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{l_tier.total_trip_cost.to_formatted_str()}")
        parts.append("")
    else:
        rec = budget_data.recommended_tier
        parts.append(f"🏷️ **{rec.tier_name}:**")
        parts.append(f"- **Roundtrip Flights:** ~{rec.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{rec.total_hotel_cost.to_formatted_str()} ({rec.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{rec.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{rec.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{rec.total_trip_cost.to_formatted_str()}")
        parts.append("")

    parts.append("*Note: All figures are indicative average estimates in Indian Rupees (₹ INR). Actual booking costs may fluctuate based on seasonal demand and advance reservations.*")
    parts.append("")
    parts.append(f"*{itinerary.closing_note}*")

    return "\n".join(parts)


async def synthesis_agent_node(state: PlanMyTripState) -> dict[str, object]:
    flight_options = state.get("flight_options", [])
    return_flight_options = state.get("return_flight_options", [])
    hotel_options = state.get("hotel_options", [])
    places_info = state.get("places_data", {})
    activity_options = state.get("activity_options", [])

    travelers = state.get("travelers_count") or 1
    if travelers < 1:
        travelers = 1

    dep_station = state.get("departure_station") or "Pune"
    dest = state.get("destination") or "Gujarat"
    gateway_note = state.get("gateway_note")
    resolved_gateway = state.get("resolved_gateway")
    display_dest = dest or resolved_gateway
    clean_origin = re.sub(r"\s*\([A-Z]{3}\)", "", dep_station).strip()
    clean_dest = re.sub(r"\s*\([A-Z]{3}\)", "", display_dest).strip()
    start_d = state.get("start_date") or "2026-10-19"
    end_d = state.get("end_date") or "2026-10-23"

    total_days = state.get("duration_days")
    if not total_days:
        try:
            d_start = datetime.fromisoformat(str(start_d)).date()
            d_end = datetime.fromisoformat(str(end_d)).date()
            diff = (d_end - d_start).days
            if diff >= 0:
                total_days = diff + 1
        except Exception:
            pass
    if not total_days or total_days < 1:
        total_days = 5

    total_nights = state.get("trip_nights")
    if not total_nights or total_nights < 0:
        total_nights = max(1, total_days - 1)

    raw_tier = str(state.get("budget_tier") or "unspecified").lower()
    budget_tier_literal: Literal["budget", "mid_range", "luxury", "unspecified"]
    if raw_tier in ["budget", "mid_range", "luxury", "unspecified"]:
        budget_tier_literal = raw_tier  # type: ignore[assignment]
    else:
        budget_tier_literal = "unspecified"

    budget_data = reconcile_multi_tier_budget(
        budget_tier=budget_tier_literal,
        travelers_count=travelers,
        duration_days=total_days,
        duration_nights=total_nights,
        flight_options=flight_options,
        return_flight_options=return_flight_options,
        hotel_options=hotel_options,
    )

    flight_costs = [f.fare for f in flight_options[:1]] if flight_options else [budget_data.recommended_tier.total_flights_cost]
    hotel_costs = [h.total_rate for h in hotel_options[:1]] if hotel_options else [budget_data.recommended_tier.total_hotel_cost]
    activity_costs = [a.cost for a in activity_options[:2]] if activity_options else [budget_data.recommended_tier.total_transit_cost]
    trip_budget = state.get("trip_budget") or budget_data.recommended_tier.total_trip_cost

    budget_result = reconcile_trip_budget(
        total_cap=trip_budget,
        flight_costs=flight_costs,
        hotel_costs=hotel_costs,
        activity_costs=activity_costs,
    )

    flight_items: list[FlightPlanItem] = []
    for fo in flight_options[:3]:
        leg = fo.legs[0] if fo.legs else None
        dep_t = leg.departure_time.strftime("%I:%M %p") if leg else "07:15 AM"
        arr_t = leg.arrival_time.strftime("%I:%M %p") if leg else "08:35 AM"
        fl_label = leg.flight_number if leg and leg.flight_number else "Scheduled Service"
        p_head = float(fo.fare.amount / Decimal(travelers))
        flight_items.append(
            FlightPlanItem(
                carrier=fo.carrier,
                timing=f"Dep: {dep_t} ➔ Arr: {arr_t}",
                price_per_person_inr=p_head,
                total_price_inr=float(fo.fare.amount),
                service_type=fl_label,
            )
        )

    ret_items: list[FlightPlanItem] = []
    for rfo in return_flight_options[:2]:
        leg = rfo.legs[0] if rfo.legs else None
        dep_t = leg.departure_time.strftime("%I:%M %p") if leg else "02:30 PM"
        arr_t = leg.arrival_time.strftime("%I:%M %p") if leg else "03:55 PM"
        fl_label = leg.flight_number if leg and leg.flight_number else "Scheduled Service"
        p_head = float(rfo.fare.amount / Decimal(travelers))
        ret_items.append(
            FlightPlanItem(
                carrier=rfo.carrier,
                timing=f"Dep: {dep_t} ➔ Arr: {arr_t}",
                price_per_person_inr=p_head,
                total_price_inr=float(rfo.fare.amount),
                service_type=fl_label,
            )
        )

    hotel_items: list[HotelPlanItem] = []
    for ho in hotel_options[:3]:
        clean_loc = re.sub(r"\s*\([A-Z]{3}\)", "", ho.location).strip()
        clean_hname = re.sub(r"\s*\([A-Z]{3}\)", "", ho.name).strip()
        hotel_items.append(
            HotelPlanItem(
                name=clean_hname,
                location=clean_loc,
                nightly_rate_inr=float(ho.nightly_rate.amount),
                total_stay_inr=float(ho.total_rate.amount),
                amenities=ho.cancellation_terms,
            )
        )

    b_t = budget_data.budget_tier
    m_t = budget_data.mid_range_tier
    l_t = budget_data.luxury_tier
    cost_breakdown_obj = CostBreakdown(
        is_multi_tier=budget_data.budget_tier_specified == "unspecified",
        budget_tier=TierSummary(
            tier_name=b_t.tier_name,
            description=b_t.description,
            flights_total_inr=float(b_t.total_flights_cost.amount),
            accommodation_total_inr=float(b_t.total_hotel_cost.amount),
            transit_total_inr=float(b_t.total_transit_cost.amount),
            dining_total_inr=float(b_t.total_dining_cost.amount),
            total_trip_inr=float(b_t.total_trip_cost.amount),
            notes="Smart budget tier.",
        ),
        mid_range_tier=TierSummary(
            tier_name=m_t.tier_name,
            description=m_t.description,
            flights_total_inr=float(m_t.total_flights_cost.amount),
            accommodation_total_inr=float(m_t.total_hotel_cost.amount),
            transit_total_inr=float(m_t.total_transit_cost.amount),
            dining_total_inr=float(m_t.total_dining_cost.amount),
            total_trip_inr=float(m_t.total_trip_cost.amount),
            notes="Comfort boutique tier.",
        ),
        luxury_tier=TierSummary(
            tier_name=l_t.tier_name,
            description=l_t.description,
            flights_total_inr=float(l_t.total_flights_cost.amount),
            accommodation_total_inr=float(l_t.total_hotel_cost.amount),
            transit_total_inr=float(l_t.total_transit_cost.amount),
            dining_total_inr=float(l_t.total_dining_cost.amount),
            total_trip_inr=float(l_t.total_trip_cost.amount),
            notes="5-star luxury heritage tier.",
        ),
        recommended_tier_name=budget_data.recommended_tier.tier_name,
    )

    flight_text_summary = "\n".join([f"- {f.carrier} ({f.service_type}) | {f.timing} | ₹{f.price_per_person_inr:,.0f}/person" for f in flight_items])
    hotel_text_summary = "\n".join([f"- {h.name} ({h.location}) | ₹{h.nightly_rate_inr:,.0f}/night" for h in hotel_items])

    zones_list: list[dict[str, Any]] = []
    stay_strategy_text = "Stay centrally to optimize daily transit."
    transit_guide_dict: dict[str, Any] = {}
    if isinstance(places_info, dict):
        tg = places_info.get("transit_guide")
        if isinstance(tg, dict):
            transit_guide_dict = tg
        zn = places_info.get("zones")
        if isinstance(zn, list):
            zones_list = [z for z in zn if isinstance(z, dict)]
        st = places_info.get("stay_strategy")
        if st:
            stay_strategy_text = str(st)

    places_summary_text = ""
    for z in zones_list:
        z_name = z.get("zone_name", "Scenic Zone")
        z_places = z.get("places", [])
        z_stay = z.get("recommended_stay_area", "Central")
        places_summary_text += f"\n- {z_name}: " + ", ".join([str(p) for p in z_places]) + f" (Stay in: {z_stay})"

    easiest_transit = str(transit_guide_dict.get("easiest_way", "App cabs or dedicated chauffeur vehicle."))
    taxi_guidance = str(transit_guide_dict.get("taxi_guidance", "Airport prepaid taxi or app cabs readily available."))

    client = get_openai_client()
    settings = get_settings()

    day_reqs = "\n".join([f"- Day {i}: Full individual plan for Day {i}" for i in range(1, total_days + 1)])

    system_prompt = (
        f"You are the senior synthesis agent for PlanMyTrip AI. You are generating a complete {total_days}-Day day-by-day travel itinerary.\n"
        f"CRITICAL REQUIREMENT: You MUST generate exactly {total_days} DayActivityPlan objects in day_plans (Day 1 through Day {total_days}).\n"
        f"It is strictly forbidden to output fewer than {total_days} days. Do not truncate after Day 1."
    )

    user_prompt = (
        f"Trip Specs:\n"
        f"- Origin: {clean_origin}\n"
        f"- Destination: {clean_dest}\n"
        f"- Travelers: {travelers}\n"
        f"- Duration: {total_days} Days / {total_nights} Nights\n"
        f"- Dates: {start_d} to {end_d}\n"
        f"- Budget Tier: {budget_tier_literal}\n\n"
        f"Available Flights from Origin ({clean_origin} ➔ {clean_dest}):\n{flight_text_summary}\n\n"
        f"Available Accommodation in {clean_dest}:\n{hotel_text_summary}\n\n"
        f"Key Sights & Zones in {clean_dest}:\n"
        f"{places_summary_text or '- Historic UNESCO landmarks, cultural heritage, and local artisan markets.'}\n\n"
        f"Transit Guidance: {easiest_transit}. {taxi_guidance}\n"
        f"Stay Strategy: {stay_strategy_text}\n\n"
        f"MANDATORY REQUIREMENT:\n"
        f"You MUST generate exactly {total_days} items in the day_plans list:\n"
        f"{day_reqs}\n"
        f"Make sure every day has rich morning, afternoon, evening activities, transport_mode, and stay_area."
    )

    parsed_itinerary: StructuredItinerary | None = None
    try:
        completion = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_WORKER,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=StructuredItinerary,
            temperature=0.2,
        )
        parsed_itinerary = completion.choices[0].message.parsed
    except Exception:
        pass

    target_stay = state.get("target_stay_neighborhood") or "Central District"

    raw_plans: list[DayActivityPlan] = []
    if parsed_itinerary is not None:
        raw_plans = list(parsed_itinerary.day_plans)
    day_map = {p.day_number: p for p in raw_plans}

    hub_schedule = build_circuit_hub_schedule(
        destination=f"{dest} {clean_dest}",
        duration_days=total_days,
        target_stay_neighborhood=target_stay,
        route_circuits=state.get("route_circuits"),
        destination_type=state.get("destination_type"),
    )

    final_day_plans: list[DayActivityPlan] = []
    for d_num in range(1, total_days + 1):
        hub_item = hub_schedule[d_num - 1] if d_num <= len(hub_schedule) else None
        stay_note = hub_item.stay_area if hub_item else (f"{target_stay}, {clean_dest}" if d_num == 1 else f"Your hotel in {target_stay}, {clean_dest} (Luggage stays in room - no hotel change needed)")

        if d_num in day_map:
            p = day_map[d_num]
            trans_mode = p.transport_mode
            day_theme = p.day_theme
            morning = p.morning
            afternoon = p.afternoon
            evening = p.evening

            if hub_item and hub_item.city:
                if hub_item.city.lower() in ["jodhpur", "udaipur", "munnar", "thekkady", "alleppey"]:
                    day_theme = hub_item.day_theme
                    morning = hub_item.morning
                    afternoon = hub_item.afternoon
                    evening = hub_item.evening
                elif d_num == total_days:
                    day_theme = hub_item.day_theme
                    morning = hub_item.morning
                    afternoon = hub_item.afternoon
                    evening = hub_item.evening

            if hub_item and hub_item.is_city_transition and d_num > 1 and d_num < total_days:
                trans_mode = f"Private chauffeur inter-city vehicle transfer to {hub_item.city}. ({hub_item.luggage_instruction})"
            elif hub_item and not hub_item.is_city_transition:
                trans_mode = f"{p.transport_mode} (Same-city stay: {hub_item.luggage_instruction})"
            elif hub_item and hub_item.special_stay == "houseboat":
                trans_mode = "Private chauffeur transfer to Alleppey boat jetty; private luxury houseboat cruise & overnight stay."

            final_day_plans.append(
                DayActivityPlan(
                    day_number=d_num,
                    day_theme=day_theme,
                    morning=morning,
                    afternoon=afternoon,
                    evening=evening,
                    transport_mode=trans_mode,
                    stay_area=stay_note,
                )
            )
        else:
            if d_num == 1:
                final_day_plans.append(
                    DayActivityPlan(
                        day_number=1,
                        day_theme="Arrival, Check-in & Scenic Relaxation",
                        morning=f"Arrival in {clean_dest}, private airport cab transfer to hotel.",
                        afternoon="Hotel check-in, unpack, freshen up, and enjoy a relaxed local lunch.",
                        evening="Leisurely stroll through local promenade or hotel lounge followed by dinner.",
                        transport_mode="Prepaid airport cab or app cab directly to hotel.",
                        stay_area=stay_note,
                    )
                )
            elif d_num == total_days:
                final_day_plans.append(
                    DayActivityPlan(
                        day_number=d_num,
                        day_theme=hub_item.day_theme if hub_item else "Morning Bazaars, Wrap-Up & Return Journey",
                        morning=hub_item.morning if hub_item else "Leisurely breakfast, check-out, and final souvenir shopping at local markets.",
                        afternoon=hub_item.afternoon if hub_item else "Lunch at a renowned cafe followed by cab transfer to airport departure terminal.",
                        evening=hub_item.evening if hub_item else f"Board scheduled evening return flight back to {clean_origin}.",
                        transport_mode="Hired cab to airport departure terminal.",
                        stay_area=stay_note,
                    )
                )
            else:
                z_idx = (d_num - 2) % len(zones_list) if zones_list else 0
                curr_zone = zones_list[z_idx] if zones_list else {}
                z_name = curr_zone.get("zone_name", f"Scenic & Cultural Highlights (Part {d_num - 1})")
                z_places = curr_zone.get("places", [f"Explore top landmarks and scenic sights of {clean_dest}"])
                p_str = ", ".join([str(p) for p in z_places[:3]])
                hub_city = hub_item.city if hub_item else clean_dest
                trans_mode = f"Private chauffeur cab for sightseeing and transfers. ({hub_item.luggage_instruction})" if hub_item else "Dedicated chauffeur cab."
                final_day_plans.append(
                    DayActivityPlan(
                        day_number=d_num,
                        day_theme=hub_item.day_theme if hub_item else z_name,
                        morning=hub_item.morning if hub_item else f"Morning visit to top landmarks and heritage sites in {hub_city}: {p_str}.",
                        afternoon=hub_item.afternoon if hub_item else "Relish authentic regional cuisine and local delicacies for lunch.",
                        evening=hub_item.evening if hub_item else "Sunset viewing, vibrant evening promenades, and dinner at a top restaurant.",
                        transport_mode=trans_mode,
                        stay_area=stay_note,
                    )
                )

    final_day_plans.sort(key=lambda x: x.day_number)

    trip_title = f"Your Tour Plan for {clean_dest}"

    if "RAJASTHAN" in dest.upper():
        closing_note = "Wishing you a royal and unforgettable vacation across Rajasthan!"
    elif "KERALA" in dest.upper():
        closing_note = "Wishing you a serene and rejuvenating vacation across God's Own Country, Kerala!"
    elif parsed_itinerary and parsed_itinerary.closing_note:
        closing_note = parsed_itinerary.closing_note
    else:
        closing_note = f"Wishing you an unforgettable, serene vacation in {clean_dest}!"

    structured_itinerary = StructuredItinerary(
        trip_title=trip_title,
        dates_formatted=f"{start_d} to {end_d}",
        duration_label=f"{total_days} Days / {total_nights} Nights",
        origin=clean_origin,
        destination=clean_dest,
        return_origin=state.get("return_gateway") or None,
        gateway_note=None,
        flights=flight_items,
        return_flights=ret_items,
        hotels=hotel_items,
        day_plans=final_day_plans,
        cost_breakdown=cost_breakdown_obj,
        closing_note=closing_note,
    )

    rendered_markdown = sanitize_markdown_text(render_itinerary_markdown(structured_itinerary, budget_data))

    verdict = evaluate_output_guardrail(rendered_markdown)
    if not verdict.allowed:
        rendered_markdown = "Itinerary output failed safety evaluation. Please review requirements and try again."

    return {
        "budget_reconciliation": budget_result,
        "itinerary_draft": rendered_markdown,
        "messages": [AIMessage(content=rendered_markdown)],
        "next_step": "complete",
    }
