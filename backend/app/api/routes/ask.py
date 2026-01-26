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
    
    # Log to DB
    latency = int((time.time() - start_time) * 1000)
    log_chat("guest", payload.question, answer, latency_ms=latency, tenant_id=tenant_id)
    
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
async def ask_staff(payload: QuestionRequest):
  start_time = time.time()
  try:
    answer = await get_staff_answer(payload.question)
    
    # Log to DB
    latency = int((time.time() - start_time) * 1000)
    log_chat("staff", payload.question, answer, latency_ms=latency)
    
    return AnswerResponse(
      role="staff",
      question=payload.question,
      answer=answer,
    )
  except Exception as e:
    print(f"[ERROR] Staff query failed: {e}")
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
