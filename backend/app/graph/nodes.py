from __future__ import annotations
import re
from app.guardrails import is_prompt_injection
from app.rag.retriever import HandbookRetriever
from app.tools.booking import extract_email, list_slots, book_slot
from .state import AgentState, BookingInfo

def _last_user(state: AgentState) -> str:
    return next((m["content"] for m in reversed(state.get("messages", [])) if m["role"] == "user"), "")

def guardrail_node(state: AgentState) -> AgentState:
    state["active_node"] = "Guardrail"
    if is_prompt_injection(_last_user(state)):
        state["intent"] = "blocked"
        state["messages"].append({"role": "assistant", "content": "I can help with HR handbook questions and 1-on-1 bookings, but I can't reveal internal instructions or secrets."})
    return state

def router_node(state: AgentState) -> AgentState:
    state["active_node"] = "Router"
    text = _last_user(state).lower()
    if state.get("booking_active") and (extract_email(text) or "performance review" in text or "career discussion" in text):
        state["booking"] = _merge_booking(state)
    if any(word in text for word in ("cancel booking", "cancel my booking")):
        state["intent"] = "booking"
    elif any(word in text for word in ("how often", "how many", "what is", "what's", "how long", "remote", "pto", "insurance", "probation", "hotel", "conducted")):
        state["intent"] = "faq"
    elif state.get("booking_active") or any(word in text for word in ("book", "schedule", "session", "slot", "tomorrow", "friday", "monday")) or extract_email(text):
        state["intent"] = "booking"
    else:
        state["intent"] = "smalltalk"
    return state

def _faq_answer(query: str, retriever: HandbookRetriever) -> tuple[str, list[dict]]:
    chunks = retriever.search(query)
    if not chunks:
        return "I couldn't find that in the handbook.", []
    best = chunks[0]
    return f"{best.text} (Page {best.page})", [{"page": best.page, "source": best.source}]

def faq_node(state: AgentState, retriever: HandbookRetriever) -> AgentState:
    state["active_node"] = "FAQ RAG"
    answer, citations = _faq_answer(_last_user(state), retriever)
    state["citations"] = citations
    state["messages"].append({"role": "assistant", "content": answer})
    return state

def _merge_booking(state: AgentState) -> BookingInfo:
    booking = dict(state.get("booking", {}))
    text = _last_user(state)
    lowered = text.lower()
    email = extract_email(text)
    if email:
        booking["email"] = email
    if "performance review" in lowered:
        booking["session_type"] = "Performance Review"
    elif "career discussion" in lowered:
        booking["session_type"] = "Career Discussion"
    elif "benefits consultation" in lowered:
        booking["session_type"] = "Benefits Consultation"
    if not booking.get("name"):
        if email:
            cleaned = text[: text.lower().find(email.lower())]
        else:
            cleaned = text
        cleaned = re.sub(r"\b(wait|before that|please|hi|hello)\b.*?:", "", cleaned, flags=re.I).strip(" .,()")
        if cleaned and len(cleaned.split()) >= 2 and not any(x in cleaned.lower() for x in ("how", "what", "when", "book", "slot")):
            booking["name"] = cleaned.split("(")[0].strip(" .,")
    return booking

async def booking_node(state: AgentState) -> AgentState:
    state["active_node"] = "Booking"
    text = _last_user(state)
    if "cancel" in text.lower():
        state["booking"] = {"status": "idle"}
        state["booking_active"] = False
        state["messages"].append({"role": "assistant", "content": "Your pending booking has been cancelled."})
        return state
    booking = _merge_booking(state)
    booking.setdefault("session_type", "Performance Review")
    booking["status"] = "collecting"
    state["booking_active"] = True
    if booking.get("email") and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", booking["email"]):
        booking["email"] = None
        state["messages"].append({"role": "assistant", "content": "That email looks invalid. Please provide a valid email address."})
    elif not booking.get("name") or not booking.get("email"):
        missing = []
        if not booking.get("name"): missing.append("full name")
        if not booking.get("email"): missing.append("email")
        state["messages"].append({"role": "assistant", "content": f"Happy to help schedule a {booking['session_type']}. May I have your {' and '.join(missing)}?"})
    elif not booking.get("slot_id"):
        available = list_slots()
        chosen = None
        for index, slot in enumerate(available, 1):
            if str(index) in text or slot["slot_id"] in text.lower() or slot["label"].lower() in text.lower():
                chosen = slot
                break
        if chosen:
            result = await book_slot(chosen["slot_id"], booking["name"], booking["email"], booking["session_type"])
            booking.update(result)
            booking["status"] = "confirmed"
            state["booking_active"] = False
            state["messages"].append({"role": "assistant", "content": f"Confirmed! Your {booking['session_type']} is scheduled for {booking['slot_label']} for {booking['name']}. Reference ID: {booking['reference_id']}."})
        else:
            booking["status"] = "awaiting_slot"
            options = " ".join(f"{i + 1}) {slot['label']}." for i, slot in enumerate(available))
            prefix = f"Returning to your booking, {booking['name']} — " if state.get("citations") else ""
            state["messages"].append({"role": "assistant", "content": f"{prefix}Available slots: {options} Which works best?"})
    state["booking"] = booking
    return state

def smalltalk_node(state: AgentState) -> AgentState:
    state["active_node"] = "Smalltalk"
    state["messages"].append({"role": "assistant", "content": "Hello! I can answer Northwind handbook questions or help book a 1-on-1 HR session."})
    return state

def blocked_node(state: AgentState) -> AgentState:
    state["active_node"] = "Guardrail"
    return state
