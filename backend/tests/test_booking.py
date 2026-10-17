import pytest
from app.tools.booking import book_slot, list_slots, reset_slots

@pytest.mark.asyncio
async def test_booking_happy_path():
    reset_slots()
    result = await book_slot("tomorrow-11", "Alex Chen", "alex@example.com", "Performance Review")
    assert result["reference_id"].startswith("#REV-")
    assert not any(slot["slot_id"] == "tomorrow-11" for slot in list_slots())

@pytest.mark.asyncio
async def test_taken_slot_rejected():
    reset_slots()
    await book_slot("tomorrow-11", "Alex Chen", "alex@example.com", "Performance Review")
    with pytest.raises(ValueError):
        await book_slot("tomorrow-11", "Sam Lee", "sam@example.com", "Performance Review")

