from .types import Plan, PlanStep
from app.agent.tools import ToolRegistry

class PlanValidator:
    def __init__(self, tool_registry: ToolRegistry):
        self.tools = tool_registry

    def validate_plan(self, plan: Plan) -> Plan:
        """
        Validate plan safety and policy compliance.
        Raises ValueError if invalid.
        """
        
        # 1. Limit steps
        if len(plan.steps) > 5:
            raise ValueError("Plan too complex (max 5 steps).")

        for step in plan.steps:
            if step.step_type == "TOOL":
                # Check existance
                tool_def = self.tools.get_tool(step.tool_name)
                if not tool_def:
                    raise ValueError(f"Unknown tool: {step.tool_name}")
                
                # Check Audience Policy
                # Guest only allowed: check_room_availability
                # Guest only allowed: check_room_availability
                allowed_guest_tools = [
                    "check_room_availability", "book_room", 
                    "list_restaurants", "list_events", 
                    "check_table_availability", "check_event_availability",
                    "reserve_table", "buy_event_tickets"
                ]
                if plan.audience == "guest" and step.tool_name not in allowed_guest_tools:
                     raise ValueError(f"Full guest access not yet implemented for {step.tool_name}")
                
                # Enforce Risk (Don't trust LLM/User provided risk)
                step.risk = tool_def["risk"]
                
        return plan
