import json
from collections.abc import AsyncGenerator
from fastapi import APIRouter, Depends, Query, Request
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from decimal import Decimal
from ...core.database import create_checkpointer_pool, setup_checkpointer
from ...core.money import Money, parse_indian_budget_decimal
from ...graph.builder import build_trip_graph
from ...models.user import User
from ..dependencies import get_current_user, verify_thread_ownership

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/stream")
async def chat_stream(
    request: Request,
    thread_id: str = Query(...),
    message: str = Query(...),
    user: User = Depends(get_current_user),
    _thread: object = Depends(verify_thread_ownership),
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        pool = create_checkpointer_pool()
        await pool.open()
        try:
            checkpointer = await setup_checkpointer(pool)
            graph = build_trip_graph(checkpointer=checkpointer)

            config = {"configurable": {"thread_id": thread_id}}

            msg_lower = message.lower()
            budget_keywords = ["lakh", "lac", "cr", "crore", "thousand", "k", "budget", "inr", "₹", "rs"]
            user_budget = None
            if any(kw in msg_lower for kw in budget_keywords):
                parsed_val = parse_indian_budget_decimal(message)
                if parsed_val > Decimal("0.00"):
                    user_budget = Money(amount=parsed_val, currency="INR")

            initial_input: dict[str, object] = {
                "messages": [HumanMessage(content=message)],
            }
            if user_budget:
                initial_input["trip_budget"] = user_budget

            yield {
                "event": "status",
                "data": json.dumps({"step": "planning_started", "message": "Analyzing request..."}),
            }


            async for event in graph.astream(initial_input, config=config, stream_mode="updates"):
                if await request.is_disconnected():
                    break

                for node_name, node_update in event.items():
                    if node_name == "input_guard":
                        verdict = node_update.get("guardrail_verdict")
                        if verdict:
                            dumped = verdict.model_dump(mode="json") if hasattr(verdict, "model_dump") else verdict
                            yield {
                                "event": "guardrail",
                                "data": json.dumps(dumped, default=str),
                            }
                    elif node_name in ["flight_agent", "hotel_agent", "itinerary_agent"]:
                        serialized: dict[str, object] = {}
                        for k, v in node_update.items():
                            if isinstance(v, list):
                                serialized[k] = [
                                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                                    for item in v
                                ]
                            elif hasattr(v, "model_dump"):
                                serialized[k] = v.model_dump(mode="json")
                            else:
                                serialized[k] = v

                        yield {
                            "event": "node_update",
                            "data": json.dumps({"node": node_name, "update": serialized}, default=str),
                        }
                    elif node_name == "synthesis_agent":
                        draft = node_update.get("itinerary_draft", "")
                        yield {
                            "event": "synthesis",
                            "data": json.dumps({"draft": draft}, default=str),
                        }


            state_snapshot = await graph.aget_state(config)
            if state_snapshot.next:
                yield {
                    "event": "interrupt",
                    "data": json.dumps({
                        "interrupt_before": list(state_snapshot.next),
                        "requires_action": True,
                    }),
                }
            else:
                yield {
                    "event": "done",
                    "data": json.dumps({"status": "completed"}),
                }

        finally:
            await pool.close()

    return EventSourceResponse(event_generator())
