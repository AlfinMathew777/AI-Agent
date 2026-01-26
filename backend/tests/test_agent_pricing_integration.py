
import pytest
import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.planner.runner import PlanRunner
from app.agent.planner.types import Plan, PlanStep
from app.agent.tools import ToolRegistry
from app.db.session import init_db

# Mock Tool Registry
class MockToolRegistry:
    async def execute(self, tool_name, params):
        if tool_name == "reserve_table":
            return f"Reservation Confirmed! ID: bk_mock_123 (Table 5)"
        return "Done"

@pytest.mark.asyncio
async def test_agent_quote_flow():
    print("\n--- Starting Agent Pricing Integration Test ---")
    init_db()
    
    # Setup
    tools = MockToolRegistry()
    runner = PlanRunner(tools)
    
    import uuid
    # Create a Plan with a WRITE step
    session_id = "sess_pricing_integ"
    plan = Plan(
        id=str(uuid.uuid4()),
        session_id=session_id,
        audience="guest",
        question="Book table",
        plan_summary="Booking test",
        steps=[
            PlanStep(
                step_index=0, step_type="TOOL", tool_name="reserve_table",
                tool_args={"restaurant_id": "r1", "party_size": 2, "date": "tomorrow"},
                risk="WRITE"
            )
        ],
        plan_mode="commit",
        context={"restaurants": {"restaurants": [{"name": "Mock Grill", "id": "r1"}]}}
    )
    
    # 1. Run Plan -> Should Pause for Confirmation + Produce Quote
    result = await runner.run_plan(plan)
    
    print(f"[Test] Phase 1 Result Status: {result['status']}")
    assert result["status"] == "needs_confirmation"
    assert "quote" in result
    print(f"[Test] Generated Quote: {json.dumps(result['quote']['totals'], indent=2)}")
    
    # Verify Quote Content
    # Default dinner price per person is 4500 cents. 2 people = 9000.
    # Tax 10% = 900. Fees = 250. Total = 10150.
    assert result['quote']['totals']['total_cents'] == 10150
    
    action_id = result["action_id"]
    print(f"[Test] Action ID: {action_id}")
    
    # 2. Confirm Action
    # Resume plan
    print("[Test] Confirming Action...")
    final_result = await runner.resume_plan(action_id, confirm=True)
    
    print(f"[Test] Phase 2 Result: {final_result['status']}")
    assert final_result["status"] == "success"
    
    # Verify Receipt Usage
    # The output should contain "(Receipt Generated)"
    answer = final_result["answer"]
    print(f"[Test] Final Output: {answer}")
    assert "(Receipt Generated)" in answer

    print("--- Agent Pricing Integration Test Passed ---")

if __name__ == "__main__":
    asyncio.run(test_agent_quote_flow())
