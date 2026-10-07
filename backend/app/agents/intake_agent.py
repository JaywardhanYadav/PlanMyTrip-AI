from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from langchain_core.messages import AnyMessage
from ..core.config import get_openai_client, get_settings
from ..core.money import parse_indian_budget_decimal
from ..schemas.intake import IntakeSupervisorEvaluation


def compute_relative_reference_dates() -> tuple[str, str, str, str, str, str]:
    now = datetime.now(timezone.utc)
    today_date = now.date()
    today_name = now.strftime("%A")
    days_to_monday = (7 - today_date.weekday()) if today_date.weekday() != 0 else 7
    next_monday = today_date + timedelta(days=days_to_monday)
    days_to_sunday = (6 - today_date.weekday()) if today_date.weekday() != 6 else 7
    upcoming_sunday = today_date + timedelta(days=days_to_sunday)
    return (
        today_name,
        today_date.isoformat(),
        next_monday.isoformat(),
        next_monday.strftime("%B %d, %Y"),
        upcoming_sunday.isoformat(),
        upcoming_sunday.strftime("%B %d, %Y"),
    )


def get_time_of_day_greeting() -> str:
    utc_now = datetime.now(timezone.utc)
    ist_hour = (utc_now.hour + 5 + (1 if utc_now.minute + 30 >= 60 else 0)) % 24
    if ist_hour < 12:
        return "Good morning"
    elif ist_hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


