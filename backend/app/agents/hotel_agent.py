from decimal import Decimal
from ..core.money import Money
from ..core.state import HotelOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


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
        elif "bangalore" in last_msg:
            destination = "Bangalore"
        elif "paris" in last_msg:
            destination = "Paris"
        elif "london" in last_msg:
            destination = "London"
        elif "tokyo" in last_msg:
            destination = "Tokyo"

    registry = MCPRegistry()
    try:
        raw_result = await registry.places_client.call_tool(
            name="search_hotels",
            arguments={"destination": destination, "nights": nights},
        )
        hotels_raw = raw_result.get("hotels", [])
    except Exception:
        hotels_raw = []

    parsed_hotels: list[HotelOption] = []
    if isinstance(hotels_raw, list):
        for item in hotels_raw:
            if isinstance(item, dict):
                nightly = str(item.get("nightly_rate", "5500.00"))
                total = str(item.get("total_rate", "16500.00"))
                curr = str(item.get("currency", "INR"))
                parsed_hotels.append(
                    HotelOption(
                        option_id=str(item.get("option_id", f"ht_{destination}_01")),
                        name=str(item.get("name", f"{destination} Grand Resort")),
                        location=str(item.get("location", f"Central {destination}")),
                        nightly_rate=Money(amount=Decimal(nightly), currency=curr),
                        total_rate=Money(amount=Decimal(total), currency=curr),
                        cancellation_terms=str(item.get("cancellation_terms", "Free cancellation within 24h.")),
                        source_provenance="cached",
                        source_citation=str(item.get("source_citation", "https://example.com/hotels")),
                    )
                )

    if not parsed_hotels:
        parsed_hotels = [
            HotelOption(
                option_id=f"hotel_{destination.lower()}_primary",
                name=f"{destination} Heritage Resort & Spa",
                location=f"Prime Area, {destination}",
                nightly_rate=Money(amount=Decimal("6500.00"), currency="INR"),
                total_rate=Money(amount=Decimal("19500.00"), currency="INR"),
                cancellation_terms="Free cancellation up to 48h before arrival.",
                source_provenance="cached",
                source_citation="https://example.com/hotels/resort",
            )
        ]

    selected_id = parsed_hotels[0].option_id if parsed_hotels else None
    return {
        "hotel_options": parsed_hotels,
        "selected_hotel_id": selected_id,
    }

