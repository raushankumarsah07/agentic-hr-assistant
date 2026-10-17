from __future__ import annotations
import asyncio
import random
import re
from datetime import datetime, timedelta

_lock = asyncio.Lock()
_taken: set[str] = set()
_slots = [
    ("tomorrow-11", "Tomorrow 11:00 AM IST"),
    ("tomorrow-15", "Tomorrow 3:00 PM IST"),
    ("friday-1030", "Friday 10:30 AM IST"),
    ("friday-14", "Friday 2:00 PM IST"),
    ("monday-0930", "Monday 9:30 AM IST"),
    ("monday-16", "Monday 4:00 PM IST"),
]

def list_slots() -> list[dict[str, str]]:
    """Return currently available slots."""
    return [{"slot_id": sid, "label": label} for sid, label in _slots if sid not in _taken]

def _resolve_slot(value: str) -> str | None:
    value = value.lower().strip()
    available = list_slots()
    if value.isdigit():
        index = int(value) - 1
        return available[index]["slot_id"] if 0 <= index < len(available) else None
    for item in available:
        if value in item["slot_id"] or value in item["label"].lower():
            return item["slot_id"]
    aliases = {"friday at 10:30 am": "friday-1030", "friday 10:30": "friday-1030"}
    return aliases.get(value)

async def book_slot(slot_id: str, name: str, email: str, session_type: str) -> dict:
    """Atomically reserve a slot and return a deterministic-format reference."""
    async with _lock:
        resolved = _resolve_slot(slot_id)
        if not resolved:
            raise ValueError("That slot is unavailable. Please choose one of the listed slots.")
        _taken.add(resolved)
        label = dict(_slots)[resolved]
        return {
            "reference_id": f"#REV-{random.randint(1000, 9999)}",
            "slot_id": resolved,
            "slot_label": label,
            "name": name,
            "email": email,
            "session_type": session_type,
        }

def reset_slots() -> None:
    """Reset reservations for tests and local development."""
    _taken.clear()

def extract_email(text: str) -> str | None:
    match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.I)
    return match.group(0) if match else None

