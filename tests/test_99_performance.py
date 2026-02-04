"""
Test Suite 99: Performance Diagnostics (Optional)
Validates performance claims - marked as optional for CI/CD
"""

import pytest
import aiohttp
import os
import time
import asyncio
import statistics

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")

@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.optional
async def test_latency_200_300ms_claim_diagnostic():
    """
    Diagnostic: Measure actual latency vs documented 200-300ms claim.
    This test is informational - it doesn't fail based on results.
    """
    iterations = int(os.getenv("ACP_PERF_ITERATIONS", "50"))
    
    payload = {
        "intent_type": "discover",
        "target_entity_id": "*",
        "intent_payload": {"location": "Hobart"}
    }
    
    latencies = []
    
    async with aiohttp.ClientSession() as session:
        # Warm-up
        for _ in range(5):
            try:
                async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=10):
                    pass
            except:
                pass
        
        await asyncio.sleep(0.5)  # Let system settle
        
        # Actual measurements
        for i in range(iterations):
            start = time.time()
            try:
                async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=10) as resp:
                    await resp.text()
                    latency = (time.time() - start) * 1000
                    latencies.append(latency)
            except Exception as e:
                print(f"   Request {i} failed: {e}")
    
    if not latencies:
        pytest.skip("No successful measurements")
    
    # Calculate statistics
    avg_latency = statistics.mean(latencies)
    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
    p99 = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
    min_lat = min(latencies)
    max_lat = max(latencies)
    
    print(f"\n📊 LATENCY DIAGNOSTIC REPORT:")
    print(f"   Target claim: 200-300ms average")
    print(f"   {'='*40}")
    print(f"   Iterations:   {len(latencies)}")
    print(f"   Average:      {avg_latency:.1f}ms")
    print(f"   Median (P50): {p50:.1f}ms")
    print(f"   P95:          {p95:.1f}ms")
    print(f"   P99:          {p99:.1f}ms")
    print(f"   Min/Max:      {min_lat:.1f}ms / {max_lat:.1f}ms")
    print(f"   {'='*40}")
    
    if avg_latency > 300:
        print(f"   ⚠️  RESULT: Average {avg_latency:.1f}ms EXCEEDS documented 300ms")
        print(f"       Recommendation: Update docs or optimize performance")
    elif avg_latency > 200:
        print(f"   ✅ RESULT: Within documented range (200-300ms)")
    else:
        print(f"   ✅ RESULT: Better than documented (< 200ms)")
    
    # Store for report
    pytest.latency_results = {
        "average": avg_latency,
        "p95": p95,
        "claim_met": avg_latency <= 300
    }
    
    # Don't fail - this is diagnostic
    assert True

@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.optional
async def test_throughput_100rps_claim_diagnostic():
    """
    Diagnostic: Measure throughput vs 100+ req/sec claim.
    """
    duration = int(os.getenv("ACP_PERF_DURATION", "10"))
    concurrency = int(os.getenv("ACP_PERF_CONCURRENCY", "50"))
    
    payload = {
        "intent_type": "discover",
        "target_entity_id": "*",
        "intent_payload": {"location": "Hobart"}
    }
    
    request_count = 0
    success_count = 0
    error_count = 0
    start_time = time.time()
    end_time = start_time + duration
    
    async def worker(session):
        nonlocal request_count, success_count, error_count
        while time.time() < end_time:
            try:
                async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=5) as resp:
                    request_count += 1
                    if resp.status == 200:
                        success_count += 1
                    else:
                        error_count += 1
            except:
                error_count += 1
                request_count += 1
    
    async with aiohttp.ClientSession() as session:
        workers = [asyncio.create_task(worker(session)) for _ in range(concurrency)]
        await asyncio.gather(*workers)
    
    actual_duration = time.time() - start_time
    rps = request_count / actual_duration
    success_rate = (success_count / request_count * 100) if request_count > 0 else 0
    
    print(f"\n📊 THROUGHPUT DIAGNOSTIC REPORT:")
    print(f"   Target claim: 100+ req/sec")
    print(f"   {'='*40}")
    print(f"   Duration:     {actual_duration:.1f}s")
    print(f"   Concurrency:  {concurrency}")
    print(f"   Total req:    {request_count}")
    print(f"   Successful:   {success_count}")
    print(f"   Errors:       {error_count}")
    print(f"   RPS:          {rps:.1f}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   {'='*40}")
    
    if rps < 100:
        print(f"   ⚠️  RESULT: {rps:.1f} RPS BELOW claimed 100+")
    else:
        print(f"   ✅ RESULT: Meets or exceeds claim")
    
    if success_rate < 95:
        print(f"   ❌ WARNING: Success rate {success_rate:.1f}% below 95% threshold")
    
    # Don't fail - diagnostic only
    assert True
