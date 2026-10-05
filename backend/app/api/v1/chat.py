import json
from collections.abc import AsyncGenerator
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, Request
from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse

from ...core.database import async_session_factory, create_checkpointer_pool, setup_checkpointer
from ...core.money import Money, parse_indian_budget_decimal
from ...graph.builder import build_trip_graph
from ...models.chat_message import ChatMessage
from ...models.conversation_intake import ConversationIntake
from ...models.trip import Trip
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
    trip_id = getattr(_thread, "trip_id", None)

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        msg_lower = message.lower()
        budget_keywords = ["lakh", "lac", "cr", "crore", "thousand", "k", "budget", "inr", "₹", "rs"]
        user_budget = None
        if any(kw in msg_lower for kw in budget_keywords):
            parsed_val = parse_indian_budget_decimal(message)
            if parsed_val > Decimal("0.00"):
                user_budget = Money(amount=parsed_val, currency="INR")

        intake_station = None
        intake_dest = None
        intake_start = None
        intake_end = None
        intake_budget = None

        if trip_id:
            async with async_session_factory() as db_session:
                user_msg = ChatMessage(
                    trip_id=trip_id,
                    user_id=user.id,
                    role="user",
                    content=message,
                )
                db_session.add(user_msg)
                intake_stmt = select(ConversationIntake).where(ConversationIntake.trip_id == trip_id)
                intake_res = await db_session.execute(intake_stmt)
                intake_row = intake_res.scalar_one_or_none()
                if intake_row:
                    if user_budget:
                        intake_row.budget_amount = user_budget.amount
                    intake_station = intake_row.departure_station
                    intake_dest = intake_row.destination
                    intake_start = str(intake_row.start_date) if intake_row.start_date else None
                    intake_end = str(intake_row.end_date) if intake_row.end_date else None
                    if intake_row.budget_amount:
                        intake_budget = Money(amount=intake_row.budget_amount, currency=intake_row.currency or "INR")
                await db_session.commit()

        pool = create_checkpointer_pool()
        await pool.open()
        try:
            checkpointer = await setup_checkpointer(pool)
            graph = build_trip_graph(checkpointer=checkpointer)

            config = {"configurable": {"thread_id": thread_id}}

            initial_input: dict[str, object] = {
                "messages": [HumanMessage(content=message)],
                "departure_station": intake_station,
                "destination": intake_dest,
                "start_date": intake_start,
                "end_date": intake_end,
            }
            if user_budget:
                initial_input["trip_budget"] = user_budget
            elif intake_budget:
                initial_input["trip_budget"] = intake_budget

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
                    elif node_name == "intake_supervisor":
                        eval_data = node_update.get("intake_evaluation")
                        if eval_data:
                            if trip_id:
                                async with async_session_factory() as db_session:
                                    intake_stmt = select(ConversationIntake).where(ConversationIntake.trip_id == trip_id)
                                    intake_res = await db_session.execute(intake_stmt)
                                    intake_row = intake_res.scalar_one_or_none()
                                    if intake_row:
                                        if eval_data.departure_station:
                                            intake_row.departure_station = eval_data.departure_station
                                        if eval_data.destination:
                                            intake_row.destination = eval_data.destination
                                        if eval_data.start_date:
                                            try:
                                                from datetime import date
                                                intake_row.start_date = date.fromisoformat(eval_data.start_date)
                                            except Exception:
                                                pass
                                        if eval_data.end_date:
                                            try:
                                                from datetime import date
                                                intake_row.end_date = date.fromisoformat(eval_data.end_date)
                                            except Exception:
                                                pass
                                        if eval_data.budget_inr:
                                            intake_row.budget_amount = eval_data.budget_inr

                                    trip_stmt = select(Trip).where(Trip.id == trip_id)
                                    trip_res = await db_session.execute(trip_stmt)
                                    trip_row = trip_res.scalar_one_or_none()
                                    if trip_row and eval_data.destination:
                                        trip_row.destination = eval_data.destination
                                        trip_row.title = f"Trip to {eval_data.destination}"

                                    if not eval_data.is_complete and eval_data.next_question_or_confirmation:
                                        asst_msg = ChatMessage(
                                            trip_id=trip_id,
                                            user_id=user.id,
                                            role="assistant",
                                            content=eval_data.next_question_or_confirmation,
                                        )
                                        db_session.add(asst_msg)
                                    await db_session.commit()

                            if eval_data.destination:
                                yield {
                                    "event": "intake_update",
                                    "data": json.dumps({
                                        "destination": eval_data.destination,
                                        "title": f"Trip to {eval_data.destination}",
                                        "departure_station": eval_data.departure_station,
                                        "start_date": eval_data.start_date,
                                        "end_date": eval_data.end_date,
                                        "is_complete": eval_data.is_complete,
                                    }, default=str),
                                }

                            if not eval_data.is_complete and eval_data.next_question_or_confirmation:
                                yield {
                                    "event": "synthesis",
                                    "data": json.dumps({"draft": eval_data.next_question_or_confirmation}, default=str),
                                }
                            elif eval_data.is_complete:
                                yield {
                                    "event": "status",
                                    "data": json.dumps({"step": "intake_complete", "message": "All trip parameters confirmed! Researching flights, stays, and activities..."}),
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
                        if draft and trip_id:
                            async with async_session_factory() as db_session:
                                assistant_msg = ChatMessage(
                                    trip_id=trip_id,
                                    user_id=user.id,
                                    role="assistant",
                                    content=str(draft),
                                )
                                db_session.add(assistant_msg)
                                await db_session.commit()
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
