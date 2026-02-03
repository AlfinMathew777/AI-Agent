"""
Manually add missing properties to avoid database locking issues
"""

from app.properties.registry import PropertyRegistry

registry = PropertyRegistry()

# Property 4: Boutique Salamanca Inn
prop4 = {
    "property_id": "hotel_tas_standard",
    "name": "Boutique Salamanca Inn",
    "pms_type": "sandbox",
    "config": {
        "tier": "standard",
        "location": "Hobart, TAS",
        "amenities": {
            "breakfast": True,
            "wifi": True,
            "parking": True
        },
        "share_demand_signals": True
    }
}

# Property 5: Hobart Central Budget Stay
prop5 = {
    "property_id": "hotel_tas_budget",
    "name": "Hobart Central Budget Stay",
    "pms_type": "sandbox",
    "config": {
        "tier": "budget",
        "location": "Hobart, TAS",
        "amenities": {
            "wifi": True,
            "24hr_checkin": True
        },
        "share_demand_signals": False
    }
}

print("Adding remaining 2 properties...")
result1 = registry.register_property(prop4)
print(f"Boutique Salamanca Inn: {'SUCCESS' if result1 else 'ALREADY EXISTS'}")

result2 = registry.register_property(prop5)
print(f"Hobart Central Budget Stay: {'SUCCESS' if result2 else 'ALREADY EXISTS'}")

# Verify all 5 properties
props = registry.list_active_properties()
print(f"\nTotal active properties: {len(props)}")
for p in props:
    tier = p.config_json.get("tier", "unknown")
    print(f"  - {p.name} ({tier})")

print("\n[SUCCESS] All 5 properties now registered!")
