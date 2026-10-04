import asyncio
import sys
import uuid

sys.path.insert(0, "backend")

from langchain_core.messages import HumanMessage
from app.core.database import create_checkpointer_pool, setup_checkpointer
from app.graph.builder import build_trip_graph


async def smoke_test() -> None:
    pool = create_checkpointer_pool()
    await pool.open()
    try:
        checkpointer = await setup_checkpointer(pool)
        graph = build_trip_graph(checkpointer=checkpointer)

        thread_id = f"smoke_test_inr_{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}


        print(f"[*] Executing smoke test on thread: {thread_id}")
        initial_input = {"messages": [HumanMessage(content="Plan a trip to Goa on Dec 1st with budget 2 lakhs")]}



        async for update in graph.astream(initial_input, config=config):
            for node, values in update.items():
                print(f"[->] Node executed: {node}")

        state = await graph.aget_state(config)
        print(f"[*] Graph paused at checkpoint before: {state.next}")

        if "synthesis_agent" in state.next:
            print("[*] Resuming past Human-in-the-Loop breakpoint...")
            await graph.aupdate_state(
                config,
                {"human_feedback": {"action": "approve"}},
                as_node="supervisor",
            )
            final_res = await graph.ainvoke(None, config=config)
            print("[SUCCESS] Synthesis completed successfully!")
            print(f"[*] Final itinerary length: {len(str(final_res.get('itinerary_draft', '')))} chars")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(smoke_test())
