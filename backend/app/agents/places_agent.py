from typing import Any
from ..core.state import PlanMyTripState
from ..mcp_client.registry import MCPRegistry


DESTINATION_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "BANGALORE": {
        "zones": [
            {
                "zone_name": "Central Heritage & Royal Enclaves",
                "places": [
                    "Bangalore Palace (Tudor-style royal estate with wooden carvings & courtyard)",
                    "Vidhana Soudha & Attara Kacheri (Majestic Neo-Dravidian architecture)",
                    "Cubbon Park (Bespoke bamboo groves & tree-lined walkways)",
                    "UB City & Lavelle Road (Luxury boutiques, open-air alfresco dining & rooftop lounges)"
                ],
                "recommended_stay_area": "Racecourse Road, Residency Road, or Old Airport Road",
                "stay_reason": "Central location offering convenient access to top heritage landmarks and upscale dining without prolonged transit."
            },
            {
                "zone_name": "Historic Gardens & Iconic Flavors",
                "places": [
                    "Lalbagh Botanical Garden (Famous Victorian Glass House & centuries-old bonsai collection)",
                    "Tipu Sultan's Summer Palace (Intricate teakwood architecture & museum)",
                    "Bull Temple & Basavanagudi heritage food trail (Vidyarthi Bhavan & traditional filter coffee)",
                    "National Gallery of Modern Art (Heritage colonial mansion housing premier art exhibits)"
                ],
                "recommended_stay_area": "Central Bengaluru Heritage Corridor",
                "stay_reason": "Puts you within 15-20 minutes of iconic parks, royal palaces, and traditional Bangalore breakfast hubs."
            }
        ],
        "transit_guide": {
            "best_option": "Chauffeur-driven private luxury cab or Uber Premier",
            "car_rental_rate": "₹3,500 - ₹5,000 per day for premium chauffeur sedan (Innova Crysta / Luxury vehicle)",
            "scooter_rental_rate": "₹500 - ₹700 per day",
            "taxi_guidance": "Kempegowda International Airport (BLR) is ~35 km from city center. Use the official prepaid airport taxi or Uber Premier (~₹1,200 - ₹1,500). Dedicated full-day chauffeur cabs cost ~₹2,200 - ₹3,500 for seamless city transit.",
            "easiest_way": "Book a dedicated private chauffeur cab for full-day travel to navigate Bengaluru comfortably with air-conditioning."
        },
        "stay_strategy": "For a 3-day couple vacation, staying at the same luxury 5-star hotel in Central Bengaluru (like The Leela Palace, The Taj West End, or ITC Gardenia) is ideal so you can indulge in spa treatments and fine dining without switching hotels."
    },
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
    },
    "PUNE": {
        "zones": [
            {
                "zone_name": "Historic Peshwa Heritage & Royal Palaces",
                "places": [
                    "Shaniwar Wada (Grand 18th-century Peshwa fort palace with historic fountains and ramparts)",
                    "Aga Khan Palace (Italian arches, tranquil gardens, and national Gandhi memorial)",
                    "Dagdusheth Halwai Ganpati Temple & Tulshibaug heritage craft market",
                    "Raja Dinkar Kelkar Museum (Historic 3-floor treasure trove of royal Maratha artifacts)"
                ],
                "recommended_stay_area": "Senapati Bapat Road, Shivajinagar, or Koregaon Park",
                "stay_reason": "Central location providing 10-15 minutes reach to major historic palaces, museums, and premier dining hubs."
            },
            {
                "zone_name": "Scenic Mountain Forts, Nature & Cafe Enclaves",
                "places": [
                    "Sinhagad Fort (Scenic mountain fortress, misty ridge trek & traditional pitla bhakri)",
                    "Khadakwasla Dam & Panshet Lake viewpoints (Lakeside breeze & sunset viewpoints)",
                    "Koregaon Park & Osho Teerth Zen Gardens (Lush bamboo walkways, German Bakery & artisan cafes)",
                    "Vetal Tekdi / ARAI Hill (Highest point in Pune with panoramic city sunrise vistas)"
                ],
                "recommended_stay_area": "Koregaon Park or Kalyani Nagar",
                "stay_reason": "Tree-lined boulevards with vibrant cafes, fine-dining restaurants, and relaxing boutique stays."
            }
        ],
        "transit_guide": {
            "best_option": "Dedicated chauffeur private cab (Ola/Uber Premier or rental cab)",
            "car_rental_rate": "₹2,200 - ₹3,500 per day for AC sedan/SUV with driver",
            "scooter_rental_rate": "₹450 - ₹650 per day",
            "taxi_guidance": "Pune International Airport (PNQ) is in Lohegaon (~10 km from city center). Prepaid airport taxis and Uber/Ola are readily available. For Sinhagad Fort, private day cabs are recommended due to steep hill ghats.",
            "easiest_way": "Book a full-day AC chauffeur cab (~₹2,500/day) for comfortable, hassle-free sightseeing across historic city zones and Sinhagad."
        },
        "stay_strategy": "For a 5-day trip, staying at a luxury hotel in Central Pune or Koregaon Park (like The Ritz-Carlton, JW Marriott, or Conrad Pune) gives you the best mix of luxury amenities, spa relaxation, and convenient access to all heritage spots and hill forts without switching hotels."
    }
}


def get_destination_cluster_data(destination: str) -> dict[str, Any]:
    dest_clean = destination.upper().strip()
    if any(b in dest_clean for b in ["BENGL", "BANGAL", "BENGAL", "BLR"]):
        return DESTINATION_KNOWLEDGE["BANGALORE"]
    elif any(p in dest_clean for p in ["PUNE", "PNQ"]):
        return DESTINATION_KNOWLEDGE["PUNE"]

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
            "easiest_way": f"Hire a dedicated private day cab (~₹2,000/day) or chauffeur vehicle for seamless sightseeing across {destination}."
        },
        "stay_strategy": f"For trips under 4 days, staying at the same central hotel in {destination} is recommended to maximize sightseeing time without checking in and out."
    }


async def places_agent_node(state: PlanMyTripState) -> dict[str, object]:
    raw_dest = (state.get("destination") or "Pune").strip()
    clean = raw_dest.upper()
    if any(p in clean for p in ["PUNE", "PNQ"]):
        destination = "Pune"
    elif any(b in clean for b in ["BENGL", "BANGAL", "BENGAL", "BLR"]):
        destination = "Bangalore"
    elif any(g in clean for g in ["GOA", "GOI", "DABOLIM"]):
        destination = "Goa"
    elif any(j in clean for j in ["JAIPUR", "JAI"]):
        destination = "Jaipur"
    elif any(m in clean for m in ["MUMBAI", "BOMBAY", "BOM"]):
        destination = "Mumbai"
    elif any(d in clean for d in ["DELHI", "DEL"]):
        destination = "Delhi"
    else:
        destination = raw_dest or "Pune"

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
