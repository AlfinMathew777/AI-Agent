from pydantic import BaseModel

class AnswerResponse(BaseModel):
  role: str
  question: str
  answer: str
