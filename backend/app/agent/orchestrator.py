# Main Agent Orchestrator
import time
import uuid
import json
from .router import AgentRouter
from app.agent.tools import ToolRegistry
from app.db.queries import log_tool_call, create_action, confirm_action, update_action_status
from app.db.session import get_db_connection

class AgentOrchestrator:
    def __init__(self, hotel_ai):
        self.hotel_ai = hotel_ai
        self.router = AgentRouter()
        self.tools = ToolRegistry(hotel_ai.mcp_client)
        
        # Planner Integrations
        from app.agent.planner.planner import HybridPlanner
        from app.agent.planner.validator import PlanValidator
        from app.agent.planner.runner import PlanRunner
        
        self.planner = HybridPlanner(self.tools)
        self.validator = PlanValidator(self.tools)
        self.runner = PlanRunner(self.tools)

    async def process_request(self, audience: str, question: str, session_id: str = None, confirm: bool = False, tenant_id: str = None):
        """
        Main Agent Loop:
        1. Context Retrieval (RAG)
        2. Planner (New) -> If plan found, execute workflow.
        3. Fallback: Intent Routing (Chat vs Tool)
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            if not tenant_id:
                tenant_id = "default-tenant-0000"
            
            # 1. Retrieve Context
            try:
                context_chunks = self.hotel_ai.query_docs(audience, question, tenant_id=tenant_id)
            except Exception as e:
                print(f"[Agent] Warning: Context retrieval failed (Quota or other): {e}", flush=True)
                context_chunks = []
            
            # 1.5 Retrieve Session Context (Last Explore Plan) for "Experience Package" flow
            # We need to know if we are in "Selection Phase"
            try:
                print("[DEBUG] Step 1.5 Started (Session Context)", flush=True)
                from app.db.session import get_db_connection
                from app.db.queries import get_plan # Lazy import
                # Note: get_plan isn't directly exposed for recent session. Custom query needed.
                prev_context = {}
                conn = get_db_connection()
                try:
                    # Find last completed explore plan
                    cur = conn.execute(
                        "SELECT id FROM plans WHERE session_id = ? AND status = 'completed' ORDER BY created_at DESC LIMIT 1", 
                        (session_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        last_plan = get_plan(row[0]) # Returns dict with 'plan' and 'steps' keys
                        if last_plan:
                            # Heuristic: If context summary has "restaurants", it was explore.
                            steps_data = last_plan.get('steps', [])
                        
                            # Hack: We will look for Tool 'list_restaurants' in steps to confirm explore.
                            # And we need to rebuild the context from the results.
                            # This is "Rehydration".
                            for s in steps_data:
                                res_json = s.get('result_json')
                                tool = s.get('tool_name')
                                if tool == 'list_restaurants':
                                     prev_context['restaurants'] = json.loads(res_json) if res_json else {}
                                elif tool == 'list_events':
                                     prev_context['events'] = json.loads(res_json) if res_json else {}
                                elif tool == 'check_room_availability':
                                     prev_context['room_availability'] = res_json or ""
                            
                            print(f"[DEBUG] Orchestrator: Retrieved Context keys: {list(prev_context.keys())}", flush=True)

                finally:
                     conn.close()
            except Exception as e:
                print(f"[Agent] Context retrieval warning: {e}")
                prev_context = {}

            # 2. Try Planning First
            try:
                # Pass prev_context to planner
                plan = await self.planner.plan(audience, question, session_id, context=prev_context)
                if plan:
                    print(f"[Agent] Plan created with {len(plan.steps)} steps. Mode: {plan.plan_mode}")
                    try:
                        self.validator.validate_plan(plan)
                    except Exception as e:
                        print(f"[Agent] Plan validation failed: {e}")
                        # Continue anyway - validation is advisory
                    
                    result = await self.runner.run_plan(plan)
                    
                    # Ensure result is a dict or string
                    if result is None:
                        result = {"answer": "I processed your request but didn't get a response. Please try again.", "status": "error"}
                    
                    # Store internal trace if result has plan_id
                    if isinstance(result, dict) and result.get("plan_id"):
                        try:
                            from app.db.queries import get_plan
                            plan_data = get_plan(result["plan_id"])
                            if plan_data:
                                internal_trace = {
                                    "plan_id": result["plan_id"],
                                    "session_id": session_id,
                                    "audience": audience,
                                    "question": question,
                                    "plan_summary": getattr(plan, 'plan_summary', ''),
                                    "plan_mode": getattr(plan, 'plan_mode', ''),
                                    "steps": [
                                        {
                                            "step_index": s.get("step_index"),
                                            "tool_name": s.get("tool_name"),
                                            "tool_args": json.loads(s.get("tool_args_json")) if s.get("tool_args_json") else {},
                                            "status": s.get("status"),
                                            "result": s.get("result_json")
                                        }
                                        for s in plan_data.get("steps", [])
                                    ]
                                }
                                result["_internal_trace"] = json.dumps(internal_trace)
                        except Exception as trace_error:
                            print(f"[Agent] Failed to create internal trace: {trace_error}")
                            # Don't fail the whole request if trace fails
                    
                    return result
            except Exception as e:
                print(f"[Agent] Planning failed (falling back to router): {e}")
                import traceback
                traceback.print_exc()

            # 3. Fallback: Legacy Router Logic
            mode = self.router.decide_mode(question, context_chunks)
            print(f"[Agent] Mode: {mode} | Question: {question}")
            
            if mode == "CHAT":
                try:
                    return await self.hotel_ai.generate_answer_async(audience, question, context_chunks)
                except Exception as e:
                    print(f"[Agent] Chat generation failed: {e}")
                    return {"answer": "I'm having trouble processing your question right now. Please try again.", "status": "error"}
            
            elif mode == "TOOL":
                # Identify Tool (Naive extraction for MVP - Real agent uses LLM for slot filling)
                # For now, we hackily map keywords to tools
                tool_name = None
                params = {}
                
                q_lower = question.lower()
                if "book" in q_lower or "reserve" in q_lower:
                    tool_name = "book_room"
                    # Mock extraction
                    params = {"guest_name": "Guest", "room_type": "Standard", "date": "Tomorrow"} 
                elif "availab" in q_lower or "check" in q_lower:
                    tool_name = "check_room_availability"
                    params = {"room_type": "Standard", "date": "Tomorrow"}
                    
                if not tool_name:
                    # Fallback if router said TOOL but we can't find one
                    return await self.hotel_ai.generate_answer_async(audience, question, context_chunks)

                # Check Risk
                tool_def = self.tools.get_tool(tool_name)
                if not tool_def:
                    return {"answer": f"Tool '{tool_name}' not found. Please try rephrasing.", "status": "error"}
                
                risk = tool_def["risk"]
                
                # handle WRITE confirmation
                if risk == "WRITE":
                    if not confirm:
                        # Create Pending Action in DB
                        action_id = str(uuid.uuid4())
                        params_str = json.dumps(params)
                        create_action(action_id, session_id, tool_name, params_str, requires_confirmation=True, tenant_id=tenant_id)
                        
                        # Create user-friendly confirmation message
                        if tool_name == "book_room":
                            guest_name = params.get("guest_name", "you")
                            room_type = params.get("room_type", "Standard")
                            date = params.get("date", "Tomorrow")
                            confirmation_msg = f"I can book a {room_type} room for {guest_name} on {date}. Would you like me to proceed with this booking?"
                        else:
                            confirmation_msg = f"I can {tool_def['description']}. Do you want to proceed?"
                        
                        return {
                            "status": "needs_confirmation",
                            "message": confirmation_msg,
                            "answer": confirmation_msg,  # Also include as answer for frontend compatibility
                            "proposed_action": {
                                "tool": tool_name,
                                "params": params,
                                "risk": risk
                            },
                            "action_id": action_id
                        }
                    else:
                        # User Confirmed!
                        # Logic: We might need to look up the 'pending' action for this session if confirm=True
                        # For MVP simplistic flow, we assume the frontend sends the params again or we trust the intent.
                        # Best practice: Look up the action_id.
                        pass 

                # Execute Request (READ or CONFIRMED WRITE)
                start_t = time.time()
                result = await self.tools.execute(tool_name, params, tenant_id=tenant_id)
                latency = int((time.time() - start_t) * 1000)
                
                # Log Tool Call
                log_tool_call(
                    session_id=session_id,
                    audience=audience,
                    tool_name=tool_name,
                    params_str=json.dumps(params),
                    result_str=str(result),
                    risk_level=risk,
                    status="success",
                    latency_ms=latency
                )
                
                # Summarize result with LLM
                # We treat the tool result as a "Context Chunk"
                try:
                    summary_prompt = f"Agent executed tool '{tool_name}'. Result: {result}. Please summarize this for the user."
                    response = await self.hotel_ai.generate_answer_async(audience, summary_prompt, [])
                    return response
                except Exception as e:
                    print(f"[Agent] Summary generation failed: {e}")
                    # Return the raw result if summary fails
                    return {"answer": str(result), "status": "success"}

            return {"answer": "I'm not sure how to handle that request. Could you please rephrase?", "status": "error"}
        
        except Exception as outer_error:
            # Catch-all for any unhandled exceptions
            import traceback
            error_trace = traceback.format_exc()
            print(f"[Agent] CRITICAL ERROR in process_request: {outer_error}")
            print(f"[Agent] Traceback:\n{error_trace}")
            return {
                "answer": "I encountered an error processing your request. Please try again or rephrase your question.",
                "status": "error",
                "error": str(outer_error)
            }

    async def execute_confirmed_action(self, action_id: str, confirm: bool):
        """
        Execute an action that was previously pending confirmation.
        Supports both Plan Workflows and Legacy Single Actions.
        """
        # 1. Try Resuming a Plan first
        try:
            plan_result = await self.runner.resume_plan(action_id, confirm)
            if plan_result.get("status") != "error":
                return plan_result
        except Exception as e:
            print(f"[Agent] Plan resume failed: {e}")

        # 2. Fallback to Legacy Single Action Logic (if no plan found)
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
        conn.close()
        
        if not row:
            return "Action not found or expired."
        
        if row['status'] != 'pending':
            return f"Action is already {row['status']}."
        
        if not confirm:
            update_action_status(action_id, "cancelled")
            return "Action cancelled."
            
        # Proceed with execution
        confirm_action(action_id)
        
        tool_name = row['tool_name']
        params = json.loads(row['params_json'])
        audience = "guest" # Defaulting to guest for now as 'actions' table doesn't store audience yet. 
                           # Improvement: Add audience to actions table or retrieve from session.
                           # For now, safe assumption or pass it in.
        
        start_t = time.time()
        tenant_id = row['tenant_id'] # Use the tenant context from when action was created
        result = await self.tools.execute(tool_name, params, tenant_id=tenant_id)
        latency = int((time.time() - start_t) * 1000)
        
        # Log completion
        update_action_status(action_id, "completed")
        log_tool_call(
            session_id=row['session_id'],
            audience=audience,
            tool_name=tool_name,
            params_str=row['params_json'],
            result_str=str(result),
            risk_level="WRITE",
            status="success",
            latency_ms=latency
        )
        
        # Summarize
        summary_prompt = f"Agent executed confirmed action '{tool_name}'. Result: {result}. Please summarize this for the user."
        # We need a fallback context here.
        response = await self.hotel_ai.generate_answer_async(audience, summary_prompt, [])
        return response
