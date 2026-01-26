"""Quick test script to check the endpoint"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_service import get_guest_answer

async def test():
    try:
        print("Testing guest answer...")
        result = await get_guest_answer("What is the WiFi password?")
        print(f"Success! Result: {result[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
