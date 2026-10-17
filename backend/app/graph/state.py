from __future__ import annotations
from typing import Any, Literal, TypedDict

class BookingInfo(TypedDict, total=False):
    session_type: str | None
    name: str | None
    email: str | None
    slot_id: str | None
    slot_label: str | None
    status: Literal["idle", "collecting", "awaiting_slot", "confirmed"]
    reference_id: str | None

class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]
    intent: Literal["faq", "booking", "smalltalk", "blocked"] | None
    booking: BookingInfo
    booking_active: bool
    citations: list[dict[str, Any]]
    active_node: str

