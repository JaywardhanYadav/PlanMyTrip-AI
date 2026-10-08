import asyncio
from decimal import Decimal
from typing import Any
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from ..agents.flight_agent import flight_agent_node
from ..agents.hotel_agent import hotel_agent_node
from ..agents.intake_agent import evaluate_trip_intake
from ..agents.itinerary_agent import itinerary_agent_node
from ..agents.places_agent import places_agent_node
from ..agents.synthesis_agent import synthesis_agent_node
from ..core.money import Money
from ..core.state import PlanMyTripState
from ..guardrails.input_guard import evaluate_input_guardrail
from .edges import route_guardrail, route_intake


async def input_guard_node(state: PlanMyTripState) -> dict[str, object]:
    messages = state.get("messages", [])
    user_msg = str(messages[-1].content) if messages else "Plan a trip."
    verdict = await evaluate_input_guardrail(user_msg)
    return {"guardrail_verdict": verdict}


async def intake_supervisor_node(state: PlanMyTripState) -> dict[str, object]:
    messages = state.get("messages", [])
    current_budget = state.get("trip_budget")
    existing_state = {
        "departure_station": state.get("departure_station"),
        "destination": state.get("destination"),
        "travelers_count": state.get("travelers_count"),
        "start_date": state.get("start_date"),
        "end_date": state.get("end_date"),
        "budget_inr": current_budget.amount if current_budget else None,
    }
    user_name = state.get("user_name") or "there"
    evaluation = await evaluate_trip_intake(messages, existing_state, user_name=user_name)

    updates: dict[str, object] = {"intake_evaluation": evaluation}
    if evaluation.departure_station:
        updates["departure_station"] = evaluation.departure_station
    if evaluation.destination:
        updates["destination"] = evaluation.destination
    if evaluation.travelers_count:
        updates["travelers_count"] = evaluation.travelers_count
    if evaluation.start_date:
        updates["start_date"] = evaluation.start_date
    if evaluation.end_date:
        updates["end_date"] = evaluation.end_date
    if evaluation.budget_inr is not None:
        updates["trip_budget"] = Money(amount=Decimal(str(evaluation.budget_inr)), currency="INR")

    if not evaluation.is_complete and evaluation.next_question_or_confirmation:
        updates["messages"] = [AIMessage(content=evaluation.next_question_or_confirmation)]

    return updates


async def workers_orchestrator_node(state: PlanMyTripState) -> dict[str, object]:
    flight_res, hotel_res, places_res, itin_res = await asyncio.gather(
        flight_agent_node(state),
        hotel_agent_node(state),
        places_agent_node(state),
        itinerary_agent_node(state),
    )
    combined: dict[str, object] = {}
    combined.update(flight_res)
    combined.update(hotel_res)
    combined.update(places_res)
    combined.update(itin_res)
    return combined


def build_trip_graph(checkpointer: Any = None) -> Any:
    builder = StateGraph(PlanMyTripState)

    builder.add_node("input_guard", input_guard_node)
    builder.add_node("intake_supervisor", intake_supervisor_node)
    builder.add_node("workers_orchestrator", workers_orchestrator_node)
    builder.add_node("synthesis_agent", synthesis_agent_node)

    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges("input_guard", route_guardrail)
    builder.add_conditional_edges("intake_supervisor", route_intake)

    builder.add_edge("workers_orchestrator", "synthesis_agent")
    builder.add_edge("synthesis_agent", END)

    return builder.compile(
        checkpointer=checkpointer,
    )
