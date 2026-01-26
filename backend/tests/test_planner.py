import pytest
import asyncio
from app.agent.tools import ToolRegistry
from app.agent.planner.planner import HybridPlanner

class MockMCP:
    pass

@pytest.fixture
def planner():
    registry = ToolRegistry(MockMCP())
    return HybridPlanner(registry)

@pytest.mark.asyncio
async def test_planner_rules_booking(planner):
    # Test "book room" rule
    q = "Book a standard room for me tomorrow"
    plan = await planner.plan("staff", q, "sess_1")
    
    assert plan is not None
    assert len(plan.steps) == 2
    assert plan.steps[0].tool_name == "check_room_availability"
    assert plan.steps[0].risk == "READ"
    assert plan.steps[1].tool_name == "book_room"
    assert plan.steps[1].risk == "WRITE"

@pytest.mark.asyncio
async def test_planner_rules_availability(planner):
    # Test "check availability" rule
    q = "Check if standard room is available"
    plan = await planner.plan("guest", q, "sess_2")
    
    assert plan is not None
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "check_room_availability"
    assert plan.steps[0].risk == "READ"

@pytest.mark.asyncio
async def test_planner_fallback(planner):
    # Test unknown intent returns None (fallback)
    q = "What is the capital of France?"
    plan = await planner.plan("guest", q, "sess_3")
    
    assert plan is None
