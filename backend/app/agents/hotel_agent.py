from decimal import Decimal
from ..core.money import Money
from ..core.state import HotelOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


HOTEL_CATALOG: dict[str, list[dict[str, object]]] = {
    "GOA": [
        {
            "tier": "comfort",
            "name": "Whispering Palms Beach Resort",
            "location": "Candolim, North Goa (300m to beach)",
            "nightly_rate": Decimal("5200.00"),
            "amenities": "Outdoor swimming pool, ayurvedic spa, multi-cuisine restaurant & bar, evening live music, sun deck.",
        },
        {
            "tier": "luxury",
            "name": "Taj Fort Aguada Resort & Spa",
            "location": "Sinquerim Beach, North Goa",
            "nightly_rate": Decimal("13500.00"),
            "amenities": "Clifftop ocean infinity pool, Jiva luxury spa, fine dining, tennis court, direct beach access.",
        },
        {
            "tier": "budget",
            "name": "BloomSuites Calangute",
            "location": "Calangute, North Goa (Central Market & Beach)",
            "nightly_rate": Decimal("3100.00"),
            "amenities": "Rooftop swimming pool, free high-speed Wi-Fi, air conditioning, buffet breakfast, 24/7 travel desk.",
        },
        {
            "tier": "south_heritage",
            "name": "Heritage Village Resort & Spa",
            "location": "Arossim / Cansaulim Beach, South Goa",
            "nightly_rate": Decimal("6800.00"),
            "amenities": "Portuguese boutique architecture, tranquil swimming pool, wellness spa, close to serene uncrowded beaches.",
        },
    ],
    "JAIPUR": [
        {
            "tier": "comfort",
            "name": "Shahpura House Heritage Hotel",
            "location": "Bani Park, Central Jaipur",
            "nightly_rate": Decimal("4800.00"),
            "amenities": "Traditional royal architecture, swimming pool, rooftop rooftop dining overlooking city, cultural dance shows.",
        },
        {
            "tier": "luxury",
            "name": "ITC Rajputana, Luxury Collection",
            "location": "Gopalbari, Jaipur",
            "nightly_rate": Decimal("11500.00"),
            "amenities": "Signature royal spa, grand pool, multiple fine-dining restaurants, poolside lounge, royal courtyards.",
        },
        {
            "tier": "budget",
            "name": "Umaid Bhawan - A Heritage Style Hotel",
            "location": "Bani Park, Jaipur",
            "nightly_rate": Decimal("2900.00"),
            "amenities": "Carved stone balconies, rooftop restaurant with city view, swimming pool, friendly travel tour desk.",
        },
    ],
    "MUMBAI": [
        {
            "tier": "comfort",
            "name": "Fariyas Hotel Colaba",
            "location": "Colaba, South Mumbai (5 mins to Gateway of India)",
            "nightly_rate": Decimal("6500.00"),
            "amenities": "Indoor swimming pool, fitness center, multi-cuisine restaurant, close to Colaba Causeway shops.",
        },
        {
            "tier": "luxury",
            "name": "The Taj Mahal Tower, Mumbai",
            "location": "Apollo Bunder, Colaba, Mumbai",
            "nightly_rate": Decimal("18500.00"),
            "amenities": "Iconic Arabian Sea views, luxury spa, outdoor pool, world-renowned heritage restaurants and high tea.",
        },
        {
            "tier": "budget",
            "name": "Hotel Suba Palace",
            "location": "Near Gateway of India, Colaba, Mumbai",
            "nightly_rate": Decimal("3800.00"),
            "amenities": "Modern boutique rooms, buffet breakfast, elevator, high-speed Wi-Fi, walking distance to monuments.",
        },
    ],
}


