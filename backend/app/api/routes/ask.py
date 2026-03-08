from fastapi import APIRouter, HTTPException, Depends
import time
import traceback
from app.schemas.requests import QuestionRequest
from app.schemas.responses import AnswerResponse
from app.ai_service import get_guest_answer, get_staff_answer
from app.db.queries import log_chat
from app.api.deps import get_tenant_header

router = APIRouter()

@router.post("/ask/guest", response_model=AnswerResponse)
async def ask_guest(
    payload: QuestionRequest,
    tenant_id: str = Depends(get_tenant_header)
):
  start_time = time.time()
  try:
    answer = await get_guest_answer(payload.question, tenant_id=tenant_id)
    
    # Log to DB with internal trace (if available)
    latency = int((time.time() - start_time) * 1000)
    internal_trace = None
    if isinstance(answer, dict) and "_internal_trace" in answer:
        internal_trace = answer.pop("_internal_trace")  # Remove from response, keep in DB
        answer_text = answer.get("answer", str(answer))
    else:
        answer_text = answer if isinstance(answer, str) else str(answer)
    
    log_chat("guest", payload.question, answer_text, latency_ms=latency, tenant_id=tenant_id, session_id=None, internal_trace_json=internal_trace)
    
    return AnswerResponse(
      role="guest",
      question=payload.question,
      answer=answer,
    )
  except Exception as e:
    print(f"[ERROR] Guest query failed: {e}")
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/ask/staff", response_model=AnswerResponse)
async def ask_staff(
    payload: QuestionRequest,
    tenant_id: str = Depends(get_tenant_header)
):
  start_time = time.time()
  try:
    answer = await get_staff_answer(payload.question, tenant_id=tenant_id)
    
    # Log to DB with tenant_id
    latency = int((time.time() - start_time) * 1000)
    answer_text = answer if isinstance(answer, str) else str(answer)
    log_chat("staff", payload.question, answer_text, latency_ms=latency, tenant_id=tenant_id, session_id=None)
    
    return AnswerResponse(
      role="staff",
      question=payload.question,
      answer=answer,
    )
  except Exception as e:
    print(f"[ERROR] Staff query failed: {e}")
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
