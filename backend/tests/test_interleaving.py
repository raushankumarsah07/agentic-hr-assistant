import pytest
from app.graph.builder import build_graph
from app.rag.retriever import HandbookRetriever
from app.tools.booking import reset_slots

async def invoke(graph, state, text, thread_id="test"):
    state.setdefault("messages", []).append({"role": "user", "content": text})
    return await graph.ainvoke(state, config={"configurable": {"thread_id": thread_id}})

@pytest.mark.asyncio
async def test_faq_interleaving_preserves_booking():
    reset_slots()
    graph = build_graph(HandbookRetriever())
    state = {}
    state = await invoke(graph, state, "I need to book a Performance Review")
    state = await invoke(graph, state, "Alex Chen (alex.chen@example.com). Wait, how often are performance reviews conducted?")
    assert state["booking"]["name"] == "Alex Chen"
    assert state["booking"]["email"] == "alex.chen@example.com"
    assert state["citations"][0]["page"] == 4
    assert "Available slots" in state["messages"][-1]["content"]

@pytest.mark.asyncio
async def test_threads_do_not_share_state():
    graph = build_graph(HandbookRetriever())
    first = await invoke(graph, {}, "Book a Performance Review", "thread-one")
    second = await invoke(graph, {}, "Hello", "thread-two")
    assert first["booking_active"] is True
    assert second.get("booking_active", False) is False
