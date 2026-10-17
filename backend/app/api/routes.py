from __future__ import annotations
import asyncio
import json
import sqlite3
import uuid
from typing import AsyncIterator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest, ChatResponse, ThreadResponse
from app.tools.booking import list_slots

router = APIRouter(prefix="/api")

def _db(request: Request) -> sqlite3.Connection:
    return request.app.state.db

def _load(request: Request, thread_id: str) -> dict:
    row = _db(request).execute("SELECT state FROM threads WHERE id=?", (thread_id,)).fetchone()
    return json.loads(row[0]) if row else {"messages": [], "booking": {"status": "idle"}, "booking_active": False, "citations": [], "active_node": "Router"}

def _save(request: Request, thread_id: str, state: dict) -> None:
    _db(request).execute("INSERT OR REPLACE INTO threads(id,state) VALUES(?,?)", (thread_id, json.dumps(state)))
    _db(request).commit()

def _reply(state: dict) -> str:
    return next((m["content"] for m in reversed(state.get("messages", [])) if m["role"] == "assistant"), "")

@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@router.get("/slots")
async def slots() -> list[dict[str, str]]:
    return list_slots()

@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    thread_id = payload.thread_id or str(uuid.uuid4())
    state = _load(request, thread_id)
    state.setdefault("messages", []).append({"role": "user", "content": payload.message})
    try:
        result = await request.app.state.graph.ainvoke(state, config={"configurable": {"thread_id": thread_id}})
    except Exception as exc:
        raise HTTPException(503, "The assistant is temporarily unavailable. Please retry.") from exc
    _save(request, thread_id, result)
    return ChatResponse(thread_id=thread_id, reply=_reply(result), active_node=result.get("active_node", "Router"), intent=result.get("intent"), citations=result.get("citations", []), booking_status=result.get("booking", {}).get("status", "idle"))

@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
    response = await chat(payload, request)
    async def events() -> AsyncIterator[str]:
        yield f"event: node\ndata: {json.dumps({'node': response.active_node})}\n\n"
        for token in response.reply.split():
            yield f"event: token\ndata: {json.dumps({'token': token + ' '})}\n\n"
            await asyncio.sleep(0.005)
        yield f"event: done\ndata: {response.model_dump_json()}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def thread(thread_id: str, request: Request) -> ThreadResponse:
    state = _load(request, thread_id)
    return ThreadResponse(thread_id=thread_id, messages=state.get("messages", []), booking=state.get("booking", {}))

