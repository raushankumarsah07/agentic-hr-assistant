from __future__ import annotations
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    thread_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)

class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    active_node: str
    intent: str | None
    citations: list[dict]
    booking_status: str

class ThreadResponse(BaseModel):
    thread_id: str
    messages: list[dict[str, str]]
    booking: dict

