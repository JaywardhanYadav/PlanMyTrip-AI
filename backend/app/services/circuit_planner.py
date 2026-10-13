from decimal import Decimal
import re
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from ..core.state import PlanMyTripState


class HubScheduleItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    day_number: int
    city: str
    stay_area: str
    is_city_transition: bool
    luggage_instruction: str
    special_stay: str | None = None


CIRCUIT_HUB_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "KERALA": [
        {"city": "Kochi", "stay_area": "Fort Kochi or Bolgatty Island waterfront, Kochi", "special_stay": None},
        {"city": "Kochi", "stay_area": "Fort Kochi or Bolgatty Island waterfront, Kochi", "special_stay": None},
        {"city": "Munnar", "stay_area": "Munnar Tea Valley or Pallivasal hill resort, Munnar", "special_stay": None},
        {"city": "Munnar", "stay_area": "Munnar Tea Valley or Pallivasal hill resort, Munnar", "special_stay": None},
        {"city": "Thekkady", "stay_area": "Kumily / Periyar Wildlife Gateway retreat, Thekkady", "special_stay": None},
        {"city": "Thekkady", "stay_area": "Kumily / Periyar Wildlife Gateway retreat, Thekkady", "special_stay": None},
        {"city": "Alleppey", "stay_area": "Private Luxury Houseboat on Vembanad Lake canals, Alleppey", "special_stay": "houseboat"},
        {"city": "Kochi", "stay_area": "Departure Airport / Cochin (COK)", "special_stay": None},
    ],
    "RAJASTHAN": [
        {"city": "Jaipur", "stay_area": "MI Road or C-Scheme Heritage Hotel, Jaipur", "special_stay": None},
        {"city": "Jaipur", "stay_area": "MI Road or C-Scheme Heritage Hotel, Jaipur", "special_stay": None},
        {"city": "Jodhpur", "stay_area": "Old City or Ratanada Heritage Haveli, Jodhpur", "special_stay": None},
        {"city": "Jodhpur", "stay_area": "Old City or Ratanada Heritage Haveli, Jodhpur", "special_stay": None},
        {"city": "Udaipur", "stay_area": "Lake Pichola waterfront resort, Udaipur", "special_stay": None},
        {"city": "Udaipur", "stay_area": "Lake Pichola waterfront resort, Udaipur", "special_stay": None},
        {"city": "Jaipur", "stay_area": "Departure Airport / Jaipur (JAI)", "special_stay": None},
    ],
    "HIMACHAL": [
        {"city": "Shimla", "stay_area": "Mall Road or Chotta Shimla heritage resort, Shimla", "special_stay": None},
        {"city": "Shimla", "stay_area": "Mall Road or Chotta Shimla heritage resort, Shimla", "special_stay": None},
        {"city": "Manali", "stay_area": "Old Manali or Log Huts riverside resort, Manali", "special_stay": None},
        {"city": "Manali", "stay_area": "Old Manali or Log Huts riverside resort, Manali", "special_stay": None},
        {"city": "Manali", "stay_area": "Old Manali or Log Huts riverside resort, Manali", "special_stay": None},
        {"city": "Chandigarh", "stay_area": "Departure Airport / Chandigarh (IXC)", "special_stay": None},
    ],
}


CIRCUIT_ALIASES: dict[str, list[str]] = {
    "KERALA": ["KERALA", "MUNNAR", "ALLEPPEY", "THEKKADY", "COCHIN CIRCUIT"],
    "RAJASTHAN": ["RAJASTHAN", "JAIPUR CIRCUIT", "JODHPUR", "UDAIPUR", "GOLDEN TRIANGLE"],
    "HIMACHAL": ["HIMACHAL", "SHIMLA CIRCUIT", "MANALI", "KULLU", "DHARAMSHALA"],
}


