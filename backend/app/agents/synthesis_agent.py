from decimal import Decimal
from langchain_core.messages import AIMessage
from ..core.config import get_openai_client, get_settings
from ..core.money import Money, reconcile_trip_budget
from ..core.state import PlanMyTripState
from ..guardrails.output_guard import evaluate_output_guardrail


async def synthesis_agent_node(state: PlanMyTripState) -> dict[str, object]:
    flight_options = state.get("flight_options", [])
    selected_flight_id = state.get("selected_flight_id")
    selected_flights = [f for f in flight_options if f.option_id == selected_flight_id]
    flight_costs = [f.fare for f in selected_flights]

    hotel_options = state.get("hotel_options", [])
    selected_hotel_id = state.get("selected_hotel_id")
    selected_hotels = [h for h in hotel_options if h.option_id == selected_hotel_id]
    hotel_costs = [h.total_rate for h in selected_hotels]

    activity_options = state.get("activity_options", [])
    selected_act_ids = set(state.get("selected_activity_ids", []))
    selected_activities = [a for a in activity_options if a.option_id in selected_act_ids]
    activity_costs = [a.cost for a in selected_activities]

    trip_budget = state.get("trip_budget")
    if trip_budget and isinstance(trip_budget, Money):
        total_cap = trip_budget
    else:
        total_cap = Money(amount=Decimal("200000.00"), currency="INR")

    budget_result = reconcile_trip_budget(
        total_cap=total_cap,
        flight_costs=flight_costs,
        hotel_costs=hotel_costs,
        activity_costs=activity_costs,
    )

    flight_desc = f"{selected_flights[0].carrier} ({selected_flights[0].fare.to_formatted_str()})" if selected_flights else "None"
    hotel_desc = f"{selected_hotels[0].name} ({selected_hotels[0].total_rate.to_formatted_str()})" if selected_hotels else "None"
    activities_desc = ", ".join([f"{a.title} ({a.cost.to_formatted_str()})" for a in selected_activities]) or "Free sightseeing"

    client = get_openai_client()
    settings = get_settings()

    dep_station = state.get("departure_station") or "New Delhi"
    dest = state.get("destination") or "Goa"
    start_d = state.get("start_date") or "2026-12-01"
    end_d = state.get("end_date") or "2026-12-05"

    prompt = (
        f"You are the Synthesis Agent for PlanMyTrip AI. Synthesize the finalized trip plan.\n"
        f"- Departure Station / City: {dep_station}\n"
        f"- Destination: {dest}\n"
        f"- Travel Dates: {start_d} to {end_d}\n"
        f"- Flights: {flight_desc}\n"
        f"- Hotel: {hotel_desc}\n"
        f"- Activities: {activities_desc}\n"
        f"- Budget Cap: {budget_result.total_cap.to_formatted_str()} ({budget_result.total_cap.to_words()})\n"
        f"- Committed Total: {budget_result.committed_total.to_formatted_str()} ({budget_result.committed_total.to_words()})\n"
        f"- Remaining Balance: {budget_result.remaining_balance.to_formatted_str()} ({budget_result.remaining_balance.to_words()})\n"
        f"Provide a structured, beautifully formatted markdown travel itinerary with daily breakdown and cost summary in Indian Rupees (INR, ₹). "
        f"Always use Indian currency notations like ₹ and Lakhs/Thousands. "
        f"Mention that all prices are indicative estimates."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_WORKER,
            messages=[
                {"role": "system", "content": "You are a professional travel synthesis consultant specializing in Indian and global travel planning in Indian Rupees (INR)."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS_WORKER,
            temperature=0.3,
        )
        draft = response.choices[0].message.content or "Trip itinerary generated successfully."
    except Exception:
        draft = (
            f"### Proposed Trip Itinerary\n\n"
            f"- **Flight**: {flight_desc}\n"
            f"- **Accommodation**: {hotel_desc}\n"
            f"- **Scheduled Activities**: {activities_desc}\n\n"
            f"**Total Estimated Cost**: {budget_result.committed_total.to_formatted_str()} "
            f"(Remaining: {budget_result.remaining_balance.to_formatted_str()})\n\n"
            f"*Note: All prices are indicative estimates in Indian Rupees (INR).*"
        )

    verdict = evaluate_output_guardrail(draft)
    if not verdict.allowed:
        draft = "Itinerary output failed safety evaluation. Please review requirements and try again."

    return {
        "budget_reconciliation": budget_result,
        "itinerary_draft": draft,
        "messages": [AIMessage(content=draft)],
        "next_step": "human_approval",
    }
