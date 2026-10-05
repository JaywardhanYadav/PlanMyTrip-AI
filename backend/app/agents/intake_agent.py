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


async def evaluate_trip_intake(
    messages: list[AnyMessage],
    existing_state: dict[str, Any] | None = None,
) -> IntakeSupervisorEvaluation:
    existing_state = existing_state or {}
    today_name, today_iso, next_mon_iso, next_mon_formatted = compute_relative_reference_dates()

    client = get_openai_client()
    settings = get_settings()

    conversation_text = ""
    for msg in messages:
        sender = "User" if msg.type in ["human", "user"] else "Assistant"
        conversation_text += f"{sender}: {msg.content}\n"

    system_prompt = (
        f"You are the Intake Supervisor for PlanMyTrip AI.\n"
        f"Today is {today_name}, {today_iso}.\n"
        f"Calculated next week Monday is: {next_mon_iso} ({next_mon_formatted}).\n\n"
        f"Current known state:\n"
        f"- Departure station: {existing_state.get('departure_station')}\n"
        f"- Destination: {existing_state.get('destination')}\n"
        f"- Start date: {existing_state.get('start_date')}\n"
        f"- End date: {existing_state.get('end_date')}\n"
        f"- Budget: {existing_state.get('budget_inr')}\n\n"
        f"You must evaluate if all 5 mandatory details are collected:\n"
        f"1. Departure / Boarding location (departure_station)\n"
        f"2. Destination location (destination)\n"
        f"3. Duration of the trip in days (duration_days)\n"
        f"4. Approximate budget in Indian Rupees INR (budget_inr)\n"
        f"5. Date of journey (start_date, with user confirmation if relative)\n\n"
        f"RULES FOR RELATIVE DATES & CONFIRMATION:\n"
        f"- If user says 'next week' without an exact date, resolve start_date to {next_mon_iso}, "
        f"set relative_date_inferred='Next week Monday ({next_mon_formatted})', and set is_date_confirmed=False.\n"
        f"- Explicitly request confirmation in next_question_or_confirmation: e.g., "
        f"'I noticed you mentioned next week — should we schedule your departure for next Monday, {next_mon_formatted}?'\n"
        f"- If the user confirms an inferred date (e.g. 'yes', 'sure', 'confirm', 'that works') or gave an exact date, set is_date_confirmed=True.\n\n"
        f"QUESTIONING RULES:\n"
        f"- Acknowledge details already provided.\n"
        f"- Only ask for missing details and date confirmation in next_question_or_confirmation.\n"
        f"- If all 5 fields are present and date is confirmed, set is_complete=True, missing_fields=[], and next_question_or_confirmation=None.\n"
        f"- All currency amounts must be in Indian Rupees (INR, ₹)."
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
            temperature=0.0,
        )
        parsed = response.choices[0].message.parsed
        if parsed:
            return parsed
    except Exception:
        pass

    latest_content = str(messages[-1].content) if messages else ""
    parsed_budget = parse_indian_budget_decimal(latest_content)
    fallback_budget = parsed_budget if parsed_budget > Decimal("0.00") else existing_state.get("budget_inr")

    return IntakeSupervisorEvaluation(
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
        next_question_or_confirmation="Could you please share your departure city, destination, travel dates, duration, and approximate budget in INR (₹)?",
    )
