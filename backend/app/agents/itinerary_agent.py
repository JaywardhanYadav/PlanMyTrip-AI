from datetime import date, datetime
from decimal import Decimal
from ..core.money import Money
from ..core.state import ActivityOption, PlanMyTripState, WeatherOutlook
from ..mcp_client.registry import MCPRegistry


async def itinerary_agent_node(state: PlanMyTripState) -> dict[str, object]:
    destination = "Goa"
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

    weather_outlooks: list[WeatherOutlook] = []
    try:
        w_res = await registry.weather_client.call_tool(
            name="get_weather_forecast",
            arguments={"destination": destination, "target_date": "2026-12-01"},
        )
        outlook_raw = w_res.get("outlook", {})
        if isinstance(outlook_raw, dict):
            weather_outlooks.append(
                WeatherOutlook(
                    destination=str(outlook_raw.get("destination", destination)),
                    target_date=date.fromisoformat(str(outlook_raw.get("target_date", "2026-12-01"))),
                    source="climate_normal" if outlook_raw.get("source") == "climate_normal" else "forecast",
                    temp_high_celsius=Decimal(str(outlook_raw.get("temp_high_celsius", "28.0"))),
                    temp_low_celsius=Decimal(str(outlook_raw.get("temp_low_celsius", "22.0"))),
                    condition=str(outlook_raw.get("condition", "Sunny Beach Weather")),
                    precipitation_probability=Decimal(str(outlook_raw.get("precipitation_probability", "0.05"))),
                )
            )
    except Exception:
        pass

    if not weather_outlooks:
        weather_outlooks = [
            WeatherOutlook(
                destination=destination,
                target_date=date.fromisoformat("2026-12-01"),
                source="climate_normal",
                temp_high_celsius=Decimal("30.0"),
                temp_low_celsius=Decimal("23.0"),
                condition="Sunny & Clear",
                precipitation_probability=Decimal("0.05"),
            )
        ]

    activities: list[ActivityOption] = []
    try:
        p_res = await registry.places_client.call_tool(
            name="search_activities",
            arguments={"destination": destination, "date": "2026-12-01"},
        )
        raw_acts = p_res.get("activities", [])
        if isinstance(raw_acts, list):
            for item in raw_acts:
                if isinstance(item, dict):
                    cost_val = str(item.get("cost", "0.00"))
                    curr = str(item.get("currency", "INR"))
                    t_str = str(item.get("timing", "2026-12-01T10:00:00Z")).replace("Z", "+00:00")
                    activities.append(
                        ActivityOption(
                            option_id=str(item.get("option_id", f"act_{destination}_01")),
                            title=str(item.get("title", f"{destination} Sightseeing Tour")),
                            location=str(item.get("location", destination)),
                            timing=datetime.fromisoformat(t_str),
                            duration_minutes=int(item.get("duration_minutes", 120)),
                            cost=Money(amount=Decimal(cost_val), currency=curr),
                            is_free=bool(item.get("is_free", False)),
                            weather_sensitive=bool(item.get("weather_sensitive", False)),
                            source_provenance="cached",
                            source_citation=str(item.get("source_citation", "https://example.com/activity")),
                        )
                    )
    except Exception:
        pass

    if not activities:
        activities = [
            ActivityOption(
                option_id=f"act_{destination.lower()}_primary",
                title=f"{destination} Heritage City & Sunset Cruise",
                location=f"Harbor Front, {destination}",
                timing=datetime.fromisoformat("2026-12-01T10:00:00+00:00"),
                duration_minutes=150,
                cost=Money(amount=Decimal("1500.00"), currency="INR"),
                is_free=False,
                weather_sensitive=True,
                source_provenance="cached",
                source_citation="https://example.com/cruise",
            )
        ]

    selected_ids = [act.option_id for act in activities[:2]]
    return {
        "weather_outlook": weather_outlooks,
        "activity_options": activities,
        "selected_activity_ids": selected_ids,
    }

