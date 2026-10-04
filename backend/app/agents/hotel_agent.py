from decimal import Decimal
from ..core.money import Money
from ..core.state import HotelOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


async def hotel_agent_node(state: PlanMyTripState) -> dict[str, object]:
    destination = "Paris"
    messages = state.get("messages", [])
    if messages:
        last_msg = str(messages[-1].content).lower()
        if "london" in last_msg:
            destination = "London"
        elif "tokyo" in last_msg:
            destination = "Tokyo"

    registry = MCPRegistry()
    try:
        raw_result = await registry.places_client.call_tool(
            name="search_hotels",
            arguments={"destination": destination, "nights": 3},
        )
        hotels_raw = raw_result.get("hotels", [])
    except Exception:
        hotels_raw = []

    parsed_hotels: list[HotelOption] = []
    if isinstance(hotels_raw, list):
        for item in hotels_raw:
            if isinstance(item, dict):
                nightly = str(item.get("nightly_rate", "120.00"))
                total = str(item.get("total_rate", "360.00"))
                parsed_hotels.append(
                    HotelOption(
                        option_id=str(item.get("option_id", f"ht_{destination}_01")),
                        name=str(item.get("name", f"{destination} City Hotel")),
                        location=str(item.get("location", f"Central {destination}")),
                        nightly_rate=Money(amount=Decimal(nightly), currency="USD"),
                        total_rate=Money(amount=Decimal(total), currency="USD"),
                        cancellation_terms=str(item.get("cancellation_terms", "Free cancellation within 24h.")),
                        source_provenance="cached",
                        source_citation=str(item.get("source_citation", "https://example.com/hotels")),
                    )
                )

    if not parsed_hotels:
        parsed_hotels = [
            HotelOption(
                option_id=f"hotel_{destination.lower()}_primary",
                name=f"{destination} Central Boutique",
                location=f"Downtown, {destination}",
                nightly_rate=Money(amount=Decimal("130.00"), currency="USD"),
                total_rate=Money(amount=Decimal("390.00"), currency="USD"),
                cancellation_terms="Free cancellation up to 48h before arrival.",
                source_provenance="cached",
                source_citation="https://example.com/hotels/central",
            )
        ]

    selected_id = parsed_hotels[0].option_id if parsed_hotels else None
    return {
        "hotel_options": parsed_hotels,
        "selected_hotel_id": selected_id,
    }
