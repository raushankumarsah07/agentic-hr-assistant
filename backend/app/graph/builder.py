from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import guardrail_node, router_node, faq_node, booking_node, smalltalk_node, blocked_node

def build_graph(retriever, checkpointer=None):
    """Build the state machine with a checkpointer supplied by the application."""
    graph = StateGraph(AgentState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("router", router_node)
    graph.add_node("faq_rag", lambda state: faq_node(state, retriever))
    graph.add_node("booking_flow", booking_node)
    graph.add_node("smalltalk", smalltalk_node)
    graph.add_node("blocked", blocked_node)
    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges("guardrail", lambda s: "blocked" if s.get("intent") == "blocked" else "router", {"blocked": "blocked", "router": "router"})
    graph.add_conditional_edges("faq_rag", lambda s: "booking_flow" if s.get("booking_active") and s.get("booking", {}).get("status") != "confirmed" else END, {"booking_flow": "booking_flow", END: END})
    graph.add_conditional_edges("router", lambda s: "booking_flow" if s.get("intent") == "booking" else s.get("intent", "smalltalk"), {"booking_flow": "booking_flow", "faq": "faq_rag", "smalltalk": "smalltalk", "blocked": "blocked"})
    for node in ("booking_flow", "smalltalk", "blocked"):
        graph.add_edge(node, END)
    return graph.compile(checkpointer=checkpointer or MemorySaver())
