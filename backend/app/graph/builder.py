from decimal import Decimal
from typing import Any
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from ..agents.flight_agent import flight_agent_node
from ..agents.hotel_agent import hotel_agent_node
from ..agents.intake_agent import evaluate_trip_intake
from ..agents.itinerary_agent import itinerary_agent_node
from ..agents.supervisor import supervisor_node
from ..agents.synthesis_agent import synthesis_agent_node
from ..core.money import Money
from ..core.state import PlanMyTripState
from ..guardrails.input_guard import evaluate_input_guardrail
from .edges import route_guardrail, route_intake, route_supervisor


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
    if evaluation.start_date:
        updates["start_date"] = evaluation.start_date
    if evaluation.end_date:
        updates["end_date"] = evaluation.end_date
    if evaluation.budget_inr is not None:
        updates["trip_budget"] = Money(amount=Decimal(str(evaluation.budget_inr)), currency="INR")

    if not evaluation.is_complete and evaluation.next_question_or_confirmation:
        updates["messages"] = [AIMessage(content=evaluation.next_question_or_confirmation)]

    return updates


def build_trip_graph(checkpointer: Any = None) -> Any:
    builder = StateGraph(PlanMyTripState)

    builder.add_node("input_guard", input_guard_node)
    builder.add_node("intake_supervisor", intake_supervisor_node)
    builder.add_node("flight_agent", flight_agent_node)
    builder.add_node("hotel_agent", hotel_agent_node)
    builder.add_node("itinerary_agent", itinerary_agent_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("synthesis_agent", synthesis_agent_node)

    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges("input_guard", route_guardrail)
    builder.add_conditional_edges("intake_supervisor", route_intake)

    builder.add_edge("flight_agent", "supervisor")
    builder.add_edge("hotel_agent", "supervisor")
    builder.add_edge("itinerary_agent", "supervisor")

    builder.add_conditional_edges("supervisor", route_supervisor)
    builder.add_edge("synthesis_agent", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["synthesis_agent"],
    )
