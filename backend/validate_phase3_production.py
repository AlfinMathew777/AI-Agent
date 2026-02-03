"""
Phase 3 Production Validation Script
Validates all components are operational and production-ready
"""

import os
import sys
import asyncio
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

RESULTS = {"passed": 0, "failed": 0, "errors": []}

def test(name):
    """Decorator for test functions"""
    def decorator(func):
        async def wrapper():
            try:
                print(f"\n[TEST] {name}...")
                result = await func() if asyncio.iscoroutinefunction(func) else func()
                if result:
                    print(f"  [PASS] {name}")
                    RESULTS["passed"] += 1
                    return True
                else:
                    print(f"  [FAIL] {name}")
                    RESULTS["failed"] += 1
                    RESULTS["errors"].append(name)
                    return False
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
                RESULTS["failed"] += 1
                RESULTS["errors"].append(f"{name}: {e}")
                return False
        return wrapper
    return decorator


# ============================================================================
# SECTION 1: DATABASE VALIDATION
# ============================================================================

@test("6 SQLite databases exist")
def validate_databases():
    databases = [
        'acp_properties.db',
        'acp_trust.db',
        'acp_transactions.db',
        'acp_commissions.db',
        'acp_network.db',
        'acp_monitoring.db'
    ]
    
    for db in databases:
        if os.path.exists(db):
            print(f"    [OK] {db}")
        else:
            print(f"    [MISSING] {db}")
            return False
    return True


# ============================================================================
# SECTION 2: CORE INFRASTRUCTURE VALIDATION
# ============================================================================

@test("1. Multi-Tenant Property Registry")
async def validate_property_registry():
    from app.properties.registry import PropertyRegistry
    
    registry = PropertyRegistry()
    props = registry.list_active_properties()
    
    if len(props) >= 5:
        print(f"    [OK] {len(props)} properties registered")
        for p in props[:5]:
            tier = p.config_json.get("tier", "unknown")
            print(f"      - {p.name} ({tier})")
        return True
    else:
        print(f"    [FAIL] Only {len(props)} properties (expected >= 5)")
        return False


@test("2. PMS Adapter Factory")
async def validate_adapter_factory():
    from app.acp.domains.hotel.adapter_factory import get_adapter
    
    # Test sandbox adapter
    adapter = await get_adapter("hotel_tas_luxury")
    if adapter:
        print(f"    [OK] Adapter factory working")
        return True
    return False


@test("3. Tier-Aware Negotiation Engine")
async def validate_negotiation_engine():
    from app.acp.negotiation.engine import NegotiationEngine
    
    engine = NegotiationEngine()
    await engine.initialize()
    print(f"    [OK] Negotiation engine initialized")
    return True


@test("4. Admin Property Onboarding Routes")
def validate_property_routes():
    from app.acp.api.routes import properties
    
    # Check router exists
    if hasattr(properties, 'router'):
        print(f"    [OK] Property routes registered")
        return True
    return False


@test("5. Agent Self-Registration Routes")
def validate_agent_routes():
    from app.acp.api.routes import agents
    
    if hasattr(agents, 'router'):
        print(f"    [OK] Agent routes registered")
        return True
    return False


@test("6. Marketplace Discovery Routes")
def validate_marketplace_routes():
    from app.acp.api.routes import marketplace
    
    if hasattr(marketplace, 'router'):
        print(f"    [OK] Marketplace routes registered")
        # Check for sqlite3 import
        import inspect
        source = inspect.getsource(marketplace)
        if 'import sqlite3' in source:
            print(f"    [OK] sqlite3 import present")
            return True
        else:
            print(f"    [FAIL] Missing 'import sqlite3'")
            return False
    return False


@test("7. Commission Ledger")
async def validate_commission_ledger():
    from app.acp.commissions.ledger import get_property_commissions
    
    # Test function exists
    result = await get_property_commissions("hotel_tas_luxury")
    print(f"    [OK] Commission ledger operational")
    return True


@test("8. Monitoring & Alerts")
async def validate_monitoring():
    from app.monitoring.dashboard import get_dashboard_stats
    
    stats = await get_dashboard_stats()
    print(f"    [OK] Monitoring dashboard operational")
    return True


# ============================================================================
# SECTION 3: DEMO DATA VALIDATION
# ============================================================================

