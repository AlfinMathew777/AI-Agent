import pytest
import asyncio
import json
import uuid
import sys
import os

# Ensure paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.planner.types import Plan, PlanStep
from app.agent.planner.runner import PlanRunner
from app.agent.tools import ToolRegistry
from app.db.session import init_db
from app.db.queries import create_plan, get_plan

class MockMCP:
    pass

class MockTools(ToolRegistry):
    def __init__(self):
        super().__init__(MockMCP())

    async def execute(self, tool_name, params):
        if tool_name == "check_room_availability":
            return "Yes, available."
        if tool_name == "book_room":
            return "Booked 123."
        return "Unknown"

@pytest.fixture
def runner():
    # Helper: Init DB in-memory or file for test
    # Ideally we mock the DB, but for integration test we use real SQLite 
    # (assuming test config overrides DB path or we use the default dev.db)
    # BEWARE: This uses the REAL dev database if configured that way.
    # Safe checks:
    init_db() 
    return PlanRunner(MockTools())

@pytest.mark.asyncio
async def test_runner_read_only(runner):
    # Plan with 1 READ step
    plan = Plan(
        id=str(uuid.uuid4()),
        session_id="test_sess_read",
        audience="guest",
        question="Check avail",
        plan_summary="test",
        steps=[
            PlanStep(
                step_index=0, step_type="TOOL", tool_name="check_room_availability", 
                tool_args={}, risk="READ"
            )
        ]
    )
    
    result = await runner.run_plan(plan)
    assert result["status"] == "success"
    assert "Yes, available" in result["answer"]

@pytest.mark.asyncio
async def test_runner_write_needs_confirmation(runner):
    # Plan with WRITE step
    plan = Plan(
        id=str(uuid.uuid4()),
        session_id="test_sess_write",
        audience="staff",
        question="Book room",
        plan_summary="test",
        steps=[
            PlanStep(
                step_index=0, step_type="TOOL", tool_name="book_room", 
                tool_args={}, risk="WRITE"
            )
        ]
    )
    
    result = await runner.run_plan(plan)
    assert result["status"] == "needs_confirmation"
    assert "action_id" in result
    
    # Verify in DB
    db_plan = get_plan(plan.id)
    assert db_plan['plan']['status'] == "needs_confirmation"
    assert db_plan['steps'][0]['status'] == "pending"

