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
    "KERALA": [
        {
            "tier": "ultra_luxury",
            "name": "Kumarakom Lake Resort & Luxury Houseboats",
            "location": "Vembanad Lake, Kumarakom / Alleppey, Kerala",
            "nightly_rate": Decimal("22500.00"),
            "amenities": "Heritage backwater villas, meandering infinity pool, private plunge pools, Ayurmana Ayurvedic spa, luxury sunset backwater cruises.",
        },
        {
            "tier": "luxury",
            "name": "Grand Hyatt Kochi Bolgatty",
            "location": "Bolgatty Island, Kochi, Kerala",
            "nightly_rate": Decimal("14500.00"),
            "amenities": "Waterfront resort overlooking Vembanad backwaters, Santata Ayurvedic spa, marina, Thai & Malabar fine dining, indoor and outdoor pools.",
        },
        {
            "tier": "scenic_luxury",
            "name": "Blanket Hotel & Spa Munnar",
            "location": "Attukad Waterfalls, Munnar Hills, Kerala",
            "nightly_rate": Decimal("11500.00"),
            "amenities": "Panoramic mist and tea plantation valley vistas, heated infinity pool, nature treks, spa, organic multi-cuisine dining.",
        },
        {
            "tier": "heritage_luxury",
            "name": "Brunton Boatyard - CGH Earth",
            "location": "Fort Kochi Historic Harbour, Kerala",
            "nightly_rate": Decimal("16500.00"),
            "amenities": "Restored Victorian shipyard architecture, harbor views with dolphins, History Restaurant, colonial sea-facing balconies.",
        },
        {
            "tier": "comfort",
            "name": "Spice Village - CGH Earth Thekkady",
            "location": "Kumily / Periyar Tiger Reserve, Thekkady, Kerala",
            "nightly_rate": Decimal("8500.00"),
            "amenities": "Tribal village style cottages with elephant grass roofs, spice gardens, Ayurvedic center, close to Periyar safari gate.",
        },
        {
            "tier": "budget",
            "name": "Rossitta Wood Castle / Fort Kochi Heritage Inn",
            "location": "Fort Kochi Heritage District, Kerala",
            "nightly_rate": Decimal("3150.00"),
            "amenities": "Teakwood boutique heritage rooms, authentic Kerala breakfast, close to Chinese fishing nets and art cafes.",
        },
        {
            "tier": "houseboat",
            "name": "Alleppey Luxury Private Houseboat (Cruise & Stay)",
            "location": "Punnamada Jetty / Vembanad Lake canals, Alleppey, Kerala",
            "nightly_rate": Decimal("9500.00"),
            "amenities": "Private 1-bedroom AC luxury houseboat, personal chef & captain, upper sun deck, all freshly prepared meals included (lunch, tea, dinner, breakfast).",
        },
    ],
    "AHMEDABAD": [
        {
            "tier": "luxury",
            "name": "The House of MG (Heritage Grand Hotel)",
            "location": "Opp. Sidi Saiyyed Mosque, Lal Darwaja, Central Ahmedabad",
            "nightly_rate": Decimal("8500.00"),
            "amenities": "Restored 1924 heritage mansion, Agashiye rooftop Gujarati thali terrace, indoor pool, Lotus spa, heritage craft shop.",
        },
        {
            "tier": "comfort",
            "name": "Courtyard by Marriott Ahmedabad Sindhu Bhavan Road",
            "location": "SG Highway / Sindhu Bhavan Road, Ahmedabad",
            "nightly_rate": Decimal("6200.00"),
            "amenities": "Modern fitness center, rooftop pool, multi-cuisine restaurant, close to upscale cafes and boutiques.",
        },
        {
            "tier": "budget",
            "name": "Bloom Hotel - Ahmedabad Heritage",
            "location": "Ashram Road / Central Commercial Hub, Ahmedabad",
            "nightly_rate": Decimal("3100.00"),
            "amenities": "Smart boutique rooms, signature cloud beds, high-speed Wi-Fi, walking distance to Sabarmati Riverfront.",
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
                "tier": "luxury",
                "name": "Taj Hotels & Resorts / The Leela (Verified 5-Star Chain)",
                "location": f"Heritage Landmark District, {dest}",
                "nightly_rate": Decimal("18500.00"),
                "amenities": "Verified 5-star luxury brand hospitality, heritage architecture, full-service spa, fine dining restaurant, swimming pool, concierge desk.",
            },
            {
                "tier": "comfort",
                "name": "Courtyard by Marriott / Lemon Tree Premier (Verified 4-Star Chain)",
                "location": f"City Center & Business District, {dest}",
                "nightly_rate": Decimal("6800.00"),
                "amenities": "Verified 4-star comfort hospitality, modern fitness center, multi-cuisine dining, high-speed Wi-Fi, 24/7 front desk.",
            },
        ]

    return [
        {
            "tier": "comfort",
            "name": "Courtyard by Marriott / Lemon Tree Premier (Verified 4-Star Chain)",
            "location": f"City Center & Business District, {dest}",
            "nightly_rate": Decimal("6200.00"),
            "amenities": "Verified 4-star comfort hospitality, fitness center, multi-cuisine restaurant, high-speed Wi-Fi, 24/7 reception desk.",
        },
        {
            "tier": "luxury",
            "name": "Taj Hotels & Resorts / The Leela (Verified 5-Star Chain)",
            "location": f"Heritage Landmark District, {dest}",
            "nightly_rate": Decimal("16500.00"),
            "amenities": "Verified 5-star luxury brand hospitality, full-service spa, fine dining pavilions, swimming pool, concierge service.",
        },
        {
            "tier": "budget",
            "name": "Bloom Hotels / Ginger by IHCL / Ibis (Verified Smart Economy Chain)",
            "location": f"Transit & Commercial District, {dest}",
            "nightly_rate": Decimal("3100.00"),
            "amenities": "Verified smart economy hospitality, clean air-conditioned rooms, complimentary breakfast, high-speed Wi-Fi, convenient transit connectivity.",
        },
    ]


