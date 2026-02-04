"""
Test Suite 0: Path Discovery (Non-Failing)
Purpose: Discover working API paths without breaking CI/CD pipelines
These tests NEVER FAIL - they only report what they find for documentation updates
"""

import pytest
import aiohttp
import os
import asyncio

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")

@pytest.mark.asyncio
@pytest.mark.probe
async def test_probe_agent_registration_paths():
    """
    Discover working agent registration endpoints.
    Doc says: /acp/agents/register
    Repo has: /acp/register (gateway_server.py line 94)
    """
    async with aiohttp.ClientSession() as session:
        test_payload = {
            "agent_id": f"probe_{asyncio.get_event_loop().time()}",
            "name": "Path Probe Agent",
            "agent_type": "probe",
            "identity_blob": {"email": "probe@test.com"},
            "initial_reputation": 0.50
        }
        
        paths_to_test = [
            "/acp/agents/register",  # Documented
            "/acp/register",         # Actual implementation
            "/api/agents/register",
            "/agents/register"
        ]
        
        results = {}
        for path in paths_to_test:
            try:
                async with session.post(f"{BASE_URL}{path}", json=test_payload, timeout=5) as resp:
                    results[path] = {
                        "status": resp.status,
                        "working": resp.status in [200, 201, 400]  # 400 = validation error (endpoint exists)
                    }
            except Exception as e:
                results[path] = {"status": "error", "error": str(e), "working": False}
        
        # Print findings for documentation update
        print("\n📡 AGENT REGISTRATION PATH DISCOVERY:")
        working_paths = [p for p, r in results.items() if r.get("working")]
        print(f"   Working paths found: {working_paths}")
        
        for path, result in results.items():
            status = "✅" if result.get("working") else "❌"
            print(f"   {status} {path}: {result.get('status')}")
        
        if "/acp/agents/register" not in working_paths and "/acp/register" in working_paths:
            print("   ⚠️  DOCUMENTATION MISMATCH DETECTED:")
            print("       Doc says: /acp/agents/register")
            print("       Actual:   /acp/register")
            print("       Action:   Update Section 2.1.3 in ACP_TECHNICAL_DOCUMENTATION.md")
        
        # Always pass - this is discovery only
        assert True

@pytest.mark.asyncio
@pytest.mark.probe
async def test_probe_marketplace_paths():
    """
    Discover working marketplace endpoints.
    Doc says: /marketplace/properties
    Need to verify: Full mounted path in app_factory.py
    """
    async with aiohttp.ClientSession() as session:
        paths_to_test = [
            "/marketplace/properties",      # Documented
            "/acp/marketplace/properties",  # Likely with prefix
            "/api/marketplace/properties",
            "/properties"                   # Alternative
        ]
        
        results = {}
        for path in paths_to_test:
            try:
                async with session.get(f"{BASE_URL}{path}", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results[path] = {
                            "status": resp.status,
                            "working": True,
                            "has_properties": "properties" in data or isinstance(data, list)
                        }
                    else:
                        results[path] = {"status": resp.status, "working": False}
            except Exception as e:
                results[path] = {"status": "error", "error": str(e), "working": False}
        
        print("\n📡 MARKETPLACE PATH DISCOVERY:")
        working_paths = [p for p, r in results.items() if r.get("working")]
        print(f"   Working paths found: {working_paths}")
        
        for path, result in results.items():
            status = "✅" if result.get("working") else "❌"
            detail = " (has properties)" if result.get("has_properties") else ""
            print(f"   {status} {path}: {result.get('status')}{detail}")
        
        if working_paths and "/marketplace/properties" not in working_paths:
            print(f"   ⚠️  DOCUMENTATION MISMATCH:")
            print(f"       Doc says: /marketplace/properties")
            print(f"       Actual:   {working_paths[0]}")
        
        assert True

@pytest.mark.asyncio
@pytest.mark.probe
async def test_probe_monitoring_paths():
    """
    Discover working monitoring dashboard paths.
    Doc says: GET /admin/monitoring/dashboard
    Repo has: GET /dashboard in monitoring.py line 13
    """
    admin_key = os.getenv("ACP_ADMIN_KEY", "test_admin_key")
    headers = {"X-Admin-Key": admin_key}
    
    async with aiohttp.ClientSession() as session:
        paths_to_test = [
            "/admin/monitoring/dashboard",  # Documented
            "/dashboard",                   # Actual in monitoring.py
            "/acp/dashboard",
            "/admin/dashboard",
            "/monitoring/dashboard"
        ]
        
        results = {}
        for path in paths_to_test:
            try:
                async with session.get(f"{BASE_URL}{path}", headers=headers, timeout=5) as resp:
                    results[path] = {
                        "status": resp.status,
                        "working": resp.status == 200,
                        "content_type": resp.headers.get("content-type", "unknown")
                    }
            except Exception as e:
                results[path] = {"status": "error", "error": str(e), "working": False}
        
        print("\n📡 MONITORING DASHBOARD PATH DISCOVERY:")
        working_paths = [p for p, r in results.items() if r.get("working")]
        print(f"   Working paths found: {working_paths}")
        
        for path, result in results.items():
            status = "✅" if result.get("working") else "❌"
            print(f"   {status} {path}: HTTP {result.get('status')}")
        
        if working_paths and "/admin/monitoring/dashboard" not in working_paths:
            print(f"   ⚠️  DOCUMENTATION MISMATCH:")
            print(f"       Doc says: /admin/monitoring/dashboard")
            print(f"       Actual:   {working_paths[0]}")
        
        assert True

@pytest.mark.asyncio
@pytest.mark.probe
async def test_probe_submit_paths():
    """
    Discover working submit endpoint for intent submission.
    Critical: Contract tests hardcode /acp/submit - this verifies it works.
    """
    async with aiohttp.ClientSession() as session:
        test_payload = {
            "intent_type": "discover",
            "request_id": f"probe_{asyncio.get_event_loop().time()}",
            "target_entity_id": "probe_test",
            "intent_payload": {
                "dates": {"check_in": "2026-05-01", "check_out": "2026-05-03"},
                "room_type": "any",
                "guests": 2
            }
        }
        
        paths_to_test = [
            "/acp/submit",          # Current hardcoded path
            "/api/acp/submit",      # With API prefix
            "/submit",              # Direct mount
            "/acp/intents/submit"   # Alternative structure
        ]
        
        results = {}
        for path in paths_to_test:
            try:
                async with session.post(f"{BASE_URL}{path}", json=test_payload, timeout=5) as resp:
                    results[path] = {
                        "status": resp.status,
                        "working": resp.status in [200, 201, 400, 422]  # 400/422 = validation (endpoint exists)
                    }
            except Exception as e:
                results[path] = {"status": "error", "error": str(e), "working": False}
        
        print("\n📡 SUBMIT ENDPOINT PATH DISCOVERY:")
        working_paths = [p for p, r in results.items() if r.get("working")]
        print(f"   Working paths found: {working_paths}")
        
        for path, result in results.items():
            status = "✅" if result.get("working") else "❌"
            print(f"   {status} {path}: {result.get('status')}")
        
        if working_paths and "/acp/submit" not in working_paths:
            print(f"   ⚠️  HARDCODED PATH MISMATCH:")
            print(f"       Contract tests use: /acp/submit")
            print(f"       Actual working:     {working_paths[0]}")
            print(f"       Action: Update test_01_contract_endpoints.py or use ACP_PREFIX env var")
        
        assert True

