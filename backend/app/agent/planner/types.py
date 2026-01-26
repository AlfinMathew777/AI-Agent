from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class PlanStep(BaseModel):
    id: Optional[str] = None
    step_index: int
    step_type: str  # "TOOL" or "CHAT"
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    risk: str # "READ", "WRITE", "NONE"
    status: str = "pending" # pending, running, success, failed, blocked
    result: Optional[str] = None
    # Experience Package Extensions
    save_as: Optional[str] = None 
    requires_input: bool = False
    input_key: Optional[str] = None

class Plan(BaseModel):
    id: Optional[str] = None
    session_id: str
    audience: str
    question: str
    plan_summary: str
    steps: List[PlanStep]
    status: str = "created"
    # Experience Package Extensions
    plan_mode: str = "commit" # "explore" or "commit"
    context: Dict[str, Any] = {} # Store intermediate results