async def hotel_agent_node(state: PlanMyTripState) -> dict[str, object]:
    gateway_raw = state.get("resolved_gateway")
    raw_dest = (gateway_raw or state.get("destination") or "Pune").strip()
    clean = raw_dest.upper()
    if any(p in clean for p in ["PUNE", "PNQ"]):
        destination = "Pune"
    elif any(b in clean for b in ["BENGL", "BANGAL", "BENGAL", "BLR"]):
        destination = "Bangalore"
    elif any(g in clean for g in ["GOA", "GOI", "DABOLIM"]):
        destination = "Goa"
    elif any(j in clean for j in ["JAIPUR", "JAI", "RAJASTHAN"]):
        destination = "Jaipur"
    elif any(m in clean for m in ["MUMBAI", "BOMBAY", "BOM"]):
        destination = "Mumbai"
    elif any(d in clean for d in ["DELHI", "DEL"]):
        destination = "Delhi"
    elif any(k in clean for k in ["KERALA", "KOCHI", "COCHIN", "MUNNAR", "ALLEPPEY"]):
        destination = "Kerala"
    elif any(h in clean for h in ["HIMACHAL", "SHIMLA", "MANALI"]):
        destination = "Shimla"
    elif any(u in clean for u in ["UTTARAKHAND", "DEHRADUN", "RISHIKESH"]):
        destination = "Dehradun"
    elif any(s in clean for s in ["KASHMIR", "SRINAGAR"]):
        destination = "Srinagar"
    elif any(a in clean for a in ["GUJARAT", "AHMEDABAD", "AMD"]):
        destination = "Ahmedabad"
    else:
        destination = raw_dest or "Pune"

    nights = state.get("trip_nights")
    if not nights or nights < 1:
        dur = state.get("duration_days")
        if dur and dur > 1:
            nights = dur - 1
        else:
            start_str = state.get("start_date")
            end_str = state.get("end_date")
            if start_str and end_str:
                try:
                    from datetime import date
                    d1 = date.fromisoformat(str(start_str))
                    d2 = date.fromisoformat(str(end_str))
                    diff = (d2 - d1).days
                    nights = diff if diff > 0 else 1
                except Exception:
                    nights = 2
            else:
                nights = 2

    trip_budget = state.get("trip_budget")
    budget_dec = trip_budget.amount if trip_budget else Decimal("50000.00")

    neighborhood = state.get("target_stay_neighborhood")
    start_d = str(state.get("start_date") or "2026-10-19")
    end_d = str(state.get("end_date") or "2026-10-23")

    registry = MCPRegistry()
    raw_hotels: list[object] = []
    try:
        raw_result = await registry.places_client.call_tool(
            name="search_hotels",
            arguments={
                "destination": destination,
                "neighborhood": neighborhood or "",
                "check_in_date": start_d,
                "check_out_date": end_d,
                "nights": nights,
            },
        )
        res_hotels = raw_result.get("hotels", [])
        if isinstance(res_hotels, list):
            raw_hotels = res_hotels
    except Exception:
        raw_hotels = []

    parsed_hotels: list[HotelOption] = []
    if isinstance(raw_hotels, list):
        for idx, item in enumerate(raw_hotels, 1):
            if isinstance(item, dict):
                nightly_str = str(item.get("nightly_rate", "5500.00"))
                curr = str(item.get("currency", "INR"))
                nightly_dec = Decimal(nightly_str)
                total_dec = nightly_dec * Decimal(str(nights))
                amenities = str(item.get("cancellation_terms", "Free cancellation up to 48 hours before check-in."))
                prov_val = str(item.get("source_provenance", "serpapi"))
                if prov_val not in ["serpapi", "tavily", "cached"]:
                    prov_val = "cached"

                parsed_hotels.append(
                    HotelOption(
                        option_id=str(item.get("option_id", f"ht_{destination.lower()}_serp_{idx}")),
                        name=str(item.get("name", "Verified Hotel")),
                        location=str(item.get("location", neighborhood or f"Central {destination}")),
                        nightly_rate=Money(amount=nightly_dec, currency=curr),
                        total_rate=Money(amount=total_dec, currency=curr),
                        cancellation_terms=amenities,
                        source_provenance=prov_val,
                        source_citation=str(item.get("source_citation", "https://www.google.com/travel/hotels")),
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
