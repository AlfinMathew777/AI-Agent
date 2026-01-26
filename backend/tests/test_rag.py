# backend/test_rag.py
import sys
import os

# Add current dir to path so we can import app
# Add backend root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_service import get_guest_answer

print("--- Testing Guest RAG ---")
q = "What time is breakfast?"
print(f"Question: {q}")
ans = get_guest_answer(q)
print(f"Answer: {ans}")

print("\n--- Testing Fallback ---")
q = "What is the meaning of life?"
print(f"Question: {q}")
ans = get_guest_answer(q)
print(f"Answer: {ans}")
