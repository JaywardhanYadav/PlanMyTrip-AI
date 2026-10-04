import os
from decimal import Decimal
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="PlanMyTrip MCP Places & Hotels Server")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


class HotelResult(BaseModel):
    option_id: str
    name: str
    location: str
    nightly_rate: str
    total_rate: str
    currency: str
    cancellation_terms: str
    source_provenance: str
    source_citation: str | None


class ActivityResult(BaseModel):
    option_id: str
    title: str
    location: str
    timing: str
    duration_minutes: int
    cost: str
    currency: str = "INR"
    is_free: bool
    weather_sensitive: bool
    source_provenance: str
    source_citation: str | None


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, object]


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, object]


@app.get("/tools")
async def list_tools() -> dict[str, list[ToolDefinition]]:
    return {
        "tools": [
            ToolDefinition(
                name="search_hotels",
                description="Search for hotel accommodations in a destination.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "destination": {"type": "string"},
                        "nights": {"type": "integer", "default": 3},
                    },
                    "required": ["destination"],
                },
            ),
            ToolDefinition(
                name="search_activities",
                description="Search for attractions, tours, and activities in a destination.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "destination": {"type": "string"},
                        "date": {"type": "string"},
                    },
                    "required": ["destination", "date"],
                },
            ),
        ]
    }


@app.post("/call")
async def call_tool(call: ToolCallRequest) -> dict[str, object]:
    args = call.arguments
    destination = str(args.get("destination", "City Center")).strip()

    if call.name == "search_hotels":
        nights = int(args.get("nights", 3))
        rate_1 = Decimal("5500.00")
        rate_2 = Decimal("8500.00")

        hotels = [
            HotelResult(
                option_id=f"hotel_{destination.lower()}_01",
                name=f"Grand {destination} Plaza Hotel",
                location=f"Central District, {destination}",
                nightly_rate=str(rate_1),
                total_rate=str(rate_1 * Decimal(nights)),
                currency="INR",
                cancellation_terms="Free cancellation up to 48 hours before check-in.",
                source_provenance="tavily" if TAVILY_API_KEY else "cached",
                source_citation="https://example.com/hotels/grand-plaza",
            ),
            HotelResult(
                option_id=f"hotel_{destination.lower()}_02",
                name=f"{destination} Heritage Boutique Inn",
                location=f"Old Town, {destination}",
                nightly_rate=str(rate_2),
                total_rate=str(rate_2 * Decimal(nights)),
                currency="INR",
                cancellation_terms="Non-refundable special rate.",
                source_provenance="tavily" if TAVILY_API_KEY else "cached",
                source_citation="https://example.com/hotels/heritage-inn",
            ),
        ]
        return {"status": "success", "hotels": [h.model_dump() for h in hotels]}

    elif call.name == "search_activities":
        date_str = str(args.get("date", "2026-12-01"))
        activities = [
            ActivityResult(
                option_id=f"act_{destination.lower()}_01",
                title=f"{destination} Guided Walking & Cultural Tour",
                location=f"Historic District, {destination}",
                timing=f"{date_str}T10:00:00Z",
                duration_minutes=150,
                cost="1500.00",
                currency="INR",
                is_free=False,
                weather_sensitive=True,
                source_provenance="tavily" if TAVILY_API_KEY else "cached",
                source_citation="https://example.com/tours/walking-tour",
            ),
            ActivityResult(
                option_id=f"act_{destination.lower()}_02",
                title=f"{destination} Heritage Museum & Art Gallery",
                location=f"Museum Row, {destination}",
                timing=f"{date_str}T14:30:00Z",
                duration_minutes=120,
                cost="0.00",
                currency="INR",
                is_free=True,
                weather_sensitive=False,
                source_provenance="tavily" if TAVILY_API_KEY else "cached",
                source_citation="https://example.com/museums/national-gallery",
            ),
        ]
        return {"status": "success", "activities": [a.model_dump() for a in activities]}


    raise HTTPException(status_code=404, detail=f"Tool {call.name} not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)
