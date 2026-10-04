from ..core.state import PlanMyTripState


async def supervisor_node(state: PlanMyTripState) -> dict[str, object]:
    feedback = state.get("human_feedback")
    if feedback and isinstance(feedback, dict):
        action = feedback.get("action")
        if action == "edit_flight":
            new_id = feedback.get("selected_flight_id")
            return {
                "selected_flight_id": new_id,
                "next_step": "replan_synthesis",
            }
        elif action == "edit_hotel":
            new_id = feedback.get("selected_hotel_id")
            return {
                "selected_hotel_id": new_id,
                "next_step": "replan_synthesis",
            }
        elif action == "approve":
            return {
                "next_step": "complete",
            }

    budget = state.get("budget_reconciliation")
    if budget and budget.is_over_budget:
        return {
            "next_step": "replan_budget",
        }

    return {
        "next_step": "synthesize",
    }
