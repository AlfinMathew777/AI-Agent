# Agent Pydantic Models will go here
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AgentRequest(BaseModel):
    audience: str
    question: str
    session_id: str
    confirm: Optional[bool] = False

class ActionPlan(BaseModel):
    tool: str
    params: Dict[str, Any]
    risk_level: str

class AgentResponse(BaseModel):
    answer: str
    status: str = "success" # success, needs_confirmation, failed
    data: Optional[Dict[str, Any]] = None
    action_id: Optional[str] = None
