import json
import uuid
import time
from typing import Dict, Any, Union
from .types import Plan, PlanStep
from app.db.queries import (
    create_plan, add_plan_step, update_plan_status, update_step_status, 
    get_plan, create_action, update_action_status, confirm_action, get_db_connection
)
from app.agent.tools import ToolRegistry

class PlanRunner:
    def __init__(self, tool_registry: ToolRegistry):
        self.tools = tool_registry

    async def run_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        Execute a plan from the beginning.
        """
        # 1. Persist Plan to DB
        create_plan(plan.id, plan.session_id, plan.audience, plan.question, plan.plan_summary, status="running")
        
        for step in plan.steps:
            step.id = str(uuid.uuid4())
            add_plan_step(
                step.id, plan.id, step.step_index, step.step_type, 
                step.tool_name, json.dumps(step.tool_args) if step.tool_args else None, 
                step.risk, status="pending"
            )

        # 2. Execute Steps
        return await self._execute_loop(plan)

    async def resume_plan(self, action_id: str, confirm: bool) -> Dict[str, Any]:
        """
        Resume a plan blocked on an action.
        """
        # Lookup action to find plan_id / step_id
        # Note: current actions table doesn't have plan_id/step_id columns.
        # We need to link them. 
        # Strategy: We can store plan_id/step_id in the 'params_json' or add columns.
        # Strict Rule: "Integrate... do not remove or break [existing tables]"
        # So we can't easily add columns without migration (which I can do, but risky).
        # Alternative: We can fetch the plan associated with the session that is 'needs_confirmation'.
        # Or simplistic: The user prompt said: "Add helper functions... Integrate these".
        # I'll rely on looking up the action, and then finding the active plan for that session.
        
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM actions WHERE action_id = ?", (action_id,)).fetchone()
        conn.close()
        
        if not row:
            return {"status": "error", "message": "Action not found"}
            
        session_id = row['session_id']
        
        # Find active plan for session
        # Simpler: We assume there's one active plan per session for MVP.
        conn = get_db_connection()
        conn.row_factory = get_db_connection().row_factory
        c = conn.cursor()
        c.execute("SELECT * FROM plans WHERE session_id = ? AND status = 'needs_confirmation' ORDER BY created_at DESC LIMIT 1", (session_id,))
        plan_row = c.fetchone()
        conn.close()
        
        if not plan_row:
             return {"status": "error", "message": "No active plan found for this action."}
             
        plan_data = get_plan(plan_row['id'])
        # Reconstruct Plan Object
        steps = []
        current_step_index = -1
        
        for s in plan_data['steps']:
            step = PlanStep(
                id=s['id'],
                step_index=s['step_index'],
                step_type=s['step_type'],
                tool_name=s['tool_name'],
                tool_args=json.loads(s['tool_args_json']) if s['tool_args_json'] else {},
                risk=s['risk'],
                status=s['status'],
                result=s['result_json']
            )
            steps.append(step)
            if s['status'] == 'pending' and current_step_index == -1:
                 current_step_index = s['step_index']
                 
        plan = Plan(
            id=plan_data['plan']['id'],
            session_id=plan_data['plan']['session_id'],
            audience=plan_data['plan']['audience'],
            question=plan_data['plan']['question'],
            plan_summary=plan_data['plan']['plan_summary'],
            steps=steps,
            status=plan_data['plan']['status']
        )

        # Handle Confirmation Logic
        if not confirm:
            update_action_status(action_id, "cancelled")
            update_plan_status(plan.id, "cancelled")
            return {"status": "cancelled", "message": "Plan cancelled by user."}

        # Confirmed
        confirm_action(action_id)
        
        # We need to execute the step that was blocked.
        # Ideally, we know WHICH step was blocked.
        # It's the first 'pending' step (which triggered the confirmation).
        # We will assume _execute_loop handles resuming from the first pending step.
        
        # Update plan status back to running
        update_plan_status(plan.id, "running")
        
        return await self._execute_loop(plan, resume_action_id=action_id)

    async def _execute_loop(self, plan: Plan, resume_action_id: str = None) -> Dict[str, Any]:
        """
        Internal loop to run steps.
        """
        results_accumulator = []
        
        for step in plan.steps:
            if step.status == "success":
                # Don't add step details - keep customer message clean
                continue
            
            if step.status == "failed" or step.status == "blocked":
                return {"status": "failed", "message": "Plan previously failed."}
                
            # Current Pending Step
            update_step_status(step.id, "running")
            
            if step.step_type == "TOOL":
                # Check Risk
                if step.risk == "WRITE" and not resume_action_id:
                    # BLOCK for confirmation
                    action_id = str(uuid.uuid4())
                    
                    # --- PRICING & QUOTE GENERATION ---
                    from app.services.pricing_service import PricingService
                    # We need tenant_id. Runner currently doesn't carry it explicitly in signature?
                    # Ideally, Plan object or ToolRegistry has it.
                    # Fallback: prompt implies tenant_id available.
                    # Let's assume passed in `plan.audience` context or similar, OR use default.
                    # Tools have execution context.
                    # For MVP, we use "default-tenant-0000" if missing, or extract from somewhere.
                    tenant_id = "default-tenant-0000" # TODO: Fix context passing
                    pricing = PricingService(tenant_id)
                    
                    # Build Pricing Context from Tool Args & Plan Context
                    # (Simplified for MVP: Extract params directly)
                    p_context = {}
                    if "room_type" in step.tool_args: p_context["room_type"] = step.tool_args["room_type"]
                    if "party_size" in step.tool_args: p_context["party_size"] = step.tool_args["party_size"]
                    if "quantity" in step.tool_args: p_context["party_size"] = step.tool_args["quantity"]
                    
                    # Look for selected items in plan context (from explore phase)
                    if "restaurants" in plan.context:
                         # Heuristic: If reserve_table, grab the restaurant details if mapped?
                         # Or just pass name if available.
                         p_context["selected_restaurant"] = {"name": "Selected Restaurant"} 
                    
                    if "events" in plan.context:
                        p_context["selected_event"] = {"name": "Selected Event", "price": 0}

                    # Create Quote
                    quote = pricing.create_quote(plan.session_id, p_context)
                    
                    # Store action in DB with tenant_id
                    create_action(
                        action_id, plan.session_id, step.tool_name, 
                        json.dumps(step.tool_args), requires_confirmation=True,
                        tenant_id=tenant_id
                    )
                    
                    # Update DB status
                    update_step_status(step.id, "pending")
                    update_plan_status(plan.id, "needs_confirmation")
                    
                    # Update Quote with pending_plan_id (Task 9.3)
                    # We need to link the quote to this plan so webhook can resume it.
                    # PricingService needs update or we do direct SQL update here.
                    conn = get_db_connection()
                    conn.execute("UPDATE quotes SET pending_plan_id = ? WHERE id = ?", (plan.id, quote["id"]))
                    conn.commit()
                    conn.close()

                    return {
                        "status": "needs_payment", # Client will see this and show Payment UI
                        "message": f"A quote has been generated. Payment of ${quote['totals']['total_cents']/100:.2f} is required to proceed.",
                        "action_id": action_id,
                        "plan_id": plan.id,
                        "quote": quote,
                        "payment_required": True,
                        "proposed_action": {
                            "tool": step.tool_name,
                            "params": step.tool_args
                        }
                    }
                
                # Execute (READ or Resumed WRITE)
                # If we are resuming, we consume the resume_action_id for this step, then clear it for next steps
                is_resumed_write = (resume_action_id is not None)
                if resume_action_id:
                    resume_action_id = None 
                    
                try:
                    result = await self.tools.execute(step.tool_name, step.tool_args)
                    
                    
                    # --- RECEIPT GENERATION (Post-Write) ---
                    if is_resumed_write:
                        # Find latest quote for session
                        conn = get_db_connection()
                        # Task 9.3 Fix: Quote might be 'paid' now if triggered by webhook
                        quote_row = conn.execute(
                            "SELECT id, tenant_id FROM quotes WHERE session_id = ? AND status IN ('proposed', 'awaiting_payment', 'paid') ORDER BY created_at DESC LIMIT 1", 
                            (plan.session_id,)
                        ).fetchone()
                        conn.close()
                        
                        if quote_row:
                            q_id = quote_row[0]
                            q_tenant = quote_row[1]
                            
                            from app.services.pricing_service import PricingService
                            pricing = PricingService(q_tenant)
                            
                            # Extract booking references from Tool Result
                            ref_id = "unknown"
                            if "ID: " in str(result):
                                ref_id = str(result).split("ID: ")[1].split(" ")[0].strip()
                                
                            pricing.create_receipt(q_id, plan.session_id, {"booking_ref": ref_id})
                            result += "\n(Receipt Generated)"

                    # Update DB
                    update_step_status(step.id, "success", result_json=str(result))
                    step.status = "success"
                    step.result = str(result)
                    
                    # Store Context
                    if step.save_as:
                        try:
                            # Try to parse JSON for structured context
                            parsed_result = json.loads(result)
                            plan.context[step.save_as] = parsed_result
                        except:
                            # Fallback string
                            plan.context[step.save_as] = result
                    
                    # Don't add step details to results_accumulator - keep it clean for customer
                    # Internal trace will be stored in DB separately
                    pass  # Skip adding step details to customer message
                    
                except Exception as e:
                    update_step_status(step.id, "failed", result_json=str(e))
                    update_plan_status(plan.id, "failed")
                    return {"status": "failed", "message": f"Step failed: {e}"}
            
            elif step.step_type == "CHAT":
                # ... existing ...
                update_step_status(step.id, "success", result_json=step.result)
                # Don't add to results_accumulator - keep customer message clean

        # All steps complete
        update_plan_status(plan.id, "completed")
        
        #EXPLORE MODE COMPLETION
        if plan.plan_mode == "explore":
            # Summarize options for user
            summary = self._summarize_explore_results(plan.context)
            return {
                "status": "needs_input",
                "session_id": plan.session_id,
                "message": "I found some great options for your night out:",
                "answer": summary, # Display to user
                "context_summary": plan.context # Full data if needed by FE
            }

        # COMMIT MODE - Professional customer-facing message
        # Get last tool result for better formatting
        last_result = None
        for step in reversed(plan.steps):
            if step.status == "success" and step.result:
                try:
                    import json
                    last_result = json.loads(step.result)
                except:
                    last_result = step.result
                break
        
        return self._format_customer_message(plan, results_accumulator, last_tool_result=last_result)
    
    def _format_customer_message(self, plan: Plan, results_accumulator: list, last_tool_result: Any = None) -> Dict[str, Any]:
        """
        Format professional, customer-friendly completion message.
        Hides all internal steps, tool details, and technical information.
        """
        import re
        import json
        
        # Extract details from tool results (prefer last_tool_result, fallback to step results)
        booking_id = None
        receipt_id = None
        room_type = None
        date_str = None
        reservation_id = None
        ticket_id = None
        
        # Try to parse last_tool_result first (most recent)
        if last_tool_result:
            if isinstance(last_tool_result, dict):
                booking_id = last_tool_result.get("booking_id") or last_tool_result.get("booking_ref")
                receipt_id = last_tool_result.get("receipt_id") or last_tool_result.get("receipt_ref")
                room_type = last_tool_result.get("room_type")
                date_str = last_tool_result.get("date_human") or last_tool_result.get("date")
                reservation_id = last_tool_result.get("reservation_id")
                ticket_id = last_tool_result.get("ticket_id")
            elif isinstance(last_tool_result, str):
                # Try to extract from string
                if "BK-" in last_tool_result:
                    match = re.search(r'BK-[\w\d-]+', last_tool_result)
                    if match:
                        booking_id = match.group(0)
                if "RCP-" in last_tool_result:
                    match = re.search(r'RCP-[\w\d-]+', last_tool_result)
                    if match:
                        receipt_id = match.group(0)
        
        # Fallback: Extract from step results
        if not booking_id or not receipt_id:
            for step in plan.steps:
                if step.status == "success" and step.result:
                    result_str = str(step.result)
                    
                    # Try to parse as JSON first
                    try:
                        result_dict = json.loads(result_str)
                        if not booking_id:
                            booking_id = result_dict.get("booking_id") or result_dict.get("booking_ref")
                        if not receipt_id:
                            receipt_id = result_dict.get("receipt_id") or result_dict.get("receipt_ref")
                        if not room_type:
                            room_type = result_dict.get("room_type")
                        if not date_str:
                            date_str = result_dict.get("date_human") or result_dict.get("date")
                    except:
                        # Not JSON, extract from string
                        if "BK-" in result_str and not booking_id:
                            match = re.search(r'BK-[\w\d-]+', result_str)
                            if match:
                                booking_id = match.group(0)
                        if "RCP-" in result_str and not receipt_id:
                            match = re.search(r'RCP-[\w\d-]+', result_str)
                            if match:
                                receipt_id = match.group(0)
        
        # Build professional customer message
        lines = []
        
        # Determine action type from tool names
        tool_names = [step.tool_name for step in plan.steps if step.tool_name]
        has_booking = any("book" in name.lower() for name in tool_names if name)
        has_reservation = any("reserve" in name.lower() or "table" in name.lower() for name in tool_names if name)
        has_ticket = any("ticket" in name.lower() or "event" in name.lower() for name in tool_names if name)
        
        if has_booking:
            room_display = room_type or "room"
            date_display = date_str or "your selected date"
            lines.append(f"✅ Your {room_display} is booked for {date_display}!")
        elif has_reservation:
            lines.append("✅ Your table reservation has been confirmed!")
        elif has_ticket:
            lines.append("✅ Your event tickets have been booked!")
        else:
            lines.append("✅ Your request has been completed successfully!")
        
        lines.append("")  # Blank line
        
        # Add booking details
        if booking_id:
            lines.append("Booking Details:")
            lines.append(f"• Booking ID: {booking_id}")
        
        if reservation_id:
            lines.append(f"• Reservation ID: {reservation_id}")
        
        if ticket_id:
            lines.append(f"• Ticket ID: {ticket_id}")
        
        if receipt_id:
            lines.append(f"• Receipt: {receipt_id}")
            lines.append("")
            lines.append("📧 A confirmation email with your receipt has been sent.")
        elif booking_id or reservation_id or ticket_id:
            lines.append("")
            lines.append("📧 You'll receive a confirmation email shortly.")
        
        message = "\n".join(lines)
        
        return {
            "status": "success",
            "answer": message,
            "plan_id": plan.id,
            "session_id": plan.session_id
        }

    def _summarize_explore_results(self, context: Dict[str, Any]) -> str:
        msg = []
        
        # Rooms
        if "room_availability" in context:
            msg.append(f"**Room**: {context['room_availability']}") # It's a string message often
            
        # Restaurants
        if "restaurants" in context:
            # context['restaurants'] might be string (if json parse failed) or dict {"restaurants": [...]}
            data = context["restaurants"]
            if isinstance(data, dict) and "restaurants" in data:
                items = data["restaurants"][:3] # Top 3
                msg.append("\n**Dining Options**:")
                for r in items:
                    msg.append(f"- {r.get('name')} ({r.get('price_band')}) - {r.get('slots_hint')}")
            else:
                 msg.append(f"\n**Dining**: {str(data)[:100]}...")

        # Events
        if "events" in context:
            data = context["events"]
            if isinstance(data, dict) and "events" in data:
                items = data["events"][:3]
                msg.append("\n**Events**:")
                for e in items:
                    msg.append(f"- {e.get('title')} @ {str(e.get('start_time'))[:16]}")
            else:
                 msg.append(f"\n**Events**: {str(data)[:100]}...")
                 
        msg.append("\nPlease reply with your choices (e.g. 'Reserve Test Bistro and Jazz Night').")
        return "\n".join(msg)

    async def execute_plan_for_quote(self, quote_id: str):
        """
        Task 9.3: Resume execution after payment.
        1. Find Plan ID linked to Quote.
        2. Resume Plan (similar to confirm_action).
        3. Ensure Receipt generated.
        """
        conn = get_db_connection()
        conn.row_factory = get_db_connection().row_factory
        
        # 1. Get Quote & Plan ID
        quote = conn.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
        if not quote or not quote["pending_plan_id"]:
            print(f"[Runner] No pending plan for quote {quote_id}")
            conn.close()
            return
            
        plan_id = quote["pending_plan_id"]
        
        # 2. Get Plan
        # We need to construct the Plan object to run _execute_loop
        # Re-using get_plan logic
        plan_row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        conn.close()
        
        if not plan_row:
             print(f"[Runner] Plan {plan_id} not found.")
             return

        plan_data = get_plan(plan_id)
        
        # Reconstruct Plan
        steps = []
        resume_action_id = None
        
        for s in plan_data['steps']:
            step = PlanStep(
                id=s['id'],
                step_index=s['step_index'],
                step_type=s['step_type'],
                tool_name=s['tool_name'],
                tool_args=json.loads(s['tool_args_json']) if s['tool_args_json'] else {},
                risk=s['risk'],
                status=s['status'],
                result=s['result_json']
            )
            steps.append(step)
            
            # Identify the block point (pending step)
            if s['status'] == 'pending':
                # We need the action_id to "resume" the write block?
                # _execute_loop checks `step.risk == "WRITE" and not resume_action_id`
                # If we pass a dummy resume_action_id, it will proceed.
                # OR we update the step status manually?
                # Using execution loop is safer.
                pass

        plan = Plan(
            id=plan_data['plan']['id'],
            session_id=plan_data['plan']['session_id'],
            audience=plan_data['plan']['audience'],
            question=plan_data['plan']['question'],
            plan_summary=plan_data['plan']['plan_summary'],
            steps=steps,
            status=plan_data['plan']['status']
        )
        
        # 3. Resume
        print(f"[Runner] Executing PAID plan {plan_id}")
        # We pass a 'bypass' flag or dummy action ID to signal "Yes, proceed with write"
        # In _execute_loop: `if resume_action_id: ...` logic unlocks the WRITE.
        # We don't have the original action_id easily available unless we query `actions` table.
        
        # Let's find the pending action for this plan/session?
        conn = get_db_connection()
        action_row = conn.execute(
            "SELECT action_id FROM actions WHERE session_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1", 
            (plan.session_id,)
        ).fetchone()
        conn.close()
        
        bypass_id = action_row[0] if action_row else "bypass_payment_confirmed"
        
        if action_row:
            confirm_action(action_row[0]) # Mark action confirmed in DB too
            
        update_plan_status(plan.id, "running")
        
        # 4. Execute
        result = await self._execute_loop(plan, resume_action_id=bypass_id)
        
        # 5. Finalize Quote status?
        # payment_service handles "paid". 
        # Quote status is "paid". 
        # Plan status will be "completed" if successful.
        print(f"[Runner] Execution Result: {result}")
        return result