def build_circuit_hub_schedule(
    destination: str,
    duration_days: int,
    target_stay_neighborhood: str | None = None,
    route_circuits: list[str] | None = None,
    destination_type: str | None = None,
) -> list[HubScheduleItem]:
    full_context = destination.strip().upper()
    if route_circuits:
        full_context += " " + " ".join([str(c).upper() for c in route_circuits])

    total_days = max(1, duration_days)

    matched_template: list[dict[str, Any]] | None = None
    for key, aliases in CIRCUIT_ALIASES.items():
        if any(alias in full_context for alias in aliases):
            matched_template = CIRCUIT_HUB_TEMPLATES.get(key)
            break

    if not matched_template:
        default_stay = target_stay_neighborhood or f"Central {destination}"
        schedule: list[HubScheduleItem] = []
        for d in range(1, total_days + 1):
            if d == 1:
                schedule.append(
                    HubScheduleItem(
                        day_number=1,
                        city=destination,
                        stay_area=f"{default_stay}, {destination}",
                        is_city_transition=True,
                        luggage_instruction="Check-in to hotel upon arrival",
                        special_stay=None,
                    )
                )
            elif d == total_days:
                schedule.append(
                    HubScheduleItem(
                        day_number=d,
                        city=destination,
                        stay_area=f"Departure Airport / {destination} (Hotel check-out completed in morning)",
                        is_city_transition=True,
                        luggage_instruction="Check out after breakfast; concierge luggage storage until departure",
                        special_stay=None,
                    )
                )
            else:
                schedule.append(
                    HubScheduleItem(
                        day_number=d,
                        city=destination,
                        stay_area=f"Your hotel in {default_stay}, {destination} (Luggage stays in room - no hotel change needed)",
                        is_city_transition=False,
                        luggage_instruction="Luggage stays in room - no hotel change needed",
                        special_stay=None,
                    )
                )
        return schedule

    schedule = []
    temp_len = len(matched_template)

    for d in range(1, total_days + 1):
        if d == total_days:
            schedule.append(
                HubScheduleItem(
                    day_number=d,
                    city=destination,
                    stay_area=f"Departure Airport (Hotel check-out completed in morning)",
                    is_city_transition=True,
                    luggage_instruction="Check out after breakfast; luggage in chauffeur cab until evening departure flight",
                    special_stay=None,
                )
            )
            continue

        template_idx = min(d - 1, temp_len - 2)
        item = matched_template[template_idx]
        city = str(item["city"])
        stay_area = str(item["stay_area"])
        special = item.get("special_stay")

        prev_city = schedule[-1].city if schedule else None
        is_transition = (prev_city != city) if prev_city is not None else True

        if special == "houseboat":
            luggage_note = "Check out from previous stay; board private luxury houseboat (cruise & overnight stay with all meals included)"
            stay_note = f"{stay_area} (All meals included on board)"
        elif is_transition:
            if d == 1:
                luggage_note = f"Arrive and check in to your hotel in {city}"
                stay_note = stay_area
            else:
                luggage_note = f"Morning check-out from {prev_city}, pack luggage into vehicle, transfer to {city} and check in to your new hotel"
                stay_note = f"Check-in to your new hotel in {stay_area}"
        else:
            luggage_note = f"Luggage stays in room - no hotel change needed"
            stay_note = f"Your hotel in {stay_area} (Luggage stays in room - no hotel change needed)"

        schedule.append(
            HubScheduleItem(
                day_number=d,
                city=city,
                stay_area=stay_note,
                is_city_transition=is_transition,
                luggage_instruction=luggage_note,
                special_stay=special,
            )
        )

    return schedule


def sanitize_markdown_text(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"-\s*\n-\s*", "- ", cleaned)
    cleaned = re.sub(r"-\s*Option\s*(\d+):\s*\*\s*", r"- **Option \1:** ", cleaned)
    cleaned = re.sub(r"-\s*Return Option\s*(\d+):\s*\*\s*", r"- **Return Option \1:** ", cleaned)
    cleaned = re.sub(r"\*\s*\*", "**", cleaned)
    cleaned = re.sub(r"~\s*\*", "", cleaned)
    cleaned = re.sub(r"\*~", "", cleaned)
    cleaned = re.sub(r"Total Trip Cost:\s*~\s*\*+", "Total Trip Cost: ~", cleaned)
    cleaned = re.sub(r"Total Trip Cost:\*+", "Total Trip Cost:", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
