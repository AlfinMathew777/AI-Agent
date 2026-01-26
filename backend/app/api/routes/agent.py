from fastapi import APIRouter, HTTPException, Depends
import time
import traceback
from app.schemas.requests import AgentRequest, AgentConfirmRequest
from app.ai_service import get_agent_answer, confirm_agent_action
from app.api.deps import get_current_tenant

router = APIRouter()

@router.post("/ask/agent")
async def ask_agent(
    payload: AgentRequest, 
    tenant_id: str = Depends(get_current_tenant)
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
        
        # If response is a dict (Confirmation Request), return it directly
        if isinstance(response, dict):
            return response
            
        # If string (Chat Answer), wrap it
        return {"answer": response, "status": "success"}

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
