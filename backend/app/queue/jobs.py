
import logging
import json
import traceback
from datetime import datetime
from app.db.session import get_db_connection
from app.db.queries import get_plan, update_plan_status
from app.agent.planner.runner import PlanRunner
from app.agent.tools import ToolRegistry
from app.mcp_client import MCPClient  # Or local mock

logger = logging.getLogger("worker")

async def execute_quote_job(tenant_id: str, quote_id: str, payment_id: str, stripe_event_id: str, job_id: str):
    """
    Background job to execute a plan for a paid quote.
    Idempotent and safe.
    """
    logger.info(f"[Job {job_id}] Starting execution for Quote {quote_id} (Event: {stripe_event_id})")
    
    # 1. State Check & Locking (Optimistic Update)
    conn = get_db_connection()
    conn.row_factory = get_db_connection().row_factory # Ensure dict access
    
    # Update job to running
    conn.execute("UPDATE execution_jobs SET status = 'running', attempts = attempts + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
    conn.commit()
    
    try:
        # Check Quote Status
        quote = conn.execute("SELECT * FROM quotes WHERE id = ? AND tenant_id = ?", (quote_id, tenant_id)).fetchone()
        if not quote:
             raise ValueError(f"Quote {quote_id} not found")
             
        # Idempotency check: If already executed, mark success and exit
        if quote["status"] == "completed" or (quote.get("executed_at") is not None):
             logger.info(f"[Job {job_id}] Quote {quote_id} already executed. Marking job success.")
             conn.execute("UPDATE execution_jobs SET status = 'success', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
             conn.commit()
             conn.close()
             return

        # 2. Setup Runner
        # Use appropriate ToolRegistry. 
        # In worker context, we probably need a fresh registry.
        mcp = MCPClient() 
        registry = ToolRegistry(mcp)
        runner = PlanRunner(registry)
        
        # 3. Execute
        # Reuse existing logic `execute_plan_for_quote` but wrap it?
        # `execute_plan_for_quote` assumes DB connection capability.
        # It updates `plan` status.
        result = await runner.execute_plan_for_quote(quote_id)
        
        if result and result.get("status") == "success":
             # 4. Success Handling
             conn = get_db_connection() # Reconnect if needed or reuse
             conn.execute("UPDATE execution_jobs SET status = 'success', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
             conn.execute("UPDATE quotes SET status = 'completed', executed_at = CURRENT_TIMESTAMP WHERE id = ?", (quote_id,))
             conn.commit()
             logger.info(f"[Job {job_id}] Execution Successful.")
        else:
             # Logic failure (not exception)
             msg = result.get("message") if result else "Unknown failure"
             raise RuntimeError(f"Plan Execution Failed: {msg}")

    except Exception as e:
        logger.error(f"[Job {job_id}] Execution Job Failed: {e}")
        traceback.print_exc()
        
        # 5. Failure Handling
        conn = get_db_connection()
        conn.execute("UPDATE execution_jobs SET status = 'failed', last_error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (str(e), job_id))
        
        # Mark quote as failed? Or keep as 'paid' to allow retry?
        # If retryable, we keep 'paid'. Quote status 'failed' implies permanent failure?
        # For now, we note error in quote but maybe not change overall status if we want to retry manually.
        conn.execute("UPDATE quotes SET execution_error = ? WHERE id = ?", (str(e), quote_id))
        conn.commit()
        
        # Re-raise so RQ handles retry backoff
        raise e
    finally:
        try:
             conn.close()
        except: pass
