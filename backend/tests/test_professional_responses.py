"""
Tests for Professional Chat Responses
Ensures customer-facing messages hide internal steps and tool details.
"""
import pytest
from app.agent.planner.runner import PlanRunner
from app.agent.planner.types import Plan, PlanStep
from app.agent.tools import ToolRegistry
from app.llm import HotelAI


def test_customer_message_no_steps():
    """Test that customer messages don't contain 'Step' or 'Tool' keywords."""
    # Mock tool registry
    hotel_ai = HotelAI()
    tool_registry = ToolRegistry(hotel_ai.mcp_client)
    runner = PlanRunner(tool_registry)
    
    # Create a mock plan with successful booking
    plan = Plan(
        id="test-plan-1",
        session_id="test-session",
        audience="guest",
        question="Book a room for tomorrow",
        plan_summary="Book standard room",
        steps=[
            PlanStep(
                step_index=0,
                step_type="TOOL",
                tool_name="book_room",
                tool_args={"room_type": "Standard", "date": "Tomorrow"},
                risk="WRITE",
                status="success",
                result='{"booking_id": "BK-12345", "receipt_id": "RCP-67890", "room_type": "Standard", "date_human": "Tomorrow"}'
            )
        ],
        status="completed"
    )
    
    # Format message
    result = runner._format_customer_message(plan, [], last_tool_result={"booking_id": "BK-12345", "receipt_id": "RCP-67890", "room_type": "Standard", "date_human": "Tomorrow"})
    
    # Assertions
    assert "Step" not in result["answer"]
    assert "Tool" not in result["answer"]
    assert "BK-12345" in result["answer"]  # Booking ID should be present
    assert "RCP-67890" in result["answer"]  # Receipt ID should be present
    assert "✅" in result["answer"]  # Should have success indicator


def test_customer_message_explore_mode():
    """Test explore mode returns options message."""
    hotel_ai = HotelAI()
    tool_registry = ToolRegistry(hotel_ai.mcp_client)
    runner = PlanRunner(tool_registry)
    
    plan = Plan(
        id="test-plan-2",
        session_id="test-session",
        audience="guest",
        question="Show me restaurants",
        plan_summary="Explore dining options",
        steps=[
            PlanStep(
                step_index=0,
                step_type="TOOL",
                tool_name="list_restaurants",
                tool_args={},
                risk="READ",
                status="success",
                result='{"restaurants": [{"name": "Test Bistro"}]}'
            )
        ],
        status="completed",
        plan_mode="explore"
    )
    
    # For explore mode, should return needs_input
    # This is handled in _execute_loop, but we can test the message format
    result = runner._format_customer_message(plan, [], last_tool_result={"options": ["Test Bistro"]})
    
    # Should not contain step details
    assert "Step" not in result["answer"]
    assert "Tool" not in result["answer"]


def test_customer_message_fallback():
    """Test fallback when no booking details found."""
    hotel_ai = HotelAI()
    tool_registry = ToolRegistry(hotel_ai.mcp_client)
    runner = PlanRunner(tool_registry)
    
    plan = Plan(
        id="test-plan-3",
        session_id="test-session",
        audience="guest",
        question="Check availability",
        plan_summary="Check room availability",
        steps=[
            PlanStep(
                step_index=0,
                step_type="TOOL",
                tool_name="check_room_availability",
                tool_args={},
                risk="READ",
                status="success",
                result="Available"
            )
        ],
        status="completed"
    )
    
    result = runner._format_customer_message(plan, [], last_tool_result=None)
    
    # Should still be professional, no step details
    assert "Step" not in result["answer"]
    assert "Tool" not in result["answer"]
    assert "✅" in result["answer"]  # Should have success indicator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
