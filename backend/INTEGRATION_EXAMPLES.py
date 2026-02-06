"""
Example: Drop-In Integration
Shows how to integrate the enhanced chatbot into existing ai_service.py
"""

# ============================================================================
# OPTION 1: Complete Replacement (Recommended for testing)
# ============================================================================
# Replace the entire get_guest_answer() function in app/ai_service.py

from app.chatbot.integration_wrapper import enhanced_guest_answer_full

async def get_guest_answer(question: str, tenant_id: str = None) -> str:
    """
    Enhanced guest answer with full ACP integration
    
    This replaces the existing RAG-based system with the enhanced chatbot
    that has real booking capabilities, property context, and date parsing.
    """
    try:
        # Use enhanced chatbot
        response = await enhanced_guest_answer_full(
            question=question,
            tenant_id=tenant_id,
            session_id=None  # Extract from request if available
        )
        
        # Return just the answer text for compatibility
        answer = response.get("answer", "I'm sorry, I couldn't process that.")
        
        # Optionally log the full response for debugging
        if response.get("intent"):
            print(f"[Enhanced Chatbot] Intent: {response['intent']}")
        
        return answer
    except Exception as e:
        print(f"[Enhanced Chatbot] Error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to friendly error message
        return "I'm having trouble processing your request right now. Please try rephrasing or contact our front desk for assistance."


# ============================================================================
# OPTION 2: Hybrid Approach (Use both systems)
# ============================================================================
# Keep existing RAG for general questions, use enhanced chatbot for bookings

from app.chatbot.integration_wrapper import get_enhanced_chatbot
from app.llm import HotelAI  # Existing RAG system

# Keep the original function as a backup
hotel_ai = HotelAI()

async def get_guest_answer_hybrid(question: str, tenant_id: str = None) -> str:
    """
    Hybrid approach: Use enhanced chatbot for booking-related queries,
    fall back to RAG for general questions.
    """
    question_lower = question.lower()
    
    # Keywords that indicate booking/property-specific intents
    booking_keywords = [
        'book', 'reserve', 'reservation', 'available', 'availability',
        'rates', 'price', 'cost', 'discount', 'check-in', 'check-out',
        'spa', 'amenities', 'policy', 'room', 'rooms', 'properties',
        'hotel', 'stay', 'night', 'week', 'month'
    ]
    
    # Check if query is booking-related
    is_booking_query = any(keyword in question_lower for keyword in booking_keywords)
    
    if is_booking_query:
        print(f"[Hybrid] Using enhanced chatbot for: {question}")
        try:
            chatbot = get_enhanced_chatbot()
            response = await chatbot.process_message(
                message=question,
                tenant_id=tenant_id
            )
            return response.get("answer")
        except Exception as e:
            print(f"[Hybrid] Enhanced chatbot failed, falling back to RAG: {e}")
            # Fall through to RAG
    
    # Use existing RAG system for general questions
    print(f"[Hybrid] Using RAG for: {question}")
    try:
        docs = hotel_ai.query_docs("guest", question, n_results=5, tenant_id=tenant_id)
        response = await hotel_ai.generate_answer_async("guest", question, docs)
        return response
    except Exception as e:
        print(f"[Hybrid] RAG failed: {e}")
        return "I'm having trouble answering that right now. Please try rephrasing or contact our front desk."


# ============================================================================
# OPTION 3: Add as New Endpoint (Safest for production)
# ============================================================================
# Add to app/api/routes/ask.py

from fastapi import APIRouter, HTTPException, Depends, Header
from app.chatbot.integration_wrapper import enhanced_guest_answer_full
from app.schemas.requests import QuestionRequest
from app.schemas.responses import AnswerResponse
from app.api.deps import get_tenant_header
import time

router = APIRouter()

@router.post("/ask/guest/enhanced", response_model=AnswerResponse)
async def ask_guest_enhanced(
    payload: QuestionRequest,
    tenant_id: str = Depends(get_tenant_header),
    session_id: str = Header(None, alias="x-session-id")
):
    """
    Enhanced guest endpoint with full ACP integration
    
    Headers:
      X-Tenant-ID: Property identifier (required)
      X-Session-ID: Session identifier for conversation continuity (optional)
    """
    start_time = time.time()
    try:
        # Process with enhanced chatbot
        response = await enhanced_guest_answer_full(
            question=payload.question,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        answer = response.get("answer", "I'm sorry, I couldn't process that.")
        latency = int((time.time() - start_time) * 1000)
        
        # Log to database
        from app.db.queries import log_chat
        log_chat(
            "guest",
            payload.question,
            answer,
            latency_ms=latency,
            tenant_id=tenant_id,
            session_id=response.get("session_id")
        )
        
        return AnswerResponse(
            role="guest",
            question=payload.question,
            answer=answer,
        )
    except Exception as e:
        print(f"[ERROR] Enhanced guest query failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION MANAGEMENT FOR FRONTEND
# ============================================================================
# Frontend should maintain session_id for conversation continuity

"""
JavaScript Example (Frontend):

let sessionId = null;

async function sendMessage(question) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Tenant-ID': 'hotel_tas_luxury'  // Set based on subdomain or config
  };
  
  // Add session ID if we have one
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }
  
  const response = await fetch('/ask/guest/enhanced', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ question: question })
  });
  
  const data = await response.json();
  
  // Store session ID from first response
  if (!sessionId && response.headers.get('X-Session-ID')) {
    sessionId = response.headers.get('X-Session-ID');
  }
  
  return data.answer;
}

// Clear session on page refresh or explicit logout
function clearSession() {
  sessionId = null;
}
"""


# ============================================================================
# INITIALIZATION
# ============================================================================
# Add to app/main.py startup event (optional)

"""
@app.on_event("startup")
async def startup_event():
    # Initialize chatbot on startup
    from app.chatbot.integration_wrapper import get_enhanced_chatbot
    
    chatbot = get_enhanced_chatbot()
    
    # Set default property if needed
    chatbot.set_property_from_context(tenant_id="hotel_tas_luxury")
    
    print("[Chatbot] Enhanced chatbot initialized")
"""


# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of the integration
    """
    import asyncio
    
    async def test():
        print("Testing enhanced chatbot integration...\n")
        
        # Test 1: Simple question
        answer1 = await get_guest_answer(
            "Do you have any rooms available?",
            tenant_id="hotel_tas_luxury"
        )
        print(f"Q: Do you have any rooms available?")
        print(f"A: {answer1}\n")
        
        # Test 2: With dates
        answer2 = await get_guest_answer(
            "I need a room for March 15-17",
            tenant_id="hotel_tas_luxury"
        )
        print(f"Q: I need a room for March 15-17")
        print(f"A: {answer2}\n")
        
        # Test 3: Amenity question
        answer3 = await get_guest_answer(
            "Do you have a spa?",
            tenant_id="hotel_tas_luxury"
        )
        print(f"Q: Do you have a spa?")
        print(f"A: {answer3}\n")
    
    asyncio.run(test())
