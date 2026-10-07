from typing import Any
from ..core.state import PlanMyTripState
from ..mcp_client.registry import MCPRegistry


DESTINATION_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "GOA": {
        "zones": [
            {
                "zone_name": "North Goa (Beaches, Forts & Cafes)",
                "places": [
                    "Aguada Fort & Lighthouse (Panoramic Arabian Sea views)",
                    "Anjuna & Vagator Beaches (Sunset cliffs & coastal cafes)",
                    "Chapora Fort (Historic ramparts & sunset point)",
                    "Calangute & Baga Beach (Water sports & vibrant shacks)"
                ],
                "recommended_stay_area": "Candolim, Calangute, or Sinquerim",
                "stay_reason": "Centrally located in North Goa, keeps you within 15-20 minutes of all northern forts and beaches without traffic."
            },
            {
                "zone_name": "South Goa & Heritage (Peaceful Beaches, Churches & Falls)",
                "places": [
                    "Basilica of Bom Jesus & Se Cathedral (UNESCO Old Goa Heritage)",
                    "Colva & Benaulim White Sand Beaches",
                    "Cabo de Rama Fort & Palolem Beach (Scenic cliffs & quiet waters)",
                    "Dudhsagar Waterfalls day excursion"
                ],
                "recommended_stay_area": "Colva, Benaulim, or Cavelossim",
                "stay_reason": "South Goa is 40-50 km from North Goa. If spending full days here, switching to a South Goa beach resort saves 2-3 hours of daily travel."
            }
        ],
        "transit_guide": {
            "best_option": "Self-drive rental car or scooter",
            "car_rental_rate": "₹1,200 - ₹1,800 per day (Swift, Baleno, Thar)",
            "scooter_rental_rate": "₹400 - ₹500 per day (Activa / Jupiter)",
            "taxi_guidance": "GoaMiles app cabs or prepaid airport taxis (~₹1,200 - ₹1,500 for airport transfers). Hired private day cabs cost ~₹2,200 - ₹2,500 for 8 hours.",
            "easiest_way": "Rent a car or scooter directly upon arrival or hotel delivery for maximum flexibility across beaches."
        },
        "stay_strategy": "For a 2 to 3-day trip, stay at the same hotel in Candolim/Calangute to avoid repeated check-in/check-out hassle. If extending to 4+ days and exploring South Goa or Dudhsagar, consider splitting stay with a South Goa resort."
    },
    "JAIPUR": {
        "zones": [
            {
                "zone_name": "Old City & Royal Palaces",
                "places": [
                    "Hawa Mahal & City Palace (Royal courtyards & museum)",
                    "Jantar Mantar (Astronomical observatory)",
                    "Bapu Bazaar & Johari Bazaar (Handicrafts & jewelry)"
                ],
                "recommended_stay_area": "MI Road or C-Scheme",
                "stay_reason": "Close to the Walled City with top restaurants and easy walkability."
            },
            {
                "zone_name": "Amer & Hill Forts",
                "places": [
                    "Amer Fort (Elephant/jeep ride & Sheesh Mahal)",
                    "Jaigarh Fort (World's largest cannon on wheels)",
                    "Nahargarh Fort (Hilltop sunset overlooking Jaipur city)",
                    "Jal Mahal (Water palace photo stop)"
                ],
                "recommended_stay_area": "Kukas or Amer Road heritage resorts",
                "stay_reason": "Quiet royal palace hotels near the hills away from city bustle."
            }
        ],
        "transit_guide": {
            "best_option": "Uber / Ola or dedicated AC day cab",
            "car_rental_rate": "₹2,000 per day for full-day city cab with chauffeur",
            "scooter_rental_rate": "₹500 per day",
            "taxi_guidance": "Uber and Ola are readily available everywhere in Jaipur. Auto-rickshaws are abundant for short 2-3 km hops in the Old City.",
            "easiest_way": "Book a full-day Uber HIRE or local tourist taxi (~₹1,800 - ₹2,200) to cover Amer, Jaigarh, and Nahargarh comfortably."
        },
        "stay_strategy": "Stay at the same hotel in C-Scheme or Civil Lines for the entire duration as all city forts are within 25-35 minutes drive."
    },
    "MUMBAI": {
        "zones": [
            {
                "zone_name": "South Mumbai (Colaba, Marine Drive & Fort)",
                "places": [
                    "Gateway of India & Taj Mahal Palace Hotel",
                    "Marine Drive (Queen's Necklace promenade sunset)",
                    "Colaba Causeway shopping & Leopold Cafe",
                    "Chhatrapati Shivaji Maharaj Terminus (Victorian Gothic landmark)"
                ],
                "recommended_stay_area": "Colaba, Marine Drive, or Nariman Point",
                "stay_reason": "Heritage ambience with prime access to historical landmarks and sea breeze."
            },
            {
                "zone_name": "Bandra & Western Suburbs",
                "places": [
                    "Bandra Bandstand & Mount Mary Basilica",
                    "Linking Road & Hill Road fashion boutiques",
                    "Juhu Beach sunset and street food"
                ],
                "recommended_stay_area": "Bandra West, BKC, or Juhu",
                "stay_reason": "Near Mumbai nightlife, trendy cafes, and closer to airport."
            }
        ],
        "transit_guide": {
            "best_option": "Uber/Ola cabs and Mumbai Metro",
            "car_rental_rate": "₹2,500 - ₹3,000 per day with driver",
            "scooter_rental_rate": "Not recommended in heavy Mumbai traffic",
            "taxi_guidance": "Black-and-Yellow (Kaali-Peeli) metered cabs in South Mumbai, or Uber/Ola. The Mumbai Metro and Coastal Road make travel smooth.",
            "easiest_way": "Use Uber Premier or Ola for air-conditioned city transit avoiding local train peak crowds."
        },
        "stay_strategy": "Stay in South Mumbai (Colaba) for historical sightseeing, or near BKC/Bandra if you prefer quick airport connectivity and contemporary nightlife."
    }
}


