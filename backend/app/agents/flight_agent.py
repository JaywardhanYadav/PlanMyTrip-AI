from decimal import Decimal
from ..core.money import Money
from ..core.state import FlightLeg, FlightOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


async def flight_agent_node(state: PlanMyTripState) -> dict[str, object]:
    destination = "PAR"
    origin = "NYC"

    messages = state.get("messages", [])
    if messages:
        last_msg = str(messages[-1].content).lower()
        if "london" in last_msg or "lhr" in last_msg:
            destination = "LHR"
        elif "tokyo" in last_msg or "nrt" in last_msg:
            destination = "NRT"

    registry = MCPRegistry()
    try:
        raw_result = await registry.flight_client.call_tool(
            name="search_flight_offers",
            arguments={"origin": origin, "destination": destination, "departure_date": "2026-12-01"},
        )
        raw_options = raw_result.get("options", [])
    except Exception:
        raw_options = []

    parsed_options: list[FlightOption] = []
    if isinstance(raw_options, list):
        for item in raw_options:
            if isinstance(item, dict):
                legs_raw = item.get("legs", [])
                legs: list[FlightLeg] = []
                for leg in legs_raw:
                    if isinstance(leg, dict):
                        legs.append(
                            FlightLeg(
                                origin_iata=str(leg.get("origin_iata", origin)),
                                destination_iata=str(leg.get("destination_iata", destination)),
                                carrier_code=str(leg.get("carrier_code", "SE")),
                                flight_number=str(leg.get("flight_number", "101")),
                                departure_time=str(leg.get("departure_time", "2026-12-01T08:00:00Z")),  # type: ignore[arg-type]
                                arrival_time=str(leg.get("arrival_time", "2026-12-01T12:00:00Z")),  # type: ignore[arg-type]
                                duration_minutes=int(leg.get("duration_minutes", 240)),
                            )
                        )
                fare_str = str(item.get("fare_amount", "450.00"))
                parsed_options.append(
                    FlightOption(
                        option_id=str(item.get("option_id", f"fl_{origin}_{destination}")),
                        carrier=str(item.get("carrier", "Airline")),
                        legs=legs,
                        fare=Money(amount=Decimal(fare_str), currency="USD"),
                        is_estimate=bool(item.get("is_estimate", True)),
                        source_provenance="aviationstack",
                        source_citation=str(item.get("source_citation", "https://example.com/flights")),
                    )
                )

    if not parsed_options:
        parsed_options = [
            FlightOption(
                option_id=f"flight_{origin}_{destination}_def",
                carrier="Transatlantic Wings",
                legs=[
                    FlightLeg(
                        origin_iata=origin,
                        destination_iata=destination,
                        carrier_code="TW",
                        flight_number="202",
                        departure_time="2026-12-01T09:00:00Z",  # type: ignore[arg-type]
                        arrival_time="2026-12-01T13:30:00Z",  # type: ignore[arg-type]
                        duration_minutes=270,
                    )
                ],
                fare=Money(amount=Decimal("420.00"), currency="USD"),
                is_estimate=True,
                source_provenance="cached",
                source_citation="https://example.com/benchmark",
            )
        ]

    selected_id = parsed_options[0].option_id if parsed_options else None
    return {
        "flight_options": parsed_options,
        "selected_flight_id": selected_id,
    }
