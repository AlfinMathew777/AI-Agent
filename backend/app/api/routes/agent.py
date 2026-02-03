from fastapi import APIRouter, HTTPException, Depends
import time
import traceback
from app.schemas.requests import AgentRequest, AgentConfirmRequest
from app.ai_service import get_agent_answer, confirm_agent_action
from app.api.deps import get_current_tenant, get_tenant_header
from app.db.queries import log_chat

router = APIRouter()

@router.post("/ask/agent")
async def ask_agent(
    payload: AgentRequest, 
    tenant_id: str = Depends(get_tenant_header)  # Use header-based tenant (no auth required)
):
    """
    Unified Agent Endpoint. 
    Handles both chat and tool execution.
    """
    start_time = time.time()
    try:
        response = await get_agent_answer(
            audience=payload.audience, 
            question=payload.question,
            session_id=payload.session_id,
            confirm=payload.confirm,
            tenant_id=tenant_id
        )
        
        # Extract internal trace if present
        internal_trace = None
        answer_text = None
        session_id_for_log = payload.session_id
        
        if isinstance(response, dict):
            # Check if it has internal trace
            if "_internal_trace" in response:
                internal_trace = response.pop("_internal_trace")
            
            # Extract answer from response
            if "answer" in response:
                answer_text = response["answer"]
            elif "message" in response:
                answer_text = response["message"]
            else:
                answer_text = str(response)
            
            # Log to DB with trace (only for successful completions, not confirmation requests)
            if answer_text and response.get("status") in ["success", "completed"]:
                latency = int((time.time() - start_time) * 1000)
                log_chat(
                    payload.audience, 
                    payload.question, 
                    answer_text, 
                    latency_ms=latency, 
                    tenant_id=tenant_id,
                    session_id=session_id_for_log,
                    internal_trace_json=internal_trace
                )
            
            return response
        else:
            # String response
            answer_text = str(response)
            latency = int((time.time() - start_time) * 1000)
            log_chat(
                payload.audience, 
                payload.question, 
                answer_text, 
                latency_ms=latency, 
                tenant_id=tenant_id,
                session_id=session_id_for_log,
                internal_trace_json=None
            )
            return {"answer": answer_text, "status": "success"}

    except Exception as e:
        print(f"[ERROR] Agent query failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

@router.post("/ask/agent/confirm")
async def confirm_agent(payload: AgentConfirmRequest):
    """
    Confirm or Cancel a pending agent action.
    """
    try:
        response = await confirm_agent_action(payload.action_id, payload.confirm)
        
        # If string output, wrap it
        if isinstance(response, str):
            status = "success" if payload.confirm else "cancelled"
            return {"answer": response, "status": status}
            
        return response
        
    except Exception as e:
        print(f"[ERROR] Agent confirmation failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent Confirm Error: {str(e)}")
