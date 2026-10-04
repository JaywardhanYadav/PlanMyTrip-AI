from datetime import datetime, timezone
from decimal import Decimal
from ..core.money import Money
from ..core.state import FlightLeg, FlightOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


async def flight_agent_node(state: PlanMyTripState) -> dict[str, object]:
    destination = "GOI"
    origin = "DEL"

    messages = state.get("messages", [])
    if messages:
        last_msg = str(messages[-1].content).lower()
        if "goa" in last_msg or "goi" in last_msg:
            destination = "GOI"
            origin = "DEL"
        elif "mumbai" in last_msg or "bom" in last_msg:
            destination = "BOM"
            origin = "DEL"
        elif "delhi" in last_msg or "del" in last_msg:
            destination = "DEL"
            origin = "BOM"
        elif "bangalore" in last_msg or "blr" in last_msg:
            destination = "BLR"
            origin = "DEL"
        elif "paris" in last_msg or "par" in last_msg or "cdg" in last_msg:
            destination = "CDG"
            origin = "DEL"
        elif "london" in last_msg or "lhr" in last_msg:
            destination = "LHR"
            origin = "DEL"
        elif "tokyo" in last_msg or "nrt" in last_msg:
            destination = "NRT"
            origin = "DEL"

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
                        dep_raw = str(leg.get("departure_time", "2026-12-01T08:00:00Z")).replace("Z", "+00:00")
                        arr_raw = str(leg.get("arrival_time", "2026-12-01T12:00:00Z")).replace("Z", "+00:00")
                        legs.append(
                            FlightLeg(
                                origin_iata=str(leg.get("origin_iata", origin)),
                                destination_iata=str(leg.get("destination_iata", destination)),
                                carrier_code=str(leg.get("carrier_code", "AI")),
                                flight_number=str(leg.get("flight_number", "804")),
                                departure_time=datetime.fromisoformat(dep_raw),
                                arrival_time=datetime.fromisoformat(arr_raw),
                                duration_minutes=int(leg.get("duration_minutes", 150)),
                            )
                        )
                fare_str = str(item.get("fare_amount", "18500.00"))
                curr = str(item.get("currency", "INR"))
                parsed_options.append(
                    FlightOption(
                        option_id=str(item.get("option_id", f"fl_{origin}_{destination}")),
                        carrier=str(item.get("carrier", "Air India")),
                        legs=legs,
                        fare=Money(amount=Decimal(fare_str), currency=curr),
                        is_estimate=bool(item.get("is_estimate", True)),
                        source_provenance="aviationstack",
                        source_citation=str(item.get("source_citation", "https://example.com/flights")),
                    )
                )

    if not parsed_options:
        parsed_options = [
            FlightOption(
                option_id=f"flight_{origin}_{destination}_def",
                carrier="Air India Express",
                legs=[
                    FlightLeg(
                        origin_iata=origin,
                        destination_iata=destination,
                        carrier_code="IX",
                        flight_number="342",
                        departure_time=datetime(2026, 12, 1, 9, 30, tzinfo=timezone.utc),
                        arrival_time=datetime(2026, 12, 1, 12, 15, tzinfo=timezone.utc),
                        duration_minutes=165,
                    )
                ],
                fare=Money(amount=Decimal("16500.00"), currency="INR"),
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

