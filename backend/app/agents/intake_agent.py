from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from langchain_core.messages import AnyMessage
from ..core.config import get_openai_client, get_settings
from ..core.money import parse_indian_budget_decimal
from ..schemas.intake import IntakeSupervisorEvaluation


def compute_relative_reference_dates() -> tuple[str, str, str, str]:
    now = datetime.now(timezone.utc)
    today_date = now.date()
    today_name = now.strftime("%A")
    days_to_monday = (7 - today_date.weekday()) if today_date.weekday() != 0 else 7
    next_monday = today_date + timedelta(days=days_to_monday)
    return today_name, today_date.isoformat(), next_monday.isoformat(), next_monday.strftime("%B %d, %Y")


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
    today_name, today_iso, next_mon_iso, next_mon_formatted = compute_relative_reference_dates()
    time_greeting = get_time_of_day_greeting()

    latest_content = str(messages[-1].content).strip() if messages else ""
    latest_lower = latest_content.lower()

    if any(q in latest_lower for q in ["how are you", "how are u", "how r u", "how's it going", "how is it going"]):
        return IntakeSupervisorEvaluation(
            intent="chit_chat",
            departure_station=existing_state.get("departure_station"),
            destination=existing_state.get("destination"),
            duration_days=existing_state.get("duration_days"),
            budget_inr=existing_state.get("budget_inr"),
            start_date=existing_state.get("start_date"),
            end_date=existing_state.get("end_date"),
            relative_date_inferred=None,
            is_date_confirmed=False,
            missing_fields=["departure_station", "destination", "duration_days", "budget_inr", "start_date"],
            is_complete=False,
            next_question_or_confirmation=f"I'm doing wonderful, thank you for asking, {user_name}! I am PlanMyTrip AI, your personal travel planner. Where are you thinking of traveling next?",
        )

    if latest_lower in ["hi", "hello", "hey", "hlo", "hola", "namaste", "good morning", "good evening", "good afternoon"]:
        return IntakeSupervisorEvaluation(
            intent="chit_chat",
            departure_station=existing_state.get("departure_station"),
            destination=existing_state.get("destination"),
            duration_days=existing_state.get("duration_days"),
            budget_inr=existing_state.get("budget_inr"),
            start_date=existing_state.get("start_date"),
            end_date=existing_state.get("end_date"),
            relative_date_inferred=None,
            is_date_confirmed=False,
            missing_fields=["departure_station", "destination", "duration_days", "budget_inr", "start_date"],
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
        f"Calculated next week Monday is: {next_mon_iso} ({next_mon_formatted}).\n"
        f"User's name: {user_name}\n"
        f"Time-of-day greeting: {time_greeting}\n\n"
        f"Current known state:\n"
        f"- Departure station: {existing_state.get('departure_station')}\n"
        f"- Destination: {existing_state.get('destination')}\n"
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
        f"   - When the user discusses travel, destinations, flights, hotels, dates, budgets, or confirms an earlier question.\n"
        f"   - Track the 5 mandatory travel details:\n"
        f"     1. departure_station (boarding / departure city)\n"
        f"     2. destination (vacation city/region)\n"
        f"     3. duration_days (total days)\n"
        f"     4. budget_inr (approximate total budget in INR ₹)\n"
        f"     5. start_date (journey date, with user confirmation if relative)\n"
        f"   - RULES FOR RELATIVE DATES:\n"
        f"     * If user says 'next week' without a date, resolve start_date to {next_mon_iso}, set relative_date_inferred='Next week Monday ({next_mon_formatted})', set is_date_confirmed=False.\n"
        f"     * Explicitly confirm: 'I noticed you mentioned next week — should we schedule your departure for next Monday, {next_mon_formatted}?'\n"
        f"     * If user confirms an inferred date ('yes', 'sure', 'confirm', 'that works') or gives exact dates, set is_date_confirmed=True.\n"
        f"   - QUESTIONING RULES:\n"
        f"     * Acknowledge what was already provided with genuine enthusiasm (e.g. 'Goa sounds incredible!').\n"
        f"     * Never re-ask details that are already known.\n"
        f"     * Ask for missing details in a natural, cohesive sentence.\n"
        f"     * If all 5 fields are present AND date is confirmed: set is_complete=True, missing_fields=[], and next_question_or_confirmation=None.\n"
        f"     * Always use Indian Rupees (INR, ₹) for pricing."
    )

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_GUARDRAIL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation history:\n{conversation_text}"},
            ],
            response_format=IntakeSupervisorEvaluation,
            max_tokens=settings.OPENAI_MAX_TOKENS_WORKER,
            temperature=0.3,
        )
        parsed = response.choices[0].message.parsed
        if parsed:
            return parsed
    except Exception:
        pass

    latest_content = str(messages[-1].content).strip() if messages else ""
    latest_lower = latest_content.lower()

    if any(q in latest_lower for q in ["how are you", "how are u", "how r u", "how's it going", "how is it going"]):
        return IntakeSupervisorEvaluation(
            intent="chit_chat",
            departure_station=existing_state.get("departure_station"),
            destination=existing_state.get("destination"),
            duration_days=existing_state.get("duration_days"),
            budget_inr=existing_state.get("budget_inr"),
            start_date=existing_state.get("start_date"),
            end_date=existing_state.get("end_date"),
            relative_date_inferred=None,
            is_date_confirmed=False,
            missing_fields=["departure_station", "destination", "duration_days", "budget_inr", "start_date"],
            is_complete=False,
            next_question_or_confirmation=f"I'm doing wonderful, thank you for asking, {user_name}! I am PlanMyTrip AI, your personal travel planner. Where are you thinking of traveling next?",
        )

    if latest_lower in ["hi", "hello", "hey", "hola", "namaste", "good morning", "good evening", "good afternoon"]:
        return IntakeSupervisorEvaluation(
            intent="chit_chat",
            departure_station=existing_state.get("departure_station"),
            destination=existing_state.get("destination"),
            duration_days=existing_state.get("duration_days"),
            budget_inr=existing_state.get("budget_inr"),
            start_date=existing_state.get("start_date"),
            end_date=existing_state.get("end_date"),
            relative_date_inferred=None,
            is_date_confirmed=False,
            missing_fields=["departure_station", "destination", "duration_days", "budget_inr", "start_date"],
            is_complete=False,
            next_question_or_confirmation=f"Hi {user_name}! {time_greeting}! I am PlanMyTrip AI, your personal travel planner. Where would you like to travel next?",
        )

    off_topic_keywords = ["dsa", "langchain", "programming", "code", "python", "javascript", "java", "sql", "algorithm", "homework", "politics", "president"]
    if any(kw in latest_lower for kw in off_topic_keywords):
        return IntakeSupervisorEvaluation(
            intent="off_topic",
            departure_station=None,
            destination=None,
            duration_days=None,
            budget_inr=None,
            start_date=None,
            end_date=None,
            relative_date_inferred=None,
            is_date_confirmed=False,
            missing_fields=["departure_station", "destination", "duration_days", "budget_inr", "start_date"],
            is_complete=False,
            next_question_or_confirmation=f"Sorry {user_name}, I am unable to answer that as I can only plan trips. Do you have any destination or vacation in mind you would like to plan?",
        )

    parsed_budget = parse_indian_budget_decimal(latest_content)
    fallback_budget = float(parsed_budget) if parsed_budget > Decimal("0.00") else existing_state.get("budget_inr")

    return IntakeSupervisorEvaluation(
        intent="travel_planning",
        departure_station=existing_state.get("departure_station"),
        destination=existing_state.get("destination"),
        duration_days=existing_state.get("duration_days"),
        budget_inr=fallback_budget,
        start_date=existing_state.get("start_date"),
        end_date=existing_state.get("end_date"),
        relative_date_inferred=None,
        is_date_confirmed=bool(existing_state.get("start_date")),
        missing_fields=["departure_station", "destination", "duration_days", "budget_inr", "start_date"],
        is_complete=False,
        next_question_or_confirmation=f"Could you please share where you would like to travel from, your destination, travel dates, duration, and approximate budget in INR (₹)?",
    )