async def evaluate_trip_intake(
    messages: list[AnyMessage],
    existing_state: dict[str, Any] | None = None,
    user_name: str = "there",
) -> IntakeSupervisorEvaluation:
    existing_state = existing_state or {}
    today_name, today_iso, next_mon_iso, next_mon_formatted, up_sun_iso, up_sun_formatted = compute_relative_reference_dates()
    time_greeting = get_time_of_day_greeting()

    latest_content = str(messages[-1].content).strip() if messages else ""
    latest_lower = latest_content.lower()
    has_existing_plan = bool(existing_state.get("destination"))

    if not has_existing_plan:
        if any(q in latest_lower for q in ["how are you", "how are u", "how r u", "how's it going", "how is it going"]):
            return IntakeSupervisorEvaluation(
                intent="chit_chat",
                departure_station=existing_state.get("departure_station"),
                destination=existing_state.get("destination"),
                travelers_count=existing_state.get("travelers_count"),
                duration_days=existing_state.get("duration_days"),
                budget_inr=existing_state.get("budget_inr"),
                start_date=existing_state.get("start_date"),
                end_date=existing_state.get("end_date"),
                relative_date_inferred=None,
                is_date_confirmed=False,
                missing_fields=["departure_station", "destination", "travelers_count", "duration_days", "budget_inr", "start_date"],
                is_complete=False,
                next_question_or_confirmation=f"I'm doing wonderful, thank you for asking, {user_name}! I am PlanMyTrip AI, your personal travel planner. Where are you thinking of traveling next?",
            )

        if latest_lower in ["hi", "hello", "hey", "hlo", "hola", "namaste", "good morning", "good evening", "good afternoon"]:
            return IntakeSupervisorEvaluation(
                intent="chit_chat",
                departure_station=existing_state.get("departure_station"),
                destination=existing_state.get("destination"),
                travelers_count=existing_state.get("travelers_count"),
                duration_days=existing_state.get("duration_days"),
                budget_inr=existing_state.get("budget_inr"),
                start_date=existing_state.get("start_date"),
                end_date=existing_state.get("end_date"),
                relative_date_inferred=None,
                is_date_confirmed=False,
                missing_fields=["departure_station", "destination", "travelers_count", "duration_days", "budget_inr", "start_date"],
                is_complete=False,
                next_question_or_confirmation=f"Hi {user_name}! {time_greeting}! I am PlanMyTrip AI, your personal travel planner. Where would you like to travel next?",
            )

    client = get_openai_client()
    settings = get_settings()

    conversation_text = ""
    for msg in messages:
        sender = "User" if msg.type in ["human", "user"] else "Assistant"
        conversation_text += f"{sender}: {msg.content}\n"

    system_prompt = (
        f"You are PlanMyTrip AI, an intelligent, empathetic, and proactive travel concierge designed with the natural conversational flair of ChatGPT.\n"
        f"Today is {today_name}, {today_iso}.\n"
        f"Calculated upcoming Sunday (this weekend) is: {up_sun_iso} ({up_sun_formatted}).\n"
        f"Calculated next week Monday is: {next_mon_iso} ({next_mon_formatted}).\n"
        f"User's name: {user_name}\n"
        f"Time-of-day greeting: {time_greeting}\n\n"
        f"Current known state:\n"
        f"- Departure station: {existing_state.get('departure_station')}\n"
        f"- Destination: {existing_state.get('destination')}\n"
        f"- Number of travelers: {existing_state.get('travelers_count')}\n"
        f"- Duration (days): {existing_state.get('duration_days')}\n"
        f"- Start date: {existing_state.get('start_date')}\n"
        f"- End date: {existing_state.get('end_date')}\n"
        f"- Budget: {existing_state.get('budget_inr')}\n\n"
        f"CLASSIFY USER INTENT INTO ONE OF THREE CATEGORIES:\n\n"
        f"1. INTENT = 'chit_chat':\n"
        f"   - When the user engages in social greetings, pleasantries, small talk, or asks about you.\n"
        f"   - Examples: 'how are you', 'how is it going', 'who are you', 'what can you do', 'hi', 'hello', 'hey', 'thanks', 'cool', 'good morning', etc.\n"
        f"   - Response Rule (Acknowledge & Pivot):\n"
        f"     * To 'how are you': Respond warmly in 1 short sentence (e.g. 'I am doing wonderful, thank you for asking, {user_name}!') and smoothly pivot to asking about their travel ideas.\n"
        f"     * To greetings ('hi', 'hello'): Greet them by name: 'Hi {user_name}! {time_greeting}! I am PlanMyTrip AI, your personal travel planner. Where would you like to travel next?'\n"
        f"     * To 'who are you' / 'what can you do': Explain concisely that you are their AI travel concierge who finds flights, hotels, and crafts itineraries, then ask where they want to go.\n"
        f"     * To 'thanks' / 'cool': Acknowledge warmly and keep the door open for their travel plans.\n"
        f"   - Set is_complete=False.\n\n"
        f"2. INTENT = 'off_topic':\n"
        f"   - When the user asks about completely unrelated topics (programming, DSA, LangChain, coding, math, physics, homework, political debates, general non-travel trivia).\n"
        f"   - Response Rule: State your role politely and invite travel planning:\n"
        f"     'Sorry {user_name}, I am unable to answer that as I can only plan trips. Do you have any destination or vacation in mind you would like to plan?'\n"
        f"   - Set is_complete=False.\n\n"
        f"3. INTENT = 'travel_planning':\n"
        f"   - When the user discusses travel, destinations, flights, hotels, dates, budgets, travelers count, or confirms an earlier question.\n"
        f"   - Track the 6 mandatory travel details:\n"
        f"     1. departure_station (boarding / departure city)\n"
        f"     2. destination (vacation city/region - standardize variations like 'benglore', 'bangalore', 'bengaluru' to 'Bangalore')\n"
        f"     3. travelers_count (number of people traveling, e.g. 1 for solo/alone, 2 for couple/wife/partner/friend, 4 for family/group)\n"
        f"     4. duration_days (total days)\n"
        f"     5. budget_inr (approximate total budget in INR ₹)\n"
        f"     6. start_date (journey date, with user confirmation if relative)\n"
        f"   - RULES FOR RELATIVE DATES:\n"
        f"     * If user says 'next week sunday' or 'sunday', calculate start_date accurately: if they mean this upcoming Sunday, resolve to {up_sun_iso}; if subsequent Sunday, add 7 days. If the user explicitly provided the day of travel ('next week sunday'), mark is_date_confirmed=True.\n"
        f"     * If user says 'next week' without a specific day, resolve start_date to {next_mon_iso}, set relative_date_inferred='Next week Monday ({next_mon_formatted})', set is_date_confirmed=False.\n"
        f"     * If user confirms an inferred date ('yes', 'sure', 'confirm', 'that works') or gives exact dates, set is_date_confirmed=True.\n"
        f"   - QUESTIONING RULES:\n"
        f"     * Acknowledge what was already provided with genuine enthusiasm.\n"
        f"     * Never re-ask details that are already known.\n"
        f"     * Naturally ask for missing details that haven't been provided yet, including group size / number of travelers.\n"
        f"     * Combine questions naturally into 1 smooth, cohesive conversational sentence rather than an interrogation.\n"
        f"     * If all 6 fields are present AND date is confirmed: set is_complete=True, missing_fields=[], and next_question_or_confirmation=None.\n"
        f"     * Always use Indian Rupees (INR, ₹) for pricing."
    )

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_GUARDRAIL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Full Conversation History:\n{conversation_text}\n\nLatest User Message:\n{latest_content}\n\nExisting State:\n{existing_state}"},
            ],
            response_format=IntakeSupervisorEvaluation,
            temperature=0.0,
        )
        parsed = response.choices[0].message.parsed
        if parsed:
            if parsed.budget_inr is None and any(kw in latest_lower for kw in ["lakh", "lac", "cr", "thousand", "k", "budget", "inr", "₹", "rs"]):
                inferred_amt = parse_indian_budget_decimal(latest_content)
                if inferred_amt > Decimal("0"):
                    parsed.budget_inr = float(inferred_amt)

            if parsed.budget_inr is not None and "budget_inr" in parsed.missing_fields:
                parsed.missing_fields.remove("budget_inr")

            if parsed.travelers_count is None and existing_state.get("travelers_count"):
                parsed.travelers_count = existing_state.get("travelers_count")

            if parsed.travelers_count is not None and "travelers_count" in parsed.missing_fields:
                parsed.missing_fields.remove("travelers_count")

            if parsed.start_date and parsed.duration_days and not parsed.end_date:
                try:
                    s_dt = datetime.fromisoformat(parsed.start_date)
                    parsed.end_date = (s_dt + timedelta(days=parsed.duration_days)).date().isoformat()
                except Exception:
                    pass

            if parsed.start_date and any(d_kw in latest_lower for d_kw in ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "oct", "nov", "dec", "2026", "next week", "yes"]):
                parsed.is_date_confirmed = True

            if (
                parsed.departure_station
                and parsed.destination
                and parsed.travelers_count
                and parsed.start_date
                and parsed.duration_days
                and parsed.budget_inr is not None
                and parsed.is_date_confirmed
            ):
                parsed.is_complete = True
                parsed.missing_fields = []
                parsed.next_question_or_confirmation = None

            return parsed

    except Exception:
        pass

    clean_budget = None
    if any(kw in latest_lower for kw in ["lakh", "lac", "cr", "thousand", "k", "budget", "inr", "₹", "rs"]):
        amt = parse_indian_budget_decimal(latest_content)
        if amt > Decimal("0"):
            clean_budget = float(amt)

    inferred_travelers = existing_state.get("travelers_count")
    if not inferred_travelers:
        if any(w in latest_lower for w in ["wife", "husband", "partner", "couple", "two of us", "with my friend"]):
            inferred_travelers = 2
        elif any(w in latest_lower for w in ["alone", "solo", "myself", "just me"]):
            inferred_travelers = 1

    return IntakeSupervisorEvaluation(
        intent="travel_planning",
        departure_station=existing_state.get("departure_station"),
        destination=existing_state.get("destination"),
        travelers_count=inferred_travelers,
        duration_days=existing_state.get("duration_days"),
        budget_inr=clean_budget or existing_state.get("budget_inr"),
        start_date=existing_state.get("start_date"),
        end_date=existing_state.get("end_date"),
        relative_date_inferred=None,
        is_date_confirmed=False,
        missing_fields=["departure_station", "destination", "travelers_count", "duration_days", "budget_inr", "start_date"],
        is_complete=False,
        next_question_or_confirmation=f"I would be glad to help plan your getaway! What departure city, dates, and travelers are you thinking of?",
    )