def get_default_catalog(dest: str) -> list[dict[str, object]]:
    clean = dest.upper().strip()
    for k, v in HOTEL_CATALOG.items():
        if k in clean or clean in k:
            return v

    return [
        {
            "tier": "comfort",
            "name": f"{dest} Grand Central Resort",
            "location": f"Central Downtown, {dest}",
            "nightly_rate": Decimal("5200.00"),
            "amenities": "Swimming pool, complimentary breakfast, fitness center, on-site multi-cuisine restaurant.",
        },
        {
            "tier": "luxury",
            "name": f"The Royal Palace & Spa {dest}",
            "location": f"Prime Waterfront / Landmark Area, {dest}",
            "nightly_rate": Decimal("12500.00"),
            "amenities": "Luxury wellness spa, infinity pool, valet parking, private balcony suites, concierge lounge.",
        },
        {
            "tier": "budget",
            "name": f"Bloom Hotel {dest}",
            "location": f"Transit & Market Hub, {dest}",
            "nightly_rate": Decimal("2900.00"),
            "amenities": "Clean air-conditioned rooms, free Wi-Fi, 24/7 reception desk, convenient local transit access.",
        },
    ]


async def hotel_agent_node(state: PlanMyTripState) -> dict[str, object]:
    destination = state.get("destination") or "Goa"
    nights = 3
    start_str = state.get("start_date")
    end_str = state.get("end_date")
    if start_str and end_str:
        try:
            from datetime import date
            d1 = date.fromisoformat(str(start_str))
            d2 = date.fromisoformat(str(end_str))
            diff = (d2 - d1).days
            if diff > 0:
                nights = diff
        except Exception:
            nights = 3

    messages = state.get("messages", [])
    if messages:
        last_msg = str(messages[-1].content).lower()
        if "goa" in last_msg:
            destination = "Goa"
        elif "mumbai" in last_msg:
            destination = "Mumbai"
        elif "delhi" in last_msg:
            destination = "Delhi"
        elif "jaipur" in last_msg:
            destination = "Jaipur"
        elif "bangalore" in last_msg:
            destination = "Bangalore"

    registry = MCPRegistry()
    raw_hotels: list[object] = []
    try:
        raw_result = await registry.places_client.call_tool(
            name="search_hotels",
            arguments={"destination": destination, "nights": nights},
        )
        res_hotels = raw_result.get("hotels", [])
        if isinstance(res_hotels, list):
            raw_hotels = res_hotels
    except Exception:
        raw_hotels = []

    parsed_hotels: list[HotelOption] = []
    if isinstance(raw_hotels, list):
        for item in raw_hotels:
            if isinstance(item, dict):
                nightly_str = str(item.get("nightly_rate", "5500.00"))
                curr = str(item.get("currency", "INR"))
                nightly_dec = Decimal(nightly_str)
                total_dec = nightly_dec * Decimal(str(nights))
                amenities = str(item.get("cancellation_terms", "Free cancellation within 24h. Outdoor pool, restaurant, Wi-Fi."))
                parsed_hotels.append(
                    HotelOption(
                        option_id=str(item.get("option_id", f"ht_{destination}_mcp")),
                        name=str(item.get("name", f"{destination} Grand Stay")),
                        location=str(item.get("location", f"Central {destination}")),
                        nightly_rate=Money(amount=nightly_dec, currency=curr),
                        total_rate=Money(amount=total_dec, currency=curr),
                        cancellation_terms=amenities,
                        source_provenance="cached",
                        source_citation=str(item.get("source_citation", "https://example.com/hotels")),
                    )
                )

    catalog = get_default_catalog(destination)
    for cat in catalog:
        nightly_dec = Decimal(str(cat["nightly_rate"]))
        total_dec = nightly_dec * Decimal(str(nights))
        tier_id = f"hotel_{destination.lower()}_{cat['tier']}"
        if not any(h.option_id == tier_id for h in parsed_hotels):
            parsed_hotels.append(
                HotelOption(
                    option_id=tier_id,
                    name=str(cat["name"]),
                    location=str(cat["location"]),
                    nightly_rate=Money(amount=nightly_dec, currency="INR"),
                    total_rate=Money(amount=total_dec, currency="INR"),
                    cancellation_terms=f"Activities & Amenities: {cat['amenities']}. Free cancellation up to 48 hours prior to check-in.",
                    source_provenance="cached",
                    source_citation="https://example.com/hotels/catalog",
                )
            )

    selected_id = parsed_hotels[0].option_id if parsed_hotels else None
    return {
        "hotel_options": parsed_hotels,
        "selected_hotel_id": selected_id,
    }