@test("Demo Data: 5 Properties Seeded")
def validate_demo_properties():
    conn = sqlite3.connect('acp_properties.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
    count = cur.fetchone()[0]
    conn.close()
    
    expected_names = [
        "The Grand Tasman Hotel",
        "Boutique Salamanca Inn",
        "Hobart Central Budget Stay",
        "Launceston Riverside Hotel",
        "Devonport Express Lodge"
    ]
    
    if count >= 5:
        print(f"    [OK] {count} active properties")
        return True
    else:
        print(f"    [FAIL] Only {count} properties (expected >= 5)")
        return False


@test("Demo Data: 8 Verified Agents Seeded")
def validate_demo_agents():
    import json
    conn = sqlite3.connect('acp_trust.db')
    cur = conn.cursor()
    
    # Agent data is stored as JSON in identity_json column
    cur.execute('SELECT identity_json FROM agent_identities')
    rows = cur.fetchall()
    
    verified_count = 0
    for row in rows:
        identity = json.loads(row[0])
        if identity.get('verification_status') == 'verified':
            verified_count += 1
    
    conn.close()
    
    if verified_count >= 8:
        print(f"    [OK] {verified_count} verified agents")
        return True
    else:
        print(f"    [FAIL] Only {verified_count} verified agents (expected >= 8)")
        return False


@test("Demo Data: Marketplace Connections")
def validate_marketplace_connections():
    conn = sqlite3.connect('acp_trust.db')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM agent_marketplace_connections')
    count = cur.fetchone()[0]
    conn.close()
    
    if count >= 10:
        print(f"    [OK] {count} marketplace connections")
        return True
    else:
        print(f"    [FAIL] Only {count} connections (expected >= 10)")
        return False


# ============================================================================
# SECTION 4: NETWORK EFFECTS MODULE
# ============================================================================

@test("Network Effects Module Exists")
def validate_network_effects():
    try:
        from app.acp import network_effects
        
        # Check functions exist
        funcs = ['record_demand_signal', 'generate_weekly_summary', 'get_network_insights']
        for func in funcs:
            if not hasattr(network_effects, func):
                print(f"    [FAIL] Missing function: {func}")
                return False
        
        print(f"    [OK] All network effects functions present")
        return True
    except ImportError as e:
        print(f"    [FAIL] Cannot import network_effects: {e}")
        return False


# ============================================================================
# SECTION 5: FILE VALIDATION
# ============================================================================

@test("Integration Test Suite Exists")
def validate_integration_tests():
    path = Path("tests/test_phase3_integration.py")
    if path.exists():
        print(f"    [OK] {path}")
        return True
    else:
        print(f"    [FAIL] Missing {path}")
        return False


@test("Failover Test Exists")
def validate_failover_test():
    path = Path("tests/test_pms_failover.py")
    if path.exists():
        print(f"    [OK] {path}")
        return True
    else:
        print(f"    [FAIL] Missing {path}")
        return False


@test("Demo Seeder Exists")
def validate_demo_seeder():
    path = Path("app/acp/dev/seed_phase3_demo.py")
    if path.exists():
        print(f"    [OK] {path}")
        return True
    else:
        print(f"    [FAIL] Missing {path}")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def run_all_validations():
    print("=" * 70)
    print("PHASE 3 PRODUCTION READINESS VALIDATION")
    print("=" * 70)
    
    # Section 1
    print("\n" + "-" * 70)
    print("SECTION 1: DATABASE VALIDATION")
    print("-" * 70)
    await validate_databases()
    
    # Section 2
    print("\n" + "-" * 70)
    print("SECTION 2: CORE INFRASTRUCTURE (8 COMPONENTS)")
    print("-" * 70)
    await validate_property_registry()
    await validate_adapter_factory()
    await validate_negotiation_engine()
    await validate_property_routes()
    await validate_agent_routes()
    await validate_marketplace_routes()
    await validate_commission_ledger()
    await validate_monitoring()
    
    # Section 3
    print("\n" + "-" * 70)
    print("SECTION 3: DEMO DATA VALIDATION")
    print("-" * 70)
    await validate_demo_properties()
    await validate_demo_agents()
    await validate_marketplace_connections()
    
    # Section 4
    print("\n" + "-" * 70)
    print("SECTION 4: NETWORK EFFECTS MODULE")
    print("-" * 70)
    await validate_network_effects()
    
    # Section 5
    print("\n" + "-" * 70)
    print("SECTION 5: TEST FILES")
    print("-" * 70)
    await validate_integration_tests()
    await validate_failover_test()
    await validate_demo_seeder()
    
    # Results
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print(f"PASSED: {RESULTS['passed']}")
    print(f"FAILED: {RESULTS['failed']}")
    
    if RESULTS["failed"] > 0:
        print("\nFailed tests:")
        for error in RESULTS["errors"]:
            print(f"  - {error}")
        print("\n[STATUS] NOT PRODUCTION READY")
        return False
    else:
        print("\n[STATUS] PRODUCTION READY [OK]")
        return True


if __name__ == "__main__":
    success = asyncio.run(run_all_validations())
    sys.exit(0 if success else 1)
