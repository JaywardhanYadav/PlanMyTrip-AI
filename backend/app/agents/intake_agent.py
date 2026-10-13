import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal
from langchain_core.messages import AnyMessage
from ..core.config import get_openai_client, get_settings
from ..core.money import parse_indian_budget_decimal
from ..schemas.intake import IntakeSupervisorEvaluation


STATE_REGION_GATEWAYS: dict[str, dict[str, Any]] = {
    "RAJASTHAN": {
        "gateway": "Jaipur (JAI)",
        "destination_city": "Jaipur",
        "iata": "JAI",
        "circuits": [
            "Golden Triangle & Heritage: Jaipur -> Jodhpur -> Udaipur",
            "Desert & Forts: Jaipur -> Pushkar -> Jaisalmer",
        ],
        "note": "Resolved state Rajasthan to primary commercial gateway Jaipur (JAI).",
    },
    "KERALA": {
        "gateway": "Kochi (COK)",
        "destination_city": "Kochi",
        "iata": "COK",
        "circuits": [
            "Classic Kerala: Kochi -> Munnar -> Thekkady -> Alleppey",
            "Backwaters & Coast: Kochi -> Alleppey -> Varkala -> Kovalam",
        ],
        "note": "Resolved state Kerala to primary commercial gateway Kochi (COK).",
    },
    "HIMACHAL": {
        "gateway": "Chandigarh (IXC) / Shimla (SLV)",
        "destination_city": "Shimla",
        "iata": "IXC",
        "circuits": [
            "Valley Route: Shimla -> Kullu -> Manali",
            "Cultural Circuit: Chandigarh -> Dharamshala -> Dalhousie",
        ],
        "note": "Resolved state Himachal to commercial gateway Chandigarh / Shimla.",
    },
    "HIMACHAL PRADESH": {
        "gateway": "Chandigarh (IXC) / Shimla (SLV)",
        "destination_city": "Shimla",
        "iata": "IXC",
        "circuits": [
            "Valley Route: Shimla -> Kullu -> Manali",
            "Cultural Circuit: Chandigarh -> Dharamshala -> Dalhousie",
        ],
        "note": "Resolved state Himachal Pradesh to commercial gateway Chandigarh / Shimla.",
    },
    "SHIMLA": {
        "gateway": "Chandigarh (IXC) / Shimla (SLV)",
        "destination_city": "Shimla",
        "iata": "IXC",
        "circuits": [
            "Heritage & Ridge: Mall Road -> Viceregal Lodge -> Jakhoo Temple",
            "Himalayan Hills: Kufri -> Chail -> Mashobra",
        ],
        "note": "Resolved Shimla hill station to primary commercial airport gateway Chandigarh (IXC) / Jubbarhatti (SLV).",
    },
    "MANALI": {
        "gateway": "Chandigarh (IXC) / Bhuntar (KUU)",
        "destination_city": "Manali",
        "iata": "IXC",
        "circuits": [
            "Valley Highlights: Solang Valley -> Old Manali -> Hadimba Temple",
            "High Pass Adventure: Rohtang Pass -> Atal Tunnel -> Sissu",
        ],
        "note": "Resolved Manali to primary commercial airport gateway Chandigarh (IXC) / Kullu (KUU).",
    },
    "GOA": {
        "gateway": "Goa (GOI / GOX)",
        "destination_city": "Goa",
        "iata": "GOI",
        "circuits": [
            "North Goa Coastal & Heritage Circuit",
            "South Goa Serenity & Beach Circuit",
        ],
        "note": "Resolved Goa to Dabolim / Mopa airport gateway.",
    },
    "UTTARAKHAND": {
        "gateway": "Dehradun (DED)",
        "destination_city": "Dehradun",
        "iata": "DED",
        "circuits": [
            "Garhwal Foothills: Dehradun -> Rishikesh -> Mussoorie",
            "Kumaon Lakes: Nainital -> Almora -> Ranikhet",
        ],
        "note": "Resolved state Uttarakhand to primary commercial gateway Dehradun (DED).",
    },
    "KASHMIR": {
        "gateway": "Srinagar (SXR)",
        "destination_city": "Srinagar",
        "iata": "SXR",
        "circuits": [
            "Classic Paradise: Srinagar -> Gulmarg -> Pahalgam",
            "Valleys & Meadows: Srinagar -> Sonamarg -> Doodhpathri",
        ],
        "note": "Resolved Kashmir valley to primary commercial gateway Srinagar (SXR).",
    },
    "JAMMU AND KASHMIR": {
        "gateway": "Srinagar (SXR)",
        "destination_city": "Srinagar",
        "iata": "SXR",
        "circuits": [
            "Classic Paradise: Srinagar -> Gulmarg -> Pahalgam",
            "Valleys & Meadows: Srinagar -> Sonamarg -> Doodhpathri",
        ],
        "note": "Resolved Jammu and Kashmir to primary commercial gateway Srinagar (SXR).",
    },
    "LADAKH": {
        "gateway": "Leh (IXL)",
        "destination_city": "Leh",
        "iata": "IXL",
        "circuits": [
            "High Passes: Leh -> Nubra Valley -> Pangong Tso",
            "Monasteries & Lakes: Leh -> Sham Valley -> Tso Moriri",
        ],
        "note": "Resolved Ladakh region to gateway Leh (IXL).",
    },
    "TAMIL NADU": {
        "gateway": "Chennai (MAA)",
        "destination_city": "Chennai",
        "iata": "MAA",
        "circuits": [
            "Heritage & Temples: Chennai -> Mahabalipuram -> Pondicherry",
            "Hill Station Circuit: Coimbatore -> Ooty -> Kodaikanal",
        ],
        "note": "Resolved state Tamil Nadu to primary commercial gateway Chennai (MAA).",
    },
    "KARNATAKA": {
        "gateway": "Bangalore (BLR)",
        "destination_city": "Bangalore",
        "iata": "BLR",
        "circuits": [
            "Palaces & Coffee Hills: Bangalore -> Mysore -> Coorg",
            "Ruins & Coast: Bangalore -> Hampi -> Gokarna",
        ],
        "note": "Resolved state Karnataka to primary commercial gateway Bangalore (BLR).",
    },
    "MAHARASHTRA": {
        "gateway": "Mumbai (BOM)",
        "destination_city": "Mumbai",
        "iata": "BOM",
        "circuits": [
            "Western Ghats: Mumbai -> Lonavala -> Pune -> Mahabaleshwar",
            "Konkan Coast: Mumbai -> Alibaug -> Ganpatipule",
        ],
        "note": "Resolved state Maharashtra to primary commercial gateway Mumbai (BOM).",
    },
}

