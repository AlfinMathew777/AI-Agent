# tests/test_00_probes_paths.py
"""
Probes (Non-failing discovery)
This is NOT strict — it prints working paths so you can fix docs.
"""

import os
import pytest
import aiohttp

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ACP_ADMIN_KEY", "")

@pytest.mark.asyncio
async def test_probe_agent_registration_paths(capsys):
    """Probe possible agent registration paths (does not fail if mismatch)."""
    paths = ["/acp/agents/register", "/acp/register", "/register"]
    payload = {
        "agent_id": "probe_agent_001",
        "name": "Probe Agent",
        "agent_type": "probe",
        "identity_blob": {},
        "initial_reputation": 0.5
    }

    working = []
    async with aiohttp.ClientSession() as session:
        for p in paths:
            try:
                async with session.post(f"{BASE_URL}{p}", json=payload) as resp:
                    if resp.status in (200, 201, 409):  # 409 if agent already exists
                        working.append((p, resp.status))
            except Exception:
                pass

    print(f"[PROBE] Agent register working paths: {working}")
    assert True


@pytest.mark.asyncio
async def test_probe_marketplace_paths():
    """Probe marketplace mounted prefix paths."""
    paths = [
        "/marketplace/properties",
        "/acp/marketplace/properties",
        "/api/marketplace/properties",
    ]
    working = []

    async with aiohttp.ClientSession() as session:
        for p in paths:
            try:
                async with session.get(f"{BASE_URL}{p}") as resp:
                    if resp.status == 200:
                        working.append(p)
            except Exception:
                pass

    print(f"[PROBE] Marketplace working paths: {working}")
    assert True


@pytest.mark.asyncio
async def test_probe_monitoring_paths():
    """Probe monitoring dashboard mounted prefix paths."""
    headers = {"X-Admin-Key": ADMIN_KEY} if ADMIN_KEY else {}
    paths = [
        "/admin/monitoring/dashboard",
        "/admin/dashboard",
        "/dashboard",
        "/acp/dashboard",
        "/acp/admin/dashboard",
    ]
    working = []

    async with aiohttp.ClientSession() as session:
        for p in paths:
            try:
                async with session.get(f"{BASE_URL}{p}", headers=headers) as resp:
                    if resp.status == 200:
                        working.append(p)
            except Exception:
                pass

    print(f"[PROBE] Monitoring working paths: {working}")
    assert True
