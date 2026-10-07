from decimal import Decimal
from typing import Any
from langchain_core.messages import AIMessage
from ..core.config import get_openai_client, get_settings
from ..core.money import Money, reconcile_trip_budget
from ..core.state import PlanMyTripState
from ..guardrails.output_guard import evaluate_output_guardrail


async def synthesis_agent_node(state: PlanMyTripState) -> dict[str, object]:
    flight_options = state.get("flight_options", [])
    return_flight_options = state.get("return_flight_options", [])
    hotel_options = state.get("hotel_options", [])
    places_info = state.get("places_data", {})
    activity_options = state.get("activity_options", [])
    travelers = state.get("travelers_count") or 1
    if travelers < 1:
        travelers = 1

    selected_flight_id = state.get("selected_flight_id")
    selected_flights = [f for f in flight_options if f.option_id == selected_flight_id]
    if not selected_flights and flight_options:
        selected_flights = [flight_options[0]]
    flight_costs = [f.fare for f in selected_flights]

    selected_hotel_id = state.get("selected_hotel_id")
    selected_hotels = [h for h in hotel_options if h.option_id == selected_hotel_id]
    if not selected_hotels and hotel_options:
        selected_hotels = [hotel_options[0]]
    hotel_costs = [h.total_rate for h in selected_hotels]

    selected_act_ids = set(state.get("selected_activity_ids", []))
    selected_activities = [a for a in activity_options if a.option_id in selected_act_ids]
    if not selected_activities and activity_options:
        selected_activities = activity_options[:2]
    activity_costs = [a.cost for a in selected_activities]

    trip_budget = state.get("trip_budget")
    if trip_budget and isinstance(trip_budget, Money):
        total_cap = trip_budget
    else:
        total_cap = Money(amount=Decimal("150000.00"), currency="INR")

    budget_result = reconcile_trip_budget(
        total_cap=total_cap,
        flight_costs=flight_costs,
        hotel_costs=hotel_costs,
        activity_costs=activity_costs,
    )

    dep_station = state.get("departure_station") or "Pune"
    dest = state.get("destination") or "Goa"
    start_d = state.get("start_date") or "2026-12-01"
    end_d = state.get("end_date") or "2026-12-04"

    outbound_flights_text = ""
    for idx, f in enumerate(flight_options, 1):
        leg = f.legs[0] if f.legs else None
        dep_str = leg.departure_time.strftime("%I:%M %p") if leg else "Morning"
        arr_str = leg.arrival_time.strftime("%I:%M %p") if leg else "Afternoon"
        dur = leg.duration_minutes if leg else 75
        fl_no = f"{leg.carrier_code}-{leg.flight_number}" if leg else "Non-stop"
        per_person = (f.fare.amount / Decimal(str(travelers))).quantize(Decimal("1"))
        outbound_flights_text += (
            f"  * Option {idx}: **{f.carrier}** ({fl_no}) | Dep: {dep_str} ➔ Arr: {arr_str} ({dur}m) | "
            f"₹{per_person:,.0f} per person (Total: {f.fare.to_formatted_str()} for {travelers} traveler{'s' if travelers > 1 else ''})\n"
        )

    return_flights_text = ""
    for idx, f in enumerate(return_flight_options, 1):
        leg = f.legs[0] if f.legs else None
        dep_str = leg.departure_time.strftime("%I:%M %p") if leg else "Afternoon"
        arr_str = leg.arrival_time.strftime("%I:%M %p") if leg else "Evening"
        dur = leg.duration_minutes if leg else 75
        fl_no = f"{leg.carrier_code}-{leg.flight_number}" if leg else "Non-stop"
        per_person = (f.fare.amount / Decimal(str(travelers))).quantize(Decimal("1"))
        return_flights_text += (
            f"  * Return Option {idx}: **{f.carrier}** ({fl_no}) | Dep: {dep_str} ➔ Arr: {arr_str} ({dur}m) | "
            f"₹{per_person:,.0f} per person (Total: {f.fare.to_formatted_str()} for {travelers} traveler{'s' if travelers > 1 else ''})\n"
        )

    hotels_text = ""
    for idx, h in enumerate(hotel_options, 1):
        hotels_text += (
            f"  * Option {idx}: **{h.name}** ({h.location}) | "
            f"Nightly: {h.nightly_rate.to_formatted_str()} | Stay Total: {h.total_rate.to_formatted_str()} | "
            f"{h.cancellation_terms}\n"
        )

    transit_guide_dict: dict[str, Any] = {}
    zones_list: list[dict[str, Any]] = []
    stay_strategy_text = "Stay at your primary hotel to avoid repeated check-in hassle unless touring far regions."
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
        z_name = z.get("zone_name", "Local Zone")
        z_places = z.get("places", [])
        z_stay = z.get("recommended_stay_area", "Central")
        z_reason = z.get("stay_reason", "")
        places_summary_text += f"\n- **{z_name}**:\n"
        for p in z_places:
            places_summary_text += f"  * {p}\n"
        places_summary_text += f"  * *Stay in area*: {z_stay} ({z_reason})\n"

    easiest_transit = str(transit_guide_dict.get("easiest_way", "Self-drive rental or private day cab."))
    rental_car_rate = str(transit_guide_dict.get("car_rental_rate", "₹1,500/day"))
    rental_scooter_rate = str(transit_guide_dict.get("scooter_rental_rate", "₹400/day"))
    taxi_guidance = str(transit_guide_dict.get("taxi_guidance", "Prepaid taxis or app-based cabs readily available."))

    client = get_openai_client()
    settings = get_settings()

    prompt = (
        f"You are the Synthesis Agent for PlanMyTrip AI. You must construct a rich, highly practical, chronologically structured day-by-day travel plan for {travelers} traveler{'s' if travelers > 1 else ''}.\n\n"
        f"Trip Specs:\n"
        f"- Origin / Departure City: {dep_station}\n"
        f"- Destination: {dest}\n"
        f"- Number of Travelers: {travelers}\n"
        f"- Travel Dates: {start_d} to {end_d}\n"
        f"- Budget Cap: {budget_result.total_cap.to_formatted_str()} ({budget_result.total_cap.to_words()})\n\n"
        f"Data Gathered by Worker Agents:\n"
        f"AVAILABLE OUTBOUND FLIGHTS (Day 1):\n{outbound_flights_text or '  * Scheduled flights from ' + dep_station + ' to ' + dest}\n\n"
        f"AVAILABLE HOTELS TO STAY & REST:\n{hotels_text or '  * Handpicked hotels in ' + dest}\n\n"
        f"PLACES & ZONES TO VISIT:\n{places_summary_text}\n\n"
        f"TRANSIT & LOCAL TRAVEL GUIDANCE:\n"
        f"- Easiest way: {easiest_transit}\n"
        f"- Rental car rate: {rental_car_rate}\n"
        f"- Rental scooter/bike: {rental_scooter_rate}\n"
        f"- Taxi & cab guidance: {taxi_guidance}\n"
        f"- Stay strategy: {stay_strategy_text}\n\n"
        f"AVAILABLE RETURN FLIGHTS (Last Day):\n{return_flights_text or '  * Scheduled return flights to ' + dep_station}\n\n"
        f"MANDATORY FORMAT RULES:\n"
        f"You must strictly present the itinerary broken down into days:\n\n"
        f"### Day 1: Arrival, Transfers & Settling In\n"
        f"- **Available Outbound Flights ({dep_station} ➔ {dest})**: Show all options above with timings, airline, and prices (per person & total for {travelers}).\n"
        f"- **Airport Transfer**: Tell how to get from airport to hotel (e.g. prepaid taxi / app cab) with typical rate.\n"
        f"- **Available Hotels to Check-in & Rest**: List all available hotel options above with their nightly prices, total stay prices, location, and hotel amenities/activities (pool, spa, beach access, restaurant).\n"
        f"- **Evening Plan**: Unwind and relax at hotel or nearby beach/promenade.\n\n"
        f"### Day 2: Exploring Nearby Attractions & Smart Stay\n"
        f"- **Planned Sightseeing**: List places near the city/zone to visit.\n"
        f"- **How to Visit & Easiest Transport**: Detail rental cars, scooters, or Uber/cabs with daily rates so the traveler knows exactly how to travel.\n"
        f"- **Where to Stay Tonight**: Explain whether they should stay at the same Day 1 hotel (if places are nearby) or switch to a different hotel (if visiting a far-off area).\n\n"
        f"### Day 3 (or Final Day): Morning Wrap-Up & Return Journey\n"
        f"- **Morning Plan**: Hotel check-out, local breakfast/souvenirs.\n"
        f"- **Airport Transfer**: Easiest cab back to airport.\n"
        f"- **Available Return Flights ({dest} ➔ {dep_station})**: Show all return flight options with timings, airline, and prices.\n\n"
        f"### 💰 Budget & Cost Summary\n"
        f"- Clear financial breakdown for Flights, Hotels, Local Transit, and Activities in Indian Rupees (₹ INR).\n"
        f"- Compare against Budget Cap of {budget_result.total_cap.to_formatted_str()}.\n"
    )

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_WORKER,
            messages=[
                {"role": "system", "content": "You are a professional travel synthesis consultant specializing in Indian and global travel planning in Indian Rupees (INR). Provide clear, beautiful Markdown itineraries."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS_WORKER,
            temperature=0.3,
        )
        draft = response.choices[0].message.content or ""
        if not draft:
            raise ValueError("Empty response from worker model")
    except Exception:
        draft = (
            f"### Proposed {dest} Travel Itinerary ({travelers} Traveler{'s' if travelers > 1 else ''})\n\n"
            f"**Dates:** {start_d} to {end_d} | **Budget Cap:** {budget_result.total_cap.to_formatted_str()}\n\n"
            f"---\n\n"
            f"### Day 1: Arrival, Transfers & Settling In\n\n"
            f"✈️ **Available Outbound Flights ({dep_station} ➔ {dest}):**\n"
            f"{outbound_flights_text}\n"
            f"🚖 **Airport Transfer:** Easiest option is a prepaid airport taxi counter or app-based cab directly to your hotel (~{taxi_guidance}).\n\n"
            f"🏨 **Available Nearby Hotels to Stay & Rest:**\n"
            f"{hotels_text}\n"
            f"🌅 **Evening Relaxation:** Check-in, refresh at the pool or resort grounds, and enjoy sunset dining.\n\n"
            f"---\n\n"
            f"### Day 2: City & Attraction Exploration\n\n"
            f"📍 **Places to Visit:**\n"
            f"{places_summary_text}\n"
            f"🚗 **How to Visit & Easiest Transport:**\n"
            f"* **{easiest_transit}**\n"
            f"* Self-Drive Rental Cars: {rental_car_rate}\n"
            f"* Scooter / Bike Rental: {rental_scooter_rate}\n"
            f"* Cabs & Transit: {taxi_guidance}\n\n"
            f"🏨 **Where to Stay Tonight:**\n"
            f"{stay_strategy_text}\n\n"
            f"---\n\n"
            f"### Day 3: Morning Wrap-Up & Return Journey\n\n"
            f"🛍️ **Morning:** Leisurely breakfast, hotel check-out, and local market souvenir stop.\n"
            f"🚕 **Airport Transfer:** Hired cab to airport.\n\n"
            f"✈️ **Available Return Flights ({dest} ➔ {dep_station}):**\n"
            f"{return_flights_text}\n\n"
            f"---\n\n"
            f"### 💰 Budget & Cost Summary\n"
            f"- **Estimated Flights Total**: {budget_result.allocated_flights.to_formatted_str()}\n"
            f"- **Estimated Hotel Stay**: {budget_result.allocated_hotels.to_formatted_str()}\n"
            f"- **Activities & Local Transit**: {budget_result.allocated_activities.to_formatted_str()}\n"
            f"- **Committed Total**: **{budget_result.committed_total.to_formatted_str()}** ({budget_result.committed_total.to_words()})\n"
            f"- **Remaining Balance**: **{budget_result.remaining_balance.to_formatted_str()}**\n\n"
            f"*Note: All fares and hotel tariffs are indicative market estimates in Indian Rupees (₹ INR).*"
        )

    verdict = evaluate_output_guardrail(draft)
    if not verdict.allowed:
        draft = "Itinerary output failed safety evaluation. Please review requirements and try again."

    return {
        "budget_reconciliation": budget_result,
        "itinerary_draft": draft,
        "messages": [AIMessage(content=draft)],
        "next_step": "complete",
    }
