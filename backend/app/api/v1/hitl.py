from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import create_checkpointer_pool, get_db_session, setup_checkpointer
from ...graph.builder import build_trip_graph
from ...models.trip_thread import TripThread
from ...models.user import User
from ...schemas.hitl import HitlResumeRequest
from ..dependencies import get_current_user, verify_thread_ownership

router = APIRouter(prefix="/hitl", tags=["hitl"])


@router.get("/state")
async def get_thread_state(
    thread_id: str = Query(...),
    user: User = Depends(get_current_user),
    _thread: object = Depends(verify_thread_ownership),
) -> dict[str, object]:
    pool = create_checkpointer_pool()
    await pool.open()
    try:
        checkpointer = await setup_checkpointer(pool)
        graph = build_trip_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await graph.aget_state(config)
        if not snapshot.values:
            raise HTTPException(status_code=404, detail="No active state found for thread")

        values = snapshot.values
        serialized: dict[str, object] = {}
        for k, v in values.items():
            if k == "messages":
                serialized[k] = [m.content for m in v]
            elif isinstance(v, list):
                serialized[k] = [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                    for item in v
                ]
            elif hasattr(v, "model_dump"):
                serialized[k] = v.model_dump(mode="json")
            else:
                serialized[k] = v

        return {
            "values": serialized,
            "next": list(snapshot.next),
        }
    finally:
        await pool.close()


@router.post("/resume")
async def resume_hitl(
    req: HitlResumeRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    stmt = select(TripThread).where(
        TripThread.langgraph_thread_id == req.thread_id,
        TripThread.user_id == user.id,
    )
    result = await session.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: thread does not belong to authenticated user",
        )

    pool = create_checkpointer_pool()
    await pool.open()
    try:
        checkpointer = await setup_checkpointer(pool)
        graph = build_trip_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": req.thread_id}}

        feedback = {
            "action": req.action,
            "selected_flight_id": req.selected_flight_id,
            "selected_hotel_id": req.selected_hotel_id,
        }

        await graph.aupdate_state(config, {"human_feedback": feedback}, as_node="supervisor")
        res = await graph.ainvoke(None, config=config)

        draft = res.get("itinerary_draft", "")
        return {
            "status": "resumed",
            "itinerary_draft": draft,
        }
    finally:
        await pool.close()
