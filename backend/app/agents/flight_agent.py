import re
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import cast, Literal
from typing_extensions import TypedDict
from ..core.money import Money
from ..core.state import FlightLeg, FlightOption, PlanMyTripState
from ..mcp_client.registry import MCPRegistry


class ScheduleTemplate(TypedDict):
    id_suffix: str
    carrier: str
    carrier_code: str
    departure_window: str
    dep_time: time
    arr_time: time
    duration: int
    unit_fare: Decimal


def resolve_iata(name: str | None, default: str) -> str:
    if not name:
        return default
    clean = name.upper()

    paren_match = re.search(r"\(([A-Z]{3})\)", clean)
    if paren_match:
        return paren_match.group(1)

    mapping = {
        "BLR": "BLR", "BANGALORE": "BLR", "BENGALURU": "BLR", "BENGLORE": "BLR",
        "DEL": "DEL", "DELHI": "DEL", "NEW DELHI": "DEL",
        "BOM": "BOM", "MUMBAI": "BOM", "BOMBAY": "BOM",
        "GOI": "GOI", "GOA": "GOI", "GOX": "GOX", "DABOLIM": "GOI", "MOPA": "GOX",
        "CCU": "CCU", "KOLKATA": "CCU", "CALCUTTA": "CCU",
        "HYD": "HYD", "HYDERABAD": "HYD",
        "MAA": "MAA", "CHENNAI": "MAA", "MADRAS": "MAA",
        "JAI": "JAI", "JAIPUR": "JAI", "RAJASTHAN": "JAI",
        "PNQ": "PNQ", "PUNE": "PNQ",
        "COK": "COK", "KOCHI": "COK", "COCHIN": "COK", "KERALA": "COK",
        "TRV": "TRV", "TRIVANDRUM": "TRV", "THIRUVANANTHAPURAM": "TRV",
        "UDR": "UDR", "UDAIPUR": "UDR",
        "AMD": "AMD", "AHMEDABAD": "AMD",
        "IXC": "IXC", "CHANDIGARH": "IXC", "HIMACHAL": "IXC", "SHIMLA": "IXC", "MANALI": "IXC",
        "DED": "DED", "DEHRADUN": "DED", "UTTARAKHAND": "DED", "RISHIKESH": "DED",
        "SXR": "SXR", "SRINAGAR": "SXR", "KASHMIR": "SXR",
        "IXL": "IXL", "LEH": "IXL", "LADAKH": "IXL",
        "CDG": "CDG", "PARIS": "CDG",
        "LHR": "LHR", "LONDON": "LHR",
        "NRT": "NRT", "TOKYO": "NRT",
    }
    for k, v in mapping.items():
        if k in clean:
            return v
    return default


def parse_or_default_date(d_str: str | None, fallback: date) -> date:
    if not d_str:
        return fallback
    try:
        return datetime.strptime(d_str[:10], "%Y-%m-%d").date()
    except Exception:
        return fallback


