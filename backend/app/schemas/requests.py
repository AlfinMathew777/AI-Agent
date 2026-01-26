from pydantic import BaseModel

class QuestionRequest(BaseModel):
  question: str

class AgentRequest(BaseModel):
    audience: str
    question: str
    session_id: str = None
    confirm: bool = False

class AgentConfirmRequest(BaseModel):
    action_id: str
    confirm: bool