KNOWN_COUNTRIES = {
    "FRANCE", "JAPAN", "USA", "UNITED STATES", "THAILAND", "VIETNAM",
    "SINGAPORE", "INDONESIA", "BALI", "DUBAI", "UAE", "SWITZERLAND",
    "UK", "UNITED KINGDOM", "ITALY", "SPAIN", "GERMANY", "AUSTRALIA",
    "NEW ZEALAND", "MALAYSIA", "TURKEY", "GREECE", "EGYPT", "MALDIVES",
    "SRI LANKA", "NEPAL", "BHUTAN", "MAURITIUS",
}


def resolve_destination_entity(
    destination: str | None,
) -> tuple[Literal["city", "state_region", "country"], str | None, list[str], str | None]:
    if not destination:
        return "city", None, [], None

    clean = destination.strip().upper()

    for state_name, info in STATE_REGION_GATEWAYS.items():
        if state_name in clean or clean in state_name:
            return "state_region", str(info["gateway"]), [str(c) for c in info["circuits"]], str(info["note"])

    for country in KNOWN_COUNTRIES:
        if country in clean or clean in country:
            return "country", None, [], None

    return "city", None, [], None


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
                destination_type="city",
                travelers_count=existing_state.get("travelers_count"),
                duration_days=existing_state.get("duration_days"),
                trip_nights=None,
                budget_inr=existing_state.get("budget_inr"),
                budget_tier="unspecified",
                start_date=existing_state.get("start_date"),
                end_date=existing_state.get("end_date"),
                relative_date_inferred=None,
                is_date_confirmed=False,
                missing_fields=["departure_station", "destination", "travelers_count", "duration_days", "start_date"],
                is_complete=False,
                next_question_or_confirmation=f"I'm doing wonderful, thank you for asking, {user_name}! I am PlanMyTrip AI, your personal travel planner. Where are you thinking of traveling next?",
            )

        if latest_lower in ["hi", "hello", "hey", "hlo", "hola", "namaste", "good morning", "good evening", "good afternoon"]:
            return IntakeSupervisorEvaluation(
                intent="chit_chat",
                departure_station=existing_state.get("departure_station"),
                destination=existing_state.get("destination"),
                destination_type="city",
                travelers_count=existing_state.get("travelers_count"),
                duration_days=existing_state.get("duration_days"),
                trip_nights=None,
                budget_inr=existing_state.get("budget_inr"),
                budget_tier="unspecified",
                start_date=existing_state.get("start_date"),
                end_date=existing_state.get("end_date"),
                relative_date_inferred=None,
                is_date_confirmed=False,
                missing_fields=["departure_station", "destination", "travelers_count", "duration_days", "start_date"],
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
        f"     * To 'how are you': Respond warmly in 1 short sentence and smoothly pivot to asking about their travel ideas.\n"
        f"     * To greetings ('hi', 'hello'): Greet them by name: 'Hi {user_name}! {time_greeting}! I am PlanMyTrip AI, your personal travel planner. Where would you like to travel next?'\n"
        f"     * To 'who are you' / 'what can you do': Explain concisely that you find flights, hotels, and craft itineraries, then ask where they want to go.\n"
        f"     * To 'thanks' / 'cool': Acknowledge warmly and keep the door open for travel plans.\n"
        f"   - Set is_complete=False.\n\n"
        f"2. INTENT = 'off_topic':\n"
        f"   - When the user asks about completely unrelated topics (programming, DSA, coding, math, homework, politics).\n"
        f"   - Response Rule: State your role politely and invite travel planning:\n"
        f"     'Sorry {user_name}, I am unable to answer that as I can only plan trips. Do you have any destination or vacation in mind you would like to plan?'\n"
        f"   - Set is_complete=False.\n\n"
        f"3. INTENT = 'travel_planning':\n"
        f"   - When the user discusses travel, destinations, flights, hotels, dates, budgets, travelers count, or confirms an earlier question.\n"
        f"   - Slot Filling & Validation Rules:\n"
        f"     1. departure_station: Boarding or departure city.\n"
        f"     2. destination: Vacation city or region.\n"
        f"        * Categorize destination_type: 'city', 'state_region', or 'country'.\n"
        f"        * If user enters a state or broad region (e.g. Rajasthan, Kerala, Himachal), resolve to primary commercial gateway (e.g. Jaipur (JAI) for Rajasthan, Kochi (COK) for Kerala) with an explicit note, or propose 2 route circuits.\n"
        f"     3. travelers_count: Number of people traveling (e.g. 1 for solo, 2 for couple/wife/partner/friend, 4 for family).\n"
        f"     4. duration_days: Total travel days (positive integer).\n"
        f"     5. start_date & end_date math:\n"
        f"        * start_date parsed from prompt or relative reference.\n"
        f"        * end_date = start_date + timedelta(days=duration_days - 1) (inclusive travel range).\n"
        f"        * trip_nights = duration_days - 1.\n"
        f"     6. budget_inr & budget_tier:\n"
        f"        * budget_tier: 'budget', 'mid_range', 'luxury', or 'unspecified'.\n"
        f"        * If user does NOT specify a budget, set budget_tier='unspecified' and budget_inr=None. Do NOT invent an arbitrary luxury budget.\n"
        f"        * Budget is optional: If departure_station, destination, travelers_count, duration_days, and start_date are present and confirmed, set is_complete=True.\n"
        f"   - QUESTIONING RULES:\n"
        f"     * Acknowledge what was already provided with genuine enthusiasm.\n"
        f"     * Never re-ask details that are already known.\n"
        f"     * Naturally ask for missing details that haven't been provided yet.\n"
        f"     * Combine questions naturally into 1 smooth, cohesive conversational sentence rather than an interrogation."
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
            if parsed.duration_days is None:
                d_m = re.search(r"(\d+)\s*(?:day|days|d\b)", latest_lower)
                if d_m:
                    try:
                        parsed.duration_days = int(d_m.group(1))
                    except Exception:
                        pass
                elif existing_state.get("duration_days"):
                    try:
                        parsed.duration_days = int(str(existing_state["duration_days"]))
                    except Exception:
                        pass

            if parsed.duration_days is not None and "duration_days" in parsed.missing_fields:
                parsed.missing_fields.remove("duration_days")

            if not parsed.start_date and any(kw in latest_lower for kw in ["tomorrow", "tomarrow"]):
                try:
                    today_d = datetime.fromisoformat(today_iso).date()
                    parsed.start_date = (today_d + timedelta(days=1)).isoformat()
                    parsed.is_date_confirmed = True
                except Exception:
                    pass

            if parsed.budget_inr is None and any(kw in latest_lower for kw in ["lakh", "lac", "cr", "thousand", "k", "budget", "inr", "₹", "rs"]):
                inferred_amt = parse_indian_budget_decimal(latest_content)
                if inferred_amt > Decimal("0"):
                    parsed.budget_inr = float(inferred_amt)

            if parsed.travelers_count is None and existing_state.get("travelers_count"):
                parsed.travelers_count = existing_state.get("travelers_count")

            if parsed.travelers_count is not None and "travelers_count" in parsed.missing_fields:
                parsed.missing_fields.remove("travelers_count")

            dest_type, gateway, circuits, note = resolve_destination_entity(parsed.destination)
            parsed.destination_type = dest_type
            if gateway and not parsed.resolved_gateway:
                parsed.resolved_gateway = gateway
            if circuits and not parsed.route_circuits:
                parsed.route_circuits = circuits
            if note and not parsed.gateway_note:
                parsed.gateway_note = note

            if parsed.start_date and parsed.duration_days:
                try:
                    s_dt = datetime.fromisoformat(parsed.start_date).date()
                    trip_days = max(1, parsed.duration_days)
                    parsed.end_date = (s_dt + timedelta(days=trip_days - 1)).isoformat()
                    parsed.trip_nights = max(0, trip_days - 1)
                except Exception:
                    pass

            if parsed.budget_inr is not None and parsed.budget_inr > 0:
                t_count = parsed.travelers_count or 1
                per_head = parsed.budget_inr / t_count
                if per_head < 35000:
                    parsed.budget_tier = "budget"
                elif per_head <= 100000:
                    parsed.budget_tier = "mid_range"
                else:
                    parsed.budget_tier = "luxury"
                if "budget_inr" in parsed.missing_fields:
                    parsed.missing_fields.remove("budget_inr")
            else:
                if any(w in latest_lower for w in ["luxury", "5-star", "5 star", "heritage", "palace"]):
                    parsed.budget_tier = "luxury"
                elif any(w in latest_lower for w in ["budget", "cheap", "hostel", "backpacker", "low cost", "affordable"]):
                    parsed.budget_tier = "budget"
                elif any(w in latest_lower for w in ["mid-range", "mid range", "comfort", "boutique", "4-star"]):
                    parsed.budget_tier = "mid_range"
                else:
                    parsed.budget_tier = "unspecified"
                    parsed.budget_inr = None

            if parsed.start_date and any(d_kw in latest_lower for d_kw in ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "oct", "nov", "dec", "2026", "next week", "yes", "tomorrow", "tomarrow"]):
                parsed.is_date_confirmed = True

            if (
                parsed.departure_station
                and parsed.destination
                and parsed.travelers_count
                and parsed.start_date
                and parsed.duration_days
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

    dest_val = existing_state.get("destination")
    dest_type, gateway, circuits, note = resolve_destination_entity(dest_val)
    dur_days = existing_state.get("duration_days")
    start_d = existing_state.get("start_date")
    end_d = existing_state.get("end_date")
    nights = None
    if start_d and dur_days:
        try:
            s_dt = datetime.fromisoformat(str(start_d)).date()
            trip_days = max(1, int(str(dur_days)))
            end_d = (s_dt + timedelta(days=trip_days - 1)).isoformat()
            nights = max(0, trip_days - 1)
        except Exception:
            pass

    return IntakeSupervisorEvaluation(
        intent="travel_planning",
        departure_station=existing_state.get("departure_station"),
        destination=dest_val,
        destination_type=dest_type,
        resolved_gateway=gateway,
        route_circuits=circuits,
        gateway_note=note,
        travelers_count=inferred_travelers,
        duration_days=dur_days,
        trip_nights=nights,
        budget_inr=clean_budget or existing_state.get("budget_inr"),
        budget_tier="unspecified" if not clean_budget and not existing_state.get("budget_inr") else "mid_range",
        start_date=start_d,
        end_date=end_d,
        relative_date_inferred=None,
        is_date_confirmed=False,
        missing_fields=["departure_station", "destination", "travelers_count", "duration_days", "start_date"],
        is_complete=False,
        next_question_or_confirmation=f"I would be glad to help plan your getaway! What departure city, dates, and travelers are you thinking of?",
    )
