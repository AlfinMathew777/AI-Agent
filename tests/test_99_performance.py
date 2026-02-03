# tests/test_99_performance.py
"""
PERFORMANCE TESTS (Marked, not default CI)
Run only when you want: pytest -m performance -v
"""

import os
import time
import statistics
import pytest
import aiohttp
import asyncio

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
SUBMIT_PATH = os.getenv("ACP_SUBMIT_PATH", "/acp/submit")

@pytest.mark.performance
@pytest.mark.asyncio
async def test_latency_200_300ms_claim_diagnostic():
    """Diagnostic performance test: does not enforce 200-300ms hard, only reports & asserts sanity."""
    payload = {
        "intent_type": "discover",
        "target_entity_id": "*",
        "intent_payload": {"location": "Hobart"}
    }

    lat = []
    async with aiohttp.ClientSession() as session:
        # warmup
        for _ in range(5):
            async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload):
                pass

        for _ in range(30):
            start = time.time()
            async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
                await resp.json()
            lat.append((time.time() - start) * 1000)

    avg = statistics.mean(lat)
    p95 = sorted(lat)[int(len(lat) * 0.95)]

    print(f"[PERF] avg={avg:.1f}ms p95={p95:.1f}ms")
    assert avg < 1500, "Latency too high (sanity threshold)"
