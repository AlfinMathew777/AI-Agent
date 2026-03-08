"""
FastAPI Chatbot API Endpoints
Production-ready endpoints with error handling and session management
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
import asyncio

from .concierge_bot import HotelConciergeBot

app = FastAPI(
    title="ACP Hotel Chatbot API",
    description="AI Concierge chatbot with ACP backend integration",
    version="1.0.0"
)

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bot instances (PRODUCTION: Use Redis instead)
# This is memory-only and will NOT survive restarts or work with multiple workers
bot_instances: Dict[str, HotelConciergeBot] = {}

# Cleanup task for expired sessions
async def cleanup_task():
    """Background task to cleanup expired bot sessions"""
    while True:
        await asyncio.sleep(600)  # Every 10 minutes
        expired = []
        for session_id, bot in bot_instances.items():
            # Check if session manager has expired sessions
            if bot.sessions.cleanup_expired_sessions() > 0:
                # If all sessions expired, remove bot instance
                if len(bot.sessions.sessions) == 0:
                    expired.append(session_id)
        
        for session_id in expired:
            del bot_instances[session_id]
            print(f"[Cleanup] Removed expired bot instance: {session_id}")


@app.on_event("startup")
async def startup_event():
    """Start background cleanup task"""
    asyncio.create_task(cleanup_task())


class InitRequest(BaseModel):
    """Initialize chatbot session request"""
    property_id: str
    session_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "property_id": "hotel_tas_luxury",
                "session_id": None
            }
        }


class ChatRequest(BaseModel):
    """Chat message request"""
    session_id: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc-123-def-456",
                "message": "Do you have rooms available next weekend?"
            }
        }


class ChatResponse(BaseModel):
    """Chat response with action and optional data"""
    response: str
    action: str
    data: Optional[dict] = None
    session_id: Optional[str] = None


@app.post("/chat/init", response_model=ChatResponse, tags=["Chat"])
async def initialize_chat(request: InitRequest):
    """
    Initialize new chat session with property context
    
    - **property_id**: Property identifier (e.g., 'hotel_tas_luxury')
    - **session_id**: Optional session ID (generates if not provided)
    
    Returns welcome message and session ID
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Create bot instance
        bot = HotelConciergeBot(property_id=request.property_id)
        
        # Initialize session
        welcome_msg = await bot.initialize_session(session_id, request.property_id)
        
        # Store bot instance
        bot_instances[session_id] = bot
        
        return ChatResponse(
            response=welcome_msg,
            action="initialized",
            data={"property_id": request.property_id},
            session_id=session_id
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Property database not found: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid property ID: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Initialization failed: {str(e)}"
        )


@app.post("/chat/message", response_model=ChatResponse, tags=["Chat"])
async def process_message(request: ChatRequest):
    """
    Process chat message
    
    - **session_id**: Active session ID (from /chat/init)
    - **message**: User message text
    
    Returns AI response with action type
    """
    if request.session_id not in bot_instances:
        raise HTTPException(
            status_code=400,
            detail="Session not found or expired. Please call /chat/init first."
        )
    
    try:
        bot = bot_instances[request.session_id]
        result = await bot.process_message(request.session_id, request.message)
        
        return ChatResponse(
            response=result["response"],
            action=result.get("action", "unknown"),
            data=result.get("data"),
            session_id=request.session_id
        )
    except Exception as e:
        print(f"[API] Error processing message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.post("/chat/reset", tags=["Chat"])
async def reset_session(session_id: str):
    """
    Clear session data and remove bot instance
    
    - **session_id**: Session ID to reset
    """
    if session_id in bot_instances:
        # Close database connections
        bot_instances[session_id].db.close()
        del bot_instances[session_id]
        
    return {"status": "reset", "session_id": session_id}


@app.get("/chat/session/{session_id}", tags=["Chat"])
async def get_session_info(session_id: str):
    """
    Get session information and context
    
    Returns current session context and conversation history
    """
    if session_id not in bot_instances:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    try:
        bot = bot_instances[session_id]
        session = bot.sessions.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session expired")
        
        # Get summary and history
        summary = bot.sessions.get_session_summary(session_id)
        history = bot.sessions.get_history(session_id, limit=10)
        
        return {
            "session_id": session_id,
            "summary": summary,
            "context": session.get("context", {}),
            "current_intent": session.get("current_intent"),
            "pending_action": session.get("pending_action"),
            "history": history,
            "created_at": session.get("created_at").isoformat(),
            "last_activity": session.get("last_activity").isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Status"])
async def health_check():
    """
    Health check endpoint
    
    Returns API status and active session count
    """
    return {
        "status": "healthy",
        "active_sessions": len(bot_instances),
        "service": "ACP Hotel Chatbot API"
    }


@app.get("/", tags=["Status"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "ACP Hotel Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "init": "POST /chat/init",
            "message": "POST /chat/message",
            "reset": "POST /chat/reset",
            "session_info": "GET /chat/session/{session_id}",
            "health": "GET /health"
        },
        "docs": "/docs"
    }


# PRODUCTION NOTES:
# 1. Replace bot_instances dict with Redis:
#    import redis
#    r = redis.Redis(host='localhost', port=6379, db=0)
#    
#    # Store session data:
#    r.setex(f"session:{session_id}", 1800, json.dumps(session_data))
#    
#    # Retrieve:
#    data = r.get(f"session:{session_id}")
#
# 2. Add authentication middleware if needed
# 
# 3. Configure CORS properly for production domains
#
# 4. Add rate limiting:
#    from slowapi import Limiter, _rate_limit_exceeded_handler
#    limiter = Limiter(key_func=get_remote_address)
#    app.state.limiter = limiter
#
# 5. Add logging and monitoring
#    import logging
#    logger = logging.getLogger(__name__)
