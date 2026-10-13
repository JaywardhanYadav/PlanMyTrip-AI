from decimal import Decimal
import re
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class HubScheduleItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    day_number: int
    city: str
    stay_area: str
    is_city_transition: bool
    luggage_instruction: str
    day_theme: str
    morning: str
    afternoon: str
    evening: str
    special_stay: str | None = None


CIRCUIT_HUB_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "KERALA": [
        {
            "city": "Kochi",
            "stay_area": "Fort Kochi or Bolgatty Island waterfront, Kochi",
            "day_theme": "Arrival, Colonial Coastline & Cultural Heritage",
            "morning": "Arrive at Cochin International Airport (COK). Meet your private chauffeur and transfer to your heritage hotel in Fort Kochi. Check-in and freshen up.",
            "afternoon": "Explore Fort Kochi: Walk past iconic Chinese Fishing Nets, stroll along the harbor promenade, and savor fresh coastal seafood lunch.",
            "evening": "Visit St. Francis Church and attend a classical Kathakali dance and Kalaripayattu martial arts show at Kerala Kathakali Centre followed by dinner.",
            "special_stay": None,
        },
        {
            "city": "Kochi",
            "stay_area": "Fort Kochi or Bolgatty Island waterfront, Kochi",
            "day_theme": "Mattancherry Palaces, Jew Town & Spice Bazaars",
            "morning": "Visit Mattancherry Dutch Palace with historic murals, and explore Paradesi Synagogue in historic Jew Town.",
            "afternoon": "Stroll through aromatic spice markets and antique warehouses; lunch at a local heritage cafe.",
            "evening": "Sunset harbor cruise on Kochi backwaters followed by waterfront dinner overlooking the illuminated shipping channel.",
            "special_stay": None,
        },
        {
            "city": "Munnar",
            "stay_area": "Munnar Tea Valley or Pallivasal hill resort, Munnar",
            "day_theme": "Ascent to Munnar Hills & Tea Plantations",
            "morning": "Check out from Fort Kochi hotel; picturesque drive (~4 hrs) ascending the misty Western Ghats past Cheeyappara Waterfalls.",
            "afternoon": "Arrive in Munnar, check in to your hillside tea valley resort, and enjoy lunch surrounded by tea gardens.",
            "evening": "Tour the Tata Tea Museum and Lockhart Tea Estate for tea processing insights and fresh estate tea tasting.",
            "special_stay": None,
        },
        {
            "city": "Munnar",
            "stay_area": "Munnar Tea Valley or Pallivasal hill resort, Munnar",
            "day_theme": "Eravikulam National Park & Waterfalls",
            "morning": "Early morning safari into Eravikulam National Park to spot endangered Nilgiri Tahr and take in panoramic Anamudi Peak vistas.",
            "afternoon": "Visit Mattupetty Dam and enjoy serene boating on Kundala Lake surrounded by eucalyptus woods; local lunch.",
            "evening": "Visit picturesque Attukad Waterfalls for scenic sunset photo stops; dinner at your resort.",
            "special_stay": None,
        },
        {
            "city": "Thekkady",
            "stay_area": "Kumily / Periyar Wildlife Gateway retreat, Thekkady",
            "day_theme": "Periyar Spice Plantations & Wildlife Gateway",
            "morning": "Check out from Munnar; scenic winding drive (~3 hrs) through cardamom hills to Thekkady (Kumily).",
            "afternoon": "Check in to your spice valley resort; guided walking tour through Abraham's Spice Garden learning about pepper, cinnamon, and vanilla.",
            "evening": "Experience live traditional martial arts at Kadathanadan Kalari Centre followed by authentic Kerala dinner.",
            "special_stay": None,
        },
        {
            "city": "Thekkady",
            "stay_area": "Kumily / Periyar Wildlife Gateway retreat, Thekkady",
            "day_theme": "Periyar Lake Boat Safari & Forest Walks",
            "morning": "Early morning boat safari on Periyar Lake inside the tiger reserve for wild elephant, bison, and waterbird sightings.",
            "afternoon": "Guided forest nature trail with eco-guides; leisurely lunch at a local spice restaurant.",
            "evening": "Relax with an authentic Ayurvedic rejuvenation therapy at your resort spa followed by quiet dinner.",
            "special_stay": None,
        },
        {
            "city": "Alleppey",
            "stay_area": "Private Luxury Houseboat on Vembanad Lake canals, Alleppey",
            "day_theme": "Private Luxury Houseboat Cruise & Overnight Stay",
            "morning": "Check out from Thekkady; drive down (~4 hrs) to Alleppey backwater boat jetty.",
            "afternoon": "Board your private luxury AC houseboat; glide through palm-fringed backwaters while enjoying freshly cooked Karimeen fish lunch on board.",
            "evening": "Anchor amidst tranquil waters; watch rural village life along the canals, savor evening tea and snacks, and enjoy traditional candlelight dinner on board.",
            "special_stay": "houseboat",
        },
        {
            "city": "Kochi",
            "stay_area": "Departure Airport / Cochin (COK)",
            "day_theme": "Disembarkation, Kumarakom & Departure",
            "morning": "Sunrise cruise on the backwaters with breakfast on board. Disembark houseboat at boat jetty.",
            "afternoon": "Chauffeur transfer (~1.5 hrs) to Cochin International Airport (COK) with optional craft shopping stop.",
            "evening": "Board scheduled return flight back to Pune, concluding your 8-day Kerala vacation.",
            "special_stay": None,
        },
    ],
    "RAJASTHAN": [
        {
            "city": "Jaipur",
            "stay_area": "MI Road or C-Scheme Heritage Hotel, Jaipur",
            "day_theme": "Arrival, Walled City & Royal Palaces",
            "morning": "Arrive in Jaipur at Jaipur International Airport (JAI), transfer to hotel. Check-in, freshen up, and enjoy breakfast.",
            "afternoon": "Explore the UNESCO Walled City: Visit Hawa Mahal (Palace of Winds) and City Palace royal courtyards and museum.",
            "evening": "Stroll through colorful Johari Bazaar and Bapu Bazaar followed by traditional Rajasthani thali dinner.",
            "special_stay": None,
        },
        {
            "city": "Jaipur",
            "stay_area": "MI Road or C-Scheme Heritage Hotel, Jaipur",
            "day_theme": "Amer Royal Citadel & Heritage Forts",
            "morning": "Ascend to majestic Amer Fort; explore the glittering Sheesh Mahal mirror palace, Diwan-e-Khas, and ramparts.",
            "afternoon": "Scenic photo-stop at Jal Mahal water palace on Man Sagar Lake; lunch at a renowned heritage restaurant.",
            "evening": "Cultural evening at Chokhi Dhani with traditional folk dance, puppet shows, and authentic Rajasthani feast.",
            "special_stay": None,
        },
        {
            "city": "Jaipur",
            "stay_area": "MI Road or C-Scheme Heritage Hotel, Jaipur",
            "day_theme": "Hilltop Forts & Sunset Panoramas",
            "morning": "Ascend to Jaigarh Fort to view the massive Jaivana cannon and ancient underground royal armory.",
            "afternoon": "Visit royal cenotaphs at Gaitore; relaxed lunch at a rooftop cafe overlooking the Pink City.",
            "evening": "Spectacular sunset vistas over Jaipur from the high ramparts of Nahargarh Fort followed by dinner.",
            "special_stay": None,
        },
        {
            "city": "Jodhpur",
            "stay_area": "Old City or Ratanada Heritage Haveli, Jodhpur",
            "day_theme": "Journey to Jodhpur: The Blue City",
            "morning": "Check out from Jaipur hotel; scenic chauffeur drive across the Marwar plains to Jodhpur (~5 hrs).",
            "afternoon": "Arrive in Jodhpur, check in to your heritage haveli, and enjoy lunch with a view of the fortress.",
            "evening": "Explore the historic Toorji Ka Jhalra stepwell, Clock Tower (Ghanta Ghar), and bustling Sardar Market blue alleys.",
            "special_stay": None,
        },
        {
            "city": "Jodhpur",
            "stay_area": "Old City or Ratanada Heritage Haveli, Jodhpur",
            "day_theme": "Mehrangarh Citadel & Royal Cenotaphs",
            "morning": "Tour the imposing Mehrangarh Fort towering 400 feet above the Blue City; visit its royal palanquin and weapon galleries.",
            "afternoon": "Visit the peaceful white marble memorial of Jaswant Thada and Umaid Bhawan Palace museum.",
            "evening": "Stroll through the lush gardens and historic pavilions of Mandore Gardens; dinner with fort views.",
            "special_stay": None,
        },
        {
            "city": "Udaipur",
            "stay_area": "Lake Pichola waterfront resort, Udaipur",
            "day_theme": "Ranakpur Marble Wonders & Udaipur Arrival",
            "morning": "Check out from Jodhpur; drive through the Aravalli hills to Udaipur with an excursion to Ranakpur Jain Temple (1444 carved pillars).",
            "afternoon": "Arrive in Udaipur, the City of Lakes; check in to your Lake Pichola resort and relax.",
            "evening": "Sunset boat cruise on Lake Pichola past the illuminated Lake Palace and Jag Mandir; lakeside dinner.",
            "special_stay": None,
        },
        {
            "city": "Udaipur",
            "stay_area": "Lake Pichola waterfront resort, Udaipur",
            "day_theme": "City Palace & Lakeside Heritage",
            "morning": "Tour the grand City Palace Udaipur, exploring the crystal gallery, peacock courtyards, and museum.",
            "afternoon": "Visit historic Jagdish Temple; enjoy lunch at a terrace cafe with panoramic lake views.",
            "evening": "Attend the vibrant Dharohar folk dance and puppet show at Bagore Ki Haveli right by the water at Gangaur Ghat.",
            "special_stay": None,
        },
        {
            "city": "Udaipur",
            "stay_area": "Lake Pichola waterfront resort, Udaipur",
            "day_theme": "Royal Gardens & Monsoon Palace Sunset",
            "morning": "Walk through the serene fountains and marble pavilions of Saheliyon Ki Bari and Nehru Park on Fateh Sagar Lake.",
            "afternoon": "Lunch at a lakeside restaurant; browse vibrant Rajasthani miniature paintings and silver jewelry.",
            "evening": "Drive up to Sajjangarh Monsoon Palace for a breathtaking sunset over the Aravalli hills; farewell dinner.",
            "special_stay": None,
        },
        {
            "city": "Udaipur",
            "stay_area": "Maharana Pratap Airport Udaipur (UDR)",
            "day_theme": "Departure from Udaipur Airport",
            "morning": "Leisurely breakfast overlooking Lake Pichola. Check-out and last-minute handicraft shopping.",
            "afternoon": "Private transfer to Maharana Pratap Airport Udaipur (UDR) for scheduled return flight to Pune.",
            "evening": "Board flight from Udaipur to Pune, concluding your royal 9-day journey.",
            "special_stay": None,
        },
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
                        day_theme="Arrival, Check-in & Scenic Relaxation",
                        morning=f"Arrival in {destination}, private airport cab transfer to hotel.",
                        afternoon="Hotel check-in, unpack, freshen up, and enjoy a relaxed local lunch.",
                        evening="Leisurely stroll through local promenade or hotel lounge followed by dinner.",
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
                        day_theme="Morning Bazaars, Wrap-Up & Return Journey",
                        morning="Leisurely breakfast, check-out, and final souvenir shopping at local markets.",
                        afternoon="Lunch at a renowned cafe followed by cab transfer to airport departure terminal.",
                        evening="Board scheduled evening return flight home.",
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
                        day_theme=f"Exploring Highlights of {destination} (Day {d})",
                        morning=f"Morning visit to top landmarks and heritage sites in {destination}.",
                        afternoon="Relish authentic regional cuisine and local delicacies for lunch.",
                        evening="Sunset viewing, vibrant evening promenades, and dinner at a top restaurant.",
                        special_stay=None,
                    )
                )
        return schedule

    schedule = []
    temp_len = len(matched_template)

    for d in range(1, total_days + 1):
        if d == total_days:
            last_item = matched_template[-1]
            last_city = str(last_item["city"])
            schedule.append(
                HubScheduleItem(
                    day_number=d,
                    city=last_city,
                    stay_area=f"Departure Airport (Hotel check-out completed in morning)",
                    is_city_transition=True,
                    luggage_instruction="Check out after breakfast; luggage in chauffeur cab until departure flight",
                    day_theme=str(last_item.get("day_theme", "Departure & Return Journey")),
                    morning=str(last_item.get("morning", "Leisurely breakfast, check-out, and last-minute shopping.")),
                    afternoon=str(last_item.get("afternoon", "Chauffeur transfer to departure airport.")),
                    evening=str(last_item.get("evening", "Board return flight home.")),
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
            luggage_note = "Luggage stays in room - no hotel change needed"
            stay_note = f"Your hotel in {stay_area} (Luggage stays in room - no hotel change needed)"

        schedule.append(
            HubScheduleItem(
                day_number=d,
                city=city,
                stay_area=stay_note,
                is_city_transition=is_transition,
                luggage_instruction=luggage_note,
                day_theme=str(item.get("day_theme", f"Exploring {city}")),
                morning=str(item.get("morning", f"Morning sightseeing in {city}.")),
                afternoon=str(item.get("afternoon", f"Lunch and afternoon exploration in {city}.")),
                evening=str(item.get("evening", f"Evening relaxation and dinner in {city}.")),
                special_stay=special,
            )
        )

    return schedule


def sanitize_markdown_text(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"(?m)^\s*#+\s*", "", cleaned)
    cleaned = re.sub(r"-\s*\n+-\s*", "- ", cleaned)
    cleaned = re.sub(r"\n+-\s*\n+", "\n", cleaned)
    cleaned = re.sub(r"(?m)^(?:\s*-\s*)?(?!\*\*Return Option\s*\d+:\*\*)\*?Return Option\s*(\d+):(?:\s*\*)?\s*", r"- **Return Option \1:** ", cleaned)
    cleaned = re.sub(r"(?m)^(?:\s*-\s*)?(?!\*\*Option\s*\d+:\*\*)\*?Option\s*(\d+):(?:\s*\*)?\s*", r"- **Option \1:** ", cleaned)
    cleaned = re.sub(r"~\s*\*", "", cleaned)
    cleaned = re.sub(r"\*~", "", cleaned)
    cleaned = re.sub(r"~\s*~+", "~", cleaned)
    cleaned = re.sub(r"\*₹", "₹", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
