
import asyncio
import sys
import os
import traceback

# Setup path
sys.path.append(os.getcwd())

from app.ai_service import get_guest_answer, hotel_ai

async def run_debug():
    print("--- Debugging 500 Error ---")
    question = "Is the pool open?"
    print(f"Question: {question}")
    
    try:
        # Check if HotelAI initialized correctly
        print("Checking HotelAI initialization...")
        if not hotel_ai:
            print("ERROR: hotel_ai is None")
        else:
            print(f"Provider: {hotel_ai.provider}")
            print(f"Model: {getattr(hotel_ai, '_gemini_model', 'N/A')}")
        
        # Run generation
        print("\nCalling get_guest_answer...")
        answer = await get_guest_answer(question)
        print(f"\nSUCCESS! Answer: {answer}")
        
    except Exception:
        print("\n!!! CRASH DETECTED !!!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