async def flight_agent_node(state: PlanMyTripState) -> dict[str, object]:
    gateway_raw = state.get("resolved_gateway")
    raw_dest = (gateway_raw or state.get("destination") or "Pune").strip()
    raw_dep = (state.get("departure_station") or "Mumbai").strip()

    destination = resolve_iata(raw_dest, "PNQ")
    origin = resolve_iata(raw_dep, "BOM")

    if origin == destination:
        origin = "BOM" if destination != "BOM" else "DEL"

    travelers = state.get("travelers_count") or 1
    if travelers < 1:
        travelers = 1

    dep_date_obj = parse_or_default_date(state.get("start_date"), date(2026, 12, 1))
    ret_date_obj = parse_or_default_date(state.get("end_date"), date(2026, 12, 4))

    registry = MCPRegistry()
    raw_options: list[object] = []
    try:
        raw_result = await registry.flight_client.call_tool(
            name="search_flight_offers",
            arguments={"origin": origin, "destination": destination, "departure_date": dep_date_obj.isoformat()},
        )
        res_opts = raw_result.get("options", [])
        if isinstance(res_opts, list):
            raw_options = res_opts
    except Exception:
        raw_options = []

    outbound_options: list[FlightOption] = []
    for item in raw_options:
        if isinstance(item, dict):
            legs_raw = item.get("legs", [])
            legs: list[FlightLeg] = []
            for leg in legs_raw:
                if isinstance(leg, dict):
                    dep_raw = str(leg.get("departure_time", f"{dep_date_obj.isoformat()}T08:00:00Z")).replace("Z", "+00:00")
                    arr_raw = str(leg.get("arrival_time", f"{dep_date_obj.isoformat()}T09:25:00Z")).replace("Z", "+00:00")
                    dep_dt = datetime.fromisoformat(dep_raw)
                    if dep_dt.tzinfo is None:
                        dep_dt = dep_dt.replace(tzinfo=timezone.utc)
                    arr_dt = datetime.fromisoformat(arr_raw)
                    if arr_dt.tzinfo is None:
                        arr_dt = arr_dt.replace(tzinfo=timezone.utc)

                    legs.append(
                        FlightLeg(
                            origin_iata=str(leg.get("origin_iata", origin)),
                            destination_iata=str(leg.get("destination_iata", destination)),
                            carrier_code=str(leg.get("carrier_code", "6E")),
                            flight_number=str(leg.get("flight_number", "Morning Window")),
                            departure_time=dep_dt,
                            arrival_time=arr_dt,
                            duration_minutes=int(leg.get("duration_minutes", 80)),
                        )
                    )
            base_fare = Decimal(str(item.get("fare_amount", "4500.00")))
            total_fare = base_fare * Decimal(str(travelers))
            curr = str(item.get("currency", "INR"))
            prov_val = str(item.get("source_provenance", "flightapi"))
            if prov_val not in ["aviationstack", "flightapi", "tavily", "cached"]:
                prov_val = "cached"

            outbound_options.append(
                FlightOption(
                    option_id=str(item.get("option_id", f"fl_{origin}_{destination}_live_{len(outbound_options)+1}")),
                    carrier=str(item.get("carrier", "IndiGo")),
                    legs=legs,
                    fare=Money(amount=total_fare, currency=curr),
                    is_estimate=bool(item.get("is_estimate", False)),
                    source_provenance=cast(Literal["aviationstack", "flightapi", "tavily", "cached"], prov_val),
                    source_citation=str(item.get("source_citation", "https://www.flightapi.io")),
                )
            )

    schedule_templates: list[ScheduleTemplate] = [
        {
            "id_suffix": "morning",
            "carrier": "IndiGo",
            "carrier_code": "6E",
            "departure_window": "Morning Window (Scheduled Service)",
            "dep_time": time(7, 15),
            "arr_time": time(8, 35),
            "duration": 80,
            "unit_fare": Decimal("4400.00"),
        },
        {
            "id_suffix": "afternoon",
            "carrier": "Air India",
            "carrier_code": "AI",
            "departure_window": "Afternoon Window (Scheduled Service)",
            "dep_time": time(13, 10),
            "arr_time": time(14, 35),
            "duration": 85,
            "unit_fare": Decimal("4950.00"),
        },
        {
            "id_suffix": "evening",
            "carrier": "SpiceJet",
            "carrier_code": "SG",
            "departure_window": "Evening Window (Scheduled Service)",
            "dep_time": time(18, 20),
            "arr_time": time(19, 45),
            "duration": 85,
            "unit_fare": Decimal("4150.00"),
        },
    ]

    for tmpl in schedule_templates:
        dep_dt = datetime.combine(dep_date_obj, tmpl["dep_time"], tzinfo=timezone.utc)
        arr_dt = datetime.combine(dep_date_obj, tmpl["arr_time"], tzinfo=timezone.utc)
        total_fare = tmpl["unit_fare"] * Decimal(str(travelers))
        opt_id = f"flight_out_{origin}_{destination}_{tmpl['id_suffix']}"
        if not any(f.option_id == opt_id for f in outbound_options):
            outbound_options.append(
                FlightOption(
                    option_id=opt_id,
                    carrier=tmpl["carrier"],
                    legs=[
                        FlightLeg(
                            origin_iata=origin,
                            destination_iata=destination,
                            carrier_code=tmpl["carrier_code"],
                            flight_number=tmpl["departure_window"],
                            departure_time=dep_dt,
                            arrival_time=arr_dt,
                            duration_minutes=tmpl["duration"],
                        )
                    ],
                    fare=Money(amount=total_fare, currency="INR"),
                    is_estimate=True,
                    source_provenance="cached",
                    source_citation="https://example.com/indicative_market_fares",
                )
            )

    return_templates: list[ScheduleTemplate] = [
        {
            "id_suffix": "afternoon",
            "carrier": "IndiGo",
            "carrier_code": "6E",
            "departure_window": "Afternoon Window (Scheduled Service)",
            "dep_time": time(14, 30),
            "arr_time": time(15, 55),
            "duration": 85,
            "unit_fare": Decimal("4600.00"),
        },
        {
            "id_suffix": "night",
            "carrier": "Air India Express",
            "carrier_code": "IX",
            "departure_window": "Evening Window (Scheduled Service)",
            "dep_time": time(20, 15),
            "arr_time": time(21, 35),
            "duration": 80,
            "unit_fare": Decimal("4250.00"),
        },
    ]

    ret_origin = state.get("return_iata") or destination
    raw_return_opts: list[object] = []
    try:
        raw_ret_res = await registry.flight_client.call_tool(
            name="search_flight_offers",
            arguments={"origin": ret_origin, "destination": origin, "departure_date": ret_date_obj.isoformat(), "adults": travelers},
        )
        res_ret = raw_ret_res.get("options", [])
        if isinstance(res_ret, list):
            raw_return_opts = res_ret
    except Exception:
        raw_return_opts = []

    return_options: list[FlightOption] = []
    for item in raw_return_opts[:2]:
        if isinstance(item, dict):
            legs_raw = item.get("legs", [])
            ret_legs: list[FlightLeg] = []
            for leg in legs_raw:
                if isinstance(leg, dict):
                    dep_raw = str(leg.get("departure_time", f"{ret_date_obj.isoformat()}T15:00:00Z")).replace("Z", "+00:00")
                    arr_raw = str(leg.get("arrival_time", f"{ret_date_obj.isoformat()}T16:25:00Z")).replace("Z", "+00:00")
                    dep_dt = datetime.fromisoformat(dep_raw)
                    if dep_dt.tzinfo is None:
                        dep_dt = dep_dt.replace(tzinfo=timezone.utc)
                    arr_dt = datetime.fromisoformat(arr_raw)
                    if arr_dt.tzinfo is None:
                        arr_dt = arr_dt.replace(tzinfo=timezone.utc)

                    ret_legs.append(
                        FlightLeg(
                            origin_iata=str(leg.get("origin_iata", ret_origin)),
                            destination_iata=str(leg.get("destination_iata", origin)),
                            carrier_code=str(leg.get("carrier_code", "6E")),
                            flight_number=str(leg.get("flight_number", "Return Scheduled Service")),
                            departure_time=dep_dt,
                            arrival_time=arr_dt,
                            duration_minutes=int(leg.get("duration_minutes", 85)),
                        )
                    )
            base_fare = Decimal(str(item.get("fare_amount", "4600.00")))
            total_fare = base_fare * Decimal(str(travelers))
            curr = str(item.get("currency", "INR"))
            prov_val = str(item.get("source_provenance", "flightapi"))
            if prov_val not in ["aviationstack", "flightapi", "tavily", "cached"]:
                prov_val = "cached"

            return_options.append(
                FlightOption(
                    option_id=str(item.get("option_id", f"flight_ret_{ret_origin}_{origin}_{len(return_options)+1}")),
                    carrier=str(item.get("carrier", "IndiGo")),
                    legs=ret_legs,
                    fare=Money(amount=total_fare, currency=curr),
                    is_estimate=bool(item.get("is_estimate", False)),
                    source_provenance=cast(Literal["aviationstack", "flightapi", "tavily", "cached"], prov_val),
                    source_citation=str(item.get("source_citation", "https://www.flightapi.io")),
                )
            )

    if not return_options:
        for tmpl in return_templates:
            ret_dep_dt = datetime.combine(ret_date_obj, tmpl["dep_time"], tzinfo=timezone.utc)
            ret_arr_dt = datetime.combine(ret_date_obj, tmpl["arr_time"], tzinfo=timezone.utc)
            total_fare = tmpl["unit_fare"] * Decimal(str(travelers))
            return_options.append(
                FlightOption(
                    option_id=f"flight_ret_{ret_origin}_{origin}_{tmpl['id_suffix']}",
                    carrier=tmpl["carrier"],
                    legs=[
                        FlightLeg(
                            origin_iata=ret_origin,
                            destination_iata=origin,
                            carrier_code=tmpl["carrier_code"],
                            flight_number=tmpl["departure_window"],
                            departure_time=ret_dep_dt,
                            arrival_time=ret_arr_dt,
                            duration_minutes=tmpl["duration"],
                        )
                    ],
                    fare=Money(amount=total_fare, currency="INR"),
                    is_estimate=True,
                    source_provenance="cached",
                    source_citation="https://example.com/indicative_market_fares",
                )
            )

    selected_id = outbound_options[0].option_id if outbound_options else None
    return {
        "flight_options": outbound_options,
        "return_flight_options": return_options,
        "selected_flight_id": selected_id,
    }
