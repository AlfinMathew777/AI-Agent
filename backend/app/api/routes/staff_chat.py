"""
Staff Chat API Routes

Provides endpoints for the internal staff AI assistant.
Role-aware responses based on logged-in user's role.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

from app.api.deps import get_current_user, require_staff
from app.schemas.auth import TokenData
from app.agents.policy_agent import get_policy_agent, ROLE_CONTEXTS

router = APIRouter()


class StaffChatRequest(BaseModel):
    """Request model for staff chat."""
    message: str
    session_id: Optional[str] = None


class SourceInfo(BaseModel):
    """Source document information."""
    index: int
    preview: str
    type: str


class StaffChatResponse(BaseModel):
    """Response model for staff chat."""
    answer: str
    sources: List[SourceInfo]
    role_context: str
    chunks_used: int
    session_id: str
    timestamp: str


class RoleContextResponse(BaseModel):
    """Response model for role context."""
    role: str
    title: str
    focus_areas: List[str]
    example_questions: List[str]


# Example questions per role for UI
ROLE_EXAMPLES = {
    "front_desk": [
        "What is the late check-out policy?",
        "How do I handle a guest complaint about noise?",
        "What's the procedure for processing a room upgrade?",
        "How do I handle a lost room key situation?"
    ],
    "housekeeping": [
        "What is the standard room cleaning checklist?",
        "How do I report a maintenance issue?",
        "What's the procedure for handling lost and found items?",
        "What should I do if I find a safety hazard in a room?"
    ],
    "restaurant": [
        "What allergens are in the salmon dish?",
        "How do I handle a guest with a food allergy?",
        "What's the recommended wine pairing for the steak?",
        "How should I handle a complaint about food quality?"
    ],
    "manager": [
        "What's the escalation procedure for serious guest complaints?",
        "How do I approve overtime for staff?",
        "What are the fire safety evacuation procedures?",
        "How should I handle a staffing shortage?"
    ],
    "admin": [
        "What are the emergency evacuation procedures?",
        "How do I onboard a new employee?",
        "What's the vendor management process?",
        "What are our compliance requirements for data privacy?"
    ]
}


@router.post("/staff/chat", response_model=StaffChatResponse)
async def staff_chat(
    request: StaffChatRequest,
    user: TokenData = Depends(require_staff)
):
    """
    Staff AI chat endpoint.
    
    Provides role-aware answers to staff questions about
    hotel policies, procedures, and operations.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get or create session ID
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get the policy agent
    policy_agent = get_policy_agent()
    
    try:
        # Get role-aware answer
        result = await policy_agent.answer(
            role=user.role,
            question=request.message,
            tenant_id=user.tenant_id,
            session_id=session_id
        )
        
        return StaffChatResponse(
            answer=result["answer"],
            sources=[SourceInfo(**s) for s in result.get("sources", [])],
            role_context=result.get("role_context", user.role),
            chunks_used=result.get("chunks_used", 0),
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        print(f"[StaffChat] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response. Please try again."
        )


@router.get("/staff/context", response_model=RoleContextResponse)
async def get_role_context(user: TokenData = Depends(require_staff)):
    """
    Get the current user's role context and suggested questions.
    """
    role = user.role
    context = ROLE_CONTEXTS.get(role, ROLE_CONTEXTS.get("front_desk"))
    examples = ROLE_EXAMPLES.get(role, ROLE_EXAMPLES.get("front_desk"))
    
    return RoleContextResponse(
        role=role,
        title=context["title"],
        focus_areas=context["focus_areas"],
        example_questions=examples
    )


@router.get("/staff/examples")
async def get_example_questions(user: TokenData = Depends(require_staff)):
    """
    Get example questions for the current user's role.
    """
    role = user.role
    examples = ROLE_EXAMPLES.get(role, ROLE_EXAMPLES.get("front_desk"))
    
    return {
        "role": role,
        "examples": examples
    }


@router.get("/staff/roles")
async def get_available_roles():
    """
    Get all available staff roles and their descriptions.
    Public endpoint for reference.
    """
    roles = []
    for role, context in ROLE_CONTEXTS.items():
        roles.append({
            "role": role,
            "title": context["title"],
            "focus_areas": context["focus_areas"][:3]  # First 3 focus areas
        })
    return {"roles": roles}
