
from app.llm import HotelAI
from app.rag_loader import index_knowledge_base

ai = HotelAI()
index_knowledge_base(ai)
