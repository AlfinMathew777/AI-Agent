import uuid
from typing import Optional, List, Dict, Any
from .types import Plan, PlanStep
from app.agent.tools import ToolRegistry

class HybridPlanner:
    def __init__(self, tool_registry: ToolRegistry):
        self.tools = tool_registry

    async def plan(self, audience: str, question: str, session_id: str, context: Dict[str, Any] = {}) -> Optional[Plan]:
        print(f"[DEBUG] Planner.plan called with q='{question}'", flush=True)
        """
        Create a plan based on the question.
        Returns None if no clear plan can be determined (fallback to old router).
        """
        # 1. Check for Commit Intent (Selection from Explore)
        if context and ("restaurants" in context or "events" in context):
             commit_steps = self._plan_commit(question, context)
             if commit_steps:
                 return Plan(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    audience=audience,
                    question=question,
                    plan_summary=f"Booking selection: {question[:30]}",
                    steps=commit_steps,
                    plan_mode="commit"
                 )

        # 2. Rules-based Logic (Explore)
        steps = self._plan_rules(audience, question)
        
        # 2. LLM-based Logic (Future/Stub)
        if not steps:
            # steps = await self._plan_llm(audience, question)
            pass
            
        if not steps:
            return None
            
        # 3. Create Plan Object
        plan_id = str(uuid.uuid4())
        
        # Determine Mode: If steps have save_as, it's explore
        is_explore = any(s.save_as for s in steps)
        mode = "explore" if is_explore else "commit"

        plan = Plan(
            id=plan_id,
            session_id=session_id,
            audience=audience,
            question=question,
            plan_summary=f"Automated plan for: {question[:30]}...",
            steps=steps,
            plan_mode=mode
        )
        
        return plan

    def _plan_rules(self, audience: str, question: str) -> List[PlanStep]:
        """Deterministic rules for MVP."""
        steps = []
        q_lower = question.lower()
        print(f"[DEBUG] Planner Rules: Checking '{q_lower}'")
        
        q_lower = question.lower()
        print(f"[DEBUG] Planner Rules: Checking '{q_lower}'")
        
        # Intent: Experience Package (Explore Phase) - PRIORITY 1
        if "night" in q_lower or "package" in q_lower or ("dinner" in q_lower and "show" in q_lower):
            print("[DEBUG] Matched Experience Package Rule", flush=True)
            # Parse Party Size
            party_size = 2
            if "for 1" in q_lower: party_size = 1
            if "for 3" in q_lower: party_size = 3
            if "for 4" in q_lower: party_size = 4
            
            # Parse Date logic (Stub)
            date = "Tomorrow" 
            
            # Step 1: Check Room Avail
            steps.append(PlanStep(
                step_index=0, step_type="TOOL", tool_name="check_room_availability",
                tool_args={"room_type": "standard", "date": date}, risk="READ",
                save_as="room_availability"
            ))
            
            # Step 2: List Restaurants
            steps.append(PlanStep(
                step_index=1, step_type="TOOL", tool_name="list_restaurants",
                tool_args={"date": date, "party_size": party_size}, risk="READ",
                save_as="restaurants"
            ))
            
            # Step 3: List Events
            steps.append(PlanStep(
                step_index=2, step_type="TOOL", tool_name="list_events",
                tool_args={"date": date, "party_size": party_size}, risk="READ",
                save_as="events"
            ))
            
        # Intent: Check Availability
        elif "check" in q_lower and ("availab" in q_lower or "room" in q_lower) and "book" not in q_lower:
            print("[DEBUG] Matched Check Availability Rule", flush=True)
            # Parse Party Size
            # ... existing logic simplified ...
            room_type = "standard" 
            if "suite" in q_lower: room_type = "suite"
            elif "deluxe" in q_lower: room_type = "deluxe"
            
            steps.append(PlanStep(
                step_index=0,
                step_type="TOOL",
                tool_name="check_room_availability",
                tool_args={"room_type": room_type, "date": "Tomorrow"}, # Mock date extraction
                risk="READ" 
            ))
            
        elif "book" in q_lower or "reserve" in q_lower:
            print("[DEBUG] Matched Book Rule", flush=True)
            # ... existing single action logic ...
            # Reuse existing but ensure we don't break
            room_type = "standard"
            if "suite" in q_lower: room_type = "suite"
            
            steps.append(PlanStep(
                step_index=0,
                step_type="TOOL",
                tool_name="check_room_availability",
                tool_args={"room_type": room_type, "date": "Tomorrow"},
                risk="READ"
            ))
            
            steps.append(PlanStep(
                step_index=1,
                step_type="TOOL",
                tool_name="book_room",
                tool_args={"guest_name": "Guest", "room_type": room_type, "date": "Tomorrow"},
                risk="WRITE"
            ))
            
        return steps

    def _plan_commit(self, question: str, context: Dict[str, Any]) -> List[PlanStep]:
        """
        Parse user selection against context context to build Commit Plan.
        """
        steps = []
        q_lower = question.lower()
        print(f"[DEBUG] _plan_commit: Checking '{q_lower}' against context {list(context.keys())}", flush=True)
        
        # 1. Identify Restaurant
        selected_restaurant = None
        if "restaurants" in context:
            data = context["restaurants"]
            # Handle both list and dict wrapper
            r_list = data.get("restaurants", []) if isinstance(data, dict) else []
            
            for r in r_list:
                # Fuzzy match name
                if r["name"].lower() in q_lower:
                    selected_restaurant = r
                    break
        
        # 2. Identify Event
        selected_event = None
        if "events" in context:
            data = context["events"]
            e_list = data.get("events", []) if isinstance(data, dict) else []
            
            for e in e_list:
                if e["title"].lower() in q_lower: # e.g. "Jazz" in "Jazz Night"
                     selected_event = e
                     break
                     
        # If we found at least one selection, we assume this is a commit request
        if selected_restaurant or selected_event:
            idx = 0
            
            # Default Params
            date = "Tomorrow" 
            party_size = 2 # MVP simplification
            
            if selected_restaurant:
                steps.append(PlanStep(
                    step_index=idx, step_type="TOOL", tool_name="reserve_table",
                    tool_args={
                        "restaurant_id": selected_restaurant["id"],
                        "name": "Guest",
                        "date": date,
                        "time": "19:00",
                        "party_size": party_size
                    },
                    risk="WRITE"
                ))
                idx += 1
                
            if selected_event:
                steps.append(PlanStep(
                    step_index=idx, step_type="TOOL", tool_name="buy_event_tickets",
                    tool_args={
                        "event_id": selected_event["id"],
                        "name": "Guest",
                        "date": date,
                        "quantity": party_size
                    },
                    risk="WRITE"
                ))
                idx += 1
                
            # Always book room? Or only if "room" mentioned?
            # Prompt 12.8 says: "3) book_room... WRITE"
            # Let's assume if it's the package, we book the room too.
            # Only if room_availability context existed
            if "room_availability" in context or "room" in q_lower: 
                steps.append(PlanStep(
                    step_index=idx, step_type="TOOL", tool_name="book_room",
                    tool_args={"guest_name": "Guest", "room_type": "standard", "date": date},
                    risk="WRITE"
                ))
                
            return steps
            
        return []
