from decimal import Decimal
from ..core.money import Money
from ..core.state import HotelOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


HOTEL_CATALOG: dict[str, list[dict[str, object]]] = {
    "BANGALORE": [
        {
            "tier": "ultra_luxury",
            "name": "The Leela Palace Bengaluru",
            "location": "Old Airport Road, Bengaluru",
            "nightly_rate": Decimal("24500.00"),
            "amenities": "Grand royal palace architecture, 7 acres of private gardens, award-winning spa, maharaja suites, signature dining at Jamavar and Citrus.",
        },
        {
            "tier": "heritage_luxury",
            "name": "The Taj West End, Bengaluru",
            "location": "Racecourse Road, Central Bengaluru",
            "nightly_rate": Decimal("19500.00"),
            "amenities": "20-acre heritage tropical sanctuary, open-air garden pavilions, Jiva luxury spa, legendary Karavalli coastal restaurant.",
        },
        {
            "tier": "business_luxury",
            "name": "ITC Gardenia, Luxury Collection",
            "location": "Residency Road, Central Bengaluru",
            "nightly_rate": Decimal("16500.00"),
            "amenities": "Wind-cooled green architecture, Kaya Kalp luxury spa, rooftop infinity pool, signature Edo Japanese & Kebabs & Kurries dining.",
        },
        {
            "tier": "comfort",
            "name": "Courtyard by Marriott Bengaluru Hebbal",
            "location": "Hebbal / Outer Ring Road, Bengaluru",
            "nightly_rate": Decimal("6500.00"),
            "amenities": "Rooftop swimming pool overlooking Nagavara lake, modern fitness center, multi-cuisine restaurant, close to airport highway.",
        },
        {
            "tier": "budget",
            "name": "BloomSuites Indiranagar",
            "location": "100ft Road, Indiranagar, Bengaluru",
            "nightly_rate": Decimal("3200.00"),
            "amenities": "Boutique smart rooms, high-speed Wi-Fi, air conditioning, buffet breakfast, surrounded by trendy cafes and boutiques.",
        },
    ],
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
            "nightly_rate": Decimal("14500.00"),
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
            "amenities": "Traditional royal architecture, swimming pool, rooftop dining overlooking city, cultural dance shows.",
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
            "name": "The Taj Mahal Palace, Mumbai",
            "location": "Apollo Bunder, Colaba, Mumbai",
            "nightly_rate": Decimal("26500.00"),
            "amenities": "Iconic Arabian Sea views, heritage palace wing, luxury spa, outdoor pool, world-renowned heritage restaurants and high tea.",
        },
        {
            "tier": "budget",
            "name": "Hotel Suba Palace",
            "location": "Near Gateway of India, Colaba, Mumbai",
            "nightly_rate": Decimal("3800.00"),
            "amenities": "Modern boutique rooms, buffet breakfast, elevator, high-speed Wi-Fi, walking distance to monuments.",
        },
    ],
    "PUNE": [
        {
            "tier": "ultra_luxury",
            "name": "The Ritz-Carlton, Pune",
            "location": "Golf Course Road, Yerwada, Pune",
            "nightly_rate": Decimal("21500.00"),
            "amenities": "Panoramic Poona Club golf course views, lavish wellness spa, rooftop Aish fine dining, signature suites.",
        },
        {
            "tier": "luxury",
            "name": "JW Marriott Hotel Pune",
            "location": "Senapati Bapat Road, Central Pune",
            "nightly_rate": Decimal("15500.00"),
            "amenities": "Iconic luxury city hotel, outdoor heated pool, Quan Spa, Paasha rooftop lounge, premium dining.",
        },
        {
            "tier": "luxury",
            "name": "Conrad Pune - Luxury by Hilton",
            "location": "Mangaldas Road, Koregaon Park, Pune",
            "nightly_rate": Decimal("16500.00"),
            "amenities": "Art-deco inspired architecture, temperature-controlled pool, signature Coriander Kitchen & Koji Asian dining.",
        },
        {
            "tier": "comfort",
            "name": "Hyatt Pune",
            "location": "Kalyani Nagar (near Aga Khan Palace), Pune",
            "nightly_rate": Decimal("6200.00"),
            "amenities": "Lush garden poolside dining, outdoor pool, modern fitness center, serene spa, close to Koregaon Park.",
        },
        {
            "tier": "budget",
            "name": "Bloom Hotel - Koregaon Park",
            "location": "Koregaon Park, Pune",
            "nightly_rate": Decimal("3200.00"),
            "amenities": "Modern boutique rooms, high-speed Wi-Fi, cloud beds, walking distance to cafes and Osho garden.",
        },
    ],
}


def get_default_catalog(dest: str, budget: Decimal) -> list[dict[str, object]]:
    clean = dest.upper().strip()
    for k, v in HOTEL_CATALOG.items():
        if k in clean or clean in k:
            if budget >= Decimal("200000.00"):
                return [h for h in v if str(h.get("tier")) in ["ultra_luxury", "heritage_luxury", "business_luxury", "luxury", "comfort"]]
            return v

    if budget >= Decimal("200000.00"):
        return [
            {
                "tier": "ultra_luxury",
                "name": f"The Grand Palace & Spa, {dest}",
                "location": f"Prime Central District, {dest}",
                "nightly_rate": Decimal("22000.00"),
                "amenities": "5-star luxury wellness spa, private butler service, infinity pool, premier dining pavilions, luxury suites.",
            },
            {
                "tier": "heritage_luxury",
                "name": f"Taj Heritage Sanctuary, {dest}",
                "location": f"Exclusive Landmark Enclave, {dest}",
                "nightly_rate": Decimal("18000.00"),
                "amenities": "Lush estate gardens, gourmet dining, signature spa, private pool access, concierge chauffeur.",
            },
            {
                "tier": "comfort",
                "name": f"Marriott Executive Suites, {dest}",
                "location": f"City Centre, {dest}",
                "nightly_rate": Decimal("7500.00"),
                "amenities": "Rooftop swimming pool, 24/7 fitness club, executive lounge, complimentary buffet breakfast.",
            },
        ]

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
            "name": f"The Royal Landmark Hotel {dest}",
            "location": f"Prime Landmark Area, {dest}",
            "nightly_rate": Decimal("12500.00"),
            "amenities": "Luxury wellness spa, pool, valet parking, private balcony suites, concierge lounge.",
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

    trip_budget = state.get("trip_budget")
    budget_dec = trip_budget.amount if trip_budget else Decimal("50000.00")

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
                        option_id=str(item.get("option_id", f"ht_{destination.lower()}_mcp")),
                        name=str(item.get("name", f"{destination} Grand Stay")),
                        location=str(item.get("location", f"Central {destination}")),
                        nightly_rate=Money(amount=nightly_dec, currency=curr),
                        total_rate=Money(amount=total_dec, currency=curr),
                        cancellation_terms=amenities,
                        source_provenance="cached",
                        source_citation=str(item.get("source_citation", "https://example.com/hotels")),
                    )
                )

    catalog = get_default_catalog(destination, budget_dec)
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