def get_destination_cluster_data(destination: str) -> dict[str, Any]:
    dest_clean = destination.upper().strip()
    for key, data in DESTINATION_KNOWLEDGE.items():
        if key in dest_clean or dest_clean in key:
            return data

    return {
        "zones": [
            {
                "zone_name": f"Central & Historic {destination}",
                "places": [
                    f"Top landmark & architectural center of {destination}",
                    f"Historic old quarter and vibrant local markets",
                    f"Iconic viewpoint and cultural museum"
                ],
                "recommended_stay_area": f"Central {destination} or Downtown",
                "stay_reason": f"Offers walkable access to top monuments, dining, and central transport."
            },
            {
                "zone_name": f"Scenic Outskirts & Nature of {destination}",
                "places": [
                    f"Scenic hill / waterfront viewpoint overlooking {destination}",
                    f"Botanical gardens or nature sanctuary",
                    f"Traditional artisan village and craft center"
                ],
                "recommended_stay_area": f"Scenic Resort Zone, {destination}",
                "stay_reason": f"Peaceful environment with resort amenities for relaxation after city exploration."
            }
        ],
        "transit_guide": {
            "best_option": "App-based cabs (Uber/Ola) or rented private chauffeur cab",
            "car_rental_rate": "₹1,500 - ₹2,500 per day with driver",
            "scooter_rental_rate": "₹500 - ₹700 per day",
            "taxi_guidance": "Airport prepaid taxi counter upon arrival is reliable. Local cabs or ride-hailing for day-to-day transit.",
            "easiest_way": f"Hire a dedicated private day cab (~₹2,000/day) or self-drive vehicle for seamless sightseeing across {destination}."
        },
        "stay_strategy": f"For trips under 4 days, staying at the same central hotel in {destination} is recommended to maximize sightseeing time without checking in and out."
    }


async def places_agent_node(state: PlanMyTripState) -> dict[str, object]:
    destination = state.get("destination") or "Goa"
    messages = state.get("messages", [])
    if messages:
        last_msg = str(messages[-1].content).lower()
        if "goa" in last_msg:
            destination = "Goa"
        elif "mumbai" in last_msg:
            destination = "Mumbai"
        elif "jaipur" in last_msg:
            destination = "Jaipur"
        elif "delhi" in last_msg:
            destination = "Delhi"
        elif "bangalore" in last_msg:
            destination = "Bangalore"

    registry = MCPRegistry()
    mcp_places: list[dict[str, Any]] = []
    try:
        raw_result = await registry.places_client.call_tool(
            name="search_activities",
            arguments={"destination": destination},
        )
        activities_raw = raw_result.get("activities", [])
        if isinstance(activities_raw, list):
            for item in activities_raw:
                if isinstance(item, dict):
                    mcp_places.append(item)
    except Exception:
        mcp_places = []

    cluster_info = get_destination_cluster_data(destination)
    if mcp_places:
        cluster_info["live_mcp_activities"] = mcp_places

    return {
        "places_data": cluster_info,
    }
