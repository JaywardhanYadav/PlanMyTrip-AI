from typing import Literal
from langgraph.graph import END
from ..core.state import PlanMyTripState


def route_guardrail(state: PlanMyTripState) -> list[str] | str:
    verdict = state.get("guardrail_verdict")
    if verdict and not verdict.allowed:
        return END
    return ["flight_agent", "hotel_agent", "itinerary_agent"]


def route_supervisor(state: PlanMyTripState) -> str:
    step = state.get("next_step")
    if step == "complete":
        return END
    return "synthesis_agent"
