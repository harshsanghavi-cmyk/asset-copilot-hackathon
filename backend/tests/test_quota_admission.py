"""Deterministic clock checks of shared admission; no model or network calls."""
import asyncio
import sqlite3

import pytest
from backend.chains import gemma


@pytest.mark.asyncio
async def test_foreground_preempts_waiting_evaluation_and_input_window_holds(tmp_path, monkeypatch):
    clock = [1000.0]
    original_sleep = asyncio.sleep
    async def advance(seconds):
        clock[0] += seconds
        await original_sleep(0)
    monkeypatch.setattr(gemma.time, "time", lambda: clock[0])
    monkeypatch.setattr(gemma.asyncio, "sleep", advance)
    limiter = gemma.GlobalLimiter(tmp_path / "quota.sqlite", minimum_interval=0)
    with sqlite3.connect(limiter.path) as db:
        db.execute("INSERT INTO calls(kind,purpose,reserved_at,started_at,status,model_id,input_reservation,priority) VALUES('generation','existing',1000,'started','started',?,249000,0)", (gemma.MODEL,))
    background = asyncio.create_task(limiter.reserve("evaluation", input_tokens=2000, priority=10))
    await original_sleep(0)
    foreground_id = await limiter.reserve("user", input_tokens=500, priority=0)
    limiter.finish(foreground_id, "complete", 200, {"input_tokens": 500})
    background_id = await background
    calls = {r["id"]: r for r in limiter.stats()["calls"]}
    assert calls[foreground_id]["reserved_at"] < calls[background_id]["reserved_at"]
    assert calls[background_id]["reserved_at"] >= 1060
    assert limiter.stats()["generation_attempts"] == 3


@pytest.mark.asyncio
async def test_cancelled_queue_consumes_no_generation_allowance(tmp_path, monkeypatch):
    limiter = gemma.GlobalLimiter(tmp_path / "quota.sqlite", max_generations=1, minimum_interval=0)
    limiter.cooldown(gemma.MODEL, 60)
    queued = asyncio.create_task(limiter.reserve("waiting", input_tokens=100))
    await asyncio.sleep(.03)
    queued.cancel()
    with pytest.raises(asyncio.CancelledError):
        await queued
    assert limiter.stats()["generation_attempts"] == 0
    assert limiter.stats()["calls"][0]["status"] == "cancelled"
