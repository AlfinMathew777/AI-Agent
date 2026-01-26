
import asyncio
import sys
from app.ai_service import get_guest_answer, hotel_ai

async def test_general_chat():
    print("--- Testing General Chat ---", flush=True)
    
    # 1. Ask a general question (unlikely to be in RAG)
    question = "How are you doing today?"
    print(f"\nQuestion: {question}", flush=True)
    
    # Force empty docs to simulate no RAG match if needed, 
    # but the service should handle it naturally.
    answer = await get_guest_answer(question)
    print(f"Answer: {answer}", flush=True)
    
    # 2. Ask a hotel question (should still work)
    question_hotel = "Is there a gym?"
    print(f"\nQuestion: {question_hotel}", flush=True)
    answer_hotel = await get_guest_answer(question_hotel)
    print(f"Answer: {answer_hotel}", flush=True)

if __name__ == "__main__":
    asyncio.run(test_general_chat())
